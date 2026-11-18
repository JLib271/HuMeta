# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""App settings with no Streamlit dependency: file locations and file formats.

Study metadata vocabularies live in the HuMeta profile
(standard/humeta/vocabularies.json); theories and lenses for Module 2 live in
library/frameworks.json (a snapshot of the HuMeta Instrument Library)."""

from __future__ import annotations

import re
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
PUBLISHED_DIR = APP_DIR / "published"
PUBLISHED_SUMMARIES_DIR = PUBLISHED_DIR / "study_summaries"
DEFAULT_GITHUB_REPO = "JLib271/HuMeta"
#: The HuMeta Instrument Library's repository: recommendations (suggestions/) go there
DEFAULT_LIBRARY_REPO = "JLib271/humeta-library"
#: The HuMeta profile's repository: proposed changes to the standard go there as issues
DEFAULT_PROFILE_REPO = "JLib271/humeta-profile"
#: The HuMeta Library website, built by humeta-library's scripts/build_site.py
LIBRARY_SITE_URL = "https://jlib271.github.io/humeta-library/"
#: The deployed HuMeta Portal (Streamlit) app; the Library website links to it
PORTAL_URL = "https://humeta.streamlit.app/"


#: Persistent identifiers of library records on w3id.org (redirect rules: humeta-library w3id/ids/humeta/.htaccess).
#: Identifiers are opaque (hmi0004, hmi0004.1, hmc0024, hmf0038): each record's "pid" in the library. The policy,
#: which follows McMurry et al. (2017), is humeta-library's IDENTIFIERS.md.
PERSISTENT_BASE = "https://w3id.org/humeta/"
IDENTIFIER_POLICY_URL = "https://github.com/JLib271/humeta-library/blob/main/IDENTIFIERS.md"
#: The HuMeta metadata-code scheme (Construct_Measure_Item_Target)
METADATA_CODE_URI = PERSISTENT_BASE + "metadata-code"
_PID_TYPES = (("instrument", re.compile(r"^hmi[0-9]{4}(\.[1-9][0-9]*)?$")),
              ("construct", re.compile(r"^hmc[0-9]{4}$")),
              ("framework", re.compile(r"^hmf[0-9]{4}$")))


def pid_uri(pid: str | None) -> str | None:
    """https://w3id.org/humeta/<type>/<pid> for a HuMeta identifier, else None."""
    for kind, pattern in _PID_TYPES:
        if pid and pattern.match(pid):
            return f"{PERSISTENT_BASE}{kind}/{pid}"
    return None


def persistent_uri(lib, kind: str, record_id: str | None, version_id: str | None = None) -> str | None:
    """Persistent identifier of a library record, or None if the record has none (or is not in the library).

    kind: instrument, construct or framework. With version_id, the identifier of that instrument version
    (https://w3id.org/humeta/instrument/hmi0004.1); if the version is not found, the instrument's."""
    records = {"instrument": lib.instruments, "construct": lib.constructs, "framework": lib.frameworks}[kind]
    rec = records.get(record_id or "")
    if not rec:
        return None
    if kind == "instrument" and version_id:
        version = next((v for v in rec.get("versions", []) if v.get("version_id") == version_id), None)
        if version and pid_uri(version.get("pid")):
            return pid_uri(version["pid"])
    return pid_uri(rec.get("pid"))


def item_uri(lib, instrument_id: str, item_id: str) -> str | None:
    """Persistent identifier of an item, the same in every version that has it:
    https://w3id.org/humeta/instrument/hmi0004/item/q05."""
    base = persistent_uri(lib, "instrument", instrument_id)
    return f"{base}/item/{item_id}" if base else None


def library_page_url(kind: str, record_id: str) -> str:
    """Address of a record's page on the Library website (kind: instruments, frameworks or constructs)."""
    return f"{LIBRARY_SITE_URL}{kind}/{record_id.replace('_', '-')}/"
PROJECT_FILE_FORMAT = "humeta-project"
#: earlier project-file format names that still load
LEGACY_PROJECT_FILE_FORMATS = ("openedmetadata-project",)

