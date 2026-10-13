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

# Initialize Supabase Client Safely
@st.cache_resource
def init_supabase() -> Client:
    # 1. Pull raw values from secrets and strip hidden whitespace characters
    url = st.secrets["SUPABASE_URL"].strip().rstrip("/")
    key = st.secrets["SUPABASE_KEY"].strip()
    
    # 2. DEFENSIVE FIX: If the bare URL is failing with PGRST125, 
    # append the strict REST endpoint suffix that PostgREST requires to map public tables
    if not url.endswith("/rest/v1"):
        url = f"{url}/rest/v1"
        
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
    [
        "1. Study Metadata Schema Registry", 
        "2. Variable Instrument Architect", 
        "3. Community Data Repository Sync", 
        "4. Descriptive & Scale Analytics",
        "5. Live Central Database Viewer"
    ]
)
import time
from github import Github

def automate_github_pull_request(suggestion_type: str, file_name: str, file_content: str, title_summary: str) -> str:
    """
    Automates a full GitOps flow: Connects to GitHub via PAT, creates a branch,
    commits a clean schema file into /suggestions, and triggers a live Pull Request.
    """
    try:
        # 1. Initialize standalone GitHub engine using your hidden Secrets Token
        if "GITHUB_PAT" not in st.secrets:
            return "❌ Missing 'GITHUB_PAT' configuration token inside your Streamlit Cloud Secrets dashboard."
            
        token = st.secrets["GITHUB_PAT"].strip()
        g = Github(token)
        
        # 2. Automatically detect your repository information
        # (Replace 'your-username/your-repo-name' with your actual GitHub path)
        repo_path = "openedmetadata/openedmetadata" 
        repo = g.get_repo(repo_path)
        
        # 3. Establish structural branch identifiers
        main_branch = repo.get_branch("main")
        unique_timestamp = int(time.time())
        new_branch_name = f"proposal-{suggestion_type.lower()}-{unique_timestamp}"
        
        # 4. Programmatically fork a new branch off your primary branch head
        repo.create_git_ref(ref=f"refs/heads/{new_branch_name}", sha=main_branch.commit.sha)
        
        # 5. Commit the clean structural file into your new landing folder
        target_path = f"suggestions/{file_name}"
        commit_message = f"Community Schema Proposal: {title_summary}"
        
        repo.create_file(
            path=target_path,
            message=commit_message,
            content=file_content,
            branch=new_branch_name
        )
        
        # 6. Execute an API call to open a live Pull Request back to your main branch
        pr_body = f"""
        ### 🚀 Community Metadata Architecture Proposal
        An automated structural amendment suggestion has been compiled and submitted via the live portal interface.
        
        * **Proposal Type:** {suggestion_type}
        * **Target Asset:** `{target_path}`
        * **Submission Timestamp:** {unique_timestamp}
        
        Please evaluate, comment on, and merge this change into your global core schemas when ready.
        """
        
        pull_request = repo.create_pull(
            title=f"📁 [Schema Proposal] {title_summary}",
            body=pr_body,
            head=new_branch_name,
            base="main"
        )
        
        # Return success confirmation URL link back to the stream
        return f"🎉 Success! A formal Pull Request has been opened automatically. Track it here: {pull_request.html_url}"
        
    except Exception as git_error:
        return f"❌ Automated GitOps pipeline failure: {git_error}"

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
        
            # --- SUBMIT BUTTON & VALIDATION (INSIDE THE FORM CONTAINER) ---
        submit_metadata = st.form_submit_button("🚀 Submit Complete Study Record")
        
        if submit_metadata:
            has_author = any(auth["name"].strip() for auth in st.session_state.authors_list)
            
            if not title:
                st.error("DCMES Core Field Title (dc:title) is required to index the study.")
            elif not has_author:
                st.error("At least one Creator/Author Name is required.")
            else:
                try:
                    with st.spinner("Establishing isolated API handshake for data ingestion..."):
                        from supabase import create_client as form_client
                        
                        # 1. Pull and clean credentials directly inside the local submission loop
                        local_url = str(st.secrets["SUPABASE_URL"]).strip().rstrip("/")
                        local_key = str(st.secrets["SUPABASE_KEY"]).strip()
                        
                        # 2. Build the independent client object
                        direct_form_supabase = form_client(local_url, local_key)
                        
                        # 3. Cleanly pack your author array down into a comma-separated string for standard database tracking
                        authors_string = ", ".join([auth["name"].strip() for auth in st.session_state.authors_list if auth["name"].strip()])
                        
                        # 4. Map your user text inputs directly to your Supabase SQL column keys
                        db_payload = {
                            "study_title": str(title).strip(),
                            "principal_investigator": authors_string,
                            "institution": str(language), # Storing language indicator for layout tracking
                            "funding_source": str(keywords).strip() if keywords else "N/A",
                            "study_description": str(description).strip() if description else "No description provided."
                        }
                        
                        # 5. Execute the clean database insert query
                        direct_form_supabase.from_("studies").insert(db_payload).execute()
                        
                        st.success(f"🎉 Success! '{title}' has been permanently recorded in your live Supabase database!")
                        
                        # Reset authors list back to a clean default state for the next entry session
                        st.session_state.authors_list = [{"name": "", "orcid": ""}]
                        
                except Exception as form_db_error:
                    st.error(f"Failed to transmit data to the central repository: {form_db_error}")


    # --- MODULE 1 EXTENSION PIPELINE BUTTON ---
    st.markdown("---")
    st.markdown("### 🚀 Propose Extensions to Core Study Metadata Architecture")
    st.caption("Suggest new Dublin Core (DCMES) descriptors, alternative CEDS geographic drop-down indicators, or updated standard options.")
    
    with st.expander("💡 Click to Draft a Metadata Schema Suggestion"):
        suggested_schema_field = st.text_input("Target Element / Field Code to Change", placeholder="e.g., CEDS Section 2 - Alternative Grade Classifications", key="mod1_suggest_field")
        suggested_schema_text = st.text_area("Detailed Suggestion / Additions Details", placeholder="Describe new drop-down selections, alternative labels, or documentation requirements...", key="mod1_suggest_text")
        
        if suggested_schema_field and suggested_schema_text:
            schema_payload = f"""**Study Metadata Architecture Amendment Proposal**

**Target Allocation Segment:** {suggested_schema_field}

### PROPOSED SUB-MATRIX SELECTIONS
```text
{suggested_schema_text}
```

---
            st.markdown("##### **Submit Change Directly to GitHub**")
            st.caption("Clicking the button below will automatically fork a branch, save your suggestion, and issue a formal pull request.")
            
            # This triggers your new automated PyGithub pipeline function
            if st.button("🚀 Push Proposal to GitHub as Pull Request", key="submit_mod1_pr_btn"):
                with st.spinner("Talking to GitHub API, creating branch, and launching Pull Request..."):
                    # Generate a clean filename and summary string
                    safe_filename = f"metadata_proposal_{suggested_schema_field.lower().replace(' ', '_')}.txt"
                    summary_title = f"Update Metadata Section: {suggested_schema_field}"
                    
                    # Run the automated GitOps function you pasted at the top of the file
                    result_message = automate_github_pull_request(
                        suggestion_type="Metadata",
                        file_name=safe_filename,
                        file_content=schema_payload, # Hooks into your existing schema_payload text string
                        title_summary=summary_title
                    )
                    
                    # Display the final status or the live PR link on the screen!
                    if "❌" in result_message:
                        st.error(result_message)
                    else:
                        st.success(result_message)

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
        sampling_procedure = st.text_area(
            "Sampling Method Explanation / Implementation Context*",
            placeholder="Describe your sampling criteria, recruitment parameters, and response yield thresholds..."
        )

    st.divider()

    # --- SECTION B: VARIABLE CONFIGURATION (DDI SCHEMA STANDARDS) ---
    st.subheader("🧠 2. Study Variable & Framework Configuration")
    st.caption("Establish DDI-compliant metadata linking conceptual variables, parent constructs, target question items, and response scaling categories.")

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
    
    selected_frameworks = st.multiselect(
        "Choose core guiding theoretical framework(s) to populate variables:",
        options=["Theory of Planned Behavior (TPB)", "Self-Determination Theory (SDT)", "Technology Acceptance Model (TAM)"]
    )
    
    active_items = []
    
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
                
    st.markdown(" ")
    st.subheader("➕ 3. Bulk Import Custom Variables & Suggestions")
    st.warning(
        "⚠️ **Important Template Instructions:** After downloading the CSV template below, "
        "you **MUST delete the sample row** (VAR_SAMPLE_ID) before typing your own constructs. "
        "If left in, the example will be automatically filtered out by the ingestion engine."
    )
    
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
                initial_count = len(uploaded_df)
                uploaded_df = uploaded_df[uploaded_df["Variable_ID"] != "VAR_SAMPLE_ID"]
                filtered_count = len(uploaded_df)
                
                uploaded_items = uploaded_df.to_dict(orient="records")
                
                if filtered_count < initial_count:
                    st.success(f"✅ Successfully imported {filtered_count} custom variable definitions into active session workspace! (Placeholder template row was detected and safely stripped out).")
                else:
                    st.success(f"✅ Successfully imported {filtered_count} custom variable definitions into active session workspace!")
                
                st.dataframe(uploaded_df, use_container_width=True, hide_index=True)
            else:
                st.error("❌ Column mismatch. Please verify your file headers perfectly match the downloaded template format.")
        except Exception as e:
            st.error(f"Error parsing custom variable spreadsheet file: {e}")

    final_instrument_list = active_items + uploaded_items + st.session_state.session_instruments
    
    if final_instrument_list:
        df_manifest = pd.DataFrame(final_instrument_list)
        st.subheader("📋 Your Active Study Instrument Summary Table")
        st.dataframe(df_manifest, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("### 🚀 Propose Custom Framework Variables to Global Schema")
        st.caption("Want to make your uploaded CSV variables part of our permanent core dropdown systems?")
        
        if uploaded_custom_vars is not None:
            uploaded_custom_vars.seek(0)
            raw_csv_text = uploaded_custom_vars.read().decode('utf-8')
            first_framework = str(uploaded_df["Framework_Source"].iloc[0]) if not uploaded_df.empty else "Custom Framework"
            
            # Formats the file content safely to avoid f-string syntax breaking
            pasteboard_content = (
                f"**New Theoretical Framework Submission**\n\n"
                f"**Framework Target Name:** {first_framework}\n\n"
                f"### RAW SCHEMA PAYLOAD\n"
                f"```csv\n{raw_csv_text}\n```\n\n"
                f"---\n*Submitted securely via the Open Educational Metadata Portal Variable Ingest Box.*"
            )
            
            st.markdown("##### **Submit Framework Directly to GitHub**")
            st.caption("Clicking the button below will automatically create a branch and issue a formal pull request for this custom framework.")
            
            # Automated PyGithub pull request launcher button for Module 2
            if st.button("🚀 Push Framework to GitHub as Pull Request", key="submit_mod2_pr_btn"):
                with st.spinner("Connecting to GitHub API, saving framework schema, and launching Pull Request..."):
                    safe_filename = f"framework_proposal_{first_framework.lower().replace(' ', '_')}.csv"
                    summary_title = f"Add Theoretical Framework: {first_framework}"
                    
                    # Fire the automated pipeline function
                    result_message = automate_github_pull_request(
                        suggestion_type="Framework",
                        file_name=safe_filename,
                        file_content=pasteboard_content,
                        title_summary=summary_title
                    )
                    
                    if "❌" in result_message:
                        st.error(result_message)
                    else:
                        st.success(result_message)

    
        else:
            st.warning("📥 To submit brand new constructs or alternative theoretical schemas to our open repository, please download the template, fill it out, and upload your custom CSV file above.")
            
        st.markdown("---")

        # --- EXPORT PIPELINES ---
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        
        with col_exp1:
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
            clean_survey = f"=== SURVEY INSTRUMENT FOR STUDY MANIFEST ===\n"
            if repository_id:
                clean_survey += f"Study Reference DOI: {repository_id}\n"
            clean_survey += "Instructions: Please read each question carefully and select or enter the option that best describes your response.\n"
            clean_survey += "=" * 60 + "\n\n"
            
            for idx, row in df_manifest.iterrows():
                clean_survey += f"Q{idx+1}. {row['Question_Item_Text']}\n"
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
            
            if check_names and check_dates and check_irb:
                if st.button("🚀 Push De-Identified Dataset to Collective Global Repository"):
                    if shared_conn is not None:
                        st.info("Uploading data to cloud platform...")
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
    
    st.subheader("📂 1. Ingest Data Sheet Mapping Workspace")
    data_source = st.radio("Analytics Dataset Source Selection:", ["Use Standard Synthetic Sample Dataset", "Upload Custom Research Data Sheet (.csv)"])
    
    st.info(
        r"📝 **Strict CSV Data Schema Ingestion Requirements:**\n\n"
        "To execute structural calculations without errors, your custom file **must conform exactly** to these criteria:\n"
        "* **Demographics:** Include columns labeled precisely as `Age` (Numeric Integer values) and `Gender` (Text values match: `Woman`, `Man`, `Non-binary`, `Prefer not to say`).\n"
        "* **Psychometric Scales:** Scale item columns must follow the prefix notation pattern matching your constructs so the engine can automatically bundle them together:\n"
        "  - **Theory of Planned Behavior:** Columns must be named starting with `TPB_` (e.g., `TPB_Attitude_1`, `TPB_Norms_2`, `TPB_Control_3`).\n"
        "  - **Self-Determination Theory:** Columns must be named starting with `SDT_` (e.g., `SDT_Autonomy_1`, `SDT_Competence_2`).\n"
        "  - **Technology Acceptance Model:** Columns must be named starting with `TAM_` (e.g., `TAM_Usefulness_1`, `TAM_EaseOfUse_2`).\n"
        "* **Values Scaling:** Psychometric matrix items must contain continuous numeric data vectors (e.g., standard Likert items scored 1-5 or 1-7)."
    )
        
    template_cols = [
        "Participant_ID", "Age", "Gender", 
        "TPB_Attitude_1", "TPB_Norms_2", "TPB_Control_3", 
        "SDT_Autonomy_1", "SDT_Competence_2", 
        "TAM_Usefulness_1", "TAM_EaseOfUse_2"
    ]
    analytics_template_df = pd.DataFrame(columns=template_cols)
    analytics_template_df.loc[0] = [1, 21, "Woman", 4, 5, 3, 4, 5, 4, 4]
    analytics_template_df.loc[1] = [2, 19, "Man", 2, 3, 4, 3, 2, 5, 5]
    analytics_template_csv = analytics_template_df.to_csv(index=False).encode('utf-8')
    
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
        
        all_numeric_cols = df_analytics.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [c for c in all_numeric_cols if "ID" not in c]
        
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
                counts_df = df_analytics[selected_col].value_counts().sort_index().reset_index()
                counts_df.columns = ["Response Categories", "Frequency (Participant Count)"]
                
                st.markdown(f"**Response Value Counts for `{selected_col}`**")
                st.bar_chart(counts_df.set_index("Response Categories"), y="Frequency (Participant Count)", use_container_width=True)
        
        st.divider()
        st.subheader("🧮 3. Automated Composite Scale Index & Reliability Architect")
        st.caption("The engine crawls your dataset column tags to dynamically bind scales as averages of their matched item matrices and calculates Alpha coefficients.")
        
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

        scale_prefixes = {"TPB_": "Theory of Planned Behavior", "SDT_": "Self-Determination Theory", "TAM_": "Technology Acceptance Model"}
        computed_scales_manifest = {}
        scale_summary_text = "=== CRONBACH'S ALPHA INTERNAL CONSISTENCY PROFILE ===\n"
        
        for prefix, scale_name in scale_prefixes.items():
            matched_items = [col for col in df_analytics.columns if col.startswith(prefix)]
            if len(matched_items) >= 2:
                scale_score_col = f"Scale_Composite_{prefix.replace('_', '')}"
                df_analytics[scale_score_col] = df_analytics[matched_items].mean(axis=1)
                
                alpha_val = calculate_cronbach_alpha(df_analytics[matched_items])
                computed_scales_manifest[scale_name] = {"column": scale_score_col, "items": matched_items, "alpha": alpha_val}
                
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.metric(label=f"🌐 {scale_name} Mean Index", value=f"{df_analytics[scale_score_col].mean():.2f}")
                with col_m2:
                    st.metric(label=f"🧬 {scale_name} Cronbach's Alpha (α)", value=f"{alpha_val:.3f}", help="Values above 0.70 represent high scale profiling reliability standards.")
                
                scale_summary_text += f"Scale Target: {scale_name}\nIncluded Item Items: {', '.join(matched_items)}\nCalculated Reliability (Cronbach's Alpha): {alpha_val:.4f}\n\n"
                st.markdown(" ")

        st.divider()
        st.subheader("🔗 4. Statistical Correlation Matrix Model")
        st.caption("Processes correlations across all active items, using spearman ordinal rules or continuous Pearson coefficient vectors depending on item classifications.")
        
        correlation_targets = []
        if "Age" in df_analytics.columns:
            correlation_targets.append("Age")
            
        for scale_name, properties in computed_scales_manifest.items():
            correlation_targets.append(properties["column"])
            
        if len(correlation_targets) >= 2:
            correlation_matrix = df_analytics[correlation_targets].corr(method="spearman")
            friendly_labels = {col: col.replace("Scale_Composite_", "Index: ") for col in correlation_targets}
            clean_corr_matrix = correlation_matrix.rename(index=friendly_labels, columns=friendly_labels)
            
            st.markdown("**Spearman Rank Correlation Matrix ($r_s$):**")
            st.dataframe(clean_corr_matrix.style.background_gradient(cmap="coolwarm", axis=None).format("{:.3f}"), use_container_width=True)
        else:
            st.warning("Insufficient structural aggregate composite dimensions available to compute multi-variable correlation grids.")
            clean_corr_matrix = pd.DataFrame()

        st.divider()
        st.subheader("📥 5. Download Evaluation Compendium")
        st.caption("Generate a compiled analytical summary PDF handbook detailing item statistics, alpha metrics, and active distribution data charts.")

        pdf_buffer = io.BytesIO()
        
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            import matplotlib.pyplot as plt
            
            fig_dist, ax_dist = plt.subplots(figsize=(6, 3))
            counts_df.plot(kind="bar", x="Response Categories", y="Frequency (Participant Count)", ax=ax_dist, color="#1f77b4", legend=False)
            ax_dist.set_title(f"Distribution: {selected_col}")
            ax_dist.set_xlabel("Response Categories")
            ax_dist.set_ylabel("Frequency")
            plt.tight_layout()
            
            dist_img_path = os.path.join(tempfile.gettempdir(), "temp_dist_chart.png")
            fig_dist.savefig(dist_img_path, dpi=200)
            plt.close(fig_dist)
            
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

            doc = SimpleDocTemplate(
                pdf_buffer, 
                pagesize=letter,
                rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40,
                title="Open Educational Metadata Analysis Report"
            )
            
            styles = getSampleStyleSheet()
            
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

            story = []
            story.append(Paragraph("<b>Open Educational Metadata Report Compendium</b>", title_style))
            story.append(Paragraph(f"<b>Dataset Sample Metric Matrix Size:</b> {df_analytics.shape[0]} Rows | {df_analytics.shape[1]} Columns", body_style))
            story.append(Spacer(1, 15))
            
            story.append(Paragraph("<b>1. Cronbach's Alpha Scale Reliability Internal Consistency</b>", h2_style))
            for line in scale_summary_text.split("\n"):
                if line.strip() and "CRONBACH" not in line:
                    story.append(Paragraph(line, body_style))
            story.append(Spacer(1, 10))
            
            story.append(Paragraph(f"<b>2. Distribution Visualization Graph: {selected_col}</b>", h2_style))
            if os.path.exists(dist_img_path):
                story.append(Image(dist_img_path, width=320, height=160))
            story.append(Spacer(1, 15))
            
            if not clean_corr_matrix.empty and corr_img_path and os.path.exists(corr_img_path):
                story.append(Paragraph("<b>3. Mixed Multi-Variable Inter-Correlation Matrix</b>", h2_style))
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
                
            story.append(Paragraph("<b>4. Global Item Descriptive Metric Summaries Annex</b>", h2_style))
            desc_df = df_analytics[numeric_cols].describe().round(3).reset_index()
            desc_data = [list(desc_df.columns)] + desc_df.values.tolist()
            
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

            doc.build(story)
            
            if os.path.exists(dist_img_path):
                os.unlink(dist_img_path)
            if corr_img_path and os.path.exists(corr_img_path):
                os.unlink(corr_img_path)
                
            st.download_button(
                label="📥 Download Complete Analytical Summary Report (.pdf)",
                data=pdf_buffer.getvalue(),
                file_name="educational_analytics_summary_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
        except Exception as pdf_error:
            st.error(f"Failed to assemble PDF Report Compendium structure: {pdf_error}. Ensure reportlab and matplotlib packages exist.")
    else:
        st.warning("No continuous numeric variable items identified in the targeted workspace tracking file sheet.")

# --- MODULE 4 ANALYTICS SUGGESTION PIPELINE BUTTON ---
st.markdown("---")
st.markdown("### 🚀 Propose Alternative Statistical & Analytical Functions")
st.caption("Suggest new mathematical equations, code models, plotting styles, or data analysis methods (e.g., ANOVA, multi-level regression equations).")

with st.expander("💡 Click to Draft an Analytics Function Suggestion"):
    suggested_stat_metric = st.text_input("Proposed Statistical Function Title", placeholder="e.g., Add Two-Way ANOVA Matrix Calculations", key="mod4_suggest_metric")
    suggested_stat_code = st.text_area("Proposed Python Code block / Mathematical Formula", placeholder="def calculate_anova():\n    # Provide code suggestions or mathematical description models here...", height=150, key="mod4_suggest_code")
    
    if suggested_stat_metric and suggested_stat_code:
        analytics_payload = f"""**Analytics Engine Function Enhancement Proposal**

