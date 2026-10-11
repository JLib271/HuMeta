import streamlit as st
import pandas as pd
import numpy as np
import json
import urllib.parse

st.set_page_config(page_title="Open Educational Metadata Portal", layout="wide")
st.title("🔬 Open Educational Metadata Portal")
st.caption("An Open Source, Community-Driven Engine for Standardized Educational Research and Psychometrics.")

# Configuration for your repository
GITHUB_REPO_URL = "https://github.com"

# Initialize an entry tracker for community suggestions
if "proposed_columns" not in st.session_state:
    st.session_state["proposed_columns"] = []

# 1. Unpack our JSON Registry database
try:
    with open("schema_config.json", "r") as f:
        registry = json.load(f)
    FRAMEWORK_MAP = registry["frameworks"]
    VARIABLES_DB = registry["variables"]
except Exception as e:
    st.error(f"Failed to pull schema registry database mapping configurations: {e}")
    st.stop()

# Math equation to calculate Cronbach's Alpha reliability
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
# MAIN APPLICATION INTERFACE NAVIGATION
# -------------------------------------------------------------
t_meta, t_spec, t_score, t_share = st.tabs([
    "🌐 1. Study Profile Metadata", 
    "📋 2. Survey Builder & Templates", 
    "📊 3. Automated Scale Scoring Engine",
    "📤 4. Open Science Propose & Share"
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
    
    st.markdown("### Step 1: Select a Theoretical Framework Blueprint")
    selected_framework = st.selectbox(
        "Choosing a framework flags and isolates matching scale configurations.",
        options=list(FRAMEWORK_MAP.keys())
    )
    framework_defaults = FRAMEWORK_MAP[selected_framework]

    # Core constraint logic variables configuration
    st.markdown("### Step 2: Fine-Tune Variable Scales & Survey Prompts")
    include_core = st.checkbox("Include Baseline Demographics (`StudentID`, `Gender_Identity`, `Qualitative_Notes`)", value=True)
    
    # Conditional prompt querying extra model components
    allow_extra_variables = st.checkbox("➕ Would you like to select additional variables outside this framework?", value=False)
    
    selected_variables = []
    
    # Filter variables to display based on user alignment preferences
    for var_key, var_data in VARIABLES_DB.items():
        is_aligned = var_key in framework_defaults
        total_items = len(var_data["items"]) + len(var_data["reverse_items"])
        
        # Condition rule: Render if aligned, or if user unlocked the extra variables toggle check
        if is_aligned or allow_extra_variables:
            # Visually mark outside metrics if rendering a cross-theory field block
            label_prefix = "📊 [Aligned Construct]" if is_aligned else "🔄 [External Construct]"
            
            with st.expander(f"{label_prefix} {var_key} ({total_items} Items Total)", expanded=is_aligned):
                st.caption(f"📚 **Citation Source:** *{var_data['citation']}*")
                
                # Default checked to True if it belongs directly to the selected theory model core path
                if st.checkbox(f"Deploy Scale Construct: `{var_key}`", value=is_aligned, key=f"deploy_{var_key}"):
                    selected_variables.append(var_key)
                    
                    if var_data["items"]:
                        st.markdown("**Standard Items Wording:**")
                        for text in var_data["items"]:
                            st.markdown(f"- 📝 *\"{text}\"*")
                    if var_data["reverse_items"]:
                        st.markdown("**Reverse-Coded Items Wording:**")
                        for text in var_data["reverse_items"]:
                            st.markdown(f"- ⚠️ *\"{text}\" (Inverted Score Required)*")

    st.markdown("---")
    st.markdown("### Step 3: Export Aligned Metadata Matrices & Questionnaires")
    col_temp, col_surv = st.columns(2)
    
    with col_temp:
        st.subheader("Data Entry Template Matrix File")
        template_columns = ["StudentID", "Gender_Identity", "Qualitative_Notes"] if include_core else []
        
        for var_key in selected_variables:
            v_info = VARIABLES_DB[var_key]
            template_columns.extend(v_info["items"])
            template_columns.extend(v_info["reverse_items"])
        
        df_template = pd.DataFrame(columns=template_columns)
        st.dataframe(df_template, use_container_width=True)
        
        st.download_button(
            label="📥 Download Blank Metadata Template (CSV)",
            data=df_template.to_csv(index=False).encode('utf-8'),
            file_name="educational_metadata_schema.csv",
            mime="text/csv"
        )

    with col_surv:
        st.subheader("Printable Questionnaire Sheet File")
        if selected_variables:
            txt_output = "========================================================\n"
            txt_output += "RESEARCH SURVEY INSTRUMENT & FIELD QUESTIONNAIRE\n"
            txt_output += "========================================================\n\n"
            txt_output += "INSTRUCTIONS: Please respond to each statement honestly by checking\n"
            txt_output += "the option that matches your experience.\n\n"
            txt_output += "RESPONSE OPTIONS:\n"
            txt_output += " Strongly Disagree  Disagree  Neutral  Agree  Strongly Agree\n\n"
            txt_output += "--------------------------------------------------------\n\n"
            
            item_counter = 1
            for var_key in selected_variables:
                v_info = VARIABLES_DB[var_key]
                txt_output += f"### SCALE CONSTRUCT: {var_key}\n"
                txt_output += f"Source Citation: {v_info['citation']}\n"
                txt_output += "--------------------------------------------------------\n"
                
                for text in v_info["items"]:
                    txt_output += f"{item_counter}. {text}\n"
                    txt_output += "   [ ] 1      [ ] 2      [ ] 3      [ ] 4      [ ] 5\n\n"
                    item_counter += 1
                    
                for text in v_info["reverse_items"]:
                    txt_output += f"{item_counter}. {text}\n"
                    txt_output += "   [ ] 1      [ ] 2      [ ] 3      [ ] 4      [ ] 5\n\n"
                    item_counter += 1
            
            st.text_area("Questionnaire Sheet Text Preview", value=txt_output, height=250)
            
            st.download_button(
                label="📝 Download Ready-to-Complete Questionnaire (TXT)",
                data=txt_output.encode('utf-8'),
                file_name="psychometric_survey_instrument.txt",
                mime="text/plain"
            )
        else:
            st.warning("Please choose at least one scale variable to compile survey templates.")

# -------------------------------------------------------------
# TAB 3: AUTOMATED SCALE SCORING ENGINE
# -------------------------------------------------------------
with t_score:
    st.header("🧠 Automated Scale Scoring Engine")
    st.write("Upload your raw participant response data sheet. The dashboard will automatically locate individual item text columns, reverse negative items, and generate standardized composite structural scores.")

    scoring_file = st.file_uploader("Upload raw research response spreadsheet (CSV Format)", type=["csv"], key="scoring_input")

    if scoring_file is not None:
        df_raw = pd.read_csv(scoring_file)
        st.success("Dataset successfully parsed by the psychometric engine layers.")

        st.markdown("#### ⚙️ Scoring Inversion Metrics Calibration")
        col_scale1, col_scale2 = st.columns(2)
        with col_scale1:
            likert_min = st.number_input("Minimum Likert Response Scale Point Value", value=1)
        with col_scale2:
            likert_max = st.number_input("Maximum Likert Response Scale Point Value", value=5)
        
        inversion_constant = likert_min + likert_max
        df_processed = df_raw.copy()
        df_processed.columns = df_processed.columns.str.strip()
        
        generated_scales_summary = {}

        st.markdown("### 📈 Compute Matrix Statistics Overview")

        for var_key, var_data in VARIABLES_DB.items():
            standard_items = [item.strip() for item in var_data["items"]]
            reverse_items = [item.strip() for item in var_data["reverse_items"]]
            
            matched_standard = [c for c in df_processed.columns if c in standard_items]
            matched_reverse = [c for c in df_processed.columns if c in reverse_items]
            all_matched_items = matched_standard + matched_reverse

            if len(all_matched_items) >= 1:
                sub_df = df_processed[all_matched_items].apply(pd.to_numeric, errors='coerce')
                
                for rev_col in matched_reverse:
                    sub_df[rev_col] = inversion_constant - sub_df[rev_col]

                scale_score_column_name = f"SCORE_{var_key}"
                df_processed[scale_score_column_name] = sub_df.mean(axis=1)

                if len(all_matched_items) > 1:
                    alpha_val = calculate_cronbach_alpha(sub_df)
                else:
                    alpha_val = "Single Item Measure"
                
                generated_scales_summary[var_key] = {
                    "Matched Items Found": f"{len(all_matched_items)} / {len(standard_items) + len(reverse_items)}",
                    "Reverse Items Inverted": len(matched_reverse),
                    "Cronbach's Alpha Reliability": f"{alpha_val:.3f}" if isinstance(alpha_val, float) else alpha_val
                }

        if generated_scales_summary:
            st.write("#### 🔍 Identified Psychometric Measurements Profile")
            st.json(generated_scales_summary)

            st.write("#### 📊 Processed Dataset Output Preview (Featuring Generated Scale Columns)")
            st.dataframe(df_processed, use_container_width=True)

            st.download_button(
                label="📥 Download Scored Dataset File (CSV)",
                data=df_processed.to_csv(index=False).encode('utf-8'),
                file_name="computed_scale_scores_output.csv",
                mime="text/csv",
                help="Click here to download your original file appended with automated composite scale score columns."
            )
        else:
            st.warning("No columns matched your configurations registry items profiles.")
    else:
        st.info("Awaiting raw response spreadsheet files containing item question headers to initialize scoring calculations engine loops.")

# -------------------------------------------------------------
# TAB 4: OPEN SCIENCE DATA SHARING & PROPOSALS
# -------------------------------------------------------------
with t_share:
    st.header("Open Science Data Hub & Repository Submissions")
    
    with st.container(border=True):
        st.subheader("📤 Data Repository Contribution Layer")
        shared_file = st.file_uploader("Upload target project data spreadsheet (CSV Format)", type=["csv"], key="share_upload")
        
        st.markdown("#### Open Science Compliance & Certifications")
        cert_irb = st.checkbox("I certify that this dataset is completely de-identified and has appropriate institutional board approval (IRB).")
        cert_cc0 = st.checkbox("I agree to dedicate this dataset to the public domain under Creative Commons Zero (CC0 1.0) licensing rules.")
        
        submit_share = st.button("Publish to Repository Queue", type="primary")
        
        if submit_share:
            if shared_file is not None and cert_irb and cert_cc0:
                df_shared = pd.read_csv(shared_file)
                st.success(f"🎉 Dataset containing {len(df_shared)} rows successfully submitted to the validation queue!")
                st.dataframe(df_shared.head(5), use_container_width=True)
            else:
                st.error("Please ensure your target CSV file is uploaded and both compliance verification boxes are selected.")

    st.markdown("---")
    st.subheader("💡 Propose New Schema Columns to the Core Engine")
    with st.form("schema_proposal_form", clear_on_submit=True):
        new_key = st.text_input("Proposed Variable Column Key", placeholder="e.g., Digital_Literacy_Scale")
        new_citation = st.text_input("APA Citation Source Reference", placeholder="Author, A. A. (Year). Title...")
        new_items = st.text_area("Survey Scale Items Wording", placeholder="Separate multiple items using a semicolon (;)")
        submitted_proposal = st.form_submit_button("Generate Proposal Pack")

    if submitted_proposal:
        if new_key and new_citation and new_items:
            new_proposal = {"Proposed Column Key": new_key, "Citation": new_citation}
            st.session_state["proposed_columns"].append(new_proposal)
            st.success("Proposal packet compiled! Use the button below to submit your request to the repository maintainers.")
            
            issue_title = f"[Schema Proposal] Add '{new_key}'"
            issue_body = f"### 💡 New Variable Schema Proposal\n\n[START_DATA]\nKEY={new_key}\nCITATION={new_citation}\nITEMS={new_items}\n[END_DATA]\n\n### 📄 Research Justification\nCommunity submission scale configuration entry."
            github_issue_link = f"{GITHUB_REPO_URL}/issues/new?title={urllib.parse.quote(issue_title)}&body={urllib.parse.quote(issue_body)}"
            st.link_button("Submit Proposal via GitHub Issue", github_issue_link, type="primary")
        else:
            st.error("Please fill out all schema parameters before compiling tracking configurations.")
