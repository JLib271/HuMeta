#!/usr/bin/env python3
# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Generate the SHE profile's derived files from its two sources.

Sources (edit these):   standard/she/profile.json, vocabularies.json,
                        library/constructs.json
Generated (don't edit): schema/she-record.schema.json, elements.md,
                        crosswalks/datacite-4.7.csv, crosswalks/eric.csv,
                        crosswalks/alignments.csv,
                        examples/*.datacite.json, examples/*.datacite.xml

Usage:
    python scripts/build_profile_artifacts.py          # write files
    python scripts/build_profile_artifacts.py --check  # fail if any are out of date (CI)
"""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from oem import profile  # noqa: E402
from oem.library import Library  # noqa: E402

BASE = ROOT / "standard" / "she"


def csv_text(rows: list[list[str]]) -> str:
    buffer = io.StringIO()
    csv.writer(buffer, lineterminator="\n").writerows(rows)
    return buffer.getvalue()


def build() -> dict[Path, str]:
    p = profile.load()
    lib = Library.load()
    verified = p.verified_eric()
    files: dict[Path, str] = {}

    files[BASE / "schema" / "she-record.schema.json"] = json.dumps(profile.json_schema(p), indent=2, ensure_ascii=False) + "\n"

    rows = [["element", "module", "label", "obligation", "cardinality", "vocabulary", "datacite_4_7"]]
    for e in p.definition["elements"]:
        rows.append([e["id"], e["module"], e["label"], e["obligation"], e["cardinality"], e.get("vocabulary", ""), e["datacite"]])
    files[BASE / "crosswalks" / "datacite-4.7.csv"] = csv_text(rows)

    standards = p.definition["standards"]
    rows = [["element", "module", "label", "standard", "standard_name", "term", "match", "status", "note", "standard_url"]]
    for e in p.definition["elements"]:
        for a in e.get("alignments", []):
            std = standards[a["standard"]]
            rows.append([e["id"], e["module"], e["label"], std["short"], std["name"], a["term"], a["match"],
                         a.get("status", ""), a.get("note", ""), std["url"]])
    files[BASE / "crosswalks" / "alignments.csv"] = csv_text(rows)

    rows = [["vocabulary", "term_id", "term_label", "eric_descriptor", "eric_status"]]
    for c in lib.constructs.values():
        for d in c.get("eric", []):
            rows.append(["construct", c["id"], c["label"], d, "verified" if d in verified else "unverified"])
    for vocab_id, vocab in p.vocabularies.items():
        for t in vocab["terms"]:
            for d in t.get("eric", []):
                rows.append([vocab_id, t["id"], t["label"], d, "verified" if d in verified else "unverified"])
    files[BASE / "crosswalks" / "eric.csv"] = csv_text(rows)

    lines = [
        f"# {p.definition['title']}: elements and vocabularies",
        "",
        f"*{p.definition['full_title']}*",
        "",
        f"Version {p.version} ({p.definition['status']}). Generated from `profile.json` and "
        "`vocabularies.json` by `scripts/build_profile_artifacts.py`; do not edit by hand.",
        "",
        "Obligations: " + "; ".join(f"**{k}** = {v}" for k, v in p.definition["obligations"].items()),
        "",
        "Alignments: each element lists the standards it corresponds to. No mark = exact match; "
        "**≈** = close match; **~** = related. `SHE` = defined by this profile, with no equivalent in a "
        "general-purpose standard. "
        f"*{profile.SEEKING_INPUT_BADGE}* = {p.definition['alignment_status']['seeking_input'].lower()} "
        "Full list, with notes, in [`crosswalks/alignments.csv`](crosswalks/alignments.csv).",
        "",
        "Standards: " + "; ".join(f"[{s['short']}]({s['url']}) = {s['name']}" for s in p.definition["standards"].values()),
        "",
        "Modules: the **core** applies to every record; a field module (such as **Education**) applies only "
        "when a record includes it, and its mandatory elements are mandatory only then.",
        "",
    ]
    for module_id, module in p.definition["modules"].items():
        lines += [f"## {'Core elements' if module_id == 'core' else module['label'] + ' module'}", "",
                  module["definition"], "",
                  "| Element | Obligation | Cardinality | Definition | Aligned with | DataCite 4.7 mapping |",
                  "|---|---|---|---|---|---|"]
        for e in p.definition["elements"]:
            if e["module"] != module_id:
                continue
            definition = e["definition"] + (f" *{e['condition']}*" if e.get("condition") else "")
            vocab = f" Vocabulary: [{e['vocabulary']}](#{e['vocabulary']})." if e.get("vocabulary") else ""
            lines.append(f"| <a id=\"{e['id']}\"></a>`{e['id']}` | {e['obligation']} | {e['cardinality']} | {definition}{vocab} | "
                     f"{profile.alignment_badges(e['id'], p).replace('` `', '`, `')} | {e['datacite']} |")
        lines.append("")
    lines += ["## Rules", "", "| Rule | Severity | Requirement |", "|---|---|---|"]
    for r in p.definition["rules"]:
        lines.append(f"| {r['id']} | {r['severity']} | {r['message']} |")
    lines += ["", "## Vocabularies", ""]
    for vocab_id, vocab in p.vocabularies.items():
        lines += [f"### <a id=\"{vocab_id}\"></a>{vocab['label']} (`{vocab_id}`)", "", vocab["definition"], "",
                  "| Code | Label | ERIC descriptors |", "|---|---|---|"]
        for t in vocab["terms"]:
            eric = ", ".join(d + ("" if d in verified else " (unverified)") for d in t.get("eric", []))
            lines.append(f"| `{t['id']}` | {t['label']} | {eric} |")
        lines.append("")
    lines += ["### <a id=\"constructs\"></a>Constructs", "",
              "Defined in [`library/constructs.json`](../../library/constructs.json).", "",
              "| Code | Label | Definition | ERIC descriptors |", "|---|---|---|---|"]
    for c in lib.constructs.values():
        eric = ", ".join(d + ("" if d in verified else " (unverified)") for d in c.get("eric", []))
        lines.append(f"| `{c['id']}` | {c['label']} | {c['definition']} | {eric} |")
    files[BASE / "elements.md"] = "\n".join(lines) + "\n"

    for example in sorted((BASE / "examples").glob("*.json")):
        if example.name.endswith(".datacite.json"):
            continue
        record = json.loads(example.read_text(encoding="utf-8"))
        stem = example.name[: -len(".json")]
        files[example.with_name(f"{stem}.datacite.json")] = json.dumps(profile.to_datacite_json(record, lib, p), indent=2, ensure_ascii=False) + "\n"
        if (record["resource"].get("identifier") or {}).get("type") == "DOI":
            files[example.with_name(f"{stem}.datacite.xml")] = profile.to_datacite_xml(record, lib, p) + "\n"
    return files


def main() -> int:
    check = "--check" in sys.argv
    stale = []
    for path, content in build().items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != content:
            stale.append(path.relative_to(ROOT))
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
    if check and stale:
        print("Out of date (run python scripts/build_profile_artifacts.py):")
        for p in stale:
            print(f"  - {p}")
        return 1
    print(("All profile artifacts up to date." if check else f"Wrote {len(stale)} file(s).") if not (check and stale) else "")
    return 0


if __name__ == "__main__":
    sys.exit(main())
