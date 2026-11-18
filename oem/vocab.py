# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""App settings with no Streamlit dependency: file locations and file formats.

Study metadata vocabularies live in the HuMeta profile
(standard/humeta/vocabularies.json); theories and lenses for Module 2 live in
library/frameworks.json (a snapshot of the HuMeta Instrument Library)."""

from __future__ import annotations

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


#: Persistent identifiers of library records on w3id.org (redirect rules: humeta-library w3id/ids/humeta/.htaccess)
PERSISTENT_BASE = "https://w3id.org/humeta/"
#: The HuMeta metadata-code scheme (Construct_Measure_Item_Target)
METADATA_CODE_URI = PERSISTENT_BASE + "metadata-code"


def persistent_uri(kind: str, record_id: str, version_id: str | None = None) -> str:
    """Persistent identifier of a library record: kind instrument, construct or framework, e.g.
    https://w3id.org/humeta/construct/self-efficacy or https://w3id.org/humeta/instrument/gci/gci-v4-2014."""
    return f"{PERSISTENT_BASE}{kind}/{record_id.replace('_', '-')}" + (f"/{version_id}" if version_id else "")


def item_uri(instrument_id: str, item_id: str) -> str:
    """Persistent identifier of an item, the same in every version that has it:
    https://w3id.org/humeta/instrument/gci/item/q05."""
    return f"{persistent_uri('instrument', instrument_id)}/item/{item_id}"


def library_page_url(kind: str, record_id: str) -> str:
    """Address of a record's page on the Library website (kind: instruments, frameworks or constructs)."""
    return f"{LIBRARY_SITE_URL}{kind}/{record_id.replace('_', '-')}/"
PROJECT_FILE_FORMAT = "humeta-project"
#: earlier project-file format names that still load
LEGACY_PROJECT_FILE_FORMATS = ("openedmetadata-project",)

