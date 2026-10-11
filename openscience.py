import streamlit as st
import pandas as pd
import numpy as np
import urllib.parse

st.set_page_config(page_title="Open Educational Metadata Portal", layout="wide")
st.title("🔬 Open Educational Metadata Portal")
st.caption("An Open Source, Community-Driven Engine for Standardized Educational Research and Psychometrics.")

# Configuration for your repository
GITHUB_REPO_URL = "https://github.com"

# -------------------------------------------------------------
# SCHEMA DICTIONARIES: CONFIGURATION & ITEM BANK
# -------------------------------------------------------------
# 1. Framework to variable mapping
import json

# Safely open and unpack the unified database dictionary entries
try:
    with open("schema_config.json", "r") as f:
        registry = json.load(f)
    FRAMEWORK_MAP = registry["frameworks"]
    SUBSCALE_MAP = registry["subscales"]
    ITEM_BANK = registry["item_bank"]
except Exception as e:
    st.error(f"Failed to pull configuration layout mappings: {e}")
    st.stop()

if "proposed_columns" not in st.session_state:
    st.session_state["proposed_columns"] = []

def calculate_cronbach_alpha(df_items):
    num_columns = len(df_items.columns)
    if num_columns in (0, 1):
        return np.nan
    item_vars = df_items.var(ddof=1, axis=0)
    total_var = df_items.sum(axis=1).var(ddof=1)
    if total_var == 0:
        return 0.0
    return (num_columns / (num_columns - 1)) * (1 - (item_vars.sum() / total_var))

# -------------------------------------------------------------
# MAIN LAYOUT CONFIGURATION
# -------------------------------------------------------------
t_meta, t_spec, t_share = st.tabs([
    "🌐 1. Study Profile Metadata", 
    "📋 2. Survey Builder & Schema Templates", 
    "📤 3. Open Science Data Sharing Hub"
])

# -------------------------------------------------------------
# TAB 1: STUDY PROFILE METADATA
# -------------------------------------------------------------
with t_meta:
    st.header("Public Multi-Standard Study Metadata")
    with st.container(border=True):
        t_dc, t_ddi, t_lom = st.tabs(["Dublin Core Core Elements", "DDI Research Methodology", "IEEE LOM Educational Context"])
        with t_dc:
            dc_title = st.text_input("Title (dc:title)", value="")
            dc_creator = st.text_input("Creator / Lead Investigator (dc:creator)", value="")
            dc_subject = st.text_input("Subject Keywords (dc:subject)", value="")
            dc_date = st.text_input("Lifecycle Assembly Date (dc:date)", value="")
            dc_type = st.selectbox("Resource Material Type (dc:type)", ["Dataset", "Text / Observation Log", "Software Application"])
        with t_ddi:
            ddi_design = st.selectbox("Methodology Paradigm", ["Randomized Controlled Trial (RCT)", "Quasi-Experimental Design (QED)", "Correlational Study"])
            ddi_unit = st.selectbox("Observation Level", ["Individual Student Level", "Classroom-Level Aggregation"])
        with t_lom:
            academic_keys_discipline = st.selectbox("Disciplinary Focus", ["Mathematics", "Science", "Special Education"])
            student_levels = st.multiselect("Grade Levels", ["Kindergarten", "Elementary", "Middle School", "High School", "Undergraduate"])

# -------------------------------------------------------------
# TAB 2: SURVEY BUILDER & TEMPLATE GENERATOR
# -------------------------------------------------------------
with t_spec:
    st.header("Survey Instrument Builder & Schema Designer")
    
    # 1. Theoretical Framework Preset Selector
    st.markdown("### Step 1: Select a Theoretical Framework Blueprint")
    selected_framework = st.selectbox(
        "Choosing a framework pre-selects validated variables for your model.",
        options=list(FRAMEWORK_MAP.keys())
    )
    framework_defaults = FRAMEWORK_MAP[selected_framework]

    # 2. Dynamic Variable Checklist Configuration
    st.markdown("### Step 2: Fine-Tune Variable Selection")
    include_core = st.checkbox("Include Core Identifiers (`StudentID`, `Gender_Identity`, `Qualitative_Notes`)", value=True)
    
    selected_variables = []
    # Loop over structural category groups to organize the UI cleanly
    for subscale, rules in SUBSCALE_MAP.items():
        with st.expander(f"✨ {subscale} Subscale Fields", expanded=True):
            for item in rules["items"]:
                # Checked by default if part of the framework blueprint
                is_default_checked = item in framework_defaults
                if st.checkbox(f"Use Variable: `{item}` — *\"{ITEM_BANK[item]}\"*", value=is_default_checked, key=f"select_{item}"):
                    selected_variables.append(item)

    # 3. Structural CSV Blueprint Exporter
    st.markdown("---")
    st.markdown("### Step 3: Export Clean Metadata Templates & Questionnaires")
    
    col_temp, col_surv = st.columns(2)
    
    with col_temp:
        st.subheader("Data Entry Schema File")
        template_columns = ["StudentID", "Gender_Identity", "Qualitative_Notes"] if include_core else []
        template_columns.extend(selected_variables)
        
        df_template = pd.DataFrame(columns=template_columns)
        st.dataframe(df_template, use_container_width=True)
        
        csv_buffer = df_template.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Blank Metadata Template (CSV)",
            data=csv_buffer,
            file_name="educational_metadata_schema.csv",
            mime="text/csv"
        )

    with col_surv:
        st.subheader("Printable Survey Instrument File")
        if selected_variables:
            # Construct a human-readable survey list dataframe
            survey_data = {
                "Variable Header Key": selected_variables,
                "Survey Question Prompt / Statement Text": [ITEM_BANK[v] for v in selected_variables],
                "Suggested Response Scale": ["Likert Scale (1-5 Strongly Disagree to Strongly Agree)"] * len(selected_variables)
            }
            df_survey = pd.DataFrame(survey_data)
            st.dataframe(df_survey, use_container_width=True)
            
            survey_csv = df_survey.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📝 Download Custom Survey Document (CSV)",
                data=survey_csv,
                file_name="psychometric_survey_instrument.csv",
                mime="text/csv"
            )
        else:
            st.warning("Please select at least one psychometric variable to generate a functional survey tool.")

