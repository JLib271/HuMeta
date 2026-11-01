# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""The STEMEd+ Metadata Application Profile.

The profile itself is data in ``standard/stemed-ap/`` (``profile.json`` and
``vocabularies.json``); this module loads it and works with records:

* :func:`empty_record` / :func:`from_project` create a record, pre-filled from
  an OpenEdMetadata project file (Modules 1 and 2) where possible.
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
PROFILE_DIR = ROOT / "standard" / "stemed-ap"
CONSTRUCTS_URI = "https://github.com/JLib271/OpenEdMetadata/blob/main/library/constructs.json#"
VOCAB_URI = "https://github.com/JLib271/OpenEdMetadata/blob/main/standard/stemed-ap/vocabularies.json#"
LIBRARY_RECORD_URI = "https://github.com/JLib271/OpenEdMetadata/blob/main/library/instruments/"
DATACITE_NS = "http://datacite.org/schema/kernel-4"
DATACITE_XSD = "http://schema.datacite.org/meta/kernel-4.7/metadata.xsd"
ERIC_SCHEME = "ERIC Thesaurus"
ERIC_SCHEME_URI = "https://eric.ed.gov/?ti=all"

#: record path -> (vocabulary id, DataCite subjectScheme label)
VOCAB_FIELDS: dict[tuple[str, ...], tuple[str, str]] = {
    ("discipline",): ("discipline", "STEMEd+ Disciplines"),
    ("population", "participant_roles"): ("participant_role", "STEMEd+ Participant Roles"),
    ("population", "education_levels"): ("education_level", "STEMEd+ Education Levels"),
    ("population", "undergraduate_levels"): ("undergraduate_level", "STEMEd+ Undergraduate Levels"),
    ("context", "institution_types"): ("institution_type", "STEMEd+ Institution Types"),
    ("context", "locale"): ("locale", "STEMEd+ Locales"),
    ("setting", "modality"): ("modality", "STEMEd+ Modalities"),
    ("setting", "learning_environments"): ("learning_environment", "STEMEd+ Learning Environments"),
    ("setting", "pedagogy"): ("pedagogy", "STEMEd+ Instructional Approaches"),
    ("evidence", "study_designs"): ("study_design", "STEMEd+ Study Designs"),
    ("evidence", "measurement_evidence"): ("measurement_evidence", "STEMEd+ Measurement Evidence"),
    ("evidence", "data_collection_methods"): ("data_collection_method", "STEMEd+ Data Collection Methods"),
    ("ethics", "sensitivity_flags"): ("sensitivity_flag", None),
}
#: single-valued vocabulary fields
VOCAB_SINGLE: dict[tuple[str, ...], str] = {
    ("ethics", "human_subjects_review"): "human_subjects_review",
    ("ethics", "consent"): "consent",
    ("ethics", "consent_for_sharing"): "consent_for_sharing",
    ("ethics", "identifiability"): "identifiability",
    ("ethics", "access_level"): "access_level",
    ("care", "indigenous_data"): "indigenous_data",
    ("care", "governance"): "indigenous_governance",
}
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
    """JSON Schema for a STEMEd+ record, generated from the profile definition."""
    p = profile or load()

    def enum_array(vocab_id: str) -> dict:
        return {"type": "array", "uniqueItems": True, "items": {"enum": p.ids(vocab_id)}}

    def enum_single(vocab_id: str) -> dict:
        return {"enum": p.ids(vocab_id) + [None]}

    stemed_sections: dict[str, dict] = {}
    for path, (vocab_id, _) in VOCAB_FIELDS.items():
        if len(path) == 1:
            stemed_sections[path[0]] = enum_array(vocab_id)
        else:
            stemed_sections.setdefault(path[0], {"type": "object", "additionalProperties": False, "properties": {}})
            stemed_sections[path[0]]["properties"][path[1]] = enum_array(vocab_id)
    for path, vocab_id in VOCAB_SINGLE.items():
        stemed_sections.setdefault(path[0], {"type": "object", "additionalProperties": False, "properties": {}})
        stemed_sections[path[0]]["properties"][path[1]] = enum_single(vocab_id)
    stemed_sections["population"]["properties"].update({
        "description": {"type": ["string", "null"]},
        "sample_size": {"type": ["integer", "null"], "minimum": 0},
    })
    stemed_sections["care"]["properties"].update({
        "statement": {"type": ["string", "null"]},
        "local_contexts_project": {"type": ["string", "null"], "format": "uri"},
        "local_contexts_labels": {"type": "array", "items": {"type": "string"}},
    })
    stemed_sections["constructs"] = {
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
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://github.com/JLib271/OpenEdMetadata/blob/main/standard/stemed-ap/schema/stemed-ap-record.schema.json",
        "title": f"STEMEd+ Metadata Application Profile record ({p.version})",
        "description": "Generated from standard/stemed-ap/profile.json and vocabularies.json by scripts/build_profile_artifacts.py. Do not edit by hand.",
        "type": "object",
        "additionalProperties": False,
        "required": ["profile", "profile_version", "resource", "stemed"],
        "properties": {
            "profile": {"const": "stemed-ap"},
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
            "stemed": {"type": "object", "additionalProperties": False, "properties": stemed_sections},
        },
    }


