#!/usr/bin/env python3
"""Validate the instrument library in library/.

Checks every file against its JSON Schema, then checks cross-references:
file names match ids, construct ids exist, evidence points at a real
instrument/version/dimension, and source_verified records have no open
needs_check items.

Usage: python scripts/validate_library.py [path/to/library]
Exit code 0 = valid, 1 = problems found.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


def load(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def schema_errors(validator: Draft202012Validator, data, label: str) -> list[str]:
    return [
        f"{label}: {'/'.join(str(p) for p in err.absolute_path) or '(root)'}: {err.message}"
        for err in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    ]


def main(library: Path) -> int:
    problems: list[str] = []
    schemas = library / "schema"
    fmt = FormatChecker()
    instrument_v = Draft202012Validator(load(schemas / "instrument.schema.json"), format_checker=fmt)
    evidence_v = Draft202012Validator(load(schemas / "evidence.schema.json"), format_checker=fmt)
    constructs_v = Draft202012Validator(load(schemas / "constructs.schema.json"), format_checker=fmt)

    # Constructs
    constructs_doc = load(library / "constructs.json")
    problems += schema_errors(constructs_v, constructs_doc, "constructs.json")
    construct_ids: set[str] = set()
    for c in constructs_doc.get("constructs", []):
        if c["id"] in construct_ids:
            problems.append(f"constructs.json: duplicate id {c['id']}")
        construct_ids.add(c["id"])
    for c in constructs_doc.get("constructs", []):
        if c.get("broader") and c["broader"] not in construct_ids:
            problems.append(f"constructs.json: {c['id']} has unknown broader '{c['broader']}'")

    def check_review(review: dict, label: str):
        if review.get("status") == "source_verified" and review.get("needs_check"):
            problems.append(f"{label}: status is source_verified but needs_check is not empty")

    # Instruments
    instruments: dict[str, dict] = {}
    for path in sorted((library / "instruments").glob("*.json")):
        label = f"instruments/{path.name}"
        data = load(path)
        problems += schema_errors(instrument_v, data, label)
        iid = data.get("id")
        if iid != path.stem:
            problems.append(f"{label}: id '{iid}' does not match file name")
        if iid in instruments:
            problems.append(f"{label}: duplicate instrument id {iid}")
        instruments[iid] = data

        refs = list(data.get("construct_ids", []))
        version_ids = [v.get("version_id") for v in data.get("versions", [])]
        if len(version_ids) != len(set(version_ids)):
            problems.append(f"{label}: duplicate version_id")
        for v in data.get("versions", []):
            parent = v.get("adapted_from_version_id")
            if parent and parent not in version_ids:
                problems.append(f"{label}: version {v.get('version_id')} adapted from unknown version {parent}")
        dim_ids = [d.get("dimension_id") for d in data.get("dimensions", [])]
        if len(dim_ids) != len(set(dim_ids)):
            problems.append(f"{label}: duplicate dimension_id")
        for d in data.get("dimensions", []):
            refs += d.get("construct_ids", [])
            for vid in d.get("version_ids", []):
                if vid not in version_ids:
                    problems.append(f"{label}: dimension {d.get('dimension_id')} lists unknown version {vid}")
        for cid in sorted(set(refs) - construct_ids):
            problems.append(f"{label}: unknown construct id '{cid}' (add it to constructs.json)")
        check_review(data.get("review", {}), label)

    for iid, data in instruments.items():
        for rid in data.get("related_instrument_ids", []):
            if rid not in instruments:
                problems.append(f"instruments/{iid}.json: related instrument '{rid}' not found")

    # Evidence
    evidence_ids: set[str] = set()
    for path in sorted((library / "evidence").glob("*/*.json")):
        label = f"evidence/{path.parent.name}/{path.name}"
        data = load(path)
        problems += schema_errors(evidence_v, data, label)
        eid = data.get("id")
        if eid != path.stem:
            problems.append(f"{label}: id '{eid}' does not match file name")
        if eid in evidence_ids:
            problems.append(f"{label}: duplicate evidence id {eid}")
        evidence_ids.add(eid)
        iid = data.get("instrument_id")
        if iid != path.parent.name:
            problems.append(f"{label}: instrument_id '{iid}' does not match folder name")
        inst = instruments.get(iid)
        if inst is None:
            problems.append(f"{label}: unknown instrument '{iid}'")
        else:
            version_ids = {v["version_id"] for v in inst.get("versions", [])}
            if data.get("version_id") not in version_ids:
                problems.append(f"{label}: unknown version '{data.get('version_id')}' for {iid}")
            dim = data.get("dimension_id")
            dims = {d["dimension_id"]: d for d in inst.get("dimensions", [])}
            if dim is not None:
                if dim not in dims:
                    problems.append(f"{label}: unknown dimension '{dim}' for {iid}")
                elif dims[dim].get("version_ids") and data.get("version_id") not in dims[dim]["version_ids"]:
                    problems.append(f"{label}: dimension '{dim}' does not apply to version '{data.get('version_id')}'")
        check_review(data.get("review", {}), label)

    # Item files (crosswalks and, where permitted, item text)
    items_schema_path = schemas / "items.schema.json"
    item_file_count = 0
    if items_schema_path.exists() and (library / "items").exists():
        items_v = Draft202012Validator(load(items_schema_path), format_checker=fmt)
        item_ids_by_instrument: dict[str, set[str]] = {}
        derived_refs: list[tuple[str, str, str]] = []
        for path in sorted((library / "items").glob("*/*.json")):
            item_file_count += 1
            label = f"items/{path.parent.name}/{path.name}"
            data = load(path)
            problems += schema_errors(items_v, data, label)
            iid = data.get("instrument_id")
            if iid != path.parent.name:
                problems.append(f"{label}: instrument_id '{iid}' does not match folder name")
            if data.get("version_id") != path.stem:
                problems.append(f"{label}: version_id '{data.get('version_id')}' does not match file name")
            inst = instruments.get(iid)
            if inst is None:
                problems.append(f"{label}: unknown instrument '{iid}'")
                continue
            if data.get("version_id") not in {v["version_id"] for v in inst.get("versions", [])}:
                problems.append(f"{label}: unknown version '{data.get('version_id')}' for {iid}")
            access = inst.get("access", {})
            text_ok = access.get("item_text_shareable", False)
            key_ok = access.get("answer_key_shareable", False)
            dims = {d["dimension_id"] for d in inst.get("dimensions", [])}
            seen: set[str] = set()
            numbers: set[str] = set()
            for item in data.get("items", []):
                item_id = item.get("item_id", "?")
                where = f"{label}: item {item_id}"
                if item_id in seen:
                    problems.append(f"{where}: duplicate item_id in this version")
                seen.add(item_id)
                if item.get("number") in numbers:
                    problems.append(f"{where}: duplicate number {item.get('number')}")
                numbers.add(item.get("number"))
                has_text = (
                    "stem" in item or "figures" in item
                    or any("text" in o or "image" in o for o in item.get("options", []))
                )
                for rel in [f.get("path") for f in item.get("figures", [])] + [o.get("image") for o in item.get("options", [])]:
                    if rel and not (path.parent / rel).exists():
                        problems.append(f"{where}: missing image file {rel}")
                labels = [o.get("label") for o in item.get("options", [])]
                if len(labels) != len(set(labels)):
                    problems.append(f"{where}: duplicate option label")
                if has_text and not text_ok:
                    problems.append(f"{where}: contains item text but {iid} does not permit item text")
                if any("is_correct" in o for o in item.get("options", [])) and not key_ok:
                    problems.append(f"{where}: contains an answer key but {iid} does not permit answer keys")
                for did in item.get("dimension_ids", []):
                    if did not in dims:
                        problems.append(f"{where}: unknown dimension '{did}'")
                for cid in item.get("construct_ids", []):
                    if cid not in construct_ids:
                        problems.append(f"{where}: unknown construct '{cid}'")
                for req in item.get("requires_item_ids", []):
                    derived_refs.append((iid, req, where))
                if item.get("derived_from"):
                    derived_refs.append((iid, item["derived_from"]["item_id"], where))
            item_ids_by_instrument.setdefault(iid, set()).update(seen)
        for iid, ref, where in derived_refs:
            if ref not in item_ids_by_instrument.get(iid, set()):
                problems.append(f"{where}: referenced item '{ref}' not found in any {iid} version file")

    # Every instrument with item text must appear in the LICENSE.md table with the same license
    license_doc = library / "LICENSE.md"
    license_text = license_doc.read_text(encoding="utf-8") if license_doc.exists() else ""
    for iid, inst in instruments.items():
        basis = inst.get("access", {}).get("item_text_basis")
        if inst.get("access", {}).get("item_text_shareable") and basis:
            lic = basis.get("license", "")
            short = lic.split(" (")[0]
            if short and short not in license_text:
                problems.append(f"instruments/{iid}.json: item text license '{lic}' is not listed in library/LICENSE.md")

    if problems:
        print(f"Library validation failed with {len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1
    open_checks = sum(
        len(load(p).get("review", {}).get("needs_check", []))
        for p in list((library / "instruments").glob("*.json")) + list((library / "evidence").glob("*/*.json"))
    )
    print(
        f"Library OK: {len(construct_ids)} constructs, {len(instruments)} instruments, "
        f"{len(evidence_ids)} evidence records, {item_file_count} item files "
        f"({open_checks} open needs_check items)."
    )
    return 0


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "library"
    sys.exit(main(root))
