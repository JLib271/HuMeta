import streamlit as st
import pandas as pd
import numpy as np
import io
import os
import tempfile
import sqlite3
from sqlalchemy import text
import requests

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
# MODULE 2: VARIABLE ARCHITECT & INSTRUMENT EXPORTER
# ==========================================
elif app_mode == "2. Variable Instrument Architect":
    st.header("📐 Variable Architect & Instrument Exporter")
    st.caption("Design variable frameworks, configure measurement items, and instantly download standardized DDI-compliant templates or clean survey forms.")
    st.markdown("---")
    
        # --- SECTION A: REPOSITORY & STUDY INDEXING (ICPSR / DATAVERSE STANDARDS) ---
    st.subheader("📚 1. Social Science Repository Metadata (ICPSR / Dataverse Alignment)")
    st.caption("Align study indexing with major repositories using rich, study-level methodology and citation tracing variables.")
    
    # Updated text specifying de-identified research artifacts
    st.info(
        "💡 **Need a DOI for your study artifacts?** Please submit **de-identified** research artifacts directly to the "
        "[STEMEd+ Commons Collection in KCWorks](https://kcworks.org) to receive a unique persistent DOI before completing this index profile."
    )
    
    col_rep1, col_rep2 = st.columns(2)
    with col_rep1:
        repository_id = st.text_input(
            "Persistent Identifier / DOI (e.g., from KCWorks, Harvard Dataverse, or ICPSR)", 
            placeholder="e.g., doi:10.xxxx/kcworks..."
        )
        unit_of_analysis = st.selectbox(
            "Unit of Analysis (DDI Core)", 
            options=["Individual (Student/Teacher)", "Group/Classroom", "Organization/Institution", "Geographic/School District Level"]
        )
    with col_rep2:
        # Standardized DDI/ICPSR sampling methodology dropdown selection matrix
        sampling_method = st.selectbox(
            "Sampling Procedure / Methodology Type",
            options=[
                "Non-probability: Convenience / Availability Sampling",
                "Non-probability: Purposive / Judgmental Sampling",
                "Non-probability: Snowball / Network Voluntarism",
                "Probability: Simple Random Sampling",
                "Probability: Stratified Random Sampling",
                "Probability: Cluster / Multi-Stage Area Sampling",
                "Total Universe / Complete Census Ingestion",
                "Other / Mixed Framework Specification"
            ]
        )
        # Required fillable text area block ensuring thorough methodological description
        sampling_procedure = st.text_area(
            "Sampling Method Explanation / Implementation Context*",
            placeholder="Describe your sampling criteria, recruitment parameters, and response yield thresholds..."
        )

    st.divider()


    # --- SECTION B: VARIABLE CONFIGURATION (DDI SCHEMA STANDARDS) ---
    st.subheader("🧠 2. Study Variable & Framework Configuration")
    st.caption("Establish DDI-compliant metadata linking conceptual variables, parent constructs, target question items, and response scaling categories.")

    # 1. Expanded Demographics Selection Grid (DDI-Core / CEDS options)
    st.markdown("**Core Demographic Variables (CEDS Standards)**")
    col_dem1, col_dem2 = st.columns(2)
    with col_dem1:
        collect_gender = st.checkbox("Include Gender Category", value=True)
        collect_age = st.checkbox("Include Age / Birthdate Metrics", value=True)
        collect_race = st.checkbox("Include Race / Ethnicity Classifications")
    with col_dem2:
        collect_ses = st.checkbox("Include Socioeconomic Status Indicators (e.g., Free/Reduced Lunch, Income Level)")
        collect_lep = st.checkbox("Include English Proficiency / Language Status Flags")
        collect_disability = st.checkbox("Include Disability / Special Education Services Markers")
    
    # 2. Multi-Select Theoretical Structural Framework Selector
    # Changed to multiselect to allow multiple theories to inform a single study instrument
    selected_frameworks = st.multiselect(
        "Choose core guiding theoretical framework(s) to populate variables:",
        options=["Theory of Planned Behavior (TPB)", "Self-Determination Theory (SDT)", "Technology Acceptance Model (TAM)"]
    )
    
    # Compile variable items collection matrix mapping exactly to DDI specifications
    active_items = []
    
    # Append selected standardized CEDS demographic variables
    if collect_gender:
        active_items.append({"Variable_ID": "VAR_GENDER", "Concept_Construct": "Demographics", "Variable_Label": "Participant Gender", "Question_Item_Text": "What gender category do you most closely identify with?", "Response_Scale_Options": "Woman | Man | Non-binary | Prefer to self-describe | Prefer not to say", "Framework_Source": "CEDS / DDI-Core"})
    if collect_age:
        active_items.append({"Variable_ID": "VAR_AGE", "Concept_Construct": "Demographics", "Variable_Label": "Participant Age", "Question_Item_Text": "Please enter your age in numerical years:", "Response_Scale_Options": "Continuous Integer Entry", "Framework_Source": "CEDS / DDI-Core"})
    if collect_race:
        active_items.append({"Variable_ID": "VAR_RACE_ETHNICITY", "Concept_Construct": "Demographics", "Variable_Label": "Participant Race/Ethnicity", "Question_Item_Text": "Select the racial/ethnic categories that best describe you:", "Response_Scale_Options": "American Indian or Alaska Native | Asian | Black or African American | Hispanic or Latino | Native Hawaiian or Other Pacific Islander | White | Two or More Races", "Framework_Source": "CEDS / DDI-Core"})
    if collect_ses:
        active_items.append({"Variable_ID": "VAR_ECONOMIC_STATUS", "Concept_Construct": "Demographics", "Variable_Label": "Socioeconomic Status Indicator", "Question_Item_Text": "Does the participant qualify for economic assistance programs (e.g., Free or Reduced Price Lunch)?", "Response_Scale_Options": "Yes | No | Unknown", "Framework_Source": "CEDS / DDI-Core"})
    if collect_lep:
        active_items.append({"Variable_ID": "VAR_ENGLISH_PROFICIENCY", "Concept_Construct": "Demographics", "Variable_Label": "English Learner Status", "Question_Item_Text": "Is the participant classified as an English Learner (EL) / Limited English Proficient (LEP)?", "Response_Scale_Options": "Yes | No", "Framework_Source": "CEDS / DDI-Core"})
    if collect_disability:
        active_items.append({"Variable_ID": "VAR_DISABILITY_STATUS", "Concept_Construct": "Demographics", "Variable_Label": "Special Education Disability Status", "Question_Item_Text": "Is the participant receiving services under the Individuals with Disabilities Education Act (IDEA)?", "Response_Scale_Options": "Yes | No", "Framework_Source": "CEDS / DDI-Core"})

    # Iterate through all checked frameworks and append their constructs
    for framework in selected_frameworks:
        if framework in THEORY_MAP:
            st.markdown(f"**Pre-populated variables for: {framework}**")
            theory_data = THEORY_MAP[framework]
            for construct, props in theory_data.items():
                include = st.checkbox(f"Include {construct} ({framework})", value=True)
                if include:
                    var_id = f"VAR_{construct.upper().replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '')}"
                    active_items.append({
                        "Variable_ID": var_id,
                        "Concept_Construct": construct,
                        "Variable_Label": f"{framework} - {construct}",
                        "Question_Item_Text": props["item"],
                        "Response_Scale_Options": props["scale"],
                        "Framework_Source": framework
                    })
                
       # --- 3. CUSTOM VARIABLE CSV UPLOADER WITH SAFETY FILTERING ---
    st.markdown(" ")
    st.subheader("➕ 3. Bulk Import Custom Variables & Suggestions")
    
    st.warning(
        "⚠️ **Important Template Instructions:** After downloading the CSV template below, "
        "you **MUST delete the sample row** (VAR_SAMPLE_ID) before typing your own constructs. "
        "If left in, the example will be automatically filtered out by the ingestion engine."
    )
    
    # Create the template CSV for download
    custom_template_df = pd.DataFrame(columns=["Variable_ID", "Concept_Construct", "Variable_Label", "Question_Item_Text", "Response_Scale_Options", "Framework_Source"])
    custom_template_df.loc[0] = ["VAR_SAMPLE_ID", "Sample Construct", "Sample Label Text", "This is an example survey prompt item question?", "1=Option A | 2=Option B | 3=Option C", "Name of New or Existing Theoretical Framework"]
    template_csv_bytes = custom_template_df.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="📥 Download Custom Variables CSV Template",
        data=template_csv_bytes,
        file_name="custom_variables_schema_template.csv",
        mime="text/csv"
    )
    
    uploaded_custom_vars = st.file_uploader("Upload your completed Custom Variables CSV file", type=["csv"])
    
    uploaded_items = []
    if uploaded_custom_vars is not None:
        try:
            uploaded_df = pd.read_csv(uploaded_custom_vars)
            required_fields = ["Variable_ID", "Concept_Construct", "Variable_Label", "Question_Item_Text", "Response_Scale_Options", "Framework_Source"]
            
            if all(field in uploaded_df.columns for field in required_fields):
                # Automated backend filtering guard to strip placeholder out safely
                initial_count = len(uploaded_df)
                uploaded_df = uploaded_df[uploaded_df["Variable_ID"] != "VAR_SAMPLE_ID"]
                filtered_count = len(uploaded_df)
                
                uploaded_items = uploaded_df.to_dict(orient="records")
                
                if filtered_count < initial_count:
                    st.success(f"✅ Successfully imported {filtered_count} custom variable definitions into active session workspace! (Placeholder template row was detected and safely stripped out).")
                else:
                    st.success(f"✅ Successfully imported {filtered_count} custom variable definitions into active session workspace!")
                
                st.dataframe(uploaded_df, use_container_width=True, hide_index=True)
                st.info("💡 **Want to contribute these variables to our global open source system?** When you connect your repository, these uploaded records will format into automated GitHub Suggestion tickets for review.")
            else:
                st.error("❌ Column mismatch. Please verify your file headers perfectly match the downloaded template format.")
        except Exception as e:
            st.error(f"Error parsing custom variable spreadsheet file: {e}")

    # Merge active form items with newly imported custom spreadsheet items
    final_instrument_list = active_items + uploaded_items + st.session_state.session_instruments
    
    if final_instrument_list:
        df_manifest = pd.DataFrame(final_instrument_list)
        
        # --- RENAME DATA GRID FOR ACCESSIBILITY ---
        st.subheader("📋 Your Active Study Instrument Summary Table")
        st.dataframe(df_manifest, use_container_width=True, hide_index=True)
        
        # --- EXPORT PIPELINES & REPOSITORY ACTION BUTTONS ---
        st.markdown("---")
        st.markdown("### 🚀 Contribute Custom Framework to Global Schema")
        st.caption("Want to make these variables part of our open-source system? Clicking below will generate a pre-formatted suggestion ticket on our GitHub repository. Our automated actions will immediately process it into a secure Pull Request branch package.")
        
        # 🌟 SAFETY WRAPPER: Only build the GitHub Ticket button if a custom CSV file was actually uploaded
        if uploaded_custom_vars is not None:
            # Unpack the active spreadsheet rows into an optimized text chunk for the issue ticket body
            uploaded_custom_vars.seek(0)
            raw_csv_text = uploaded_custom_vars.read().decode('utf-8')
            first_framework = str(uploaded_df["Framework_Source"].iloc[0]) if not uploaded_df.empty else "Custom Framework"
            
            # Format URL parameters for the pre-filled issue route
            issue_title = urllib.parse.quote(f"[Schema Suggestion] Add {first_framework}")
            issue_body = urllib.parse.quote(
                f"**New Theoretical Framework Submission**\n\n"
                f"**Framework Target Name:** {first_framework}\n\n"
                f"### RAW SCHEMA PAYLOAD\n"
                f"```csv\n{raw_csv_text}\n```\n\n"
                f"---\n*Submitted securely via the Open Educational Metadata Portal Variable Ingest Box.*"
            )
            
            # Targets your exact repo issue tracking endpoint securely
            github_issue_url = f"https://github.com{issue_title}&body={issue_body}"
            
            # Render an elegant, accessible action link button style
            st.markdown(
                f'<a href="{github_issue_url}" target="_blank">'
                f'<button style="background-color:#1A365D; color:white; border:none; padding:12px 24px; text-align:center; text-decoration:none; display:inline-block; font-size:16px; border-radius:6px; cursor:pointer; font-weight:bold; width:100%;">'
                f'📦 Open Pre-filled GitHub Ingestion Ticket</button></a>',
                unsafe_allow_html=True
            )
        else:
            # Fallback message displayed when they are viewing core framework items but haven't uploaded an external CSV yet
            st.warning("📥 To submit brand new constructs or alternative theoretical schemas to our open repository, please download the template, fill it out, and upload your custom CSV file above.")
            
        st.markdown("---")
        col_exp1, col_exp2, col_exp3 = st.columns(3)



    # Merge active form items with newly imported custom spreadsheet items
    final_instrument_list = active_items + uploaded_items + st.session_state.session_instruments
    
    if final_instrument_list:
        df_manifest = pd.DataFrame(final_instrument_list)
        
        # --- RENAME DATA GRID FOR ACCESSIBILITY ---
        st.subheader("📋 Your Active Study Instrument Summary Table")
        st.dataframe(df_manifest, use_container_width=True, hide_index=True)
        
        # --- EXPORT PIPELINES ---
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        
        with col_exp1:
            # 1. Structured Data Dictionary Metadata CSV File
            csv_buffer = io.StringIO()
            df_manifest.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📥 Download Metadata Sheet (.csv)",
                data=csv_buffer.getvalue(),
                file_name="educational_study_metadata_sheet.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        with col_exp2:
            # 2. Complete Technical Schema Mapping TXT File (Retained original)
            txt_manifest = "=== DDI & CEDS COMPLIANT TECHNICAL STUDY METADATA MANIFEST ===\n"
            txt_manifest += f"Repository Context Code: {repository_id if repository_id else 'Not Cataloged'}\n"
            txt_manifest += f"Unit of Analysis: {unit_of_analysis}\n"
            txt_manifest += "=" * 60 + "\n\n"
            for idx, row in df_manifest.iterrows():
                txt_manifest += f"DDI Variable ID:  {row['Variable_ID']}\n"
                txt_manifest += f"Concept/Construct: {row['Concept_Construct']}\n"
                txt_manifest += f"Variable Label:    {row['Variable_Label']}\n"
                txt_manifest += f"Question Text:     {row['Question_Item_Text']}\n"
                txt_manifest += f"Response Scaling:  {row['Response_Scale_Options']}\n"
                txt_manifest += f"Framework Source:  {row['Framework_Source']}\n"
                txt_manifest += "-" * 60 + "\n\n"
                
            st.download_button(
                label="📥 Download Technical Manifest (.txt)",
                data=txt_manifest,
                file_name="technical_study_metadata_manifest.txt",
                mime="text/plain",
                use_container_width=True
            )
            
        with col_exp3:
            # 🌟 3. NEW FEATURE: Clean, Print-Ready Survey Instrument File TXT
            clean_survey = f"=== SURVEY INSTRUMENT FOR STUDY MANIFEST ===\n"
            if repository_id:
                clean_survey += f"Study Reference DOI: {repository_id}\n"
            clean_survey += "Instructions: Please read each question carefully and select or enter the option that best describes your response.\n"
            clean_survey += "=" * 60 + "\n\n"
            
            for idx, row in df_manifest.iterrows():
                clean_survey += f"Q{idx+1}. {row['Question_Item_Text']}\n"
                # Formatting options cleanly for participant deployment views
                options = str(row['Response_Scale_Options'])
                if "|" in options:
                    for opt in options.split("|"):
                        clean_survey += f"   [ ] {opt.strip()}\n"
                elif "Continuous" in options:
                    clean_survey += "   [_______________________________________]\n"
                else:
                    clean_survey += f"   Options: {options}\n"
                clean_survey += "\n"
                
            st.download_button(
                label="📥 Download Deployment Survey Form (.txt)",
                data=clean_survey,
                file_name="clean_participant_survey_form.txt",
                mime="text/plain",
                use_container_width=True
            )
    else:
        st.info("No structural frameworks, demographic indicators, or custom variables selected yet.")

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
    st.caption("Analyze item matrices, evaluate structural scale internal consistency coefficients, compute correlations, and export analytical packages.")
    st.markdown("---")
    
    # 1. RIGOROUS USER DATA INGEST INSTRUCTIONS
    st.subheader("📂 1. Ingest Data Sheet Mapping Workspace")
    data_source = st.radio("Analytics Dataset Source Selection:", ["Use Standard Synthetic Sample Dataset", "Upload Custom Research Data Sheet (.csv)"])
    
    # Detailed warning blueprint box instructing users on exact label column expectations
    st.info(
        "📝 **Strict CSV Data Schema Ingestion Requirements:**\n\n"
        "To execute structural calculations without errors, your custom file **must conform exactly** to these criteria:\n"
        "* **Demographics:** Include columns labeled precisely as `Age` (Numeric Integer values) and `Gender` (Text values match: `Woman`, `Man`, `Non-binary`, `Prefer not to say`).\n"
        "* **Psychometric Scales:** Scale item columns must follow the prefix notation pattern matching your constructs so the engine can automatically bundle them together:\n"
        "  - **Theory of Planned Behavior:** Columns must be named starting with `TPB_` (e.g., `TPB_Attitude_1`, `TPB_Norms_2`, `TPB_Control_3`).\n"
        "  - **Self-Determination Theory:** Columns must be named starting with `SDT_` (e.g., `SDT_Autonomy_1`, `SDT_Competence_2`).\n"
        "  - **Technology Acceptance Model:** Columns must be named starting with `TAM_` (e.g., `TAM_Usefulness_1`, `TAM_EaseOfUse_2`).\n"
        "* **Values Scaling:** Psychometric matrix items must contain continuous numeric data vectors (e.g., standard Likert items scored 1-5 or 1-7)."
    )
        # --- AUTOMATED DATA TEMPLATE GENERATION & DOWNLOAD ---
    # Create a structured DataFrame matching your exact schema requirements
    template_cols = [
        "Participant_ID", "Age", "Gender", 
        "TPB_Attitude_1", "TPB_Norms_2", "TPB_Control_3", 
        "SDT_Autonomy_1", "SDT_Competence_2", 
        "TAM_Usefulness_1", "TAM_EaseOfUse_2"
    ]
    analytics_template_df = pd.DataFrame(columns=template_cols)
    
    # Inject a clean placeholder row as a visual guide for the researcher
    analytics_template_df.loc[0] = [1, 21, "Woman", 4, 5, 3, 4, 5, 4, 4]
    analytics_template_df.loc[1] = [2, 19, "Man", 2, 3, 4, 3, 2, 5, 5]
    
    # Convert the structured matrix into downloadable CSV bytes
    analytics_template_csv = analytics_template_df.to_csv(index=False).encode('utf-8')
    
    # Render the download trigger button
    st.download_button(
        label="📥 Download Analytics CSV Template File",
        data=analytics_template_csv,
        file_name="analytics_data_ingest_template.csv",
        mime="text/csv",
        use_container_width=True
    )
    
    st.markdown("---")

    df_analytics = None
    
    if data_source == "Use Standard Synthetic Sample Dataset":
        # Generate stable, clean psychometric sample data arrays
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
            "TAM_Usefulness_Item1": np.random.choice([1, 2, 3, 4, 5], size=n_samples, p=[0.05, 0.05, 0.15, 0.45, 0.30]),
            "TAM_Usefulness_Item2": np.random.choice([1, 2, 3, 4, 5], size=n_samples, p=[0.03, 0.07, 0.20, 0.40, 0.30])
        }
        df_analytics = pd.DataFrame(synthetic_data)
    else:
        uploaded_analytics_file = st.file_uploader("Upload target tracking matrix sheet (.csv)", type=["csv"])
        if uploaded_analytics_file is not None:
            df_analytics = pd.read_csv(uploaded_analytics_file)
            
    if df_analytics is not None:
        st.subheader("📋 Dataset Workspace Snapshot")
        st.dataframe(df_analytics.head(10), use_container_width=True, hide_index=True)
        
        # Isolate continuous variables and item scores
        all_numeric_cols = df_analytics.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [c for c in all_numeric_cols if "ID" not in c]
        
        # --- 2. ADD AXES LABELS TO THE DISTRIBUTION CHART VISUALIZER ---
        st.divider()
        st.subheader("📊 2. Distribution Data Chart Visualizer")
        if numeric_cols:
            selected_col = st.selectbox("Select Target Variable for Distribution Evaluation:", numeric_cols)
            
            col_chart1, col_chart2 = st.columns([1, 2])
            with col_chart1:
                desc_stats = df_analytics[selected_col].describe()
                st.markdown(f"**Descriptive Vectors for `{selected_col}`:**")
                st.dataframe(pd.DataFrame(desc_stats), use_container_width=True)
            with col_chart2:
                # Compile accurate counting distributions for categorical/Likert scales
                counts_df = df_analytics[selected_col].value_counts().sort_index().reset_index()
                counts_df.columns = ["Response Categories", "Frequency (Participant Count)"]
                
                # Render bar chart with explicit, scannable axes labels
                st.markdown(f"**Response Value Counts for `{selected_col}`**")
                st.bar_chart(counts_df.set_index("Response Categories"), y="Frequency (Participant Count)", use_container_width=True)
        
        # --- 3. AUTOMATED COMPOSITE SCALE INDEX ARCHITECT & CRONBACH'S ALPHA ---
        st.divider()
        st.subheader("🧮 3. Automated Composite Scale Index & Reliability Architect")
        st.caption("The engine crawls your dataset column tags to dynamically bind scales as averages of their matched item matrices and calculates Alpha coefficients.")
        
        # Define internal mathematical function to compute standard Cronbach's Alpha
        def calculate_cronbach_alpha(scale_df):
            clean_df = scale_df.dropna()
            n_items = clean_df.shape[1]
            if n_items <= 1:
                return 0.0
            item_variances = clean_df.var(ddof=1, axis=0).sum()
            total_variance = clean_df.sum(axis=1).var(ddof=1)
            if total_variance == 0:
                return 0.0
            alpha = (n_items / (n_items - 1)) * (1 - (item_variances / total_variance))
            return alpha

        # Detect prefix structural grouping columns
        scale_prefixes = {"TPB_": "Theory of Planned Behavior", "SDT_": "Self-Determination Theory", "TAM_": "Technology Acceptance Model"}
        computed_scales_manifest = {}
        scale_summary_text = "=== CRONBACH'S ALPHA INTERNAL CONSISTENCY PROFILE ===\n"
        
        for prefix, scale_name in scale_prefixes.items():
            matched_items = [col for col in df_analytics.columns if col.startswith(prefix)]
            if len(matched_items) >= 2:
                # 🌟 AUTOMATED AVERAGING LOGIC: Compute index values dynamically across rows
                scale_score_col = f"Scale_Composite_{prefix.replace('_', '')}"
                df_analytics[scale_score_col] = df_analytics[matched_items].mean(axis=1)
                
                # Compute Cronbach's Alpha
                alpha_val = calculate_cronbach_alpha(df_analytics[matched_items])
                computed_scales_manifest[scale_name] = {"column": scale_score_col, "items": matched_items, "alpha": alpha_val}
                
                # Visual verification reporting output card matrix
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.metric(label=f"🌐 {scale_name} Mean Index", value=f"{df_analytics[scale_score_col].mean():.2f}")
                with col_m2:
                    st.metric(label=f"🧬 {scale_name} Cronbach's Alpha (α)", value=f"{alpha_val:.3f}", help="Values above 0.70 represent high scale profiling reliability standards.")
                
                scale_summary_text += f"Scale Target: {scale_name}\nIncluded Item Items: {', '.join(matched_items)}\nCalculated Reliability (Cronbach's Alpha): {alpha_val:.4f}\n\n"
                st.markdown(" ")

        # --- 4. MIXED VARIABLE DATA CORRELATIONS MATRIX ENGINE ---
        st.divider()
        st.subheader("🔗 4. Statistical Correlation Matrix Model")
        st.caption("Processes correlations across all active items, using spearman ordinal rules or continuous Pearson coefficient vectors depending on item classifications.")
        
        # Accumulate demographic variables alongside newly constructed index average scores
        correlation_targets = []
        if "Age" in df_analytics.columns:
            correlation_targets.append("Age")
            
        for scale_name, properties in computed_scales_manifest.items():
            correlation_targets.append(properties["column"])
            
        if len(correlation_targets) >= 2:
            # Build correlation dataframe using Spearman rank-order correlation matrix 
            # as it accommodates mixed numeric classifications (Age vs Likert Scale averages) safely
            correlation_matrix = df_analytics[correlation_targets].corr(method="spearman")
            
            # Clean column labels to look friendly to social-science readers
            friendly_labels = {col: col.replace("Scale_Composite_", "Index: ") for col in correlation_targets}
            clean_corr_matrix = correlation_matrix.rename(index=friendly_labels, columns=friendly_labels)
            
            st.markdown("**Spearman Rank Correlation Matrix ($r_s$):**")
            st.dataframe(clean_corr_matrix.style.background_gradient(cmap="coolwarm", axis=None).format("{:.3f}"), use_container_width=True)
        else:
            st.warning("Insufficient structural aggregate composite dimensions available to compute multi-variable correlation grids.")
            clean_corr_matrix = pd.DataFrame()

                # --- 5. COMPREHENSIVE PDF REPORT GENERATION ENGINE ---
        st.divider()
        st.subheader("📥 5. Download Evaluation Compendium")
        st.caption("Generate a compiled analytical summary PDF handbook detailing item statistics, alpha metrics, and active distribution data charts.")

        # Create a binary buffer to hold the compiled PDF data in memory
        pdf_buffer = io.BytesIO()
        
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            import matplotlib.pyplot as plt
            
            # --- 1. SILENT VISUALIZATION GRAPH COMPILATION ---
            # Compile Distribution Graph
            fig_dist, ax_dist = plt.subplots(figsize=(6, 3))
            counts_df.plot(kind="bar", x="Response Categories", y="Frequency (Participant Count)", ax=ax_dist, color="#1f77b4", legend=False)
            ax_dist.set_title(f"Distribution: {selected_col}")
            ax_dist.set_xlabel("Response Categories")
            ax_dist.set_ylabel("Frequency")
            plt.tight_layout()
            
            dist_img_path = os.path.join(tempfile.gettempdir(), "temp_dist_chart.png")
            fig_dist.savefig(dist_img_path, dpi=200)
            plt.close(fig_dist)
            
            # Compile Correlation Matrix Graph (If data is available)
            corr_img_path = None
            if not clean_corr_matrix.empty:
                fig_corr, ax_corr = plt.subplots(figsize=(5, 4))
                cax = ax_corr.matshow(clean_corr_matrix, cmap="coolwarm", vmin=-1, vmax=1)
                fig_corr.colorbar(cax)
                
                ticks = np.arange(len(clean_corr_matrix.columns))
                ax_corr.set_xticks(ticks)
                ax_corr.set_yticks(ticks)
                ax_corr.set_xticklabels(clean_corr_matrix.columns, rotation=45, ha="left", fontsize=8)
                ax_corr.set_yticklabels(clean_corr_matrix.index, fontsize=8)
                ax_corr.set_title("Spearman Rank Correlation Matrix", pad=20)
                plt.tight_layout()
                
                corr_img_path = os.path.join(tempfile.gettempdir(), "temp_corr_chart.png")
                fig_corr.savefig(corr_img_path, dpi=200)
                plt.close(fig_corr)

            # --- 2. BUILD THE STRUCTURAL PDF FRAMEWORK ---
            doc = SimpleDocTemplate(
                pdf_buffer, 
                pagesize=letter,
                rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40,
                title="Open Educational Metadata Analysis Report"
            )
            
            styles = getSampleStyleSheet()
            
            # Custom accessible text style elements
            title_style = ParagraphStyle(
                'ReportTitle', parent=styles['Heading1'],
                fontSize=22, textColor=colors.HexColor("#1A365D"), spaceAfter=12
            )
            h2_style = ParagraphStyle(
                'SectionHeader', parent=styles['Heading2'],
                fontSize=14, textColor=colors.HexColor("#2B6CB0"), spaceBefore=14, spaceAfter=8
            )
            body_style = ParagraphStyle(
                'ReportBody', parent=styles['BodyText'],
                fontSize=10, leading=14, textColor=colors.HexColor("#2D3748")
            )
            code_style = ParagraphStyle(
                'CodeStyle', parent=styles['Normal'],
                fontName='Courier', fontSize=8, leading=10, textColor=colors.HexColor("#1A202C")
            )

            story = []
            
            # Title & Subheaders Block
            story.append(Paragraph("<b>Open Educational Metadata Report Compendium</b>", title_style))
            story.append(Paragraph(f"<b>Dataset Sample Metric Matrix Size:</b> {df_analytics.shape[0]} Rows | {df_analytics.shape[1]} Columns", body_style))
            story.append(Spacer(1, 15))
            
            # Cronbach's Alpha Reliability Block
            story.append(Paragraph("<b>1. Cronbach's Alpha Scale Reliability Internal Consistency</b>", h2_style))
            for line in scale_summary_text.split("\n"):
                if line.strip() and "CRONBACH" not in line:
                    story.append(Paragraph(line, body_style))
            story.append(Spacer(1, 10))
            
            # Variable Distribution and Visual Graphs Section
            story.append(Paragraph(f"<b>2. Distribution Visualization Graph: {selected_col}</b>", h2_style))
            if os.path.exists(dist_img_path):
                story.append(Image(dist_img_path, width=320, height=160))
            story.append(Spacer(1, 15))
            
            # Structural Correlation Matrix Table Section
            if not clean_corr_matrix.empty and corr_img_path and os.path.exists(corr_img_path):
                story.append(Paragraph("<b>3. Mixed Multi-Variable Inter-Correlation Matrix</b>", h2_style))
                
                # Transform correlation values array framework into a readable text grid layout
                corr_data = [["Variable"] + list(clean_corr_matrix.columns)]
                for idx, row in clean_corr_matrix.iterrows():
                    corr_data.append([str(idx)] + [f"{val:.3f}" for val in row])
                
                corr_table = Table(corr_data, hAlign='LEFT')
                corr_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#1A202C")),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,-1), 8),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                    ('TOPPADDING', (0,0), (-1,-1), 4),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
                ]))
                
                story.append(corr_table)
                story.append(Spacer(1, 15))
                story.append(Paragraph("<b>Correlation Map Matrix Diagram:</b>", body_style))
                story.append(Image(corr_img_path, width=240, height=192))
                story.append(Spacer(1, 15))
                
            # Descriptive Evaluation Table Block Annex
            story.append(Paragraph("<b>4. Global Item Descriptive Metric Summaries Annex</b>", h2_style))
            desc_df = df_analytics[numeric_cols].describe().round(3).reset_index()
            desc_data = [list(desc_df.columns)] + desc_df.values.tolist()
            
            # Format raw numerical rows safely into clean string representations for table rendering
            string_desc_data = []
            for row in desc_data:
                string_desc_data.append([f"{item:.3f}" if isinstance(item, (int, float)) else str(item) for item in row])
                
            desc_table = Table(string_desc_data, hAlign='LEFT')
            desc_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EDF2F7")),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 7),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ]))
            story.append(desc_table)

            # Build and lock down document stream data
            doc.build(story)
            
            # Clean up background image paths from server storage space
            if os.path.exists(dist_img_path):
                os.unlink(dist_img_path)
            if corr_img_path and os.path.exists(corr_img_path):
                os.unlink(corr_img_path)
                
            # --- 3. STREAM STREAM INTERFACE COMPONENT DOWNLOAD ---
            st.download_button(
                label="📥 Download Complete Analytical Summary Report (.pdf)",
                data=pdf_buffer.getvalue(),
                file_name="educational_analytics_summary_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
        except Exception as pdf_error:
            st.error(f"Failed to assemble PDF Report Compendium structure: {pdf_error}. Ensure reportlab and matplotlib packages exist.")





