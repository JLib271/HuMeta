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
    st.subheader("Official Good et al. (2012) Open Source Schema Mapping Specifications")
    st.write("Researchers can mirror this structure in their data tables to allow the calculation engine to automatically run calculations.")
    
    dictionary_data = []
    for subscale, rules in SUBSCALE_MAP.items():
        for item in rules["items"]:
            is_reversed = "Yes (Inverted automatically)" if item in rules["reverse"] else "No"
            dictionary_data.append({
                "Expected Column Header": item,
                "Psychometric Subscale Domain": subscale,
                "Requires Reverse Scoring": is_reversed
            })
    st.table(pd.DataFrame(dictionary_data))

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
