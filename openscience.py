import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Open Educational Metadata Portal", layout="wide")
st.title("🔬 Open Educational Metadata Portal")
st.caption("An Open Source, Community-Driven Engine for Standardized Educational Research and Psychometrics.")

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
        dc_title = st.text_input("Title (dc:title)", value="Evaluation of Domain Belonging Patterns in STEM Classrooms")
        dc_creator = st.text_input("Creator / Lead Investigator (dc:creator)", value="Dr. Jane Doe")
        dc_subject = st.text_input("Subject Keywords (dc:subject)", value="belonging, motivation, gender-studies, psychometrics")
        dc_date = st.text_input("Lifecycle Assembly Date (dc:date)", value="2026-10-10")
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
            default=["3rd Grade", "4th Grade", "5th Grade"]
        )
        lom_interactivity = st.selectbox("Intended Interactivity Complexity", ["Active Learning Intervention", "Expository Lecture", "Mixed Blended Design"])

# -------------------------------------------------------------
# TIER 2: PRIVATE LOCAL DATA PROCESSING LAYER & SCHEMA EXPLORER
# -------------------------------------------------------------
st.header("🔒 2. Confidential Local Data & Schema Specifications")

t_upload, t_schema, t_propose = st.tabs(["📥 Data Upload & Alignment Checker", "📋 Open Source Data Dictionary", "💡 Propose New Schema Columns"])

with t_upload:
    st.info("Upload your research dataset spreadsheet. The column mapping utility will compare your keys against the verified Good et al. schema.")
    uploaded_file = st.file_uploader("Upload local research data spreadsheet (CSV Format)", type=["csv"])

    student_ids = "S01,S02,S03,S04,S05,S06".split(",")
    gender_identities = "Woman,Man,Woman,Non-binary,Woman,Man".split(",")
    notes_list = ["Notes A", "Notes B", "Notes C", "Notes D", "Notes E", "Notes F"]

    belong_comm_scores = [int(x) for x in "4,3,5,2,4,5".split(",")]
    member_math_scores = [int(x) for x in "4,2,4,3,3,5".split(",")]
    feel_valued_scores = [int(x) for x in "5,4,4,3,4,5".split(",")]
    feel_excl_scores = [int(x) for x in "1,2,1,4,2,1".split(",")]
    feel_anx_scores = [int(x) for x in "2,3,2,4,3,1".split(",")]

    short_scale_mock = {
        "StudentID": student_ids,
        "Gender_Identity": gender_identities,
        "Belong_Community": belong_comm_scores,
        "Member_Math_World": member_math_scores,
        "Feel_Valued": feel_valued_scores,
        "Feel_Excluded": feel_excl_scores, 
        "Feel_Anxious": feel_anx_scores,  
        "Qualitative_Notes": notes_list
    }
    base_df = pd.DataFrame(short_scale_mock)

    if uploaded_file is not None:
        df_local = pd.read_csv(uploaded_file)
        st.success("Custom user dataset parsing layer connected successfully!")
    else:
        df_local = base_df
        st.info("Displaying automated short-scale data context. Upload your project CSV file above to substitute records.")

    # Column Checklist Comparison Tool
    st.subheader("Column Name Match Analyzer")
    all_expected_items = []
    for sub, sub_rules in SUBSCALE_MAP.items():
        all_expected_items.extend(sub_rules["items"])

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

