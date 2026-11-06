import copy
import dataclasses
import json
import os
import re
import urllib.request
from pathlib import Path

import pytest

from oem import profile
from oem.library import Library

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "standard" / "humeta"
ONLINE = json.loads((ROOT / "standard" / "humeta" / "examples" / "online-discourse-dataset.json").read_text())
ARCHIVAL = json.loads((ROOT / "standard" / "humeta" / "examples" / "archival-letters-collection.json").read_text())
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
    on_disk = json.loads((BASE / "schema" / "humeta-record.schema.json").read_text())
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


def test_eric_export_skips_unverified(p, lib):
    # Every mapped descriptor is verified now, so mark one unverified for this test only.
    status = copy.deepcopy(p.eric_status)
    status["verified"] = [d for d in status["verified"] if d != "Surveys"]
    status["unverified"] = [*status["unverified"], "Surveys"]
    test_profile = dataclasses.replace(p, eric_status=status)
    verified_only = profile.eric_descriptors(EXAMPLE, lib, test_profile)
    everything = profile.eric_descriptors(EXAMPLE, lib, test_profile, include_unverified=True)
    assert "Surveys" in everything and "Surveys" not in verified_only
    assert "Climate" in verified_only
    assert "Surveys" in profile.eric_descriptors(EXAMPLE, lib, p)


@pytest.mark.parametrize("change, rule", [
    ({"identifiability": "identifiable"}, "R4"),
    ({"consent_for_sharing": "restricted_sharing"}, "R5"),
    ({"human_subjects_review": "pending"}, "R6"),
])
def test_open_access_rules(lib, change, rule):
    record = copy.deepcopy(EXAMPLE)
    record["study"]["ethics"].update(change)
    assert rule in rules_fired(record, lib)


def test_constructs_and_design_required_for_datasets(lib):
    record = copy.deepcopy(EXAMPLE)
    record["study"]["constructs"] = []
    record["study"]["evidence"]["study_designs"] = []
    assert {"R1", "R2"} <= rules_fired(record, lib)


def test_measurement_evidence_is_optional_for_instruments(lib):
    record = copy.deepcopy(EXAMPLE)
    record["resource"]["resource_type"] = "Instrument"
    record["study"]["evidence"]["measurement_evidence"] = []
    assert "R3" not in rules_fired(record, lib)  # R3 retired: evidence lives with the instrument in the library


def test_care_rules(lib):
    record = copy.deepcopy(EXAMPLE)
    record["study"]["care"].update({"indigenous_data": "yes", "governance": "none", "statement": None})
    assert {"R7", "R8"} <= rules_fired(record, lib)
    record["study"]["care"].update({"governance": "community_agreement", "statement": "Co-designed with the Nation's education department."})
    assert not {"R7", "R8"} & rules_fired(record, lib)


def test_care_prompt_for_tribal_college(lib):
    record = copy.deepcopy(EXAMPLE)
    record["education"]["institution_types"] = ["tribal_college"]
    assert "R11" in rules_fired(record, lib)


def test_education_records_warning_is_not_an_error(lib):
    record = copy.deepcopy(EXAMPLE)
    record["study"]["ethics"]["sensitivity_flags"] = ["education_records"]
    issues = profile.validate(record, lib)
    assert [i.rule for i in issues] == ["R9"] and issues[0].severity == "warning"


def test_datacite_json_has_mandatory_properties(lib):
    data = profile.to_datacite_json(EXAMPLE, lib)
    for key in ("doi", "types", "titles", "creators", "publisher", "publicationYear"):
        assert data.get(key)
    schemes = {s.get("subjectScheme") for s in data["subjects"]}
    assert {"HuMeta Constructs", "ERIC Thesaurus", "HuMeta Education Levels"} <= schemes
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
    partial = {"profile": "humeta", "profile_version": "1.0.0-draft.1",
               "resource": {"title": "T"}, "study": {"ethics": {"access_level": "closed"}}}
    filled = profile.migrate(partial, p)
    assert filled["resource"]["title"] == "T"
    assert filled["study"]["ethics"]["access_level"] == "closed"
    assert filled["study"]["care"]["local_contexts_labels"] == []
    assert filled["education"] is None  # module not used
    with_module = profile.migrate({**partial, "education": {"pedagogy": ["flipped"]}}, p)
    assert with_module["education"]["pedagogy"] == ["flipped"]
    assert with_module["education"]["education_levels"] == []


