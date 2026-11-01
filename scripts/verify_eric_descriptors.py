#!/usr/bin/env python3
# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check the profile's ERIC descriptors against the official ERIC Thesaurus.

1. Download the thesaurus from https://eric.ed.gov/?download (the "ERIC
   Thesaurus" file).
2. Run:  python scripts/verify_eric_descriptors.py path/to/thesaurus-file [--update]

The file may be a .zip or the extracted XML/CSV/text. A descriptor counts as
found when it appears as an exact, whole entry (an XML element's text, a CSV
cell, or a line). Retired descriptors are usually marked with a year in
parentheses, e.g. "Climate Change (2004)"; those do not match because the
entry text differs.

With --update, newly confirmed descriptors move from "unverified" to
"verified" in standard/stemed-ap/crosswalks/eric_descriptor_status.json.
Descriptors that are not found are reported; fix their mappings by hand.
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATUS = ROOT / "standard" / "stemed-ap" / "crosswalks" / "eric_descriptor_status.json"


def entries_from_text(text: str) -> set[str]:
    found: set[str] = set()
    found.update(m.strip() for m in re.findall(r">([^<>]{2,120})<", text))
    for row in csv.reader(io.StringIO(text)):
        found.update(cell.strip() for cell in row if 1 < len(cell.strip()) <= 120)
    found.update(line.strip() for line in text.splitlines() if 1 < len(line.strip()) <= 120)
    return found


def load_entries(path: Path) -> set[str]:
    if zipfile.is_zipfile(path):
        entries: set[str] = set()
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if not name.endswith("/"):
                    entries |= entries_from_text(archive.read(name).decode("utf-8", errors="replace"))
        return entries
    return entries_from_text(path.read_text(encoding="utf-8", errors="replace"))


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    entries = load_entries(Path(sys.argv[1]))
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    missing_verified = [t for t in status["verified"] if t not in entries]
    confirmed = [t for t in status["unverified"] if t in entries]
    still_missing = [t for t in status["unverified"] if t not in entries]
    print(f"Thesaurus entries read: {len(entries)}")
    print(f"Previously verified but not found ({len(missing_verified)}): {missing_verified}")
    print(f"Unverified now confirmed ({len(confirmed)}): {confirmed}")
    print(f"Unverified and not found ({len(still_missing)}): {still_missing}")
    if "--update" in sys.argv and confirmed:
        status["verified"] = sorted(set(status["verified"]) | set(confirmed))
        status["unverified"] = still_missing
        status["checked_on"] = date.today().isoformat()
        STATUS.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("Updated eric_descriptor_status.json; now run python scripts/build_profile_artifacts.py")
    return 1 if missing_verified else 0


if __name__ == "__main__":
    sys.exit(main())
