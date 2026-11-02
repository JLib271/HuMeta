# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Streamlit widgets for editing a HuMeta profile record.

Used by Module 1 (the study profile form) and Module 3 (constructs, checks,
and exports). The record format and all rules live in ``oem/profile.py``.
"""

from __future__ import annotations

import datetime as dt
import re

import pandas as pd
import streamlit as st

from oem import profile
from oem.app.common import LICENSE_HELP, current_project
from oem.library import Library

SPEC_URL = "https://github.com/JLib271/HuMeta/blob/main/standard/humeta/README.md"
ISSUES_URL = "https://github.com/JLib271/HuMeta/issues"
DDI_URL = "https://ddialliance.org/"
TADIRAH_URL = "https://vocabs.dariah.eu/tadirah/"
#: plain-language answers for the DataCite resource type
RESOURCE_TYPE_LABELS = {
    "Dataset": "Data from the study (a dataset)",
    "StudyRegistration": "A study plan or preregistration (no data yet)",
    "Instrument": "A measure or instrument (a survey, test, rubric, or coding scheme)",
    "Collection": "A collection of sources or materials (an archive, corpus, or set of works)",
    "Text": "A report, article, or other text",
    "Software": "Software or code",
    "Other": "Something else",
}
#: starting choice in Module 1: field module -> button label, and the research field it adds
FIELD_START = {"education": "Education", "social_science": "Social sciences", "humanities": "Arts and humanities",
               "other": "Other field"}
#: research field -> OECD FOS prefix used to narrow the discipline list
FIELD_FOS = {"social_sciences": "5", "humanities": "6", "arts": "6"}
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
    """The project's HuMeta profile record, filled out to the current profile shape."""
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
    # Older profiles may list a research field without its section; add the section (saved with the form).
    if any(m and profile.START_CHOICES[c][1] == m and not profile.uses(record, m)
           for c in profile.start_choices(record) for m in [profile.START_CHOICES[c][1]]):
        record = profile.apply_start_choices(record, profile.start_choices(record), p)
    res, s = record["resource"], record["study"]
    edu = record.get("education") or {}
    social = record.get("social_science") or {}
    hum = record.get("humanities") or {}
    with_education = profile.uses(record, "education")
    with_social = profile.uses(record, "social_science")
    with_humanities = profile.uses(record, "humanities")
    v = st.session_state.get("profile_form_version", 0)

    def key(name: str) -> str:
        return f"profile_{name}_{v}"

    def lab(text: str, element_id: str) -> str:
        """Field label. Standard alignments are in the field's (?) tooltip, not the label."""
        return text

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
            "Hover over the **?** next to any field to see its definition and the standards it matches "
            "(exact, close, or related match), so records stay compatible with tools that already use them. "
            "Fields with no match are defined by the HuMeta profile. Some matches are marked as seeking "
            f"expert input; if you know the standard, please comment on [GitHub]({ISSUES_URL})."
        )
        st.markdown("\n".join(f"- **{std['short']}**: [{std['name']}]({std['url']})"
                                 for std in p.definition["standards"].values()))
    st.markdown("**Start here: what field is your study in?** *")
    st.caption("Choose all that apply. Education, social sciences, and arts and humanities each add a short section "
               "for that field to the form below; every study gets the shared core. Removing a field clears its section.")
    active = profile.start_choices(record)
    chosen = list(st.pills("Field", list(FIELD_START), selection_mode="multi", default=active,
                           format_func=FIELD_START.get, key=key("start_fields"), label_visibility="collapsed",
                           help=tip("study.fields")) or [])
    if set(chosen) != set(active):
        store_record(profile.apply_start_choices(record, chosen, p), reset_widgets=True)
        st.rerun()
    if not chosen:
        st.warning("Choose at least one field to continue.")
    st.caption("Field sections are starting points, to be developed with researchers in each field. "
               f"[Suggest changes on GitHub]({ISSUES_URL}).")
    with st.form(key=f"profile_form_{v}"):
        # Narrow the subject list to the chosen fields (education studies can be about any subject).
        current_fields = set(s.get("fields") or [])
        prefixes = {FIELD_FOS[f] for f in current_fields if f in FIELD_FOS}
        all_subjects = p.ids("discipline")
        narrowed = bool(prefixes) and not current_fields & {"education", "other_field"}
        subject_ids = [d for d in all_subjects if not narrowed or d in (s.get("discipline") or [])
                       or any(str(p.term("discipline", d).get("fos", "")).startswith(x) for x in prefixes)]
        disciplines = st.multiselect(
            lab("Discipline or subject area", "study.discipline"), subject_ids,
            default=[d for d in s.get("discipline") or [] if d in subject_ids],
            format_func=lambda t: p.label("discipline", t), key=key("discipline"),
            help=tip("study.discipline", "Showing subjects in the fields you chose above." if narrowed else
                     "For education studies, the subject taught or learned."))
        st.subheader("1 · The study")
        title = st.text_input(lab("Title *", "resource.title"), res.get("title") or "", key=key("title"),
                              help=tip("resource.title"))
        # Full-width radio buttons: the answers need a few words each, which a narrow dropdown cuts off.
        type_options = [t for t in RESOURCE_TYPE_LABELS if t in profile.RESOURCE_TYPES]
        resource_type = st.radio(
            lab("What will this profile be attached to? *", "resource.resource_type"), type_options,
            index=type_options.index(res.get("resource_type") or "Dataset"), key=key("rtype"),
            format_func=RESOURCE_TYPE_LABELS.get,
            help=tip("resource.resource_type", "A study profile describes your study through the thing you will share, "
                     "register, or cite. This sets the DataCite resource type used when you get a DOI, and what the "
                     "profile checks for (for example, a dataset needs a study design)."))
        st.markdown("**Study team**",
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
        description = st.text_area(lab("Short summary of the study", "resource.description"), res.get("description") or "",
                                   key=key("description"),
                                   placeholder="Two to five sentences: what you studied, with whom or what, and how.",
                                   help=tip("resource.description", "Used as the abstract when you share or register the study."))
        st.markdown("**For citing and sharing**")
        st.caption("These become the citation when you share data or register a DOI. Estimates are fine for now; "
                   "you can update them later.")
        c1, c2, c3 = st.columns(3)
        publisher = c1.text_input(lab("Lead institution or repository *", "resource.publisher"), res.get("publisher") or "",
                                  key=key("publisher"), placeholder="e.g., your university, or ICPSR",
                                  help=tip("resource.publisher", "Who releases this: usually your university, or the "
                                           "repository that will publish the data. DataCite calls this the publisher."))
        publication_year = c2.number_input(lab("Year it will be shared (estimate) *", "resource.publication_year"),
                                           min_value=1900, max_value=2100, step=1,
                                           value=int(res.get("publication_year") or dt.date.today().year), key=key("year"),
                                           help=tip("resource.publication_year", "Your best estimate of when the data or "
                                                    "record will be available. DataCite calls this the publication year."))
        doi = c3.text_input(lab("DOI, if you already have one", "resource.identifier"),
                            (res.get("identifier") or {}).get("value") or "", key=key("doi"),
                            placeholder="Leave blank until a repository assigns one",
                            help=tip("resource.identifier", "A DOI is a permanent link to your data or materials, "
                                     "usually assigned when you deposit them in a repository (for example 10.3886/ICPSR12345)."))
        c1, c2, c3 = st.columns(3)
        funder = c1.text_input(lab("Funder", "resource.funding"), "; ".join(f["funder_name"] for f in res.get("funding") or []),
                               key=key("funder"), help=tip("resource.funding"))
        award = c2.text_input(lab("Award number", "resource.funding"),
                              next((f.get("award_number") or "" for f in res.get("funding") or []), ""), key=key("award"),
                              help=tip("resource.funding"))
        keywords = c3.text_input(lab("Keywords (comma-separated)", "resource.keywords"), ", ".join(res.get("keywords") or []),
                                 key=key("keywords"), help=tip("resource.keywords"))
        c1, c2 = st.columns(2)
        language = c1.text_input(lab("Main language of the study materials (code)", "resource.language"),
                                 res.get("language") or "en", key=key("language"),
                                 help=tip("resource.language", "A language code, for example en (English) or es (Spanish)."))
        current_license = (res.get("license") or {}).get("spdx")
        license_options = list(LICENSES)
        license_id = c2.selectbox(lab("Data license", "resource.license"), license_options, help=tip("resource.license"),
                                  index=license_options.index(current_license) if current_license in license_options else 0,
                                  format_func=lambda k: LICENSES[k], key=key("license"))
        c2.caption(LICENSE_HELP)

        st.subheader("2 · Study design")
        design = s.get("design") or {}
        topic = st.text_input(lab("Topic / content domain", "study.design.topic"), design.get("topic") or "", key=key("topic"),
                              help=tip("study.design.topic", "Used by Module 2 to find related studies."))
        research_questions = st.text_area(lab("Research questions and aims", "study.design.research_questions"),
                                          design.get("research_questions") or "", key=key("rq"),
                                          help=tip("study.design.research_questions"))
        lib = library()
        framework_ids = sorted(lib.frameworks, key=lambda fid: (
            ["theory", "lens", "own", "exploratory"].index(lib.frameworks[fid]["kind"]), lib.frameworks[fid]["label"]))
        c1, c2 = st.columns([2, 3])
        frameworks = c1.multiselect(
            lab("Theoretical framework", "study.design.frameworks"), framework_ids,
            default=[f for f in design.get("frameworks") or [] if f in lib.frameworks],
            format_func=lambda fid: lib.frameworks[fid]["label"], key=key("frameworks"),
            help=tip("study.design.frameworks", "Module 2 builds your concepts and measures from this framework."))
        framework_description = c2.text_area(
            lab("How the framework guides the study", "study.design.framework_description"),
            design.get("framework_description") or "", key=key("fdesc"), height=80,
            help=tip("study.design.framework_description"))
        c1, c2 = st.columns(2)
        with c1:
            designs = multi("Study design", "study_design", s["evidence"].get("study_designs"), "designs", "study.evidence.study_designs",
                            help="Required for datasets and study registrations.")
            units = multi("Unit of analysis", "unit_of_analysis", design.get("unit_of_analysis"), "units", "study.design.unit_of_analysis")
            methods = multi("Data collection method", "data_collection_method", s["evidence"].get("data_collection_methods"), "methods",
                            "study.evidence.data_collection_methods")
        with c2:
            analysis = multi("Analysis method", "analysis_method", s["evidence"].get("analysis_methods"), "analysis",
                             "study.evidence.analysis_methods")
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

        st.subheader("3 · People and place")
        # Full-width radio buttons: these answers are long and a half-width dropdown cuts them off.
        part_options = p.ids("human_participants")
        current_part = s["population"].get("human_participants")
        participants = st.radio(
            lab("Do people take part in this study? *", "study.population.human_participants"), part_options,
            index=part_options.index(current_part) if current_part in part_options else None,
            format_func=lambda t: p.label("human_participants", t), key=key("participants"),
            help=tip("study.population.human_participants",
                     "If no people take part (for example, only texts, artworks, or objects), choose No "
                     "and describe your sources in the next section."))
        c1, c2 = st.columns(2)
        with c1:
            roles = multi("Participants (required if people take part)", "participant_role",
                          s["population"].get("participant_roles"), "roles", "study.population.participant_roles")
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

        st.subheader("4 · Sources")
        st.caption("Texts, archives, images, artworks, media, online content, objects, or existing datasets you study. "
                   "Required if no people take part; useful for any study that analyzes materials.")
        src = s.get("sources") or {}
        c1, c2 = st.columns(2)
        with c1:
            source_types = multi("Source type", "source_type", src.get("types"), "srctypes", "study.sources.types")
            source_rights = single("Rights status of sources", "source_rights", src.get("rights"), "srcrights",
                                   "study.sources.rights")
        with c2:
            holdings = st.text_input(lab("Holding institutions or platforms", "study.sources.holdings"), src.get("holdings") or "",
                                     key=key("holdings"), help=tip("study.sources.holdings"))
            time_period = st.text_input(lab("Time period of sources", "study.sources.time_period"), src.get("time_period") or "",
                                        key=key("period"), placeholder="e.g., 1850-1900 or 19th century",
                                        help=tip("study.sources.time_period", "A year range such as 1850-1900 is also exported as a DataCite Coverage date."))
        sources_description = st.text_area(lab("Sources description", "study.sources.description"), src.get("description") or "",
                                           key=key("srcdesc"), help=tip("study.sources.description"))

        number = 5
        if with_education:
            st.subheader(f"{number} · Education")
            st.caption("Learners, institutions and instructional settings. Remove Education under Start here if this "
                       "study is not in an education setting.")
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
            number += 1

        if with_social:
            st.subheader(f"{number} · Social science")
            st.info(
                f"The social sciences already have a full metadata standard: [DDI, the Data Documentation Initiative]({DDI_URL}). "
                "ICPSR, CESSDA archives, the UK Data Service, and Dataverse all use it. If you deposit with ICPSR, ICPSR "
                "creates the study's DDI record for you; link it below once it is published. Module 3 can also export "
                "this profile and your Module 2 variable plan as a DDI-Codebook file to give your archive at deposit. "
                "The fields here use DDI's own elements, so they stay consistent with that record. What HuMeta adds is "
                "how your constructs and measures connect to theory (Module 2)."
            )
            c1, c2 = st.columns(2)
            with c1:
                kind_of_data = single("Kind of data", "kind_of_data", social.get("kind_of_data"), "kinddata",
                                      "social_science.kind_of_data")
                geographic_unit = st.text_input(lab("Smallest geographic unit", "social_science.geographic_unit"),
                                                social.get("geographic_unit") or "", key=key("geogunit"),
                                                placeholder="e.g., county, school district, census tract",
                                                help=tip("social_science.geographic_unit"))
                response_rate = st.text_input(lab("Response rate", "social_science.response_rate"),
                                              social.get("response_rate") or "", key=key("resprate"),
                                              placeholder="e.g., AAPOR RR3 = 41%", help=tip("social_science.response_rate"))
            with c2:
                universe = st.text_area(lab("Universe", "social_science.universe"), social.get("universe") or "",
                                        key=key("universe"), help=tip("social_science.universe"), height=100)
                weighting = st.text_input(lab("Weighting", "social_science.weighting"), social.get("weighting") or "",
                                          key=key("weight"), help=tip("social_science.weighting"))
            ddi_record = st.text_input(lab("Full DDI documentation (URL)", "social_science.ddi_record"),
                                       social.get("ddi_record") or "", key=key("ddirecord"),
                                       placeholder="e.g., the study's page at ICPSR (after deposit), the CESSDA Data Catalogue, or a Dataverse",
                                       help=tip("social_science.ddi_record"))
            number += 1

        if with_humanities:
            st.subheader(f"{number} · Arts and humanities")
            st.caption(f"Research activities come from [TaDiRAH]({TADIRAH_URL}), the Taxonomy of Digital Research "
                       "Activities in the Humanities. Sources, their time period, holdings, and rights are in section 4.")
            c1, c2 = st.columns(2)
            with c1:
                activities = multi("Research activities", "tadirah_activity", hum.get("research_activities"), "tadirah",
                                   "humanities.research_activities")
                source_languages = st.text_input(lab("Languages of the sources (codes, comma-separated)", "humanities.source_languages"),
                                                 ", ".join(hum.get("source_languages") or []), key=key("srclang"),
                                                 placeholder="e.g., en, fr, la", help=tip("humanities.source_languages"))
            with c2:
                objects_of_study = st.text_area(lab("Works, creators, or objects studied", "humanities.objects_of_study"),
                                                hum.get("objects_of_study") or "", key=key("objects"),
                                                help=tip("humanities.objects_of_study"), height=100)
            editorial = st.text_input(lab("Editorial or encoding standards", "humanities.editorial_standards"),
                                      hum.get("editorial_standards") or "", key=key("editorial"),
                                      placeholder="e.g., TEI P5, IIIF", help=tip("humanities.editorial_standards"))
            number += 1

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
        online_data = multi("Online data practices (required if you use social media, websites, or platform data)",
                            "online_data_practice", s["ethics"].get("online_data"), "online", "study.ethics.online_data",
                            help="Informed by the Association of Internet Researchers' ethical guidelines (IRE 3.0).")
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
    new = profile.empty_record(p, modules=tuple(m for m in profile.MODULES if profile.uses(record, m)))
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
    ns["fields"] = list(s.get("fields") or [])  # set by the starting question
    ns["discipline"] = disciplines
    ns["design"].update({"topic": _blank(topic), "research_questions": _blank(research_questions),
                         "frameworks": frameworks, "framework_description": _blank(framework_description),
                         "unit_of_analysis": units, "sampling_procedure": sampling})
    ns["population"].update({"human_participants": participants, "participant_roles": roles,
                             "description": _blank(population_description),
                             "sample_size": int(sample_size) if sample_size else None})
    ns["context"].update({"locale": locale})
    if with_education:
        new["education"].update({"education_levels": levels, "undergraduate_levels": ug_levels,
                                 "institution_types": institutions, "modality": modality,
                                 "learning_environments": environments, "pedagogy": pedagogy})
    if with_social:
        new["social_science"].update({"kind_of_data": kind_of_data, "universe": _blank(universe),
                                      "geographic_unit": _blank(geographic_unit), "response_rate": _blank(response_rate),
                                      "weighting": _blank(weighting), "ddi_record": _blank(ddi_record)})
    if with_humanities:
        new["humanities"].update({"research_activities": activities, "objects_of_study": _blank(objects_of_study),
                                  "source_languages": [c.strip() for c in source_languages.split(",") if c.strip()],
                                  "editorial_standards": _blank(editorial)})
    ns["evidence"].update({"study_designs": designs, "measurement_evidence": measurement, "data_collection_methods": methods,
                           "analysis_methods": analysis})
    ns["sources"].update({"types": source_types, "rights": source_rights, "holdings": _blank(holdings),
                          "time_period": _blank(time_period), "description": _blank(sources_description)})
    ns["ethics"].update({"human_subjects_review": review, "consent": consent, "consent_for_sharing": sharing,
                         "identifiability": identifiability, "sensitivity_flags": flags, "access_level": access,
                         "online_data": online_data,
                         "governance_notes": _blank(governance_notes)})
    ns["care"].update({"indigenous_data": indigenous, "governance": governance, "statement": _blank(care_statement),
                       "local_contexts_project": _blank(lc_project),
                       "local_contexts_labels": [x.strip() for x in lc_labels.split(",") if x.strip()]})
    return new


def show_issues(issues: list[profile.Issue]) -> None:
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    if not issues:
        st.success("This study profile meets every requirement of HuMeta.")
    for issue in errors:
        st.error(f"**{issue.element}**: {issue.message}" + (f" ({issue.rule})" if issue.rule else ""))
    for issue in warnings:
        st.warning(f"**{issue.element}**: {issue.message}" + (f" ({issue.rule})" if issue.rule else ""))