def test_suggest_constructs_from_module2_plan(lib):
    plan = {"variables": [{"Variable_ID": "Math_Membership", "Concept_Construct": "Membership"},
                          {"Concept_Construct": "Self-efficacy"}, {"Concept_Construct": "Unrelated thing"}]}
    assert set(profile.suggest_constructs(lib, plan)) >= {"sense_of_belonging", "self_efficacy"}


def test_study_record_view_for_later_modules(p):
    study = profile.to_study_record(EXAMPLE, profile=p)
    meta = json.loads(study["study_description"])["metadata"]
    assert study["study_title"] == EXAMPLE["resource"]["title"]
    assert meta["content_domain"] == EXAMPLE["study"]["design"]["topic"]
    assert meta["unit_of_analysis"] == "Individual (person)"
    assert meta["sampling_procedure"].startswith("Non-probability: availability")
    assert meta["participant_populations"] == ["Students / learners"]
    assert meta["state_origin"] == "MI"
    again = profile.to_study_record(EXAMPLE, existing=study, profile=p)
    assert again["id"] == study["id"] and again["created_at"] == study["created_at"]


def test_every_element_has_alignments_to_known_standards(p):
    standards = p.definition["standards"]
    for e in p.definition["elements"]:
        assert e.get("alignments"), f"{e['id']} has no standard alignments"
        for a in e["alignments"]:
            assert a["standard"] in standards, f"{e['id']}: unknown standard {a['standard']}"
            assert a["match"] in p.definition["match_types"], f"{e['id']}: bad match type"
            assert a["term"].strip()
    # resource (citation) elements are general-purpose: each aligns exactly with DataCite
    for e in p.definition["elements"]:
        if e["id"].startswith("resource."):
            assert any(a["standard"] == "datacite" and a["match"] == "exact" for a in e["alignments"]), e["id"]


def test_alignment_badges(p):
    assert profile.alignment_badges("resource.title", p) == "`DataCite: titles.title` `DC: title` `schema.org: name` `DDI-C: titl`"
    assert profile.alignment_badges("resource.publication_year", p).count("≈") == 3
    assert profile.alignment_badges("study.constructs", p).startswith("`HuMeta`")
    assert "Close match: Dublin Core" in profile.alignment_help("resource.publication_year", p)


def test_alignment_status_and_notes():
    p = profile.load()
    for e in p.definition["elements"]:
        for a in e["alignments"]:
            assert a.get("status", "seeking_input") in p.definition["alignment_status"], (e["id"], a)
    badges = profile.alignment_badges("education.education_levels")
    assert "`ISCED: levels of education 0–8`" in badges
    assert f"`≈DC: educationLevel` {profile.SEEKING_INPUT_BADGE}" in badges
    assert profile.SEEKING_INPUT_BADGE in profile.alignment_badges("education.pedagogy")
    assert "seeking expert input" in profile.alignment_help("education.pedagogy")


def test_education_levels_follow_isced_and_export_as_subjects():
    p = profile.load()
    codes = [t.get("isced") for t in p.vocab("education_level")]
    assert [c for c in codes if c is not None] == [str(i) for i in range(9)]
    record = profile.empty_record(modules=("education",))
    record["education"]["education_levels"] = ["short_cycle_tertiary", "informal_learning"]
    subjects = profile.to_datacite_json(record, Library.load(), p)["subjects"]
    isced = [s for s in subjects if s.get("subjectScheme") == profile.ISCED_SCHEME]
    assert [s["subject"] for s in isced] == ["ISCED level 5: Short-cycle tertiary education"]


def test_education_module_is_optional(lib, p):
    record = copy.deepcopy(EXAMPLE)
    record["education"] = None
    assert profile.is_valid(record, lib, p)
    assert not any(s.get("subjectScheme") == "HuMeta Education Levels"
                   for s in profile.to_datacite_json(record, lib, p)["subjects"])
    record["education"] = profile.empty_record(p, modules=("education",))["education"]
    issues = profile.validate(record, lib, p)
    assert any(i.element == "education.education_levels" and i.severity == "error" for i in issues)


def test_every_element_belongs_to_a_known_module(p):
    for e in p.definition["elements"]:
        assert e["module"] in p.definition["modules"], e["id"]
        prefix = e["id"].split(".")[0]
        expected = ("resource", "study") if e["module"] == "core" else (e["module"],)
        assert prefix in expected, e["id"]


