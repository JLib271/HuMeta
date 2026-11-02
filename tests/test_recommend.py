import json

from oem import recommend as R
from oem.library import Library

LIB = Library.load()


def test_framework_recommendation_lists_constructs_and_paths():
    rec = R.framework_recommendation(
        name="Situated Expectancy-Value Theory", kind="theory", description="Updated EVT.",
        citation="Eccles, J. S., & Wigfield, A. (2020). Contemporary Educational Psychology, 61, 101859.",
        doi="https://doi.org/10.1016/j.cedpsych.2020.101859",
        constructs=[{"construct": "Expectancy", "definition": "belief about success", "shared_construct_id": "self_efficacy",
                     "instruments": "MSLQ self-efficacy subscale"},
                    {"construct": "Task value"}, {"construct": float("nan")}],
        relationships="Expectancy -> Task value: relates to")
    assert rec["doi"] == "10.1016/j.cedpsych.2020.101859"
    assert [c["label"] for c in rec["constructs"]] == ["Expectancy", "Task value"]
    assert rec["constructs"][0] == {"label": "Expectancy", "definition": "belief about success",
                                    "shared_construct_id": "self_efficacy", "instruments": "MSLQ self-efficacy subscale"}
    assert rec["relationships"] == [{"from": "Expectancy", "to": "Task value", "relationship": "relates to"}]
    assert R.framework_problems(rec, LIB) == []
    path, text = R.file_for(rec)
    assert path.startswith("suggestions/frameworks/situated-expectancy-value-theory-") and path.endswith(".json")
    assert json.loads(text)["recommendation"] == "framework"
    text = R.pr_description(rec)
    assert "Maintainer checklist" in text and "| Expectancy | belief about success | self_efficacy |" in text


def test_framework_problems():
    rec = R.framework_recommendation(name="Self-Determination Theory (SDT)", kind="theory", description="", citation="",
                                     relationships="A -> B: x")
    issues = " ".join(R.framework_problems(rec, LIB))
    assert "already in the list" in issues and "citation" in issues and "constructs" in issues and "A -> B" in issues


def test_instrument_recommendation_maps_each_part_to_a_construct():
    rec = R.instrument_recommendation(
        name="Science Identity Scale", citation="Author (2020). Journal.", access="open_download",
        relationship="developer", item_text_permission=True,
        alignment=[{"part": "Recognition", "items": "1-4", "shared_construct_id": "disciplinary_identity",
                    "theory_construct": "Science Identity Model: Recognition"},
                   {"part": "Interest", "items": "5-8", "other_construct": "Science interest"},
                   {"part": None, "items": float("nan")}])
    assert R.instrument_problems(rec, LIB) == []
    assert [r["part"] for r in rec["alignment"]] == ["Recognition", "Interest"]
    assert rec["developer_offers_item_text"] is True
    assert R.file_for(rec)[0].startswith("suggestions/instruments/")
    text = R.pr_description(rec)
    assert "developer offers to share item text" in text
    assert "| Recognition | 1-4 | disciplinary_identity |  | Science Identity Model: Recognition |" in text
    assert "governance committee" in text


def test_instrument_problems():
    dup = R.instrument_recommendation(name="Motivated Strategies for Learning Questionnaire", citation="x",
                                      alignment=[{"part": "Whole instrument", "shared_construct_id": "nope"}],
                                      url="www.example.org")
    issues = " ".join(R.instrument_problems(dup, LIB))
    assert "already in the library" in issues and "Unknown constructs" in issues and "http" in issues
    missing = R.instrument_recommendation(name="X", citation="y", alignment=[{"part": "Whole instrument"}])
    assert "which construct it measures" in " ".join(R.instrument_problems(missing, LIB))
    empty = R.instrument_recommendation(name="X", citation="y", alignment=[])
    assert "alignment table" in " ".join(R.instrument_problems(empty, LIB))
    user = R.instrument_recommendation(name="X", citation="y", relationship="user", item_text_permission=True,
                                       alignment=[{"part": "Whole instrument", "shared_construct_id": "interest"}])
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