with t_schema:

    st.subheader("📋 FAIR-Aligned Metadata & Data Entry Template")

    st.write(
        """
        Build standards-aligned educational research datasets using
        controlled vocabularies and metadata fields that improve
        consistency, interoperability, repository deposit, and
        future meta-analysis.
        """
    )

    # =====================================================
    # VARIABLE SELECTION SECTION
    # =====================================================

    st.subheader("🧩 Select Variables For Your Dataset")

    ALL_METADATA_FIELDS = {

        "Participant Demographics": [
            "Gender_Identity",
            "Gender_Identity_Other",
            "Race_Ethnicity",
            "Race_Ethnicity_Other",
            "Grade_Level",
            "Grade_Level_Other"
        ],

        "Educational Context": [
            "Course_Subject",
            "Course_Subject_Other"
        ],

        "Institution Metadata": [
            "Institution_Type",
            "Institution_Type_Other"
        ],

        "Research Metadata": [
            "Research_Design",
            "Research_Design_Other",
            "DOI",
            "ORCID",
            "Grant_Number",
            "IRB_Protocol"
        ]
    }

    selected_columns = ["StudentID"]

    for group_name, field_list in ALL_METADATA_FIELDS.items():

        st.markdown(f"#### {group_name}")

        chosen = st.multiselect(
            f"Choose {group_name}",
            field_list,
            default=field_list,
            key=f"select_{group_name}"
        )

        selected_columns.extend(chosen)

    st.markdown("#### Psychometric Scales")

    selected_scales = st.multiselect(
        "Choose Scale Domains",
        list(SUBSCALE_MAP.keys()),
        default=list(SUBSCALE_MAP.keys())
    )

    for scale in selected_scales:
        selected_columns.extend(
            SUBSCALE_MAP[scale]["items"]
        )

    include_notes = st.checkbox(
        "Include Qualitative Notes",
        value=True
    )

    if include_notes:
        selected_columns.append(
            "Qualitative_Notes"
        )

    selected_columns = list(
        dict.fromkeys(selected_columns)
    )

    st.subheader("📋 Selected Dataset Structure")

    st.dataframe(
        pd.DataFrame(
            {"Variable": selected_columns}
        ),
        use_container_width=True,
        hide_index=True
    )

    # -----------------------------------------------------
    # CONTROLLED VOCABULARIES
    # -----------------------------------------------------

    GENDER_OPTIONS = [
        "Woman",
        "Man",
        "Non-binary",
        "Agender",
        "Genderfluid",
        "Two-Spirit",
        "Prefer Not To Answer",
        "Other"
    ]

    RACE_OPTIONS = [
        "American Indian or Alaska Native",
        "Asian",
        "Black or African American",
        "Hispanic or Latino",
        "Middle Eastern or North African",
        "Native Hawaiian or Pacific Islander",
        "White",
        "Prefer Not To Answer",
        "Other"
    ]

    GRADE_OPTIONS = [
        "Pre-K",
        "Kindergarten",
        "1st Grade",
        "2nd Grade",
        "3rd Grade",
        "4th Grade",
        "5th Grade",
        "6th Grade",
        "7th Grade",
        "8th Grade",
        "9th Grade",
        "10th Grade",
        "11th Grade",
        "12th Grade",
        "Undergraduate",
        "Graduate",
        "Adult Learning",
        "Other"
    ]

    SUBJECT_OPTIONS = [
        "Mathematics",
        "Biology",
        "Chemistry",
        "Physics",
        "Earth Science",
        "Environmental Science",
        "Engineering",
        "Computer Science",
        "Data Science",
        "English Language Arts",
        "Social Studies",
        "History",
        "Economics",
        "Special Education",
        "ESL / ELL",
        "Other"
    ]

    INSTITUTION_OPTIONS = [
        "Public Elementary School",
        "Public Middle School",
        "Public High School",
        "Charter School",
        "Private School",
        "Community College",
        "4-Year College",
        "Research University",
        "Minority Serving Institution",
        "Tribal College",
        "Online Institution",
        "Museum",
        "Science Center",
        "Informal Learning Organization",
        "Other"
    ]

    RESEARCH_OPTIONS = [
        "Randomized Controlled Trial (RCT)",
        "Quasi-Experimental Design (QED)",
        "Correlational Study",
        "Mixed Methods",
        "Qualitative Study",
        "Case Study",
        "Design-Based Research",
        "Improvement Science",
        "Meta-Analysis",
        "Systematic Review",
        "Other"
    ]

    LIKERT_OPTIONS = [
        "1 - Strongly Disagree",
        "2 - Disagree",
        "3 - Neutral",
        "4 - Agree",
        "5 - Strongly Agree"
    ]