# -------------------------------------------------------------
# TAB 3: DATA SHARING HUB & INTEGRITY LAYOUT
# -------------------------------------------------------------
with t_share:
    st.header("Open Science Public Data Sharing Repository")
    st.write("Contribute de-identified research datasets to the centralized crowdsourced open education project repository.")
    
    # 1. Dataset Submission Form
    with st.container(border=True):
        st.subheader("📤 Data Repository Contribution Layer")
        shared_file = st.file_uploader("Upload target project data spreadsheet (CSV Format)", type=["csv"], key="share_upload")
        
        st.markdown("#### Open Science Compliance & Certifications")
        cert_irb = st.checkbox("I certify that this dataset is completely de-identified and has appropriate institutional board approval (IRB).")
        cert_cc0 = st.checkbox("I agree to dedicate this dataset to the public domain under Creative Commons Zero (CC0 1.0) licensing rules.")
        
        submit_share = st.button("Publish to Repository Queue", type="primary")
        
        if submit_share:
            if shared_file is not None:
                if cert_irb and cert_cc0:
                    df_shared = pd.read_csv(shared_file)
                    st.success(f"🎉 Dataset containing {len(df_shared)} rows successfully submitted to the validation queue!")
                    
                    # Quick analytics profile verification display
                    st.markdown("### Profile Distribution Validation Check")
                    all_expected = []
                    for s, r in SUBSCALE_MAP.items():
                        all_expected.extend(r["items"])
                    matched = [c for c in df_shared.columns if c in all_expected]
                    st.info(f"Verified alignment profile: Found {len(matched)} standard variables out of {len(all_expected)} recognized entries.")
                    st.dataframe(df_shared.head(5), use_container_width=True)
                else:
                    st.error("You must check both validation boxes to verify compliance before publishing data.")
            else:
                st.error("Please upload a target CSV data spreadsheet file first.")

    # 2. Schema Modification Box
    st.markdown("---")
    st.subheader("💡 Propose New Schema Columns to the Core Engine")
    with st.form("schema_proposal_form", clear_on_submit=True):
        new_key = st.text_input("Proposed Variable Column Key", placeholder="e.g., Digital_Literacy_Scale")
        category_options = list(SUBSCALE_MAP.keys()) + ["Institutional / Demographics", "External Context Factor"]
        new_category = st.selectbox("Subscale or Metadata Category Alignment", options=category_options)
        is_reverse = st.checkbox("Is this variable reverse-coded?")
        new_justification = st.text_area("Research Justification / Theoretical Framework", placeholder="Explain why this field is necessary.")
        submitted_proposal = st.form_submit_button("Generate Proposal Pack")

    if submitted_proposal:
        if new_key and new_justification:
            new_proposal = {"Proposed Column Key": new_key, "Subscale Category": new_category, "Justification": new_justification}
            st.session_state["proposed_columns"].append(new_proposal)
            st.success("Proposal packet compiled! Use the button below to submit your request.")
            
            issue_title = f"[Schema Proposal] Add '{new_key}'"
            issue_body = f"### 💡 New Variable Schema Proposal\n\n[START_DATA]\nKEY={new_key}\nCATEGORY={new_category}\nREVERSE={'True' if is_reverse else 'False'}\n[END_DATA]\n\n### 📄 Research Justification\n{new_justification}"
            github_issue_link = f"{GITHUB_REPO_URL}/issues/new?title={urllib.parse.quote(issue_title)}&body={urllib.parse.quote(issue_body)}"
            st.link_button("Submit Proposal via GitHub Issue", github_issue_link, type="primary")
        else:
            st.error("Please fill out the Variable Column Key and Research Justification fields.")
