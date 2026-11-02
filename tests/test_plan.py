import json

import pytest

from oem import naming
from oem import plan as P
from oem import profile
from oem.library import Library


@pytest.fixture(scope="module")
def lib():
    return Library.load()


def sdt_plan(lib):
    plan = P.empty_plan()
    plan["frameworks"] = ["sdt"]
    plan["constructs"] = P.framework_constructs(lib, ["sdt"]) + [
        {"id": "own.curiosity", "label": "Curiosity", "framework_id": None, "shared_construct_id": None, "definition": ""}]
    plan["relationships"] = P.default_relationships(lib, ["sdt"], {c["id"] for c in plan["constructs"]})
    plan["measures"] = [P.as_measure(c) for c in P.candidate_measures(lib, plan["constructs"])] + [
        {"construct": "sdt.autonomy", "kind": "question", "text": "I can choose how I learn.", "scale_id": "agree5"},
        {"construct": "own.curiosity", "kind": "code", "label": "Asks a question", "text": "Asks an unprompted question."},
    ]
    return P.normalize(plan)


def test_frameworks_supply_constructs_linked_to_shared_constructs(lib):
    constructs = {c["id"]: c for c in P.framework_constructs(lib, ["tpb", "sdt"])}
    assert constructs["tpb.subjective_norms"]["shared_construct_id"] == "subjective_norm"
    assert constructs["sdt.competence"]["shared_construct_id"] == "self_efficacy"
    assert {f["kind"] for f in lib.frameworks.values()} == {"theory", "lens", "own", "exploratory"}


def test_default_relationships_follow_the_theory_and_drop_removed_constructs(lib):
    kept = {c["id"] for c in P.framework_constructs(lib, ["tpb"])} - {"tpb.behavior"}
    rels = P.default_relationships(lib, ["tpb"], kept)
    assert {"from": "tpb.subjective_norms", "to": "tpb.behavioral_intention",
            "relationship": "Supports intention", "hypothesis": ""} in rels
    assert all("tpb.behavior" not in (r["from"], r["to"]) for r in rels)


def test_candidates_show_what_each_part_measures_and_mapping_status(lib):
    rows = P.candidate_measures(lib, P.framework_constructs(lib, ["sdt"]))
    mslq = next(r for r in rows if r["instrument_id"] == "mslq")
    assert mslq["construct"] == "sdt.competence" and mslq["dimension_id"] == "self-efficacy"
    assert mslq["measures"] == ["Self-efficacy"] and mslq["mapping_status"] == "provisional"
    assert set(P.as_measure(mslq)) == set(P.MEASURE_KEYS)


def test_climate_inventory_measures_climate_change_conceptual_understanding(lib):
    construct = {"id": "own.climate", "label": "Climate understanding", "framework_id": None,
                 "shared_construct_id": "climate_change_conceptual_understanding", "definition": ""}
    rows = P.candidate_measures(lib, [construct])
    assert [r["instrument_id"] for r in rows] == ["climate-change-concept-inventory"]
    assert lib.constructs["climate_change_conceptual_understanding"]["broader"] == "conceptual_understanding"


def test_codebook_from_framework_to_variables(lib):
    plan = sdt_plan(lib)
    plan["standard_variables"] = ["participant_id"]
    plan["timepoints"] = ["pre", "post"]
    assert P.problems(lib, plan) == []
    book = P.build_codebook(lib, plan)
    names = book.names()
    assert names[0] == "participant_id"
    assert {"mslq_self_efficacy_pre", "mslq_self_efficacy_post", "autonomy_01_pre", "code_asks_a_question_post"} <= set(names)
    assert all(naming.is_valid(n) for n in names) and len(names) == len(set(names))
    by_name = {v.name: v for v in book.variables}
    assert by_name["autonomy_01_pre"].question == "I can choose how I learn." and by_name["autonomy_01_pre"].scale_id == "agree5"
    assert "Measures construct: Curiosity" in by_name["code_asks_a_question_pre"].notes


def test_alignment_table(lib):
    rows = P.alignment(lib, sdt_plan(lib))
    competence = [r for r in rows if r["Construct"] == "Competence"]
    assert competence and all(r["Shared construct"] == "Self-efficacy" for r in competence)
    assert any(r["Mapping status"].startswith("Provisional") for r in competence)
    assert next(r for r in rows if r["Construct"] == "Curiosity")["Mapping status"] == "Researcher-defined"


