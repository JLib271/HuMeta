# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Comment on an instrument recommendation with what its KCWorks deposit says.

Run by .github/workflows/recommendation-check.yml when a "Recommend an instrument" issue is opened or
edited. It finds the deposit link in the issue form, looks the record up on Knowledge Commons Works,
and posts (or updates) one comment with the deposit's title, DOI, license, and whether it is in the
STEMEd+ collection, plus a ready-to-paste ``commons_records`` entry. The issue text is untrusted: only
a link is extracted from it, and nothing from it is run.

Environment: ISSUE_BODY, ISSUE_NUMBER, GITHUB_REPOSITORY, GITHUB_TOKEN. With --dry-run, prints the comment.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kcworks_lookup as K  # noqa: E402

MARKER = "<!-- humeta-deposit-check -->"
LINK_HEADING = "Link to the deposit on Knowledge Commons (KCWorks)"
CONTENTS_HEADING = "What's in the deposit?"
RIGHTS_HEADING = "Rights"
CONTENTS = {"The instrument": "instrument", "Manual or user guide": "manual", "Item, image, or scoring files": "item_files",
            "A paper about it": "paper"}


def ticked(answer: str) -> list[str]:
    """Contents ticked in the form's checkbox list."""
    out = []
    for line in answer.splitlines():
        m = re.match(r"\s*-\s*\[[xX]\]\s*(.+)", line)
        if m:
            out += [v for k, v in CONTENTS.items() if m.group(1).startswith(k)]
    return out


def form_field(body: str, heading: str) -> str:
    """The answer under '### heading' in a GitHub issue form body ('' if empty)."""
    m = re.search(r"^###\s+" + re.escape(heading) + r"\s*$(.*?)(?=^###\s|\Z)", body or "", re.M | re.S)
    value = m.group(1).strip() if m else ""
    return "" if value in ("_No response_", "None") else value


def safe(text: str) -> str:
    return re.sub(r"[<>`|\[\]]", "", str(text or ""))[:300]


def build_comment(body: str, fetch=K.get_json) -> str:
    link = form_field(body, LINK_HEADING)
    contents = ticked(form_field(body, CONTENTS_HEADING))
    holder = "[x]" in form_field(body, RIGHTS_HEADING).lower()
    lines = [MARKER, "### STEMEd+ Commons deposit check"]
    if not link:
        lines += ["No deposit link was given. Depositing the instrument, its manual, or a paper about it in the "
                  "[STEMEd+ collection](https://works.hcommons.org/collections/stemedplus/) gives it a DOI and a link "
                  "from its Library page ([how to deposit](https://jlib271.github.io/HuMeta/recommend/#deposit)). "
                  "Edit this issue to add the link and this check will run again."]
        return "\n\n".join(lines)
    try:
        s = K.summarize(K.find_record(link, fetch), fetch)
    except K.LookupError_ as exc:
        return "\n\n".join(lines + [f"Could not read the deposit link: {safe(exc)}"])
    except Exception:  # noqa: BLE001
        return "\n\n".join(lines + ["Could not reach Knowledge Commons Works just now. A maintainer will check the link."])
    lic = s["licenses"]
    lic_text = ", ".join(safe(x["title"]) for x in lic) if lic else "none recorded"
    rows = [f"- **Title:** {safe(s['title'])}",
            f"- **Link:** {s['url']}" + (f" (DOI [{s['doi']}](https://doi.org/{s['doi']}))" if s.get("doi") else ""),
            f"- **License:** {lic_text}",
            "- **In the STEMEd+ collection:** " + ("yes (" + ", ".join(s["in_collections"]) + ")" if s["in_collections"]
                                                 else "not yet (it may be awaiting approval, or was not added)"),
            f"- **Files public:** {'yes' if s['files_public'] else 'no'}",
            "- **Files:** " + (", ".join(safe(f) for f in s.get("files", [])) or "none listed")]
    lines.append("\n".join(rows))
    kind = "instrument" if "instrument" in contents else (contents[0] if contents and contents[0] != "item_files" else "other")
    notes = []
    if kind == "instrument" and lic and all(K.is_open(x["id"]) for x in lic):
        if holder:
            notes.append("The instrument itself is deposited under an open license by its rights holder, so this deposit can be "
                         "the basis for showing its item text (`access.item_text_basis`: `open_license`).")
        else:
            notes.append("The instrument is deposited under an open license, but the submitter did not say they hold the "
                         "rights. Confirm with the developer before using it as the basis for item text.")
        if not all(K.allows_adaptation(x["id"]) for x in lic):
            notes.append("The license forbids derivatives (ND), so translations and adaptations are not allowed.")
    if not s["in_collections"]:
        notes.append("Collection admins: approve the deposit into the STEMEd+ collection.")
    if len(s.get("files", [])) == 1 and len(contents) > 1:
        notes.append("Only one file is in the record, but several kinds of content were ticked. Please put each in the same "
                     "record as a separate file.")
    if notes:
        lines.append("\n".join(f"- {n}" for n in notes))
    entry = K.commons_record(s, kind)
    if contents:
        entry["contents"] = contents
    if kind == "instrument" and holder:
        entry["deposited_by_rights_holder"] = True
    lines.append("For maintainers, a `commons_records` entry for the instrument record:\n\n```json\n"
                 + json.dumps(entry, indent=2, ensure_ascii=False) + "\n```")
    return "\n\n".join(lines)


def api(method: str, url: str, token: str, payload: dict | None = None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "User-Agent": K.USER_AGENT,
        "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
        return json.load(resp) if resp.status != 204 else None


def post(comment: str, repo: str, number: str, token: str) -> None:
    base = f"https://api.github.com/repos/{repo}/issues/{number}/comments"
    existing = [c for c in api("GET", base + "?per_page=100", token) if MARKER in (c.get("body") or "")
                and (c.get("user") or {}).get("login") == "github-actions[bot]"]
    if existing:
        api("PATCH", existing[0]["url"], token, {"body": comment})
    else:
        api("POST", base, token, {"body": comment})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    comment = build_comment(os.environ.get("ISSUE_BODY", ""))
    if args.dry_run:
        print(comment)
        return 0
    post(comment, os.environ["GITHUB_REPOSITORY"], os.environ["ISSUE_NUMBER"], os.environ["GITHUB_TOKEN"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
