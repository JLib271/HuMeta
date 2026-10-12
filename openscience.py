import streamlit as st
import pandas as pd
import numpy as np
import json
import urllib.parse
import requests
import base64

# --- New Database Imports ---
import tempfile
import os
import sqlite3

# --- DATABASE INITIALIZATION ---
# 1. Global Cloud Shared Database (Supabase/Postgres) via Streamlit Secrets
try:
    shared_conn = st.connection("postgresql", type="sql")
except Exception:
    shared_conn = None
local_df = None
st.set_page_config(page_title="Open Educational Metadata Portal", layout="wide")
st.title("🔬 Open Educational Metadata Portal")
st.caption("An Open Source, Community-Driven Engine for Standardized Educational Research and Psychometrics.")

import streamlit as st
import pandas as pd
import sqlite3
import tempfile
import os

# --- SILENT DATABASE INITIALIZATION ---
# Fallback to local SQLite if a cloud database is not linked in Streamlit Secrets
try:
    shared_conn = st.connection("postgresql", type="sql")
except Exception:
    shared_conn = None

# Ensure structural tables exist in local/fallback modes 
# In production Postgres, you would run these CREATE scripts once inside your Supabase SQL console.
def init_local_tables(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS studies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            authors TEXT,
            abstract TEXT,
            keywords TEXT,
            theoretical_framework TEXT
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS variables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            study_id INTEGER,
            variable_name TEXT NOT NULL,
            variable_type TEXT,
            operational_definition TEXT,
            FOREIGN KEY(study_id) REFERENCES studies(id)
        );
    """)
    conn.commit()

# --- STEP 1: CHOOSE TARGET ENGINE WORKFLOW ---
st.sidebar.header("⚙️ Workspace Engine")
db_mode = st.sidebar.radio("Data Saving Destination:", ["Local Locked (SQLite File)", "Global Collaborative Hub"])

# Setup local session tracking
if "local_db_path" not in st.session_state:
    # Set up a clean persistent file for this specific session
    temp_dir = tempfile.gettempdir()
    st.session_state.local_db_path = os.path.join(temp_dir, "opened_metadata_session.db")
    conn = sqlite3.connect(st.session_state.local_db_path)
    init_local_tables(conn)
    conn.close()

# --- STEP 2: USER METADATA SUBMISSION FORM ---
st.header("📝 Submit New Study Metadata")

with st.form("study_submission_form", clear_on_submit=True):
    st.subheader("Core Project Details")
    title = st.text_input("Study Title*", placeholder="e.g., Impact of Open Textbooks on Retention")
    authors = st.text_input("Author(s)", placeholder="e.g., Jane Doe, John Smith")
    abstract = st.text_area("Abstract", placeholder="Summary of the study's objective and design...")
    keywords = st.text_input("Keywords (comma separated)", placeholder="e.g., open education, OER, equity")
    
    st.divider()
    st.subheader("Theoretical & Conceptual Framework")
    framework = st.text_area(
        "Theoretical Framework", 
        placeholder="e.g., Self-Determination Theory (SDT), Technology Acceptance Model (TAM)..."
    )
    
    st.divider()
    st.subheader("Study Variables Layout")
    st.caption("Define the properties of what you are measuring (do not upload raw collection spreadsheets here).")
    
    # Dynamic variables entry text strings parsed dynamically 
    variables_input = st.text_area(
        "List variables being collected (One per line format -> Name | Type | Operational Definition)",
        value="Course Grade | Dependent Variable | Final numerical score percentage scaled 0-100\nTextbook Cost | Independent Variable | Total out of pocket dollar cost calculated at checkout",
        help="Use the pipe symbol '|' to break out properties easily."
    )
    
    submit_btn = st.form_submit_button("💾 Save Study Record")

    if submit_btn:
        if not title:
            st.error("Study Title is required.")
        else:
            # Process variable strings into clean array structures
            parsed_variables = []
            for line in variables_input.strip().split("\n"):
                if "|" in line:
                    parts = [p.strip() for p in line.split("|")]
                    v_name = parts[0]
                    v_type = parts[1] if len(parts) > 1 else ""
                    v_def = parts[2] if len(parts) > 2 else ""
                    if v_name:
                        parsed_variables.append((v_name, v_type, v_def))
                else:
                    if line.strip():
                        parsed_variables.append((line.strip(), "Not Specified", "No definition provided"))

            # Execution block base routing
            if db_mode == "Local Locked (SQLite File)":
                # Save to local sandboxed database
                conn = sqlite3.connect(st.session_state.local_db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO studies (title, authors, abstract, keywords, theoretical_framework) VALUES (?, ?, ?, ?, ?)",
                    (title, authors, abstract, keywords, framework)
                )
                study_id = cursor.lastrowid
                
                for var in parsed_variables:
                    cursor.execute(
                        "INSERT INTO variables (study_id, variable_name, variable_type, operational_definition) VALUES (?, ?, ?, ?)",
                        (study_id, var[0], var[1], var[2])
                    )
                conn.commit()
                conn.close()
                st.success("Successfully logged study to your temporary local instance!")
                st.rerun()
                
            elif db_mode == "Global Collaborative Hub":
                if shared_conn is not None:
                    with shared_conn.session as session:
                        # Save main study layer
                        res = session.execute(
                            """INSERT INTO studies (title, authors, abstract, keywords, theoretical_framework) 
                               VALUES (:title, :authors, :abstract, :keywords, :framework) RETURNING id;""",
                            {"title": title, "authors": authors, "abstract": abstract, "keywords": keywords, "framework": framework}
                        )
                        # Handles platform returning styles
                        try:
                            study_id = res.fetchone()[0]
                        except Exception:
                            # Fallback tracking if framework lacks direct sequential returning markers
                            study_id = session.execute("SELECT max(id) FROM studies;").fetchone()[0]
                        
                        # Save sub-relational variables
                        for var in parsed_variables:
                            session.execute(
                                """INSERT INTO variables (study_id, variable_name, variable_type, operational_definition) 
                                   VALUES (:study_id, :name, :type, :def);""",
                                {"study_id": study_id, "name": var[0], "type": var[1], "def": var[2]}
                            )
                        session.commit()
                    st.success("Successfully broadcasted your study metadata layout live to the global community database!")
                    st.rerun()
                else:
                    st.error("Global database engine credentials are unconfigured. Please use 'Local Locked' engine mode.")

# --- STEP 3: DATA VISUALIZATION EXPLORER ---
st.divider()
st.header("🔍 Explored Studies Registries")

if db_mode == "Local Locked (SQLite File)":
    # If the user uploaded a local CSV file, use it. Otherwise, initialize an empty registry dataframe.
    if local_df is not None:
        df_studies = local_df.copy()
        # Create a sequential ID to match the rest of your app's rendering loops
        df_studies['id'] = range(1, len(df_studies) + 1)
        
        # Unpack variables layout into a structured dataframe to match your rendering expectations
        vars_list = []
        for idx, row in df_studies.iterrows():
            if pd.notna(row['variables_layout']):
                for line in str(row['variables_layout']).strip().split("\n"):
                    if "|" in line:
                        parts = [p.strip() for p in line.split("|")]
                        v_name = parts[0] if len(parts) > 0 else line.strip()
                        v_type = parts[1] if len(parts) > 1 else "Not Specified"
                        v_def = parts[2] if len(parts) > 2 else "No definition"
                    else:
                        v_name = line.strip()
                        v_type = "Not Specified"
                        v_def = "No definition"
                    if v_name:
                        vars_list.append({"study_id": row['id'], "variable_name": v_name, "variable_type": v_type, "operational_definition": v_def})
        df_vars = pd.DataFrame(vars_list)
    else:
        df_studies = pd.DataFrame(columns=["id", "title", "authors", "abstract", "keywords", "theoretical_framework", "variables_layout"])
        df_vars = pd.DataFrame(columns=["study_id", "variable_name", "variable_type", "operational_definition"])
        
    # Provide a simple export mechanism to save their work back out to an Excel/CSV file layout
    if not df_studies.empty:
        csv_download = df_studies.to_csv(index=False).encode('utf-8')
        st.sidebar.download_button(
            label="📥 Download Local Registry (.csv)",
            data=csv_download,
            file_name="open_ed_metadata_registry.csv",
            mime="text/csv"
        )
else:
    if shared_conn is not None:
        try:
            df_studies = shared_conn.query("SELECT * FROM studies ORDER BY id DESC;", ttl="0")
            df_vars = shared_conn.query("SELECT * FROM variables;", ttl="0")
        except Exception:
            df_studies, df_vars = pd.DataFrame(), pd.DataFrame()
    else:
        df_studies, df_vars = pd.DataFrame(), pd.DataFrame()
        st.info("Global catalog offline.")

# Render output summaries natively using nested tabs layout
if not df_studies.empty:
    for idx, row in df_studies.iterrows():
        with st.expander(f"📚 {row['title']} — by {row['authors'] if row['authors'] else 'Unknown'}"):
            st.markdown(f"**Keywords:** `{row['keywords']}`")
            st.markdown(f"### Abstract\n{row['abstract'] if row['abstract'] else '*No summary provided.*'}")
            st.markdown(f"### Theoretical Framework\n{row['theoretical_framework'] if row['theoretical_framework'] else '*None specified.*'}")
            
            # Match child elements belonging to this study sequence cleanly
            if not df_vars.empty:
                # Filter down variables for just this study ID
                matched_vars = df_vars[df_vars['study_id'] == row['id']]
                if not matched_vars.empty:
                    st.markdown("### Collected Variables Layout")
                    st.dataframe(
                        matched_vars[['variable_name', 'variable_type', 'operational_definition']], 
                        use_container_width=True,
                        hide_index=True
                    )
else:
    st.info("No study models found matching your current workspace selection database filter criteria.")


# Configuration for your repository
GITHUB_REPO_URL = "https://github.com"
REPO_OWNER = "JLib271"
REPO_NAME = "OpenEdMetadata"
MASTER_FILE_PATH = "master_repository_data.csv"

# Initialize an entry tracker for community suggestions
if "proposed_columns" not in st.session_state:
    st.session_state["proposed_columns"] = []

# Unpack our central JSON Registry database
try:
    with open("schema_config.json", "r") as f:
        registry = json.load(f)
    FRAMEWORK_MAP = registry["frameworks"]
    VARIABLES_DB = registry["variables"]
except Exception as e:
    st.error(f"Failed to pull schema registry database mapping configurations: {e}")
    st.stop()

# Helper engine to push data safely to GitHub repository files via API
def append_to_github_master(df_new_rows):
    if "GITHUB_PAT" not in st.secrets:
        st.error("Missing secure repository credentials configuration ('GITHUB_PAT') inside Streamlit settings.")
        return False
        
    token = st.secrets["GITHUB_PAT"]
    url = f"https://github.com{REPO_OWNER}/{REPO_NAME}/contents/{MASTER_FILE_PATH}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    
    # Step A: Get the existing master repository file if it exists
    res = requests.get(url, headers=headers)
    sha = None
    df_existing = pd.DataFrame()
    
    if res.status_code == 200:
        file_data = res.json()
        sha = file_data["sha"]
        content_decoded = base64.b64decode(file_data["content"]).decode('utf-8')
        from io import StringIO
        df_existing = pd.read_csv(StringIO(content_decoded))
    
    # Step B: Combine old records with new rows cleanly
    df_combined = pd.concat([df_existing, df_new_rows], ignore_index=True)
    csv_updated_string = df_combined.to_csv(index=False)
    content_encoded = base64.b64encode(csv_updated_string.encode('utf-8')).decode('utf-8')
    
    # Step C: Send the payload commit matrix pack back up to GitHub
    payload = {
        "message": "database: automated row injection into master repository archive",
        "content": content_encoded
    }
    if sha:
        payload["sha"] = sha
        
    put_res = requests.put(url, headers=headers, json=payload)
    return put_res.status_code in [200, 201]

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
# MAIN INTERFACE NAVIGATION TABS SYSTEM
# -------------------------------------------------------------
t_meta, t_spec, t_score, t_share = st.tabs([
    "🌐 1. Study Profile Metadata", 
    "📋 2. Survey Builder & Templates", 
    "📊 3. Automated Scale Scoring Engine",
    "📤 4. Global Connected Repository Hub"
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

    st.markdown("### Step 2: Fine-Tune Variable Scales & Survey Prompts")
    include_core = st.checkbox("Include Baseline Demographics (`StudentID`, `Gender_Identity`, `Qualitative_Notes`)", value=True)
    allow_extra_variables = st.checkbox("➕ Would you like to select additional variables outside this framework?", value=False)
    
    selected_variables = []
    for var_key, var_data in VARIABLES_DB.items():
        is_aligned = var_key in framework_defaults
        total_items = len(var_data["items"]) + len(var_data["reverse_items"])
        
        if is_aligned or allow_extra_variables:
            label_prefix = "📊 [Aligned Construct]" if is_aligned else "🔄 [External Construct]"
            with st.expander(f"{label_prefix} {var_key} ({total_items} Items Total)", expanded=is_aligned):
                st.caption(f"📚 **Citation Source:** *{var_data['citation']}*")
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
            txt_output += "RESPONSE OPTIONS: 1=Strongly Disagree, 2=Disagree, 3=Neutral, 4=Agree, 5=Strongly Agree\n\n"
            
            item_counter = 1
            for var_key in selected_variables:
                v_info = VARIABLES_DB[var_key]
                txt_output += f"### SCALE CONSTRUCT: {var_key}\nSource: {v_info['citation']}\n"
                for text in v_info["items"] + v_info["reverse_items"]:
                    txt_output += f"{item_counter}. {text}\n   [ ] 1      [ ] 2      [ ] 3      [ ] 4      [ ] 5\n\n"
                    item_counter += 1
            st.text_area("Questionnaire Sheet Text Preview", value=txt_output, height=150)
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
    st.write("Upload your raw student data sheet. The dashboard will automatically locate item text columns, reverse negative responses, and generate finalized structural scale composite score attributes.")

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

                alpha_val = calculate_cronbach_alpha(sub_df) if len(all_matched_items) > 1 else "Single Item Measure"
                generated_scales_summary[var_key] = {
                    "Matched Items Found": f"{len(all_matched_items)} / {len(standard_items) + len(reverse_items)}",
                    "Reverse Items Inverted": len(matched_reverse),
                    "Cronbach's Alpha Reliability": f"{alpha_val:.3f}" if isinstance(alpha_val, float) else alpha_val
                }

        if generated_scales_summary:
            st.write("#### 🔍 Identified Psychometric Measurements Profile")
            st.json(generated_scales_summary)

            # ---------------------------------------------------------
            # INTERACTIVE ANALYTICS & FIGURES PLATFORM (TAB 3)
            # ---------------------------------------------------------
            import plotly.express as px
            st.markdown("---")
            st.markdown("### 📊 Interactive Analytics & Figures Platform")
            
            score_cols = [f"SCORE_{k}" for k in generated_scales_summary.keys()]
            
            if score_cols:
                chart_tab1, chart_tab2 = st.tabs(["📈 Scale Distributions", "👥 Group Demographics Analytics"])
                
                with chart_tab1:
                    st.write("**Participant Profile Score Density Distributions**")
                    df_melted = df_processed.melt(
                        id_vars=["StudentID"] if "StudentID" in df_processed.columns else None,
                        value_vars=score_cols,
                        var_name="Psychometric Scale Construct",
                        value_name="Calculated Composite Score"
                    )
                    
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
            st.write("#### 📊 Processed Dataset Output Preview")
            st.dataframe(df_processed, use_container_width=True)
            st.download_button(
                label="📥 Download Scored Dataset File (CSV)",
                data=df_processed.to_csv(index=False).encode('utf-8'),
                file_name="computed_scale_scores_output.csv",
                mime="text/csv"
            )
        else:
            st.warning("No columns matched your configuration profiles.")
    else:
        st.info("Awaiting raw response spreadsheet files containing item question headers to initialize loops.")
        # -------------------------------------------------------------
# TAB 4: TWO-WAY DATA MERGE & PROPOSAL PLATFORM HUB
# -------------------------------------------------------------
with t_share:
    st.header("🔀 Connected Master Data Hub & Open Science Repository Gateways")
    st.write("This tab securely connects your contribution to a global unified database table while helping you publish individual records to KCWorks for citable DOIs.")
    
    import plotly.express as px
    st.markdown("### 📊 Global Registry Analytics Dashboard")
    
    # CORRECTED URL ENHANCEMENT FUNCTION
    @st.cache_data(ttl=300)
    def load_global_master_data():
        raw_url = f"https://githubusercontent.com{REPO_OWNER}/{REPO_NAME}/main/{MASTER_FILE_PATH}"
        try:
            return pd.read_csv(raw_url)
        except Exception:
            return pd.DataFrame()

    df_global_master = load_global_master_data()

    if not df_global_master.empty:
        total_global_records = len(df_global_master)
        unique_studies = df_global_master["Meta_Global_Contributor_ID"].nunique() if "Meta_Global_Contributor_ID" in df_global_master.columns else 1
        
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.metric("Total Global Observations Collected", f"{total_global_records:,} Rows")
        with m_col2:
            st.metric("Unique Contributing Studies / Pipelines", f"{unique_studies} Projects")
            
        st.write("**Cross-Project Contribution Distribution Map**")
        if "Meta_Global_Contributor_ID" in df_global_master.columns:
            score_columns = [c for c in df_global_master.columns if c.startswith("SCORE_")]
            
            if score_columns:
                selected_master_scale = st.selectbox("Select Target Benchmark Metric for Cross-Project Comparison", options=score_columns, key="master_chart_selector")
                
                fig_master = px.box(
                    df_global_master,
                    x="Meta_Global_Contributor_ID",
                    y=selected_master_scale,
                    color="Meta_Global_Contributor_ID",
                    title=f"Global Variance Mapping Matrix: '{selected_master_scale}' across Studies",
                    template="plotly_white"
                )
                fig_master.update_layout(xaxis_title="Registered Contributor Project ID Tag", yaxis_title="Calculated Score Metrics")
                st.plotly_chart(fig_master, use_container_width=True)
            else:
                st.info("Global master data file found, but no scored metrics columns (`SCORE_...`) have been streamed yet.")
        else:
            st.info("Master storage dataset initialization is complete. Individual telemetry metrics lines will plot here upon project submission.")
    else:
        st.info("ℹ️ The global repository file (`master_repository_data.csv`) is empty. The data dashboard will populate automatically when the first researcher uploads a validated dataset below.")

    st.markdown("---")
    
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
                    df_upload["Meta_Global_Contributor_ID"] = unique_id_stamp
                    
                    with st.spinner("Streaming rows to global connected repository matrix file..."):
                        success = append_to_github_master(df_upload)
                        
                    if success:
                        st.success(f"🎉 Success! {len(df_upload)} rows appended to the connected master registry file.")
                        st.cache_data.clear()
                        
                        st.markdown("### 2️⃣ Step Two: Secure Your Individual Personal DOI via KCWorks")
                        st.write("Now that your rows are cleanly unified within the core registry database, download your standard aligned validation file below and drop it into KCWorks to receive your citable reference DOI.")
                        
                        st.download_button(
                            label="📥 Download Verified Clean File for KCWorks",
                            data=df_upload.to_csv(index=False).encode('utf-8'),
                            file_name=f"{unique_id_stamp}_verified_metadata.csv",
                            mime="text/csv"
                        )
                        st.link_button("📤 Open KCWorks Deposit Portal Interface", "https://hcommons.org", type="primary")
                    else:
                        st.error("Failed to append rows to master repository code file. Verify GITHUB_PAT credentials.")
                else:
                    st.error("You must select both validation checklist items to clear compliance validation routines.")
            else:
                st.error("Please ensure a CSV spreadsheet is uploaded and a unique Project Tracker identifier tag is provided.")

    st.markdown("---")
    st.subheader("💡 Propose New Schema Columns to the Core Engine")
    
    with st.expander("📖 View Formatting Guidelines & Question Type Examples", expanded=False):
        st.markdown("Format inputs cleanly. Split multiple text question items using a semicolon (`;`). Group multiple choice options with commas.")
    
    proposal_contributor = st.text_input(
        "Contributor Identifier for Proposal Tracking (Your name or organization)", 
        placeholder="e.g., Jane_Doe_MSU",
        key="proposal_contributor_id"
    )
    
    with st.form("schema_proposal_form", clear_on_submit=True):
        new_key = st.text_input("Proposed Variable Column Key", placeholder="e.g., Student_Self_Efficacy")
        new_citation = st.text_input("APA Citation Source Reference", placeholder="Author, A. A. (Year)...")
        var_type = st.selectbox("Variable Format", options=["Likert Scale (Ordinal Rating)", "Multiple Choice (Categorical / Nominal)", "Text Entry (Qualitative / String)"])
        mc_options = st.text_input("Multiple Choice Options (Commas separated)", placeholder="e.g., Option A, Option B")
        new_items = st.text_area("Survey Items Questions Text prompts", placeholder="Separate multiple variables items with a semicolon (;)")
        
        submitted_proposal = st.form_submit_button("Generate Proposal Pack")

    if submitted_proposal:
        if new_key and new_citation and new_items and proposal_contributor:
            issue_title = f"[Schema Proposal] Add '{new_key}' by {proposal_contributor}"
            issue_body = f"### 💡 New Variable Schema Proposal\n\n[START_DATA]\nKEY={new_key}\nCITER={proposal_contributor}\nCITATION={new_citation}\nTYPE={var_type}\nOPTIONS={mc_options if mc_options and var_type == 'Multiple Choice (Categorical / Nominal)' else 'N/A'}\nITEMS={new_items}\n[END_DATA]\n\n### 📄 Research Justification\nCommunity submission scale configuration entry."
            
            github_issue_link = f"{GITHUB_REPO_URL}/issues/new?title={urllib.parse.quote(issue_title)}&body={urllib.parse.quote(issue_body)}"
            
            st.success("Proposal packet compiled! Click the button below to transfer it to the GitHub Action validation pipeline.")
            st.link_button("Submit Proposal via GitHub Issue", github_issue_link, type="primary")
        else:
            st.error("Please ensure all form parameters AND your Contributor Identifier are filled out completely.")
    # --- LOCAL USER OFFLINE DATABASE (Sidebar Placement) ---
with st.sidebar:
    st.markdown("---")
    st.header("📂 Your Private Data")
    uploaded_file = st.file_uploader("Upload your local metadata.db file", type=["db", "sqlite"])

    local_df = None
    temp_db_path = None

    if uploaded_file is not None:
        # Temporarily cache uploaded file stream to local container memory
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as fp:
            fp.write(uploaded_file.getvalue())
            temp_db_path = fp.name

        local_conn = sqlite3.connect(temp_db_path)
        try:
            # Assumes a relational schema named 'metadata'
            local_df = pd.read_sql_query("SELECT * FROM metadata", local_conn)
            
            # Interactive write form to edit the local schema inside the sidebar lane
            with st.form("add_local_record"):
                st.write("Add New Record Locally")
                title = st.text_input("Resource Title")
                url = st.text_input("Resource URL")
                submitted = st.form_submit_button("Save Locally")
                
                if submitted and title:
                    cursor = local_conn.cursor()
                    cursor.execute("CREATE TABLE IF NOT EXISTS metadata (title TEXT, url TEXT)")
                    cursor.execute("INSERT INTO metadata (title, url) VALUES (?, ?)", (title, url))
                    local_conn.commit()
                    st.success("Saved! Download the file below to preserve changes.")
                    st.rerun()
        except Exception as e:
            st.error(f"Error reading file: {e}")
        finally:
            local_conn.close()

        # Dynamic file down-loader pipeline
        if temp_db_path and os.path.exists(temp_db_path):
            with open(temp_db_path, "rb") as f:
                st.download_button(
                    label="📥 Download Updated Local DB",
                    data=f.read(),
                    file_name="my_updated_metadata.db",
                    mime="application/x-sqlite3"
                )
            os.unlink(temp_db_path)

# --- GLOBAL COMMUNITY DATABASE (Main Screen Placement) ---
st.markdown("---")
st.subheader("🌐 Public Collaborative Database")

if shared_conn is not None:
    # Safely query cloud records from Postgres
    try:
        global_df = shared_conn.query("SELECT * FROM public_metadata;", ttl="0")
        st.dataframe(global_df, use_container_width=True)
    except Exception:
        st.info("The public repository table is initializing or empty.")

    # Cross-sync data frames via parameterized transaction session
    if local_df is not None:
        if st.button("🚀 Publish My Local Records to Community Feed"):
            with shared_conn.session as session:
                for index, row in local_df.iterrows():
                    session.execute(
                        "INSERT INTO public_metadata (title, url) VALUES (:title, :url) ON CONFLICT DO NOTHING;",
                        {"title": row['title'], "url": row['url']}
                    )
                session.commit()
            st.success("Successfully synchronized data with the community repository!")
            st.rerun()
else:
    st.warning("Running in offline mode. Configure Streamlit Secrets to enable the global community hub.")

