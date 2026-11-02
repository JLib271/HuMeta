# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""HuMeta: The Social Science, Humanities, and Education Study Metadata Profile.

A core for any study, plus optional field modules (currently: Education).
The profile itself is data in ``standard/humeta/`` (``profile.json`` and
``vocabularies.json``); this module loads it and works with records:

* :func:`empty_record` creates a record; :func:`suggest_constructs` proposes
  constructs from a Module 2 plan; :func:`to_study_record` gives the study view
  that Module 2 and later modules read.
* :func:`validate` checks a record against the JSON Schema and the profile's
  obligations and responsible-sharing rules.
* :func:`to_datacite_json` / :func:`to_datacite_xml` export DataCite 4.7.
* :func:`eric_descriptors` gives ERIC Thesaurus descriptors for the record.

Nothing here imports Streamlit.
"""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from oem.library import Library

ROOT = Path(__file__).resolve().parent.parent
PROFILE_DIR = ROOT / "standard" / "humeta"
CONSTRUCTS_URI = "https://github.com/JLib271/HuMeta/blob/main/library/constructs.json#"
FRAMEWORKS_URI = "https://github.com/JLib271/HuMeta/blob/main/library/frameworks.json#"
VOCAB_URI = "https://github.com/JLib271/HuMeta/blob/main/standard/humeta/vocabularies.json#"
LIBRARY_RECORD_URI = "https://github.com/JLib271/HuMeta/blob/main/library/instruments/"
DATACITE_NS = "http://datacite.org/schema/kernel-4"
DATACITE_XSD = "http://schema.datacite.org/meta/kernel-4.7/metadata.xsd"
ERIC_SCHEME = "ERIC Thesaurus"
ERIC_SCHEME_URI = "https://eric.ed.gov/?ti=all"
ISCED_SCHEME = "ISCED 2011"
ISCED_SCHEME_URI = ("https://uis.unesco.org/sites/default/files/documents/"
                    "international-standard-classification-of-education-isced-2011-en.pdf")
ISCED_LEVELS = {"0": "Early childhood education", "1": "Primary education", "2": "Lower secondary education",
                "3": "Upper secondary education", "4": "Post-secondary non-tertiary education",
                "5": "Short-cycle tertiary education", "6": "Bachelor's or equivalent level",
                "7": "Master's or equivalent level", "8": "Doctoral or equivalent level"}
SEEKING_INPUT_BADGE = "(expert input wanted)"
#: OECD Fields of Science and Technology, labels as used in DataCite metadata
FOS_SCHEME = "Fields of Science and Technology (FOS)"
FOS_SCHEME_URI = "http://www.oecd.org/science/inno/38235147.pdf"
FOS_LABELS = {
    "1": "Natural sciences", "1.1": "Mathematics", "1.2": "Computer and information sciences",
    "1.3": "Physical sciences", "1.4": "Chemical sciences", "1.5": "Earth and related environmental sciences",
    "1.6": "Biological sciences", "2": "Engineering and technology",
    "5": "Social sciences", "5.1": "Psychology", "5.2": "Economics and business", "5.3": "Educational sciences",
    "5.4": "Sociology", "5.5": "Law", "5.6": "Political science", "5.7": "Social and economic geography",
    "5.8": "Media and communications", "5.9": "Other social sciences",
    "6": "Humanities", "6.1": "History and archaeology", "6.2": "Languages and literature",
    "6.3": "Philosophy, ethics and religion", "6.4": "Arts (arts, history of arts, performing arts, music)",
    "6.5": "Other humanities",
}
DDI_CV_URI = "http://rdf-vocabulary.ddialliance.org/cv/"
RIGHTS_STATEMENTS_URI = "http://rightsstatements.org/vocab/{}/1.0/"
ONLINE_SOURCES = {"social_media", "websites"}

#: record path (from the record root) -> (vocabulary id, DataCite subjectScheme label)
VOCAB_FIELDS: dict[tuple[str, ...], tuple[str, str | None]] = {
    ("study", "fields"): ("research_field", None),  # exported as OECD FOS subjects
    ("study", "discipline"): ("discipline", "HuMeta Disciplines"),
    ("study", "population", "participant_roles"): ("participant_role", "HuMeta Participant Roles"),
    ("study", "context", "locale"): ("locale", "HuMeta Locales"),
    ("study", "evidence", "study_designs"): ("study_design", "HuMeta Study Designs"),
    ("study", "design", "unit_of_analysis"): ("unit_of_analysis", "HuMeta Units of Analysis"),
    ("study", "design", "sampling_procedure"): ("sampling_procedure", "HuMeta Sampling Procedures"),
    ("study", "evidence", "measurement_evidence"): ("measurement_evidence", "HuMeta Measurement Evidence"),
    ("study", "evidence", "data_collection_methods"): ("data_collection_method", "HuMeta Data Collection Methods"),
    ("study", "evidence", "analysis_methods"): ("analysis_method", "HuMeta Analysis Methods"),
    ("study", "sources", "types"): ("source_type", "HuMeta Source Types"),
    ("study", "ethics", "sensitivity_flags"): ("sensitivity_flag", None),
    ("study", "ethics", "online_data"): ("online_data_practice", None),
    # Education module
    ("education", "education_levels"): ("education_level", "HuMeta Education Levels"),
    ("education", "undergraduate_levels"): ("undergraduate_level", "HuMeta Undergraduate Levels"),
    ("education", "institution_types"): ("institution_type", "HuMeta Institution Types"),
    ("education", "modality"): ("modality", "HuMeta Modalities"),
    ("education", "learning_environments"): ("learning_environment", "HuMeta Learning Environments"),
    ("education", "pedagogy"): ("pedagogy", "HuMeta Instructional Approaches"),
}
#: single-valued vocabulary fields
VOCAB_SINGLE: dict[tuple[str, ...], str] = {
    ("study", "population", "human_participants"): "human_participants",
    ("study", "sources", "rights"): "source_rights",
    ("study", "ethics", "human_subjects_review"): "human_subjects_review",
    ("study", "ethics", "consent"): "consent",
    ("study", "ethics", "consent_for_sharing"): "consent_for_sharing",
    ("study", "ethics", "identifiability"): "identifiability",
    ("study", "ethics", "access_level"): "access_level",
    ("study", "care", "indigenous_data"): "indigenous_data",
    ("study", "care", "governance"): "indigenous_governance",
}
#: optional field modules: record key -> label
MODULES = {"education": "Education"}
PROFILE_ID = "humeta"
RESOURCE_TYPES = ("Dataset", "Instrument", "StudyRegistration", "Text", "Software", "Collection", "Other")


# --------------------------------------------------------------------- loading
@dataclass(frozen=True)
class Profile:
    definition: dict
    vocabularies: dict
    eric_status: dict

    @property
    def version(self) -> str:
        return self.definition["profile_version"]

    def vocab(self, vocab_id: str) -> list[dict]:
        return self.vocabularies[vocab_id]["terms"]

    def term(self, vocab_id: str, term_id: str) -> dict:
        for term in self.vocab(vocab_id):
            if term["id"] == term_id:
                return term
        raise KeyError(f"{term_id!r} is not in vocabulary {vocab_id!r}")

    def label(self, vocab_id: str, term_id: str) -> str:
        return self.term(vocab_id, term_id)["label"]

    def ids(self, vocab_id: str) -> list[str]:
        return [t["id"] for t in self.vocab(vocab_id)]

    def verified_eric(self) -> set[str]:
        return set(self.eric_status["verified"])


@lru_cache(maxsize=4)
def load(profile_dir: str | None = None) -> Profile:
    base = Path(profile_dir) if profile_dir else PROFILE_DIR
    definition = json.loads((base / "profile.json").read_text(encoding="utf-8"))
    vocabularies = json.loads((base / "vocabularies.json").read_text(encoding="utf-8"))["vocabularies"]
    eric_status = json.loads((base / "crosswalks" / "eric_descriptor_status.json").read_text(encoding="utf-8"))
    return Profile(definition=definition, vocabularies=vocabularies, eric_status=eric_status)


# ---------------------------------------------------------------- JSON Schema
def json_schema(profile: Profile | None = None) -> dict:
    """JSON Schema for a HuMeta record, generated from the profile definition."""
    p = profile or load()

    def enum_array(vocab_id: str) -> dict:
        return {"type": "array", "uniqueItems": True, "items": {"enum": p.ids(vocab_id)}}

    def enum_single(vocab_id: str) -> dict:
        return {"enum": p.ids(vocab_id) + [None]}

    def obj() -> dict:
        return {"type": "object", "additionalProperties": False, "properties": {}}

    root: dict[str, dict] = {"study": obj(), "education": obj()}

    def put(path: tuple[str, ...], schema: dict) -> None:
        node = root[path[0]]
        for key in path[1:-1]:
            node = node["properties"].setdefault(key, obj())
        node["properties"][path[-1]] = schema

    for path, (vocab_id, _) in VOCAB_FIELDS.items():
        put(path, enum_array(vocab_id))
    for path, vocab_id in VOCAB_SINGLE.items():
        put(path, enum_single(vocab_id))
    text = {"type": ["string", "null"]}
    put(("study", "population", "description"), text)
    put(("study", "population", "sample_size"), {"type": ["integer", "null"], "minimum": 0})
    put(("study", "design", "topic"), text)
    put(("study", "design", "research_questions"), text)
    put(("study", "design", "framework_description"), text)
    put(("study", "design", "frameworks"), {"type": "array", "uniqueItems": True,
                                            "items": {"type": "string", "pattern": "^[a-z][a-z0-9_]*$"}})
    put(("study", "ethics", "governance_notes"), text)
    put(("study", "sources", "description"), text)
    put(("study", "sources", "holdings"), text)
    put(("study", "sources", "time_period"), text)
    put(("study", "care", "statement"), text)
    put(("study", "care", "local_contexts_project"), {"type": ["string", "null"], "format": "uri"})
    put(("study", "care", "local_contexts_labels"), {"type": "array", "items": {"type": "string"}})
    put(("study", "constructs"), {
        "type": "array",
        "items": {
            "type": "object", "additionalProperties": False, "required": ["construct_id"],
            "properties": {
                "construct_id": {"type": "string", "pattern": "^[a-z][a-z0-9_]*$"},
                "instrument_id": {"type": ["string", "null"]},
                "version_id": {"type": ["string", "null"]},
                "dimension_id": {"type": ["string", "null"]},
            },
        },
    })
    education = root["education"]
    education["type"] = ["object", "null"]
    education["description"] = "Education module. Null or absent when the study is not in an education setting."
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://github.com/JLib271/HuMeta/blob/main/standard/humeta/schema/humeta-record.schema.json",
        "title": f"HuMeta profile record ({p.version})",
        "description": "Generated from standard/humeta/profile.json and vocabularies.json by scripts/build_profile_artifacts.py. Do not edit by hand.",
        "type": "object",
        "additionalProperties": False,
        "required": ["profile", "profile_version", "resource", "study"],
        "properties": {
            "profile": {"const": PROFILE_ID},
            "profile_version": {"type": "string"},
            "resource": {
                "type": "object", "additionalProperties": False,
                "required": ["title", "creators", "publisher", "publication_year", "resource_type"],
                "properties": {
                    "title": {"type": "string", "minLength": 1},
                    "creators": {
                        "type": "array", "minItems": 1,
                        "items": {"type": "object", "additionalProperties": False, "required": ["name"], "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "orcid": {"type": ["string", "null"], "pattern": r"^(\d{4}-){3}\d{3}[\dX]$"},
                            "affiliation": {"type": ["string", "null"]},
                        }},
                    },
                    "publisher": {"type": "string", "minLength": 1},
                    "publication_year": {"type": "integer", "minimum": 1900, "maximum": 2100},
                    "resource_type": {"enum": list(RESOURCE_TYPES)},
                    "identifier": {"type": ["object", "null"], "additionalProperties": False, "properties": {
                        "value": {"type": "string"}, "type": {"type": "string"}}},
                    "description": {"type": ["string", "null"]},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "language": {"type": ["string", "null"], "pattern": "^[a-z]{2,3}(-[A-Za-z0-9]+)*$"},
                    "license": {"type": ["object", "null"], "additionalProperties": False, "properties": {
                        "spdx": {"type": ["string", "null"]}, "name": {"type": ["string", "null"]}, "url": {"type": ["string", "null"]}}},
                    "funding": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["funder_name"], "properties": {
                        "funder_name": {"type": "string"}, "award_number": {"type": ["string", "null"]}}}},
                    "collection_dates": {"type": ["object", "null"], "additionalProperties": False, "properties": {
                        "start": {"type": ["string", "null"], "format": "date"}, "end": {"type": ["string", "null"], "format": "date"}}},
                    "geography": {"type": ["object", "null"], "additionalProperties": False, "properties": {
                        "countries": {"type": "array", "items": {"type": "string", "pattern": "^[A-Z]{2}$"}},
                        "us_states": {"type": "array", "items": {"type": "string", "pattern": "^[A-Z]{2}$"}}}},
                    "related": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                        "required": ["identifier", "identifier_type", "relation"], "properties": {
                            "identifier": {"type": "string"}, "identifier_type": {"enum": ["DOI", "URL", "Handle", "ISBN", "ISSN", "ARK"]},
                            "relation": {"type": "string"}}}},
                },
            },
            "study": root["study"],
            "education": education,
        },
    }


# ------------------------------------------------------------------- records
def _empty_section(section: str) -> dict:
    out: dict[str, Any] = {}

    def put(path: tuple[str, ...], value: Any) -> None:
        node = out
        for key in path[1:-1]:
            node = node.setdefault(key, {})
        node[path[-1]] = value

    for path in VOCAB_FIELDS:
        if path[0] == section:
            put(path, [])
    for path in VOCAB_SINGLE:
        if path[0] == section:
            put(path, None)
    if section == "study":
        out["constructs"] = []
        out["population"].update({"description": None, "sample_size": None})
        out["design"].update({"topic": None, "research_questions": None, "frameworks": [], "framework_description": None})
        out["ethics"]["governance_notes"] = None
        out["sources"].update({"description": None, "holdings": None, "time_period": None})
        out["care"].update({"statement": None, "local_contexts_project": None, "local_contexts_labels": []})
    return out


def empty_record(profile: Profile | None = None, modules: tuple[str, ...] = ()) -> dict:
    """A new record. ``modules`` lists the field modules to include, e.g. ("education",)."""
    p = profile or load()
    record = {
        "profile": PROFILE_ID,
        "profile_version": p.version,
        "resource": {"title": "", "creators": [], "publisher": "", "publication_year": None,
                     "resource_type": "Dataset", "keywords": [], "funding": [], "related": []},
        "study": _empty_section("study"),
    }
    for module in MODULES:
        record[module] = _empty_section(module) if module in modules else None
    return record


def uses(record: dict, module: str) -> bool:
    """True if the record includes the given field module."""
    return isinstance(record.get(module), dict)


def get(record: dict, path: tuple[str, ...]) -> Any:
    node: Any = record
    for key in path:
        node = (node or {}).get(key)
    return node


def suggest_constructs(lib: Library, plan: dict) -> list[str]:
    """Constructs measured in the Module 2 variable plan.

    Current plans link their constructs to the shared construct list directly.
    The earliest plans are matched by variable keys, labels and construct synonyms.
    """
    if (plan or {}).get("schema_version", 1) >= 2:
        from oem import plan as plan_model
        return [c for c in plan_model.shared_construct_ids(plan_model.normalize(plan, lib)) if c in lib.constructs]
    texts: list[str] = []
    for row in (plan or {}).get("variables", []) + (plan or {}).get("custom_variables", []):
        if isinstance(row, dict):
            texts += [str(row.get(k) or "") for k in ("Variable_ID", "Concept_Construct", "Construct_ID", "Variable_Label")]
    found: list[str] = []
    lowered = [t.lower().replace("_", " ") for t in texts if t]
    raw = set(texts)
    for construct in lib.constructs.values():
        names = [construct["label"], *construct.get("synonyms", [])]
        if raw & set(construct.get("app_variable_keys", [])) or any(
            re.search(rf"\b{re.escape(n.lower())}\b", t) for n in names for t in lowered
        ):
            found.append(construct["id"])
    return found


def migrate(record: dict, profile: Profile | None = None) -> dict:
    """Fill any keys missing from an older or partial record with defaults."""
    base = empty_record(profile, modules=tuple(m for m in MODULES if uses(record, m)))

    def merge(default: Any, actual: Any) -> Any:
        if isinstance(default, dict) and isinstance(actual, dict):
            return {k: merge(default.get(k), actual.get(k)) if k in default else actual.get(k)
                    for k in {**default, **actual}}
        return default if actual is None and isinstance(default, list) else (actual if actual is not None else default)

    return merge(base, copy.deepcopy(record))


# ----------------------------------------------------------------- validation
@dataclass(frozen=True)
class Issue:
    severity: str  # "error" | "warning"
    element: str
    message: str
    rule: str | None = None


def validate(record: dict, lib: Library | None = None, profile: Profile | None = None) -> list[Issue]:
    """Schema errors, missing mandatory elements, and responsible-sharing rule results."""
    from jsonschema import Draft202012Validator

    p = profile or load()
    lib = lib or Library.load()
    issues: list[Issue] = []
    for err in Draft202012Validator(json_schema(p)).iter_errors(record):
        where = "/".join(str(x) for x in err.absolute_path) or "(record)"
        issues.append(Issue("error", where, err.message))
    if any(i.severity == "error" for i in issues):
        return issues
    record = migrate(record, p)

    res, s = record["resource"], record["study"]
    edu = record.get("education") or {}
    rtype = res["resource_type"]
    participants = get(record, ("study", "population", "human_participants"))
    source_types = set(get(record, ("study", "sources", "types")) or [])
    uses_online = bool(source_types & ONLINE_SOURCES) or "web_platform_data" in (s["evidence"].get("data_collection_methods") or [])
    required_lists = [(("study", "fields"), "research_field")]
    if participants in ("direct", "indirect"):
        required_lists.append((("study", "population", "participant_roles"), "participant_role"))
    if participants == "none":
        required_lists.append((("study", "sources", "types"), "source_type"))
    if uses_online:
        required_lists.append((("study", "ethics", "online_data"), "online_data_practice"))
    if uses(record, "education"):
        required_lists.append((("education", "education_levels"), "education_level"))
    for path, vocab_id in required_lists:
        if not get(record, path):
            issues.append(Issue("error", ".".join(path), f"Select at least one {p.vocabularies[vocab_id]['label'].lower()}."))
    for path in [("study", "population", "human_participants"), ("study", "ethics", "human_subjects_review"), ("study", "ethics", "consent_for_sharing"),
                 ("study", "ethics", "identifiability"), ("study", "ethics", "access_level"),
                 ("study", "care", "indigenous_data")]:
        if not get(record, path):
            issues.append(Issue("error", ".".join(path), "Required."))
    for fid in s["design"].get("frameworks") or []:
        if fid not in lib.frameworks:
            issues.append(Issue("error", "study.design.frameworks", f"Unknown framework {fid!r}."))
    for c in s.get("constructs", []):
        if c["construct_id"] not in lib.constructs:
            issues.append(Issue("error", "study.constructs", f"Unknown construct {c['construct_id']!r}."))
        if c.get("instrument_id") and c["instrument_id"] not in lib.instruments:
            issues.append(Issue("error", "study.constructs", f"Unknown instrument {c['instrument_id']!r}."))

    rules = {r["check"]: r for r in p.definition["rules"]}

    def flag(check: str, element: str) -> None:
        r = rules[check]
        issues.append(Issue(r["severity"], element, r["message"], r["id"]))

    ethics, care = s["ethics"], s["care"]
    access = ethics.get("access_level")
    needs_constructs = rtype == "Instrument" or (rtype == "Dataset" and participants == "direct")
    if needs_constructs and not s.get("constructs"):
        flag("constructs_required", "study.constructs")
    if rtype in ("Dataset", "StudyRegistration") and not s["evidence"].get("study_designs"):
        flag("design_required", "study.evidence.study_designs")
    if rtype == "Instrument" and not s["evidence"].get("measurement_evidence"):
        flag("measurement_evidence_required", "study.evidence.measurement_evidence")
    if access == "open" and ethics.get("identifiability") not in (None, "deidentified", "anonymous", "aggregate_only", "synthetic", "not_applicable"):
        flag("open_requires_deidentified", "study.ethics.identifiability")
    if access == "open" and ethics.get("consent_for_sharing") not in (None, "broad_sharing", "not_applicable"):
        flag("open_requires_sharing_consent", "study.ethics.consent_for_sharing")
    if access in ("open", "registered") and ethics.get("human_subjects_review") in ("not_assessed", "pending"):
        flag("sharing_requires_review", "study.ethics.human_subjects_review")
    if care.get("indigenous_data") == "yes":
        if care.get("governance") in (None, "none", "not_applicable") or not (care.get("statement") or "").strip():
            flag("care_requires_governance", "study.care.governance")
        if access == "open" and care.get("governance") not in ("community_agreement", "tribal_review"):
            flag("care_open_requires_agreement", "study.ethics.access_level")
    if "education_records" in (ethics.get("sensitivity_flags") or []) and access not in (None, "closed", "metadata_only"):
        flag("education_records_review", "study.ethics.sensitivity_flags")
    if care.get("indigenous_data") == "unknown":
        flag("care_unknown", "study.care.indigenous_data")
    if care.get("indigenous_data") != "yes" and (
        "specific_community" in s["population"].get("participant_roles", [])
        or "tribal_college" in (edu.get("institution_types") or [])
    ):
        flag("care_prompt", "study.care.indigenous_data")
    if "direct_identifiers" in (ethics.get("sensitivity_flags") or []) and access not in (None, "closed", "metadata_only"):
        flag("identifiers_not_shared", "study.ethics.sensitivity_flags")
    online = set(ethics.get("online_data") or [])
    if uses_online:
        shares_content = access not in (None, "closed", "metadata_only") and "ids_only" not in online
        if shares_content and not {"usernames_removed", "quotes_altered"} <= online:
            flag("online_authors_traceable", "study.ethics.online_data")
        if "platform_terms" not in online:
            flag("online_platform_terms", "study.ethics.online_data")
        if "minors_possible" in online and access in ("open", "registered"):
            flag("online_minors", "study.ethics.online_data")
        if "private_spaces" in online and "author_consent" not in online:
            flag("online_private_spaces", "study.ethics.online_data")
    rights = s["sources"].get("rights")
    if access in ("open", "registered") and (rights in ("in_copyright", "unknown_rights", "mixed_rights")
                                             or (source_types and not rights)):
        flag("source_rights", "study.sources.rights")
    return issues


def is_valid(record: dict, lib: Library | None = None, profile: Profile | None = None) -> bool:
    return not any(i.severity == "error" for i in validate(record, lib, profile))


# ----------------------------------------------------------------------- ERIC
def eric_descriptors(record: dict, lib: Library | None = None, profile: Profile | None = None,
                     include_unverified: bool = False) -> list[str]:
    """ERIC Thesaurus descriptors implied by the record (verified terms only by default)."""
    p = profile or load()
    lib = lib or Library.load()
    record = migrate(record, p)
    terms: list[str] = []
    for c in record["study"].get("constructs", []):
        terms += lib.constructs.get(c["construct_id"], {}).get("eric", [])
    for path, (vocab_id, _) in VOCAB_FIELDS.items():
        for term_id in get(record, path) or []:
            terms += p.term(vocab_id, term_id).get("eric", [])
    for path, vocab_id in VOCAB_SINGLE.items():
        value = get(record, path)
        if value:
            terms += p.term(vocab_id, value).get("eric", [])
    verified = p.verified_eric()
    unique = list(dict.fromkeys(terms))
    return unique if include_unverified else [t for t in unique if t in verified]


# ------------------------------------------------------------------- DataCite
def _ethics_text(record: dict, p: Profile) -> str:
    e = record["study"]["ethics"]
    parts = []
    for key, vocab_id, label in [
        ("human_subjects_review", "human_subjects_review", "Human-subjects review"),
        ("consent", "consent", "Participation consent"),
        ("consent_for_sharing", "consent_for_sharing", "Consent for data sharing"),
        ("identifiability", "identifiability", "Identifiability"),
        ("access_level", "access_level", "Access level"),
    ]:
        if e.get(key):
            parts.append(f"{label}: {p.label(vocab_id, e[key])}.")
    if record["study"]["population"].get("human_participants"):
        parts.insert(0, f"Human participants: {p.label('human_participants', record['study']['population']['human_participants'])}.")
    online = [p.label("online_data_practice", x) for x in e.get("online_data") or []]
    if online:
        parts.append("Online data: " + "; ".join(online) + ".")
    flags = [p.label("sensitivity_flag", f) for f in e.get("sensitivity_flags") or []]
    if flags:
        parts.append("Sensitivity: " + "; ".join(flags) + ".")
    if (e.get("governance_notes") or "").strip():
        parts.append(e["governance_notes"].strip())
    return "Ethics and access (HuMeta profile). " + " ".join(parts)


def _care_text(record: dict, p: Profile) -> str | None:
    care = record["study"]["care"]
    if not care.get("indigenous_data"):
        return None
    parts = [f"Indigenous data: {p.label('indigenous_data', care['indigenous_data'])}."]
    if care.get("governance"):
        parts.append(f"Governance: {p.label('indigenous_governance', care['governance'])}.")
    if care.get("local_contexts_labels"):
        parts.append("Local Contexts Labels/Notices: " + "; ".join(care["local_contexts_labels"]) + ".")
    if (care.get("statement") or "").strip():
        parts.append(care["statement"].strip())
    return "CARE statement (HuMeta profile). " + " ".join(parts)


def _methods_text(record: dict, p: Profile, lib: Library | None = None) -> str | None:
    lib = lib or Library.load()
    s = record["study"]
    parts = []
    designs = [p.label("study_design", d) for d in s["evidence"].get("study_designs") or []]
    if designs:
        parts.append("Study design: " + "; ".join(designs) + ".")
    if (s["design"].get("research_questions") or "").strip():
        parts.append("Research questions: " + s["design"]["research_questions"].strip())
    frameworks = [lib.frameworks[f]["label"] for f in s["design"].get("frameworks") or [] if f in lib.frameworks]
    if frameworks:
        parts.append("Theoretical framework: " + "; ".join(frameworks) + ".")
    if (s["design"].get("framework_description") or "").strip():
        parts.append(s["design"]["framework_description"].strip())
    sampling = [p.label("sampling_procedure", m) for m in s["design"].get("sampling_procedure") or []]
    if sampling:
        parts.append("Sampling: " + "; ".join(sampling) + ".")
    methods = [p.label("data_collection_method", m) for m in s["evidence"].get("data_collection_methods") or []]
    if methods:
        parts.append("Data collection: " + "; ".join(methods) + ".")
    analysis = [p.label("analysis_method", m) for m in s["evidence"].get("analysis_methods") or []]
    if analysis:
        parts.append("Analysis: " + "; ".join(analysis) + ".")
    src = s.get("sources") or {}
    types = [p.label("source_type", t) for t in src.get("types") or []]
    if types:
        parts.append("Sources: " + "; ".join(types) + ".")
    for key, label in (("description", "Sources"), ("holdings", "Held at"), ("time_period", "Period covered")):
        if (src.get(key) or "").strip():
            parts.append(f"{label}: {src[key].strip()}")
    if (s["population"].get("description") or "").strip():
        parts.append("Participants: " + s["population"]["description"].strip())
    return " ".join(parts) or None


def to_datacite_json(record: dict, lib: Library | None = None, profile: Profile | None = None) -> dict:
    """DataCite 4.7 metadata in the JSON 'attributes' form used by the DataCite REST API."""
    p = profile or load()
    lib = lib or Library.load()
    record = migrate(record, p)
    res, s = record["resource"], record["study"]
    out: dict[str, Any] = {
        "types": {"resourceTypeGeneral": res["resource_type"], "resourceType": f"HuMeta {res['resource_type']}"},
        "titles": [{"title": res["title"]}],
        "creators": [],
        "publisher": {"name": res["publisher"]},
        "publicationYear": str(res["publication_year"]),
        "subjects": [],
        "descriptions": [],
        "schemaVersion": "http://datacite.org/schema/kernel-4",
    }
    if res.get("identifier") and res["identifier"].get("type") == "DOI":
        out["doi"] = res["identifier"]["value"]
    for c in res["creators"]:
        creator: dict[str, Any] = {"name": c["name"], "nameType": "Personal"}
        if c.get("orcid"):
            creator["nameIdentifiers"] = [{"nameIdentifier": f"https://orcid.org/{c['orcid']}",
                                           "nameIdentifierScheme": "ORCID", "schemeUri": "https://orcid.org"}]
        if c.get("affiliation"):
            creator["affiliation"] = [{"name": c["affiliation"]}]
        out["creators"].append(creator)
    subjects = out["subjects"]
    for kw in res.get("keywords") or []:
        subjects.append({"subject": kw})
    if (s.get("design", {}).get("topic") or "").strip():
        subjects.append({"subject": s["design"]["topic"].strip()})
    for c in s.get("constructs", []):
        construct = lib.constructs.get(c["construct_id"])
        if construct:
            subjects.append({"subject": construct["label"], "subjectScheme": "HuMeta Constructs",
                             "schemeUri": CONSTRUCTS_URI.rstrip("#"), "valueUri": CONSTRUCTS_URI + construct["id"]})
    for fid in s["design"].get("frameworks") or []:
        framework = lib.frameworks.get(fid)
        if framework:
            subjects.append({"subject": framework["label"], "subjectScheme": "HuMeta Frameworks",
                             "schemeUri": FRAMEWORKS_URI.rstrip("#"), "valueUri": FRAMEWORKS_URI + fid})
    for path, (vocab_id, scheme) in VOCAB_FIELDS.items():
        if not scheme:
            continue
        for term_id in get(record, path) or []:
            subjects.append({"subject": p.label(vocab_id, term_id), "subjectScheme": scheme,
                             "schemeUri": VOCAB_URI.rstrip("#"), "valueUri": f"{VOCAB_URI}{vocab_id}.{term_id}"})
            isced = p.term(vocab_id, term_id).get("isced")
            if isced is not None:
                subjects.append({"subject": f"ISCED level {isced}: {ISCED_LEVELS[isced]}",
                                 "subjectScheme": ISCED_SCHEME, "schemeUri": ISCED_SCHEME_URI})
    fos_codes: list[str] = []
    for vocab_id, path in (("research_field", ("study", "fields")), ("discipline", ("study", "discipline"))):
        for term_id in get(record, path) or []:
            code = p.term(vocab_id, term_id).get("fos")
            if code and code not in fos_codes:
                fos_codes.append(code)
    for code in fos_codes:
        subjects.append({"subject": f"FOS: {FOS_LABELS[code]}", "subjectScheme": FOS_SCHEME,
                         "schemeUri": FOS_SCHEME_URI, "classificationCode": code})
    for term in eric_descriptors(record, lib, p):
        subjects.append({"subject": term, "subjectScheme": ERIC_SCHEME, "schemeUri": ERIC_SCHEME_URI})
    if (res.get("description") or "").strip():
        out["descriptions"].append({"description": res["description"].strip(), "descriptionType": "Abstract"})
    methods = _methods_text(record, p, lib)
    if methods:
        out["descriptions"].append({"description": methods, "descriptionType": "Methods"})
    out["descriptions"].append({"description": _ethics_text(record, p), "descriptionType": "Other"})
    care = _care_text(record, p)
    if care:
        out["descriptions"].append({"description": care, "descriptionType": "Other"})
    rights = []
    lic = res.get("license") or {}
    if lic.get("spdx") or lic.get("name"):
        right = {"rights": lic.get("name") or lic["spdx"]}
        if lic.get("spdx"):
            right.update({"rightsIdentifier": lic["spdx"], "rightsIdentifierScheme": "SPDX", "schemeUri": "https://spdx.org/licenses/"})
        if lic.get("url"):
            right["rightsUri"] = lic["url"]
        rights.append(right)
    src_rights = (s.get("sources") or {}).get("rights")
    if src_rights:
        right = {"rights": f"Sources studied: {p.label('source_rights', src_rights)}"}
        rs = p.term("source_rights", src_rights).get("rs")
        if rs:
            right["rightsUri"] = RIGHTS_STATEMENTS_URI.format(rs)
        rights.append(right)
    if s["ethics"].get("access_level"):
        rights.append({"rights": f"Access: {p.label('access_level', s['ethics']['access_level'])}"})
    if rights:
        out["rightsList"] = rights
    if res.get("language"):
        out["language"] = res["language"]
    dates = res.get("collection_dates") or {}
    start, end = dates.get("start"), dates.get("end")
    if start or end:
        out["dates"] = [{"date": f"{start}/{end}" if start and end else (start or end), "dateType": "Collected"}]
    period = ((s.get("sources") or {}).get("time_period") or "").strip()
    match = re.fullmatch(r"(\d{3,4})(?:\s*[-–/]\s*(\d{3,4}))?", period)
    if match:  # free-text periods ("19th century") stay in the Methods description
        out.setdefault("dates", []).append({"date": "/".join(g for g in match.groups() if g), "dateType": "Coverage"})
    geo = res.get("geography") or {}
    places = [f"{st}, United States" for st in geo.get("us_states") or []] + [
        c for c in geo.get("countries") or [] if not (c == "US" and geo.get("us_states"))]
    if places:
        out["geoLocations"] = [{"geoLocationPlace": place} for place in places]
    if res.get("funding"):
        out["fundingReferences"] = [{k: v for k, v in {"funderName": f["funder_name"], "awardNumber": f.get("award_number")}.items() if v}
                                    for f in res["funding"]]
    if s["population"].get("sample_size") is not None:
        out["sizes"] = [f"N = {s['population']['sample_size']} participants"]
    related = [{"relatedIdentifier": r["identifier"], "relatedIdentifierType": r["identifier_type"], "relationType": r["relation"]}
               for r in res.get("related") or []]
    seen_instruments = set()
    for c in s.get("constructs", []):
        iid = c.get("instrument_id")
        if iid and iid not in seen_instruments and iid in lib.instruments:
            seen_instruments.add(iid)
            if res["resource_type"] == "Dataset":
                # The instrument itself (its library record) collected the data ...
                related.append({"relatedIdentifier": f"{LIBRARY_RECORD_URI}{iid}.json",
                                "relatedIdentifierType": "URL", "relationType": "IsCollectedBy"})
            doi = lib.instruments[iid].get("original_citation", {}).get("doi")
            if doi:
                # ... and the instrument's publication is cited.
                related.append({"relatedIdentifier": doi, "relatedIdentifierType": "DOI", "relationType": "References"})
    if s["care"].get("local_contexts_project"):
        related.append({"relatedIdentifier": s["care"]["local_contexts_project"], "relatedIdentifierType": "URL", "relationType": "IsDescribedBy"})
    if related:
        out["relatedIdentifiers"] = related
    return out


def to_datacite_xml(record: dict, lib: Library | None = None, profile: Profile | None = None) -> str:
    """DataCite 4.7 XML. Requires a DOI in resource.identifier (DataCite XML must have one)."""
    data = to_datacite_json(record, lib, profile)
    if "doi" not in data:
        raise ValueError("DataCite XML needs a DOI. Add the DOI, or use the JSON export to register a new DOI.")
    ET.register_namespace("", DATACITE_NS)
    ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")
    q = lambda tag: f"{{{DATACITE_NS}}}{tag}"  # noqa: E731
    root = ET.Element(q("resource"), {"{http://www.w3.org/2001/XMLSchema-instance}schemaLocation": f"{DATACITE_NS} {DATACITE_XSD}"})

    def sub(parent: ET.Element, tag: str, text: str | None = None, **attrs: str) -> ET.Element:
        el = ET.SubElement(parent, q(tag), {k: v for k, v in attrs.items() if v})
        if text is not None:
            el.text = text
        return el

    sub(root, "identifier", data["doi"], identifierType="DOI")
    creators = sub(root, "creators")
    for c in data["creators"]:
        creator = sub(creators, "creator")
        sub(creator, "creatorName", c["name"], nameType=c.get("nameType"))
        for ni in c.get("nameIdentifiers", []):
            sub(creator, "nameIdentifier", ni["nameIdentifier"], nameIdentifierScheme=ni["nameIdentifierScheme"], schemeURI=ni.get("schemeUri"))
        for aff in c.get("affiliation", []):
            sub(creator, "affiliation", aff["name"])
    titles = sub(root, "titles")
    for t in data["titles"]:
        sub(titles, "title", t["title"])
    sub(root, "publisher", data["publisher"]["name"])
    sub(root, "publicationYear", data["publicationYear"])
    sub(root, "resourceType", data["types"]["resourceType"], resourceTypeGeneral=data["types"]["resourceTypeGeneral"])
    if data["subjects"]:
        subjects = sub(root, "subjects")
        for s in data["subjects"]:
            sub(subjects, "subject", s["subject"], subjectScheme=s.get("subjectScheme"), schemeURI=s.get("schemeUri"),
                valueURI=s.get("valueUri"), classificationCode=s.get("classificationCode"))
    if data.get("dates"):
        dates = sub(root, "dates")
        for d in data["dates"]:
            sub(dates, "date", d["date"], dateType=d["dateType"])
    if data.get("language"):
        sub(root, "language", data["language"])
    if data.get("relatedIdentifiers"):
        rel = sub(root, "relatedIdentifiers")
        for r in data["relatedIdentifiers"]:
            sub(rel, "relatedIdentifier", r["relatedIdentifier"], relatedIdentifierType=r["relatedIdentifierType"], relationType=r["relationType"])
    if data.get("sizes"):
        sizes = sub(root, "sizes")
        for size in data["sizes"]:
            sub(sizes, "size", size)
    if data.get("rightsList"):
        rights = sub(root, "rightsList")
        for r in data["rightsList"]:
            sub(rights, "rights", r["rights"], rightsURI=r.get("rightsUri"), rightsIdentifier=r.get("rightsIdentifier"),
                rightsIdentifierScheme=r.get("rightsIdentifierScheme"), schemeURI=r.get("schemeUri"))
    if data["descriptions"]:
        descriptions = sub(root, "descriptions")
        for d in data["descriptions"]:
            sub(descriptions, "description", d["description"], descriptionType=d["descriptionType"])
    if data.get("geoLocations"):
        geos = sub(root, "geoLocations")
        for g in data["geoLocations"]:
            sub(sub(geos, "geoLocation"), "geoLocationPlace", g["geoLocationPlace"])
    if data.get("fundingReferences"):
        funding = sub(root, "fundingReferences")
        for f in data["fundingReferences"]:
            ref = sub(funding, "fundingReference")
            sub(ref, "funderName", f["funderName"])
            if f.get("awardNumber"):
                sub(ref, "awardNumber", f["awardNumber"])
    ET.indent(root)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")


# ------------------------------------------------- legacy Module 1 study record
def _labels(p: Profile, vocab_id: str, ids: list[str] | None) -> list[str]:
    return [p.label(vocab_id, term_id) for term_id in ids or []]


def to_study_record(record: dict, existing: dict | None = None, profile: Profile | None = None) -> dict:
    """Derive the study record that Module 2 and later modules read.

    The HuMeta record is the source of truth; this is a read-only view of it in
    the shape those modules expect. (A follow-up can switch them to read the
    HuMeta record directly and remove this.)
    """
    import time
    import uuid

    p = profile or load()
    existing = existing or {}
    res, s = record["resource"], record["study"]
    edu = record.get("education") or {}

    def first(vocab_id: str, value: str | list[str] | None) -> str:
        values = value if isinstance(value, list) else ([value] if value else [])
        labels = _labels(p, vocab_id, values)
        return labels[0] if labels else ""

    authors = [{"name": c["name"], "orcid": c.get("orcid") or ""} for c in res.get("creators") or []]
    dates = res.get("collection_dates") or {}
    geo = res.get("geography") or {}
    states = geo.get("us_states") or []
    lang = res.get("language") or ""
    metadata = {
        "authors": authors,
        "study_doi_or_persistent_identifier": (res.get("identifier") or {}).get("value") or "",
        "institution": res.get("publisher") or "",
        "funding_source": "; ".join(f["funder_name"] for f in res.get("funding") or []),
        "research_questions_and_aims": s["design"].get("research_questions") or "",
        "subject_keywords": ", ".join(res.get("keywords") or []),
        "language": lang,
        "unit_of_analysis": first("unit_of_analysis", s["design"].get("unit_of_analysis")),
        "sampling_procedure": first("sampling_procedure", s["design"].get("sampling_procedure")),
        "time_method": first("study_design", s["evidence"].get("study_designs")),
        "study_start_date": dates.get("start") or "",
        "study_end_date": dates.get("end") or "",
        "state_origin": states[0] if len(states) == 1 else ("National/Multi-State" if states else ""),
        "locale_setting": first("locale", s["context"].get("locale")),
        "participant_populations": _labels(p, "participant_role", s["population"].get("participant_roles")),
        "study_settings": _labels(p, "learning_environment", edu.get("learning_environments")),
        "grade_level": _labels(p, "education_level", edu.get("education_levels")),
        "undergraduate_level": _labels(p, "undergraduate_level", edu.get("undergraduate_levels")),
        "program_type": _labels(p, "institution_type", edu.get("institution_types")),
        "content_domain": s["design"].get("topic") or "",
        "ethics_review_status": first("human_subjects_review", s["ethics"].get("human_subjects_review")),
        "consent_or_authorization": first("consent", s["ethics"].get("consent")),
        "data_sensitivity_and_identifiers": _labels(p, "sensitivity_flag", s["ethics"].get("sensitivity_flags")),
        "planned_data_access": first("access_level", s["ethics"].get("access_level")),
        "governance_notes": s["ethics"].get("governance_notes") or "",
    }
    description = {"description": res.get("description") or "No description provided.", "metadata": metadata}
    return {
        "id": existing.get("id") or str(uuid.uuid4()),
        "study_title": res.get("title") or "",
        "principal_investigator": ", ".join(a["name"] for a in authors),
        "institution": res.get("publisher") or "",
        "funding_source": metadata["funding_source"],
        "study_description": json.dumps(description, ensure_ascii=False),
        "created_at": existing.get("created_at") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


# ----------------------------------------------------------------- alignments
MATCH_MARK = {"exact": "", "close": "≈", "related": "~"}


def element(element_id: str, profile: Profile | None = None) -> dict:
    p = profile or load()
    for e in p.definition["elements"]:
        if e["id"] == element_id:
            return e
    raise KeyError(f"No element {element_id!r} in the profile")


def alignment_badges(element_id: str, profile: Profile | None = None) -> str:
    """Short, label-ready summary of an element's alignments, e.g.
    "`DataCite: titles.title` `DC: title` `schema.org: name`" (≈ close, ~ related).
    Elements defined by this profile start with `HuMeta`."""
    p = profile or load()
    parts = []
    for a in element(element_id, p).get("alignments", []):
        short = p.definition["standards"][a["standard"]]["short"]
        if a["standard"] == "humeta":
            parts.append("`HuMeta`")
        else:
            badge = f"`{MATCH_MARK[a['match']]}{short}: {a['term']}`"
            if a.get("status") == "seeking_input":
                badge += f" {SEEKING_INPUT_BADGE}"
            parts.append(badge)
    return " ".join(parts)


def alignment_help(element_id: str, profile: Profile | None = None) -> str:
    """Tooltip text: the element's definition, then the standards it aligns with."""
    p = profile or load()
    e = element(element_id, p)
    own = [a for a in e.get("alignments", []) if a["standard"] == "humeta"]
    others = [a for a in e.get("alignments", []) if a["standard"] != "humeta"]
    lines = [e["definition"]]
    if others:
        bullets = []
        for a in others:
            std = p.definition["standards"][a["standard"]]
            line = f"- {a['match'].capitalize()} match: {std['name']} — `{a['term']}`."
            if a.get("status") == "seeking_input":
                line += f" *{p.definition['alignment_status']['seeking_input']}*"
            if a.get("note"):
                line += f" {a['note']}"
            bullets.append(line)
        lines.append("**Matches in other standards**\n" + "\n".join(bullets))
    if own and not others:
        lines.append("Defined by the HuMeta profile; no general-purpose metadata standard has an equivalent.")
    elif own and e.get("vocabulary"):
        lines.append("The answer options are defined by the HuMeta profile.")
    return "\n\n".join(lines)
