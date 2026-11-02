# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Community recommendations for the library: frameworks, instruments, corrections.

Researchers recommend theories, lenses, and frameworks, or instruments for
measuring concepts, from Module 2 (or through GitHub issue forms). Each
recommendation becomes one JSON file in ``suggestions/<kind>/`` on a pull
request that maintainers review against ``suggestions/README.md`` before
adding anything to ``library/``.

The functions here build and check those files. Nothing here imports
Streamlit.
"""

from __future__ import annotations

import json
import re
import time

from oem.library import Library

FOLDERS = {
    "framework": "suggestions/frameworks/",
    "instrument": "suggestions/instruments/",
    "correction": "suggestions/corrections/",
}
FRAMEWORK_KINDS = {
    "theory": "Theory (with concepts and expected relationships)",
    "conceptual_model": "Conceptual model or framework",
    "lens": "Theoretical lens or perspective",
}
ACCESS_OPTIONS = {
    "open_download": "Free to download and use",
    "open_license": "Openly licensed (e.g., Creative Commons)",
    "request_from_developer": "Free, but request from the developer",
    "permission_needed": "Permission needed / restricted",
    "commercial": "Commercial (purchase or license)",
    "not_sure": "Not sure",
}
RELATIONSHIPS = {
    "developer": "I developed it (or am one of the developers)",
    "user": "I have used it in research",
    "aware": "I know of it but have not used it",
}
DOI_PATTERN = re.compile(r"^10\.\d{4,9}/\S+$")


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _slug(text: str, max_length: int = 50) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")[:max_length].strip("-") or "item"


def clean_doi(value: str) -> str:
    """'https://doi.org/10.1/x' or 'doi:10.1/x' -> '10.1/x'."""
    value = str(value or "").strip()
    value = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", value, flags=re.I)
    return value


def _lines(text: str) -> list[str]:
    return [line.strip(" -•\t") for line in str(text or "").splitlines() if line.strip(" -•\t")]


def parse_concepts(text: str) -> list[dict]:
    """One concept per line, optionally 'Concept: definition'."""
    concepts = []
    for line in _lines(text):
        label, _, definition = line.partition(":")
        concepts.append({"label": label.strip(), **({"definition": definition.strip()} if definition.strip() else {})})
    return concepts


def parse_relationships(text: str) -> list[dict]:
    """One per line: 'A -> B: relationship' (or 'A → B')."""
    rels = []
    for line in _lines(text):
        head, _, relationship = line.partition(":")
        parts = re.split(r"\s*(?:->|→)\s*", head)
        if len(parts) == 2 and all(parts):
            rels.append({"from": parts[0].strip(), "to": parts[1].strip(), "relationship": relationship.strip()})
    return rels


# ----------------------------------------------------------- frameworks
def framework_recommendation(*, name: str, kind: str, description: str, citation: str, doi: str = "",
                             fields: list[str] | None = None, concepts: str = "", relationships: str = "",
                             rationale: str = "", submitter_role: str = "") -> dict:
    return {
        "recommendation": "framework",
        "format_version": 1,
        "submitted_at_utc": _now(),
        "name": name.strip(),
        "kind": kind,
        "description": description.strip(),
        "citation": citation.strip(),
        "doi": clean_doi(doi),
        "fields": list(fields or []),
        "concepts": parse_concepts(concepts),
        "relationships": parse_relationships(relationships),
        "rationale": rationale.strip(),
        "submitter_role": submitter_role.strip(),
    }


def framework_problems(rec: dict, lib: Library | None = None) -> list[str]:
    issues = []
    if not rec["name"]:
        issues.append("Give the framework's name.")
    if rec["kind"] not in FRAMEWORK_KINDS:
        issues.append("Choose what kind of framework it is.")
    if not rec["description"]:
        issues.append("Describe the framework in a sentence or two.")
    if not rec["citation"]:
        issues.append("Give a key citation, so reviewers can check it.")
    if rec["doi"] and not DOI_PATTERN.match(rec["doi"]):
        issues.append("The DOI should look like 10.xxxx/xxxxx.")
    if rec["kind"] == "theory" and not rec["concepts"]:
        issues.append("List the theory's concepts, one per line.")
    labels = {c["label"].lower() for c in rec["concepts"]}
    for r in rec["relationships"]:
        if r["from"].lower() not in labels or r["to"].lower() not in labels:
            issues.append(f"Relationship '{r['from']} -> {r['to']}' should use concepts from your list.")
    if lib is not None:
        existing = {f["label"].lower() for f in lib.frameworks.values()}
        if rec["name"].lower() in existing:
            issues.append("That framework is already in the list. To change it, suggest a correction instead.")
    return issues


# ----------------------------------------------------------- instruments
def instrument_recommendation(*, name: str, citation: str, construct_ids: list[str], acronym: str = "", doi: str = "",
                              other_constructs: str = "", subscales: str = "", respondents: str = "",
                              populations: str = "", item_count: str = "", response_format: str = "",
                              access: str = "not_sure", access_details: str = "", url: str = "",
                              evidence: str = "", relationship: str = "aware", item_text_permission: bool = False,
                              concept: str = "", notes: str = "") -> dict:
    return {
        "recommendation": "instrument",
        "format_version": 1,
        "submitted_at_utc": _now(),
        "name": name.strip(),
        "acronym": acronym.strip(),
        "citation": citation.strip(),
        "doi": clean_doi(doi),
        "construct_ids": list(construct_ids),
        "other_constructs": _lines(other_constructs),
        "subscales": parse_concepts(subscales),
        "respondents": respondents.strip(),
        "populations": populations.strip(),
        "item_count": item_count.strip(),
        "response_format": response_format.strip(),
        "access": access,
        "access_details": access_details.strip(),
        "url": url.strip(),
        "evidence": evidence.strip(),
        "submitter_relationship": relationship,
        "developer_offers_item_text": bool(item_text_permission and relationship == "developer"),
        "for_concept": concept.strip(),
        "notes": notes.strip(),
    }


def instrument_problems(rec: dict, lib: Library | None = None) -> list[str]:
    issues = []
    if not rec["name"]:
        issues.append("Give the instrument's name.")
    if not rec["citation"]:
        issues.append("Give the instrument's primary citation.")
    if rec["doi"] and not DOI_PATTERN.match(rec["doi"]):
        issues.append("The DOI should look like 10.xxxx/xxxxx.")
    if not rec["construct_ids"] and not rec["other_constructs"]:
        issues.append("Say what it measures: choose constructs, or describe others.")
    if rec["access"] not in ACCESS_OPTIONS:
        issues.append("Say how researchers can get it.")
    if rec["url"] and not re.match(r"^https?://", rec["url"]):
        issues.append("The link should start with http:// or https://.")
    if lib is not None:
        unknown = [c for c in rec["construct_ids"] if c not in lib.constructs]
        if unknown:
            issues.append("Unknown constructs: " + ", ".join(unknown))
        names = {i["name"].lower() for i in lib.instruments.values()} | {
            (i.get("acronym") or "").lower() for i in lib.instruments.values() if i.get("acronym")}
        if rec["name"].lower() in names or (rec["acronym"] and rec["acronym"].lower() in names):
            issues.append("That instrument is already in the library. To change it, suggest a correction instead.")
    return issues


# ----------------------------------------------------------- corrections
def correction(*, target_kind: str, target_id: str, change: str, source: str = "") -> dict:
    return {"recommendation": "correction", "format_version": 1, "submitted_at_utc": _now(),
            "target_kind": target_kind, "target_id": target_id, "change": change.strip(), "source": source.strip()}


def correction_problems(rec: dict) -> list[str]:
    issues = []
    if rec["target_kind"] not in ("framework", "instrument", "construct") or not rec["target_id"]:
        issues.append("Choose what you are correcting.")
    if not rec["change"]:
        issues.append("Describe the change.")
    return issues


# ----------------------------------------------------------- files
def file_for(rec: dict) -> tuple[str, str]:
    """(repository path, JSON text) for a recommendation."""
    kind = rec["recommendation"]
    name = rec.get("name") or f"{rec.get('target_kind', '')}-{rec.get('target_id', '')}"
    stamp = rec["submitted_at_utc"].replace(":", "").replace("-", "")[:15]
    return f"{FOLDERS[kind]}{_slug(name)}-{stamp}.json", json.dumps(rec, ensure_ascii=False, indent=2)


def title_for(rec: dict) -> str:
    if rec["recommendation"] == "correction":
        return f"Correction to {rec['target_kind']} {rec['target_id']}"
    return f"{rec['recommendation'].capitalize()}: {rec['name']}"[:120]


def pr_description(rec: dict) -> str:
    """Pull request text: what is proposed and the maintainer checklist."""
    if rec["recommendation"] == "framework":
        lines = [f"**Recommended framework:** {rec['name']} ({FRAMEWORK_KINDS.get(rec['kind'], rec['kind'])})",
                 f"**Citation:** {rec['citation']}" + (f" https://doi.org/{rec['doi']}" if rec["doi"] else ""),
                 f"**Concepts:** {', '.join(c['label'] for c in rec['concepts']) or 'none listed'}"]
        checklist = ["Citation checked against the source", "Concepts and relationships match the source",
                     "Concepts linked to constructs in library/constructs.json where one fits",
                     "Added to library/frameworks.json (citation_status: verified) and validate_library.py passes"]
    elif rec["recommendation"] == "instrument":
        lines = [f"**Recommended instrument:** {rec['name']}" + (f" ({rec['acronym']})" if rec["acronym"] else ""),
                 f"**Citation:** {rec['citation']}" + (f" https://doi.org/{rec['doi']}" if rec["doi"] else ""),
                 f"**Measures:** {', '.join(rec['construct_ids'] + rec['other_constructs'])}",
                 f"**Access:** {ACCESS_OPTIONS.get(rec['access'], rec['access'])}",
                 f"**Submitter:** {RELATIONSHIPS.get(rec['submitter_relationship'], '')}"]
        if rec["developer_offers_item_text"]:
            lines.append("**The developer offers to share item text.** Confirm the license in writing before adding items.")
        checklist = ["Citation and DOI checked", "Constructs and subscales match the source",
                     "Access and license terms confirmed; no item text added without documented permission",
                     "Added as library/instruments/<id>.json and validate_library.py passes"]
    else:
        lines = [f"**Correction to {rec['target_kind']}** `{rec['target_id']}`", rec["change"]]
        checklist = ["Change checked against the source", "Library files updated and validate_library.py passes"]
    return "\n\n".join(lines) + "\n\n**Maintainer checklist** (see suggestions/README.md)\n" + "\n".join(f"- [ ] {c}" for c in checklist)
