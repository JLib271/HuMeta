import streamlit as st
import pandas as pd
import numpy as np
import urllib.parse

st.set_page_config(page_title="Open Educational Metadata Portal", layout="wide")
st.title("🔬 Open Educational Metadata Portal")
st.caption("An Open Source, Community-Driven Engine for Standardized Educational Research and Psychometrics.")

# Configuration for your repository
GITHUB_REPO_URL = "https://github.com"

# Initialize an entry tracker for community crowdsourced column suggestions
if "proposed_columns" not in st.session_state:
    st.session_state["proposed_columns"] = [
        {"Proposed Column Key": "Socioeconomic_Status_Tier", "Subscale Category": "Institutional / Demographics", "Justification": "To track environmental resource disparities in learning spaces."},
        {"Proposed Column Key": "First_Generation_Status", "Subscale Category": "Institutional / Demographics", "Justification": "Crucial factor for domain membership and institutional trust metrics."}
    ]

# Dictionary tracking our five belonging subscales and which ones are reverse-coded
SUBSCALE_MAP = {
    "Membership": {
        "items": ["Belong_Community", "Member_Math_World", "Connected_Math", "Fit_In_Math"],
        "reverse": []
    },
    "Acceptance": {
        "items": ["Feel_Accepted", "Feel_Valued", "Feel_Excluded", "Feel_Neglected", "Feel_Appreciated"],
        "reverse": ["Feel_Excluded", "Feel_Neglected"]
    },
    "Affect": {
        "items": ["Feel_Anxious", "Feel_Comfortable", "Feel_Inadequate", "Feel_At_Ease", "Feel_Tense", "Feel_Confident", "Feel_Stressed"],
        "reverse": ["Feel_Anxious", "Feel_Inadequate", "Feel_Tense", "Feel_Stressed"]
    },
    "Trust": {
        "items": ["Trust_Instructors", "Trust_Evaluation", "Trust_Materials", "No_Need_To_Prove_Self", "Instructors_Committed"],
        "reverse": []
    },
    "Desire_To_Fade": {
        "items": ["Try_To_Say_Little", "Wish_Invisible", "Fade_To_Background", "Avoid_Attention"],
        "reverse": ["Try_To_Say_Little", "Wish_Invisible", "Fade_To_Background", "Avoid_Attention"]
    }
}

# Math equation to calculate Cronbach's Alpha reliability
def calculate_cronbach_alpha(df_items):
    num_columns = len(df_items.columns)
    if num_columns in (0, 1):
        return np.nan
    item_vars = df_items.var(ddof=1, axis=0)
    total_var = df_items.sum(axis=1).var(ddof=1)
    if total_var == 0:
        return 0.0
    alpha = (num_columns / (num_columns - 1)) * (1 - (item_vars.sum() / total_var))
    return alpha

# -------------------------------------------------------------
# TIER 1: OPEN SCIENCE STUDY METADATA TABS
# -------------------------------------------------------------
st.header("🌐 1. Public Multi-Standard Study Metadata")
with st.container(border=True):
    t_dc, t_ddi, t_lom = st.tabs(["Dublin Core Core Elements", "DDI Research Methodology", "IEEE LOM Educational Context"])
    
    with t_dc:
        st.subheader("Dublin Core Metadata Schema")
        dc_title = st.text_input("Title (dc:title)", value="")
        dc_creator = st.text_input("Creator / Lead Investigator (dc:creator)", value="")
        dc_subject = st.text_input("Subject Keywords (dc:subject)", value="")
        dc_date = st.text_input("Lifecycle Assembly Date (dc:date)", value="")
        dc_type = st.selectbox("Resource Material Type (dc:type)", ["Dataset", "Text / Observation Log", "Software Application"])
        
    with t_ddi:
        st.subheader("Data Documentation Initiative (DDI) Standards")
        ddi_design = st.selectbox(
            "Methodology / Research Paradigm", 
            ["Randomized Controlled Trial (RCT)", "Quasi-Experimental Design (QED)", "Correlational / Observational Study"]
        )
        ddi_unit = st.selectbox("Unit of Analysis / Observation Level", ["Individual Student Level", "Classroom-Level Aggregation", "School-Wide Clusters"])
        
    with t_lom:
        st.subheader("IEEE Learning Object Metadata (LOM) Standards")
        academic_keys_discipline = st.selectbox(
            "Disciplinary Instructional Classification Focus",
            ["Mathematics", "Science", "English / Reading / Language Arts", "ELL / ESOL / ESL", "Special Education"]
        )
        student_levels = st.multiselect(
            "Target Student Grade Levels (Choose all that apply)",
            ["Pre-Kindergarten", "Kindergarten", "1st Grade", "2nd Grade", "3rd Grade", "4th Grade", "5th Grade", "6th Grade", "7th Grade", "8th Grade", "9th Grade", "10th Grade", "11th Grade", "12th Grade", "Undergraduate", "Graduate"],
            default=[]
        )
        lom_interactivity = st.selectbox("Intended Interactivity Complexity", ["Active Learning Intervention", "Expository Lecture", "Mixed Blended Design"])

