# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only access to the instrument library in ``library/``.

The library is the single source of truth for instruments, items, constructs,
response scales and standard variables. Load it once and look things up by ID::

    from oem.library import Library
    lib = Library.load()
    gci = lib.instrument("gci")
    items = lib.items("gci", "gci-v4-2014")
    agree5 = lib.scale("agree5")

The app wraps ``Library.load`` in ``st.cache_data``; nothing here imports
Streamlit.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_LIBRARY_DIR = Path(__file__).resolve().parent.parent / "library"


class LibraryError(LookupError):
    """Raised when an ID is not found in the library."""


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


@dataclass(frozen=True)
class Scale:
    id: str
    label: str
    level: str
    points: tuple[tuple[int, str | None], ...]
    missing: tuple[tuple[int, str | None], ...]
    reverse_scoring: str | None = None
    anchors_only: bool = False

    @property
    def codes(self) -> list[int]:
        return [code for code, _ in self.points]


@dataclass
class Library:
    root: Path
    instruments: dict[str, dict] = field(default_factory=dict)
    item_files: dict[tuple[str, str], dict] = field(default_factory=dict)
    constructs: dict[str, dict] = field(default_factory=dict)
    scales: dict[str, Scale] = field(default_factory=dict)
    standard_variables: dict[str, dict] = field(default_factory=dict)
    evidence: list[dict] = field(default_factory=list)

    # ------------------------------------------------------------------ load
    @classmethod
    def load(cls, root: Path | str | None = None) -> "Library":
        root = Path(root) if root else DEFAULT_LIBRARY_DIR
        lib = cls(root=root)
        for path in sorted((root / "instruments").glob("*.json")):
            record = _load_json(path)
            lib.instruments[record["id"]] = record
        items_dir = root / "items"
        if items_dir.is_dir():
            for path in sorted(items_dir.glob("*/*.json")):
                record = _load_json(path)
                record["_dir"] = str(path.parent)
                lib.item_files[(record["instrument_id"], record["version_id"])] = record
        constructs_path = root / "constructs.json"
        if constructs_path.exists():
            for construct in _load_json(constructs_path)["constructs"]:
                lib.constructs[construct["id"]] = construct
        scales_path = root / "scales.json"
        if scales_path.exists():
            doc = _load_json(scales_path)
            default_missing = tuple((p["code"], p["label"]) for p in doc.get("missing_codes", []))
            for s in doc["scales"]:
                lib.scales[s["id"]] = Scale(
                    id=s["id"],
                    label=s["label"],
                    level=s["level"],
                    points=tuple((p["code"], p["label"]) for p in s["points"]),
                    missing=tuple((p["code"], p["label"]) for p in s["missing_codes"]) if "missing_codes" in s else default_missing,
                    reverse_scoring=s.get("reverse_scoring"),
                    anchors_only=bool(s.get("anchors_only", False)),
                )
        std_path = root / "standard_variables.json"
        if std_path.exists():
            for variable in _load_json(std_path)["variables"]:
                lib.standard_variables[variable["name"]] = variable
        evidence_dir = root / "evidence"
        if evidence_dir.is_dir():
            lib.evidence = [_load_json(p) for p in sorted(evidence_dir.glob("*/*.json"))]
        return lib

    # --------------------------------------------------------------- lookups
    def instrument(self, instrument_id: str) -> dict:
        try:
            return self.instruments[instrument_id]
        except KeyError:
            raise LibraryError(f"No instrument {instrument_id!r} in the library") from None

    def version(self, instrument_id: str, version_id: str) -> dict:
        for version in self.instrument(instrument_id).get("versions", []):
            if version["version_id"] == version_id:
                return version
        raise LibraryError(f"No version {version_id!r} for instrument {instrument_id!r}")

    def items(self, instrument_id: str, version_id: str) -> list[dict]:
        """Items for one instrument version (empty list if no item file yet)."""
        self.version(instrument_id, version_id)  # raises if unknown
        record = self.item_files.get((instrument_id, version_id))
        return list(record["items"]) if record else []

    def item(self, instrument_id: str, version_id: str, item_id: str) -> dict:
        for item in self.items(instrument_id, version_id):
            if item["item_id"] == item_id:
                return item
        raise LibraryError(f"No item {item_id!r} in {instrument_id}/{version_id}")

    def scale(self, scale_id: str) -> Scale:
        try:
            return self.scales[scale_id]
        except KeyError:
            raise LibraryError(f"No response scale {scale_id!r} in the library") from None

    def standard_variable(self, name: str) -> dict:
        try:
            return self.standard_variables[name]
        except KeyError:
            raise LibraryError(f"No standard variable {name!r} in the library") from None

    def prefix(self, instrument_id: str) -> str:
        return self.instrument(instrument_id)["variable_prefix"]

    def item_text_allowed(self, instrument_id: str) -> bool:
        return bool(self.instrument(instrument_id).get("access", {}).get("item_text_shareable"))

    def evidence_for(self, instrument_id: str) -> list[dict]:
        return [e for e in self.evidence if e.get("instrument_id") == instrument_id]

    # ---------------------------------------------------------------- search
    def instruments_for_constructs(self, construct_ids: list[str] | set[str]) -> list[dict]:
        """Instruments measuring any of the constructs (whole instrument or any dimension)."""
        wanted = set(construct_ids)
        matches = []
        for record in self.instruments.values():
            measured = set(record.get("construct_ids", []))
            for dimension in record.get("dimensions", []):
                measured.update(dimension.get("construct_ids", []))
            if measured & wanted:
                matches.append(record)
        return matches

    def find_constructs(self, text: str) -> list[dict]:
        """Constructs whose id, label or synonyms contain ``text`` (case-insensitive)."""
        needle = text.strip().lower()
        if not needle:
            return []
        found = []
        for construct in self.constructs.values():
            haystack = [construct["id"], construct["label"], *construct.get("synonyms", [])]
            if any(needle in str(value).lower() for value in haystack):
                found.append(construct)
        return found
