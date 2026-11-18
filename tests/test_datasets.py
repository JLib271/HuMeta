# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Studies link to datasets in the STEMEd+ Commons Library through HuMeta keywords and the published index."""
from __future__ import annotations

import io
import json

import pytest

from oem import datasets as D

RECORD = {
    "study": {
        "constructs": [
            {"construct_id": "conceptual_understanding", "instrument_id": "gci", "version_id": "gci-v4-2014"},
            {"construct_id": "self_efficacy", "instrument_id": None, "version_id": None},
            {"construct_id": "self_efficacy", "instrument_id": None, "version_id": None},
        ],
        "design": {"frameworks": ["sct"]},
        "discipline": ["anzsrc_3702"],
    },
    "education": {"education_levels": ["bachelors"]},
}


def ds(rid, **links):
    base = {"id": rid, "title": f"Dataset {rid}", "instruments": [], "constructs": [], "frameworks": [],
            "disciplines": [], "education_levels": []}
    base.update(links)
    return base


def test_linking_keywords_match_the_library_fetcher_format():
    assert D.linking_keywords(RECORD) == [
        "humeta:instrument:gci", "humeta:version:gci-v4-2014",
        "humeta:construct:conceptual_understanding", "humeta:construct:self_efficacy", "humeta:framework:sct"]
    assert D.linking_keywords(None) == []


def test_related_ranks_by_what_is_shared():
    index = {"datasets": [
        ds("theory-only", frameworks=["sct"]),
        ds("same-instrument", instruments=["gci"], constructs=["conceptual_understanding"], disciplines=["anzsrc_3702"]),
        ds("discipline-only", disciplines=["anzsrc_3702"], education_levels=["bachelors"]),
        ds("unrelated", instruments=["other"]),
    ]}
    matches = D.related(index, RECORD)
    assert [m.dataset["id"] for m in matches] == ["same-instrument", "theory-only"]
    assert matches[0].reasons == ["1 instrument", "1 construct", "1 discipline"]


def test_related_with_no_index_or_record():
    assert D.related(None, RECORD) == [] and D.related({"datasets": [ds("x", instruments=["gci"])]}, None) == []


def test_fetch_index_checks_the_format(monkeypatch):
    def opener(payload):
        return lambda req, timeout: io.BytesIO(json.dumps(payload).encode())
    monkeypatch.setattr(D.urllib.request, "urlopen", opener({"format": "humeta-dataset-index", "datasets": []}))
    assert D.fetch_index()["datasets"] == []
    monkeypatch.setattr(D.urllib.request, "urlopen", opener({"something": "else"}))
    with pytest.raises(ValueError):
        D.fetch_index()


def test_dataset_links_point_at_the_library_and_collection():
    assert D.dataset_page({"id": "abcde-12345"}) == "https://jlib271.github.io/humeta-library/datasets/abcde-12345/"
    assert D.DATA_DEPOSIT_URL.endswith("community=stemedplus-data")
