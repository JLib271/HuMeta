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
    plan["concepts"] = P.framework_concepts(lib, ["sdt"]) + [
        {"id": "own.curiosity", "label": "Curiosity", "framework_id": None, "construct_id": None, "definition": ""}]
    plan["relationships"] = P.default_relationships(lib, ["sdt"], {c["id"] for c in plan["concepts"]})
    plan["measures"] = P.suggest_measures(lib, plan["concepts"]) + [
        {"concept_id": "sdt.autonomy", "kind": "question", "text": "I can choose how I learn.", "scale_id": "agree5"},
        {"concept_id": "own.curiosity", "kind": "code", "label": "Asks a question", "text": "Asks an unprompted question."},
    ]
    return P.normalize(plan)


def test_frameworks_supply_concepts_linked_to_constructs(lib):
    concepts = {c["id"]: c for c in P.framework_concepts(lib, ["tpb", "sdt"])}
    assert concepts["tpb.subjective_norms"]["construct_id"] == "subjective_norm"
    assert concepts["sdt.competence"]["construct_id"] == "self_efficacy"
    assert {f["kind"] for f in lib.frameworks.values()} == {"theory", "lens", "own", "exploratory"}


def test_default_relationships_follow_the_theory_and_drop_removed_concepts(lib):
    kept = {c["id"] for c in P.framework_concepts(lib, ["tpb"])} - {"tpb.behavior"}
    rels = P.default_relationships(lib, ["tpb"], kept)
    assert {"from": "tpb.subjective_norms", "to": "tpb.behavioral_intention",
            "relationship": "Supports intention", "hypothesis": ""} in rels
    assert all("tpb.behavior" not in (r["from"], r["to"]) for r in rels)


def test_library_suggestions_use_subscales(lib):
    rows = P.suggest_measures(lib, P.framework_concepts(lib, ["sdt"]))
    assert {"concept_id": "sdt.competence", "instrument_id": "mslq", "dimension_id": "self-efficacy"}.items() <= next(
        r for r in rows if r["instrument_id"] == "mslq").items()


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
    assert "Measures concept: Curiosity" in by_name["code_asks_a_question_pre"].notes


def test_instruments_with_item_files_expand_to_items(lib):
    plan = P.empty_plan()
    plan["concepts"] = [{"id": "own.understanding", "label": "Understanding", "framework_id": None,
                         "construct_id": "conceptual_understanding", "definition": ""}]
    plan["measures"] = P.suggest_measures(lib, plan["concepts"])
    names = P.build_codebook(lib, plan).names()
    assert any(n.startswith("gci_q") for n in names)
    assert any(n.startswith(lib.prefix("climate-change-concept-inventory") + "_") for n in names)


def test_manifest_and_constructs_for_later_modules(lib):
    plan = sdt_plan(lib)
    rows = {r["Variable_Label"]: r for r in P.manifest(lib, plan)}
    assert set(P.MANIFEST_FIELDS) <= set(rows["Competence"])
    assert rows["Competence"]["Framework_Source"] == "Self-Determination Theory (SDT)"
    assert rows["Curiosity"]["Framework_Source"] == "Researcher-defined"
    assert P.construct_ids(plan) == ["self_efficacy", "sense_of_belonging", "interest"]
    assert profile.suggest_constructs(lib, plan) == ["self_efficacy", "sense_of_belonging", "interest"]
    linked = {c["construct_id"]: c for c in P.profile_constructs(plan)}
    assert linked["self_efficacy"]["instrument_id"] in {"class", "mslq"}


def test_problems_are_reported(lib):
    plan = sdt_plan(lib)
    plan["measures"].append({"concept_id": "nope", "kind": "question", "text": "x", "name": "Bad Name"})
    plan["relationships"].append({"from": "sdt.autonomy", "to": "nowhere", "relationship": ""})
    issues = " ".join(P.problems(lib, plan))
    assert "choose one of the plan's concepts" in issues and "Bad Name" in issues and "both ends" in issues


def test_diagram_and_summary(lib):
    plan = sdt_plan(lib)
    dot = P.diagram_dot(lib, plan)
    assert dot.startswith("digraph") and '"sdt.autonomy" -> "sdt.intrinsic_motivation"' in dot
    shared = P.summary(lib, plan)
    assert shared["selected_theories"] == ["Self-Determination Theory (SDT)"]
    assert "I can choose how I learn." not in json.dumps(shared)  # item text is never published


def test_old_plans_are_migrated(lib):
    old = {"schema_version": 1, "selected_theories": ["Theory of Planned Behavior (TPB)"],
           "variables": [{"Variable_ID": "x", "Concept_Construct": "Subjective Norms"}],
           "custom_variables": [{"Concept_Construct": "Curiosity", "Item_Text": "I like asking questions."}]}
    plan = P.normalize(old, lib)
    assert plan["schema_version"] == 2 and plan["frameworks"] == ["tpb"]
    assert {c["id"] for c in plan["concepts"]} == {"tpb.subjective_norms", "own.curiosity"}
    assert plan["measures"][0]["text"] == "I like asking questions."
