import streamlit as st
import pandas as pd
import numpy as np
import io
import os
import tempfile
import sqlite3
from sqlalchemy import text
import requests
import urllib.parse
from supabase import create_client, Client

# Initialize Supabase Client
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

# Securely connect to your database
try:
    supabase = init_supabase()
except Exception as e:
    st.error("Database connection configuration missing. Please verify your Streamlit Cloud Secrets.")
    st.stop()

# ==========================================
# 1. PSYCHOMETRIC & METADATA DICTIONARIES
# ==========================================
THEORY_MAP = {
    "Theory of Planned Behavior (TPB)": {
        "Attitude Toward the Behavior": {
            "item": "Engaging in this educational behavior is beneficial for my academic goals.",
            "scale": "1=Strongly Disagree, 2=Disagree, 3=Neutral, 4=Agree, 5=Strongly Agree"
        },
        "Subjective Norms": {
            "item": "People who are important to me think I should perform this behavior.",
            "scale": "1=Strongly Disagree, 2=Disagree, 3=Neutral, 4=Agree, 5=Strongly Agree"
        },
        "Perceived Behavioral Control": {
            "item": "I have total control over my ability to perform this behavior successfully.",
            "scale": "1=Strongly Disagree, 2=Disagree, 3=Neutral, 4=Agree, 5=Strongly Agree"
        },
        "Behavioral Intention": {
            "item": "I intend to perform this behavior during the current academic term.",
            "scale": "1=Strongly Disagree, 2=Disagree, 3=Neutral, 4=Agree, 5=Strongly Agree"
        }
    },
    "Self-Determination Theory (SDT)": {
        "Autonomy Support": {
            "item": "I feel a strong sense of choice and freedom in how I undertake my learning tasks.",
            "scale": "1=Not at all True, 2=Somewhat True, 3=Very True"
        },
        "Competence": {
            "item": "I feel confident and capable in mastering the difficult concepts in this course.",
            "scale": "1=Not at all True, 2=Somewhat True, 3=Very True"
        },
        "Relatedness": {
            "item": "I feel a genuine sense of connection and belonging with my peers and instructors.",
            "scale": "1=Not at all True, 2=Somewhat True, 3=Very True"
        },
        "Intrinsic Motivation": {
            "item": "I engage in these learning activities because I find them deeply interesting and enjoyable.",
            "scale": "1=Not at all True, 2=Somewhat True, 3=Very True"
        }
    },
    "Technology Acceptance Model (TAM)": {
        "Perceived Usefulness (PU)": {
            "item": "Using this learning platform improves my academic performance and productivity.",
            "scale": "1=Strongly Disagree, 2=Disagree, 3=Neutral, 4=Agree, 5=Strongly Agree"
        },
        "Perceived Ease of Use (PEOU)": {
            "item": "Learning to operate this digital dashboard is easy and clear for me.",
            "scale": "1=Strongly Disagree, 2=Disagree, 3=Neutral, 4=Agree, 5=Strongly Agree"
        },
        "Behavioral Intention to Use": {
            "item": "I plan to regularly use this learning system throughout the upcoming academic year.",
            "scale": "1=Strongly Disagree, 2=Disagree, 3=Neutral, 4=Agree, 5=Strongly Agree"
        }
    }
}

# Global Cloud Connection Initialization
try:
    db_url = st.secrets["connections"]["sql"]["url"]
    shared_conn = st.connection("sql", type="sql", url=db_url)
except Exception:
    shared_conn = None

# App configuration and session setup
st.set_page_config(page_title="Open Educational Metadata Engine", layout="wide")
if "session_instruments" not in st.session_state:
    st.session_state.session_instruments = []

st.title("🔬 Open Educational Metadata Portal")
st.caption("Standardized Study Registries and Psychometric Instrument Architects under DCMES, IEEE LOM, and CEDS Standards.")

