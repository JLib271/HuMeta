# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Evidence profiles against the reliability and validity rubric."""

from __future__ import annotations

import copy

import pytest

from oem import evidence as EV
from oem.library import Library


@pytest.fixture(scope="module")
def lib():
    return Library.load()


def _cat(prof, cid):
    return next(c for c in prof.categories if c.id == cid)


def _crit(prof, cid, letter):
    return next(c for c in _cat(prof, cid).criteria if c.id == letter)


def test_rubric_loaded(lib):
    assert [c["numeral"] for c in lib.rubric] == ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"]


def test_guide_values_are_shown_not_judged(lib):
    prof = EV.profile(lib, "mslq")
    assert _crit(prof, "item_reliability", "A").status == "met"
    b = _crit(prof, "item_reliability", "B")
    assert b.status == "met" and b.detail == "15 values, 0.52 to 0.93; guide > 0.7"
    assert not any("below" in f for f in prof.flags)


def test_types_and_tags_map_to_criteria(lib):
    prof = EV.profile(lib, "math-sense-of-belonging")
    assert _crit(prof, "forms_reliability", "C").status == "met"       # test-retest
    assert _crit(prof, "scale_analysis", "A").status == "met"          # factor structure
    assert _crit(prof, "scale_analysis", "B").status == "met"          # tagged: loadings > .32
    assert _crit(prof, "criterion_construct", "C").status == "met"     # relations to other variables
    assert prof.samples >= 3 and "multi_sample" in prof.tags


def test_item_writing_applies_by_format(lib):
    likert = EV.profile(lib, "mslq")
    assert _cat(likert, "likert_item_writing").applies and not _cat(likert, "mc_item_writing").applies
    mc = EV.profile(lib, "gci")
    assert _cat(mc, "mc_item_writing").applies and not _cat(mc, "likert_item_writing").applies
    obs = EV.profile(lib, "copus")
    assert not _cat(obs, "mc_item_writing").applies and not _cat(obs, "likert_item_writing").applies


def test_inter_rater_is_reliability_outside_the_rubric(lib):
    prof = EV.profile(lib, "copus")
    assert prof.other_reliability and "reliability" in prof.tags
    assert any("inter-rater" in f for f in prof.flags)


def test_rubric_review_and_independence(lib):
    lib2 = copy.deepcopy(lib)
    inst = lib2.instruments["mslq"]
    inst["rubric_review"] = {"pre_item_content": {"criteria": ["G"], "source": "a test source"}}
    for e in lib2.evidence:
        if e["instrument_id"] == "mslq":
            e["source"]["independent"] = True
    prof = EV.profile(lib2, "mslq")
    assert _crit(prof, "pre_item_content", "G").status == "met"
    assert prof.coverage("validity")[0] == 1
    assert prof.independent == 15 and "independent" in prof.tags
    assert not any("developers" in f for f in prof.flags)


def test_range_shows_lowest_value(lib):
    lib2 = copy.deepcopy(lib)
    e = next(e for e in lib2.evidence if e["instrument_id"] == "gci")
    e["statistic"].update({"min": 0.85, "max": 0.99})
    d = _crit(EV.profile(lib2, "gci"), "item_reliability", "D")
    assert d.status == "met" and d.detail.startswith("0.85")


def test_no_evidence(lib):
    prof = EV.profile(lib, "class")
    assert prof.flags == ["No reliability or validity evidence is recorded yet."]
    assert EV.summary_line(prof).startswith("Reliability 0/3 · Validity 0/6")


def test_gci_review_counts(lib):
    prof = EV.profile(lib, "gci")
    assert _crit(prof, "communication", "A").status == "met"
    assert prof.coverage("validity")[0] >= 4
