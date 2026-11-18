import json
from pathlib import Path

import pytest

from oem import ddi
from oem import metacode as M
from oem import plan as P
from oem.library import Library

EXAMPLES = Path(__file__).resolve().parents[1] / "standard" / "humeta" / "examples"


@pytest.fixture(scope="module")
def lib():
    return Library.load()


def sct_plan(lib):
    plan = P.empty_plan()
    plan["frameworks"] = ["sct"]
    plan["constructs"] = P.framework_constructs(lib, ["sct"])
    return P.normalize(plan)


def test_the_four_levels_follow_the_spec(lib):
    construct = M.construct_code(lib, {"id": "sct.outcome_expectations", "framework_id": "sct"})
    assert construct == "outcome_expectations_SCT"
    measure = M.join(construct, "Smith2017")
    item = M.join(measure, M.item_code(1, "People expect me to ... when I graduate"))
    assert item == "outcome_expectations_SCT_Smith2017_item1_PeopleExpectMeTo"
    assert M.join(item, M.target_code("Vote")) == item + "_Vote"
    assert M.level() == "construct"
    assert M.level(measure=True, item=True, target=True) == "construct_measure_item_target"


def test_library_instruments_are_first_author_and_year(lib):
    assert M.instrument_code(lib, "mslq") == "Pintrich1991"
    assert M.instrument_code(lib, "gci") == "Libarkin2005"
    assert M.instrument_code(lib, "copus") == "Smith2013"


def test_constructs_without_measures_still_get_codes(lib):
    book = P.build_codebook(lib, sct_plan(lib))
    assert len(book) == 0
    codes = {c["metadata_code"] for c in book.constructs}
    assert "outcome_expectations_SCT" in codes
    rows = [r for r in book.to_rows() if r["metadata_code"] == "outcome_expectations_SCT"]
    assert rows[0]["code_level"] == "construct" and rows[0]["name"] == ""
    assert "constructs_without_measures" in json.loads(book.to_json())


def test_measures_extend_the_construct_code_and_target_is_added(lib):
    plan = sct_plan(lib)
    plan["measures"] = [
        {"construct": "sct.outcome_expectations", "kind": "question", "text": "People expect me to vote.",
         "scale_id": "agree5", "target": "vote"},
        {"construct": "sct.self_efficacy", "kind": "instrument", "instrument_id": "mslq"},
    ]
    book = P.build_codebook(lib, plan)
    codes = {v.metadata_code: v for v in book.variables}
    assert "outcome_expectations_SCT_Own_item1_PeopleExpectMeTo_Vote" in codes
    assert codes["outcome_expectations_SCT_Own_item1_PeopleExpectMeTo_Vote"].code_level == \
        "construct_measure_item_target"
    assert any(c.startswith("self_efficacy_SCT_Pintrich1991") for c in codes)
    assert "outcome_expectations_SCT" not in {c["metadata_code"] for c in book.constructs}


def test_items_from_the_library_get_item_codes(lib):
    plan = P.empty_plan()
    plan["constructs"] = [{"id": "own.understanding", "label": "Understanding", "framework_id": None,
                           "shared_construct_id": "conceptual_understanding", "definition": ""}]
    plan["measures"] = [{"construct": "own.understanding", "kind": "instrument", "instrument_id": "gci"}]
    variables = P.build_codebook(lib, P.normalize(plan)).variables
    assert variables and all(v.metadata_code.startswith("conceptual_understanding_Libarkin2005_item")
                             for v in variables)


def test_standard_variables_and_ddi_carry_the_code(lib):
    plan = sct_plan(lib)
    plan["standard_variables"] = ["gender_identity"]
    plan["measures"] = [{"construct": "sct.outcome_expectations", "kind": "question", "text": "People expect me to vote.",
                         "scale_id": "agree5"}]
    book = P.build_codebook(lib, plan)
    assert {v.metadata_code for v in book.variables if v.standard_variable} == {"gender_identity"}
    record = json.loads((EXAMPLES / "climate-inventory-dataset.json").read_text())
    xml = ddi.to_ddi_codebook_xml(record, plan, lib)
    assert ">outcome_expectations_SCT_Own_item1_PeopleExpectMeTo<" in xml
    assert ddi.METADATA_CODE_VOCAB in xml


