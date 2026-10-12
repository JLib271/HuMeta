import streamlit as st
import pandas as pd
import numpy as np
import json
import urllib.parse
import requests
import base64
from sqlalchemy import text  # Required for clean database operations

# Mapping of theoretical frameworks to their standard psychometric constructs/variables
THEORY_MAP = {
    "Theory of Planned Behavior": [
        "Attitude Toward the Behavior | Construct | A person's favorable or unfavorable evaluation of the behavior",
        "Subjective Norms | Construct | Perceived social pressure to perform or not perform the behavior",
        "Perceived Behavioral Control | Construct | Perceived ease or difficulty of performing the behavior",
        "Behavioral Intention | Construct | Indication of an individual's readiness to perform a given behavior"
    ],
    "Self-Determination Theory": [
        "Autonomy | Construct | The need to feel in command of one's life and actions",
        "Competence | Construct | The need to feel effective in interacting with the environment",
        "Relatedness | Construct | The need to feel a sense of belonging and attachment to other people",
        "Intrinsic Motivation / Extrinsic Motivation | Construct | Internal drive versus external rewards/pressures"
    ],
    "Diffusion of Innovations Theory": [
        "Relative Advantage | Construct | The degree to which an innovation is perceived as better than the idea it supersedes",
        "Compatibility | Construct | How well the innovation aligns with the values, experiences, and needs of potential adopters",
        "Complexity | Construct | The degree to which an innovation is perceived as difficult to understand and use",
        "Trialability | Construct | The degree to which an innovation may be experimented with before a full commitment",
        "Observability | Construct | The distinct visibility of the results of an innovation to others"
    ],
    "Technology Acceptance Model": [
        "Perceived Usefulness (PU) | Construct | The degree to which a person believes a system enhances job performance",
        "Perceived Ease of Use (PEOU) | Construct | The degree to which a person believes a system is free of effort",
        "Attitude Toward Using | Construct | The user's evaluation of the desirability of employing the application",
        "Behavioral Intention to Use | Construct | The user's likelihood to adopt or continue using the technology"
    ],
    "Social Cognitive Theory": [
        "Self-Efficacy | Construct | One's belief in their capability to execute behaviors necessary to produce specific performance attainments",
        "Outcome Expectations | Construct | Beliefs about the consequences of specific actions",
        "Observational Learning (Modeling) | Construct | Acquiring information/behaviors by watching others",
        "Behavioral Capability | Construct | Knowledge and skill to perform a given behavior",
        "Reinforcement / Reciprocal Determinism | Construct | The dynamic interaction of person, environment, and behavior"
    ]
}

# --- GLOBAL DATABASE CONNECTION ---
try:
    db_url = st.secrets["connections"]["sql"]["url"]
    shared_conn = st.connection("sql", type="sql", url=db_url)
except Exception as e:
    shared_conn = None

# Initialize application global states
local_df = None
df_studies = pd.DataFrame()
df_vars = pd.DataFrame()

# Page Layout Configurations
st.set_page_config(page_title="Open Educational Metadata Portal", layout="wide")
st.title("🔬 Open Educational Metadata Portal")
st.caption("An Open Source, Community-Driven Engine for Standardized Educational Research and Psychometrics.")

# --- STEP 1: WORKSPACE SELECTION ENGINE ---
st.sidebar.header("⚙️ Workspace Engine")
db_mode = st.sidebar.radio("Data Saving Destination:", ["Local Locked (CSV File)", "Global Collaborative Hub"])

# Initialize a temporary session database to collect items submitted via the webform
if "session_studies" not in st.session_state:
    st.session_state.session_studies = []

# --- STEP 2: SIDEBAR CSV UPLOADER & TEMPLATE GENERATOR ---
with st.sidebar:
    st.markdown("---")
    st.header("📂 Local CSV Import/Export")
    
    # 1. Downloadable CSV Template generation
    template_data = pd.DataFrame(columns=["title", "authors", "abstract", "keywords", "theoretical_framework", "variables_layout"])
    template_data.loc[0] = [
        "Sample Study Title", 
        "Jane Doe, John Smith", 
        "This is a sample abstract summary.", 
        "open education, OER", 
        "Self-Determination Theory", 
        "Course Grade | Dependent Variable | Final score\nTextbook Cost | Independent Variable | Cost at checkout"
    ]
    csv_template = template_data.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="📥 Download CSV Template",
        data=csv_template,
        file_name="opened_metadata_template.csv",
        mime="text/csv"
    )
    
    st.markdown("---")
    
    # 2. File Uploader for local CSV
    uploaded_file = st.file_uploader("Upload your local metadata CSV file", type=["csv"])

    if uploaded_file is not None:
        try:
            user_csv_df = pd.read_csv(uploaded_file)
            required_cols = ["title", "authors", "abstract", "keywords", "theoretical_framework", "variables_layout"]
            
            if all(col in user_csv_df.columns for col in required_cols):
                local_df = user_csv_df.copy()
                st.success("✅ CSV uploaded and parsed!")
                st.dataframe(local_df[["title", "authors"]], use_container_width=True, hide_index=True)
            else:
                st.error("❌ Invalid layout. Use the template provided above.")
        except Exception as e:
            st.error(f"Error reading CSV: {e}")

