# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Module 1: Study Metadata Schema Registry."""

from __future__ import annotations
import streamlit as st
import json
import time
import uuid
from oem.vocab import (EDUCATION_LEVEL_OPTIONS, PROGRAM_TYPE_OPTIONS, SAMPLING_PROCEDURE_OPTIONS, UNDERGRADUATE_LEVEL_OPTIONS, UNIT_OF_ANALYSIS_OPTIONS)
from oem.app.common import (automate_github_pull_request, current_project, render_project_download)


def render(*, signed_in: bool, publish_disabled: bool, publish_hint: str | None) -> None:
    st.header("1. Study Metadata Schema Registry")
    st.caption("Document the study, its design and population, and the ethical and data-governance context needed for responsible sharing.")
    st.markdown("---")
    
    # --- DYNAMIC AUTHOR TRACKING INITIALIZATION ---
    if "authors_list" not in st.session_state:
        st.session_state.authors_list = [{"name": "", "orcid": ""}]

    with st.container(border=True):
        st.subheader("Step 1 — Study Team")
        st.caption("Add study creators and their ORCID iDs. At least one author name is required.")

        updated_authors = []
        for idx, author in enumerate(st.session_state.authors_list):
            col_name, col_orcid, col_del = st.columns([2, 2, 0.5], vertical_alignment="bottom")

            with col_name:
                auth_name = st.text_input(
                    f"Author {idx + 1} Name",
                    value=author["name"],
                    key=f"auth_name_{idx}",
                    placeholder="e.g., Dr. Jane Doe",
                    help="Enter the author's full name as it should appear in the study record."
                )
            with col_orcid:
                auth_orcid = st.text_input(
                    f"Author {idx + 1} ORCID iD",
                    value=author["orcid"],
                    key=f"auth_orcid_{idx}",
                    placeholder="https://orcid.org/0000-0000-0000-0000",
                    help="Enter a full ORCID URL or ORCID identifier (format: 0000-0000-0000-0000)."
                )
            with col_del:
                if st.button(
                    "🗑️",
                    key=f"auth_del_{idx}",
                    disabled=len(st.session_state.authors_list) <= 1,
                    help="Remove this author."
                ):
                    st.session_state.authors_list.pop(idx)
                    st.rerun()

            updated_authors.append({"name": auth_name, "orcid": auth_orcid})

        st.session_state.authors_list = updated_authors
        if st.button("➕ Add Author", help="Add another study creator."):
            st.session_state.authors_list.append({"name": "", "orcid": ""})
            st.rerun()

    # --- MAIN SUBMISSION FORM ---
    with st.form("metadata_standards_form", clear_on_submit=False):
        with st.container(border=True):
            st.subheader("Step 2 — Study Identity")
            st.caption("Core Dublin Core metadata. Fields marked * are required.")
            title = st.text_input(
                "Study title (dc:title) *",
                placeholder="e.g., Impact of Open Textbooks on Course-Level Retention",
                help="Use the full, descriptive title that should appear in study catalogs."
            )
            detail_col1, detail_col2 = st.columns(2)
            with detail_col1:
                keywords = st.text_input(
                    "Subject keywords (dc:subject)",
                    placeholder="OER, student motivation, retention",
                    help="Separate keywords with commas; these improve study discovery."
                )
            with detail_col2:
                language = st.selectbox(
                    "Language (dc:language)",
                    options=["English (en)", "Spanish (es)", "French (fr)", "Other / Multilingual"],
                    help="Select the primary language used in the study materials."
                )
            study_identifier = st.text_input(
                "Study DOI or persistent identifier",
                placeholder="e.g., DOI or repository accession",
                help="Use the same persistent identifier in Module 2 when documenting variables and measures.",
            )
            context_col1, context_col2 = st.columns(2)
            with context_col1:
                institution = st.text_input(
                    "Institution or organization",
                    placeholder="e.g., Example University",
                )
            with context_col2:
                funding_source = st.text_input(
                    "Funding source",
                    placeholder="Name funder or enter Not funded",
                )
            description = st.text_area(
                "Description / abstract (dc:description)",
                placeholder="Summarize the research objectives, design, and findings...",
                help="Provide a concise summary of the study and its research context."
            )
            research_questions = st.text_area(
                "Research questions and aims",
                placeholder="List the primary research questions, objectives, or hypotheses.",
                help="Record the questions or aims that guide the study and its measures."
            )

        with st.container(border=True):
            st.subheader("Step 3 — Study Design and Context (DDI / CEDS)")
            st.caption(
                "Describe the unit, collection approach, sampling, and study timeline across human-science "
                "research, including studies in formal institutions, informal settings, and the general public."
            )
            ddi_col1, ddi_col2 = st.columns(2)
            with ddi_col1:
                unit_of_analysis = st.selectbox(
                    "Unit of analysis",
                    options=UNIT_OF_ANALYSIS_OPTIONS,
                    help="Identify the person, group, organization, place, event, or artifact about which observations are made."
                )
            with ddi_col2:
                sampling_procedure = st.selectbox(
                    "Sampling procedure",
                    options=SAMPLING_PROCEDURE_OPTIONS,
                    help="Select the approach used to recruit or select participants, visitors, groups, organizations, or sites."
                )
                time_method = st.selectbox(
                    "Study design / time method",
                    options=[
                        "Cross-sectional / Single Time Point Assessment",
                        "Longitudinal: Cohort Study / Repeated Measures",
                        "Longitudinal: Trend / Multiple Intervals",
                        "Experimental / Pre-Post Testing",
                        "Time Series Analysis"
                    ],
                    help="Choose the temporal design that best describes the study."
                )

        st.subheader("Step 4 — Study Scope and Population (CEDS)")
        st.caption(
            "Describe the study period, locations, settings, and people or other populations involved. "
            "This includes education research as well as human-science research with community members, "
            "the general public, museum visitors, and other informal-space participants."
        )
        with st.container(border=True):
            st.markdown("**Study period and location**")
            study_dates = st.date_input(
                "Study start and end dates",
                value=(),
                format="YYYY-MM-DD",
                help="Choose the start date and then the end date. Leave blank if dates are not known or cannot be shared.",
            )
            scope_col1, scope_col2 = st.columns(2)
            with scope_col1:
                state_origin = st.selectbox(
                    "State / geographic origin",
                    options=["National/Multi-State", "AK", "AL", "AR", "AZ", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "IA", "ID", "IL", "IN", "KS", "KY", "LA", "MA", "MD", "ME", "MI", "MN", "MO", "MS", "MT", "NC", "ND", "NE", "NH", "NJ", "NM", "NV", "NY", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VA", "VT", "WA", "WI", "WV", "WY"],
                    help="Choose the state or geographic scope where the study was conducted."
                )
            with scope_col2:
                locale_setting = st.selectbox(
                    "Locale",
                    options=[
                        "City", "Suburban", "Town", "Rural",
                        "Virtual / Online Environment", "Multiple / mixed locations",
                    ],
                    help="Choose the geographic or virtual setting type."
                )

        with st.container(border=True):
            st.markdown("**Population, age or education level, and participation context**")
            participant_populations = st.multiselect(
                "Participant population(s)",
                options=[
                    "General public / community members",
                    "Museum, gallery, library, or science-center visitors",
                    "Event, exhibition, or festival visitors",
                    "Children or youth",
                    "Adults",
                    "Older adults",
                    "Families or household groups",
                    "Students / learners",
                    "Teachers / educators",
                    "Researchers / professionals",
                    "Specific community or cultural group",
                    "Other / not listed",
                ],
                help="Select all populations included, whether or not participants are in a formal education program.",
            )
            study_settings = st.multiselect(
                "Study setting(s)",
                options=[
                    "K-12 school or classroom",
                    "College, university, or other postsecondary institution",
                    "Museum, gallery, or cultural institution",
                    "Library or science center",
                    "Community organization or public space",
                    "Home or family setting",
                    "Workplace or professional setting",
                    "Public event, exhibition, or festival",
                    "Online or virtual environment",
                    "Multiple settings",
                    "Other / not listed",
                ],
                help="Select where participation, observation, or data collection occurs.",
            )
            grade_level = st.multiselect(
                "Age / education level or learning setting",
                options=EDUCATION_LEVEL_OPTIONS,
                help="Use this for age-relevant or education context; general-public and visitor studies are included.",
            )
            undergraduate_level = st.multiselect(
                "Undergraduate level, if applicable",
                options=UNDERGRADUATE_LEVEL_OPTIONS,
                help="Select all undergraduate levels represented, from entry-level through advanced and capstone study.",
            )
            program_type = st.multiselect(
                "Program, organization, or participation context",
                options=PROGRAM_TYPE_OPTIONS,
                help="Select a formal program or an informal, community, visitor, or general-public participation context.",
            )

        with st.container(border=True):
            st.markdown("**Content domain or topic**")
            content_domain = st.text_input(
                "Content domain or topic",
                placeholder="e.g., climate science, teacher professional learning, community health",
                help="Describe the main subject or topic area of the study in your own words.",
                key="module1_content_domain",
            )

        # --- SUBMIT BUTTON & VALIDATION (INSIDE THE FORM CONTAINER) ---
        st.subheader("Step 5 — Ethics, Permissions, and Data Stewardship")
        st.caption(
            "Record researcher-reported governance context. These fields do not verify approvals "
            "or determine whether data may be shared."
        )
        ethics_col1, ethics_col2 = st.columns(2)
        with ethics_col1:
            review_status = st.selectbox(
                "Human-subjects / ethics review status",
                options=[
                    "Not yet assessed",
                    "Submitted / pending",
                    "Approved",
                    "Exempt determination received",
                    "Not required — determination received",
                    "Other / not listed",
                ],
            )
            consent_model = st.selectbox(
                "Participant consent or authorization",
                options=[
                    "Not yet assessed",
                    "Informed consent obtained",
                    "Parent/guardian permission and participant assent",
                    "Waiver or alteration approved",
                    "Not applicable — determination received",
                    "Other / not listed",
                ],
            )
        with ethics_col2:
            data_sensitivity = st.multiselect(
                "Data sensitivity and identifiers",
                options=[
                    "No direct identifiers expected",
                    "Direct identifiers",
                    "Indirect identifiers / small groups",
                    "Sensitive personal information",
                    "Education records",
                    "Not yet assessed",
                ],
            )
            sharing_plan = st.selectbox(
                "Planned data access",
                options=[
                    "Not yet assessed",
                    "No data sharing planned",
                    "Private — owner only",
                    "Controlled access through an external repository",
                    "Public release planned, pending review",
                ],
                help="This records a plan only. Module 3 separately requires permissions and privacy review before upload or public release.",
            )
        governance_notes = st.text_area(
            "Approval references, data-use restrictions, and governance notes",
            placeholder="Optional: oversight reference, agreement restrictions, retention or de-identification requirements.",
        )

        submit_metadata = st.form_submit_button("Save study to project file")
        
        if submit_metadata:
            has_author = any(auth["name"].strip() for auth in st.session_state.authors_list)
            
            if not title:
                st.error("Study title is required.")
            elif not has_author:
                st.error("At least one Creator/Author Name is required.")
            else:
                try:
                    # Keep author details structured in the study description.
                    authors = [
                        {
                            "name": str(auth.get("name") or "").strip(),
                            "orcid": str(auth.get("orcid") or "").strip()
                        }
                        for auth in st.session_state.authors_list
                    ]
                    authors = [author for author in authors if author["name"] or author["orcid"]]
                    authors_string = ", ".join(
                        author["name"] for author in authors if author["name"]
                    )
                    study_date_range = study_dates if isinstance(study_dates, (tuple, list)) else ()
                    study_start_date = (
                        study_date_range[0].isoformat()
                        if len(study_date_range) >= 1 and study_date_range[0]
                        else ""
                    )
                    study_end_date = (
                        study_date_range[1].isoformat()
                        if len(study_date_range) >= 2 and study_date_range[1]
                        else ""
                    )
                    
                    # Preserve every form value in the existing studies table schema.
                    study_metadata = {
                        "authors": authors,
                        "study_doi_or_persistent_identifier": str(study_identifier or "").strip(),
                        "institution": str(institution or "").strip(),
                        "funding_source": str(funding_source or "").strip(),
                        "research_questions_and_aims": str(research_questions or "").strip(),
                        "subject_keywords": str(keywords or "").strip(),
                        "language": str(language or "").strip(),
                        "unit_of_analysis": str(unit_of_analysis or "").strip(),
                        "sampling_procedure": str(sampling_procedure or "").strip(),
                        "time_method": str(time_method or "").strip(),
                        "study_start_date": study_start_date,
                        "study_end_date": study_end_date,
                        "state_origin": str(state_origin or "").strip(),
                        "locale_setting": str(locale_setting or "").strip(),
                        "participant_populations": participant_populations or [],
                        "study_settings": study_settings or [],
                        "grade_level": grade_level or [],
                        "undergraduate_level": undergraduate_level or [],
                        "program_type": program_type or [],
                        "content_domain": str(content_domain or "").strip(),
                        "ethics_review_status": str(review_status or "").strip(),
                        "consent_or_authorization": str(consent_model or "").strip(),
                        "data_sensitivity_and_identifiers": data_sensitivity or [],
                        "planned_data_access": str(sharing_plan or "").strip(),
                        "governance_notes": str(governance_notes or "").strip()
                    }
                    description_record = {
                        "description": str(description or "").strip() or "No description provided.",
                        "metadata": study_metadata
                    }

                    # Same record shape as before (the earlier database used it),
                    # now kept only in the researcher's project file.
                    project = current_project()
                    existing_study = project.get("study") or {}
                    study_record = {
                        "id": existing_study.get("id") or str(uuid.uuid4()),
                        "study_title": str(title).strip(),
                        "principal_investigator": authors_string,
                        "institution": str(institution or "").strip(),
                        "funding_source": str(funding_source or "").strip(),
                        "study_description": json.dumps(description_record, ensure_ascii=False),
                        "created_at": existing_study.get("created_at")
                        or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    }
                    project["study"] = study_record
                    st.session_state["project"] = project

                    # Reset authors list back to a clean default state for the next entry session
                    st.session_state.authors_list = [{"name": "", "orcid": ""}]
                    st.session_state["module1_saved_notice"] = title.strip()
                except Exception as form_error:
                    st.error(f"Could not build the study record: {form_error}")

    if st.session_state.get("module1_saved_notice"):
        st.success(
            f"Study record ready: {st.session_state['module1_saved_notice']}. Download the "
            "project file to keep it — the app does not store a copy."
        )
    if current_project().get("study"):
        render_project_download(key="module1_project_download")


    # --- MODULE 1 EXTENSION PIPELINE BUTTON ---
    st.markdown("---")
    st.markdown("### 🚀 Propose Extensions to Core Study Metadata Architecture")
    st.caption("Suggest new Dublin Core (DCMES) descriptors, alternative CEDS geographic drop-down indicators, or updated standard options.")
    
    with st.expander("💡 Click to Draft a Metadata Schema Suggestion"):
        suggested_schema_field = st.text_input("Target Element / Field Code to Change", placeholder="e.g., CEDS Section 2 - Alternative Grade Classifications", key="mod1_suggest_field")
        suggested_schema_text = st.text_area("Detailed Suggestion / Additions Details", placeholder="Describe new drop-down selections, alternative labels, or documentation requirements...", key="mod1_suggest_text")
        
    if suggested_schema_field and suggested_schema_text:
            # Bypasses multi-line quotation leaks completely using isolated string tuples
            schema_payload = (
                f"**Study Metadata Architecture Amendment Proposal**\n\n"
                f"**Target Element:** {suggested_schema_field}\n\n"
                f"### PROPOSED ALTERNATIVE SELECTIONS / LABELS\n"
                f"```text\n{suggested_schema_text}\n```\n\n"
                f"---\n*Submitted securely via the Study Metadata Schema Registry Interface Box.*"
            )
            
            st.markdown("##### **Submit Change Directly to GitHub**")
            st.caption("Clicking the button below will automatically fork a branch, save your suggestion, and issue a formal pull request.")
            
            # This triggers your automated PyGithub pipeline function
            if st.button(
                "🚀 Push Proposal to GitHub as Pull Request",
                key="submit_mod1_pr_btn",
                disabled=publish_disabled,
                help=publish_hint,
            ):
                with st.spinner("Talking to GitHub API, creating branch, and launching Pull Request..."):
                    safe_filename = f"metadata_proposal_{suggested_schema_field.lower().replace(' ', '_')}.txt"
                    summary_title = f"Update Metadata Section: {suggested_schema_field}"
                    
                    result_message = automate_github_pull_request(
                        suggestion_type="Metadata",
                        file_name=safe_filename,
                        file_content=schema_payload,
                        title_summary=summary_title
                    )
                    
                    if "❌" in result_message:
                        st.error(result_message)
                    else:
                        st.success(result_message)
