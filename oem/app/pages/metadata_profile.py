# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Module 6: STEMEd+ Metadata Profile.

Fill in a STEMEd+ Metadata Application Profile record (pre-filled from Modules
1 and 2), check it against the profile's rules, and export STEMEd+ JSON,
DataCite 4.7 JSON/XML, and ERIC descriptors. Logic lives in oem/profile.py.
"""

from __future__ import annotations

import datetime as dt
import json
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
def _library() -> Library:
    return Library.load()


def _store(record: dict, reset_widgets: bool = False) -> None:
    st.session_state["stemed_record"] = record
    project = current_project()
    project["stemed_record"] = record
    st.session_state["project"] = project
    if reset_widgets:
        st.session_state["stemed_form_version"] = st.session_state.get("stemed_form_version", 0) + 1


def _none_if_blank(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


def render(*, signed_in: bool, publish_disabled: bool, publish_hint: str | None) -> None:
    st.header("🏷️ STEMEd+ Metadata Profile")
    p = profile.load()
    lib = _library()
    st.caption(
        f"Describe your study or dataset with the [STEMEd+ Metadata Application Profile]({SPEC_URL}) "
        f"(version {p.version}). It records what generic repositories miss: constructs measured, population "
        "and context, instructional setting, evidence type, consent, and Indigenous data governance (CARE). "
        "Exports work with DataCite and ERIC."
    )

    project = current_project()
    record = st.session_state.get("stemed_record") or project.get("stemed_record")

    with st.expander("Start or reload a record", expanded=record is None):
        col_prefill, col_upload, col_blank = st.columns(3)
        with col_prefill:
            st.markdown("**From this project**")
            st.caption("Uses your Module 1 study record and Module 2 plan.")
            if st.button("Pre-fill from Modules 1–2", key="stemed_prefill", disabled=not project.get("study"),
                         help=None if project.get("study") else "Save a Module 1 study record (or open a project file) first."):
                _store(profile.from_project(project, lib), reset_widgets=True)
                st.rerun()
        with col_upload:
            st.markdown("**From a saved record**")
            uploaded = st.file_uploader("STEMEd+ record (.json)", type=["json"], key="stemed_upload")
            if uploaded is not None and st.button("Load this record", key="stemed_load"):
                try:
                    loaded = json.loads(uploaded.getvalue().decode("utf-8"))
                    if loaded.get("profile") != "stemed-ap":
                        raise ValueError("This file is not a STEMEd+ profile record.")
                    _store(profile.migrate(loaded, p), reset_widgets=True)
                    st.rerun()
                except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as error:
                    st.error(f"Could not load the record: {error}")
        with col_blank:
            st.markdown("**From scratch**")
            st.caption("For a resource not described in Modules 1–2.")
            if st.button("Start a blank record", key="stemed_blank"):
                _store(profile.empty_record(p), reset_widgets=True)
                st.rerun()

    if record is None:
        st.info("Choose how to start above.")
        return
    record = profile.migrate(record, p)
    res, s = record["resource"], record["stemed"]
    v = st.session_state.get("stemed_form_version", 0)

    def key(name: str) -> str:
        return f"stemed_{name}_{v}"

    def multi(label: str, vocab_id: str, current: list[str], name: str, help: str | None = None) -> list[str]:
        ids = p.ids(vocab_id)
        return st.multiselect(label, ids, default=[c for c in current or [] if c in ids],
                              format_func=lambda t: p.label(vocab_id, t), key=key(name), help=help)

    def single(label: str, vocab_id: str, current: str | None, name: str, help: str | None = None) -> str | None:
        options = [None, *p.ids(vocab_id)]
        return st.selectbox(label, options, index=options.index(current) if current in options else 0,
                            format_func=lambda t: "— choose —" if t is None else p.label(vocab_id, t),
                            key=key(name), help=help)

    construct_labels = {c["label"]: cid for cid, c in lib.constructs.items()}
    construct_names = {cid: label for label, cid in construct_labels.items()}
    instrument_labels = {i["name"]: iid for iid, i in lib.instruments.items()}
    instrument_names = {iid: label for label, iid in instrument_labels.items()}

    with st.form(key=f"stemed_form_{v}"):
        st.subheader("1 · The resource")
        c1, c2 = st.columns([3, 1])
        title = c1.text_input("Title *", res.get("title") or "", key=key("title"))
        type_options = list(profile.RESOURCE_TYPES)
        resource_type = c2.selectbox("Resource type *", type_options,
                                     index=type_options.index(res.get("resource_type") or "Dataset"), key=key("rtype"),
                                     help="DataCite resource types. Use Dataset for data, Instrument for a measure, StudyRegistration for a preregistration.")
        creators_df = st.data_editor(
            pd.DataFrame(res.get("creators") or [{"name": "", "orcid": None, "affiliation": None}],
                         columns=["name", "orcid", "affiliation"]),
            num_rows="dynamic", use_container_width=True, key=key("creators"),
            column_config={
                "name": st.column_config.TextColumn("Creator name *"),
                "orcid": st.column_config.TextColumn("ORCID iD", help="Format 0000-0000-0000-0000"),
                "affiliation": st.column_config.TextColumn("Affiliation"),
            },
        )
        c1, c2, c3 = st.columns(3)
        publisher = c1.text_input("Publisher *", res.get("publisher") or "", key=key("publisher"),
                                  help="Repository or institution that makes the resource available.")
        publication_year = c2.number_input("Publication year *", min_value=1900, max_value=2100, step=1,
                                           value=int(res.get("publication_year") or dt.date.today().year), key=key("year"))
        doi = c3.text_input("DOI (if assigned)", (res.get("identifier") or {}).get("value") or "", key=key("doi"),
                            placeholder="10.xxxx/xxxxx")
        description = st.text_area("Description / abstract", res.get("description") or "", key=key("description"))
        c1, c2, c3 = st.columns(3)
        keywords = c1.text_input("Keywords (comma-separated)", ", ".join(res.get("keywords") or []), key=key("keywords"))
        language = c2.text_input("Language code", res.get("language") or "en", key=key("language"), help="BCP 47, e.g. en, es")
        current_license = (res.get("license") or {}).get("spdx")
        license_options = list(LICENSES)
        license_id = c3.selectbox("License", license_options,
                                  index=license_options.index(current_license) if current_license in license_options else 0,
                                  format_func=lambda k: LICENSES[k], key=key("license"))
        dates = res.get("collection_dates") or {}
        geo = res.get("geography") or {}
        c1, c2, c3 = st.columns(3)
        start = c1.text_input("Data collection start (YYYY-MM-DD)", dates.get("start") or "", key=key("start"))
        end = c2.text_input("Data collection end (YYYY-MM-DD)", dates.get("end") or "", key=key("end"))
        states = c3.multiselect("US states", US_STATES, default=[x for x in geo.get("us_states") or [] if x in US_STATES], key=key("states"))
        countries = st.text_input("Countries (ISO codes, comma-separated)", ", ".join(geo.get("countries") or (["US"] if states else [])),
                                  key=key("countries"))

        st.subheader("2 · Constructs measured")
        st.caption("Pick constructs from the shared vocabulary and, if you used one, the library instrument that measured them. "
                   "Pre-filled from your Module 2 variables where they matched.")
        construct_df = st.data_editor(
            pd.DataFrame(
                [{"construct": construct_names.get(c["construct_id"]), "instrument": instrument_names.get(c.get("instrument_id"))}
                 for c in s.get("constructs") or []] or [{"construct": None, "instrument": None}],
                columns=["construct", "instrument"]),
            num_rows="dynamic", use_container_width=True, key=key("constructs"),
            column_config={
                "construct": st.column_config.SelectboxColumn("Construct", options=sorted(construct_labels)),
                "instrument": st.column_config.SelectboxColumn("Instrument (optional)", options=sorted(instrument_labels)),
            },
        )

        st.subheader("3 · Population and context")
        c1, c2 = st.columns(2)
        with c1:
            disciplines = multi("Discipline", "discipline", s.get("discipline"), "discipline")
            roles = multi("Participants *", "participant_role", s["population"].get("participant_roles"), "roles")
            levels = multi("Education level *", "education_level", s["population"].get("education_levels"), "levels")
            ug_levels = multi("Undergraduate course level", "undergraduate_level", s["population"].get("undergraduate_levels"), "ug")
        with c2:
            institutions = multi("Institution type", "institution_type", s["context"].get("institution_types"), "inst")
            locale = multi("Locale", "locale", s["context"].get("locale"), "locale")
            sample_size = st.number_input("Sample size (N)", min_value=0, step=1,
                                          value=int(s["population"].get("sample_size") or 0), key=key("n"),
                                          help="Leave 0 if not known.")
        population_description = st.text_area("Population description (no identifying details)",
                                              s["population"].get("description") or "", key=key("popdesc"))

        st.subheader("4 · Instructional setting")
        c1, c2, c3 = st.columns(3)
        with c1:
            modality = multi("Modality", "modality", s["setting"].get("modality"), "modality")
        with c2:
            environments = multi("Learning environment", "learning_environment", s["setting"].get("learning_environments"), "env")
        with c3:
            pedagogy = multi("Instructional approach", "pedagogy", s["setting"].get("pedagogy"), "pedagogy")

        st.subheader("5 · Evidence")
        c1, c2, c3 = st.columns(3)
        with c1:
            designs = multi("Study design", "study_design", s["evidence"].get("study_designs"), "designs",
                            help="Required for datasets and study registrations.")
        with c2:
            measurement = multi("Measurement evidence", "measurement_evidence", s["evidence"].get("measurement_evidence"), "measurement",
                                help="Required for instruments. Sources of validity evidence follow the Standards for Educational and Psychological Testing.")
        with c3:
            methods = multi("Data collection method", "data_collection_method", s["evidence"].get("data_collection_methods"), "methods")

        st.subheader("6 · Ethics, consent, and access")
        c1, c2, c3 = st.columns(3)
        with c1:
            review = single("Human-subjects review *", "human_subjects_review", s["ethics"].get("human_subjects_review"), "review")
            consent = single("Participation consent", "consent", s["ethics"].get("consent"), "consent")
        with c2:
            sharing = single("Consent for data sharing *", "consent_for_sharing", s["ethics"].get("consent_for_sharing"), "sharing",
                             help="What participants agreed to about sharing beyond your team.")
            identifiability = single("Identifiability *", "identifiability", s["ethics"].get("identifiability"), "ident")
        with c3:
            access = single("Access level *", "access_level", s["ethics"].get("access_level"), "access")
            flags = multi("Sensitivity flags", "sensitivity_flag", s["ethics"].get("sensitivity_flags"), "flags")

        st.subheader("7 · Indigenous data governance (CARE)")
        st.caption(
            f"The [CARE Principles]({CARE_URL}) (Collective benefit, Authority to control, Responsibility, Ethics) "
            "guide work with data about Indigenous Peoples, nations, communities, lands, and knowledges. Communities may "
            f"apply [Local Contexts]({LOCAL_CONTEXTS_URL}) Traditional Knowledge or Biocultural Labels and Notices."
        )
        care = s["care"]
        c1, c2 = st.columns(2)
        with c1:
            indigenous = single("Does this resource contain or derive from Indigenous data? *", "indigenous_data",
                                care.get("indigenous_data"), "indigenous")
            governance = single("Governance arrangement (required if yes)", "indigenous_governance", care.get("governance"), "governance")
        with c2:
            lc_project = st.text_input("Local Contexts Hub project URL", care.get("local_contexts_project") or "", key=key("lcproj"))
            lc_labels = st.text_input("Local Contexts Labels / Notices (comma-separated)",
                                      ", ".join(care.get("local_contexts_labels") or []), key=key("lclabels"))
        care_statement = st.text_area("CARE statement (required if yes)", care.get("statement") or "", key=key("care"),
                                      help="Describe collective benefit to the communities involved, how their authority to control the "
                                           "data is respected, and your responsibility and ethics commitments.")

        submitted = st.form_submit_button("Check and save to project", type="primary", use_container_width=True)

    if submitted:
        creators = []
        for row in creators_df.fillna("").to_dict(orient="records"):
            if str(row.get("name") or "").strip():
                orcid = re.search(r"(\d{4}-){3}\d{3}[\dX]", str(row.get("orcid") or ""))
                creators.append({"name": str(row["name"]).strip(), "orcid": orcid.group(0) if orcid else None,
                                 "affiliation": _none_if_blank(str(row.get("affiliation") or ""))})
        constructs = []
        for row in construct_df.to_dict(orient="records"):
            cid = construct_labels.get(row.get("construct"))
            if cid and all(c["construct_id"] != cid for c in constructs):
                constructs.append({"construct_id": cid, "instrument_id": instrument_labels.get(row.get("instrument")),
                                   "version_id": None, "dimension_id": None})
        doi_match = re.search(r"10\.\d{4,9}/\S+", doi or "")
        new = profile.empty_record(p)
        new["resource"].update({
            "title": title.strip(), "creators": creators, "publisher": publisher.strip(),
            "publication_year": int(publication_year), "resource_type": resource_type,
            "identifier": {"value": doi_match.group(0), "type": "DOI"} if doi_match else None,
            "description": _none_if_blank(description),
            "keywords": [k.strip() for k in keywords.split(",") if k.strip()],
            "language": _none_if_blank(language),
            "license": {"spdx": license_id, "name": LICENSES[license_id], "url": LICENSE_URLS.get(license_id)} if license_id else None,
            "collection_dates": {"start": _none_if_blank(start), "end": _none_if_blank(end)} if (start.strip() or end.strip()) else None,
            "geography": {"countries": [c.strip().upper() for c in countries.split(",") if c.strip()], "us_states": states}
            if (countries.strip() or states) else None,
            "related": res.get("related") or [],
            "funding": res.get("funding") or [],
        })
        ns = new["stemed"]
        ns["constructs"] = constructs
        ns["discipline"] = disciplines
        ns["population"].update({"participant_roles": roles, "education_levels": levels, "undergraduate_levels": ug_levels,
                                 "description": _none_if_blank(population_description),
                                 "sample_size": int(sample_size) if sample_size else None})
        ns["context"].update({"institution_types": institutions, "locale": locale})
        ns["setting"].update({"modality": modality, "learning_environments": environments, "pedagogy": pedagogy})
        ns["evidence"].update({"study_designs": designs, "measurement_evidence": measurement, "data_collection_methods": methods})
        ns["ethics"].update({"human_subjects_review": review, "consent": consent, "consent_for_sharing": sharing,
                             "identifiability": identifiability, "sensitivity_flags": flags, "access_level": access})
        ns["care"].update({"indigenous_data": indigenous, "governance": governance, "statement": _none_if_blank(care_statement),
                           "local_contexts_project": _none_if_blank(lc_project),
                           "local_contexts_labels": [x.strip() for x in lc_labels.split(",") if x.strip()]})
        _store(new)
        record = new
        st.success("Saved to your project. Download the project file to keep it; the app does not store a copy.")

    st.subheader("Profile check")
    issues = profile.validate(record, lib, p)
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    if not issues:
        st.success("This record meets every requirement of the STEMEd+ profile.")
    for issue in errors:
        st.error(f"**{issue.element}**: {issue.message}" + (f" ({issue.rule})" if issue.rule else ""))
    for issue in warnings:
        st.warning(f"**{issue.element}**: {issue.message}" + (f" ({issue.rule})" if issue.rule else ""))

    st.subheader("Export")
    slug = re.sub(r"[^a-z0-9]+", "-", (record["resource"].get("title") or "record").lower()).strip("-")[:50] or "record"
    st.download_button("STEMEd+ record (JSON)", json.dumps(record, ensure_ascii=False, indent=2).encode("utf-8"),
                       file_name=f"{slug}.stemed-ap.json", mime="application/json", key="stemed_dl_record",
                       use_container_width=True)
    if errors:
        st.info("Fix the errors above to enable the DataCite and ERIC exports.")
        return
    c1, c2 = st.columns(2)
    with c1:
        datacite = profile.to_datacite_json(record, lib, p)
        st.download_button("DataCite 4.7 metadata (JSON)", json.dumps(datacite, ensure_ascii=False, indent=2).encode("utf-8"),
                           file_name=f"{slug}.datacite.json", mime="application/json", key="stemed_dl_dcjson",
                           use_container_width=True,
                           help="DataCite REST API 'attributes'. Without a DOI, use it to register a new DOI through your repository or DataCite member.")
    with c2:
        if (record["resource"].get("identifier") or {}).get("type") == "DOI":
            st.download_button("DataCite 4.7 metadata (XML)", profile.to_datacite_xml(record, lib, p).encode("utf-8"),
                               file_name=f"{slug}.datacite.xml", mime="application/xml", key="stemed_dl_dcxml",
                               use_container_width=True)
        else:
            st.button("DataCite 4.7 metadata (XML)", disabled=True, use_container_width=True, key="stemed_dl_dcxml_off",
                      help="DataCite XML requires a DOI. Add the DOI once assigned.")
    descriptors = profile.eric_descriptors(record, lib, p)
    pending = [d for d in profile.eric_descriptors(record, lib, p, include_unverified=True) if d not in descriptors]
    st.markdown("**ERIC Thesaurus descriptors** (for ERIC submissions and education indexes)")
    st.code("; ".join(descriptors) or "No descriptors yet: add constructs, levels, settings, or designs.", language=None)
    st.download_button("ERIC descriptors (text)", "\n".join(descriptors).encode("utf-8"), file_name=f"{slug}.eric-descriptors.txt",
                       mime="text/plain", key="stemed_dl_eric", use_container_width=True)
    if pending:
        st.caption("Not yet verified against the current ERIC Thesaurus, so not included: " + "; ".join(pending))
    with st.expander("Preview DataCite JSON"):
        st.json(datacite, expanded=False)
