# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Streamlit widgets for editing a SHE Study Metadata Profile record.

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

SPEC_URL = "https://github.com/JLib271/OpenEdMetadata/blob/main/standard/she/README.md"
ISSUES_URL = "https://github.com/JLib271/OpenEdMetadata/issues"
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
    """The project's SHE profile record, filled out to the current profile shape."""
    record = st.session_state.get("profile_record") or current_project().get("profile_record")
    return profile.migrate(record) if record else None


def store_record(record: dict, reset_widgets: bool = False) -> None:
    """Save the record to the session and project, and refresh the derived study view."""
    project = current_project()
    project["profile_record"] = record
    project["study"] = profile.to_study_record(record, existing=project.get("study"))
    st.session_state["project"] = project
    st.session_state["profile_record"] = record
    if reset_widgets:
        st.session_state["profile_form_version"] = st.session_state.get("profile_form_version", 0) + 1


def _blank(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


def record_form(record: dict) -> dict | None:
    """Render the profile form (everything except constructs). Returns the new record on submit."""
    p = profile.load()
    res, s = record["resource"], record["study"]
    edu = record.get("education") or {}
    with_education = profile.uses(record, "education")
    v = st.session_state.get("profile_form_version", 0)

    def key(name: str) -> str:
        return f"profile_{name}_{v}"

    def lab(text: str, element_id: str) -> str:
        """Field label followed by its standard alignments."""
        return f"{text}  {profile.alignment_badges(element_id, p)}"

    def tip(element_id: str, extra: str | None = None) -> str:
        return profile.alignment_help(element_id, p) + (f"\n\n{extra}" if extra else "")

    def multi(label: str, vocab_id: str, current: list[str] | None, name: str, element_id: str,
              help: str | None = None) -> list[str]:
        ids = p.ids(vocab_id)
        return st.multiselect(lab(label, element_id), ids, default=[c for c in current or [] if c in ids],
                              format_func=lambda t: p.label(vocab_id, t), key=key(name), help=tip(element_id, help))

    def single(label: str, vocab_id: str, current: str | None, name: str, element_id: str,
               help: str | None = None) -> str | None:
        options = [None, *p.ids(vocab_id)]
        return st.selectbox(lab(label, element_id), options, index=options.index(current) if current in options else 0,
                            format_func=lambda t: "— choose —" if t is None else p.label(vocab_id, t),
                            key=key(name), help=tip(element_id, help))

    with st.expander("How fields align with metadata standards", expanded=False):
        st.markdown(
            "Each field shows the standards it corresponds to, so records stay compatible with tools "
            "that already use them. `SHE` marks fields defined by this profile; no "
            "general-purpose standard covers them. **≈** = close match, **~** = related; no mark = exact match. "
            f"**{profile.SEEKING_INPUT_BADGE}** marks alignments we are not yet sure of. If you know the standard, "
            f"please comment on [GitHub]({ISSUES_URL})."
        )
        st.markdown("\n".join(f"- **{std['short']}**: [{std['name']}]({std['url']})"
                                 for std in p.definition["standards"].values()))
    st.markdown("**Field modules**")
    wanted = st.toggle(
        "Education module: learners' education levels, institutions and instructional settings",
        value=with_education, key=key("module_education"),
        help="Use for studies in education settings. Turning it off clears the module's fields.")
    if wanted != with_education:
        changed = profile.migrate(record, p)
        changed["education"] = profile.empty_record(p, modules=("education",))["education"] if wanted else None
        store_record(changed, reset_widgets=True)
        st.rerun()
    st.caption("Modules for other fields, starting with social science and humanities, are being developed with the "
               f"community. [Suggest one on GitHub]({ISSUES_URL}).")
    with st.form(key=f"profile_form_{v}"):
        st.subheader("1 · The study")
        c1, c2 = st.columns([3, 1])
        title = c1.text_input(lab("Title *", "resource.title"), res.get("title") or "", key=key("title"),
                              help=tip("resource.title"))
        type_options = list(profile.RESOURCE_TYPES)
        resource_type = c2.selectbox(
            lab("What are you describing? *", "resource.resource_type"), type_options,
            index=type_options.index(res.get("resource_type") or "Dataset"), key=key("rtype"),
            help=tip("resource.resource_type", "Dataset: data from a study. Instrument: a measure. StudyRegistration: a preregistered plan."))
        st.markdown(f"**Study team** {profile.alignment_badges('resource.creators', p)}",
                    help=tip("resource.creators"))
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
        publisher = c1.text_input(lab("Institution / publisher *", "resource.publisher"), res.get("publisher") or "",
                                  key=key("publisher"),
                                  help=tip("resource.publisher", "The institution responsible, or the repository that will publish the data."))
        publication_year = c2.number_input(lab("Publication year *", "resource.publication_year"), min_value=1900,
                                           max_value=2100, step=1,
                                           value=int(res.get("publication_year") or dt.date.today().year), key=key("year"),
                                           help=tip("resource.publication_year", "Your best estimate of when the data or record will be available."))
        doi = c3.text_input(lab("DOI (if assigned)", "resource.identifier"), (res.get("identifier") or {}).get("value") or "",
                            key=key("doi"), placeholder="10.xxxx/xxxxx", help=tip("resource.identifier"))
        description = st.text_area(lab("Description / abstract", "resource.description"), res.get("description") or "",
                                   key=key("description"), help=tip("resource.description"))
        c1, c2, c3 = st.columns(3)
        funder = c1.text_input(lab("Funder", "resource.funding"), "; ".join(f["funder_name"] for f in res.get("funding") or []),
                               key=key("funder"), help=tip("resource.funding"))
        award = c2.text_input(lab("Award number", "resource.funding"),
                              next((f.get("award_number") or "" for f in res.get("funding") or []), ""), key=key("award"),
                              help=tip("resource.funding"))
        keywords = c3.text_input(lab("Keywords (comma-separated)", "resource.keywords"), ", ".join(res.get("keywords") or []),
                                 key=key("keywords"), help=tip("resource.keywords"))
        c1, c2 = st.columns(2)
        language = c1.text_input(lab("Language code", "resource.language"), res.get("language") or "en", key=key("language"),
                                 help=tip("resource.language", "For example en or es."))
        current_license = (res.get("license") or {}).get("spdx")
        license_options = list(LICENSES)
        license_id = c2.selectbox(lab("Data license", "resource.license"), license_options, help=tip("resource.license"),
                                  index=license_options.index(current_license) if current_license in license_options else 0,
                                  format_func=lambda k: LICENSES[k], key=key("license"))

        st.subheader("2 · Study design")
        design = s.get("design") or {}
        topic = st.text_input(lab("Topic / content domain", "study.design.topic"), design.get("topic") or "", key=key("topic"),
                              help=tip("study.design.topic", "Used by Module 2 to find related studies."))
        research_questions = st.text_area(lab("Research questions and aims", "study.design.research_questions"),
                                          design.get("research_questions") or "", key=key("rq"),
                                          help=tip("study.design.research_questions"))
        c1, c2 = st.columns(2)
        with c1:
            designs = multi("Study design", "study_design", s["evidence"].get("study_designs"), "designs", "study.evidence.study_designs",
                            help="Required for datasets and study registrations.")
            units = multi("Unit of analysis", "unit_of_analysis", design.get("unit_of_analysis"), "units", "study.design.unit_of_analysis")
            methods = multi("Data collection method", "data_collection_method", s["evidence"].get("data_collection_methods"), "methods",
                            "study.evidence.data_collection_methods")
        with c2:
            sampling = multi("Sampling procedure", "sampling_procedure", design.get("sampling_procedure"), "sampling",
                             "study.design.sampling_procedure")
            measurement = multi("Measurement evidence (for instruments)", "measurement_evidence",
                                s["evidence"].get("measurement_evidence"), "measurement", "study.evidence.measurement_evidence",
                                help="Required for instruments. Sources of validity evidence follow the Standards for Educational and Psychological Testing.")
        dates = res.get("collection_dates") or {}
        c1, c2 = st.columns(2)
        start = c1.text_input(lab("Data collection start (YYYY-MM-DD)", "resource.collection_dates"), dates.get("start") or "",
                              key=key("start"), help=tip("resource.collection_dates"))
        end = c2.text_input(lab("Data collection end (YYYY-MM-DD)", "resource.collection_dates"), dates.get("end") or "",
                            key=key("end"), help=tip("resource.collection_dates"))

        st.subheader("3 · Population and context")
        c1, c2 = st.columns(2)
        with c1:
            roles = multi("Participants *", "participant_role", s["population"].get("participant_roles"), "roles",
                          "study.population.participant_roles")
            disciplines = multi("Discipline", "discipline", s.get("discipline"), "discipline", "study.discipline")
        with c2:
            locale = multi("Locale", "locale", s["context"].get("locale"), "locale", "study.context.locale",
                           help="NCES locale types. Fully online study? Leave blank.")
            geo = res.get("geography") or {}
            states = st.multiselect(lab("US states", "resource.geography"), US_STATES, help=tip("resource.geography", "USPS state codes."), default=[x for x in geo.get("us_states") or [] if x in US_STATES],
                                    key=key("states"))
            countries = st.text_input(lab("Countries (codes, comma-separated)", "resource.geography"), help=tip("resource.geography"),
                                      value=
                                      ", ".join(geo.get("countries") or (["US"] if states else [])), key=key("countries"))
        c1, c2 = st.columns([3, 1])
        population_description = c1.text_area(lab("Population description (no identifying details)", "study.population.description"),
                                              help=tip("study.population.description"), value=
                                              s["population"].get("description") or "", key=key("popdesc"))
        sample_size = c2.number_input(lab("Sample size (N)", "study.population.sample_size"), min_value=0, step=1,
                                      value=int(s["population"].get("sample_size") or 0), key=key("n"),
                                      help=tip("study.population.sample_size", "Planned or actual. Leave 0 if not known."))

        number = 4
        if with_education:
            st.subheader("4 · Education module")
            st.caption("Learners, institutions and instructional settings. Turn the module off above if this study "
                       "is not in an education setting.")
            c1, c2, c3 = st.columns(3)
            with c1:
                levels = multi("Education level *", "education_level", edu.get("education_levels"), "levels",
                               "education.education_levels")
                ug_levels = multi("Undergraduate course level", "undergraduate_level", edu.get("undergraduate_levels"), "ug",
                                  "education.undergraduate_levels")
            with c2:
                institutions = multi("Institution type", "institution_type", edu.get("institution_types"), "inst",
                                     "education.institution_types")
                modality = multi("Modality", "modality", edu.get("modality"), "modality", "education.modality")
            with c3:
                environments = multi("Learning environment", "learning_environment", edu.get("learning_environments"), "env",
                                     "education.learning_environments")
                pedagogy = multi("Instructional approach", "pedagogy", edu.get("pedagogy"), "pedagogy", "education.pedagogy")
            number = 5

        st.subheader(f"{number} · Ethics, consent, and access")
        c1, c2, c3 = st.columns(3)
        with c1:
            review = single("Human-subjects review *", "human_subjects_review", s["ethics"].get("human_subjects_review"), "review",
                            "study.ethics.human_subjects_review")
            consent = single("Participation consent", "consent", s["ethics"].get("consent"), "consent", "study.ethics.consent")
        with c2:
            sharing = single("Consent for data sharing *", "consent_for_sharing", s["ethics"].get("consent_for_sharing"), "sharing",
                             "study.ethics.consent_for_sharing",
                             help="What participants agreed to about sharing beyond your team. Plan this before you collect data.")
            identifiability = single("Identifiability *", "identifiability", s["ethics"].get("identifiability"), "ident",
                                     "study.ethics.identifiability")
        with c3:
            access = single("Access level *", "access_level", s["ethics"].get("access_level"), "access", "study.ethics.access_level")
            flags = multi("Sensitivity flags", "sensitivity_flag", s["ethics"].get("sensitivity_flags"), "flags",
                          "study.ethics.sensitivity_flags")
        governance_notes = st.text_area(lab("Governance notes (approval references, data-use restrictions; nothing confidential)",
                                            "study.ethics.governance_notes"), help=tip("study.ethics.governance_notes"), value=
                                        s["ethics"].get("governance_notes") or "", key=key("govnotes"))

        st.subheader(f"{number + 1} · Indigenous data governance (CARE)")
        st.caption(
            f"The [CARE Principles]({CARE_URL}) (Collective benefit, Authority to control, Responsibility, Ethics) "
            "guide work with data about Indigenous Peoples, nations, communities, lands, and knowledges. Communities may "
            f"apply [Local Contexts]({LOCAL_CONTEXTS_URL}) Traditional Knowledge or Biocultural Labels and Notices."
        )
        care = s["care"]
        c1, c2 = st.columns(2)
        with c1:
            indigenous = single("Does this study involve Indigenous data? *", "indigenous_data", care.get("indigenous_data"), "indigenous",
                                "study.care.indigenous_data")
            governance = single("Governance arrangement (required if yes)", "indigenous_governance", care.get("governance"), "governance",
                                "study.care.governance")
        with c2:
            lc_project = st.text_input(lab("Local Contexts Hub project URL", "study.care.local_contexts_project"),
                                       care.get("local_contexts_project") or "", key=key("lcproj"),
                                       help=tip("study.care.local_contexts_project"))
            lc_labels = st.text_input(lab("Local Contexts Labels / Notices (comma-separated)", "study.care.local_contexts_labels"),
                                      help=tip("study.care.local_contexts_labels"), value=
                                      ", ".join(care.get("local_contexts_labels") or []), key=key("lclabels"))
        care_statement = st.text_area(
            lab("CARE statement (required if yes)", "study.care.statement"), care.get("statement") or "", key=key("care"),
            help=tip("study.care.statement", "Describe collective benefit to the communities involved, how their authority "
                     "to control the data is respected, and your responsibility and ethics commitments."))

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
    new = profile.empty_record(p, modules=("education",) if with_education else ())
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
    ns = new["study"]
    ns["constructs"] = s.get("constructs") or []  # edited in Module 3
    ns["discipline"] = disciplines
    ns["design"].update({"topic": _blank(topic), "research_questions": _blank(research_questions),
                         "unit_of_analysis": units, "sampling_procedure": sampling})
    ns["population"].update({"participant_roles": roles, "description": _blank(population_description),
                             "sample_size": int(sample_size) if sample_size else None})
    ns["context"].update({"locale": locale})
    if with_education:
        new["education"].update({"education_levels": levels, "undergraduate_levels": ug_levels,
                                 "institution_types": institutions, "modality": modality,
                                 "learning_environments": environments, "pedagogy": pedagogy})
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
        st.success("This record meets every requirement of the SHE profile.")
    for issue in errors:
        st.error(f"**{issue.element}**: {issue.message}" + (f" ({issue.rule})" if issue.rule else ""))
    for issue in warnings:
        st.warning(f"**{issue.element}**: {issue.message}" + (f" ({issue.rule})" if issue.rule else ""))