def test_fixed_library_codes_win_over_the_citation(lib, monkeypatch):
    inst = dict(lib.instruments["mslq"], metadata_code="Pintrich1991a")
    monkeypatch.setitem(lib.instruments, "mslq", inst)
    assert M.instrument_code(lib, "mslq") == "Pintrich1991a"


def test_search_finds_instruments_and_subscales(lib):
    hits = P.search_instruments(lib, "mslq efficacy")
    assert [(h["instrument_id"], h["dimension_id"] is None) for h in hits][0] == ("mslq", True)
    assert any("Self-Efficacy" in h["part"] for h in hits) and len(hits) == 2
    assert {h["instrument_id"] for h in P.search_instruments(lib, "Libarkin")} == {"gci", "climate-change-concept-inventory"}
    assert {h["instrument_id"] for h in P.search_instruments(lib, "belonging")} >= {"math-sense-of-belonging"}
    assert P.search_instruments(lib, "Pintrich1991")[0]["instrument_id"] == "mslq"
    assert P.search_instruments(lib, "") == [] and P.search_instruments(lib, "zzzz") == []


def test_dois_are_normalized():
    assert P.normalize_doi("https://doi.org/10.1037/a0026659") == "10.1037/a0026659"
    assert P.normalize_doi("doi: 10.1037/a0026659") == "10.1037/a0026659"
    assert P.normalize_doi("not-a-doi") == ""
    assert M.author_year("Smith et al. (2017)") == "Smith2017" and M.author_year("Smith 2017") == "Smith2017"
    assert M.author_year("Smith") == ""


def test_published_instruments_not_in_the_library(lib):
    plan = sct_plan(lib)
    plan["measures"] = [P.published_measure("sct.self_efficacy", "Science Self-Efficacy Scale", "Smith et al. (2017)",
                                            "https://doi.org/10.1002/tea.21234", "Physics")]
    assert P.problems(lib, plan) == []
    [v] = P.build_codebook(lib, plan).variables
    assert v.metadata_code == "self_efficacy_SCT_Smith2017_Physics" and v.code_level == "construct_measure_target"
    assert v.name == "science_self_efficacy_score" and "https://doi.org/10.1002/tea.21234" in v.notes
    # only a DOI: still valid, code from the name
    plan["measures"] = [P.published_measure("sct.self_efficacy", "Science Self-Efficacy Scale", "", "10.1002/tea.21234")]
    assert P.problems(lib, plan) == []
    assert P.build_codebook(lib, plan).variables[0].metadata_code == "self_efficacy_SCT_ScienceSelfEfficacyScale"
    # neither author-year nor DOI
    plan["measures"] = [P.published_measure("sct.self_efficacy", "Science Self-Efficacy Scale")]
    assert P.problems(lib, plan)


def test_published_instrument_dois_go_to_related_works(lib):
    plan = sct_plan(lib)
    plan["measures"] = [P.published_measure("sct.self_efficacy", "Science Self-Efficacy Scale", "Smith 2017", "10.1002/TEA.21234"),
                        P.published_measure("sct.outcome_expectations", "Science Self-Efficacy Scale", "Smith 2017",
                                            "https://doi.org/10.1002/tea.21234"),
                        P.published_measure("sct.outcome_expectations", "No DOI Scale", "Lee 2020")]
    assert [d["doi"] for d in P.published_dois(plan)] == ["10.1002/TEA.21234"]
    existing = [{"identifier": "10.1/x", "identifier_type": "DOI", "relation": "IsSupplementTo"}]
    merged, added = P.merge_related_dois(existing, plan)
    assert added == 1 and merged[0] == existing[0]
    assert merged[1] == {"identifier": "10.1002/TEA.21234", "identifier_type": "DOI", "relation": "References"}
    assert P.merge_related_dois(merged, plan) == (merged, 0)
