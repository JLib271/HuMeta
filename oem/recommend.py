# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Community recommendations for the library: frameworks, instruments, corrections.

Researchers recommend theories, lenses, and frameworks, or instruments for
measuring constructs, from Module 2 (or through GitHub issue forms). Each
recommendation becomes one JSON file in ``suggestions/<kind>/`` on a pull
request, reviewed against ``suggestions/README.md`` before anything is added
to ``library/``.

Recommendations state their alignment explicitly: a framework lists its
constructs (and, optionally, the shared construct and instruments for each);
an instrument maps each of its parts (the whole instrument or each subscale)
to the construct it measures. These are *proposed* mappings. Which instruments
map to which constructs is decided by the HuMeta governance committee.

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
    "analysis": "suggestions/analyses/",
}
FRAMEWORK_KINDS = {
    "theory": "Theory (with constructs and expected relationships)",
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


def _cell(value) -> str:
    if value is None or (isinstance(value, float) and value != value):
        return ""
    return str(value).strip()


def framework_constructs(rows: list[dict]) -> list[dict]:
    """Rows of {construct, definition, shared_construct_id, instruments} from the form's table."""
    out = []
    for row in rows or []:
        label = _cell(row.get("construct"))
        if not label:
            continue
        item = {"label": label}
        for key in ("definition", "shared_construct_id", "instruments"):
            if _cell(row.get(key)):
                item[key] = _cell(row.get(key))
        out.append(item)
    return out


def instrument_alignment(rows: list[dict]) -> list[dict]:
    """Rows of {part, items, shared_construct_id, other_construct, theory_construct} from the form's table."""
    out = []
    for row in rows or []:
        part = _cell(row.get("part"))
        if not part and not any(_cell(row.get(k)) for k in ("shared_construct_id", "other_construct")):
            continue
        out.append({"part": part, "items": _cell(row.get("items")),
                    "shared_construct_id": _cell(row.get("shared_construct_id")) or None,
                    "other_construct": _cell(row.get("other_construct")),
                    "theory_construct": _cell(row.get("theory_construct"))})
    return out


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
                             fields: list[str] | None = None, constructs: list[dict] | None = None,
                             relationships: str = "", rationale: str = "", submitter_role: str = "") -> dict:
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
        "constructs": framework_constructs(constructs or []),
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
    if rec["kind"] == "theory" and not rec["constructs"]:
        issues.append("List the theory's constructs.")
    labels = {c["label"].lower() for c in rec["constructs"]}
    for r in rec["relationships"]:
        if r["from"].lower() not in labels or r["to"].lower() not in labels:
            issues.append(f"Relationship '{r['from']} -> {r['to']}' should use constructs from your list.")
    if lib is not None:
        for c in rec["constructs"]:
            if c.get("shared_construct_id") and c["shared_construct_id"] not in lib.constructs:
                issues.append(f"Construct '{c['label']}': unknown shared construct {c['shared_construct_id']!r}.")
    if lib is not None:
        existing = {f["label"].lower() for f in lib.frameworks.values()}
        if rec["name"].lower() in existing:
            issues.append("That framework is already in the list. To change it, suggest a correction instead.")
    return issues


# ----------------------------------------------------------- instruments
#: How an instrument was conceived; a theory is optional (library/schema/instrument.schema.json, development.basis)
DEVELOPMENT_OPTIONS = {
    "construct_definition": "From a definition of what to measure (no theory named)",
    "theory": "From a theory or framework",
    "practical_need": "For a practical or instructional need",
    "not_reported": "Not sure / not reported",
}


