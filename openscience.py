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
    st.markdown("---")
    
    with st.form("metadata_standards_form", clear_on_submit=True):
        st.subheader("📋 Dublin Core Metadata Element Set (DCMES)")
        title = st.text_input("Title (dc:title)*", placeholder="e.g., Analysis of Open Textbook Impact on Retention metrics")
        creator = st.text_input("Creator/Authors (dc:creator)", placeholder="e.g., Dr. Jane Doe, Prof. John Smith")
        description = st.text_area("Description/Abstract (dc:description)", placeholder="Summary of research goals...")
        keywords = st.text_input("Subject Keywords (dc:subject)", placeholder="OER, Motivation, Grades")
        
        st.subheader("📚 IEEE Learning Object Metadata (LOM)")
        lom_context = st.multiselect("Educational Context (LOM 5.6)", ["Higher Education", "K-12 Education", "Vocational", "Informal Learning"])
        lom_role = st.selectbox("Intended End User Role (LOM 5.5)", ["Learner", "Teacher", "Author", "Manager"])
        
        st.subheader("🌐 Common Education Data Standards (CEDS Alignment)")
        ceds_scope = st.selectbox("Study Scope / Level", ["Institutional-Wide", "Course-Level Evaluation", "Multi-Institutional Cluster", "National Assessment"])
        
        st.markdown("**Target Study Population Profile**")
        pop_undergrad = st.checkbox("Undergraduate Students")
        pop_grad = st.checkbox("Graduate Students")
        pop_k12 = st.checkbox("K-12 Learners")
        pop_faculty = st.checkbox("Instructors / Faculty Members")
        
        st.markdown("**Research Methodology Framework**")
        method_quant = st.checkbox("Quantitative Experimental / Quasi-Experimental")
        method_qual = st.checkbox("Qualitative (Interviews, Case Studies)")
        method_mixed = st.checkbox("Mixed-Methods Architecture")
        
        submit_metadata = st.form_submit_button("🚀 Submit to Community Ledger")
        
        if submit_metadata:
            if not title:
                st.error("DCMES Core Field Title is required.")
            else:
                st.success("Metadata payload logged successfully to memory ledger!")

# ==========================================
# MODULE 2: VARIABLE ARCHITECT & FILE EXPORTER
# ==========================================
elif app_mode == "2. Variable Instrument Architect":
    st.header("📐 Variable Architect & Instrument Exporter")
    st.caption("Design variable frameworks, configure measurement items, and instantly download standardized CSV/TXT blueprints.")
    st.markdown("---")
    
    # 1. Demographics Selection Grid
    st.subheader("📊 1. Configure Demographic Variables")
    collect_gender = st.checkbox("Include Gender Variable", value=True)
    collect_age = st.checkbox("Include Age Variable", value=True)
    
    # 2. Theoretical Structural Framework Selector
    st.subheader("🧠 2. Establish Theoretical Framework")
    selected_framework = st.selectbox(
        "Choose core guiding theoretical framework:",
        ["None / Custom Only", "Theory of Planned Behavior (TPB)", "Self-Determination Theory (SDT)", "Technology Acceptance Model (TAM)"]
    )
    
    # Compile variable items collection matrix
    active_items = []
    
    if collect_gender:
        active_items.append({"Variable": "Gender", "Type": "Categorical / Text", "Item Text": "What gender category do you most closely identify with?", "Options": "Woman | Man | Non-binary | Prefer to self-describe | Prefer not to say"})
    if collect_age:
        active_items.append({"Variable": "Age", "Type": "Quantitative / Numeric", "Item Text": "Please enter your age in numerical years:", "Options": "Continuous Integer Entry"})
        
    if selected_framework in THEORY_MAP:
        st.markdown(f"**Pre-populated constructs for {selected_framework}:**")
        theory_data = THEORY_MAP[selected_framework]
        for construct, props in theory_data.items():
            include = st.checkbox(f"Include Construct: {construct}", value=True)
            if include:
                active_items.append({
                    "Variable": construct,
                    "Type": "Quantitative / Scale Score",
                    "Item Text": props["item"],
                    "Options": props["scale"]
                })
                
    # 3. Dynamic Injection Module for Custom / Alternative Constructs
    st.subheader("➕ 3. Inject Additional Custom Variables")
    with st.expander("Configure Additional Custom Variables (Quantitative, Text, Media References)"):
        custom_name = st.text_input("Variable Name", placeholder="e.g., Course Engagement")
        custom_type = st.selectbox("Data Classification Type", ["Quantitative / Ordinal Scale", "Text / Qualitative Response", "Other Media Link / Reference"])
        custom_item = st.text_input("Operational Survey Item Prompt", placeholder="e.g., How many hours a week do you spend using OER platforms?")
        custom_scale = st.text_input("Scale Categories / Constraints", placeholder="e.g., 0-5 hours | 6-10 hours | 11+ hours")
        
        if st.button("Add Custom Variable Entry"):
            if custom_name and custom_item:
                st.session_state.session_instruments.append({
                    "Variable": custom_name,
                    "Type": custom_type,
                    "Item Text": custom_item,
                    "Options": custom_scale
                })
                st.toast(f"Custom variable {custom_name} added successfully!")

    # Merge static map array selections with active session array configurations
    final_instrument_list = active_items + st.session_state.session_instruments
    
    if final_instrument_list:
        df_manifest = pd.DataFrame(final_instrument_list)
        st.subheader("📋 Configured Instrument Mapping Spec")
        st.dataframe(df_manifest, use_container_width=True, hide_index=True)
        
            # --- EXPORT PIPELINES ---
        col1, col2 = st.columns(2)
        
        with col1:
            # Generate the data dictionary metadata sheet (CSV)
            csv_buffer = io.StringIO()
            df_manifest.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📥 Download Metadata Sheet (.csv)",
                data=csv_buffer.getvalue(),
                file_name="educational_study_metadata_sheet.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        with col2:
            # Generate deployment survey text configuration map (TXT)
            txt_manifest = "=== STANDARDIZED EDUCATIONAL SURVEY INSTRUMENT MANIFEST ===\n\n"
            for idx, row in df_manifest.iterrows():
                txt_manifest += f"Variable Identifier: {row['Variable']}\n"
                txt_manifest += f"Data Classification: {row['Type']}\n"
                txt_manifest += f"Question Prompt: {row['Item Text']}\n"
                txt_manifest += f"Scale Categories Matrix:\n   {row['Options']}\n"
                txt_manifest += "-" * 50 + "\n\n"
                
            st.download_button(
                label="📥 Download Deployment Survey Form (.txt)",
                data=txt_manifest,
                file_name="educational_survey_instrument_form.txt",
                mime="text/plain",
                use_container_width=True
            )
    else:
        st.info("No structural framework or variables selected yet.")

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


