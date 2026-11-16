# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""The readable study profile deposited with humeta.json."""
import json
from pathlib import Path

import pytest

pytest.importorskip("reportlab")

from oem import profile, study_pdf  # noqa: E402
from oem.library import Library  # noqa: E402

EXAMPLES = Path(__file__).resolve().parents[1] / "standard" / "humeta" / "examples"


@pytest.mark.parametrize("name", ["climate-inventory-dataset", "online-discourse-dataset", "archival-letters-collection"])
def test_study_pdf_builds_for_examples(name):
    record = json.loads((EXAMPLES / f"{name}.json").read_text())
    pdf = study_pdf.study_pdf(record, Library.load(), profile.load())
    assert pdf.startswith(b"%PDF") and len(pdf) > 2000


def test_study_pdf_handles_a_new_record():
    p = profile.load()
    record = profile.empty_record(p, modules=("education",))
    record["resource"]["title"] = "Plan <draft> & notes"
    assert study_pdf.study_pdf(record, Library.load(), p).startswith(b"%PDF")
