# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""How the instrument library's records line up with the HuMeta standard.

* ``DATA_COLLECTION_METHOD``: an instrument type -> the HuMeta ``data_collection_method`` term it is used for.
* ``measurement_evidence``: the HuMeta ``measurement_evidence`` terms an instrument's evidence covers, from the
  rubric categories and criteria it meets (``library/evidence_rubric.json`` records each category's mapping)
  and from evidence outside the rubric (inter-rater agreement is reliability).

Nothing here imports Streamlit.
"""

from __future__ import annotations

from oem.library import Library

#: library instrument_type -> HuMeta data_collection_method
DATA_COLLECTION_METHOD = {
    "concept_inventory": "assessment",
    "performance_task": "assessment",
    "attitude_beliefs_survey": "survey",
    "self_report_scale": "survey",
    "observation_protocol": "observation",
    "interview_protocol": "interview",
    "rubric": "artifacts",
    "other": "other_method",
}

#: evidence types outside the rubric -> HuMeta measurement_evidence
OTHER_EVIDENCE = {"inter_rater": "reliability"}

#: order of HuMeta measurement_evidence terms (the Standards' sources of validity evidence, then reliability)
EVIDENCE_ORDER = ["test_content", "response_processes", "internal_structure", "relations_to_other_variables",
                  "consequences", "fairness", "reliability", "irt_scaling"]


def measurement_evidence(lib: Library, instrument_id: str) -> list[str]:
    """HuMeta measurement_evidence terms covered by an instrument's recorded evidence."""
    from oem import evidence as EV  # local import: evidence imports library

    prof = EV.profile(lib, instrument_id)
    by_cat = {c["id"]: c for c in lib.rubric}
    terms: set[str] = set()
    for cat in prof.categories:
        rubric_cat = by_cat.get(cat.id, {})
        crit_map = {c["id"]: c.get("humeta_evidence") for c in rubric_cat.get("criteria", [])}
        for crit in cat.criteria:
            if crit.status in ("met", "partly"):
                terms.update(crit_map.get(crit.id) or rubric_cat.get("humeta_evidence", []))
    for e in prof.other_evidence:
        if e.get("evidence_type") in OTHER_EVIDENCE:
            terms.add(OTHER_EVIDENCE[e["evidence_type"]])
    return [t for t in EVIDENCE_ORDER if t in terms]


def record_evidence(lib: Library, record: dict) -> list[str]:
    """HuMeta measurement_evidence terms one evidence record counts as."""
    from oem import evidence as EV

    by_cat = {c["id"]: c for c in lib.rubric}
    stat = (record.get("statistic") or {}).get("name")
    pairs = list(EV.BY_STATISTIC.get(stat, [])) + list(EV.BY_TYPE.get(record.get("evidence_type"), []))
    pairs += [(t["category"], t["criterion"]) for t in record.get("rubric", [])]
    terms: set[str] = set()
    for cat, letter in pairs:
        c = by_cat.get(cat, {})
        crit = next((x for x in c.get("criteria", []) if x["id"] == letter), {})
        terms.update(crit.get("humeta_evidence") or c.get("humeta_evidence", []))
    if record.get("evidence_type") in OTHER_EVIDENCE:
        terms.add(OTHER_EVIDENCE[record["evidence_type"]])
    return [t for t in EVIDENCE_ORDER if t in terms]


# ------------------------------------------------------------------ DataCite
#: KCWorks files instruments as Text document > Other, which maps to DataCite Text; DataCite's own "Instrument"
#: type is for the physical device instance, so it does not fit questionnaires, tests, or protocols.
RESOURCE_TYPE_GENERAL = "Text"
PUBLISHER = "HuMeta Instrument Library"
INSTRUMENT_SUBJECTS = (  # (record field, HuMeta vocabulary, DataCite subject scheme)
    ("education_levels", "education_level", "HuMeta Education Levels"),
    ("settings", "learning_environment", "HuMeta Learning Environments"),
    ("participants", "participant_role", "HuMeta Participant Roles"),
)
#: commons_records kind -> DataCite relationType from the instrument record to the deposit
DEPOSIT_RELATION = {"instrument": "IsVariantFormOf", "item_set": "HasPart", "manual": "IsDocumentedBy",
                    "paper": "IsDescribedBy", "link": "IsVariantFormOf", "other": "References"}


def _label(value: str | None) -> str:
    return (value or "").replace("_", " ")


def to_datacite_json(lib: Library, instrument_id: str, profile=None) -> dict:
    """DataCite 4.7 metadata (JSON 'attributes' form) describing an instrument library record."""
    from oem import profile as P
    from oem.vocab import library_page_url

    p = profile or P.load()
    inst = lib.instrument(instrument_id)
    versions = inst.get("versions", [])
    years = sorted(int(v["year"]) for v in versions if str(v.get("year", "")).isdigit())
    cite = inst.get("original_citation") or {}
    year = years[0] if years else None
    if year is None:
        import re
        m = re.search(r"\((\d{4})\)", cite.get("text", ""))
        year = int(m.group(1)) if m else None

    out: dict = {
        "types": {"resourceTypeGeneral": RESOURCE_TYPE_GENERAL,
                  "resourceType": f"Research instrument: {_label(inst.get('instrument_type'))}"},
        "titles": [{"title": inst["name"]}],
        "creators": [],
        "publisher": {"name": PUBLISHER},
        "publicationYear": str(year) if year else "",
        "subjects": [{"subject": "research instrument"}],
        "descriptions": [],
        "url": library_page_url("instruments", instrument_id),
        "schemaVersion": "http://datacite.org/schema/kernel-4",
    }
    if inst.get("acronym"):
        out["titles"].append({"title": inst["acronym"], "titleType": "AlternativeTitle"})
    for d in inst.get("developers", []):
        creator = {"name": d["name"], "nameType": "Personal"}
        if "," in d["name"]:
            family, given = (x.strip() for x in d["name"].split(",", 1))
            creator.update({"familyName": family, "givenName": given})
        if d.get("orcid"):
            creator["nameIdentifiers"] = [{"nameIdentifier": f"https://orcid.org/{d['orcid']}",
                                           "nameIdentifierScheme": "ORCID", "schemeUri": "https://orcid.org"}]
        out["creators"].append(creator)

    subjects = out["subjects"]
    for cid in inst.get("construct_ids", []):
        c = lib.constructs.get(cid)
        if c:
            subjects.append({"subject": c["label"], "subjectScheme": "HuMeta Constructs",
                             "schemeUri": P.CONSTRUCTS_URI.rstrip("#"), "valueUri": P.CONSTRUCTS_URI + cid})
    for fid in (inst.get("development") or {}).get("framework_ids", []):
        f = lib.frameworks.get(fid)
        if f:
            subjects.append({"subject": f["label"], "subjectScheme": "HuMeta Frameworks",
                             "schemeUri": P.FRAMEWORKS_URI.rstrip("#"), "valueUri": P.FRAMEWORKS_URI + fid})
    subjects += P.vocab_subjects(p, "discipline", "HuMeta Disciplines",
                                 [d for d in inst.get("disciplines", []) if p.term("discipline", d)])
    for field, vocab_id, scheme in INSTRUMENT_SUBJECTS:
        subjects += P.vocab_subjects(p, vocab_id, scheme, inst.get(field, []))
    method = DATA_COLLECTION_METHOD.get(inst.get("instrument_type"))
    if method:
        subjects += P.vocab_subjects(p, "data_collection_method", "HuMeta Data Collection Methods", [method])
    subjects += P.vocab_subjects(p, "measurement_evidence", "HuMeta Measurement Evidence",
                                 measurement_evidence(lib, instrument_id))
    subjects += P.fos_subjects(p, [("discipline", d) for d in inst.get("disciplines", [])])

    if inst.get("description"):
        out["descriptions"].append({"description": inst["description"], "descriptionType": "Abstract"})
    tech = []
    for v in versions:
        bits = [v.get("label") or v["version_id"]]
        if v.get("item_count"):
            bits.append(f"{v['item_count']} items")
        rf = (v.get("response_format") or {}).get("type")
        if rf:
            bits.append(_label(rf))
        if (v.get("scoring") or {}).get("method"):
            bits.append(f"scored by {_label(v['scoring']['method'])}")
        tech.append(", ".join(bits))
    dims = [d["name"] for d in inst.get("dimensions", [])]
    if dims:
        tech.append("Subscales: " + "; ".join(dims))
    if tech:
        out["descriptions"].append({"description": ". ".join(tech) + ".", "descriptionType": "TechnicalInfo"})
    access = inst.get("access") or {}
    if access.get("terms_summary"):
        out["descriptions"].append({"description": f"Access: {access['terms_summary']}", "descriptionType": "Other"})

    rights = []
    basis = access.get("item_text_basis") or {}
    if access.get("item_text_shareable") and basis.get("license"):
        rights.append({"rights": f"Item text: {basis['license']}"})
    if access.get("terms_url"):
        rights.append({"rights": "Terms of use set by the developers", "rightsUri": access["terms_url"]})
    rights.append({"rights": "Library record: Creative Commons Attribution Share Alike 4.0 International",
                   "rightsIdentifier": "CC-BY-SA-4.0", "rightsIdentifierScheme": "SPDX",
                   "schemeUri": "https://spdx.org/licenses/", "rightsUri": "https://creativecommons.org/licenses/by-sa/4.0/"})
    out["rightsList"] = rights

    langs = [v.get("language") for v in versions if v.get("language")]
    if langs:
        out["language"] = langs[0]
    if versions:
        out["version"] = versions[-1].get("label") or versions[-1]["version_id"]
        if versions[-1].get("item_count"):
            out["sizes"] = [f"{versions[-1]['item_count']} items"]

    related, seen = [], set()

    def add(identifier, id_type, relation):
        if identifier and (identifier, relation) not in seen:
            seen.add((identifier, relation))
            related.append({"relatedIdentifier": identifier, "relatedIdentifierType": id_type, "relationType": relation})

    add(cite.get("doi"), "DOI", "IsDescribedBy")
    for v in versions:
        add((v.get("citation") or {}).get("doi"), "DOI", "IsDescribedBy")
    for r in inst.get("commons_records", []):
        relation = "IsVariantFormOf" if "instrument" in (r.get("contents") or []) else DEPOSIT_RELATION.get(r.get("kind"), "References")
        if r.get("doi"):
            add(r["doi"], "DOI", relation)
        else:
            add(r["url"], "URL", relation)
    for e in lib.evidence_for(instrument_id):
        add((e.get("source") or {}).get("doi"), "DOI", "IsDescribedBy")
    if related:
        out["relatedIdentifiers"] = related
    return out


def to_schema_org(lib: Library, instrument_id: str, profile=None) -> dict:
    """schema.org JSON-LD for an instrument's Library page (read by search engines)."""
    dc = to_datacite_json(lib, instrument_id, profile)
    inst = lib.instrument(instrument_id)
    out = {"@context": "https://schema.org", "@type": "CreativeWork",
           "additionalType": "https://schema.org/Survey" if inst.get("instrument_type") in ("attitude_beliefs_survey", "self_report_scale")
           else None,
           "name": inst["name"], "alternateName": inst.get("acronym"), "description": inst.get("description"),
           "url": dc["url"], "genre": dc["types"]["resourceType"],
           "author": [{"@type": "Person", "name": c["name"]} for c in dc["creators"]],
           "keywords": [s["subject"] for s in dc["subjects"]],
           "about": [{"@type": "DefinedTerm", "name": s["subject"], "url": s.get("valueUri"), "inDefinedTermSet": s.get("schemeUri")}
                     for s in dc["subjects"] if s.get("subjectScheme") == "HuMeta Constructs"],
           "educationalLevel": [s["subject"] for s in dc["subjects"] if s.get("subjectScheme") == "HuMeta Education Levels"],
           "inLanguage": dc.get("language"), "version": dc.get("version"),
           "license": "https://creativecommons.org/licenses/by-sa/4.0/",
           "citation": [f"https://doi.org/{r['relatedIdentifier']}" for r in dc.get("relatedIdentifiers", [])
                        if r["relatedIdentifierType"] == "DOI" and r["relationType"] == "IsDescribedBy"],
           "sameAs": [f"https://doi.org/{r['relatedIdentifier']}" if r["relatedIdentifierType"] == "DOI" else r["relatedIdentifier"]
                      for r in dc.get("relatedIdentifiers", []) if r["relationType"] == "IsVariantFormOf"],
           "isPartOf": {"@type": "Collection", "name": PUBLISHER, "url": dc["url"].rsplit("instruments/", 1)[0]}}
    return {k: v for k, v in out.items() if v not in (None, [], "")}
