import copy
import json
import os
import re
import urllib.request
from pathlib import Path

import pytest

from oem import profile
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


def _datacite_xsd(tmp_path: Path):
    """Path to a local copy of the DataCite 4.7 XML Schema (with its includes), or None.

    lxml cannot fetch https URLs itself, so the schema files are downloaded first.
    """
    local = os.environ.get("DATACITE_XSD")
    if local and Path(local).exists():
        return local
    url = os.environ.get("DATACITE_XSD_URL") or profile.DATACITE_XSD.replace("http:", "https:")
    base = url.rsplit("/", 1)[0] + "/"
    try:
        pending, seen = ["metadata.xsd"], set()
        while pending:
            name = pending.pop()
            if name in seen:
                continue
            seen.add(name)
            with urllib.request.urlopen(base + name, timeout=20) as response:
                text = response.read().decode("utf-8")
            target = tmp_path / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
            folder = name.rsplit("/", 1)[0] + "/" if "/" in name else ""
            for ref in re.findall(r'schemaLocation="([^"]+)"', text):
                if "://" not in ref:
                    pending.append(folder + ref)
        return str(tmp_path / "metadata.xsd")
    except Exception:
        return None


def test_datacite_xml_validates_against_official_schema(lib, tmp_path):
    etree = pytest.importorskip("lxml.etree")
    xsd = _datacite_xsd(tmp_path)
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


def test_suggest_constructs_from_module2_plan(lib):
    plan = {"variables": [{"Variable_ID": "Math_Membership", "Concept_Construct": "Membership"},
                          {"Concept_Construct": "Self-efficacy"}, {"Concept_Construct": "Unrelated thing"}]}
    assert set(profile.suggest_constructs(lib, plan)) >= {"sense_of_belonging", "self_efficacy"}


def test_study_record_view_for_later_modules(p):
    study = profile.to_study_record(EXAMPLE, profile=p)
    meta = json.loads(study["study_description"])["metadata"]
    assert study["study_title"] == EXAMPLE["resource"]["title"]
    assert meta["content_domain"] == EXAMPLE["stemed"]["design"]["topic"]
    assert meta["unit_of_analysis"] == "Individual (person / participant)"
    assert meta["sampling_procedure"] == "Convenience sample"
    assert meta["participant_populations"] == ["Students / learners"]
    assert meta["state_origin"] == "MI"
    again = profile.to_study_record(EXAMPLE, existing=study, profile=p)
    assert again["id"] == study["id"] and again["created_at"] == study["created_at"]
