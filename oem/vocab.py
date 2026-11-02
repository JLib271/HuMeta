# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""App settings with no Streamlit dependency: file locations and file formats.

Study metadata vocabularies live in the HuMeta profile
(standard/humeta/vocabularies.json); theories and lenses for Module 2 live in
library/frameworks.json."""

from __future__ import annotations

from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
PUBLISHED_DIR = APP_DIR / "published"
PUBLISHED_SUMMARIES_DIR = PUBLISHED_DIR / "study_summaries"
PUBLISHED_DATASETS_DIR = PUBLISHED_DIR / "datasets"
DEFAULT_GITHUB_REPO = "JLib271/HuMeta"
PUBLIC_DATASET_MAX_MB = 25
PROJECT_FILE_FORMAT = "humeta-project"
#: earlier project-file format names that still load
LEGACY_PROJECT_FILE_FORMATS = ("openedmetadata-project",)

