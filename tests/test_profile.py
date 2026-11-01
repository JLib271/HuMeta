import copy
import json
import os
import urllib.request
from pathlib import Path

import pytest

from oem import profile, vocab
from oem.library import Library

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "standard" / "stemed-ap"
EXAMPLE = json.loads((BASE / "examples" / "climate-inventory-dataset.json").read_text())


@pytest.fixture(scope="module")
def p():
    return profile.load()


@pytest.fixture(scope="module")
def lib():
    return Library.load()


def rules_fired(record, lib):
    return {i.rule for i in profile.validate(record, lib) if i.rule}


def test_example_is_valid(lib):
    assert profile.validate(EXAMPLE, lib) == []


def test_generated_schema_is_in_sync(p):
    on_disk = json.loads((BASE / "schema" / "stemed-ap-record.schema.json").read_text())
    assert on_disk == profile.json_schema(p), "run python scripts/build_profile_artifacts.py"


def test_module1_labels_exist_in_app(p):
    """Every Module 1 answer used for pre-filling must be a real option in the app."""
    source = (ROOT / "oem" / "app" / "pages" / "study_registry.py").read_text()
    known = set(vocab.EDUCATION_LEVEL_OPTIONS + vocab.UNDERGRADUATE_LEVEL_OPTIONS + vocab.PROGRAM_TYPE_OPTIONS)
    for vocab_id, v in p.vocabularies.items():
        for term in v["terms"]:
            for label in term.get("module1", []):
                assert label in known or f'"{label}"' in source, f"{vocab_id}.{term['id']}: {label!r} not in Module 1"


def test_term_ids_unique(p):
    for vocab_id, v in p.vocabularies.items():
        ids = [t["id"] for t in v["terms"]]
        assert len(ids) == len(set(ids)), vocab_id


def test_every_eric_descriptor_has_a_status(p, lib):
    status = p.eric_status
    known = set(status["verified"]) | set(status["unverified"])
    used = {d for v in p.vocabularies.values() for t in v["terms"] for d in t.get("eric", [])}
    used |= {d for c in lib.constructs.values() for d in c.get("eric", [])}
    assert used <= known, f"descriptors without a verification status: {sorted(used - known)}"
    assert not used & set(status["rejected"]), "a rejected descriptor is still mapped"


def test_eric_export_skips_unverified(lib):
    verified_only = profile.eric_descriptors(EXAMPLE, lib)
    everything = profile.eric_descriptors(EXAMPLE, lib, include_unverified=True)
    assert "Surveys" in everything and "Surveys" not in verified_only
    assert "Climate" in verified_only


@pytest.mark.parametrize("change, rule", [
    ({"identifiability": "identifiable"}, "R4"),
    ({"consent_for_sharing": "restricted_sharing"}, "R5"),
    ({"human_subjects_review": "pending"}, "R6"),
])
def test_open_access_rules(lib, change, rule):
    record = copy.deepcopy(EXAMPLE)
    record["stemed"]["ethics"].update(change)
    assert rule in rules_fired(record, lib)


def test_constructs_and_design_required_for_datasets(lib):
    record = copy.deepcopy(EXAMPLE)
    record["stemed"]["constructs"] = []
    record["stemed"]["evidence"]["study_designs"] = []
    assert {"R1", "R2"} <= rules_fired(record, lib)


def test_instrument_needs_measurement_evidence(lib):
    record = copy.deepcopy(EXAMPLE)
    record["resource"]["resource_type"] = "Instrument"
    record["stemed"]["evidence"]["measurement_evidence"] = []
    assert "R3" in rules_fired(record, lib)


def test_care_rules(lib):
    record = copy.deepcopy(EXAMPLE)
    record["stemed"]["care"].update({"indigenous_data": "yes", "governance": "none", "statement": None})
    assert {"R7", "R8"} <= rules_fired(record, lib)
    record["stemed"]["care"].update({"governance": "community_agreement", "statement": "Co-designed with the Nation's education department."})
    assert not {"R7", "R8"} & rules_fired(record, lib)


def test_care_prompt_for_tribal_college(lib):
    record = copy.deepcopy(EXAMPLE)
    record["stemed"]["context"]["institution_types"] = ["tribal_college"]
    assert "R11" in rules_fired(record, lib)


def test_education_records_warning_is_not_an_error(lib):
    record = copy.deepcopy(EXAMPLE)
    record["stemed"]["ethics"]["sensitivity_flags"] = ["education_records"]
    issues = profile.validate(record, lib)
    assert [i.rule for i in issues] == ["R9"] and issues[0].severity == "warning"