def test_examples_from_three_fields_are_valid(lib, p):
    for record in (EXAMPLE, ONLINE, ARCHIVAL):
        assert profile.is_valid(record, lib, p), [i for i in profile.validate(record, lib, p) if i.severity == "error"]
        assert profile.migrate(record, p) == record


def test_studies_without_participants_need_sources_not_roles_or_constructs(lib, p):
    record = copy.deepcopy(ARCHIVAL)
    record["resource"]["resource_type"] = "Dataset"
    assert profile.is_valid(record, lib, p)  # no constructs or participant roles needed
    record["study"]["sources"]["types"] = []
    assert any(i.element == "study.sources.types" for i in profile.validate(record, lib, p))
    record = copy.deepcopy(EXAMPLE)
    record["study"]["population"]["participant_roles"] = []
    assert any(i.element == "study.population.participant_roles" for i in profile.validate(record, lib, p))


def test_online_data_rules(lib, p):
    record = copy.deepcopy(ONLINE)
    record["study"]["ethics"]["online_data"] = []
    assert any(i.element == "study.ethics.online_data" and i.severity == "error" for i in profile.validate(record, lib, p))
    record["study"]["ethics"]["online_data"] = ["public_content", "private_spaces", "minors_possible"]
    record["study"]["ethics"]["access_level"] = "open"
    assert {"R13", "R14", "R15", "R16"} <= rules_fired(record, lib)
    assert {"R13", "R14", "R15", "R16"}.isdisjoint(rules_fired(ONLINE, lib))


def test_source_rights_rule(lib):
    record = copy.deepcopy(ARCHIVAL)
    record["study"]["sources"]["rights"] = "in_copyright"
    assert "R17" in rules_fired(record, lib)
    assert "R17" not in rules_fired(ARCHIVAL, lib)


def test_fos_subjects_coverage_dates_and_source_rights(lib, p):
    data = profile.to_datacite_json(ARCHIVAL, lib, p)
    fos = [s for s in data["subjects"] if s.get("subjectScheme") == profile.FOS_SCHEME]
    assert {s["subject"] for s in fos} == {"FOS: Humanities", "FOS: Educational sciences", "FOS: History and archaeology"}
    assert all(s["classificationCode"] in profile.FOS_LABELS for s in fos)
    assert {"date": "1921/1929", "dateType": "Coverage"} in data["dates"]
    assert any(r.get("rightsUri") == "http://rightsstatements.org/vocab/NoC-US/1.0/" for r in data["rightsList"])
    methods = next(d["description"] for d in data["descriptions"] if d["descriptionType"] == "Methods")
    assert "Archival research" in methods and "Period covered: 1921-1929" in methods


def test_vocabulary_mappings_point_to_known_codes(p):
    ddi_codes = {
        "KindOfData": {"Quantitative", "Qualitative", "Mixed"},  # DDI CV KindOfData 1.0.0
        "AnalysisUnit": {"Individual", "Group", "Household", "OrganizationOrInstitution", "EventOrProcessOrActivity",
                         "GeographicUnit", "TimeUnit", "MediaUnit.Text", "MediaUnit.StillImage", "MediaUnit.Sound",
                         "MediaUnit.Video", "Object", "Other"},
    }
    for vocab_id, vocab in p.vocabularies.items():
        for t in vocab["terms"]:
            if "fos" in t:
                assert t["fos"] in profile.FOS_LABELS, (vocab_id, t["id"])
            if "ddi" in t:
                assert t["ddi"]["match"] in p.definition["match_types"]
                if t["ddi"]["cv"] in ddi_codes:
                    assert t["ddi"]["code"] in ddi_codes[t["ddi"]["cv"]], t["id"]
            if "rs" in t:
                assert t["rs"] in {"InC", "NoC-US", "CNE", "UND", "NKC"}


def test_tooltips_carry_the_alignments(p):
    text = profile.alignment_help("resource.title", p)
    assert text.startswith(profile.element("resource.title", p)["definition"])
    assert "**Matches in other standards**" in text and "`titles.title`" in text and "`titl`" in text
    assert "answer options are defined by the HuMeta profile" in profile.alignment_help("study.population.human_participants", p)


