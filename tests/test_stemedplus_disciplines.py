"""The shared STEMEd+ discipline list that the STEMEd+ Commons sites build from."""
import json
import re
from pathlib import Path

import jsonschema

BASE = Path(__file__).resolve().parent.parent / "standard" / "humeta"
DOC = json.loads((BASE / "stemedplus_disciplines.json").read_text())
SCHEMA = json.loads((BASE / "schema" / "stemedplus_disciplines.schema.json").read_text())
VOCAB = json.loads((BASE / "vocabularies.json").read_text())["vocabularies"]["discipline"]["terms"]


def _rule(d):
    pattern = r"\b(?:" + d["match"]["terms"] + r")\b"
    pattern += "".join(r"|\b(?-i:" + a + r")\b" for a in d["match"]["acronyms"])
    return re.compile(pattern, re.IGNORECASE)


def _term_ids():
    return {t["id"]: t for t in VOCAB}


def test_matches_schema():
    jsonschema.validate(DOC, SCHEMA)


def test_ids_and_labels_unique():
    ids = [d["id"] for d in DOC["disciplines"]]
    labels = [d["label"] for d in DOC["disciplines"]]
    assert len(ids) == len(set(ids))
    assert len(labels) == len(set(labels))


def test_humeta_disciplines_are_current_terms():
    terms = _term_ids()
    for d in DOC["disciplines"]:
        for t in d["humeta_disciplines"]:
            assert t in terms, (d["id"], t)
            assert not terms[t].get("deprecated"), (d["id"], t)


def test_patterns_compile_and_match_examples():
    rules = {d["id"]: _rule(d) for d in DOC["disciplines"]}
    examples = {
        "agriculture": "Assistant Professor of Agricultural Education",
        "bioscience": "Biology education research (BER) postdoc",
        "chemistry": "Chemistry Education Research",
        "earth_science": "Geoscience education",
        "engineering": "Engineering education",
        "health_education": "Nursing education",
        "learning_science": "Learning sciences",
        "mathematics": "Mathematics education",
        "physics": "PER group",
        "science_education": "Science teacher education",
    }
    for i, text in examples.items():
        assert rules[i].search(text), i
    assert not rules["physics"].search("$50 per year")
    assert not rules["health_education"].search("medical, dental and vision coverage")