# --- STEP 3: USER METADATA SUBMISSION FORM ---
st.header("📝 Submit New Study Metadata")

# 1. Start the form container layout
with st.form("study_submission_form", clear_on_submit=False):
    st.subheader("Core Project Details")
    title = st.text_input("Study Title*", placeholder="e.g., Impact of Open Textbooks on Retention")
    authors = st.text_input("Author(s)", placeholder="e.g., Jane Doe, John Smith")
    abstract = st.text_area("Abstract", placeholder="Summary of the study's objective and design...")
    keywords = st.text_input("Keywords (comma separated)", placeholder="e.g., open education, OER, equity")
    
    # We close the core details container group with an implicit submit form execution trick
    # so we can break out of the form block to render live reactive selection checkboxes
    core_details_submitted = st.form_submit_button("Proceed to Framework Validation", help="Validates layout elements live below")

st.divider()
st.subheader("Theoretical & Conceptual Framework")

# 2. Place your checkboxes out here so they remain completely live and responsive!
selected_theories = st.multiselect(
    "Which theoretical framework(s) inform your study?",
    options=[
        "Theory of Planned Behavior", 
        "Self-Determination Theory", 
        "Diffusion of Innovations Theory",
        "Technology Acceptance Model", 
        "Social Cognitive Theory", 
        "Other"
    ]
)

other_framework = ""
if "Other" in selected_theories:
    other_framework = st.text_input("Please specify your alternative theoretical framework:")

# 3. Process framework updates on-the-fly to calculate variable payloads
prepopulated_vars = []
for theory in selected_theories:
    if theory in THEORY_MAP:
        prepopulated_vars.extend(THEORY_MAP[theory])
        
if not prepopulated_vars:
    default_value = "Course Grade | Dependent Variable | Final numerical score percentage scaled 0-100\nTextbook Cost | Independent Variable | Total out of pocket dollar cost calculated at checkout"
else:
    default_value = "\n".join(prepopulated_vars)

st.divider()

# 4. Open a second companion form to process the variables verification and final save transactional steps
# --- STEP 4: DATA MODEL PROCESSING & SAVE AGGREGATION ---
with st.form("variables_submission_form", clear_on_submit=True):
    st.subheader("📊 Study Demographics Collection")
    st.caption("Identify any standard baseline participant demographics your study intends to collect.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Gender Metrics**")
        collect_gender = st.checkbox("Collect Participant Gender Data")
        gender_options = st.multiselect(
            "Select intended gender selection categories:",
            options=["Woman", "Man", "Non-binary", "Prefer to self-describe", "Prefer not to say"],
            default=["Woman", "Man", "Non-binary", "Prefer not to say"],
            disabled=not collect_gender
        )
        
        gender_custom = ""
        if "Prefer to self-describe" in gender_options and collect_gender:
            gender_custom = st.text_input("Specify custom self-description placeholder text:", value="Custom Description text layout")

    with col2:
        st.markdown("**Age Metrics**")
        collect_age = st.checkbox("Collect Participant Age Data")
        age_mode = st.radio(
            "Select age collection format:",
            options=["Continuous (Numerical Entry / Open Age)", "Categorical Range (e.g., 18-24, 25-34)"],
            disabled=not collect_age
        )

    st.divider()
    st.subheader("Study Variables Layout")
    st.caption("Define the properties of what you are measuring. Checking frameworks and demographics above will automatically build and append baseline rows below.")

    # Generate demographic rows on the fly to append to the variables layout text area
    demo_vars = []
    if collect_gender and gender_options:
        cleaned_options = [g for g in gender_options if g != "Prefer to self-describe"]
        if gender_custom:
            cleaned_options.append(gender_custom)
        options_string = ", ".join(cleaned_options)
        demo_vars.append(f"Gender | Demographics | Participant gender selected categories: [{options_string}]")
        
    if collect_age:
        demo_vars.append(f"Age | Demographics | Participant numerical entry or timeline tracking configured as: {age_mode}")

    # Combine theoretical variables and demographic variables together into the box
    if demo_vars:
        if default_value == "Course Grade | Dependent Variable | Final numerical score percentage scaled 0-100\nTextbook Cost | Independent Variable | Total out of pocket dollar cost calculated at checkout":
            final_default_value = "\n".join(demo_vars)
        else:
            final_default_value = default_value + "\n" + "\n".join(demo_vars)
    else:
        final_default_value = default_value

    variables_input = st.text_area(
        "List variables being collected (One per line format -> Name | Type | Operational Definition)",
        value=final_default_value,
        help="You can append, edit, or remove rows freely to customize your study's precise profile metrics.",
        height=250
    )
    
    submit_btn = st.form_submit_button("💾 Save Complete Study Record")

    
    submit_btn = st.form_submit_button("💾 Save Complete Study Record")


    if submit_btn:
        if not title:
            st.error("Study Title is required.")
        else:
            # Format framework strings
            frameworks_to_save = [t for t in selected_theories if t != "Other"]
            if "Other" in selected_theories and other_framework.strip():
                frameworks_to_save.append(other_framework.strip())
            final_framework_string = ", ".join(frameworks_to_save) if frameworks_to_save else "None Specified"
                
            # Process variables array layout
            parsed_variables = []
            for line in variables_input.strip().split("\n"):
                if "|" in line:
                    parts = [p.strip() for p in line.split("|")]
                    v_name = parts[0] if len(parts) > 0 else ""
                    v_type = parts[1] if len(parts) > 1 else "Not Specified"
                    v_def = parts[2] if len(parts) > 2 else "No definition provided"
                    if v_name:
                        parsed_variables.append((v_name, v_type, v_def))
                else:
                    if line.strip():
                        parsed_variables.append((line.strip(), "Not Specified", "No definition provided"))

            # --- ROUTING SAVE PATHS ---
            if db_mode == "Local Locked (CSV File)":
                # Appends record to browser's session history array
                st.session_state.session_studies.append({
                    "title": title,
                    "authors": authors,
                    "abstract": abstract,
                    "keywords": keywords,
                    "theoretical_framework": final_framework_string,
                    "variables_layout": variables_input
                })
                st.success("Successfully logged study to your current web session registry!")
                st.rerun()
                
            elif db_mode == "Global Collaborative Hub":
                if shared_conn is not None:
                    with shared_conn.session as session:
                        res = session.execute(
                            text("""INSERT INTO studies (title, authors, abstract, keywords, theoretical_framework) 

                                   VALUES (:title, :authors, :abstract, :keywords, :framework) RETURNING id;"""),
                            {"title": title, "authors": authors, "abstract": abstract, "keywords": keywords, "framework": final_framework_string}
                        )
                        try:
                            study_id = res.fetchone()
                        except Exception:
                            study_id = session.execute(text("SELECT max(id) FROM studies;")).fetchone()
                        
                        for var in parsed_variables:
                            session.execute(
                                text("""INSERT INTO variables (study_id, variable_name, variable_type, operational_definition) 
                                       VALUES (:study_id, :name, :type, :def);"""),
                                {"study_id": study_id, "name": var[0], "type": var[1], "def": var[2]}
                            )
                        session.commit()
                    st.success("Successfully broadcasted study layout metadata live to the global community database!")
                    st.rerun()
                else:
                    st.error("Global database engine credentials are unconfigured or offline. Please save using 'Local Locked' mode.")

