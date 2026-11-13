#!/usr/bin/env python3
# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Keep standard/humeta/ in step with a released version of the HuMeta profile.

The profile lives in its own repository, https://github.com/JLib271/humeta-profile.
The portal uses one released version of it, named in humeta-profile.json at the
top of this repository, and keeps a copy of that release in standard/humeta/
(everything in the release except .github/). Do not edit standard/humeta/ here:
change the profile in its repository, release it, then move the portal to it.

Usage:
  python scripts/update_profile.py                       # re-copy the pinned version
  python scripts/update_profile.py --version v1.0.0-draft.2  # move to a new release
  python scripts/update_profile.py --check               # does the copy match the pin?
  python scripts/update_profile.py --from ../humeta-profile  # copy from a local checkout
                                                         # (testing an unreleased change)

The copy is replaced only after the whole release has been downloaded and
checked, so a failed download never leaves a partial standard/humeta/.
Exit code 0 = done or up to date, 1 = out of date or failed.
"""
from __future__ import annotations

import argparse
import filecmp
import io
import json
import shutil
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCK = ROOT / "humeta-profile.json"
TARGET = ROOT / "standard" / "humeta"
SKIP = {".github", ".git"}
REQUIRED = ("profile.json", "vocabularies.json", "README.md")


def read_lock() -> dict:
    return json.loads(LOCK.read_text(encoding="utf-8"))


def download(repository: str, version: str, dest: Path) -> Path:
    """Unpack the tagged release into dest; return the release's top folder."""
    url = f"https://codeload.github.com/{repository}/tar.gz/refs/tags/{version}"
    with urllib.request.urlopen(url, timeout=60) as response:
        data = response.read()
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        tar.extractall(dest, filter="data")
    tops = [p for p in dest.iterdir() if p.is_dir()]
    if len(tops) != 1:
        raise RuntimeError(f"unexpected archive layout from {url}")
    return tops[0]


def release_files(source: Path) -> dict[str, Path]:
    """Relative path -> file, for every file in the release except SKIP folders."""
    files = {}
    for path in sorted(source.rglob("*")):
        rel = path.relative_to(source)
        if rel.parts[0] in SKIP or not path.is_file() or "__pycache__" in rel.parts:
            continue
        files[rel.as_posix()] = path
    return files


def differences(source: Path) -> list[str]:
    wanted = release_files(source)
    have = release_files(TARGET) if TARGET.exists() else {}
    out = []
    for rel, path in wanted.items():
        if rel not in have:
            out.append(f"missing: {rel}")
        elif not filecmp.cmp(path, have[rel], shallow=False):
            out.append(f"differs: {rel}")
    out += [f"extra:   {rel}" for rel in have if rel not in wanted]
    return out


def check_release(source: Path) -> None:
    for name in REQUIRED:
        if not (source / name).is_file():
            raise RuntimeError(f"release has no {name}")
    json.loads((source / "profile.json").read_text(encoding="utf-8"))
    json.loads((source / "vocabularies.json").read_text(encoding="utf-8"))


def replace_target(source: Path) -> None:
    """Swap in the new copy: build it beside the old one, then rename."""
    staging = TARGET.with_name(TARGET.name + ".new")
    old = TARGET.with_name(TARGET.name + ".old")
    for leftover in (staging, old):
        if leftover.exists():
            shutil.rmtree(leftover)
    for rel, path in release_files(source).items():
        out = staging / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, out)
    if TARGET.exists():
        TARGET.rename(old)
    staging.rename(TARGET)
    if old.exists():
        shutil.rmtree(old)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--version", help="release tag to move to, e.g. v1.0.0-draft.2")
    parser.add_argument("--check", action="store_true", help="only report whether the copy matches")
    parser.add_argument("--from", dest="local", type=Path, help="copy from a local checkout instead")
    args = parser.parse_args(argv)

    lock = read_lock()
    repository = lock["repository"]
    version = args.version or lock["version"]

    with tempfile.TemporaryDirectory() as tmp:
        try:
            source = args.local.resolve() if args.local else download(repository, version, Path(tmp))
            check_release(source)
        except Exception as exc:  # noqa: BLE001 - report any download or format problem
            print(f"Could not get {repository} {version}: {exc}", file=sys.stderr)
            return 1

        diffs = differences(source)
        label = str(args.local) if args.local else f"{repository} {version}"
        if args.check:
            if diffs:
                print(f"standard/humeta/ does not match {label}:")
                print("\n".join(f"  {d}" for d in diffs))
                print("Run: python scripts/update_profile.py")
                return 1
            print(f"standard/humeta/ matches {label}.")
            return 0

        if diffs:
            replace_target(source)
            print(f"standard/humeta/ now matches {label} ({len(diffs)} file(s) changed).")
        else:
            print(f"standard/humeta/ already matches {label}.")

    if args.version and not args.local and args.version != lock["version"]:
        lock["version"] = args.version
        LOCK.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
        print(f"humeta-profile.json now pins {args.version}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