# ------------------------------------------------------------------- records
def empty_record(profile: Profile | None = None) -> dict:
    p = profile or load()
    stemed: dict[str, Any] = {"constructs": []}
    for path in VOCAB_FIELDS:
        if len(path) == 1:
            stemed[path[0]] = []
        else:
            stemed.setdefault(path[0], {})[path[1]] = []
    for path in VOCAB_SINGLE:
        stemed.setdefault(path[0], {})[path[1]] = None
    stemed["population"].update({"description": None, "sample_size": None})
    stemed["care"].update({"statement": None, "local_contexts_project": None, "local_contexts_labels": []})
    return {
        "profile": "stemed-ap",
        "profile_version": p.version,
        "resource": {"title": "", "creators": [], "publisher": "", "publication_year": None,
                     "resource_type": "Dataset", "keywords": [], "funding": [], "related": []},
        "stemed": stemed,
    }


def get(record: dict, path: tuple[str, ...]) -> Any:
    node: Any = record["stemed"]
    for key in path:
        node = (node or {}).get(key)
    return node


def _set(record: dict, path: tuple[str, ...], value: Any) -> None:
    node = record["stemed"]
    for key in path[:-1]:
        node = node.setdefault(key, {})
    node[path[-1]] = value


def _map_module1(p: Profile, vocab_id: str, answers: list[str] | str | None) -> list[str]:
    """Translate Module 1 answer labels into profile term ids (order kept, no duplicates)."""
    if not answers:
        return []
    if isinstance(answers, str):
        answers = [answers]
    found: list[str] = []
    for term in p.vocab(vocab_id):
        if any(a in term.get("module1", []) for a in answers) and term["id"] not in found:
            found.append(term["id"])
    return found


def _study_metadata(project: dict) -> tuple[dict, dict]:
    study = project.get("study") or {}
    try:
        description = json.loads(study.get("study_description") or "{}")
    except (TypeError, json.JSONDecodeError):
        description = {}
    return study, description if isinstance(description, dict) else {}


DISCIPLINE_KEYWORDS = {
    "biology": ["biology", "life science", "ecology", "genetics", "microbiology"],
    "chemistry": ["chemistry", "chemical"],
    "physics": ["physics"],
    "geoscience": ["geoscience", "geology", "earth science", "geography", "ocean"],
    "climate_science": ["climate", "environmental science", "atmospheric"],
    "astronomy": ["astronomy", "astrophysics", "space science"],
    "mathematics": ["mathematics", "math", "statistics", "calculus"],
    "computer_science": ["computer science", "computing", "programming", "computer and information"],
    "engineering": ["engineering"],
}


