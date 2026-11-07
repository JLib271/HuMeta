# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""The instrument library speaks HuMeta: vocabularies, measurement evidence, and DataCite descriptions."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

from oem import instrument_metadata as IM
from oem import profile as P
from oem.library import Library

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import validate_library  # noqa: E402


@pytest.fixture(scope="module")
def lib():
    return Library.load()


@pytest.fixture(scope="module")
def p():
    return P.load()


def test_library_terms_are_current_humeta_terms(lib, p):
    for inst in lib.instruments.values():
        for field, vocab in (("education_levels", "education_level"), ("settings", "learning_environment"),
                             ("participants", "participant_role"), ("disciplines", "discipline")):
            for term in inst.get(field, []):
                assert term in p.active_ids(vocab), (inst["id"], field, term)
    for e in lib.evidence:
        s = e["sample"]
        assert s.get("education_level") or s.get("participants"), e["id"]
        for term in s.get("participants", []):
            assert term in p.active_ids("participant_role")


def test_validator_rejects_library_only_and_deprecated_terms(tmp_path):
    root = tmp_path / "library"
    shutil.copytree(ROOT / "library", root)
    path = root / "instruments" / "gci.json"
    rec = json.loads(path.read_text(encoding="utf-8"))
    rec["disciplines"] = ["geoscience"]          # deprecated
    rec["education_levels"] = ["undergraduate"]  # the library's old term
    path.write_text(json.dumps(rec), encoding="utf-8")
    assert validate_library.main(root) == 1


def test_every_type_has_a_data_collection_method(p):
    schema = json.loads((ROOT / "library" / "schema" / "instrument.schema.json").read_text(encoding="utf-8"))
    for t in schema["properties"]["instrument_type"]["enum"]:
        assert IM.DATA_COLLECTION_METHOD[t] in p.active_ids("data_collection_method")


def test_measurement_evidence_follows_the_rubric(lib):
    assert "fairness" in IM.measurement_evidence(lib, "climate-change-concept-inventory")  # DIF -> cultural validity
    assert IM.measurement_evidence(lib, "copus") == ["reliability"]                      # inter-rater, outside the rubric
    assert IM.measurement_evidence(lib, "class") == []
    alpha = next(e for e in lib.evidence if e["statistic"]["name"] == "cronbach_alpha")
    assert IM.record_evidence(lib, alpha) == ["reliability"]
    for cat in lib.rubric:
        assert cat["humeta_evidence"], cat["id"]


@pytest.mark.parametrize("iid", sorted(Library.load().instruments))
def test_datacite_description(lib, p, iid):
    d = IM.to_datacite_json(lib, iid, p)
    assert d["types"] == {"resourceTypeGeneral": "Text", "resourceType": d["types"]["resourceType"]}
    assert d["titles"][0]["title"] and d["creators"] and d["publisher"]["name"]
    assert len(d["publicationYear"]) == 4 and d["url"].endswith(f"instruments/{iid.replace('_', '-')}/")
    vocab_uris = [s["valueUri"] for s in d["subjects"] if s.get("valueUri", "").startswith(P.VOCAB_URI)]
    for uri in vocab_uris:  # every HuMeta subject points at a current term
        vocab, term = uri.removeprefix(P.VOCAB_URI).split(".", 1)
        assert term in p.active_ids(vocab), uri
    assert any(s.get("subjectScheme") == "HuMeta Data Collection Methods" for s in d["subjects"])


def test_datacite_links(lib, p):
    gci = IM.to_datacite_json(lib, "gci", p)
    rel = {(r["relatedIdentifier"], r["relationType"]) for r in gci["relatedIdentifiers"]}
    assert ("10.17613/wnm5z-00x75", "IsDescribedBy") in rel  # its KCWorks chapter
    assert any(r["rights"].startswith("Item text: CC BY-SA") for r in gci["rightsList"])
    assert {"Libarkin", "Anderson"} == {c["familyName"] for c in gci["creators"]}


def test_schema_org(lib, p):
    ld = IM.to_schema_org(lib, "mslq", p)
    assert ld["@type"] == "CreativeWork" and ld["alternateName"] == "MSLQ" and ld["author"]
    assert ld["additionalType"] == "https://schema.org/Survey"