def test_from_project_prefills_module1_and_module2(lib):
    project = {
        "study": {
            "study_title": "Belonging in intro chemistry",
            "study_description": json.dumps({"description": "A study.", "metadata": {
                "authors": [{"name": "A. Researcher", "orcid": "https://orcid.org/0000-0002-1825-0097"}],
                "institution": "Example University", "language": "English (en)",
                "subject_keywords": "chemistry, belonging", "content_domain": "General chemistry",
                "participant_populations": ["Students / learners"],
                "grade_level": ["Postsecondary undergraduate"],
                "undergraduate_level": ["Entry-level / introductory (typically first-year)"],
                "study_settings": ["College, university, or other postsecondary institution"],
                "locale_setting": "Rural", "state_origin": "MI",
                "time_method": "Longitudinal: Cohort Study / Repeated Measures",
                "ethics_review_status": "Approved", "consent_or_authorization": "Informed consent obtained",
                "data_sensitivity_and_identifiers": ["Education records"],
                "planned_data_access": "Controlled access through an external repository",
                "study_start_date": "2026-01-10", "study_end_date": "2026-05-01",
            }}),
        },
        "module2_plan": {"variables": [{"Variable_ID": "Math_Membership", "Concept_Construct": "Membership"},
                                       {"Concept_Construct": "Self-efficacy"}]},
    }
    record = profile.from_project(project, lib)
    s = record["stemed"]
    assert record["resource"]["creators"][0]["orcid"] == "0000-0002-1825-0097"
    assert record["resource"]["language"] == "en"
    assert s["discipline"] == ["chemistry"]
    assert s["population"]["education_levels"] == ["undergraduate"]
    assert s["population"]["undergraduate_levels"] == ["introductory"]
    assert s["context"]["locale"] == ["rural"]
    assert s["evidence"]["study_designs"] == ["longitudinal"]
    assert s["ethics"]["human_subjects_review"] == "approved"
    assert s["ethics"]["access_level"] == "controlled"
    assert s["ethics"]["sensitivity_flags"] == ["education_records"]
    assert {c["construct_id"] for c in s["constructs"]} >= {"sense_of_belonging", "self_efficacy"}
    assert record["resource"]["geography"] == {"countries": ["US"], "us_states": ["MI"]}


def test_datacite_json_has_mandatory_properties(lib):
    data = profile.to_datacite_json(EXAMPLE, lib)
    for key in ("doi", "types", "titles", "creators", "publisher", "publicationYear"):
        assert data.get(key)
    schemes = {s.get("subjectScheme") for s in data["subjects"]}
    assert {"STEMEd+ Constructs", "ERIC Thesaurus", "STEMEd+ Education Levels"} <= schemes
    assert {"relationType": "IsCollectedBy"}.items() <= data["relatedIdentifiers"][0].items()


def test_xml_requires_doi(lib):
    record = copy.deepcopy(EXAMPLE)
    record["resource"]["identifier"] = None
    with pytest.raises(ValueError):
        profile.to_datacite_xml(record, lib)


def _datacite_xsd():
    local = os.environ.get("DATACITE_XSD")
    if local and Path(local).exists():
        return local
    try:
        urllib.request.urlopen(profile.DATACITE_XSD.replace("http:", "https:"), timeout=10).close()
        return profile.DATACITE_XSD.replace("http:", "https:")
    except Exception:
        return None


def test_datacite_xml_validates_against_official_schema(lib):
    etree = pytest.importorskip("lxml.etree")
    xsd = _datacite_xsd()
    if not xsd:
        pytest.skip("DataCite 4.7 schema not reachable; set DATACITE_XSD to a local metadata.xsd")
    schema = etree.XMLSchema(etree.parse(xsd))
    doc = etree.fromstring(profile.to_datacite_xml(EXAMPLE, lib).encode())
    assert schema.validate(doc), schema.error_log


def test_migrate_keeps_complete_records_and_fills_partial_ones(p):
    assert profile.migrate(EXAMPLE, p) == EXAMPLE
    partial = {"profile": "stemed-ap", "profile_version": "1.0.0-draft.1",
               "resource": {"title": "T"}, "stemed": {"ethics": {"access_level": "closed"}}}
    filled = profile.migrate(partial, p)
    assert filled["resource"]["title"] == "T"
    assert filled["stemed"]["ethics"]["access_level"] == "closed"
    assert filled["stemed"]["population"]["education_levels"] == []
    assert filled["stemed"]["care"]["local_contexts_labels"] == []