def suggest_disciplines(text: str) -> list[str]:
    lowered = f" {text.lower()} "
    return [d for d, words in DISCIPLINE_KEYWORDS.items() if any(w in lowered for w in words)]


def suggest_constructs(lib: Library, plan: dict) -> list[str]:
    """Match Module 2 variables to library constructs (variable keys, labels, synonyms)."""
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


def from_project(project: dict, lib: Library | None = None, profile: Profile | None = None) -> dict:
    """Build a record pre-filled from a project file (Module 1 study + Module 2 plan)."""
    p = profile or load()
    lib = lib or Library.load()
    record = empty_record(p)
    study, desc = _study_metadata(project)
    meta = desc.get("metadata") or {}
    res = record["resource"]
    res["title"] = str(study.get("study_title") or "")
    creators = []
    for author in meta.get("authors") or []:
        if isinstance(author, dict) and str(author.get("name") or "").strip():
            orcid = re.search(r"(\d{4}-){3}\d{3}[\dX]", str(author.get("orcid") or ""))
            creators.append({"name": author["name"].strip(), "orcid": orcid.group(0) if orcid else None,
                             "affiliation": meta.get("institution") or None})
    res["creators"] = creators
    res["publisher"] = str(meta.get("institution") or "")
    description = str(desc.get("description") or "").strip()
    res["description"] = None if description in ("", "No description provided.") else description
    res["keywords"] = [k.strip() for k in str(meta.get("subject_keywords") or "").split(",") if k.strip()]
    lang = re.search(r"\(([a-z]{2,3})\)", str(meta.get("language") or ""))
    res["language"] = lang.group(1) if lang else None
    if str(meta.get("funding_source") or "").strip() and meta["funding_source"].strip().lower() != "not funded":
        res["funding"] = [{"funder_name": meta["funding_source"].strip(), "award_number": None}]
    if meta.get("study_start_date") or meta.get("study_end_date"):
        res["collection_dates"] = {"start": meta.get("study_start_date") or None, "end": meta.get("study_end_date") or None}
    state = str(meta.get("state_origin") or "")
    res["geography"] = {"countries": ["US"], "us_states": [state] if re.fullmatch(r"[A-Z]{2}", state) else []} if state else None
    pid = str(meta.get("study_doi_or_persistent_identifier") or "").strip()
    doi = re.search(r"10\.\d{4,9}/\S+", pid)
    if doi:
        res["identifier"] = {"value": doi.group(0), "type": "DOI"}

    s = record["stemed"]
    s["discipline"] = suggest_disciplines(" ".join([str(meta.get("content_domain") or ""), str(meta.get("subject_keywords") or "")]))
    s["population"]["participant_roles"] = _map_module1(p, "participant_role", meta.get("participant_populations"))
    s["population"]["education_levels"] = _map_module1(p, "education_level", meta.get("grade_level"))
    s["population"]["undergraduate_levels"] = _map_module1(p, "undergraduate_level", meta.get("undergraduate_level"))
    s["context"]["institution_types"] = _map_module1(p, "institution_type", meta.get("program_type"))
    s["context"]["locale"] = _map_module1(p, "locale", meta.get("locale_setting"))
    s["setting"]["learning_environments"] = _map_module1(p, "learning_environment", meta.get("study_settings"))
    s["evidence"]["study_designs"] = _map_module1(p, "study_design", meta.get("time_method"))
    s["ethics"]["sensitivity_flags"] = _map_module1(p, "sensitivity_flag", meta.get("data_sensitivity_and_identifiers"))
    for path, vocab_id, key in [
        (("ethics", "human_subjects_review"), "human_subjects_review", "ethics_review_status"),
        (("ethics", "consent"), "consent", "consent_or_authorization"),
        (("ethics", "access_level"), "access_level", "planned_data_access"),
    ]:
        mapped = _map_module1(p, vocab_id, meta.get(key))
        _set(record, path, mapped[0] if mapped else None)
    s["constructs"] = [{"construct_id": c} for c in suggest_constructs(lib, project.get("module2_plan") or {})]
    return record


