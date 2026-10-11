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

            # ---------------------------------------------------------
            # NEW: INTERACTIVE ANALYTICS & FIGURES PLATFORM
            # ---------------------------------------------------------
            st.markdown("---")
            st.markdown("### 📊 Interactive Analytics & Figures Platform")
            
            # Extract all calculated score columns for charting analytics
            score_cols = [f"SCORE_{k}" for k in generated_scales_summary.keys()]
            
            if score_cols:
                chart_tab1, chart_tab2 = st.tabs(["📈 Scale Distributions", "👥 Group Demographics Analytics"])
                
                with chart_tab1:
                    st.write("**Participant Profile Score Density Distributions**")
                    # Melt dataframe columns cleanly for plotting multiple series onto a single histogram layout
                    df_melted = df_processed.melt(
                        id_vars=["StudentID"] if "StudentID" in df_processed.columns else None,
                        value_vars=score_cols,
                        var_name="Psychometric Scale Construct",
                        value_name="Calculated Composite Score"
                    )
                    
                    # Generate an interactive histogram figure using plotly express
                    fig_dist = px.histogram(
                        df_melted, 
                        x="Calculated Composite Score", 
                        color="Psychometric Scale Construct",
                        barmode="overlay",
                        marginal="box",
                        nbins=20,
                        title="Distribution Profile Across Deployed Framework Scales",
                        template="plotly_white"
                    )
                    fig_dist.update_layout(xaxis_title="Scale Mean Score Value", yaxis_title="Participant Count Frequency")
                    st.plotly_chart(fig_dist, use_container_width=True)
                
                with chart_tab2:
                    if "Gender_Identity" in df_processed.columns:
                        st.write("**Cross-Sectional Identity Variance Summary Matrix**")
                        selected_chart_scale = st.selectbox("Select Scale Target for Group Profiling Analysis", options=score_cols)
                        
                        # Generate an interactive categorical box plot comparing scale scores by demographic groupings
                        fig_box = px.box(
                            df_processed,
                            x="Gender_Identity",
                            y=selected_chart_scale,
                            color="Gender_Identity",
                            points="all",
                            title=f"Variance Metrics Matrix: '{selected_chart_scale}' Group Distributions",
                            template="plotly_white"
                        )
                        fig_box.update_layout(xaxis_title="Reported Gender Identity Group", yaxis_title="Scale Composite Average Score")
                        st.plotly_chart(fig_box, use_container_width=True)
                    else:
                        st.info("To unlock Cross-Sectional Group profiling graphics, ensure your uploaded dataset includes a standard 'Gender_Identity' column.")
            
            st.markdown("---")
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
# TAB 4: TWO-WAY DATA MERGE & PROPOSAL PLATFORM HUB
# -------------------------------------------------------------
with t_share:
    st.header("🔀 Connected Master Data Hub & Open Science Repository Gateways")
    st.write("This tab securely connects your contribution to a global unified database table while helping you publish individual records to KCWorks for citable DOIs.")
    
    with st.container(border=True):
        st.subheader("1️⃣ Step One: Stream Dataset into the Connected Global Master Repository")
        st.write("Uploading here automatically appends row observations directly to the project's centralized core data collection matrix.")
        
        shared_file = st.file_uploader("Upload structured project dataset (CSV Format)", type=["csv"], key="share_upload")
        
        st.markdown("#### Open Science Compliance Validation Certifications")
        cert_irb = st.checkbox("I certify that this dataset is completely de-identified and has appropriate institutional board approval (IRB).")
        cert_cc0 = st.checkbox("I agree to dedicate this dataset to the public domain under Creative Commons Zero (CC0 1.0) licensing rules.")
        
        unique_id_stamp = st.text_input("Project Tracker Tag (Your name or study code name)", placeholder="e.g., Doe_Math_Study_2026")
        
        submit_share = st.button("🚀 Process & Append to Connected Master Repository", type="primary")
        
        if submit_share:
            if shared_file is not None and unique_id_stamp:
                if cert_irb and cert_cc0:
                    df_upload = pd.read_csv(shared_file)
                    
                    # Track row lineage source by appending tracker attributes
                    df_upload["Meta_Global_Contributor_ID"] = unique_id_stamp
                    
                    # Run secure backend API data deployment transmission stream 
                    with st.spinner("Streaming rows to global connected repository matrix file..."):
                        success = append_to_github_master(df_upload)
                        
                    if success:
                        st.success(f"🎉 Success! {len(df_upload)} rows appended to the connected master registry file.")
                        st.markdown("### 2️⃣ Step Two: Secure Your Individual Personal DOI via KCWorks")
                        st.write("Now that your rows are cleanly unified within the core registry database, download your standard aligned validation file below and drop it into KCWorks to receive your citable reference DOI.")
                        
                        # Provide clean validated dataset back to user for repository uploading
                        st.download_button(
                            label="📥 Download Verified Clean File for KCWorks",
                            data=df_upload.to_csv(index=False).encode('utf-8'),
                            file_name=f"{unique_id_stamp}_verified_metadata.csv",
                            mime="text/csv"
                        )
                        st.link_button("📤 Open KCWorks Deposit Portal Interface", "https://hcommons.org", type="primary")
                    else:
                        st.error("Failed to append rows to master repository code file. Verify GitHub PAT credentials.")
                else:
                    st.error("You must select both validation checklist items to clear compliance validation routines.")
            else:
                st.error("Please ensure a CSV spreadsheet is uploaded and a unique Project Tracker identifier tag is provided.")

    st.markdown("---")
    st.subheader("💡 Propose New Schema Columns to the Core Engine")
    
    # Guidelines container
    with st.expander("📖 View Formatting Guidelines & Question Type Examples", expanded=False):
        st.markdown("Format inputs cleanly. Split multiple text question items using a semicolon (`;`). Group multiple choice options with commas.")
    
    # 1. Capture the identity input field BEFORE the form kicks off
    proposal_contributor = st.text_input(
        "Contributor Identifier for Proposal Tracking (Your name or organization)", 
        placeholder="e.g., Jane_Doe_MSU",
        key="proposal_contributor_id"
    )
    
    # 2. Main structural input layout form
    with st.form("schema_proposal_form", clear_on_submit=True):
        new_key = st.text_input("Proposed Variable Column Key", placeholder="e.g., Student_Self_Efficacy")
        new_citation = st.text_input("APA Citation Source Reference", placeholder="Author, A. A. (Year)...")
        var_type = st.selectbox("Variable Format", options=["Likert Scale (Ordinal Rating)", "Multiple Choice (Categorical / Nominal)", "Text Entry (Qualitative / String)"])
        mc_options = st.text_input("Multiple Choice Options (Commas separated)", placeholder="e.g., Option A, Option B")
        new_items = st.text_area("Survey Items Questions Text prompts", placeholder="Separate multiple variables items with a semicolon (;)")
        
        submitted_proposal = st.form_submit_button("Generate Proposal Pack")

    # 3. Form processing logic block
    if submitted_proposal:
        if new_key and new_citation and new_items and proposal_contributor:
            # Stamp identity tracking token into the title and structural data fields
            issue_title = f"[Schema Proposal] Add '{new_key}' by {proposal_contributor}"
            issue_body = f"""### 💡 New Variable Schema Proposal

[START_DATA]
KEY={new_key}
CITER={proposal_contributor}
CITATION={new_citation}
TYPE={var_type}
OPTIONS={mc_options if mc_options and var_type == 'Multiple Choice (Categorical / Nominal)' else 'N/A'}
ITEMS={new_items}
[END_DATA]

### 📄 Research Justification
Community submission scale configuration entry."""
            
            github_issue_link = f"{GITHUB_REPO_URL}/issues/new?title={urllib.parse.quote(issue_title)}&body={urllib.parse.quote(issue_body)}"
            
            st.success("Proposal packet compiled! Click the button below to transfer it to the GitHub Action validation pipeline.")
            st.link_button("Submit Proposal via GitHub Issue", github_issue_link, type="primary")
        else:
            st.error("Please ensure all form parameters AND your Contributor Identifier are filled out completely.")
