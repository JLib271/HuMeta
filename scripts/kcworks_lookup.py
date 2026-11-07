# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Look up a Knowledge Commons Works (KCWorks) deposit: title, DOI, license, and collections.

KCWorks runs InvenioRDM, whose public API returns a record's metadata, including its license
(``metadata.rights``) and the collections ("communities") it belongs to. Given a deposit link, this
prints a ``commons_records`` entry for an instrument record in ``library/instruments/``:

    python scripts/kcworks_lookup.py https://works.hcommons.org/records/abcde-12345 --kind manual
    python scripts/kcworks_lookup.py https://doi.org/10.17613/wnm5z-00x75 --kind paper

``scripts/check_recommendation.py`` uses the same functions to comment on recommendation issues.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request

API = "https://works.hcommons.org/api"
SITE = "https://works.hcommons.org"
#: KCWorks collections (InvenioRDM community slugs) that count: the HuMeta Instrument Library subcollection and its parent
STEMEDPLUS_COLLECTIONS = ("humetainstrumentlibrary", "stemedplus")
KCWORKS_DOI_PREFIX = "10.17613/"
USER_AGENT = "HuMeta-Library (https://github.com/JLib271/HuMeta)"

RECORD_RE = re.compile(r"works\.hcommons\.org/records/([a-z0-9]{5}-[a-z0-9]{5})", re.I)
DOI_RE = re.compile(r"(10\.\d{4,9}/[^\s?#\"<>]+)", re.I)


class LookupError_(Exception):
    """The link is not a KCWorks deposit, or the record could not be read."""


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (fixed https host)
        return json.load(resp)


def parse_link(link: str) -> tuple[str | None, str | None]:
    """(record id, DOI) found in a KCWorks record link or a DOI link; either may be None."""
    link = (link or "").strip()
    m = RECORD_RE.search(link)
    if m:
        return m.group(1).lower(), None
    m = DOI_RE.search(urllib.parse.unquote(link))
    if m:
        return None, m.group(1).rstrip(".").lower()
    return None, None


def find_record(link: str, fetch=get_json) -> dict:
    record_id, doi = parse_link(link)
    if record_id:
        return fetch(f"{API}/records/{record_id}")
    if doi:
        if not doi.startswith(KCWORKS_DOI_PREFIX):
            raise LookupError_(f"{doi} is not a Knowledge Commons DOI (they start with {KCWORKS_DOI_PREFIX}).")
        q = urllib.parse.quote(f'pids.doi.identifier:"{doi}"')
        hits = fetch(f"{API}/records?q={q}&size=1").get("hits", {}).get("hits", [])
        if hits:
            return hits[0]
        raise LookupError_(f"No KCWorks record has the DOI {doi}.")
    raise LookupError_("That is not a link to a KCWorks record (https://works.hcommons.org/records/...) or a 10.17613 DOI.")


def collection_ids(fetch=get_json) -> dict[str, str]:
    """InvenioRDM community UUID -> slug for the STEMEd+ collections."""
    out = {}
    for slug in STEMEDPLUS_COLLECTIONS:
        try:
            out[fetch(f"{API}/communities/{slug}")["id"]] = slug
        except Exception:  # noqa: BLE001 - a missing subcollection should not stop the lookup
            pass
    return out


def licenses(record: dict) -> list[dict]:
    out = []
    for r in record.get("metadata", {}).get("rights", []) or []:
        title = r.get("title")
        if isinstance(title, dict):
            title = title.get("en") or next(iter(title.values()), None)
        out.append({"id": r.get("id") or "", "title": title or r.get("id") or "Custom license", "link": r.get("link") or ""})
    return out


def is_open(lic_id: str) -> bool:
    return lic_id.lower().startswith(("cc-", "cc0"))


def allows_adaptation(lic_id: str) -> bool:
    return is_open(lic_id) and "-nd" not in lic_id.lower()


def summarize(record: dict, fetch=get_json) -> dict:
    md = record.get("metadata", {})
    doi = (record.get("pids", {}).get("doi") or {}).get("identifier")
    url = (record.get("links") or {}).get("self_html") or f"{SITE}/records/{record.get('id')}"
    comm = record.get("parent", {}).get("communities", {}) or {}
    ids = set(comm.get("ids", []) or [])
    slugs = {e.get("slug") for e in comm.get("entries", []) or [] if e.get("slug")}
    stemed = collection_ids(fetch)
    in_stemed = sorted({stemed[i] for i in ids if i in stemed} | (slugs & set(STEMEDPLUS_COLLECTIONS)))
    creators = [((c.get("person_or_org") or {}).get("name") or "") for c in md.get("creators", [])]
    files = []
    entries = (record.get("files") or {}).get("entries")
    if isinstance(entries, dict):
        files = sorted(entries)
    elif record.get("id"):
        try:
            data = fetch(f"{API}/records/{record['id']}/files")
            files = sorted(e.get("key") for e in data.get("entries", []) if e.get("key"))
        except Exception:  # noqa: BLE001 - restricted or metadata-only records have no file list
            files = []
    return {"id": record.get("id"), "url": url, "files": files, "doi": doi, "title": md.get("title"), "creators": [c for c in creators if c],
            "resource_type": ((md.get("resource_type") or {}).get("title") or {}).get("en") or (md.get("resource_type") or {}).get("id"),
            "licenses": licenses(record), "files_public": (record.get("access") or {}).get("files") == "public",
            "in_collections": in_stemed}


def commons_record(summary: dict, kind: str) -> dict:
    entry = {"url": f"https://doi.org/{summary['doi']}" if summary.get("doi") else summary["url"], "kind": kind,
             "label": summary.get("title") or summary["url"]}
    if summary.get("doi"):
        entry["doi"] = summary["doi"]
    if summary["licenses"]:
        entry["license"] = "; ".join(lic["title"] for lic in summary["licenses"])
    entry["in_stemedplus_collection"] = bool(summary["in_collections"])
    return entry


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("link")
    ap.add_argument("--kind", default="instrument", choices=["instrument", "manual", "paper", "item_set", "link", "other"])
    args = ap.parse_args(argv)
    try:
        summary = summarize(find_record(args.link))
    except LookupError_ as exc:
        print(exc, file=sys.stderr)
        return 1
    print(json.dumps({"summary": summary, "commons_records_entry": commons_record(summary, args.kind)}, indent=2,
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