# -------------------------------------------------------------
# TIER 2: PRIVATE LOCAL DATA PROCESSING LAYER & SCHEMA EXPLORER
# -------------------------------------------------------------
st.header("🔒 2. Confidential Local Data & Schema Specifications")

t_upload, t_schema, t_propose = st.tabs(["📥 Data Upload & Alignment Checker", "📋 Open Source Data Dictionary", "💡 Propose New Schema Columns"])

# Gather all valid schema items for matching checks
all_expected_items = []
for sub, sub_rules in SUBSCALE_MAP.items():
    all_expected_items.extend(sub_rules["items"])

with t_upload:
    st.info("Upload your research dataset spreadsheet. The column mapping utility will compare your keys against the verified Good et al. schema.")
    uploaded_file = st.file_uploader("Upload local research data spreadsheet (CSV Format)", type=["csv"])

    if uploaded_file is not None:
        df_local = pd.read_csv(uploaded_file)
        st.success("Custom user dataset parsing layer connected successfully!")
        
        # Column Checklist Comparison Tool
        st.subheader("Column Name Match Analyzer")
        found_expected = [col for col in df_local.columns if col in all_expected_items]
        missing_expected = [col for col in all_expected_items if col not in df_local.columns]

        col_chk1, col_chk2 = st.columns(2)
        with col_chk1:
            st.markdown(f"✅ **Matched Variables Found ({len(found_expected)}):**")
            st.text(", ".join(found_expected) if found_expected else "None matched.")
        with col_chk2:
            st.markdown(f"⚠️ **Omitted or Different Variable Keys ({len(missing_expected)}):**")
            st.text(", ".join(missing_expected) if missing_expected else "None missing.")

        st.subheader("Raw Local Data Explorer View")
        st.dataframe(df_local, use_container_width=True)
        
        # Chronbach's Alpha Calculator for matched columns
        st.subheader("Psychometric Data Reliability Statistics")
        alpha_results = {}
        for subscale_name, rules in SUBSCALE_MAP.items():
            matched_subscale_cols = [c for c in df_local.columns if c in rules["items"]]
            if len(matched_subscale_cols) > 1:
                sub_df = df_local[matched_subscale_cols].copy().apply(pd.to_numeric, errors='coerce').dropna()
                if not sub_df.empty:
                    alpha_val = calculate_cronbach_alpha(sub_df)
                    alpha_results[subscale_name] = alpha_val
        
        if alpha_results:
            st.write("Calculated Cronbach's Alpha for available subscales:")
            st.json(alpha_results)
        else:
            st.write("Not enough matching psychometric columns uploaded to calculate alpha metrics.")
    else:
        st.warning("Please upload a local CSV file to analyze variables, view datasets, or compute psychometric statistics.")