def migrate(record: dict, profile: Profile | None = None) -> dict:
    """Fill any keys missing from an older or partial record with defaults."""
    base = empty_record(profile)

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

    res, s = record["resource"], record["stemed"]
    rtype = res["resource_type"]
    for path, vocab_id in [(("population", "participant_roles"), "participant_role"),
                           (("population", "education_levels"), "education_level")]:
        if not get(record, path):
            issues.append(Issue("error", "stemed." + ".".join(path), f"Select at least one {p.vocabularies[vocab_id]['label'].lower()}."))
    for path in [("ethics", "human_subjects_review"), ("ethics", "consent_for_sharing"),
                 ("ethics", "identifiability"), ("ethics", "access_level"), ("care", "indigenous_data")]:
        if not get(record, path):
            issues.append(Issue("error", "stemed." + ".".join(path), "Required."))
    for c in s.get("constructs", []):
        if c["construct_id"] not in lib.constructs:
            issues.append(Issue("error", "stemed.constructs", f"Unknown construct {c['construct_id']!r}."))
        if c.get("instrument_id") and c["instrument_id"] not in lib.instruments:
            issues.append(Issue("error", "stemed.constructs", f"Unknown instrument {c['instrument_id']!r}."))

    rules = {r["check"]: r for r in p.definition["rules"]}

    def flag(check: str, element: str) -> None:
        r = rules[check]
        issues.append(Issue(r["severity"], element, r["message"], r["id"]))

    ethics, care = s["ethics"], s["care"]
    access = ethics.get("access_level")
    if rtype in ("Dataset", "Instrument") and not s.get("constructs"):
        flag("constructs_required", "stemed.constructs")
    if rtype in ("Dataset", "StudyRegistration") and not s["evidence"].get("study_designs"):
        flag("design_required", "stemed.evidence.study_designs")
    if rtype == "Instrument" and not s["evidence"].get("measurement_evidence"):
        flag("measurement_evidence_required", "stemed.evidence.measurement_evidence")
    if access == "open" and ethics.get("identifiability") not in (None, "deidentified", "anonymous", "aggregate_only", "synthetic", "not_applicable"):
        flag("open_requires_deidentified", "stemed.ethics.identifiability")
    if access == "open" and ethics.get("consent_for_sharing") not in (None, "broad_sharing", "not_applicable"):
        flag("open_requires_sharing_consent", "stemed.ethics.consent_for_sharing")
    if access in ("open", "registered") and ethics.get("human_subjects_review") in ("not_assessed", "pending"):
        flag("sharing_requires_review", "stemed.ethics.human_subjects_review")
    if care.get("indigenous_data") == "yes":
        if care.get("governance") in (None, "none", "not_applicable") or not (care.get("statement") or "").strip():
            flag("care_requires_governance", "stemed.care.governance")
        if access == "open" and care.get("governance") not in ("community_agreement", "tribal_review"):
            flag("care_open_requires_agreement", "stemed.ethics.access_level")
    if "education_records" in (ethics.get("sensitivity_flags") or []) and access not in (None, "closed", "metadata_only"):
        flag("education_records_review", "stemed.ethics.sensitivity_flags")
    if care.get("indigenous_data") == "unknown":
        flag("care_unknown", "stemed.care.indigenous_data")
    if care.get("indigenous_data") != "yes" and (
        "specific_community" in s["population"].get("participant_roles", [])
        or "tribal_college" in s["context"].get("institution_types", [])
    ):
        flag("care_prompt", "stemed.care.indigenous_data")
    if "direct_identifiers" in (ethics.get("sensitivity_flags") or []) and access not in (None, "closed", "metadata_only"):
        flag("identifiers_not_shared", "stemed.ethics.sensitivity_flags")
    return issues