def test_instruments_with_item_files_expand_to_items(lib):
    plan = P.empty_plan()
    plan["constructs"] = [{"id": "own.understanding", "label": "Understanding", "framework_id": None,
                           "shared_construct_id": "conceptual_understanding", "definition": ""}]
    plan["measures"] = [P.as_measure(c) for c in P.candidate_measures(lib, plan["constructs"])]
    names = P.build_codebook(lib, plan).names()
    assert any(n.startswith("gci_q") for n in names)


def test_manifest_and_constructs_for_later_modules(lib):
    plan = sdt_plan(lib)
    rows = {r["Variable_Label"]: r for r in P.manifest(lib, plan)}
    assert set(P.MANIFEST_FIELDS) <= set(rows["Competence"])
    assert rows["Competence"]["Framework_Source"] == "Self-Determination Theory (SDT)"
    assert rows["Curiosity"]["Framework_Source"] == "Researcher-defined"
    assert P.shared_construct_ids(plan) == ["self_efficacy", "sense_of_belonging", "interest"]
    assert profile.suggest_constructs(lib, plan) == ["self_efficacy", "sense_of_belonging", "interest"]
    linked = {c["construct_id"]: c for c in P.profile_constructs(plan)}
    assert linked["self_efficacy"]["instrument_id"] in {"class", "mslq"}


def test_problems_are_reported(lib):
    plan = sdt_plan(lib)
    plan["measures"].append({"construct": "nope", "kind": "question", "text": "x", "name": "Bad Name"})
    plan["relationships"].append({"from": "sdt.autonomy", "to": "nowhere", "relationship": ""})
    issues = " ".join(P.problems(lib, plan))
    assert "choose one of the plan's constructs" in issues and "Bad Name" in issues and "both ends" in issues


def test_diagram_and_summary(lib):
    plan = sdt_plan(lib)
    dot = P.diagram_dot(lib, plan)
    assert dot.startswith("digraph") and '"sdt.autonomy" -> "sdt.intrinsic_motivation"' in dot
    shared = P.summary(lib, plan)
    assert shared["selected_theories"] == ["Self-Determination Theory (SDT)"]
    assert "I can choose how I learn." not in json.dumps(shared)  # item text is never published


def test_older_plans_are_migrated(lib):
    v1 = {"schema_version": 1, "selected_theories": ["Theory of Planned Behavior (TPB)"],
          "variables": [{"Variable_ID": "x", "Concept_Construct": "Subjective Norms"}],
          "custom_variables": [{"Concept_Construct": "Curiosity", "Item_Text": "I like asking questions."}]}
    plan = P.normalize(v1, lib)
    assert plan["schema_version"] == P.PLAN_VERSION and plan["frameworks"] == ["tpb"]
    assert {c["id"] for c in plan["constructs"]} == {"tpb.subjective_norms", "own.curiosity"}
    assert plan["measures"][0]["text"] == "I like asking questions."
    v2 = {"schema_version": 2, "frameworks": ["sdt"], "behavior": "x",
          "concepts": [{"id": "sdt.competence", "label": "Competence", "framework_id": "sdt", "construct_id": "self_efficacy"}],
          "measures": [{"concept_id": "sdt.competence", "kind": "instrument", "instrument_id": "mslq",
                        "dimension_id": "self-efficacy"}]}
    plan = P.normalize(v2, lib)
    assert plan["constructs"][0]["shared_construct_id"] == "self_efficacy"
    assert plan["measures"][0]["construct"] == "sdt.competence" and "behavior" not in plan
    assert P.problems(lib, plan) == []


def test_browse_frameworks_filters_and_search():
    from oem.library import Library
    lib = Library.load()
    every = P.browse_frameworks(lib)
    assert len(every) == len(lib.frameworks)
    assert [lib.frameworks[f]["kind"] for f in every][-2:] == ["own", "exploratory"]  # always offered, last
    humanities = P.browse_frameworks(lib, field="humanities", kind="lens")
    assert "narratology" in humanities and "tpb" not in humanities and "own_framework" in humanities
    assert "civic_voluntarism" in P.browse_frameworks(lib, discipline="political_science")
    assert P.browse_frameworks(lib, query="Sweller")[0] == "cognitive_load"  # author names are searchable
    assert "community_of_inquiry" in P.browse_frameworks(lib, query="teaching presence")  # and construct names


def test_every_draft_framework_names_a_source_and_disciplines():
    from oem.library import Library
    for fw in Library.load().frameworks.values():
        if fw.get("status") == "draft":
            assert fw.get("citation") and fw.get("disciplines"), fw["id"]
            assert fw["kind"] == "lens" or (fw["constructs"] and fw["paths"]), fw["id"]
