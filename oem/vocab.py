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
PUBLISHED_DATASETS_DIR = PUBLISHED_DIR / "datasets"
DEFAULT_GITHUB_REPO = "JLib271/HuMeta"
#: The HuMeta Instrument Library's repository: recommendations (suggestions/) go there
DEFAULT_LIBRARY_REPO = "JLib271/humeta-library"
#: The HuMeta profile's repository: proposed changes to the standard go there as issues
DEFAULT_PROFILE_REPO = "JLib271/humeta-profile"
#: The HuMeta Library website, built by humeta-library's scripts/build_site.py
LIBRARY_SITE_URL = "https://jlib271.github.io/humeta-library/"
#: The deployed HuMeta Portal (Streamlit) app; leave empty until it has an address
PORTAL_URL = ""


def library_page_url(kind: str, record_id: str) -> str:
    """Address of a record's page on the Library website (kind: instruments, frameworks or constructs)."""
    return f"{LIBRARY_SITE_URL}{kind}/{record_id.replace('_', '-')}/"
PUBLIC_DATASET_MAX_MB = 25
PROJECT_FILE_FORMAT = "humeta-project"
#: earlier project-file format names that still load
LEGACY_PROJECT_FILE_FORMATS = ("openedmetadata-project",)

