# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Streamlit widgets for editing a STEMEd+ profile record.

Used by Module 1 (the study profile form) and Module 3 (constructs, checks,
and exports). The record format and all rules live in ``oem/profile.py``.
"""

from __future__ import annotations

import datetime as dt
import re

import pandas as pd
import streamlit as st

from oem import profile
from oem.app.common import current_project
from oem.library import Library

SPEC_URL = "https://github.com/JLib271/OpenEdMetadata/blob/main/standard/stemed-ap/README.md"
CARE_URL = "https://www.gida-global.org/care"
LOCAL_CONTEXTS_URL = "https://localcontexts.org/"
LICENSES = {
    None: "— not specified —",
    "CC-BY-4.0": "Creative Commons Attribution 4.0",
    "CC-BY-SA-4.0": "Creative Commons Attribution-ShareAlike 4.0",
    "CC-BY-NC-4.0": "Creative Commons Attribution-NonCommercial 4.0",
    "CC0-1.0": "CC0 1.0 (public domain dedication)",
}
LICENSE_URLS = {
    "CC-BY-4.0": "https://creativecommons.org/licenses/by/4.0/",
    "CC-BY-SA-4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
    "CC-BY-NC-4.0": "https://creativecommons.org/licenses/by-nc/4.0/",
    "CC0-1.0": "https://creativecommons.org/publicdomain/zero/1.0/",
}
US_STATES = ["AK", "AL", "AR", "AZ", "CA", "CO", "CT", "DC", "DE", "FL", "GA", "HI", "IA", "ID", "IL", "IN", "KS", "KY",
             "LA", "MA", "MD", "ME", "MI", "MN", "MO", "MS", "MT", "NC", "ND", "NE", "NH", "NJ", "NM", "NV", "NY", "OH",
             "OK", "OR", "PA", "PR", "RI", "SC", "SD", "TN", "TX", "UT", "VA", "VT", "WA", "WI", "WV", "WY"]


@st.cache_resource(show_spinner=False)
def library() -> Library:
    return Library.load()


def current_record() -> dict | None:
    """The project's STEMEd+ record, filled out to the current profile shape."""
    record = st.session_state.get("stemed_record") or current_project().get("stemed_record")
    return profile.migrate(record) if record else None


def store_record(record: dict, reset_widgets: bool = False) -> None:
    """Save the record to the session and project, and refresh the derived study view."""
    project = current_project()
    project["stemed_record"] = record
    project["study"] = profile.to_study_record(record, existing=project.get("study"))
    st.session_state["project"] = project
    st.session_state["stemed_record"] = record
    if reset_widgets:
        st.session_state["stemed_form_version"] = st.session_state.get("stemed_form_version", 0) + 1


