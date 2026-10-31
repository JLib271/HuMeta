# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Module 2: Variable Instrument Architect."""

from __future__ import annotations
import streamlit as st
import pandas as pd
import io
import json
import time
import uuid
from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowEdge, StreamlitFlowNode
from streamlit_flow.layouts import ManualLayout
from streamlit_flow.state import StreamlitFlowState
from oem.vocab import (APP_DIR, THEORY_MAP)
from oem.app.common import (MEASURE_CATALOG_PATH, automate_github_pull_request, citation_for_framework, context_search_terms, current_project, find_measure_suggestions, load_measure_catalog, load_published_summaries, open_review_pull_request, render_project_download, safe_slug)


def render(*, signed_in: bool, publish_disabled: bool, publish_hint: str | None) -> None:
    st.header("2. Variable Instrument Architect")
    st.caption(
        "Select theories, models, or frameworks; review their associated factors; then plan "
        "how those factors will be measured in your study."
    )
    st.markdown("---")
    
    st.subheader("Study context (optional)")
    st.caption(
        "Uses the study in your current project (saved in Module 1 or opened from a "
        "project file in the sidebar). Theory and measurement planning happens here."
    )

    project = current_project()
    selected_study = project.get("study") or None
    study_metadata = {}
    saved_module2_plan = project.get("module2_plan") or {}
    if not isinstance(saved_module2_plan, dict):
        saved_module2_plan = {}
    if selected_study:
        try:
            description_record = json.loads(selected_study.get("study_description") or "{}")
            if isinstance(description_record, dict):
                study_metadata = description_record.get("metadata", {})
                if not isinstance(study_metadata, dict):
                    study_metadata = {}
        except (TypeError, json.JSONDecodeError):
            st.warning("This study's saved metadata could not be read as structured JSON.")
            study_metadata = {}
        with st.expander("Study context from Module 1"):
            st.write(f"**Study:** {selected_study.get('study_title') or 'Untitled study'}")
            st.write(f"**Persistent identifier:** {study_metadata.get('study_doi_or_persistent_identifier') or 'Not provided'}")
            st.write(f"**Unit of analysis:** {study_metadata.get('unit_of_analysis') or 'Not specified'}")
            st.write(f"**Population:** {', '.join(study_metadata.get('participant_populations', [])) or 'Not specified'}")
            st.write(f"**Study settings:** {', '.join(study_metadata.get('study_settings', [])) or 'Not specified'}")
            st.write(f"**Study period:** {study_metadata.get('study_start_date') or 'Not specified'} to {study_metadata.get('study_end_date') or 'Not specified'}")
    else:
        st.info(
            "No study in your current project. You can still build a standalone theory and "
            "measurement draft, or save a study in Module 1 / open a project file first."
        )
    repository_id = study_metadata.get("study_doi_or_persistent_identifier", "")
    unit_of_analysis = study_metadata.get("unit_of_analysis", "Not specified")
    sampling_method = study_metadata.get("sampling_procedure", "Not specified")
    sampling_procedure = ""
    if study_metadata.get("sampling_procedure"):
        sampling_procedure = str(study_metadata["sampling_procedure"])

    workflow_key = selected_study.get("id") if selected_study else "draft"
    st.subheader("Find previously shared studies with related context")
    st.caption(
        "Search summaries that researchers chose to publish (reviewed before listing). Use a topic, population, "
        "setting, or other context; results are design examples, not validated recommendations."
    )
    discovery_query = st.text_input(
        "Study context to search",
        value=str(
            saved_module2_plan.get("study_context", {}).get("content_domain")
            or study_metadata.get("content_domain", "")
            if isinstance(saved_module2_plan.get("study_context", {}), dict)
            else study_metadata.get("content_domain", "")
        ),
        placeholder="e.g., climate science education in high-school classrooms",
        key=f"module2_discovery_query_{workflow_key}",
    )
    search_terms = context_search_terms(discovery_query)
    if search_terms:
        try:
            shared_studies = load_published_summaries()
            scored_studies = []
            query_terms = set(search_terms)
            for shared_study in shared_studies:
                shared_terms = set(shared_study.get("context_tags") or [])
                overlap = query_terms & shared_terms
                if overlap:
                    score = len(overlap) / len(query_terms | shared_terms)
                    scored_studies.append((score, shared_study))
            scored_studies.sort(key=lambda result: result[0], reverse=True)
            if not shared_studies:
                st.info(
                    "No study summaries have been published yet. This search will show "
                    "summaries as researchers submit them and maintainers approve them."
                )
            elif not scored_studies:
                st.info("No shared study summaries matched these context terms.")
            else:
                for similarity, shared_study in scored_studies[:5]:
                    with st.expander(
                        f"{shared_study.get('study_title') or 'Shared study'} "
                        f"— context match {similarity:.0%}"
                    ):
                        metadata = shared_study.get("study_metadata") or {}
                        if isinstance(metadata, str):
                            try:
                                metadata = json.loads(metadata)
                            except json.JSONDecodeError:
                                metadata = {}
                        if isinstance(metadata, dict):
                            st.write(f"**Context:** {metadata.get('context_summary') or 'Not specified'}")
                            st.write(f"**Study design:** {metadata.get('time_method') or 'Not specified'}")
                            st.write(f"**Unit of analysis:** {metadata.get('unit_of_analysis') or 'Not specified'}")
                            for field, label in (
                                ("participant_populations", "Population"),
                                ("study_settings", "Setting"),
                                ("content_domain", "Content domain"),
                                ("selected_theories", "Frameworks"),
                            ):
                                values = metadata.get(field, [])
                                st.write(f"**{label}:** {', '.join(values) if isinstance(values, list) else values or 'Not specified'}")
                            shared_variables = metadata.get("variables", [])
                            if isinstance(shared_variables, list) and shared_variables:
                                st.markdown("**Shared variable and measurement metadata**")
                                st.dataframe(
                                    pd.DataFrame(shared_variables),
                                    hide_index=True,
                                    use_container_width=True,
                                )
                        st.caption(
                            "Use these records as design examples, not as evidence that a measure is "
                            "valid for your study. Item text and participant data are not shared."
                        )
        except Exception as discovery_error:
            st.error(f"Could not read the published study summaries: {discovery_error}")
    else:
        st.info("Enter a topic, population, setting, or other context to search shared studies.")

    st.subheader("Step 1 — Define study context and choose frameworks")
    st.markdown("**Describe the study's content and context**")
    st.caption(
        "This step supports a broad range of educational and social-science studies. Add a target "
        "behavior only when it is relevant to your study; it is not assumed to be the outcome."
    )
    saved_study_context = saved_module2_plan.get("study_context", {})
    if not isinstance(saved_study_context, dict):
        saved_study_context = {}
    content_domain = str(
        saved_study_context.get("content_domain")
        or study_metadata.get("content_domain", "")
    ).strip()
    if content_domain:
        st.write(f"**Content domain or topic from Module 1:** {content_domain}")
    target_action = st.text_input(
        "Target behavior / action (optional; if relevant)",
        value=str(saved_study_context.get("target_action", "")),
        placeholder="e.g., choose a lower-carbon travel option; leave blank if not relevant",
        key=f"module2_target_action_{workflow_key}",
    )
    context_description = st.text_input(
        "Specific context",
        value=str(saved_study_context.get("context", "")),
        placeholder="e.g., high-school science classrooms in rural communities",
        help="Describe the study population, setting, or circumstances; it need not describe a behavior.",
        key=f"module2_context_description_{workflow_key}",
    )
    timeframe = st.text_input(
        "Timeframe (optional; if relevant)",
        value=str(saved_study_context.get("timeframe", "")),
        placeholder="e.g., during the next semester",
        key=f"module2_timeframe_{workflow_key}",
    )
    content_tags = st.text_input(
        "Additional content tags (comma-separated)",
        value=str(saved_study_context.get("content_tags", "")),
        placeholder="e.g., sustainability, secondary education",
        key=f"module2_content_tags_{workflow_key}",
    )
    share_study_for_discovery = False
    if selected_study:
        share_study_for_discovery = st.checkbox(
            "Publish a limited study summary for context discovery (public, after maintainer review)",
            value=bool(saved_module2_plan.get("share_for_discovery", False)),
            help=(
                "The summary includes the study title, selected study-design metadata, theory constructs, "
                "and measurement metadata. It never includes participant data or item text. "
                "It is submitted as a public GitHub pull request and listed once a maintainer merges it. "
                "Only share information you are authorized to make public."
            ),
            key=f"module2_share_discovery_{workflow_key}",
        )
    st.markdown("**Select theories, models, or frameworks**")
    st.caption(
        "Choose one or more established frameworks. Each selection brings in its associated factors "
        "and the source citations listed for that framework. Review them as theory-informed starting points."
    )
    theory_choice_options = list(THEORY_MAP) + ["Other (write in)"]
    saved_frameworks = saved_module2_plan.get("selected_theories", [])
    if not isinstance(saved_frameworks, list):
        saved_frameworks = []
    saved_custom_frameworks = [
        framework for framework in saved_frameworks
        if framework not in THEORY_MAP
    ]
    default_theory_choices = [
        framework for framework in saved_frameworks if framework in THEORY_MAP
    ]
    if saved_custom_frameworks:
        default_theory_choices.append("Other (write in)")
    selected_theories = st.multiselect(
        "Theory, model, or framework",
        options=theory_choice_options,
        default=default_theory_choices,
        help="Select all theories, models, and frameworks that inform this study.",
        key=f"module2_theories_{workflow_key}",
    )
    other_theory_names = ""
    if "Other (write in)" in selected_theories:
        other_theory_names = st.text_input(
            "Other theory, model, or framework name(s)",
            value=", ".join(saved_custom_frameworks),
            placeholder="Enter names separated by commas",
            key=f"module2_other_theory_names_{workflow_key}",
        )
        st.text_area(
            "Other framework source and key factors",
            value=str(saved_module2_plan.get(
                "other_theory_sources",
                "",
            )),
            placeholder="Cite a source and list its established constructs or factors. Measurement recommendations will be added in a future update.",
            key=f"module2_other_theory_sources_{workflow_key}",
        )
    other_framework_sources = st.session_state.get(
        f"module2_other_theory_sources_{workflow_key}",
        str(saved_module2_plan.get("other_theory_sources", "")),
    )
    selected_theories = [
        theory for theory in selected_theories if theory != "Other (write in)"
    ] + [
        theory.strip()
        for theory in other_theory_names.split(",")
        if theory.strip()
    ]
    selected_theories = list(dict.fromkeys(selected_theories))
    st.caption(
        "Factors and suggested paths are starting points, not definitive accounts. Verify them "
        "against the cited primary literature and your study context."
    )
    selected_citations = [
        f"{framework}: {citation_for_framework(framework)}"
        for framework in selected_theories
        if framework in THEORY_MAP
    ]
    if "Other (write in)" in st.session_state.get(
        f"module2_theories_{workflow_key}", []
    ):
        custom_citation = str(other_framework_sources).strip()
        if custom_citation:
            selected_citations.append(f"Researcher-entered source: {custom_citation}")
    if selected_citations:
        st.caption("Sources for selected theories, models, and frameworks:")
        st.markdown(
            "\n".join(f"- {citation}" for citation in selected_citations),
            help="References are those cited in the linked theory guide; verify the source details before use.",
        )

    st.subheader("Step 2 — Select Theory-Aligned Variables")
    st.caption(
        "The selected frameworks provide a starting set of theory-aligned variables. Include or "
        "remove each one, then choose any relevant demographic and contextual variables. Construct "
        "identity is stored separately from study content domain and tags."
    )
    if "Theory of Planned Behavior (TPB)" in selected_theories:
        st.info(
            "The TPB example creates three context-personalized prompts per included construct, "
            "with response scale, language, scoring, source, and adaptation metadata. These are "
            "illustrative, app-generated items—not a validated questionnaire. Review and revise "
            "all wording and scoring before use."
        )
    try:
        measure_catalog = load_measure_catalog()
    except (OSError, json.JSONDecodeError, ValueError) as catalog_error:
        measure_catalog = []
        st.error(f"Could not load the research measure catalog: {catalog_error}")
    selected_study_areas = [content_domain] if content_domain.strip() else []
    legacy_subject_areas = study_metadata.get("academic_subject_areas", [])
    if isinstance(legacy_subject_areas, str):
        legacy_subject_areas = [legacy_subject_areas]
    if isinstance(legacy_subject_areas, list):
        selected_study_areas.extend(
            value for value in legacy_subject_areas if isinstance(value, str)
        )
    selected_constructs_by_theory = {}
    for framework in selected_theories:
        if framework not in THEORY_MAP:
            continue
        with st.expander(f"{framework} — theory-derived variables", expanded=True):
            saved_variable_names = {
                str(row.get("Concept_Construct", ""))
                for row in saved_module2_plan.get("variables", [])
                if isinstance(row, dict)
                and row.get("Framework_Source") == framework
            }
            factor_key = (
                f"module2_factor_selection_{workflow_key}_"
                f"{framework.replace(' ', '_')}"
            )
            selected_constructs_by_theory[framework] = st.multiselect(
                "Theory-derived variables to include",
                options=THEORY_MAP[framework],
                default=[
                    factor for factor in THEORY_MAP[framework]
                    if factor in saved_variable_names
                ] if saved_module2_plan else THEORY_MAP[framework],
                help="Select the framework variables to include in your plan and conceptual diagram.",
                key=factor_key,
            )
    demographic_variable_options = [
        "Age",
        "Gender identity",
        "Race and ethnicity",
        "Socioeconomic status",
        "Home language / English learner status",
        "Disability / special education status",
        "Grade or education level",
        "School, district, or institution",
        "Geographic setting",
        "Undergraduate major / field of study",
        "Major or non-major status",
        "First-generation college status",
        "Enrollment / course status",
        "Other demographic or contextual variable",
    ]
    selected_demographic_variables = st.multiselect(
        "Core demographic and contextual variables",
        options=demographic_variable_options,
        default=saved_module2_plan.get("selected_demographic_variables", []),
        help="Choose only variables relevant to this study. No variables are selected by default.",
        key=f"module2_demographics_{workflow_key}",
    )
    other_demographic_variables = ""
    if "Other demographic or contextual variable" in selected_demographic_variables:
        other_demographic_variables = st.text_input(
            "Specify other demographic or contextual variables",
            value=str(saved_module2_plan.get("other_demographic_variables", "")),
            placeholder="Enter variables separated by commas",
            key=f"module2_other_demographics_{workflow_key}",
        )
    variable_fields = [
        "Data_Type",
        "Framework_Source",
        "Framework_ID",
        "Theory_Citation",
        "Concept_Construct",
        "Construct_ID",
        "Variable_ID",
        "Variable_Label",
        "Construct_Domain",
        "Content_Domain",
        "Content_Tags",
        "Behavioral_Target",
        "Target_Action",
        "Context",
        "Timeframe",
        "Operational_Definition",
        "Expected_Role",
        "Question_Item_or_Indicator",
        "Item_Text",
        "Item_Text_2",
        "Item_Text_3",
        "Response_Scale_or_Representation",
        "Response_Scale",
        "Language",
        "Scoring",
        "Measurement_Recommendation",
        "Instrument_Name",
        "Instrument_Citation",
        "Source_Citation",
        "Source_URL",
        "Item_Source_Type",
        "Adaptation_Notes",
        "Validation_Status",
        "Validity_Evidence",
        "Reliability_Evidence",
    ]

    def stable_identifier(value: str) -> str:
        return "_".join(
            part for part in "".join(
                char if char.isalnum() else " " for char in str(value)
            ).casefold().split()
        )

    def framework_short_name(framework: str) -> str:
        known_abbreviations = {
            "Theory of Planned Behavior (TPB)": "TPB",
            "Self-Determination Theory (SDT)": "SDT",
            "Technology Acceptance Model (TAM)": "TAM",
            "Health Belief Model (HBM)": "HBM",
        }
        if framework in known_abbreviations:
            return known_abbreviations[framework]
        words = str(framework).replace("(", " ").replace(")", " ").split()
        return "".join(word[0] for word in words if word).upper() or "FRAMEWORK"

    def prepare_variable_metadata(row: dict) -> dict:
        row = dict(row)
        framework = str(row.get("Framework_Source") or "")
        construct = str(row.get("Concept_Construct") or "")
        content_domain = str(row.get("Content_Domain") or ""        )
        row["Framework_ID"] = row.get("Framework_ID") or stable_identifier(framework)
        row["Construct_ID"] = row.get("Construct_ID") or stable_identifier(construct)
        row["Content_Domain"] = content_domain
        row["Construct_Domain"] = row.get("Construct_Domain") or "Unassigned"
        row["Content_Tags"] = row.get("Content_Tags") or ""
        row["Item_Text"] = row.get("Item_Text") or row.get("Question_Item_or_Indicator") or ""
        row["Item_Text_2"] = row.get("Item_Text_2") or ""
        row["Item_Text_3"] = row.get("Item_Text_3") or ""
        row["Question_Item_or_Indicator"] = (
            row["Item_Text"] or row.get("Question_Item_or_Indicator") or ""
        )
        row["Response_Scale"] = (
            row.get("Response_Scale") or row.get("Response_Scale_or_Representation") or ""
        )
        row["Response_Scale_or_Representation"] = (
            row["Response_Scale"] or row.get("Response_Scale_or_Representation") or ""
        )
        row["Source_Citation"] = row.get("Source_Citation") or row.get("Instrument_Citation") or ""
        row["Source_URL"] = row.get("Source_URL") or ""
        row["Item_Source_Type"] = row.get("Item_Source_Type") or ""
        row["Adaptation_Notes"] = row.get("Adaptation_Notes") or ""
        row["Validation_Status"] = "Not validated by this app; researcher review required"
        if framework and construct and content_domain:
            row["Variable_Label"] = (
                f"{framework_short_name(framework)}_"
                f"{stable_identifier(construct)}_{stable_identifier(content_domain)}"
            )
        elif not row.get("Variable_Label"):
            row["Variable_Label"] = construct
        return row

    def tpb_example_items(construct: str) -> list[str]:
        action = target_action.strip() or "[target behavior]"
        context_phrase = f" in {context_description.strip()}" if context_description.strip() else ""
        timeframe_phrase = f" {timeframe.strip()}" if timeframe.strip() else ""
        behavior_phrase = f"{action}{context_phrase}{timeframe_phrase}"
        behavior_period = timeframe.strip() or "[timeframe]"
        if behavior_period.casefold().startswith(
            ("during ", "within ", "over ", "in ", "for ")
        ):
            behavior_period = behavior_period.split(" ", 1)[1]
        examples = {
            "Attitude Toward the Behavior": [
                f"It would be good for me to {behavior_phrase}.",
                f"It would be beneficial for me to {behavior_phrase}.",
                f"For me, {behavior_phrase} would be worthwhile.",
            ],
            "Subjective Norms": [
                f"People important to me think I should {behavior_phrase}.",
                f"People whose opinions I value would approve of my decision to {behavior_phrase}.",
                f"People like me are expected to {behavior_phrase}.",
            ],
            "Perceived Behavioral Control": [
                f"I am confident that I can {behavior_phrase}.",
                f"Whether I {behavior_phrase} is mostly under my control.",
                f"I have the resources and opportunities needed to {behavior_phrase}.",
            ],
            "Behavioral Intention": [
                f"I intend to {behavior_phrase}.",
                f"I plan to {behavior_phrase}.",
                f"I expect that I will {behavior_phrase}.",
            ],
            "Behavior": [
                f"During {behavior_period}, how often did you {action}{context_phrase}?",
                f"When an opportunity arose during {behavior_period}, how often did you {action}{context_phrase}?",
                f"How consistently did you {behavior_phrase}?",
            ],
        }
        return examples.get(construct, ["", "", ""])

    tpb_agreement_scale = (
        "1=Strongly disagree|2=Disagree|3=Neither agree nor disagree|"
        "4=Agree|5=Strongly agree"
    )
    tpb_behavior_scale = (
        "0=Never|1=Rarely|2=Sometimes|3=Often|4=Always"
    )
    tpb_source_citation = (
        "Ajzen, I. (1991). The theory of planned behavior. "
        "Organizational Behavior and Human Decision Processes, 50(2), 179–211."
    )

    active_items = []
    all_demographic_variables = [
        value for value in selected_demographic_variables
        if value != "Other demographic or contextual variable"
    ]
    all_demographic_variables.extend(
        value.strip()
        for value in other_demographic_variables.split(",")
        if value.strip()
    )
    catalog_suggestions_by_variable = {}
    for framework, constructs in selected_constructs_by_theory.items():
        for construct in constructs:
            suggestions = find_measure_suggestions(
                measure_catalog,
                construct,
                [framework],
                selected_study_areas,
            )
            if suggestions:
                catalog_suggestions_by_variable[(framework, construct)] = suggestions
    for demographic in all_demographic_variables:
        suggestions = find_measure_suggestions(
            measure_catalog,
            demographic,
            [],
            selected_study_areas,
        )
        if suggestions:
            catalog_suggestions_by_variable[("Core demographic / contextual", demographic)] = suggestions

    def measurement_recommendation(variable: str, framework: str) -> str:
        suggestion_count = len(
            catalog_suggestions_by_variable.get((framework, variable), [])
        )
        if suggestion_count:
            return (
                f"{suggestion_count} possible measure(s) are listed in the catalog. "
                "Review the cited sources above."
            )
        return "Placeholder — variable-specific measurement recommendations will be added here."

    with st.expander("Measure catalog suggestions", expanded=bool(catalog_suggestions_by_variable)):
        st.caption(
            f"Catalog source: `{MEASURE_CATALOG_PATH.relative_to(APP_DIR)}`. "
            "Suggestions are matched to included variables, selected frameworks, and saved Module 1 "
            "subject areas when available. Review every source and permissions before adopting a measure."
        )
        if catalog_suggestions_by_variable:
            for (framework, variable), suggestions in catalog_suggestions_by_variable.items():
                st.markdown(f"**{variable}** — {framework}")
                st.dataframe(
                    pd.DataFrame([
                        {
                            "Measure": measure["measure_name"],
                            "Population / context": measure["population_context"],
                            "Response format": measure["response_format"],
                            "Scoring": measure["scoring"],
                            "Validity evidence": measure["validity_evidence"],
                            "Reliability evidence": measure["reliability_evidence"],
                            "Citation": measure["citation"],
                            "DOI / URL": measure["doi_url"] or measure["source_url"],
                            "License / terms": measure["license"],
                        }
                        for measure in suggestions
                    ]),
                    use_container_width=True,
                    hide_index=True,
                )
        elif measure_catalog:
            st.info(
                "The catalog has entries, but none match the currently included variables, "
                "selected frameworks, and study areas."
            )
        else:
            st.info(
                "No measures have been entered yet. Add verified records to "
                "`catalogs/measure_catalog.json`; follow the field guide in `catalogs/README.md`."
            )
    for framework in selected_theories:
        if framework not in THEORY_MAP:
            active_items.append({
                "Data_Type": "",
                "Framework_Source": framework,
                "Framework_ID": stable_identifier(framework),
                "Theory_Citation": other_framework_sources,
                "Concept_Construct": "Add framework factor / variable",
                "Construct_ID": "add_framework_factor_variable",
                "Variable_ID": "",
                "Variable_Label": "",
                "Construct_Domain": "Unassigned",
                "Content_Domain": "",
                "Content_Tags": "",
                "Behavioral_Target": "",
                "Target_Action": "",
                "Context": "",
                "Timeframe": "",
                "Operational_Definition": "",
                "Expected_Role": "",
                "Question_Item_or_Indicator": "",
                "Item_Text": "",
                "Item_Text_2": "",
                "Item_Text_3": "",
                "Response_Scale_or_Representation": "",
                "Response_Scale": "",
                "Language": "",
                "Scoring": "",
                "Measurement_Recommendation": (
                    "Placeholder — add the framework's factors and develop measurement recommendations."
                ),
                "Instrument_Name": "",
                "Instrument_Citation": "",
                "Source_Citation": "",
                "Source_URL": "",
                "Item_Source_Type": "",
                "Adaptation_Notes": "",
                "Validation_Status": "Not validated by this app; researcher review required",
                "Validity_Evidence": "",
                "Reliability_Evidence": "",
            })
    for framework, constructs in selected_constructs_by_theory.items():
        for construct in constructs:
            variable_id = "VAR_" + "_".join(
                part for part in "".join(
                    char if char.isalnum() else " " for char in construct
                ).upper().split()
            )
            active_items.append({
                "Data_Type": "",
                "Framework_Source": framework,
                "Framework_ID": stable_identifier(framework),
                "Theory_Citation": citation_for_framework(framework),
                "Concept_Construct": construct,
                "Construct_ID": stable_identifier(construct),
                "Variable_ID": variable_id,
                "Variable_Label": construct,
                "Construct_Domain": "Unassigned",
                "Content_Domain": content_domain,
                "Content_Tags": content_tags,
                "Behavioral_Target": target_action,
                "Target_Action": target_action,
                "Context": context_description,
                "Timeframe": timeframe,
                "Operational_Definition": "",
                "Expected_Role": "",
                "Question_Item_or_Indicator": "",
                "Item_Text": "",
                "Item_Text_2": "",
                "Item_Text_3": "",
                "Response_Scale_or_Representation": "",
                "Response_Scale": "",
                "Language": "",
                "Scoring": "",
                "Measurement_Recommendation": measurement_recommendation(
                    construct, framework
                ),
                "Instrument_Name": "",
                "Instrument_Citation": "",
                "Source_Citation": "",
                "Source_URL": "",
                "Item_Source_Type": "",
                "Adaptation_Notes": "",
                "Validation_Status": "Not validated by this app; researcher review required",
                "Validity_Evidence": "",
                "Reliability_Evidence": "",
            })
            old_plan_row = next(
                (
                    row for row in saved_module2_plan.get("variables", [])
                    if isinstance(row, dict)
                    and row.get("Framework_Source") == framework
                    and row.get("Concept_Construct") == construct
                ),
                {},
            )
            active_items[-1].update(
                {field: old_plan_row[field] for field in variable_fields if field in old_plan_row}
            )
            active_items[-1]["Content_Domain"] = (
                active_items[-1].get("Content_Domain") or content_domain
            )
            active_items[-1]["Content_Tags"] = (
                active_items[-1].get("Content_Tags") or content_tags
            )
            active_items[-1]["Behavioral_Target"] = (
                active_items[-1].get("Behavioral_Target") or target_action
            )
            active_items[-1]["Target_Action"] = (
                active_items[-1].get("Target_Action") or target_action
            )
            active_items[-1]["Context"] = (
                active_items[-1].get("Context") or context_description
            )
            active_items[-1]["Timeframe"] = (
                active_items[-1].get("Timeframe") or timeframe
            )
            if framework == "Theory of Planned Behavior (TPB)":
                example_items = tpb_example_items(construct)
                for item_field, example_item in zip(
                    ("Item_Text", "Item_Text_2", "Item_Text_3"),
                    example_items,
                ):
                    if not active_items[-1].get(item_field):
                        active_items[-1][item_field] = example_item
                active_items[-1]["Question_Item_or_Indicator"] = (
                    active_items[-1].get("Item_Text") or example_items[0]
                )
                active_items[-1]["Response_Scale"] = (
                    active_items[-1].get("Response_Scale")
                    or (
                        tpb_behavior_scale
                        if construct == "Behavior"
                        else tpb_agreement_scale
                    )
                )
                active_items[-1]["Response_Scale_or_Representation"] = (
                    active_items[-1]["Response_Scale"]
                )
                active_items[-1]["Language"] = (
                    active_items[-1].get("Language") or "English"
                )
                active_items[-1]["Scoring"] = (
                    active_items[-1].get("Scoring")
                    or (
                        "Report the frequency response for each behavior indicator; "
                        "do not assume the indicators form a validated scale."
                        if construct == "Behavior"
                        else (
                            "Example only: review item content and dimensionality; "
                            "calculate a mean only if justified by study-specific evidence."
                        )
                    )
                )
                active_items[-1]["Instrument_Name"] = (
                    active_items[-1].get("Instrument_Name")
                    or "Generic TPB questionnaire example (not validated)"
                )
                active_items[-1]["Source_Citation"] = (
                    active_items[-1].get("Source_Citation") or tpb_source_citation
                )
                active_items[-1]["Source_URL"] = (
                    active_items[-1].get("Source_URL")
                    or "https://doi.org/10.1016/0749-5978(91)90020-T"
                )
                active_items[-1]["Item_Source_Type"] = (
                    active_items[-1].get("Item_Source_Type")
                    or "App-generated generic example; unvalidated"
                )
                active_items[-1]["Adaptation_Notes"] = (
                    active_items[-1].get("Adaptation_Notes")
                    or "Illustrative wording only. Personalize to the defined behavior and context; "
                    "review comprehension, validity, reliability, and permissions before use."
                )
    for demographic in all_demographic_variables:
        active_items.append({
            "Data_Type": "",
            "Framework_Source": "Core demographic / contextual",
            "Framework_ID": "core_demographic_contextual",
            "Theory_Citation": "",
            "Concept_Construct": "Demographic / contextual",
            "Construct_ID": "core_demographic_contextual",
            "Variable_ID": f"DEM_{demographic.upper().replace(' ', '_').replace('/', '_')}",
            "Variable_Label": demographic,
            "Construct_Domain": "Demographic / contextual",
            "Content_Domain": "",
            "Content_Tags": "",
            "Behavioral_Target": "",
            "Target_Action": "",
            "Context": "",
            "Timeframe": "",
            "Operational_Definition": "",
            "Expected_Role": "Context / covariate",
            "Question_Item_or_Indicator": "",
            "Item_Text": "",
            "Response_Scale_or_Representation": "",
            "Response_Scale": "",
            "Language": "",
            "Scoring": "",
            "Measurement_Recommendation": measurement_recommendation(
                demographic, "Core demographic / contextual"
            ),
            "Instrument_Name": "",
            "Instrument_Citation": "",
            "Source_Citation": "",
            "Source_URL": "",
            "Item_Source_Type": "",
            "Adaptation_Notes": "",
            "Validation_Status": "Not validated by this app; researcher review required",
            "Validity_Evidence": "",
            "Reliability_Evidence": "",
        })

    conceptual_relationship_fields = [
        "From_Variable_or_Construct",
        "Relationship_or_Path",
        "To_Variable_or_Construct",
        "Expected_Direction_or_Form",
        "Applicable_Data_Type",
        "Theory_Source",
        "Theory_Citation_or_Evidence",
        "Rationale_or_Hypothesis",
    ]
    if active_items:
        st.markdown("**Included theory-derived, demographic, and contextual variables**")
        active_items = [prepare_variable_metadata(item) for item in active_items]
        active_edit_fields = [
            "Framework_Source",
            "Concept_Construct",
            "Variable_ID",
            "Variable_Label",
            "Content_Domain",
            "Content_Tags",
            "Behavioral_Target",
            "Target_Action",
            "Context",
            "Timeframe",
            "Operational_Definition",
            "Item_Text",
            "Item_Text_2",
            "Item_Text_3",
            "Response_Scale",
            "Language",
            "Scoring",
            "Instrument_Name",
            "Source_Citation",
            "Source_URL",
            "Item_Source_Type",
            "Adaptation_Notes",
            "Validation_Status",
            "Validity_Evidence",
            "Reliability_Evidence",
        ]
        active_edit_df = st.data_editor(
            pd.DataFrame(active_items, columns=variable_fields)[active_edit_fields],
            key=f"module2_construct_metadata_{workflow_key}",
            use_container_width=True,
            hide_index=True,
            disabled=[
                "Framework_Source",
                "Concept_Construct",
                "Variable_ID",
                "Variable_Label",
                "Validation_Status",
            ],
            column_config={
                "Content_Domain": st.column_config.TextColumn(
                    help="Study content domain, such as climate science; it does not change construct identity."
                ),
                "Item_Text": st.column_config.TextColumn(
                    "Item 1",
                    help="Researcher-selected or researcher-written item/indicator. The app does not validate it."
                ),
                "Item_Text_2": st.column_config.TextColumn("Item 2"),
                "Item_Text_3": st.column_config.TextColumn("Item 3"),
                "Source_Citation": st.column_config.TextColumn(
                    help="Citation or persistent identifier for the source measure/item."
                ),
            },
        )
        active_items = [
            prepare_variable_metadata(
                {**item, **active_edit_df.iloc[index].to_dict()}
            )
            for index, item in enumerate(active_items)
        ]
        st.caption(
            "Items and adaptations are researcher-reported; this app does not establish that "
            "they are validated, reliable, suitable, or permitted for reuse."
        )

    st.subheader("Step 3 — Add or Import Custom Variables")
    st.warning(
        "Use one row per variable. Record construct/framework identity separately from content "
        "domain, and document item source, language, scale, scoring, and adaptations where known. "
        "The sample row is removed automatically. User-written or adapted items are not validated by this app."
    )
    
    custom_template_df = pd.DataFrame(columns=variable_fields)
    custom_template_df.loc[0] = {
        "Data_Type": "Survey responses",
        "Framework_Source": "Framework name",
        "Framework_ID": "stable-framework-id",
        "Theory_Citation": "Author, year, DOI/URL",
        "Concept_Construct": "Sample construct",
        "Construct_ID": "sample-construct",
        "Variable_ID": "VAR_SAMPLE_ID",
        "Variable_Label": "Sample variable label",
        "Construct_Domain": "Cognitive (knowledge, beliefs, thinking)",
        "Content_Domain": "Climate science",
        "Content_Tags": "climate; science",
        "Behavioral_Target": "Climate-friendly behavior",
        "Target_Action": "Choose a lower-carbon travel option",
        "Context": "At school",
        "Timeframe": "Next month",
        "Operational_Definition": "Define how the construct is represented in the study.",
        "Expected_Role": "Predictor / outcome / mediator / moderator / context / covariate",
        "Question_Item_or_Indicator": "Example item or observable indicator",
        "Item_Text": "Example item or observable indicator",
        "Item_Text_2": "",
        "Item_Text_3": "",
        "Response_Scale_or_Representation": "1=Option A | 2=Option B | 3=Option C",
        "Response_Scale": "1=Option A | 2=Option B | 3=Option C",
        "Language": "English",
        "Scoring": "Describe scoring and any reverse coding",
        "Measurement_Recommendation": "Researcher review required",
        "Instrument_Name": "Instrument or measure name",
        "Instrument_Citation": "Author, year, source, DOI/URL",
        "Source_Citation": "Author, year, source, DOI/URL",
        "Source_URL": "https://example.org/source",
        "Item_Source_Type": "Existing / adapted / researcher-written",
        "Adaptation_Notes": "Describe changes from the source item",
        "Validation_Status": "Not validated by this app; researcher review required",
        "Validity_Evidence": "Validity type, population, estimate, source",
        "Reliability_Evidence": "Reliability statistic, population, estimate, source",
    }
    template_csv_bytes = custom_template_df.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="Download Custom Variable Template (CSV)",
        data=template_csv_bytes,
        file_name="custom_variables_schema_template.csv",
        mime="text/csv"
    )
    
    uploaded_custom_vars = st.file_uploader("Upload completed Custom Variables (CSV)", type=["csv"])
    
    uploaded_items = []
    uploaded_frameworks = []
    raw_csv_text = ""
    saved_custom_variables = saved_module2_plan.get("custom_variables", [])
    if isinstance(saved_custom_variables, list):
        uploaded_items = [
            row for row in saved_custom_variables if isinstance(row, dict)
        ]
        uploaded_frameworks = list(dict.fromkeys(
            str(row.get("Framework_Source", "")).strip()
            for row in uploaded_items
            if str(row.get("Framework_Source", "")).strip()
        ))
    if uploaded_custom_vars is not None:
        try:
            raw_csv_text = uploaded_custom_vars.getvalue().decode("utf-8-sig", errors="replace")
            uploaded_df = pd.read_csv(io.StringIO(raw_csv_text))
            required_fields = [
                "Variable_ID", "Concept_Construct", "Variable_Label",
                "Framework_Source",
            ]
            
            if all(field in uploaded_df.columns for field in required_fields):
                initial_count = len(uploaded_df)
                uploaded_df = uploaded_df[uploaded_df["Variable_ID"] != "VAR_SAMPLE_ID"]
                filtered_count = len(uploaded_df)
                if "Question_Item_Text" in uploaded_df.columns and "Question_Item_or_Indicator" not in uploaded_df.columns:
                    uploaded_df["Question_Item_or_Indicator"] = uploaded_df["Question_Item_Text"]
                if "Response_Scale_Options" in uploaded_df.columns and "Response_Scale_or_Representation" not in uploaded_df.columns:
                    uploaded_df["Response_Scale_or_Representation"] = uploaded_df["Response_Scale_Options"]
                if "Item_Text" not in uploaded_df.columns and "Question_Item_or_Indicator" in uploaded_df.columns:
                    uploaded_df["Item_Text"] = uploaded_df["Question_Item_or_Indicator"]
                if "Response_Scale" not in uploaded_df.columns and "Response_Scale_or_Representation" in uploaded_df.columns:
                    uploaded_df["Response_Scale"] = uploaded_df["Response_Scale_or_Representation"]
                if "Source_Citation" not in uploaded_df.columns and "Instrument_Citation" in uploaded_df.columns:
                    uploaded_df["Source_Citation"] = uploaded_df["Instrument_Citation"]
                for field in variable_fields:
                    if field not in uploaded_df.columns:
                        uploaded_df[field] = "Unassigned" if field == "Construct_Domain" else ""
                uploaded_df = uploaded_df[variable_fields].fillna("")
                uploaded_items = [
                    prepare_variable_metadata(row)
                    for row in uploaded_df.to_dict(orient="records")
                ]
                uploaded_df = pd.DataFrame(uploaded_items).reindex(columns=variable_fields)
                uploaded_frameworks = list(dict.fromkeys(
                    str(value).strip()
                    for value in uploaded_df["Framework_Source"].dropna()
                    if str(value).strip()
                ))
                
                if filtered_count < initial_count:
                    st.success(f"Imported {filtered_count} custom variable definitions. The sample row was removed.")
                else:
                    st.success(f"Imported {filtered_count} custom variable definitions.")
                
                st.dataframe(uploaded_df, use_container_width=True, hide_index=True)
            else:
                st.error("Required columns are missing. Use the downloaded custom variable template as a guide.")
        except Exception as e:
            st.error(f"Error parsing custom variable spreadsheet file: {e}")

    final_instrument_list = active_items + uploaded_items + st.session_state.session_instruments

    final_instrument_list = [
        prepare_variable_metadata(row) for row in final_instrument_list
    ]
    df_manifest = pd.DataFrame(final_instrument_list).reindex(columns=variable_fields)
    st.session_state["module2_variable_manifest"] = df_manifest.to_dict(orient="records")
    st.subheader("Step 4 — Build the Conceptual Framework")
    st.caption(
        "The diagram includes every included theory-derived variable, demographic/context variable, "
        "and custom variable. Its IEO-inspired layout places demographic/context inputs on the left, "
        "intermediate variables in the center, and outcomes on the far right. Drag boxes to move "
        "them; click an arrow to select it and use the controls to edit, reverse, or delete it."
    )
    if final_instrument_list:
        theory_path_templates = {
            "Theory of Planned Behavior (TPB)": [
                ("Attitude Toward the Behavior", "Behavioral Intention", "Supports intention"),
                ("Subjective Norms", "Behavioral Intention", "Supports intention"),
                ("Perceived Behavioral Control", "Behavioral Intention", "Supports intention"),
                ("Behavioral Intention", "Behavior", "Predicts behavior"),
                ("Perceived Behavioral Control", "Behavior", "May directly predict behavior"),
            ],
            "Self-Determination Theory (SDT)": [
                ("Autonomy", "Intrinsic Motivation", "Supports motivation"),
                ("Competence", "Intrinsic Motivation", "Supports motivation"),
                ("Relatedness", "Intrinsic Motivation", "Supports motivation"),
            ],
            "Technology Acceptance Model (TAM)": [
                ("Perceived Ease of Use (PEOU)", "Perceived Usefulness (PU)", "Influences usefulness"),
                ("Perceived Ease of Use (PEOU)", "Behavioral Intention to Use", "Influences intention"),
                ("Perceived Usefulness (PU)", "Behavioral Intention to Use", "Influences intention"),
                ("Behavioral Intention to Use", "Actual System Use", "Predicts system use"),
            ],
            "Health Belief Model (HBM)": [
                ("Perceived Susceptibility", "Perceived Threat", "Contributes to perceived threat"),
                ("Perceived Severity", "Perceived Threat", "Contributes to perceived threat"),
                ("Perceived Threat", "Preventive Behavior", "May motivate action"),
                ("Perceived Benefits", "Preventive Behavior", "May support action"),
                ("Perceived Barriers", "Preventive Behavior", "May inhibit action"),
                ("Cues to Action", "Preventive Behavior", "May prompt action"),
                ("Self-Efficacy", "Preventive Behavior", "May support action"),
            ],
            "Self-Efficacy Theory": [
                ("Mastery Experiences", "Self-Efficacy", "May strengthen self-efficacy"),
                ("Vicarious Experiences", "Self-Efficacy", "May shape self-efficacy"),
                ("Verbal Persuasion", "Self-Efficacy", "May shape self-efficacy"),
                ("Emotional / Physiological Arousal", "Self-Efficacy", "May shape self-efficacy"),
            ],
            "Control Theory": [
                ("Goal / Reference State", "Comparator / Discrepancy", "Defines comparison standard"),
                ("Input / Perceived Current State", "Comparator / Discrepancy", "Provides current-state input"),
                ("Comparator / Discrepancy", "Output / Behavior Adjustment", "Guides adjustment"),
                ("Output / Behavior Adjustment", "Environmental Impact", "Changes current conditions"),
                ("Environmental Impact", "Input / Perceived Current State", "Provides feedback"),
                ("Disturbances / Obstacles", "Input / Perceived Current State", "Affects current state"),
            ],
            "Social Cognitive Theory (SCT)": [
                ("Personal Factors", "Behavioral Factors", "Reciprocal influence"),
                ("Environmental Factors", "Behavioral Factors", "Reciprocal influence"),
                ("Behavioral Factors", "Personal Factors", "Reciprocal influence"),
                ("Observational Learning", "Behavioral Factors", "Informs behavior"),
                ("Outcome Expectations", "Behavioral Factors", "Informs behavior"),
                ("Self-Efficacy", "Behavioral Factors", "Informs behavior"),
            ],
            "COM-B Model": [
                ("Psychological Capability", "Behavior", "Contributes to behavior"),
                ("Physical Capability", "Behavior", "Contributes to behavior"),
                ("Physical Opportunity", "Behavior", "Contributes to behavior"),
                ("Social Opportunity", "Behavior", "Contributes to behavior"),
                ("Reflective Motivation", "Behavior", "Contributes to behavior"),
                ("Automatic Motivation", "Behavior", "Contributes to behavior"),
            ],
        }
        model_records = df_manifest.fillna("").astype(str).to_dict(orient="records")
        model_nodes_by_id = {}
        model_node_ids_by_construct = {}
        node_occurrence_counts = {}

        def flow_id_segment(value: str) -> str:
            return "".join(char.lower() if char.isalnum() else "_" for char in value).strip("_")

        for index, row in enumerate(model_records):
            variable_label = (row.get("Variable_Label") or row.get("Concept_Construct") or "").strip()
            if not variable_label:
                continue
            data_type = row.get("Data_Type", "").strip()
            framework = row.get("Framework_Source", "").strip()
            construct = row.get("Concept_Construct", "").strip()
            variable_id = row.get("Variable_ID", "").strip()
            identity = f"{data_type}|{framework}|{variable_id}|{variable_label}"
            occurrence = node_occurrence_counts.get(identity, 0)
            node_occurrence_counts[identity] = occurrence + 1
            node_id = f"variable_{uuid.uuid5(uuid.NAMESPACE_URL, identity + '|' + str(occurrence)).hex[:16]}"
            model_nodes_by_id[node_id] = {
                "label": variable_label,
                "data_type": data_type,
                "framework": framework,
                "construct": construct,
                "expected_role": row.get("Expected_Role", ""),
                "variable_id": variable_id,
                "position": (0, 0),
            }
            model_node_ids_by_construct.setdefault((data_type, framework, construct), []).append(node_id)

        suggested_edges = {}
        for framework in selected_theories:
            if framework not in THEORY_MAP:
                continue
            for source_construct, target_construct, relationship_label in theory_path_templates.get(framework, []):
                source_ids = model_node_ids_by_construct.get(("", framework, source_construct), [])
                target_ids = model_node_ids_by_construct.get(("", framework, target_construct), [])
                for source_id in source_ids:
                    for target_id in target_ids:
                        edge_id = (
                            f"theory_{flow_id_segment(framework)}_"
                            f"{source_id}_{target_id}"
                        )
                        suggested_edges[edge_id] = {
                            "source": source_id,
                            "target": target_id,
                            "framework": framework,
                            "label": relationship_label,
                            "direction": "Theory-informed suggested relationship; verify direction and study context",
                        }

        outcome_constructs = {
            "Behavior",
            "Actual System Use",
            "Preventive Behavior",
            "Intrinsic Motivation",
            "Output / Behavior Adjustment",
        }
        outcomes = {
            node_id
            for node_id, details in model_nodes_by_id.items()
            if details["construct"] in outcome_constructs
            or "outcome" in details["expected_role"].lower()
        }
        incoming_sources = {}
        for details in suggested_edges.values():
            incoming_sources.setdefault(details["target"], []).append(details["source"])
        node_layers = {node_id: None for node_id in model_nodes_by_id}
        for node_id in outcomes:
            node_layers[node_id] = 0
        queue = list(outcomes)
        while queue:
            target_id = queue.pop(0)
            for source_id in incoming_sources.get(target_id, []):
                if node_layers[source_id] is None:
                    node_layers[source_id] = node_layers[target_id] + 1
                    queue.append(source_id)
        for index, (node_id, details) in enumerate(model_nodes_by_id.items()):
            role = details["expected_role"].lower()
            if details["construct"] == "Demographic / contextual" or any(
                term in role for term in ("input", "context", "covariate")
            ):
                x_position = 0
            elif node_id in outcomes:
                x_position = 1050
            else:
                distance_from_outcome = node_layers[node_id]
                x_position = (
                    max(250, 1050 - distance_from_outcome * 300)
                    if distance_from_outcome is not None else 550
                )
            details["position"] = (x_position, index * 120)

        flow_identity = selected_study.get("id") if selected_study else "draft"
        flow_state_key = f"module2_conceptual_flow_v2_{flow_identity}"
        seeded_edges_key = f"{flow_state_key}_seeded"
        edge_sources_key = f"{flow_state_key}_edge_sources"
        edge_directions_key = f"{flow_state_key}_edge_directions"
        edge_rationales_key = f"{flow_state_key}_edge_rationales"
        saved_diagram = saved_module2_plan.get("diagram", {})
        if not isinstance(saved_diagram, dict):
            saved_diagram = {}
        saved_positions = {
            node.get("id"): node.get("position")
            for node in saved_diagram.get("nodes", [])
            if isinstance(node, dict)
            and isinstance(node.get("id"), str)
            and isinstance(node.get("position"), (list, tuple))
            and len(node["position"]) == 2
        }
        node_objects = [
            StreamlitFlowNode(
                id=node_id,
                pos=tuple(saved_positions.get(node_id, details["position"])),
                data={
                    "content": (
                        f"**{details['label']}**  \n"
                        f"{details['construct']}"
                        + (f"  \n*{details['data_type']}*" if details["data_type"] else "")
                    ),
                },
                node_type="default",
                source_position="right",
                target_position="left",
                draggable=True,
                connectable=True,
                style={"width": 230, "padding": 10, "borderRadius": 8},
            )
            for node_id, details in model_nodes_by_id.items()
        ]
        seeded_ids = st.session_state.setdefault(seeded_edges_key, set())
        edge_sources = st.session_state.setdefault(edge_sources_key, {})
        edge_directions = st.session_state.setdefault(edge_directions_key, {})
        edge_rationales = st.session_state.setdefault(edge_rationales_key, {})
        if flow_state_key not in st.session_state:
            saved_edges = saved_diagram.get("edges", [])
            flow_edges = []
            if isinstance(saved_edges, list) and saved_edges:
                for edge in saved_edges:
                    if (
                        not isinstance(edge, dict)
                        or edge.get("source") not in model_nodes_by_id
                        or edge.get("target") not in model_nodes_by_id
                    ):
                        continue
                    edge_id = str(edge.get("id") or f"researcher_{uuid.uuid4().hex[:12]}")
                    flow_edges.append(StreamlitFlowEdge(
                        id=edge_id,
                        source=edge["source"],
                        target=edge["target"],
                        marker_end={"type": "arrowclosed", "width": 24, "height": 24},
                        label=str(edge.get("relationship") or "Researcher-proposed path"),
                        label_show_bg=True,
                        deletable=True,
                        style={"strokeWidth": 4},
                    ))
                    edge_sources[edge_id] = str(edge.get("theory_source", "Researcher-proposed"))
                    edge_directions[edge_id] = str(edge.get("expected_direction", ""))
                    edge_rationales[edge_id] = str(edge.get("rationale_or_hypothesis", ""))
                    if edge_id in suggested_edges:
                        seeded_ids.add(edge_id)
            else:
                flow_edges = [
                    StreamlitFlowEdge(
                        id=edge_id,
                        source=details["source"],
                        target=details["target"],
                        marker_end={"type": "arrowclosed", "width": 24, "height": 24},
                        label=details["label"],
                        label_show_bg=True,
                        deletable=True,
                        style={"strokeWidth": 4},
                    )
                    for edge_id, details in suggested_edges.items()
                ]
                seeded_ids.update(suggested_edges)
                edge_sources.update({
                    edge_id: details["framework"]
                    for edge_id, details in suggested_edges.items()
                })
                edge_directions.update({
                    edge_id: details["direction"]
                    for edge_id, details in suggested_edges.items()
                })
            st.session_state[flow_state_key] = StreamlitFlowState(node_objects, flow_edges)
        else:
            flow_state = st.session_state[flow_state_key]
            existing_nodes = {node.id: node for node in flow_state.nodes}
            synchronized_nodes = []
            for node in node_objects:
                existing = existing_nodes.get(node.id)
                if existing:
                    existing.data = node.data
                    existing.draggable = node.draggable
                    existing.connectable = node.connectable
                    synchronized_nodes.append(existing)
                else:
                    synchronized_nodes.append(node)
            flow_state.nodes = synchronized_nodes
            current_node_ids = set(model_nodes_by_id)
            flow_state.edges = [
                edge for edge in flow_state.edges
                if edge.source in current_node_ids and edge.target in current_node_ids
            ]
            active_suggested_ids = set(suggested_edges)
            removed_suggestions = seeded_ids - active_suggested_ids
            flow_state.edges = [
                edge for edge in flow_state.edges
                if edge.id not in removed_suggestions
            ]
            seeded_ids.intersection_update(active_suggested_ids)
            for edge_id, details in suggested_edges.items():
                if edge_id not in seeded_ids and not any(
                    edge.id == edge_id for edge in flow_state.edges
                ):
                    flow_state.edges.append(StreamlitFlowEdge(
                        id=edge_id,
                        source=details["source"],
                        target=details["target"],
                        marker_end={"type": "arrowclosed", "width": 24, "height": 24},
                        label=details["label"],
                        label_show_bg=True,
                        deletable=True,
                        style={"strokeWidth": 4},
                    ))
                    seeded_ids.add(edge_id)
                    edge_sources[edge_id] = details["framework"]
                    edge_directions[edge_id] = details["direction"]

        st.session_state[flow_state_key] = streamlit_flow(
            f"module2_conceptual_diagram_{flow_identity}",
            st.session_state[flow_state_key],
            layout=ManualLayout(),
            height=560,
            fit_view=True,
            allow_new_edges=True,
            enable_edge_menu=False,
            enable_node_menu=False,
            enable_pane_menu=False,
            get_edge_on_click=True,
            pan_on_drag=False,
            style={
                "backgroundColor": "#eef6ff",
                "backgroundImage": "radial-gradient(#9ab6d8 1px, transparent 1px)",
                "backgroundSize": "20px 20px",
                "border": "1px solid #93a4b8",
                "borderRadius": "8px",
            },
            hide_watermark=True,
        )
        current_flow_state = st.session_state[flow_state_key]
        current_edges = list(current_flow_state.edges)
        if current_edges:
            edge_labels = {
                edge.id: (
                    f"{model_nodes_by_id.get(edge.source, {}).get('label', edge.source)} "
                    f"({model_nodes_by_id.get(edge.source, {}).get('data_type', '')}) → "
                    f"{model_nodes_by_id.get(edge.target, {}).get('label', edge.target)} "
                    f"({model_nodes_by_id.get(edge.target, {}).get('data_type', '')})"
                )
                for edge in current_edges
            }
            selected_edge_id = current_flow_state.selected_id
            if selected_edge_id not in edge_labels:
                selected_edge_id = current_edges[0].id
            edge_selector_key = f"module2_selected_edge_{flow_identity}"
            selection_timestamp_key = f"{flow_state_key}_selection_timestamp"
            if st.session_state.get(selection_timestamp_key) != current_flow_state.timestamp:
                if current_flow_state.selected_id in edge_labels:
                    st.session_state[edge_selector_key] = current_flow_state.selected_id
                st.session_state[selection_timestamp_key] = current_flow_state.timestamp
            chosen_edge_id = st.selectbox(
                "Select a path (click an arrow in the diagram or choose it here)",
                options=list(edge_labels),
                format_func=lambda edge_id: edge_labels[edge_id],
                index=list(edge_labels).index(selected_edge_id),
                key=edge_selector_key,
            )
            chosen_edge = next(edge for edge in current_edges if edge.id == chosen_edge_id)
            pending_reversal_key = f"{flow_state_key}_pending_reversal"
            if st.session_state.get(pending_reversal_key) == chosen_edge_id:
                st.session_state.pop(
                    f"module2_edge_label_{flow_identity}_{chosen_edge_id}", None
                )
                st.session_state.pop(
                    f"module2_edge_rationale_{flow_identity}_{chosen_edge_id}", None
                )
                st.session_state.pop(pending_reversal_key, None)
            relationship_label = st.text_input(
                "Relationship label",
                value=chosen_edge.label or "",
                placeholder="For example: predicts, supports, moderates",
                key=f"module2_edge_label_{flow_identity}_{chosen_edge_id}",
            )
            relationship_rationale = st.text_area(
                "Rationale or hypothesis",
                value=edge_rationales.get(chosen_edge_id, ""),
                placeholder="Explain why this path is expected and cite the relevant theory or evidence.",
                key=f"module2_edge_rationale_{flow_identity}_{chosen_edge_id}",
            )
            save_col, reverse_col, delete_col = st.columns(3)
            with save_col:
                save_relationship = st.button(
                    "Save path label and rationale",
                    key=f"module2_save_edge_{flow_identity}",
                )
            with reverse_col:
                reverse_relationship = st.button(
                    "Reverse selected arrow",
                    key=f"module2_reverse_edge_{flow_identity}",
                )
            with delete_col:
                delete_relationship = st.button(
                    "Delete selected path",
                    key=f"module2_delete_edge_{flow_identity}",
                )
            if save_relationship:
                chosen_edge.label = relationship_label.strip()
                edge_rationales[chosen_edge_id] = relationship_rationale.strip()
            if reverse_relationship:
                chosen_edge.source, chosen_edge.target = chosen_edge.target, chosen_edge.source
                chosen_edge.label = "Researcher-reversed; review relationship label"
                edge_rationales.pop(chosen_edge_id, None)
                edge_directions[chosen_edge_id] = "Direction reversed by researcher; verify and document rationale"
                st.session_state[pending_reversal_key] = chosen_edge_id
                st.rerun()
            if delete_relationship:
                current_flow_state.edges = [
                    edge for edge in current_flow_state.edges if edge.id != chosen_edge_id
                ]
                edge_sources.pop(chosen_edge_id, None)
                edge_directions.pop(chosen_edge_id, None)
                edge_rationales.pop(chosen_edge_id, None)
                st.rerun()
        if current_flow_state.nodes:
            with st.expander("Add a path without dragging connection handles"):
                node_options = list(model_nodes_by_id)
                node_labels = {
                    node_id: (
                        f"{model_nodes_by_id[node_id]['label']} "
                        f"({model_nodes_by_id[node_id]['data_type']})"
                    )
                    for node_id in node_options
                }
                add_source = st.selectbox(
                    "From variable",
                    options=node_options,
                    format_func=lambda node_id: node_labels[node_id],
                    key=f"module2_add_edge_source_{flow_identity}",
                )
                add_target = st.selectbox(
                    "To variable",
                    options=node_options,
                    format_func=lambda node_id: node_labels[node_id],
                    index=1 if len(node_options) > 1 else 0,
                    key=f"module2_add_edge_target_{flow_identity}",
                )
                if st.button("Add relationship arrow", key=f"module2_add_edge_{flow_identity}"):
                    if add_source == add_target:
                        st.error("Choose two different variables for a relationship.")
                    else:
                        edge_id = f"researcher_{uuid.uuid4().hex[:12]}"
                        current_flow_state.edges.append(StreamlitFlowEdge(
                            id=edge_id,
                            source=add_source,
                            target=add_target,
                            marker_end={"type": "arrowclosed", "width": 24, "height": 24},
                            label="Researcher-proposed",
                            label_show_bg=True,
                            deletable=True,
                            style={"strokeWidth": 4},
                        ))
                        edge_sources[edge_id] = "Researcher-proposed"
                        edge_directions[edge_id] = "Researcher-proposed; specify expected direction and conditions"
                        st.rerun()

        relationship_rows = []
        for edge in current_edges:
            source_details = model_nodes_by_id.get(edge.source, {})
            target_details = model_nodes_by_id.get(edge.target, {})
            relationship_rows.append({
                "From_Variable_or_Construct": source_details.get("label", edge.source),
                "Relationship_or_Path": edge.label or "Researcher-proposed path",
                "To_Variable_or_Construct": target_details.get("label", edge.target),
                "Expected_Direction_or_Form": edge_directions.get(
                    edge.id,
                    "Researcher-proposed; specify expected direction and conditions",
                ),
                "Applicable_Data_Type": source_details.get("data_type", ""),
                "Theory_Source": edge_sources.get(edge.id, "Researcher-proposed"),
                "Theory_Citation_or_Evidence": (
                    other_framework_sources
                    if edge_sources.get(edge.id) == "Researcher-proposed"
                    else citation_for_framework(edge_sources.get(edge.id, ""))
                ),
                "Rationale_or_Hypothesis": edge_rationales.get(edge.id, ""),
            })
        conceptual_relationships = pd.DataFrame(
            relationship_rows,
            columns=conceptual_relationship_fields,
        )
        if not current_edges:
            st.info(
                "No paths are shown yet. Select theory constructs to load suggested paths, "
                "or connect variables in the diagram to propose your own relationships."
            )
        else:
            st.dataframe(conceptual_relationships, use_container_width=True, hide_index=True)
        conceptual_framework_description = st.text_area(
            "Conceptual framework narrative",
            value=str(saved_module2_plan.get("narrative", "")),
            placeholder=(
                "Explain how the selected theory constructs become this study's variables, "
                "why the proposed paths are expected, and how the data types will evidence those relationships."
            ),
            key=f"module2_conceptual_narrative_{flow_identity}",
        )
        st.subheader("Step 5 — Review Variables and Measurement Metadata")
        st.caption(
            "Review the complete variable set represented in the diagram, including theory-derived, "
            "demographic/contextual, and custom variables. Review construct identity, study context, "
            "item and scale metadata, and all sources before using the exported draft."
        )
        st.dataframe(df_manifest, use_container_width=True, hide_index=True)
        diagram_nodes = [
            {
                "id": node.id,
                "variable_label": model_nodes_by_id.get(node.id, {}).get("label", ""),
                "data_type": model_nodes_by_id.get(node.id, {}).get("data_type", ""),
                "theory_construct": model_nodes_by_id.get(node.id, {}).get("construct", ""),
                "position": node.position,
            }
            for node in current_flow_state.nodes
        ]
        diagram_edges = [
            {
                "id": edge.id,
                "source": edge.source,
                "target": edge.target,
                "relationship": edge.label or "Researcher-proposed path",
                "theory_source": edge_sources.get(edge.id, "Researcher-proposed"),
                "expected_direction": edge_directions.get(edge.id, ""),
                "rationale_or_hypothesis": edge_rationales.get(edge.id, ""),
            }
            for edge in current_edges
        ]
        st.markdown("**Save this plan to your project file**")
        plan_to_save = {
            "schema_version": 1,
            "selected_theories": selected_theories,
            "other_theory_sources": str(other_framework_sources or ""),
            "selected_demographic_variables": selected_demographic_variables,
            "other_demographic_variables": other_demographic_variables,
            "study_context": {
                "content_domain": content_domain.strip(),
                "target_action": target_action.strip(),
                "context": context_description.strip(),
                "timeframe": timeframe.strip(),
                "content_tags": content_tags.strip(),
            },
            "share_for_discovery": share_study_for_discovery,
            "variables": df_manifest.fillna("").astype(str).to_dict(orient="records"),
            "custom_variables": (
                pd.DataFrame(uploaded_items)
                .fillna("")
                .astype(str)
                .to_dict(orient="records")
            ),
            "diagram": {
                "nodes": diagram_nodes,
                "edges": diagram_edges,
            },
            "narrative": conceptual_framework_description.strip(),
        }
        if st.button(
            "Save Module 2 plan to project",
            key=f"module2_save_plan_{flow_identity}",
        ):
            project = current_project()
            project["module2_plan"] = plan_to_save
            st.session_state["project"] = project
            st.session_state["module2_saved_notice"] = True
        if st.session_state.get("module2_saved_notice"):
            st.success(
                "Plan saved to your project. Download the project file to keep it — "
                "the app does not store a copy."
            )
            render_project_download(key=f"module2_project_download_{flow_identity}")

        if selected_study:
            study_id = str(selected_study.get("id"))
            summary_path = f"published/study_summaries/{safe_slug(study_id, 'study')}.json"
            already_published = (APP_DIR / summary_path).is_file()
            if share_study_for_discovery:
                public_variable_fields = [
                    "Framework_Source",
                    "Concept_Construct",
                    "Variable_Label",
                    "Content_Domain",
                    "Content_Tags",
                    "Behavioral_Target",
                    "Target_Action",
                    "Context",
                    "Timeframe",
                    "Response_Scale",
                    "Language",
                    "Scoring",
                    "Source_Citation",
                    "Source_URL",
                    "Instrument_Name",
                    "Validation_Status",
                ]
                shared_variables = []
                for variable in df_manifest.fillna("").astype(str).to_dict(orient="records"):
                    shared_variables.append({
                        field: variable.get(field, "")
                        for field in public_variable_fields
                        if variable.get(field, "")
                    })
                context_summary = "; ".join(
                    f"{label}: {value}"
                    for label, value in (
                        ("Domain", content_domain),
                        ("Target behavior", target_action),
                        ("Context", context_description),
                        ("Timeframe", timeframe),
                        ("Tags", content_tags),
                    )
                    if value.strip()
                )
                participant_populations = study_metadata.get("participant_populations", [])
                study_settings = study_metadata.get("study_settings", [])
                published_metadata = {
                    "context_summary": context_summary,
                    "time_method": study_metadata.get("time_method", ""),
                    "unit_of_analysis": study_metadata.get("unit_of_analysis", ""),
                    "participant_populations": participant_populations,
                    "study_settings": study_settings,
                    "content_domain": content_domain.strip(),
                    "selected_theories": selected_theories,
                    "variables": shared_variables,
                }
                search_tags = context_search_terms(
                    " ".join(
                        [
                            context_summary,
                            " ".join(selected_theories),
                            " ".join(selected_study_areas),
                            " ".join(participant_populations if isinstance(participant_populations, list) else []),
                            " ".join(study_settings if isinstance(study_settings, list) else []),
                        ]
                    )
                )
                summary_record = {
                    "schema_version": 1,
                    "study_id": study_id,
                    "study_title": selected_study.get("study_title") or "Shared study",
                    "context_tags": search_tags,
                    "study_metadata": published_metadata,
                    "published_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
                st.markdown("**Publish a limited study summary**")
                with st.expander("Preview exactly what will be published"):
                    st.json(summary_record)
                summary_consent = st.checkbox(
                    "I confirm this summary contains no participant data or confidential "
                    "information and I am authorized to make it public.",
                    key=f"module2_summary_consent_{flow_identity}",
                )
                if st.button(
                    "Update published summary" if already_published else "Submit summary for public listing",
                    key=f"module2_submit_summary_{flow_identity}",
                    disabled=publish_disabled or not summary_consent,
                    help=publish_hint,
                ):
                    with st.spinner("Opening a pull request for maintainer review..."):
                        result_message = open_review_pull_request(
                            suggestion_type="Study Summary",
                            title_summary=str(summary_record["study_title"])[:120],
                            files={
                                summary_path: json.dumps(summary_record, ensure_ascii=False, indent=2)
                            },
                            description="Adds or updates a limited study summary for context discovery.",
                        )
                    (st.error if "❌" in result_message else st.success)(result_message)
            elif already_published:
                st.info("A summary of this study is currently published for context discovery.")
                if st.button(
                    "Request removal of the published summary",
                    key=f"module2_remove_summary_{flow_identity}",
                    disabled=publish_disabled,
                    help=publish_hint,
                ):
                    with st.spinner("Opening a removal pull request..."):
                        result_message = open_review_pull_request(
                            suggestion_type="Remove Study Summary",
                            title_summary=str(selected_study.get("study_title") or study_id)[:120],
                            delete_paths=[summary_path],
                            description=(
                                "Removes this study summary from the listing. Earlier versions "
                                "remain in git history."
                            ),
                        )
                    (st.error if "❌" in result_message else st.success)(result_message)
        diagram_json = json.dumps({
            "schema_version": 1,
            "nodes": diagram_nodes,
            "edges": diagram_edges,
            "narrative": conceptual_framework_description.strip(),
        }, ensure_ascii=False, indent=2).encode("utf-8")
        conceptual_csv = conceptual_relationships.to_csv(index=False).encode("utf-8")
        # --- MODULE 2 THEORY AND VARIABLE PROPOSAL ---
        st.markdown("---")
        st.markdown("### Suggest a Theory or Variable for the App")
        st.caption(
            "Submit the reviewed theory/variable map and conceptual relationships as a pull request "
            "for maintainer review. Accepted suggestions can be added to the app's catalog."
        )
        st.warning(
            "This proposal will be submitted to the public GitHub repository. Do not include "
            "participant information, private study details, unpublished results, or other sensitive content."
        )
        proposal_frameworks = list(dict.fromkeys(
            str(value).strip()
            for value in df_manifest["Framework_Source"].fillna("")
            if str(value).strip()
            and str(value).strip() not in {"Core demographic / contextual", "Unassigned"}
        ))
        proposal_frameworks = list(dict.fromkeys(proposal_frameworks + uploaded_frameworks))
        default_framework_names = ", ".join(proposal_frameworks)
        proposal_title = st.text_input(
            "Suggestion title",
            value=f"Theory and variable suggestion: {default_framework_names}" if default_framework_names else "",
            max_chars=120,
            key=f"module2_proposal_title_{selected_study.get('id') if selected_study else 'draft'}",
        )
        proposal_rationale = st.text_area(
            "Literature basis and reason for the suggestion",
            placeholder="Summarize the theory's established constructs and explain why this suggestion would help researchers.",
            key=f"module2_proposal_rationale_{selected_study.get('id') if selected_study else 'draft'}",
        )
        public_proposal_consent = st.checkbox(
            "I confirm this proposal contains no confidential or identifying information and may be published in a public GitHub pull request.",
            key=f"module2_public_proposal_consent_{selected_study.get('id') if selected_study else 'draft'}",
        )
        if st.button(
            "Submit Theory and Variable Suggestion for Review",
            key="submit_mod2_pr_btn",
            disabled=publish_disabled or not public_proposal_consent,
            help=publish_hint,
        ):
            if not proposal_title.strip() or not proposal_rationale.strip():
                st.error("Enter a suggestion title and a literature basis before submitting.")
            else:
                proposal = {
                    "schema_version": 1,
                    "proposal_type": "theory_and_variable_catalog_suggestion",
                    "framework_names": proposal_frameworks,
                    "literature_basis_and_rationale": proposal_rationale.strip(),
                    "variables": (
                        df_manifest.fillna("")
                        .astype(str)
                        .to_dict(orient="records")
                    ),
                    "conceptual_relationships": (
                        conceptual_relationships.fillna("")
                        .astype(str)
                        .to_dict(orient="records")
                    ),
                    "conceptual_framework_narrative": conceptual_framework_description.strip(),
                    "conceptual_diagram": {
                        "nodes": diagram_nodes,
                        "edges": diagram_edges,
                    },
                    "submitted_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
                proposal_content = json.dumps(proposal, ensure_ascii=False, indent=2)
                with st.spinner("Creating a GitHub branch and pull request for maintainer review..."):
                    result_message = automate_github_pull_request(
                        suggestion_type="Framework",
                        file_name=f"module2_theory_variable_{uuid.uuid4().hex[:12]}.json",
                        file_content=proposal_content,
                        title_summary=proposal_title.strip(),
                    )
                if "❌" in result_message:
                    st.error(result_message)
                else:
                    st.success(result_message)
            
        st.markdown("---")
        st.subheader("Download Module 2 Matrices")
        download_col1, download_col2, download_col3 = st.columns(3)
        with download_col1:
            st.download_button(
                "Download Conceptual Framework Diagram (JSON)",
                data=diagram_json,
                file_name="conceptual_framework_diagram.json",
                mime="application/json",
                use_container_width=True,
            )
        with download_col2:
            st.download_button(
                "Download Theory and Variable Matrix (CSV)",
                data=df_manifest.to_csv(index=False).encode("utf-8"),
                file_name="theory_variable_data_type_map.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with download_col3:
            st.download_button(
                "Download Conceptual Relationships Matrix (CSV)",
                data=conceptual_csv,
                file_name="conceptual_framework_relationships.csv",
                mime="text/csv",
                use_container_width=True,
            )
        st.subheader("Download Variable Matrices and Draft")
        csv_buffer = io.StringIO()
        df_manifest.to_csv(csv_buffer, index=False)
        st.download_button(
            "Download Variable and Measure Metadata (CSV)",
            data=csv_buffer.getvalue(),
            file_name="educational_study_metadata_sheet.csv",
            mime="text/csv",
            use_container_width=True,
        )

        txt_manifest = "=== VARIABLE AND MEASURE METADATA MANIFEST ===\n"
        txt_manifest += f"Study DOI / Persistent Identifier: {repository_id or 'Not provided'}\n"
        txt_manifest += f"Unit of Analysis: {unit_of_analysis}\n"
        txt_manifest += f"Sampling Procedure: {sampling_method}\n"
        txt_manifest += f"Sampling Details: {sampling_procedure or 'Not provided'}\n"
        txt_manifest += "=" * 60 + "\n\n"
        for _, row in df_manifest.iterrows():
            txt_manifest += f"DDI Variable ID:  {row['Variable_ID']}\n"
            txt_manifest += f"Framework ID:     {row.get('Framework_ID', '')}\n"
            txt_manifest += f"Concept/Construct: {row['Concept_Construct']}\n"
            txt_manifest += f"Construct ID:     {row.get('Construct_ID', '')}\n"
            txt_manifest += f"Variable Label:    {row['Variable_Label']}\n"
            txt_manifest += f"Operational Definition: {row.get('Operational_Definition', '')}\n"
            txt_manifest += f"Content Domain:    {row.get('Content_Domain', '')}\n"
            txt_manifest += f"Content Tags:      {row.get('Content_Tags', '')}\n"
            txt_manifest += f"Behavioral Target: {row.get('Behavioral_Target', '')}\n"
            txt_manifest += f"Target Action:     {row.get('Target_Action', '')}\n"
            txt_manifest += f"Context:           {row.get('Context', '')}\n"
            txt_manifest += f"Timeframe:         {row.get('Timeframe', '')}\n"
            txt_manifest += f"Data Type:         {row.get('Data_Type', '')}\n"
            txt_manifest += f"Theory Citation:   {row.get('Theory_Citation', '')}\n"
            txt_manifest += f"Item / Indicator:  {row.get('Item_Text') or row.get('Question_Item_or_Indicator', '')}\n"
            txt_manifest += f"Item 2:            {row.get('Item_Text_2', '')}\n"
            txt_manifest += f"Item 3:            {row.get('Item_Text_3', '')}\n"
            txt_manifest += f"Response Scale:    {row.get('Response_Scale') or row.get('Response_Scale_or_Representation', '')}\n"
            txt_manifest += f"Language:          {row.get('Language', '')}\n"
            txt_manifest += f"Scoring:           {row.get('Scoring', '')}\n"
            txt_manifest += f"Framework Source:  {row['Framework_Source']}\n"
            txt_manifest += f"Instrument:        {row.get('Instrument_Name', '')}\n"
            txt_manifest += f"Source Citation:   {row.get('Source_Citation') or row.get('Instrument_Citation', '')}\n"
            txt_manifest += f"Source URL:        {row.get('Source_URL', '')}\n"
            txt_manifest += f"Item Source Type:  {row.get('Item_Source_Type', '')}\n"
            txt_manifest += f"Adaptation Notes:  {row.get('Adaptation_Notes', '')}\n"
            txt_manifest += f"Validation Status: {row.get('Validation_Status', '')}\n"
            txt_manifest += f"Validity Evidence: {row.get('Validity_Evidence', '')}\n"
            txt_manifest += f"Reliability Evidence: {row.get('Reliability_Evidence', '')}\n"
            txt_manifest += "-" * 60 + "\n\n"
        st.download_button(
            "Download Technical Variable Manifest (TXT)",
            data=txt_manifest,
            file_name="technical_study_metadata_manifest.txt",
            mime="text/plain",
            use_container_width=True,
        )

        clean_survey = "=== DRAFT SURVEY FORM ===\n"
        if repository_id:
            clean_survey += f"Study DOI / Persistent Identifier: {repository_id}\n"
        clean_survey += f"Unit of Analysis: {unit_of_analysis}\n"
        clean_survey += f"Sampling Procedure: {sampling_method}\n"
        clean_survey += (
            "Instructions: Please read each question carefully and select or enter "
            "the option that best describes your response.\n"
        )
        clean_survey += (
            "Measurement notice: Items and adaptations are researcher-reported and are not "
            "validated by this app. Review item suitability, permissions, language, and scoring "
            "before administration.\n"
        )
        clean_survey += "=" * 60 + "\n\n"
        question_number = 0
        for _, row in df_manifest.iterrows():
            item_texts = [
                str(row.get(field) or "").strip()
                for field in ("Item_Text", "Item_Text_2", "Item_Text_3")
                if str(row.get(field) or "").strip()
            ]
            if not item_texts:
                legacy_item = str(row.get("Question_Item_or_Indicator") or "").strip()
                if legacy_item:
                    item_texts = [legacy_item]
            for item_text in item_texts:
                question_number += 1
                clean_survey += f"Q{question_number}. {item_text}\n"
                if row.get("Variable_Label"):
                    clean_survey += f"   Variable: {row.get('Variable_Label')}\n"
                if row.get("Language"):
                    clean_survey += f"   Language: {row.get('Language')}\n"
                options = str(row.get("Response_Scale") or row.get("Response_Scale_or_Representation", ""))
                if "|" in options:
                    for option in options.split("|"):
                        clean_survey += f"   [ ] {option.strip()}\n"
                elif "Continuous" in options:
                    clean_survey += "   [_______________________________________]\n"
                else:
                    clean_survey += f"   Options: {options}\n"
                if row.get("Scoring"):
                    clean_survey += f"   Scoring (researcher-defined): {row.get('Scoring')}\n"
                clean_survey += "\n"
        st.download_button(
            "Download Draft Survey Form (TXT)",
            data=clean_survey,
            file_name="clean_participant_survey_form.txt",
            mime="text/plain",
            use_container_width=True,
        )
    else:
        st.subheader("Step 5 — Review Variables and Measurement Metadata")
        st.info("No variables were selected or added. Select theory variables in Step 2 or add variables in Step 3.")
        st.info("No structural frameworks, demographic indicators, or custom variables selected yet.")