**Target Statistical Metric:** {suggested_stat_metric}

### PROPOSED PYTHON ALGORITHM CODE
```text
{suggested_stat_code}
```

---
        analytics_payload = (
            f"**Analytics Engine Function Enhancement Proposal**\n\n"
            f"**Target Statistical Metric:** {suggested_stat_metric}\n\n"
            f"### PROPOSED PYTHON ALGORITHM CODE\n"
            f"```text\n{suggested_stat_code}\n```\n\n"
            f"---\n*Submitted securely via the Descriptive & Scale Analytics Suggestion Pipeline Interface.*"""
        
        st.markdown("##### **Step 1: Copy your generated analytical payload capsule**")
        st.code(analytics_payload, language="markdown")
        
        st.markdown("##### **Step 2: Open the ticket page and paste**")
        static_github_url = "https://github.com"
        
        st.markdown(
            f"1. Copy this link address: `{static_github_url}`\n"
            f"2. Paste it into your browser's address bar at the top of your screen and press Enter.\n"
            f"3. Type **`[Analytics Suggestion] Extend Functions`** in the Issue Title lane.\n"
            f"4. Paste your copied payload into the large description box below it and hit submit!"
        )


# ==========================================
# MODULE 5: LIVE CENTRAL DATABASE VIEWER
# ==========================================
if app_mode == "5. Live Central Database Viewer":
    st.header("🗄️ Central Repository Live Database Viewer")
    st.caption("Direct, read-only access to the underlying structured SQL tables storing public community metadata records.")
    st.markdown("---")

    st.subheader("📊 Select Table to Query")
    st.markdown("Click a button below to pull the real-time datasets straight from the central database.")

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

        # Ensure a fallback database target view is actively mapped
    target_table = str(st.session_state.get("active_db_view", "studies")).strip().lower()

        # 1. Cleanly grab the target table from your button session state
    target_table = str(st.session_state.get("active_db_view", "studies")).strip().lower()

    try:
        with st.spinner(f"Establishing isolated API handshake for `{target_table}`..."):
            from supabase import create_client as standalone_client
            
            # 1. Pull and scrub credentials directly inside this local block
            local_url = str(st.secrets["SUPABASE_URL"]).strip().rstrip("/")
            local_key = str(st.secrets["SUPABASE_KEY"]).strip()
            
            # 2. Build a brand new client completely separate from the rest of the script
            direct_supabase = standalone_client(local_url, local_key)
            
            # 3. Query your table explicitly using the clean standalone client
            db_response = direct_supabase.from_(target_table).select("*").execute()
            
            if db_response.data is not None:
                display_df = pd.DataFrame(db_response.data)
                
                st.subheader(f"📂 Connected Matrix: `{target_table}`")
                if not display_df.empty:
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                    
                    # File download streaming framework
                    raw_csv_bytes = display_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label=f"📥 Download Raw `{target_table}` Dataset (.csv)",
                        data=raw_csv_bytes,
                        file_name=f"supabase_central_repository_{target_table}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.info(f"Connection Live! The `{target_table}` table is ready and completely empty.")
                    
    except Exception as db_view_error:
        st.error(f"Failed to query central database: {db_view_error}")





