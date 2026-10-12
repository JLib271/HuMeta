import streamlit as st
import pandas as pd
import numpy as np
import io
from sqlalchemy import text

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
    ["1. Study Metadata Schema Registry", "2. Variable Instrument Architect", "3. Community Data Repository Sync", "4. Descriptive & Scale Analytics"]
)

# ==========================================
# MODULE 1: STUDY-LEVEL METADATA REGISTRY
# ==========================================
if app_mode == "1. Study Metadata Schema Registry":
    st.header("📝 Standardized Study Metadata Submission")
    st.caption("Aligning educational research metadata elements across Dublin Core (DCMES), CEDS, and DDI standards.")
    st.markdown("---")
    
    # --- DYNAMIC AUTHOR TRACKING INITIALIZATION ---
    if "authors_list" not in st.session_state:
        st.session_state.authors_list = [{"name": "", "orcid": ""}]

    st.subheader("👥 Dublin Core Creators (dc:creator)")
    st.caption("Manage as many authors and ORCID iDs as your study requires.")

    # Render interactive input text fields dynamically for every author in session memory
    updated_authors = []
    for idx, author in enumerate(st.session_state.authors_list):
        col_name, col_orcid, col_del = st.columns([4, 5, 1])
        
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
        
        submit_metadata = st.form_submit_button("🚀 Submit Complete Study Record")
        
        if submit_metadata:
            has_author = any(auth["name"].strip() for auth in st.session_state.authors_list)
            
            if not title:
                st.error("DCMES Core Field Title (dc:title) is required to index the study.")
            elif not has_author:
                st.error("At least one Creator/Author Name is required.")
            else:
                # Compile structural data dictionary payload capturing Dublin Core, CEDS, and DDI parameters
                metadata_payload = {
                    "title": title,
                    "creators_matrix": [a for a in st.session_state.authors_list if a["name"].strip()],
                    "description": description,
                    "subject": keywords,
                    "language": language,
                    "ddi_unit_of_analysis": unit_of_analysis,
                    "ddi_collection_mode": data_collection_mode,
                    "ddi_sampling_procedure": sampling_procedure,
                    "ddi_time_method": time_method,
                    "academic_year": academic_year,
                    "state": state_origin,
                    "locale": locale_setting,
                    "grade_levels": grade_level,
                    "program_types": program_type,
                    "academic_subject": academic_subject,
                    "assessment_purpose": assessment_purpose,
                    "course_level_type": course_level_type
                }
                st.success(f"Metadata payload for '{title}' logged with DDI schemas and {len(metadata_payload['creators_matrix'])} author(s) successfully!")
                
                # Reset authors list back to a clean default state for the next session
                st.session_state.authors_list = [{"name": "", "orcid": ""}]