# -----------------------------------------------------
# METADATA TEMPLATE
# -----------------------------------------------------

st.subheader("✏️ Metadata-Aligned Dataset Builder")

template_columns = [

    "StudentID",

    "Gender_Identity",
    "Gender_Identity_Other",

    "Race_Ethnicity",
    "Race_Ethnicity_Other",

    "Grade_Level",
    "Grade_Level_Other",

    "Course_Subject",
    "Course_Subject_Other",

    "Institution_Type",
    "Institution_Type_Other",

    "Research_Design",
    "Research_Design_Other",

    "DOI",
    "ORCID",
    "Grant_Number",
    "IRB_Protocol",

    "Qualitative_Notes"
]

for subscale, rules in SUBSCALE_MAP.items():
    template_columns.extend(rules["items"])

template_df = pd.DataFrame(columns=template_columns)

if "working_metadata_df" not in st.session_state:
    st.session_state["working_metadata_df"] = template_df.copy()

edited_template = st.data_editor(
    st.session_state["working_metadata_df"],
    num_rows="dynamic",
    use_container_width=True,
    key="metadata_template_editor"
)

st.session_state["working_metadata_df"] = edited_template

st.info(
    """
    Create records from scratch using the data editor.

    • Click '+ Add Row' to add study participants
    • Race/Ethnicity can contain multiple values separated by semicolons
    • Use *_Other fields whenever 'Other' is selected
    • Download the dataset at any time
    """
)

# -----------------------------------------------------
# CSV IMPORT / MERGE
# -----------------------------------------------------

st.subheader("📥 Import Existing Dataset")

uploaded_metadata_csv = st.file_uploader(
    "Upload Existing Metadata CSV",
    type=["csv"],
    key="metadata_import"
)

if uploaded_metadata_csv is not None:

    imported_df = pd.read_csv(uploaded_metadata_csv)

    st.success(
        f"Imported {len(imported_df)} records."
    )

    st.dataframe(
        imported_df.head(),
        use_container_width=True
    )

    if st.button("Append Imported Records"):

        st.session_state["working_metadata_df"] = pd.concat(
            [
                st.session_state["working_metadata_df"],
                imported_df
            ],
            ignore_index=True
        )

        st.success(
            "Imported records merged successfully."
        )

# -----------------------------------------------------
# DOWNLOAD DATASET
# -----------------------------------------------------

st.download_button(
    label="📥 Download Current Metadata Dataset",
    data=st.session_state["working_metadata_df"].to_csv(index=False),
    file_name="metadata_dataset.csv",
    mime="text/csv"
)



# -----------------------------------------------------
# PSYCHOMETRIC DICTIONARY
# -----------------------------------------------------

st.subheader("📚 Good et al. Instrument Dictionary")

dictionary_data = []

for subscale, rules in SUBSCALE_MAP.items():

    for item in rules["items"]:

        dictionary_data.append(
            {
                "Expected Column Header": item,
                "Psychometric Subscale Domain": subscale,
                "Requires Reverse Scoring":
                    "Yes" if item in rules["reverse"] else "No"
            }
        )

st.dataframe(
    pd.DataFrame(dictionary_data),
    use_container_width=True,
    hide_index=True
)

# -----------------------------------------------------
# METADATA DICTIONARY
# -----------------------------------------------------

st.subheader("🌐 Metadata Dictionary")

