#!/usr/bin/env python3
# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Refresh library/, the portal's snapshot of the HuMeta Instrument Library.

The library lives in https://github.com/JLib271/humeta-library. Its website
publishes the library's files as data/library.tar.gz, described by
data/library.json; the app reads that at startup (oem.library.use_published).
library/ is a copy of one published archive, used by the tests and as the
app's fallback when the website can't be reached. library/library.json records
which archive it is. Do not edit library/ here.

Usage:
  python scripts/update_library.py            # copy the currently published library
  python scripts/update_library.py --check    # is the snapshot the published one?
  python scripts/update_library.py --from ../humeta-library/_site/data
                                              # a locally built site (python scripts/build_site.py there)

The snapshot is replaced only after the new archive has been checked and loads,
so a failed download never leaves a partial library/.
Exit code 0 = done or current, 1 = out of date or failed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from oem import library as L  # noqa: E402

TARGET = ROOT / "library"


def read_source(source: str | None) -> tuple[dict, bytes | None, str]:
    """(manifest, archive bytes or None if only the manifest was needed, label)."""
    if source:
        base = Path(source)
        manifest = json.loads((base / "library.json").read_text(encoding="utf-8"))
        return manifest, (base / manifest["archive"]).read_bytes(), str(base)
    manifest = json.loads(L._fetch(L.PUBLISHED_DATA_URL + "library.json", 30).decode("utf-8"))
    return manifest, None, L.PUBLISHED_DATA_URL


def current_digest() -> str | None:
    try:
        return json.loads((TARGET / "library.json").read_text(encoding="utf-8")).get("sha256")
    except (OSError, ValueError):
        return None


def replace_snapshot(manifest: dict, packed: bytes) -> None:
    if hashlib.sha256(packed).hexdigest() != manifest["sha256"]:
        raise ValueError("the archive does not match library.json")
    with tempfile.TemporaryDirectory() as tmp:
        unpacked = L.unpack_archive(packed, Path(tmp))
        (unpacked / "library.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        old = TARGET.with_name("library.old")
        if old.exists():
            shutil.rmtree(old)
        staging = TARGET.with_name("library.new")
        if staging.exists():
            shutil.rmtree(staging)
        shutil.copytree(unpacked, staging)
        if TARGET.exists():
            TARGET.rename(old)
        staging.rename(TARGET)
        if old.exists():
            shutil.rmtree(old)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="only report whether the snapshot is current")
    ap.add_argument("--from", dest="source", help="a folder with library.json and library.tar.gz")
    args = ap.parse_args(argv)
    try:
        manifest, packed, label = read_source(args.source)
        if manifest.get("format") != "humeta-library-archive":
            raise ValueError("not a HuMeta library manifest")
    except Exception as exc:  # noqa: BLE001 - report any download or format problem
        print(f"Could not read the published library: {exc}", file=sys.stderr)
        return 1

    if current_digest() == manifest["sha256"]:
        print(f"library/ is current ({label}, built {manifest.get('built', '?')}).")
        return 0
    if args.check:
        print(f"library/ is not the library published at {label} (built {manifest.get('built', '?')}).")
        print("Run: python scripts/update_library.py")
        return 1
    try:
        if packed is None:
            packed = L._fetch(L.PUBLISHED_DATA_URL + manifest["archive"], 60)
        replace_snapshot(manifest, packed)
    except Exception as exc:  # noqa: BLE001
        print(f"Could not update library/: {exc}", file=sys.stderr)
        return 1
    counts = manifest.get("counts", {})
    print(f"library/ now matches {label}: {counts.get('instruments', '?')} instruments, "
          f"{counts.get('constructs', '?')} constructs, {counts.get('frameworks', '?')} frameworks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