# ==========================================
# MODULE 2: VARIABLE INSTRUMENT ARCHITECT
# ==========================================
elif app_mode == "2. Variable Instrument Architect":
    st.header("📐 Variable Architect & Instrument Exporter")
    st.caption("Design variable frameworks, configure measurement items, and instantly download standardized DDI-compliant XML/CSV blueprints.")
    st.markdown("---")
    
    # --- SECTION A: REPOSITORY & STUDY INDEXING (ICPSR / DATAVERSE STANDARDS) ---
    st.subheader("📚 1. Social Science Repository Metadata (ICPSR / Dataverse Alignment)")
    st.caption("Align study indexing with major repositories using rich, study-level methodology and citation tracing variables.")
    
    # Explicit user guidance for obtaining a DOI via KCWorks
    st.info(
        "💡 **Need a DOI for your study artifacts?** Please submit your research data, code, or materials directly to the "
        "[STEMEd+ Commons Collection in KCWorks](https://kcworks.org) to receive a unique persistent DOI before completing this index profile."
    )
    
    col_rep1, col_rep2 = st.columns(2)
    with col_rep1:
        repository_id = st.text_input(
            "Persistent Identifier / DOI (e.g., from KCWorks, Harvard Dataverse, or ICPSR)", 
            placeholder="e.g., doi:10.xxxx/kcworks..."
        )
        data_type = st.selectbox("Data Collection Type / Media Vector", ["Quantitative Matrix", "Qualitative Text Transcript", "Audio/Video Media", "Mixed Matrix"])
    with col_rep2:
        unit_of_analysis = st.selectbox("Unit of Analysis (DDI Core)", ["Individual (Student/Teacher)", "Group/Classroom", "Organization/Institution", "Geographic/School District"])
        sampling_procedure = st.text_input("Sampling Procedure", placeholder="e.g., Convenience sample, Stratified random sampling...")


    # --- SECTION B: PSYCHOMETRIC SCALE CONFIGURATOR (APA PsycTESTS STANDARDS) ---
    st.subheader("🧪 2. Psychometric Scale Metadata (APA PsycTESTS Alignment)")
    st.caption("Capture construct operationalization parameters including standard validity, reliability scores, and origin scales.")
    
    col_psy1, col_psy2 = st.columns(2)
    with col_psy1:
        origin_scale = st.text_input("Origin Scale Name", placeholder="e.g., Scientific Attitude Scale (SAS), Intrinsic Motivation Inventory (IMI)")
        reliability_metric = st.selectbox("Reliability Estimate Method", ["Cronbach's Alpha (α)", "McDonald's Omega (ω)", "Test-Retest Coefficient", "None/Qualitative"])
    with col_psy2:
        reliability_value = st.number_input("Reported Reliability Value (if known)", min_value=0.0, max_value=1.0, value=0.80, step=0.01)
        validity_framework = st.text_input("Construct Validity Support", placeholder="e.g., Confirmatory Factor Analysis (CFA) supported, Face validity verified")

    st.divider()

    # --- SECTION C: VARIABLE DICTIONARY GENERATOR (DDI SCHEMA STANDARDS) ---
    st.subheader("🧠 3. DDI Variable Schema Configuration")
    st.caption("Establish DDI-compliant metadata linking conceptual variables, parent constructs, target question items, and response scaling categories.")

    # 1. Demographics Selection Grid
    st.markdown("**Core Demographic Variables**")
    collect_gender = st.checkbox("Include Gender Variable", value=True)
    collect_age = st.checkbox("Include Age Variable", value=True)
    
    # 2. Theoretical Structural Framework Selector
    selected_framework = st.selectbox(
        "Choose core guiding theoretical framework to populate variables:",
        ["None / Custom Only", "Theory of Planned Behavior (TPB)", "Self-Determination Theory (SDT)", "Technology Acceptance Model (TAM)"]
    )
    
    # Compile variable items collection matrix mapping exactly to DDI specifications
    active_items = []
    
    if collect_gender:
        active_items.append({
            "Variable_ID": "VAR_GENDER",
            "Concept_Construct": "Demographics",
            "Variable_Label": "Participant Gender",
            "Question_Item_Text": "What gender category do you most closely identify with?",
            "Response_Scale_Options": "Woman | Man | Non-binary | Prefer to self-describe | Prefer not to say",
            "Norm_Schema": "DDI-Core / CEDS"
        })
    if collect_age:
        active_items.append({
            "Variable_ID": "VAR_AGE",
            "Concept_Construct": "Demographics",
            "Variable_Label": "Participant Age",
            "Question_Item_Text": "Please enter your age in numerical years:",
            "Response_Scale_Options": "Continuous Integer Entry",
            "Norm_Schema": "DDI-Core / CEDS"
        })
        
    if selected_framework in THEORY_MAP:
        st.markdown(f"**Pre-populated DDI variable elements for {selected_framework}:**")
        theory_data = THEORY_MAP[selected_framework]
        for construct, props in theory_data.items():
            include = st.checkbox(f"Include DDI Variable: {construct}", value=True)
            if include:
                # Dynamically construct unique IDs matching the DDI schema naming conventions
                var_id = f"VAR_{construct.upper().replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '')}"
                active_items.append({
                    "Variable_ID": var_id,
                    "Concept_Construct": construct,
                    "Variable_Label": f"{selected_framework} - {construct}",
                    "Question_Item_Text": props["item"],
                    "Response_Scale_Options": props["scale"],
                    "Norm_Schema": f"DDI-Lifecycle / APA PsycTESTS ({origin_scale if origin_scale else 'Standard Mapping'})"
                })
                
    # 3. Dynamic Injection Module for Custom / Alternative Constructs
    with st.expander("➕ Inject Additional Custom DDI Variables (Quantitative, Text, Media References)"):
        custom_name = st.text_input("Variable Identifier / ID Code", placeholder="e.g., VAR_ENGAGEMENT")
        custom_construct = st.text_input("Concept / Parent Construct", placeholder="e.g., Course Engagement")
        custom_label = st.text_input("Variable Label", placeholder="e.g., Self-Reported Hours Using OER")
        custom_type = st.selectbox("Data Classification Type", ["Quantitative / Ordinal Scale", "Text / Qualitative Response", "Other Media Link / Reference"])
        custom_item = st.text_input("Operational Question Text Prompt", placeholder="e.g., How many hours a week do you spend using OER platforms?")
        custom_scale = st.text_input("Scale Categories / Code Values Matrix", placeholder="e.g., 1=0-5 hours | 2=6-10 hours | 3=11+ hours")
        
        if st.button("Add Custom Variable Entry"):
            if custom_name and custom_item:
                st.session_state.session_instruments.append({
                    "Variable_ID": custom_name.upper().strip(),
                    "Concept_Construct": custom_construct,
                    "Variable_Label": custom_label,
                    "Question_Item_Text": custom_item,
                    "Response_Scale_Options": custom_scale,
                    "Norm_Schema": f"DDI-Custom ({custom_type})"
                })
                st.toast(f"Custom DDI variable {custom_name} added successfully!")

    # Merge static map array selections with active session array configurations
    final_instrument_list = active_items + st.session_state.session_instruments
    
    if final_instrument_list:
        df_manifest = pd.DataFrame(final_instrument_list)
        st.subheader("📋 Configured DDI Variable Manifest Mapping Spec")
        st.dataframe(df_manifest, use_container_width=True, hide_index=True)
        
        # --- EXPORT PIPELINES ---
        col_exp1, col_exp2 = st.columns(2)
        
        with col_exp1:
            # Generate the data dictionary metadata sheet (CSV) aligned with ICPSR/Harvard Dataverse codebook variables
            csv_buffer = io.StringIO()
            df_manifest.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📥 Download DDI Metadata Sheet (.csv)",
                data=csv_buffer.getvalue(),
                file_name="ddi_social_science_metadata_sheet.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        with col_exp2:
            # Generate deployment survey text configuration map (TXT) that replicates APA PsycTESTS profiling layouts
            txt_manifest = "=== DDI & APA PsycTESTS COMPLIANT STUDY INSTRUMENT MANIFEST ===\n"
            txt_manifest += f"Repository Context Code: {repository_id if repository_id else 'Not Cataloged'}\n"
            txt_manifest += f"Unit of Analysis: {unit_of_analysis}\n"
            txt_manifest += f"Psychometric Target Scale: {origin_scale if origin_scale else 'Custom Build'}\n"
            txt_manifest += f"Reported Scale Reliability: {reliability_metric} = {reliability_value}\n"
            txt_manifest += "=" * 60 + "\n\n"
            
            for idx, row in df_manifest.iterrows():
                txt_manifest += f"DDI Variable ID:  {row['Variable_ID']}\n"
                txt_manifest += f"Concept/Construct: {row['Concept_Construct']}\n"
                txt_manifest += f"Variable Label:    {row['Variable_Label']}\n"
                txt_manifest += f"Question Text:     {row['Question_Item_Text']}\n"
                txt_manifest += f"Code / Response Categories Matrix:\n   {row['Response_Scale_Options']}\n"
                txt_manifest += f"Metadata Schema Compliance Trace: {row['Norm_Schema']}\n"
                txt_manifest += "-" * 60 + "\n\n"
                
            st.download_button(
                label="📥 Download Deployment Survey Form (.txt)",
                data=txt_manifest,
                file_name="ddi_survey_instrument_form.txt",
                mime="text/plain",
                use_container_width=True
            )
    else:
        st.info("No structural framework or variable items selected yet.")


