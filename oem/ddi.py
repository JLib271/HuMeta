# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""DDI-Codebook 2.5 export.

DDI (the Data Documentation Initiative) is the social sciences' metadata
standard. ICPSR, CESSDA archives, the UK Data Service, and Dataverse use
DDI-Codebook. This module writes a HuMeta study profile, and optionally the
Module 2 variable plan, as a DDI-Codebook 2.5 XML file that a researcher can
give to an archive at deposit or keep with the data.

* Study level (``stdyDscr``): citation, abstract, keywords, coverage, unit of
  analysis, universe, kind of data, sampling, collection mode, weighting,
  response rate, sources, and access. Terms that map to a DDI Alliance
  controlled vocabulary carry it as a ``concept``.
* Variable level (``dataDscr``): one ``var`` per codebook variable (label,
  question text, codes, missing codes), grouped in a ``varGrp`` per construct
  and measure. Each variable names the construct it measures as a ``concept``
  from the HuMeta construct list, so the link from theory to measures travels
  with the DDI file.

Nothing here imports Streamlit. The output validates against the official
DDI-Codebook 2.5.1 schema (see ``tests/test_ddi.py``).
"""

from __future__ import annotations

import datetime as dt
from xml.etree import ElementTree as ET

from oem import codebook, naming
from oem import plan as plan_model
from oem import profile
from oem.library import Library

DDI_NS = "ddi:codebook:2_5"
DDI_XSD = "http://www.ddialliance.org/Specification/DDI-Codebook/2.5/XMLSchema/codebook.xsd"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
XML_NS = "http://www.w3.org/XML/1998/namespace"
DDI_CV = {"AnalysisUnit": "2.1.3", "SamplingProcedure": "2.0.2", "ModeOfCollection": "5.0.1",
          "TimeMethod": "1.2.1", "KindOfData": "1.0.0"}
CONSTRUCTS_VOCAB = "HuMeta Constructs"


def _cv_uri(cv: str) -> str:
    return f"{profile.DDI_CV_URI}{cv}/{DDI_CV[cv]}/"


class _Builder:
    def __init__(self) -> None:
        ET.register_namespace("", DDI_NS)
        ET.register_namespace("xsi", XSI_NS)

    @staticmethod
    def el(parent: ET.Element | None, tag: str, text: str | None = None, **attrs: str | None) -> ET.Element:
        name = f"{{{DDI_NS}}}{tag}"
        node = ET.Element(name) if parent is None else ET.SubElement(parent, name)
        for key, value in attrs.items():
            if value not in (None, ""):
                node.set(key.replace("_", "-") if key != "xml_lang" else f"{{{XML_NS}}}lang", str(value))
        if text not in (None, ""):
            node.text = str(text)
        return node


def _vocab_terms(p: profile.Profile, vocab_id: str, ids: list[str] | str | None) -> list[tuple[str, dict]]:
    ids = [ids] if isinstance(ids, str) else (ids or [])
    return [(p.label(vocab_id, t), p.term(vocab_id, t)) for t in ids]


def _coded(b: _Builder, parent: ET.Element, tag: str, label: str, term: dict, **attrs: str | None) -> None:
    """A DDI text element, with the DDI controlled-vocabulary term as a concept when the term maps to one."""
    node = b.el(parent, tag, label, **attrs)
    ddi = term.get("ddi") or {}
    if ddi.get("cv") in DDI_CV and ddi.get("match") in ("exact", "close"):
        b.el(node, "concept", ddi["code"], vocab=f"DDI {ddi['cv']}", vocabURI=_cv_uri(ddi["cv"]))


def to_ddi_codebook_xml(record: dict, plan: dict | None = None, lib: Library | None = None,
                        p: profile.Profile | None = None) -> str:
    """The study profile (and variable plan, if given) as DDI-Codebook 2.5 XML."""
    p = p or profile.load()
    lib = lib or Library.load()
    record = profile.migrate(record, p)
    res, s = record["resource"], record["study"]
    social = record.get("social_science") or {}
    b = _Builder()
    root = b.el(None, "codeBook", version="2.5", xml_lang=res.get("language") or None)
    root.set(f"{{{XSI_NS}}}schemaLocation", f"{DDI_NS} {DDI_XSD}")

    # Document description: who produced this DDI file
    doc_cit = b.el(b.el(root, "docDscr"), "citation")
    b.el(b.el(doc_cit, "titlStmt"), "titl", f"DDI-Codebook description of: {res['title']}")
    doc_prod = b.el(doc_cit, "prodStmt")
    b.el(doc_prod, "prodDate", dt.date.today().isoformat(), date=dt.date.today().isoformat())
    b.el(doc_prod, "software", "HuMeta Portal (HuMeta profile " + p.version + ")")

    # Study description
    study = b.el(root, "stdyDscr")
    cit = b.el(study, "citation")
    titl = b.el(cit, "titlStmt")
    b.el(titl, "titl", res["title"])
    ident = res.get("identifier") or {}
    if ident.get("value"):
        b.el(titl, "IDNo", ident["value"], agency=ident.get("type"))
    if res.get("creators"):
        rsp = b.el(cit, "rspStmt")
        for c in res["creators"]:
            b.el(rsp, "AuthEnty", c["name"], affiliation=c.get("affiliation"))
    prod = b.el(cit, "prodStmt")
    if res.get("publication_year"):
        b.el(prod, "prodDate", str(res["publication_year"]), date=str(res["publication_year"]))
    for f in res.get("funding") or []:
        b.el(prod, "fundAg", f["funder_name"])
    for f in res.get("funding") or []:
        if f.get("award_number"):
            b.el(prod, "grantNo", f["award_number"], agency=f["funder_name"])
    if res.get("publisher"):
        b.el(b.el(cit, "distStmt"), "distrbtr", res["publisher"])
    if social.get("ddi_record"):
        b.el(cit, "holdings", "Full study documentation (DDI) at the archive", URI=social["ddi_record"])

    info = b.el(study, "stdyInfo")
    keywords = list(res.get("keywords") or [])
    constructs = [lib.constructs[c["construct_id"]] for c in s.get("constructs") or [] if c["construct_id"] in lib.constructs]
    if keywords or constructs or (s["design"].get("topic") or "").strip():
        subj = b.el(info, "subject")
        for kw in keywords:
            b.el(subj, "keyword", kw)
        for c in constructs:
            b.el(subj, "keyword", c["label"], vocab=CONSTRUCTS_VOCAB, vocabURI=profile.CONSTRUCTS_URI.rstrip("#"))
        if (s["design"].get("topic") or "").strip():
            b.el(subj, "topcClas", s["design"]["topic"].strip())
    if (res.get("description") or "").strip():
        b.el(info, "abstract", res["description"].strip())
    summary = b.el(info, "sumDscr")
    period = ((s.get("sources") or {}).get("time_period") or "").strip()
    if period:
        b.el(summary, "timePrd", period)
    dates = res.get("collection_dates") or {}
    for event in ("start", "end"):
        if dates.get(event):
            b.el(summary, "collDate", dates[event], date=dates[event], event=event)
    geo = res.get("geography") or {}
    for country in geo.get("countries") or []:
        b.el(summary, "nation", country, abbr=country)
    for state in geo.get("us_states") or []:
        b.el(summary, "geogCover", f"{state}, United States")
    if (social.get("geographic_unit") or "").strip():
        b.el(summary, "geogUnit", social["geographic_unit"].strip())
    for label, term in _vocab_terms(p, "unit_of_analysis", s["design"].get("unit_of_analysis")):
        _coded(b, summary, "anlyUnit", label, term, unit=(term.get("ddi") or {}).get("code"))
    if (social.get("universe") or "").strip():
        b.el(summary, "universe", social["universe"].strip(), clusion="I")
    if social.get("kind_of_data"):
        _coded(b, summary, "dataKind", p.term("kind_of_data", social["kind_of_data"])["ddi"]["code"],
               p.term("kind_of_data", social["kind_of_data"]))
    if not len(summary):
        info.remove(summary)

    method = b.el(study, "method")
    coll = b.el(method, "dataColl")
    for label, term in _vocab_terms(p, "study_design", s["evidence"].get("study_designs")):
        if (term.get("ddi") or {}).get("cv") == "TimeMethod":
            _coded(b, coll, "timeMeth", label, term)
    for label, term in _vocab_terms(p, "sampling_procedure", s["design"].get("sampling_procedure")):
        _coded(b, coll, "sampProc", label, term)
    if s["population"].get("sample_size") is not None:
        b.el(b.el(coll, "targetSampleSize"), "sampleSize", str(s["population"]["sample_size"]))
    for label, term in _vocab_terms(p, "data_collection_method", s["evidence"].get("data_collection_methods")):
        _coded(b, coll, "collMode", label, term)
    src = s.get("sources") or {}
    source_lines = [p.label("source_type", t) for t in src.get("types") or []]
    source_lines += [x.strip() for x in (src.get("description"), src.get("holdings")) if (x or "").strip()]
    if source_lines:
        sources = b.el(coll, "sources")
        for line in source_lines:
            b.el(sources, "dataSrc", line)
    if (social.get("weighting") or "").strip():
        b.el(coll, "weight", social["weighting"].strip())
    if not len(coll):
        method.remove(coll)
    if (s["design"].get("research_questions") or "").strip():
        b.el(method, "notes", "Research questions: " + s["design"]["research_questions"].strip())
    frameworks = [lib.frameworks[f]["label"] for f in s["design"].get("frameworks") or [] if f in lib.frameworks]
    if frameworks:
        b.el(method, "notes", "Theoretical framework: " + "; ".join(frameworks))
    if (social.get("response_rate") or "").strip():
        b.el(b.el(method, "anlyInfo"), "respRate", social["response_rate"].strip())
    if not len(method):
        study.remove(method)

    access = b.el(study, "dataAccs")
    use = b.el(access, "useStmt")
    if s["ethics"].get("access_level"):
        b.el(use, "restrctn", "Access: " + p.label("access_level", s["ethics"]["access_level"]))
    lic = res.get("license") or {}
    if lic.get("name") or lic.get("spdx"):
        b.el(use, "conditions", "License: " + (lic.get("name") or lic["spdx"]) + (f" ({lic['url']})" if lic.get("url") else ""))
    if not len(use):
        study.remove(access)

    # Variables from the Module 2 variable plan
    if plan:
        _data_description(b, root, lib, plan_model.normalize(plan, lib))
    ET.indent(root)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"


def _var_id(index: int) -> str:
    return f"V{index}"


def _data_description(b: _Builder, root: ET.Element, lib: Library, plan: dict) -> None:
    book = plan_model.build_codebook(lib, plan)
    if not len(book):
        return
    ids = {v.name: _var_id(i) for i, v in enumerate(book.variables, start=1)}
    data = b.el(root, "dataDscr")
    # One variable group per construct and measure (all of its timepoints). Researcher-written
    # questions or codes for the same construct form one group, as in Module 5.
    timepoints = plan["timepoints"] or [None]
    merged: dict[tuple[str, str], dict] = {}
    for group in plan_model.measure_groups(lib, plan):
        slot = merged.setdefault((group["construct"]["id"], group["label"]),
                                 {"construct": group["construct"], "label": group["label"], "variables": []})
        slot["variables"] += group["variables"]
    construct_of: dict[str, dict] = {}
    for gi, group in enumerate(merged.values(), start=1):
        names = [naming.with_timepoint(v.name, tp) for tp in timepoints for v in group["variables"]]
        members = sorted({ids[n] for n in names if n in ids}, key=lambda x: int(x[1:]))
        if not members:
            continue
        construct_of.update({n: group["construct"] for n in names})
        grp = b.el(data, "varGrp", ID=f"G{gi}", var=" ".join(members))
        b.el(grp, "labl", f"{group['construct']['label']}: {group['label']}")
        _construct_concept(b, grp, lib, group["construct"].get("shared_construct_id"), group["construct"]["label"])
        if group["construct"].get("definition"):
            b.el(grp, "defntn", group["construct"]["definition"])
    for v in book.variables:
        _variable(b, data, lib, v, ids[v.name], construct_of.get(v.name))


def _construct_concept(b: _Builder, parent: ET.Element, lib: Library, shared_id: str | None, label: str) -> None:
    if shared_id and shared_id in lib.constructs:
        b.el(parent, "concept", lib.constructs[shared_id]["label"], vocab=CONSTRUCTS_VOCAB,
             vocabURI=profile.CONSTRUCTS_URI + shared_id)
    else:
        b.el(parent, "concept", label)


NATURE = {"ordinal": "ordinal", "categorical": "nominal", "binary": "nominal", "numeric": "interval"}


def _variable(b: _Builder, parent: ET.Element, lib: Library, v: codebook.Variable, vid: str,
              construct: dict | None = None) -> None:
    discrete = v.data_type in ("ordinal", "categorical", "binary") or bool(v.values)
    node = b.el(parent, "var", ID=vid, name=v.name, intrvl="discrete" if discrete else "contin",
                nature=NATURE.get(v.data_type))
    b.el(node, "labl", v.label)
    if v.question:
        b.el(b.el(node, "qstn"), "qstnLit", v.question)
    for code, label in v.values:
        cat = b.el(node, "catgry")
        b.el(cat, "catValu", str(code))
        if label:
            b.el(cat, "labl", label)
    for code, label in v.missing:
        cat = b.el(node, "catgry", missing="Y")
        b.el(cat, "catValu", str(code))
        if label:
            b.el(cat, "labl", label)
    shared = [cid for cid in v.construct_ids if cid in lib.constructs]
    for cid in shared:
        _construct_concept(b, node, lib, cid, lib.constructs[cid]["label"])
    if construct and not shared:  # the plan's own construct, not (yet) on the shared list
        b.el(node, "concept", construct["label"])
    notes = [x.strip().rstrip(".") for x in (v.notes, f"Timepoint: {v.timepoint}" if v.timepoint else None,
                         f"Instrument: {lib.instruments[v.instrument_id]['name']}" if v.instrument_id in lib.instruments else None,
                         f"Sensitivity if shared: {v.sensitivity}" if v.sensitivity != "none" else None) if x]
    if notes:
        b.el(node, "notes", ". ".join(notes) + ".")