def _blank(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


def record_form(record: dict) -> dict | None:
    """Render the profile form (everything except constructs). Returns the new record on submit."""
    p = profile.load()
    res, s = record["resource"], record["stemed"]
    v = st.session_state.get("stemed_form_version", 0)

    def key(name: str) -> str:
        return f"stemed_{name}_{v}"

    def multi(label: str, vocab_id: str, current: list[str] | None, name: str, help: str | None = None) -> list[str]:
        ids = p.ids(vocab_id)
        return st.multiselect(label, ids, default=[c for c in current or [] if c in ids],
                              format_func=lambda t: p.label(vocab_id, t), key=key(name), help=help)

    def single(label: str, vocab_id: str, current: str | None, name: str, help: str | None = None) -> str | None:
        options = [None, *p.ids(vocab_id)]
        return st.selectbox(label, options, index=options.index(current) if current in options else 0,
                            format_func=lambda t: "— choose —" if t is None else p.label(vocab_id, t),
                            key=key(name), help=help)

    with st.form(key=f"stemed_form_{v}"):
        st.subheader("1 · The study")
        c1, c2 = st.columns([3, 1])
        title = c1.text_input("Title *", res.get("title") or "", key=key("title"))
        type_options = list(profile.RESOURCE_TYPES)
        resource_type = c2.selectbox(
            "What are you describing? *", type_options, index=type_options.index(res.get("resource_type") or "Dataset"),
            key=key("rtype"),
            help="Dataset: data from a study. Instrument: a measure. StudyRegistration: a preregistered plan. (DataCite types.)")
        creators_df = st.data_editor(
            pd.DataFrame(res.get("creators") or [{"name": "", "orcid": None, "affiliation": None}],
                         columns=["name", "orcid", "affiliation"]),
            num_rows="dynamic", use_container_width=True, key=key("creators"),
            column_config={
                "name": st.column_config.TextColumn("Study team member *"),
                "orcid": st.column_config.TextColumn("ORCID iD", help="Format 0000-0000-0000-0000"),
                "affiliation": st.column_config.TextColumn("Affiliation"),
            },
        )
        c1, c2, c3 = st.columns(3)
        publisher = c1.text_input("Institution / publisher *", res.get("publisher") or "", key=key("publisher"),
                                  help="The institution responsible, or the repository that will publish the data.")
        publication_year = c2.number_input("Publication year *", min_value=1900, max_value=2100, step=1,
                                           value=int(res.get("publication_year") or dt.date.today().year), key=key("year"),
                                           help="Year the data or record will be made available (your best estimate).")
        doi = c3.text_input("DOI (if assigned)", (res.get("identifier") or {}).get("value") or "", key=key("doi"),
                            placeholder="10.xxxx/xxxxx")
        description = st.text_area("Description / abstract", res.get("description") or "", key=key("description"))
        c1, c2, c3 = st.columns(3)
        funder = c1.text_input("Funder", "; ".join(f["funder_name"] for f in res.get("funding") or []), key=key("funder"))
        award = c2.text_input("Award number", next((f.get("award_number") or "" for f in res.get("funding") or []), ""), key=key("award"))
        keywords = c3.text_input("Keywords (comma-separated)", ", ".join(res.get("keywords") or []), key=key("keywords"))
        c1, c2 = st.columns(2)
        language = c1.text_input("Language code", res.get("language") or "en", key=key("language"), help="BCP 47, e.g. en, es")
        current_license = (res.get("license") or {}).get("spdx")
        license_options = list(LICENSES)
        license_id = c2.selectbox("Data license", license_options,
                                  index=license_options.index(current_license) if current_license in license_options else 0,
                                  format_func=lambda k: LICENSES[k], key=key("license"))

        st.subheader("2 · Study design")
        design = s.get("design") or {}
        topic = st.text_input("Topic / content domain", design.get("topic") or "", key=key("topic"),
                              help="Used by Module 2 to find related studies.")
        research_questions = st.text_area("Research questions and aims", design.get("research_questions") or "", key=key("rq"))
        c1, c2 = st.columns(2)
        with c1:
            designs = multi("Study design", "study_design", s["evidence"].get("study_designs"), "designs",
                            help="Required for datasets and study registrations.")
            units = multi("Unit of analysis", "unit_of_analysis", design.get("unit_of_analysis"), "units")
            methods = multi("Data collection method", "data_collection_method", s["evidence"].get("data_collection_methods"), "methods")
        with c2:
            sampling = multi("Sampling procedure", "sampling_procedure", design.get("sampling_procedure"), "sampling")
            measurement = multi("Measurement evidence (for instruments)", "measurement_evidence",
                                s["evidence"].get("measurement_evidence"), "measurement",
                                help="Required for instruments. Sources of validity evidence follow the Standards for Educational and Psychological Testing.")
        dates = res.get("collection_dates") or {}
        c1, c2 = st.columns(2)
        start = c1.text_input("Data collection start (YYYY-MM-DD)", dates.get("start") or "", key=key("start"))
        end = c2.text_input("Data collection end (YYYY-MM-DD)", dates.get("end") or "", key=key("end"))

        st.subheader("3 · Population and context")
        c1, c2 = st.columns(2)
        with c1:
            roles = multi("Participants *", "participant_role", s["population"].get("participant_roles"), "roles")
            levels = multi("Education level *", "education_level", s["population"].get("education_levels"), "levels")
            ug_levels = multi("Undergraduate course level", "undergraduate_level", s["population"].get("undergraduate_levels"), "ug")
            disciplines = multi("Discipline", "discipline", s.get("discipline"), "discipline")
        with c2:
            institutions = multi("Institution type", "institution_type", s["context"].get("institution_types"), "inst")
            locale = multi("Locale", "locale", s["context"].get("locale"), "locale")
            geo = res.get("geography") or {}
            states = st.multiselect("US states", US_STATES, default=[x for x in geo.get("us_states") or [] if x in US_STATES],
                                    key=key("states"))
            countries = st.text_input("Countries (ISO codes, comma-separated)",
                                      ", ".join(geo.get("countries") or (["US"] if states else [])), key=key("countries"))
        c1, c2 = st.columns([3, 1])
        population_description = c1.text_area("Population description (no identifying details)",
                                              s["population"].get("description") or "", key=key("popdesc"))
        sample_size = c2.number_input("Sample size (N)", min_value=0, step=1, value=int(s["population"].get("sample_size") or 0),
                                      key=key("n"), help="Planned or actual. Leave 0 if not known.")

        st.subheader("4 · Instructional setting")
        c1, c2, c3 = st.columns(3)
        with c1:
            modality = multi("Modality", "modality", s["setting"].get("modality"), "modality")
        with c2:
            environments = multi("Learning environment", "learning_environment", s["setting"].get("learning_environments"), "env")
        with c3:
            pedagogy = multi("Instructional approach", "pedagogy", s["setting"].get("pedagogy"), "pedagogy")

        st.subheader("5 · Ethics, consent, and access")
        c1, c2, c3 = st.columns(3)
        with c1:
            review = single("Human-subjects review *", "human_subjects_review", s["ethics"].get("human_subjects_review"), "review")
            consent = single("Participation consent", "consent", s["ethics"].get("consent"), "consent")
        with c2:
            sharing = single("Consent for data sharing *", "consent_for_sharing", s["ethics"].get("consent_for_sharing"), "sharing",
                             help="What participants agreed to about sharing beyond your team. Plan this before you collect data.")
            identifiability = single("Identifiability *", "identifiability", s["ethics"].get("identifiability"), "ident")
        with c3:
            access = single("Access level *", "access_level", s["ethics"].get("access_level"), "access")
            flags = multi("Sensitivity flags", "sensitivity_flag", s["ethics"].get("sensitivity_flags"), "flags")
        governance_notes = st.text_area("Governance notes (approval references, data-use restrictions; nothing confidential)",
                                        s["ethics"].get("governance_notes") or "", key=key("govnotes"))

        st.subheader("6 · Indigenous data governance (CARE)")
        st.caption(
            f"The [CARE Principles]({CARE_URL}) (Collective benefit, Authority to control, Responsibility, Ethics) "
            "guide work with data about Indigenous Peoples, nations, communities, lands, and knowledges. Communities may "
            f"apply [Local Contexts]({LOCAL_CONTEXTS_URL}) Traditional Knowledge or Biocultural Labels and Notices."
        )
        care = s["care"]
        c1, c2 = st.columns(2)
        with c1:
            indigenous = single("Does this study involve Indigenous data? *", "indigenous_data", care.get("indigenous_data"), "indigenous")
            governance = single("Governance arrangement (required if yes)", "indigenous_governance", care.get("governance"), "governance")
        with c2:
            lc_project = st.text_input("Local Contexts Hub project URL", care.get("local_contexts_project") or "", key=key("lcproj"))
            lc_labels = st.text_input("Local Contexts Labels / Notices (comma-separated)",
                                      ", ".join(care.get("local_contexts_labels") or []), key=key("lclabels"))
        care_statement = st.text_area(
            "CARE statement (required if yes)", care.get("statement") or "", key=key("care"),
            help="Describe collective benefit to the communities involved, how their authority to control the data is "
                 "respected, and your responsibility and ethics commitments.")

        submitted = st.form_submit_button("Save study profile", type="primary", use_container_width=True)

    if not submitted:
        return None
    creators = []
    for row in creators_df.fillna("").to_dict(orient="records"):
        if str(row.get("name") or "").strip():
            orcid = re.search(r"(\d{4}-){3}\d{3}[\dX]", str(row.get("orcid") or ""))
            creators.append({"name": str(row["name"]).strip(), "orcid": orcid.group(0) if orcid else None,
                             "affiliation": _blank(str(row.get("affiliation") or ""))})
    doi_match = re.search(r"10\.\d{4,9}/\S+", doi or "")
    new = profile.empty_record(p)
    new["resource"].update({
        "title": title.strip(), "creators": creators, "publisher": publisher.strip(),
        "publication_year": int(publication_year), "resource_type": resource_type,
        "identifier": {"value": doi_match.group(0), "type": "DOI"} if doi_match else None,
        "description": _blank(description),
        "keywords": [k.strip() for k in keywords.split(",") if k.strip()],
        "language": _blank(language),
        "license": {"spdx": license_id, "name": LICENSES[license_id], "url": LICENSE_URLS.get(license_id)} if license_id else None,
        "funding": [{"funder_name": funder.strip(), "award_number": _blank(award)}] if funder.strip() else [],
        "collection_dates": {"start": _blank(start), "end": _blank(end)} if (start.strip() or end.strip()) else None,
        "geography": {"countries": [c.strip().upper() for c in countries.split(",") if c.strip()], "us_states": states}
        if (countries.strip() or states) else None,
        "related": res.get("related") or [],
    })
    ns = new["stemed"]
    ns["constructs"] = s.get("constructs") or []  # edited in Module 3
    ns["discipline"] = disciplines
    ns["design"].update({"topic": _blank(topic), "research_questions": _blank(research_questions),
                         "unit_of_analysis": units, "sampling_procedure": sampling})
    ns["population"].update({"participant_roles": roles, "education_levels": levels, "undergraduate_levels": ug_levels,
                             "description": _blank(population_description),
                             "sample_size": int(sample_size) if sample_size else None})
    ns["context"].update({"institution_types": institutions, "locale": locale})
    ns["setting"].update({"modality": modality, "learning_environments": environments, "pedagogy": pedagogy})
    ns["evidence"].update({"study_designs": designs, "measurement_evidence": measurement, "data_collection_methods": methods})
    ns["ethics"].update({"human_subjects_review": review, "consent": consent, "consent_for_sharing": sharing,
                         "identifiability": identifiability, "sensitivity_flags": flags, "access_level": access,
                         "governance_notes": _blank(governance_notes)})
    ns["care"].update({"indigenous_data": indigenous, "governance": governance, "statement": _blank(care_statement),
                       "local_contexts_project": _blank(lc_project),
                       "local_contexts_labels": [x.strip() for x in lc_labels.split(",") if x.strip()]})
    return new


def show_issues(issues: list[profile.Issue]) -> None:
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    if not issues:
        st.success("This record meets every requirement of the STEMEd+ profile.")
    for issue in errors:
        st.error(f"**{issue.element}**: {issue.message}" + (f" ({issue.rule})" if issue.rule else ""))
    for issue in warnings:
        st.warning(f"**{issue.element}**: {issue.message}" + (f" ({issue.rule})" if issue.rule else ""))