# --- STEP 4: DATA EXPLORER REGISTRY DATA PROCESSING ---
st.divider()
st.header("🔍 Explored Studies Registries")

if db_mode == "Local Locked (CSV File)":
    # Combine uploaded CSV records with any records typed manually into the form during this session
    combined_list = []
    if local_df is not None:
        combined_list.extend(local_df.to_dict(orient="records"))
    if st.session_state.session_studies:
        combined_list.extend(st.session_state.session_studies)
        
    if combined_list:
        df_studies = pd.DataFrame(combined_list)
        df_studies['id'] = range(1, len(df_studies) + 1)
        
        # Build matching variables structural dataframe on the fly for viewing
        vars_list = []
        for idx, row in df_studies.iterrows():
            if pd.notna(row['variables_layout']):
                for line in str(row['variables_layout']).strip().split("\n"):
                    if "|" in line:
                        parts = [p.strip() for p in line.split("|")]
                        v_name = parts[0] if len(parts) > 0 else ""
                        v_type = parts[1] if len(parts) > 1 else "Not Specified"
                        v_def = parts[2] if len(parts) > 2 else "No definition provided"
                    else:
                        v_name = line.strip()
                        v_type = "Not Specified"
                        v_def = "No definition provided"
                    if v_name:
                        vars_list.append({"study_id": row['id'], "variable_name": v_name, "variable_type": v_type, "operational_definition": v_def})
        df_vars = pd.DataFrame(vars_list)
        
        # 🌟 EXPORT BACKOUT BUTTON: Download accumulated work as a spreadsheet
        csv_download = df_studies[["title", "authors", "abstract", "keywords", "theoretical_framework", "variables_layout"]].to_csv(index=False).encode('utf-8')
        st.sidebar.download_button(
            label="📥 Download Current Local Registry (.csv)",
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
        st.warning("Public Collaborative Database running in offline mode. Configure Streamlit Secrets to enable the global community hub.")

# --- STEP 5: VISUALIZE DATA LAYOUT REGISTRY ---
if not df_studies.empty:
    for idx, row in df_studies.iterrows():
        author_text = row['authors'] if pd.notna(row['authors']) and row['authors'] else 'Unknown'
        with st.expander(f"📚 {row['title']} — by {author_text}"):
            st.markdown(f"**Keywords:** `{row['keywords'] if pd.notna(row['keywords']) else 'None'}`")
            st.markdown(f"### Abstract\n{row['abstract'] if pd.notna(row['abstract']) else '*No summary provided.*'}")
            st.markdown(f"### Theoretical Framework\n{row['theoretical_framework'] if pd.notna(row['theoretical_framework']) else '*None specified.*'}")
            
            if not df_vars.empty:
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


