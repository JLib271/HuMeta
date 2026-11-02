import json

from oem import recommend as R
from oem.library import Library

LIB = Library.load()


def test_framework_recommendation_parses_concepts_and_paths():
    rec = R.framework_recommendation(
        name="Situated Expectancy-Value Theory", kind="theory", description="Updated EVT.",
        citation="Eccles, J. S., & Wigfield, A. (2020). Contemporary Educational Psychology, 61, 101859.",
        doi="https://doi.org/10.1016/j.cedpsych.2020.101859",
        concepts="Expectancy: belief about success\nTask value\n- Cost", relationships="Expectancy -> Task value: relates to")
    assert rec["doi"] == "10.1016/j.cedpsych.2020.101859"
    assert [c["label"] for c in rec["concepts"]] == ["Expectancy", "Task value", "Cost"]
    assert rec["concepts"][0]["definition"] == "belief about success"
    assert rec["relationships"] == [{"from": "Expectancy", "to": "Task value", "relationship": "relates to"}]
    assert R.framework_problems(rec, LIB) == []
    path, text = R.file_for(rec)
    assert path.startswith("suggestions/frameworks/situated-expectancy-value-theory-") and path.endswith(".json")
    assert json.loads(text)["recommendation"] == "framework"
    assert "Maintainer checklist" in R.pr_description(rec)


def test_framework_problems():
    rec = R.framework_recommendation(name="Self-Determination Theory (SDT)", kind="theory", description="", citation="",
                                     relationships="A -> B: x")
    issues = " ".join(R.framework_problems(rec, LIB))
    assert "already in the list" in issues and "citation" in issues and "concepts" in issues and "A -> B" in issues


def test_instrument_recommendation_and_checks():
    rec = R.instrument_recommendation(name="Science Identity Scale", citation="Author (2020). Journal.",
                                      construct_ids=["disciplinary_identity"], access="open_download",
                                      relationship="developer", item_text_permission=True,
                                      subscales="Recognition: being seen as a science person")
    assert R.instrument_problems(rec, LIB) == []
    assert rec["developer_offers_item_text"] is True and rec["subscales"][0]["label"] == "Recognition"
    assert R.file_for(rec)[0].startswith("suggestions/instruments/")
    assert "developer offers to share item text" in R.pr_description(rec)
    dup = R.instrument_recommendation(name="Motivated Strategies for Learning Questionnaire", citation="x",
                                      construct_ids=["nope"], url="www.example.org")
    issues = " ".join(R.instrument_problems(dup, LIB))
    assert "already in the library" in issues and "Unknown constructs" in issues and "http" in issues
    user = R.instrument_recommendation(name="X", citation="y", construct_ids=["interest"], relationship="user",
                                       item_text_permission=True)
    assert user["developer_offers_item_text"] is False  # only developers can offer item text


def test_corrections():
    rec = R.correction(target_kind="framework", target_id="sdt", change="Add the concept 'Amotivation'.")
    assert R.correction_problems(rec) == [] and R.file_for(rec)[0].startswith("suggestions/corrections/")
    assert R.correction_problems(R.correction(target_kind="framework", target_id="", change="")) != []


def test_suggestion_folders_are_allowed_for_pull_requests():
    import ast
    import pathlib
    source = pathlib.Path("oem/app/common.py").read_text()
    allowed = next(ast.literal_eval(node.value) for node in ast.walk(ast.parse(source))
                   if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "ALLOWED_PR_FOLDERS")
    assert set(R.FOLDERS.values()) <= set(allowed)