def instrument_recommendation(*, name: str, citation: str, alignment: list[dict], acronym: str = "", doi: str = "",
                              respondents: str = "",
                              populations: str = "", item_count: str = "", response_format: str = "",
                              access: str = "not_sure", access_details: str = "", url: str = "",
                              evidence: str = "", relationship: str = "aware", item_text_permission: bool = False,
                              construct: str = "", notes: str = "", development: str = "not_reported",
                              theory: str = "") -> dict:
    return {
        "recommendation": "instrument",
        "format_version": 1,
        "submitted_at_utc": _now(),
        "name": name.strip(),
        "acronym": acronym.strip(),
        "citation": citation.strip(),
        "doi": clean_doi(doi),
        "alignment": instrument_alignment(alignment),
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
        "for_construct": construct.strip(),
        "development_basis": development if development in DEVELOPMENT_OPTIONS else "not_reported",
        "theory": theory.strip(),
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
    if not rec["alignment"]:
        issues.append("Fill in the alignment table: for the whole instrument or each subscale, the construct it measures.")
    for i, row in enumerate(rec["alignment"], start=1):
        if not row["part"]:
            issues.append(f"Alignment row {i}: name the part (the whole instrument or a subscale).")
        if not (row["shared_construct_id"] or row["other_construct"]):
            issues.append(f"Alignment row {i} ({row['part'] or 'unnamed'}): say which construct it measures.")
    if rec["access"] not in ACCESS_OPTIONS:
        issues.append("Say how researchers can get it.")
    if rec["url"] and not re.match(r"^https?://", rec["url"]):
        issues.append("The link should start with http:// or https://.")
    if lib is not None:
        unknown = [r["shared_construct_id"] for r in rec["alignment"]
                   if r["shared_construct_id"] and r["shared_construct_id"] not in lib.constructs]
        if unknown:
            issues.append("Unknown constructs: " + ", ".join(unknown))
        names = {i["name"].lower() for i in lib.instruments.values()} | {
            (i.get("acronym") or "").lower() for i in lib.instruments.values() if i.get("acronym")}
        if rec["name"].lower() in names or (rec["acronym"] and rec["acronym"].lower() in names):
            issues.append("That instrument is already in the library. To change it, suggest a correction instead.")
    return issues


# ----------------------------------------------------------- analyses
def analysis_recommendation(*, name: str, purpose: str, when_to_use: str = "", software: str = "",
                            citation: str = "", doi: str = "") -> dict:
    return {"recommendation": "analysis", "format_version": 1, "submitted_at_utc": _now(), "name": name.strip(),
            "purpose": purpose.strip(), "when_to_use": when_to_use.strip(), "software": software.strip(),
            "citation": citation.strip(), "doi": clean_doi(doi)}


def analysis_problems(rec: dict) -> list[str]:
    issues = []
    if not rec["name"]:
        issues.append("Name the analysis (e.g., McDonald's omega, confirmatory factor analysis).")
    if not rec["purpose"]:
        issues.append("Say what it tells researchers.")
    if rec["doi"] and not DOI_PATTERN.match(rec["doi"]):
        issues.append("The DOI should look like 10.xxxx/xxxxx.")
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
                 f"**Citation:** {rec['citation']}" + (f" https://doi.org/{rec['doi']}" if rec["doi"] else "")]
        if rec["constructs"]:
            lines.append("**Proposed constructs** (for governance committee decision)\n\n"
                         "| Construct | Definition | Shared construct | Instruments that measure it |\n|---|---|---|---|\n"
                         + "\n".join(f"| {c['label']} | {c.get('definition', '')} | {c.get('shared_construct_id', '')} | "
                                     f"{c.get('instruments', '')} |" for c in rec["constructs"]))
        checklist = ["Citation checked against the source", "Constructs and relationships match the source",
                     "Governance committee decided the links to shared constructs and instruments",
                     "Added to library/frameworks.json (citation_status: verified) and validate_library.py passes"]
    elif rec["recommendation"] == "instrument":
        lines = [f"**Recommended instrument:** {rec['name']}" + (f" ({rec['acronym']})" if rec["acronym"] else ""),
                 f"**Citation:** {rec['citation']}" + (f" https://doi.org/{rec['doi']}" if rec["doi"] else ""),
                 "**Proposed alignment** (for governance committee decision)\n\n"
                 "| Part | Items | Measures (shared construct) | Measures (other) | Theory construct |\n|---|---|---|---|---|\n"
                 + "\n".join(f"| {r['part']} | {r['items']} | {r['shared_construct_id'] or ''} | {r['other_construct']} | "
                             f"{r['theory_construct']} |" for r in rec["alignment"]),
                 f"**Access:** {ACCESS_OPTIONS.get(rec['access'], rec['access'])}",
                 f"**Submitter:** {RELATIONSHIPS.get(rec['submitter_relationship'], '')}"]
        if rec["developer_offers_item_text"]:
            lines.append("**The developer offers to share item text.** Confirm the license in writing before adding items.")
        checklist = ["Citation and DOI checked", "Subscales and items match the source",
                     "Governance committee decided which constructs each part maps to",
                     "Access and license terms confirmed; no item text added without documented permission",
                     "Added as library/instruments/<id>.json and validate_library.py passes"]
    elif rec["recommendation"] == "analysis":
        lines = [f"**Recommended analysis for Module 5:** {rec['name']}", rec["purpose"],
                 f"**When to use:** {rec['when_to_use']}" if rec["when_to_use"] else "",
                 f"**Software (R or Python package and function):** {rec['software']}" if rec["software"] else "",
                 f"**Citation:** {rec['citation']}" + (f" https://doi.org/{rec['doi']}" if rec["doi"] else "")]
        checklist = ["Method and citation checked", "Implemented with an established open-source package (pingouin in "
                     "the app, psych or lavaan in the R script), with tests", "Results checked against a published example"]
    else:
        lines = [f"**Correction to {rec['target_kind']}** `{rec['target_id']}`", rec["change"]]
        checklist = ["Change checked against the source", "Library files updated and validate_library.py passes"]
    return "\n\n".join(line for line in lines if line) + "\n\n**Maintainer checklist** (see suggestions/README.md)\n" + "\n".join(f"- [ ] {c}" for c in checklist)