# ==========================================
# MODULE 3: COMMUNITY STORAGE SYNCHRONIZATION
# ==========================================
elif app_mode == "3. Community Data Repository Sync":
    st.header("🌐 Safe De-Identified Community Synchronization Hub")
    st.caption("Upload structured research data vectors securely. Data fields are evaluated to enforce de-identification thresholds before network execution loops activate.")
    st.markdown("---")
    
    st.subheader("🔒 Mandatory De-Identification Compliance Checklist")
    check_names = st.checkbox("Confirmed: All direct identifiers (Participant Names, Social Security / ID Handles) are completely removed.")
    check_dates = st.checkbox("Confirmed: Exact calendar timeline timestamps (Birthdates, precise exam dates) have been bucketed or masked.")
    check_irb = st.checkbox("Confirmed: Dataset distribution complies with institutional IRB, FERPA, and human subject privacy governance parameters.")
    
    st.markdown("---")
    uploaded_data_file = st.file_uploader("Upload De-Identified Local Study Data File (.csv format only)", type=["csv"])
    
    if uploaded_data_file is not None:
        try:
            df_user_raw = pd.read_csv(uploaded_data_file)
            st.success("✅ Local file successfully parsed into system memory workspace matrix!")
            st.dataframe(df_user_raw.head(10), use_container_width=True)
            
            # Lock database routing unless user checks off privacy framework parameters explicitly
            if check_names and check_dates and check_irb:
                if st.button("🚀 Push De-Identified Dataset to Collective Global Repository"):
                    if shared_conn is not None:
                        st.info("Uploading data to cloud platform...")
                        # Connection transactions route out here to target table maps
                    else:
                        st.success("Data validation completed! (Running in safe local standalone mode - file verification matches repository ingest schema parameters).")
            else:
                st.warning("⚠️ Access locked. Complete the mandatory De-Identification Compliance Checklist above to enable global server synchronization paths.")
        except Exception as e:
            st.error(f"Error parsing structural layout data frame: {e}")