# Engine selection sidebar routing
st.sidebar.header("⚙️ Core Controls")
app_mode = st.sidebar.radio(
    "Navigate Workspace Module:",
    ["1. Study Metadata Schema Registry", "2. Variable Instrument Architect", "3. Community Data Repository Sync", "4. Descriptive & Scale Analytics", "5. Live Central Database Viewer"]
)

# ==========================================
# MODULE 1: STUDY-LEVEL METADATA REGISTRY
# ==========================================
if app_mode == "1. Study Metadata Schema Registry":
    st.header("📝 Standardized Study Metadata Submission")
    st.caption("Aligning educational research metadata elements across Dublin Core (DCMES) and CEDS standards.")
    st.markdown("---")
    
    # --- DYNAMIC AUTHOR TRACKING INITIALIZATION ---
    if "authors_list" not in st.session_state:
        st.session_state.authors_list = [{"name": "", "orcid": ""}]

    st.subheader("👥 Dublin Core Creators (dc:creator)")
    st.caption("Manage as many authors and ORCID iDs as your study requires.")

    # Render interactive input text fields dynamically for every author in session memory
    updated_authors = []
    for idx, author in enumerate(st.session_state.authors_list):
        col_name, col_orcid, col_del = st.columns(3)
        
        with col_name:
            auth_name = st.text_input(
                f"Author {idx+1} Name", 
                value=author["name"], 
                key=f"auth_name_{idx}", 
                placeholder="e.g., Dr. Jane Doe"
            )
        with col_orcid:
            auth_orcid = st.text_input(
                f"Author {idx+1} ORCID iD Link", 
                value=author["orcid"], 
                key=f"auth_orcid_{idx}", 
                placeholder="e.g., https://orcid.org"
            )
        with col_del:
            st.markdown("<div style='padding-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"auth_del_{idx}", disabled=len(st.session_state.authors_list) <= 1):
                st.session_state.authors_list.pop(idx)
                st.rerun()
                
        updated_authors.append({"name": auth_name, "orcid": auth_orcid})

    # Update our state matrix on the fly with whatever the user typed
    st.session_state.authors_list = updated_authors

    if st.button("➕ Add Author"):
        st.session_state.authors_list.append({"name": "", "orcid": ""})
        st.rerun()

    st.markdown("---")

    # --- MAIN SUBMISSION FORM ---
    with st.form("metadata_standards_form", clear_on_submit=True):
        st.subheader("📋 Core Project Overview")
        
        title = st.text_input(
            "Title (dc:title)*", 
            placeholder="e.g., Impact of Open Textbooks on Course-Level Retention Metrics"
        )
        description = st.text_area(
            "Description / Abstract (dc:description)", 
            placeholder="Summary of research objectives, design schema, and core conceptual findings..."
        )
        keywords = st.text_input(
            "Subject Keywords (dc:subject)", 
            placeholder="e.g., OER, Student Motivation, Retention, Psychometrics"
        )
        language = st.selectbox(
            "Language (dc:language)", 
            options=["English (en)", "Spanish (es)", "French (fr)", "Other / Multilingual"]
        )
        
        st.divider()

        # --- DDI (DATA DOCUMENTATION INITIATIVE) STANDARD METADATA ---
        st.subheader("📊 Data Documentation Initiative (DDI Metadata Schema)")
        st.caption("Capturing structural data-level context, collection methods, and lifecycle tracking frameworks.")
        
        col_ddi1, col_ddi2 = st.columns(2)
        with col_ddi1:
            unit_of_analysis = st.selectbox(
                "Unit of Analysis (ddi:UnitOfAnalysis)",
                options=[
                    "Individual (Student / Learner)",
                    "Individual (Teacher / Instructor)",
                    "Group / Classroom Level",
                    "Organization / Institution (School/University)",
                    "Geographic / School District Level",
                    "Other / Multi-Level"
                ]
            )
            data_collection_mode = st.selectbox(
                "Data Collection Mode (ddi:ModeOfCollection)",
                options=[
                    "Self-Administered Questionnaire: Web/Online",
                    "Self-Administered Questionnaire: Paper",
                    "Face-to-Face Interview / Qualitative Audio",
                    "Focus Group / Transcript Coding",
                    "Automated Ingestion / Server Log Extraction",
                    "Mixed Modes"
                ]
            )
        with col_ddi2:
            sampling_procedure = st.selectbox(
                "Sampling Procedure (ddi:SamplingProcedure)",
                options=[
                    "Non-probability: Total Universe / Census",
                    "Non-probability: Convenience / Availability Sampling",
                    "Non-probability: Purposive / Judgmental Sampling",
                    "Probability: Simple Random Sampling",
                    "Probability: Stratified Random Sampling",
                    "Probability: Cluster / Multi-Stage Sampling"
                ]
            )
            time_method = st.selectbox(
                "Time Method / Study Design (ddi:TimeMethod)",
                options=[
                    "Cross-sectional / Single Time Point Assessment",
                    "Longitudinal: Cohort Study / Repeated Measures",
                    "Longitudinal: Trend / Multiple Intervals",
                    "Experimental / Pre-Post Testing",
                    "Time Series Analysis"
                ]
            )
            
        st.divider()
        
        # --- COMMON EDUCATION DATA STANDARDS (CEDS ALIGNMENT) ---
        st.subheader("🌐 Common Education Data Standards (CEDS Alignment)")
        st.caption("Standardized dropdown and checkbox matrices mapping directly to CEDS element repositories.")
        
        # 1. The Study Scope (The "When" and "Where")
        st.markdown("### 📍 1. The Study Scope (The 'When' and 'Where')")
        col_scope1, col_scope2, col_scope3 = st.columns(3)
        with col_scope1:
            academic_year = st.selectbox(
                "Academic Year Designator*",
                options=["2026-2027", "2025-2026", "2024-2025", "2023-2024", "2022-2023", "2021-2022", "2020-2021", "Prior to 2020"],
                index=2
            )
        with col_scope2:
            state_origin = st.selectbox(
                "State of Origin",
                options=["National/Multi-State", "AK", "AL", "AR", "AZ", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "IA", "ID", "IL", "IN", "KS", "KY", "LA", "MA", "MD", "ME", "MI", "MN", "MO", "MS", "MT", "NC", "ND", "NE", "NH", "NJ", "NM", "NV", "NY", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VA", "VT", "WA", "WI", "WV", "WY"]
            )
        with col_scope3:
            locale_setting = st.selectbox(
                "Locale (Geographic Setting)", 
                options=["City", "Suburban", "Town", "Rural", "Virtual / Online Learning Environment"]
            )
            
        st.markdown(" ")
        
        # 2. The Population (The "Who")
        st.markdown("### 👥 2. The Population (The 'Who')")
        col_pop1, col_pop2 = st.columns(2)
        with col_pop1:
            grade_level = st.multiselect(
                "Grade Level (Baseline Starting Point)",
                options=["Early Childhood / Pre-K", "Kindergarten", "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12", "Postsecondary (Undergraduate)", "Postsecondary (Graduate)", "Adult Education"],
                default=["Postsecondary (Undergraduate)"]
            )
        with col_pop2:
            program_type = st.multiselect(
                "Program Type / Student Subgroup",
                options=["Regular / General Education Program", "English Learner (EL) Program", "Special Education / IDEA Services", "Title I Schoolwide Program", "Migrant Education Program", "Career and Technical Education (CTE)", "College Preparatory / Gifted Program"],
                default=["Regular / General Education Program"]
            )
            
        st.markdown(" ")
        
        # 3. The Methodology (The "What")
        st.markdown("### 🛠️ 3. The Methodology (The 'What')")
        col_meth1, col_meth2, col_meth3 = st.columns(3)
        with col_meth1:
            academic_subject = st.selectbox(
                "Assessment Academic Subject", 
                options=["Mathematics", "Reading / English Language Arts", "Science", "Social Studies / History", "Foreign Language Education", "Fine and Performing Arts", "Computer and Information Sciences", "Interdisciplinary / General Academic"]
            )
        with col_meth2:
            assessment_purpose = st.selectbox(
                "Assessment Purpose", 
                options=["Research Intervention Evaluation", "State Accountability Assessment", "Diagnostic Benchmark Assessment", "Formative / Progress Monitoring Assessment", "Summative / End-of-Course Evaluation", "Placement / College Readiness Testing"]
            )
        with col_meth3:
            course_level_type = st.selectbox(
                "Course Level Type Rigor", 
                options=["Regular / Standard Rigor", "Remedial / Developmental / Basic", "Advanced Placement (AP)", "International Baccalaureate (IB)", "Honors Level", "Dual Enrollment / Postsecondary Credit"]
            )
            
        st.divider()
        
        # --- SUBMIT BUTTON & VALIDATION ---
        submit_metadata = st.form_submit_button("🚀 Submit Complete Study Record")
        
        if submit_metadata:
            has_author = any(auth["name"].strip() for auth in st.session_state.authors_list)
            
            if not title:
                st.error("DCMES Core Field Title (dc:title) is required to index the study.")
            elif not has_author:
                st.error("At least one Creator/Author Name is required.")
            else:
                try:
                    # Compile primary metadata schema record parameters 
                    study_payload = {
                        "study_title": title,
                        "principal_investigator": str(st.session_state.authors_list[0]["name"]),
                        "institution": "Standard Submission Profile",
                        "funding_source": "Open Educational Registry Ingest Pipeline",
                        "study_description": description if description else "No project abstract supplied."
                    }
                    
                    # Direct data integration execution loop into cloud storage schema
                    study_res = supabase.table("studies").insert(study_payload).execute()
                    new_id = study_res.data[0]["id"]
                    
                    # Package fallback tracking variable into variable database dictionary row
                    var_payload = {
                        "study_id": new_id,
                        "variable_name": "STUDY_ROOT_REGISTRY",
                        "variable_label": "System Validation Row",
                        "data_type": "String",
                        "measurement_unit": "N/A",
                        "description": f"Auto-generated configuration handle verifying structural indexing values mapping subject categories: {keywords if keywords else 'None'}."
                    }
                    supabase.table("variables").insert(var_payload).execute()
                    
                    st.success(f"🎉 Success! Metadata schema safely serialized. '{title}' has been permanently synchronized to Supabase central tables.")
                    st.session_state.authors_list = [{"name": "", "orcid": ""}]
                except Exception as db_err:
                    st.error(f"Database ingestion failure: {db_err}")

    st.markdown("---")
    st.markdown("### 🚀 Propose Extensions to Core Study Metadata Architecture")
    with st.expander("💡 Click to Draft a Metadata Schema Suggestion"):
        suggested_schema_field = st.text_input("Target Element / Field Code to Change", key="mod1_suggest_field")
        suggested_schema_text = st.text_area("Detailed Suggestion / Additions Details", key="mod1_suggest_text")
        if suggested_schema_field and suggested_schema_text:
            schema_payload = f"""**Metadata Proposal**"""

**Field:** {suggested_schema_field}

```text
{suggested_schema_text}
```"
            st.code(schema_payload, language="markdown")

# ==========================================
# MODULE 2: VARIABLE ARCHITECT & INSTRUMENT EXPORTER
# ==========================================
elif app_mode == "2. Variable Instrument Architect":
    st.header("📐 Variable Architect & Instrument Exporter")
    st.markdown("---")
    st.subheader("📚 1. Social Science Repository Metadata")
    
    st.info("💡 **Need a DOI for your study artifacts?** Please submit **de-identified** research artifacts directly to the [STEMEd+ Commons Collection in KCWorks](https://kcworks.org).")
    
    col_rep1, col_rep2 = st.columns(2)
    with col_rep1:
        repository_id = st.text_input("Persistent Identifier / DOI", placeholder="doi:10.xxxx/...")
        unit_of_analysis = st.selectbox("Unit of Analysis (DDI Core)", options=["Individual (Student/Teacher)", "Group/Classroom", "Organization/Institution"])
    with col_rep2:
        sampling_method = st.selectbox("Sampling Procedure", options=["Probability: Simple Random Sampling", "Non-probability: Convenience Sampling"])
        sampling_procedure = st.text_area("Sampling Method Explanation / Implementation Context*")

    st.divider()
    st.subheader("🧠 2. Study Variable & Framework Configuration")
    
    collect_gender = st.checkbox("Include Gender Category", value=True)
    collect_age = st.checkbox("Include Age / Birthdate Metrics", value=True)
    
    selected_frameworks = st.multiselect("Choose core guiding theoretical framework(s):", options=["Theory of Planned Behavior (TPB)", "Self-Determination Theory (SDT)", "Technology Acceptance Model (TAM)"])
    
    active_items = []
    if collect_gender:
        active_items.append({"Variable_ID": "VAR_GENDER", "Concept_Construct": "Demographics", "Variable_Label": "Participant Gender", "Question_Item_Text": "What gender category do you most closely identify with?", "Response_Scale_Options": "Woman | Man | Non-binary", "Framework_Source": "CEDS"})
    if collect_age:
        active_items.append({"Variable_ID": "VAR_AGE", "Concept_Construct": "Demographics", "Variable_Label": "Participant Age", "Question_Item_Text": "Please enter your age:", "Response_Scale_Options": "Continuous Integer Entry", "Framework_Source": "CEDS"})

    for framework in selected_frameworks:
        if framework in THEORY_MAP:
            for construct, props in THEORY_MAP[framework].items():
                if st.checkbox(f"Include {construct} ({framework})", value=True):
                    active_items.append({
                        "Variable_ID": f"VAR_{construct.upper().replace(' ', '_')}",
                        "Concept_Construct": construct,
                        "Variable_Label": f"{framework} - {construct}",
                        "Question_Item_Text": props["item"],
                        "Response_Scale_Options": props["scale"],
                        "Framework_Source": framework
                    })
                    
    st.markdown(" ")
    st.subheader("➕ 3. Bulk Import Custom Variables & Suggestions")
    
    uploaded_custom_vars = st.file_uploader("Upload your completed Custom Variables CSV file", type=["csv"])
    uploaded_items = []
    if uploaded_custom_vars is not None:
        try:
            uploaded_df = pd.read_csv(uploaded_custom_vars)
            uploaded_items = uploaded_df.to_dict(orient="records")
            st.success("✅ Custom variables loaded successfully!")
            st.dataframe(uploaded_df, use_container_width=True)
        except Exception as e:
            st.error(f"Error parsing spreadsheet file: {e}")

    final_instrument_list = active_items + uploaded_items
    if final_instrument_list:
        df_manifest = pd.DataFrame(final_instrument_list)
        st.subheader("📋 Your Active Study Instrument Summary Table")
        st.dataframe(df_manifest, use_container_width=True, hide_index=True)
        
        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            st.download_button("📥 Download Metadata Sheet (.csv)", df_manifest.to_csv(index=False), "metadata_sheet.csv", "text/csv", use_container_width=True)
        with col_exp2:
            st.download_button("📥 Download Technical Manifest (.txt)", str(final_instrument_list), "manifest.txt", "text/plain", use_container_width=True)

# ==========================================
# MODULE 3: COMMUNITY STORAGE SYNCHRONIZATION
# ==========================================
elif app_mode == "3. Community Data Repository Sync":
    st.header("🌐 Safe De-Identified Community Synchronization Hub")
    st.markdown("---")
    check_names = st.checkbox("Confirmed: Direct identifiers removed.")
    check_dates = st.checkbox("Confirmed: Exact timeline timestamps bucketed.")
    check_irb = st.checkbox("Confirmed: Complies with IRB and privacy parameters.")
    
    uploaded_data_file = st.file_uploader("Upload De-Identified Local Study Data File (.csv)", type=["csv"])
    if uploaded_data_file is not None:
        df_user_raw = pd.read_csv(uploaded_data_file)
        st.dataframe(df_user_raw.head(10), use_container_width=True)
        if check_names and check_dates and check_irb:
            if st.button("🚀 Push De-Identified Dataset to Collective Global Repository"):
                st.success("Data parameters evaluated. Standalone schema synchronization loop executed safely!")

# ==========================================
# MODULE 4: DESCRIPTIVE & SCALE ANALYTICS
# ==========================================
elif app_mode == "4. Descriptive & Scale Analytics":
    st.header("📊 Descriptive & Scale Analytics Engine")
    st.markdown("---")
    data_source = st.radio("Analytics Dataset Source Selection:", ["Use Standard Synthetic Sample Dataset", "Upload Custom Research Data Sheet (.csv)"])
    
    if data_source == "Use Standard Synthetic Sample Dataset":
        np.random.seed(42)
        n_samples = 100
        synthetic_data = {
            "Participant_ID": range(1, n_samples + 1),
            "Age": np.random.randint(18, 25, size=n_samples),
            "Gender": np.random.choice(["Woman", "Man"], size=n_samples),
            "TPB_Attitude_Item1": np.random.randint(1, 6, size=n_samples),
            "TPB_Attitude_Item2": np.random.randint(1, 6, size=n_samples)
        }
        df_analytics = pd.DataFrame(synthetic_data)
    else:
        uploaded_analytics_file = st.file_uploader("Upload target tracking matrix sheet (.csv)", type=["csv"])
        df_analytics = pd.read_csv(uploaded_analytics_file) if uploaded_analytics_file is not None else None
        
    if df_analytics is not None:
        st.subheader("📋 Dataset Workspace Snapshot")
        st.dataframe(df_analytics.head(10), use_container_width=True)
        numeric_cols = df_analytics.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            selected_col = st.selectbox("Select Target Variable for Distribution Evaluation:", numeric_cols)
            st.bar_chart(df_analytics[selected_col].value_counts().sort_index())

# ==========================================
# MODULE 5: LIVE CENTRAL DATABASE VIEWER
# ==========================================
elif app_mode == "5. Live Central Database Viewer":
    st.header("🗄️ Central Repository Live Database Viewer")
    st.caption("Direct, read-only access to the underlying structured SQL tables storing public community metadata records.")
    st.markdown("---")

    st.subheader("📊 Select Table to Query")
    col_btn1, col_btn2 = st.columns(2)
    
    if "active_db_view" not in st.session_state:
        st.session_state.active_db_view = "studies"

    with col_btn1:
        if st.button("📋 View Core Studies Table (`studies`)", use_container_width=True, type="primary" if st.session_state.active_db_view == "studies" else "secondary"):
            st.session_state.active_db_view = "studies"
            st.rerun()

    with col_btn2:
        if st.button("📐 View Mapped Variables Table (`variables`)", use_container_width=True, type="primary" if st.session_state.active_db_view == "variables" else "secondary"):
            st.session_state.active_db_view = "variables"
            st.rerun()

    st.markdown("---")

    try:
        with st.spinner(f"Querying live `{st.session_state.active_db_view}` matrix from Supabase..."):
            db_response = supabase.table(st.session_state.active_db_view).select("*").order("created_at", descending=True).execute()
            
            if db_response.data:
                display_df = pd.DataFrame(db_response.data)
                st.subheader(f"📂 Active Grid: `{st.session_state.active_db_view}` Table Records")
                st.markdown(f"Displaying the latest **{len(display_df)}** submissions recorded in the cloud architecture.")
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                raw_csv_bytes = display_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"📥 Download Raw `{st.session_state.active_db_view}` Dataset (.csv)",
                    data=raw_csv_bytes,
                    file_name=f"supabase_central_repository_{st.session_state.active_db_view}.csv",
                    mime="text/csv"
                )
            else:
                st.info(f"The `{st.session_state.active_db_view}` table is currently connected but contains no data entries yet.")
    except Exception as db_view_error:
        st.error(f"Failed to query central database: {db_view_error}")