def test_theoretical_frameworks_are_validated_and_exported(lib, p):
    record = copy.deepcopy(ARCHIVAL)
    data = profile.to_datacite_json(record, lib, p)
    fw = [s for s in data["subjects"] if s.get("subjectScheme") == "HuMeta Frameworks"]
    assert [s["subject"] for s in fw] == ["New Historicism and Cultural History"]
    assert fw[0]["valueUri"].endswith("frameworks.json#new_historicism")
    methods = next(d["description"] for d in data["descriptions"] if d["descriptionType"] == "Methods")
    assert "Theoretical framework: New Historicism and Cultural History." in methods
    record["study"]["design"]["frameworks"] = ["not_a_framework"]
    assert any(i.element == "study.design.frameworks" for i in profile.validate(record, lib, p))


def test_social_science_module_uses_ddi_and_links_the_ddi_record(lib, p):
    record = copy.deepcopy(ONLINE)
    assert profile.uses(record, "social_science")
    record["social_science"]["ddi_record"] = "https://www.icpsr.umich.edu/web/ICPSR/studies/0000"
    assert profile.is_valid(record, lib, p)
    data = profile.to_datacite_json(record, lib, p)
    assert {"relatedIdentifier": record["social_science"]["ddi_record"], "relatedIdentifierType": "URL",
            "relationType": "IsDocumentedBy"} in data["relatedIdentifiers"]
    methods = next(d["description"] for d in data["descriptions"] if d["descriptionType"] == "Methods")
    assert "Kind of data (DDI): Mixed." in methods and "Universe: Public English-language posts" in methods
    for e in p.definition["elements"]:
        if e["module"] == "social_science" and e["id"] != "social_science.ddi_record":
            assert any(a["standard"] in ("ddi", "ddi_cv") and a["match"] == "exact" for a in e["alignments"]), e["id"]


def test_humanities_module_exports_tadirah_concepts(lib, p):
    terms = p.vocab("tadirah_activity")
    assert len(terms) == 36 and len({t["tadirah"] for t in terms}) == 36
    data = profile.to_datacite_json(ARCHIVAL, lib, p)
    tadirah = [s for s in data["subjects"] if s.get("subjectScheme") == profile.TADIRAH_SCHEME]
    assert tadirah[0] == {"subject": "Capturing: Transcribing", "subjectScheme": "TaDiRAH",
                          "schemeUri": "https://vocabs.dariah.eu/tadirah/",
                          "valueUri": "https://vocabs.dariah.eu/tadirah/transcribing"}
    record = copy.deepcopy(ARCHIVAL)
    record["humanities"]["source_languages"] = ["French"]
    assert any(i.element.startswith("humanities") for i in profile.validate(record, lib, p) if i.severity == "error")


def test_new_modules_are_optional(lib, p):
    record = copy.deepcopy(ONLINE)
    record["social_science"] = record["humanities"] = None
    assert profile.is_valid(record, lib, p)
    assert profile.empty_record(p, modules=("social_science", "humanities"))["humanities"]["source_languages"] == []


def test_start_choices_set_fields_and_modules(p):
    record = copy.deepcopy(ARCHIVAL)  # fields: humanities, education; humanities module only
    assert profile.start_choices(record) == ["education", "humanities"]
    new = profile.apply_start_choices(record, ["social_science", "humanities", "other"], p)
    assert new["study"]["fields"] == ["social_sciences", "humanities", "other_field"]
    assert profile.uses(new, "social_science") and profile.uses(new, "humanities") and not profile.uses(new, "education")
    assert new["humanities"] == ARCHIVAL["humanities"]  # kept, not reset
    record["study"]["fields"] = ["arts"]
    assert profile.start_choices(record) == ["humanities"]
    assert profile.apply_start_choices(record, ["humanities"], p)["study"]["fields"] == ["humanities", "arts"]


def test_old_discipline_terms_move_to_anzsrc(lib, p):
    record = copy.deepcopy(EXAMPLE)
    record["study"]["discipline"] = ["sociology", "general_stem", "other_discipline", "anzsrc_4410"]
    assert profile.is_valid(record, lib, p)  # old terms still validate
    moved = profile.migrate(record, p)["study"]["discipline"]
    assert moved[0] == "anzsrc_4410" and "anzsrc_49" in moved and "sociology" not in moved and len(moved) == len(set(moved))
    active = p.active_ids("discipline")
    assert len(active) == 236 and all(p.term("discipline", d).get("fos") in profile.FOS_LABELS for d in active)