def is_valid(record: dict, lib: Library | None = None, profile: Profile | None = None) -> bool:
    return not any(i.severity == "error" for i in validate(record, lib, profile))


# ----------------------------------------------------------------------- ERIC
def eric_descriptors(record: dict, lib: Library | None = None, profile: Profile | None = None,
                     include_unverified: bool = False) -> list[str]:
    """ERIC Thesaurus descriptors implied by the record (verified terms only by default)."""
    p = profile or load()
    lib = lib or Library.load()
    terms: list[str] = []
    for c in record["stemed"].get("constructs", []):
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
    e = record["stemed"]["ethics"]
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
    flags = [p.label("sensitivity_flag", f) for f in e.get("sensitivity_flags") or []]
    if flags:
        parts.append("Sensitivity: " + "; ".join(flags) + ".")
    return "Ethics and access (STEMEd+ AP). " + " ".join(parts)


def _care_text(record: dict, p: Profile) -> str | None:
    care = record["stemed"]["care"]
    if not care.get("indigenous_data"):
        return None
    parts = [f"Indigenous data: {p.label('indigenous_data', care['indigenous_data'])}."]
    if care.get("governance"):
        parts.append(f"Governance: {p.label('indigenous_governance', care['governance'])}.")
    if care.get("local_contexts_labels"):
        parts.append("Local Contexts Labels/Notices: " + "; ".join(care["local_contexts_labels"]) + ".")
    if (care.get("statement") or "").strip():
        parts.append(care["statement"].strip())
    return "CARE statement (STEMEd+ AP). " + " ".join(parts)


def _methods_text(record: dict, p: Profile) -> str | None:
    s = record["stemed"]
    parts = []
    designs = [p.label("study_design", d) for d in s["evidence"].get("study_designs") or []]
    if designs:
        parts.append("Study design: " + "; ".join(designs) + ".")
    methods = [p.label("data_collection_method", m) for m in s["evidence"].get("data_collection_methods") or []]
    if methods:
        parts.append("Data collection: " + "; ".join(methods) + ".")
    if (s["population"].get("description") or "").strip():
        parts.append("Participants: " + s["population"]["description"].strip())
    return " ".join(parts) or None


def to_datacite_json(record: dict, lib: Library | None = None, profile: Profile | None = None) -> dict:
    """DataCite 4.7 metadata in the JSON 'attributes' form used by the DataCite REST API."""
    p = profile or load()
    lib = lib or Library.load()
    res, s = record["resource"], record["stemed"]
    out: dict[str, Any] = {
        "types": {"resourceTypeGeneral": res["resource_type"], "resourceType": f"STEMEd+ {res['resource_type']}"},
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
    for c in s.get("constructs", []):
        construct = lib.constructs.get(c["construct_id"])
        if construct:
            subjects.append({"subject": construct["label"], "subjectScheme": "STEMEd+ Constructs",
                             "schemeUri": CONSTRUCTS_URI.rstrip("#"), "valueUri": CONSTRUCTS_URI + construct["id"]})
    for path, (vocab_id, scheme) in VOCAB_FIELDS.items():
        if not scheme:
            continue
        for term_id in get(record, path) or []:
            subjects.append({"subject": p.label(vocab_id, term_id), "subjectScheme": scheme,
                             "schemeUri": VOCAB_URI.rstrip("#"), "valueUri": f"{VOCAB_URI}{vocab_id}.{term_id}"})
    for term in eric_descriptors(record, lib, p):
        subjects.append({"subject": term, "subjectScheme": ERIC_SCHEME, "schemeUri": ERIC_SCHEME_URI})
    if (res.get("description") or "").strip():
        out["descriptions"].append({"description": res["description"].strip(), "descriptionType": "Abstract"})
    methods = _methods_text(record, p)
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
            sub(subjects, "subject", s["subject"], subjectScheme=s.get("subjectScheme"), schemeURI=s.get("schemeUri"), valueURI=s.get("valueUri"))
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