metadata_dictionary = pd.DataFrame(
    [
        ["Gender_Identity", "Participant Metadata"],
        ["Gender_Identity_Other", "Participant Metadata"],
        ["Race_Ethnicity", "Participant Metadata"],
        ["Race_Ethnicity_Other", "Participant Metadata"],
        ["Grade_Level", "Educational Context"],
        ["Grade_Level_Other", "Educational Context"],
        ["Course_Subject", "Educational Context"],
        ["Course_Subject_Other", "Educational Context"],
        ["Institution_Type", "Institution Metadata"],
        ["Institution_Type_Other", "Institution Metadata"],
        ["Research_Design", "Study Metadata"],
        ["Research_Design_Other", "Study Metadata"],
        ["DOI", "Repository Metadata"],
        ["ORCID", "Researcher Metadata"],
        ["Grant_Number", "Funding Metadata"],
        ["IRB_Protocol", "Compliance Metadata"]
    ],
    columns=[
        "Metadata Variable",
        "Category"
    ]
)

st.dataframe(
    metadata_dictionary,
    use_container_width=True,
    hide_index=True
)

with t_propose:
    st.subheader("💡 Propose Custom Metadata Columns to the Ecosystem")
    st.write("Are you tracking an educational parameter not covered by the current core standards? Submit a recommendation below:")

with st.form("suggestion_form", clear_on_submit=True):
    new_key = st.text_input("Suggested Column Header Key", placeholder="e.g., Socioeconomic_Status_Tier")
    new_cat = st.selectbox("Subscale Alignment", ["Membership Extension", "Acceptance Extension", "Institutional / Demographics", "Qualitative Flag"])
    new_just = st.text_area("Research Justification / Purpose")
    
    if st.form_submit_button("Submit Suggestion to Manifest Log"):
        if new_key and new_just:
            st.session_state["proposed_columns"].append({
                "Proposed Column Key": new_key,
                "Subscale Category": new_cat,
                "Justification": new_just
            })
            st.success(f"Proposed column '{new_key}' successfully appended to the public manifest template log below!")
        else:
            st.error("Please fill in both the column key name and the research justification.")

st.subheader("Current Community Proposed Metadata Additions Log")
df_proposals = pd.DataFrame(st.session_state["proposed_columns"])
st.dataframe(df_proposals, use_container_width=True, hide_index=True)

# -------------------------------------------------------------
# DYNAMIC CALCULATION CORE ENGINE
# -------------------------------------------------------------
columns_to_keep = ["StudentID", "Gender_Identity", "Qualitative_Notes"]
df_scored = df_local.filter(columns_to_keep).copy()
subscale_calculated_cols = []
alpha_records = {}

for subscale, rules in SUBSCALE_MAP.items():
    found_items = [item for item in rules["items"] if item in df_local.columns]
    
    if found_items:
        sub_df = df_local.filter(found_items).copy()
        for item in found_items:
            if item in rules["reverse"]:
                sub_df[item] = 6 - sub_df[item]
        
        if len(sub_df.columns) >= 2:
            alpha_val = calculate_cronbach_alpha(sub_df)
            alpha_records[subscale] = alpha_val
        else:
            alpha_records[subscale] = "N/A (Single Item)"
            
        df_scored[f"Subscale_{subscale}"] = sub_df.mean(axis=1)
        subscale_calculated_cols.append(f"Subscale_{subscale}")

if subscale_calculated_cols:
    df_scored["Overall_Belonging_Scale_Score"] = df_scored.filter(subscale_calculated_cols).mean(axis=1)

