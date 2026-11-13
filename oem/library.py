# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only access to the HuMeta Instrument Library.

The library is the single source of truth for instruments, items, constructs,
frameworks (theories and lenses), response scales and standard variables. It is
kept in its own repository, https://github.com/JLib271/humeta-library, whose
website publishes the library's files as ``data/library.tar.gz``. Load it once
and look things up by ID::

    from oem.library import Library
    lib = Library.load()
    gci = lib.instrument("gci")
    items = lib.items("gci", "gci-v4-2014")
    agree5 = lib.scale("agree5")

``Library.load()`` reads the snapshot in ``library/`` (a copy of a published
library, refreshed with ``scripts/update_library.py``) unless
``use_published()`` has switched it to the current published library, which
the app does at startup. Tests and scripts use the snapshot, so they never
depend on the network. Nothing here imports Streamlit.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import tarfile
import tempfile
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

#: The snapshot of the library kept with the app
DEFAULT_LIBRARY_DIR = Path(__file__).resolve().parent.parent / "library"
#: Where the HuMeta Library website publishes library.json and library.tar.gz
PUBLISHED_DATA_URL = "https://jlib271.github.io/humeta-library/data/"
#: Library.load() with no folder reads this; None means the snapshot
_default_root: Path | None = None


def default_root() -> Path:
    """The folder Library.load() reads when given none: the published copy in use, or the snapshot."""
    return _default_root or DEFAULT_LIBRARY_DIR


def use_snapshot() -> Path:
    """Go back to reading the snapshot in library/."""
    global _default_root
    _default_root = None
    return DEFAULT_LIBRARY_DIR


def _fetch(url: str, timeout: float) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.read()


def unpack_archive(packed: bytes, dest: Path) -> Path:
    """Unpack a library.tar.gz into dest and return its library/ folder, after checking it loads."""
    with tarfile.open(fileobj=io.BytesIO(packed), mode="r:gz") as tar:
        names = tar.getnames()
        if not names or not all(n == "library" or n.startswith("library/") for n in names):
            raise ValueError("not a HuMeta library archive")
        tar.extractall(dest, filter="data")
    root = dest / "library"
    lib = Library.load(root)
    if not lib.instruments or not lib.constructs:
        raise ValueError("the archive holds no instruments or constructs")
    return root


def use_published(base_url: str = PUBLISHED_DATA_URL, cache_dir: Path | str | None = None,
                  timeout: float = 15) -> Path:
    """Make Library.load() read the library the website currently publishes; return the folder used.

    Reads ``library.json`` to learn the archive's checksum, reuses a cached copy with that checksum,
    and otherwise downloads ``library.tar.gz``, checks the checksum and that it loads, and caches it.
    On any problem (offline, a bad download) it keeps whatever Library.load() read before: the last
    good published copy, or the snapshot. Setting HUMETA_LIBRARY_SNAPSHOT keeps the snapshot.
    """
    global _default_root
    if os.environ.get("HUMETA_LIBRARY_SNAPSHOT") and cache_dir is None:
        return default_root()  # pinned to the snapshot (the tests set this)
    cache = Path(cache_dir) if cache_dir else Path(tempfile.gettempdir()) / "humeta-library"
    try:
        manifest = json.loads(_fetch(base_url + "library.json", timeout).decode("utf-8"))
        digest = manifest["sha256"]
        target = cache / digest / "library"
        if not (target / "constructs.json").is_file():
            packed = _fetch(base_url + manifest.get("archive", "library.tar.gz"), timeout)
            if hashlib.sha256(packed).hexdigest() != digest:
                raise ValueError("the downloaded archive does not match library.json")
            staging = Path(tempfile.mkdtemp(prefix="unpack-", dir=_ensure(cache)))
            try:
                unpack_archive(packed, staging)
                (cache / digest).mkdir(exist_ok=True)
                if not target.exists():
                    (staging / "library").rename(target)
            finally:
                shutil.rmtree(staging, ignore_errors=True)
        _default_root = target
    except Exception:  # noqa: BLE001 - the app must keep working with the copy it has
        pass
    return default_root()


def _ensure(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


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
    frameworks: dict[str, dict] = field(default_factory=dict)
    rubric: list[dict] = field(default_factory=list)

    # ------------------------------------------------------------------ load
    @classmethod
    def load(cls, root: Path | str | None = None) -> "Library":
        root = Path(root) if root else default_root()
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
        frameworks_path = root / "frameworks.json"
        if frameworks_path.exists():
            for framework in _load_json(frameworks_path)["frameworks"]:
                lib.frameworks[framework["id"]] = framework
        rubric_path = root / "evidence_rubric.json"
        if rubric_path.exists():
            lib.rubric = _load_json(rubric_path)["categories"]
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

    def framework(self, framework_id: str) -> dict:
        try:
            return self.frameworks[framework_id]
        except KeyError:
            raise LibraryError(f"No framework {framework_id!r} in the library") from None

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