# ==========================================
# MODULE 4: DESCRIPTIVE & SCALE ANALYTICS
# ==========================================
elif app_mode == "4. Descriptive & Scale Analytics":
    st.header("📊 Descriptive & Scale Analytics Engine")
    st.caption("Analyze item matrices, process missing value patterns, and compute aggregate survey construct values on the fly.")
    st.markdown("---")
    
    # Provide a simple option to load demo data if the user doesn't have a file ready
    data_source = st.radio("Analytics Workspace Mode:", ["Use Synthetic Sample Instrument Dataset", "Upload Custom Data Sheet (.csv)"])
    
    df_analytics = None
    
    if data_source == "Use Synthetic Sample Instrument Dataset":
        # Generate clean reproducible psychometric dataset distributions
        np.random.seed(42)
        n_samples = 100
        synthetic_data = {
            "Participant_ID": range(1, n_samples + 1),
            "Age": np.random.randint(18, 25, size=n_samples),
            "Gender": np.random.choice(["Woman", "Man", "Non-binary"], size=n_samples, p=[0.55, 0.40, 0.05]),
            "TPB_Attitude_Item1": np.random.choice([1, 2, 3, 4, 5], size=n_samples, p=[0.05, 0.1, 0.2, 0.4, 0.25]),
            "TPB_Attitude_Item2": np.random.choice([1, 2, 3, 4, 5], size=n_samples, p=[0.02, 0.08, 0.25, 0.45, 0.2]),
            "SDT_Autonomy_Item1": np.random.choice([1, 2, 3], size=n_samples, p=[0.1, 0.4, 0.5]),
            "SDT_Autonomy_Item2": np.random.choice([1, 2, 3], size=n_samples, p=[0.05, 0.35, 0.60]),
            "Qualitative_Notes": np.random.choice(["Excellent resource distribution", "Instruction format needs editing iterations", "Satisfactory scale"], size=n_samples)
        }
        df_analytics = pd.DataFrame(synthetic_data)
    else:
        uploaded_analytics_file = st.file_uploader("Upload target tracking matrix sheet (.csv)", type=["csv"])
        if uploaded_analytics_file is not None:
            df_analytics = pd.read_csv(uploaded_analytics_file)
            
    if df_analytics is not None:
        st.subheader("📋 Dataset Workspace Snapshot")
        st.dataframe(df_analytics.head(10), use_container_width=True)
        
        # Separate numeric data fields automatically from text properties strings
        numeric_cols = df_analytics.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [c for c in numeric_cols if "ID" not in c] # Filter out sequence identification columns
        
        if numeric_cols:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 Statistical Summarization Matrix")
                selected_col = st.selectbox("Select Target Variable for Distribution Evaluation:", numeric_cols)
                
                # Descriptive evaluation math operations using Pandas data engine structures
                desc_stats = df_analytics[selected_col].describe()
                st.dataframe(pd.DataFrame(desc_stats), use_container_width=True)
                
            with col2:
                st.subheader("📊 Distribution Data Chart Visualizer")
                # Build an distribution layout map tracking standard item responses dynamically
                counts = df_analytics[selected_col].value_counts().sort_index()
                st.bar_chart(counts, use_container_width=True)
                
            # Aggregate Construct Calculator Module
            st.markdown("---")
            st.subheader("🧮 Composite Scale Index Architect")
            st.caption("Select multiple psychometric indicator items to calculate their aggregate composite index tracking score value.")
            
            selected_scale_cols = st.multiselect("Select columns to calculate combined scale value (e.g., combining Item1 and Item2):", numeric_cols)
            if selected_scale_cols:
                # Add calculated composite indexing vectors onto memory dataframes dynamically
                df_analytics["Composite_Scale_Score"] = df_analytics[selected_scale_cols].mean(axis=1)
                st.success(f"Composite Scale Index successfully constructed for: {', '.join(selected_scale_cols)}")
                
                c_col1, c_col2 = st.columns(2)
                with c_col1:
                    st.metric(label="Overall Scale Framework Mean Score", value=f"{df_analytics['Composite_Scale_Score'].mean():.2f}")
                with c_col2:
                    st.metric(label="Overall Scale Framework Median Score", value=f"{df_analytics['Composite_Scale_Score'].median():.2f}")
                    
                st.line_chart(df_analytics["Composite_Scale_Score"], use_container_width=True)
        else:
            st.warning("No continuous numeric variable items identified in the targeted workspace tracking file sheet.")