with t_schema:
    st.subheader("📋 FAIR-Aligned Metadata & Data Entry Template Generator")
    st.write(
        """
        Build standards-aligned educational research datasets using
        controlled vocabularies and metadata fields that improve
        consistency, interoperability, repository deposit, and
        future meta-analysis.
        """
    )
    
    st.markdown("### Step 1: Select Demographics & Identifiers")
    include_core = st.checkbox("Include Core Fields (`StudentID`, `Gender_Identity`, `Qualitative_Notes`)", value=True)
    
    st.markdown("### Step 2: Select Psychometric Subscales to Include")
    selected_subscales = []
    for subscale_name in SUBSCALE_MAP.keys():
        if st.checkbox(f"Include **{subscale_name}** Subscale Variables", value=True):
            selected_subscales.append(subscale_name)
            
    # Dynamically build the empty layout based on user selections
    template_columns = []
    if include_core:
        template_columns.extend(["StudentID", "Gender_Identity", "Qualitative_Notes"])
        
    for subscale_name in selected_subscales:
        template_columns.extend(SUBSCALE_MAP[subscale_name]["items"])
        
    # Generate empty dataframe template
    df_template = pd.DataFrame(columns=template_columns)
    
    st.markdown("### Step 3: Preview and Download Blank Structural Template")
    st.write("This preview outlines the structural columns that will make up your clean metadata file.")
    st.dataframe(df_template, use_container_width=True)
    
    # Export empty structured file via downloadable CSV button
    csv_buffer = df_template.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Blank Metadata Template (CSV)",
        data=csv_buffer,
        file_name="educational_metadata_template.csv",
        mime="text/csv",
        help="Click here to download a blank CSV template featuring your chosen schema alignments."
    )

with t_propose:
    st.subheader("💡 Propose New Schema Columns")
    st.write("Suggest modifications or additions to the psychometric schema dictionary. Approved proposals can be automatically generated as a Pull Request.")

    # Dynamic proposal submission form
    with st.form("schema_proposal_form", clear_on_submit=True):
        new_key = st.text_input("Proposed Variable Column Key", placeholder="e.g., Digital_Literacy_Scale")
category_options = list(SUBSCALE_MAP.keys()) + ["Institutional / Demographics", "External Context Factor"]
new_category = st.selectbox("Subscale or Metadata Category Alignment", options=category_options)
is_reverse = st.checkbox("Is this variable reverse-coded?")
new_justification = st.text_area("Research Justification / Theoretical Framework", placeholder="Explain why this field is necessary.")
submitted = st.form_submit_button("Generate Proposal Pack")

if submitted:
    if new_key and new_justification:
        new_proposal = {
            "Proposed Column Key": new_key,
            "Subscale Category": new_category,
            "Justification": new_justification
        }
        st.session_state["proposed_columns"].append(new_proposal)
        st.success("Proposal packet compiled! Use the button below to submit your request.")
        
        # Formatted parsing tokens for GitHub Actions automation
        issue_title = f"[Schema Proposal] Add '{new_key}'"
        issue_body = f"""### 💡 New Variable Schema Proposal

[START_DATA]
KEY={new_key}
CATEGORY={new_category}
REVERSE={'True' if is_reverse else 'False'}
[END_DATA]

### 📄 Research Justification
{new_justification}

---
*Submitted via the Open Educational Metadata Portal Application.*"""

        encoded_title = urllib.parse.quote(issue_title)
        encoded_body = urllib.parse.quote(issue_body)
        github_issue_link = f"{GITHUB_REPO_URL}/issues/new?title={encoded_title}&body={encoded_body}"

        st.markdown("---")
        st.markdown("#### 🚀 Send to GitHub")
        st.write("Clicking this button opens a pre-formatted ticket. Submit it to automatically generate a Pull Request for the codebase.")
        st.link_button("Submit Proposal via GitHub Issue", github_issue_link, type="primary")
    else:
        st.error("Please fill out the Variable Column Key and Research Justification fields.")

# Historical view of proposed items tracked in this session
st.markdown("---")
st.subheader("Current Active Queue (Session Context)")
st.dataframe(pd.DataFrame(st.session_state["proposed_columns"]), use_container_width=True)
