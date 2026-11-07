# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""KCWorks deposit lookup and the recommendation-issue comment, with a sample InvenioRDM record."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import check_recommendation as C  # noqa: E402
import kcworks_lookup as K  # noqa: E402

STEMED_ID = "11111111-2222-3333-4444-555555555555"
RECORD = {
    "id": "abcde-12345",
    "pids": {"doi": {"identifier": "10.17613/abcde-12345", "provider": "datacite"}},
    "links": {"self_html": "https://works.hcommons.org/records/abcde-12345"},
    "access": {"record": "public", "files": "public"},
    "files": {"enabled": True, "entries": {"inventory.pdf": {}, "manual.pdf": {}, "scoring.xlsx": {}}},
    "metadata": {"title": "Example Concept Inventory", "resource_type": {"id": "other", "title": {"en": "Other"}},
                 "creators": [{"person_or_org": {"name": "Doe, Jane"}}],
                 "rights": [{"id": "cc-by-4.0", "title": {"en": "Creative Commons Attribution 4.0 International"}}]},
    "parent": {"communities": {"ids": [STEMED_ID]}},
}


def fake_fetch(url):
    if url.endswith("/communities/stemedplus"):
        return {"id": STEMED_ID, "slug": "stemedplus"}
    if "/records/abcde-12345" in url:
        return RECORD
    if "/records?q=" in url:
        return {"hits": {"hits": [RECORD]}}
    raise AssertionError(url)


@pytest.mark.parametrize("link,expected", [
    ("https://works.hcommons.org/records/abcde-12345", ("abcde-12345", None)),
    ("https://works.hcommons.org/records/ABCDE-12345?preview=1", ("abcde-12345", None)),
    ("https://doi.org/10.17613/abcde-12345", (None, "10.17613/abcde-12345")),
    ("not a link", (None, None)),
])
def test_parse_link(link, expected):
    assert K.parse_link(link) == expected


def test_summary_reads_license_and_collection():
    s = K.summarize(K.find_record("https://doi.org/10.17613/abcde-12345", fake_fetch), fake_fetch)
    assert s["licenses"][0]["id"] == "cc-by-4.0" and s["in_collections"] == ["stemedplus"]
    assert s["files"] == ["inventory.pdf", "manual.pdf", "scoring.xlsx"]
    entry = K.commons_record(s, "instrument")
    assert entry == {"url": "https://doi.org/10.17613/abcde-12345", "kind": "instrument", "label": "Example Concept Inventory",
                     "doi": "10.17613/abcde-12345", "license": "Creative Commons Attribution 4.0 International",
                     "in_stemedplus_collection": True}


def test_other_dois_rejected():
    with pytest.raises(K.LookupError_):
        K.find_record("https://doi.org/10.1037/a0026659", fake_fetch)


def test_license_flags():
    assert K.is_open("cc-by-nc-nd-4.0") and not K.allows_adaptation("cc-by-nc-nd-4.0")
    assert K.allows_adaptation("cc0-1.0") and not K.is_open("arr")


def _body(link="", contents=("The instrument (questionnaire, test, protocol, or rubric)", "Manual or user guide"), holder=True):
    ticks = "\n".join(f"- [X] {c}" for c in contents) + "\n- [ ] A paper about it"
    return (f"### Instrument name (and acronym)\n\nExample CI\n\n### Link to the deposit on Knowledge Commons (KCWorks)\n\n"
            f"{link or '_No response_'}\n\n### What's in the deposit?\n\n{ticks}\n\n### Rights\n\n"
            f"- [{'X' if holder else ' '}] I hold the rights to what I deposited\n\n### How was it developed?\n\nNot sure\n")


def test_comment_with_deposit():
    text = C.build_comment(_body("https://works.hcommons.org/records/abcde-12345"), fake_fetch)
    assert C.MARKER in text and "Creative Commons Attribution 4.0" in text and "yes (stemedplus)" in text
    assert "item_text_basis" in text and '"deposited_by_rights_holder": true' in text
    assert "inventory.pdf, manual.pdf, scoring.xlsx" in text and '"instrument",\n    "manual"' in text


def test_comment_without_deposit_and_not_holder():
    assert "No deposit link was given" in C.build_comment(_body(), fake_fetch)
    text = C.build_comment(_body("https://works.hcommons.org/records/abcde-12345", holder=False), fake_fetch)
    assert "did not say they hold the rights" in text


def test_comment_bad_link():
    assert "Could not read the deposit link" in C.build_comment(_body("https://example.org/x"), fake_fetch)


def test_single_file_with_several_contents_is_flagged():
    import copy
    rec = copy.deepcopy(RECORD)
    rec["files"]["entries"] = {"everything.pdf": {}}

    def fetch(url):
        return rec if "/records/abcde-12345" in url else fake_fetch(url)
    text = C.build_comment(_body("https://works.hcommons.org/records/abcde-12345"), fetch)
    assert "Only one file is in the record" in text