# -------------------------------------------------------------
# TIER 3: OPEN PUBLIC AGGREGATIONS & GRAPHICS
# -------------------------------------------------------------
st.header("📊 3. Public Demographic Aggregates, Charts & Reliability Reports")
if not df_scored.empty:
    tab_stats, tab_charts, tab_alpha, tab_text = st.tabs(["Calculated Subscale Averages", "📈 Interactive Data Visualizations", "Cronbach's Alpha Reliability Logs", "Qualitative Logs"])
    
    with tab_stats:
        st.subheader("Aggregated Scale Matrices Grouped by Gender Profile")
        aggregates_output = df_scored.groupby("Gender_Identity")[df_scored.columns.difference(columns_to_keep)].mean().reset_index()
        st.dataframe(aggregates_output.round(2), use_container_width=True, hide_index=True)
        
    with tab_charts:
        st.subheader("📈 Interactive Profile Matrix Visualizer")
        st.write("This interactive graphic breaks down calculated belonging scores by identity profile across your active dataset:")
        
        df_melted = df_scored.melt(id_vars=["Gender_Identity"], value_vars=subscale_calculated_cols, var_name="Subscale Component", value_name="Calculated Score")
        df_chart_agg = df_melted.groupby(["Gender_Identity", "Subscale Component"])["Calculated Score"].mean().reset_index()
        
        custom_brand_colors = ["#1F4E79", "#2E8B57", "#708090", "#D9534F"]
        
        fig = px.bar(
            df_chart_agg, 
            x="Subscale Component", 
            y="Calculated Score", 
            color="Gender_Identity", 
            barmode="group",
            title="Comparison of Good et al. Subscale Profiles Across Gender Identities",
            labels={"Calculated Score": "Mean Scale Score (1-5)", "Subscale Component": "Psychometric Dimension"},
            color_discrete_sequence=custom_brand_colors
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with tab_alpha:
        st.subheader("Internal Consistency Reports (Cronbach's Alpha)")
        alpha_summary_data = []
        for k, v in alpha_records.items():
            if isinstance(v, float):
                status_str = "🔥 Excellent Reliability" if v >= 0.80 else ("👍 Acceptable Reliability" if v >= 0.70 else "⚠️ Low Reliability")
                val_str = f"{v:.3f}"
            else:
                status_str = "Informational: Insufficient items to run calculation"
                val_str = str(v)
            alpha_summary_data.append({"Subscale Component Dimension": k, "Cronbach's Alpha Coefficient": val_str, "Psychometric Status Interpretation": status_str})
        st.table(pd.DataFrame(alpha_summary_data))
        
    with tab_text:
        st.subheader("Anonymized Field Observations Output")
        st.dataframe(df_scored.filter(columns_to_keep), use_container_width=True, hide_index=True)

    # -------------------------------------------------------------
    # EXPORT BLOCK
    # -------------------------------------------------------------
    st.subheader("📥 Export Open Science Manifest Package")
    levels_joined = ", ".join(student_levels) if student_levels else "None Selected"
    proposals_text = "\n".join([f"- Key: {p['Proposed Column Key']} | Category: {p['Subscale Category']} | Justification: {p['Justification']}" for p in st.session_state["proposed_columns"]])
    
    manifest_txt = (
        f"--- OPEN EDUCATIONAL METADATA MANIFEST ---\n"
        f"DUBLIN CORE METADATA ELEMENTS:\n"
        f"Identifier/Title: {dc_title}\nCreator: {dc_creator}\nSubject Group: {dc_subject}\nDate Logged: {dc_date}\nType: {dc_type}\n\n"
        f"DDI DATA DOCUMENTATION PARAMETERS:\n"
        f"Research Design Paradigm: {ddi_design}\nObservation Analysis Unit: {ddi_unit}\n\n"
        f"IEEE LOM EDUCATIONAL METADATA CONTEXT:\n"
        f"Instruction Focus Domain: {academic_keys_discipline}\nTarget Grade Cohort Levels: {levels_joined}\nInteractivity Configuration: {lom_interactivity}\n\n"
        f"COMMUNITY SCHEMATIC EXTENSIONS PROPOSED:\n"
        f"{proposals_text}\n"
    )
    
    c_exp1, c_exp2 = st.columns(2)
    with c_exp1:
        st.download_button(
            label="Download Public Aggregated Survey Tables (.CSV)",
            data=aggregates_output.to_csv(index=False),
            file_name="good_2012_anonymized_aggregates.csv",
            mime="text/csv"
        )
    with c_exp2:
        st.download_button(
            label="Download Unified Public Metadata Manifest & Community Logs (.TXT)",
            data=manifest_txt,
            file_name="open_science_schema_manifest.txt",
            mime="text/plain"
        )

