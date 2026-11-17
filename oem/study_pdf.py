# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""A readable PDF of a study profile, to deposit with ``humeta.json`` when registering a study.

The PDF is for people (reviewers, readers of the registration); ``humeta.json`` is for machines
(the HuMeta Library and other tools). Both come from the same record. Nothing here imports Streamlit.
"""
from __future__ import annotations

import datetime as dt
import io
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from oem import profile
from oem.library import Library


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("t", parent=base["Title"], fontSize=17, leading=21, alignment=0, spaceAfter=4),
        "sub": ParagraphStyle("s", parent=base["Normal"], fontSize=9, textColor=colors.HexColor("#555555"), leading=12),
        "h": ParagraphStyle("h", parent=base["Heading2"], fontSize=12.5, spaceBefore=12, spaceAfter=4,
                            textColor=colors.HexColor("#1f3a5f")),
        "body": ParagraphStyle("b", parent=base["Normal"], fontSize=9.5, leading=13),
        "label": ParagraphStyle("l", parent=base["Normal"], fontSize=9, leading=12, textColor=colors.HexColor("#444444")),
    }


def _text(value) -> str:
    return escape(str(value)).replace("\n", "<br/>")


def _labels(p: profile.Profile, vocab_id: str, ids) -> str:
    if not ids:
        return ""
    ids = ids if isinstance(ids, list) else [ids]
    return "; ".join(p.label(vocab_id, i) if i in p.ids(vocab_id) else str(i) for i in ids)


def study_pdf(record: dict, lib: Library | None = None, p: profile.Profile | None = None) -> bytes:
    """The study profile as a PDF (US Letter)."""
    p = p or profile.load()
    lib = lib or Library.load()
    record = profile.migrate(record, p)
    res, s = record["resource"], record["study"]
    st = _styles()
    story: list = []

    def section(title: str, rows: list[tuple[str, str]]) -> None:
        rows = [(k, v) for k, v in rows if v and str(v).strip()]
        if not rows:
            return
        story.append(Paragraph(_text(title), st["h"]))
        table = Table([[Paragraph(_text(k), st["label"]), Paragraph(_text(v), st["body"])] for k, v in rows],
                      colWidths=[1.8 * inch, 4.9 * inch])
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#dddddd")),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(table)

    # Heading
    story.append(Paragraph(_text(res.get("title") or "Untitled study"), st["title"]))
    team = "; ".join(c["name"] + (f" ({c['affiliation']})" if c.get("affiliation") else "")
                     + (f", ORCID {c['orcid']}" if c.get("orcid") else "") for c in res.get("creators") or [])
    if team:
        story.append(Paragraph(_text(team), st["body"]))
    doi = (res.get("identifier") or {}).get("value") if (res.get("identifier") or {}).get("type") == "DOI" else None
    meta = [f"Study profile (HuMeta {p.version})", f"prepared {dt.date.today().isoformat()}"]
    if doi:
        meta.insert(1, f"DOI https://doi.org/{doi}")
    story.append(Paragraph(_text(" · ".join(meta)), st["sub"]))
    story.append(Spacer(1, 6))
    if res.get("description"):
        story.append(Paragraph("Summary", st["h"]))
        story.append(Paragraph(_text(res["description"]), st["body"]))

    design = s.get("design") or {}
    frameworks = "; ".join(lib.frameworks[f]["label"] for f in design.get("frameworks") or [] if f in lib.frameworks)
    funding = "; ".join(f["funder_name"] + (f" ({f['award_number']})" if f.get("award_number") else "")
                        for f in res.get("funding") or [])
    section("The study", [
        ("Research fields", _labels(p, "research_field", s.get("fields"))),
        ("Disciplines", _labels(p, "discipline", s.get("discipline"))),
        ("Topic", design.get("topic")),
        ("Keywords", ", ".join(res.get("keywords") or [])),
        ("Funding", funding),
    ])
    dates = res.get("collection_dates") or {}
    section("Design", [
        ("Research questions and aims", design.get("research_questions")),
        ("Theoretical framework", frameworks),
        ("How the framework guides the study", design.get("framework_description")),
        ("Study design", _labels(p, "study_design", s["evidence"].get("study_designs"))),
        ("Unit of analysis", _labels(p, "unit_of_analysis", design.get("unit_of_analysis"))),
        ("Sampling", _labels(p, "sampling_procedure", design.get("sampling_procedure"))),
        ("Data collection", _labels(p, "data_collection_method", s["evidence"].get("data_collection_methods"))),
        ("Analysis", _labels(p, "analysis_method", s["evidence"].get("analysis_methods"))),
        ("Data collection dates", " to ".join(x for x in (dates.get("start"), dates.get("end")) if x)),
    ])
    constructs = []
    for c in s.get("constructs") or []:
        name = profile.construct_name(lib, c)
        shared = lib.constructs.get(c.get("construct_id") or "")
        if shared and name.lower() != shared["label"].lower():
            name += f" (shared construct: {shared['label']})"
        iid = c.get("instrument_id")
        if iid:
            name += f" — measured with {(lib.instruments.get(iid) or {}).get('name', iid)}"
        constructs.append(name)
    section("Constructs and measures", [("Constructs measured", "\n".join(constructs))])
    pop = s.get("population") or {}
    geo = res.get("geography") or {}
    section("People and place", [
        ("Do people take part?", _labels(p, "human_participants", pop.get("human_participants"))),
        ("Participants", _labels(p, "participant_role", pop.get("participant_roles"))),
        ("Population", pop.get("description")),
        ("Sample size (planned or actual)", str(pop["sample_size"]) if pop.get("sample_size") else ""),
        ("Locale", _labels(p, "locale", (s.get("context") or {}).get("locale"))),
        ("Countries", ", ".join(geo.get("countries") or [])),
        ("US states", ", ".join(geo.get("us_states") or [])),
    ])
    src = s.get("sources") or {}
    section("Sources", [
        ("Source types", _labels(p, "source_type", src.get("types"))),
        ("Description", src.get("description")),
        ("Held at", src.get("holdings")),
        ("Time period", src.get("time_period")),
        ("Rights status", _labels(p, "source_rights", src.get("rights"))),
    ])
    edu = record.get("education") or {}
    if profile.uses(record, "education"):
        section("Education", [
            ("Education level", _labels(p, "education_level", edu.get("education_levels"))),
            ("Undergraduate course level", _labels(p, "undergraduate_level", edu.get("undergraduate_levels"))),
            ("Institution type", _labels(p, "institution_type", edu.get("institution_types"))),
            ("Modality", _labels(p, "modality", edu.get("modality"))),
            ("Learning environment", _labels(p, "learning_environment", edu.get("learning_environments"))),
            ("Instructional approach", _labels(p, "pedagogy", edu.get("pedagogy"))),
        ])
    social = record.get("social_science") or {}
    if profile.uses(record, "social_science"):
        section("Social science", [
            ("Kind of data", _labels(p, "kind_of_data", social.get("kind_of_data"))),
            ("Universe", social.get("universe")),
            ("Smallest geographic unit", social.get("geographic_unit")),
            ("Response rate", social.get("response_rate")),
            ("Weighting", social.get("weighting")),
            ("DDI documentation", social.get("ddi_record")),
        ])
    hum = record.get("humanities") or {}
    if profile.uses(record, "humanities"):
        section("Arts and humanities", [
            ("Research activities", _labels(p, "tadirah_activity", hum.get("research_activities"))),
            ("Works, creators, or objects studied", hum.get("objects_of_study")),
            ("Languages of the sources", ", ".join(hum.get("source_languages") or [])),
            ("Editorial or encoding standards", hum.get("editorial_standards")),
        ])
    eth = s.get("ethics") or {}
    section("Ethics, consent, and access", [
        ("Human-subjects review", _labels(p, "human_subjects_review", eth.get("human_subjects_review"))),
        ("Participation consent", _labels(p, "consent", eth.get("consent"))),
        ("Consent for data sharing", _labels(p, "consent_for_sharing", eth.get("consent_for_sharing"))),
        ("Identifiability", _labels(p, "identifiability", eth.get("identifiability"))),
        ("Access level", _labels(p, "access_level", eth.get("access_level"))),
        ("Sensitivity", _labels(p, "sensitivity_flag", eth.get("sensitivity_flags"))),
        ("Online data practices", _labels(p, "online_data_practice", eth.get("online_data"))),
        ("Governance notes", eth.get("governance_notes")),
    ])
    care = s.get("care") or {}
    section("Indigenous data governance (CARE)", [
        ("Indigenous data", _labels(p, "indigenous_data", care.get("indigenous_data"))),
        ("Governance arrangement", _labels(p, "indigenous_governance", care.get("governance"))),
        ("Local Contexts project", care.get("local_contexts_project")),
        ("Local Contexts Labels / Notices", ", ".join(care.get("local_contexts_labels") or [])),
        ("CARE statement", care.get("statement")),
    ])
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Ethics and governance answers are reported by the study team; they are not approval or sharing determinations. "
        "The machine-readable version of this profile is humeta.json, deposited with this file.", st["sub"]))

    buf = io.BytesIO()
    title = res.get("title") or "Study profile"
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=0.9 * inch, rightMargin=0.9 * inch,
                            topMargin=0.8 * inch, bottomMargin=0.8 * inch, title=title,
                            author="; ".join(c["name"] for c in res.get("creators") or []),
                            subject="HuMeta study profile")

    def footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#777777"))
        canvas.drawString(0.9 * inch, 0.5 * inch, title[:90])
        canvas.drawRightString(letter[0] - 0.9 * inch, 0.5 * inch, f"Page {doc_.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
