from __future__ import annotations
import streamlit as st
import pandas as pd
import numpy as np
import io
import json
import os
import tempfile
import sqlite3
import uuid
from pathlib import Path
from sqlalchemy import text
import requests
import urllib.parse
from supabase import create_client, Client
from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowEdge, StreamlitFlowNode
from streamlit_flow.layouts import ManualLayout
from streamlit_flow.state import StreamlitFlowState

DATASET_BUCKET = "study-datasets"
PUBLIC_DATASET_BUCKET = "public-study-datasets"
UNIT_OF_ANALYSIS_OPTIONS = [
    "Individual (person / participant)",
    "Group / household / community",
    "Organization / institution",
    "Place / site / geographic area",
    "Event / activity / interaction",
    "Document / artifact / media object",
    "Other / multi-level",
]
SAMPLING_PROCEDURE_OPTIONS = [
    "Census / all eligible people, groups, organizations, or sites",
    "Convenience / accessible participant, visitor, or site sample",
    "Volunteer / self-selected participants",
    "Purposive / criterion-based sample",
    "Stratified sample by age, role, location, organization, or other characteristic",
    "Cluster or multistage sample of communities, organizations, groups, or sites",
    "Random sample of people or units within selected sites",
    "Systematic sample from a roster, registry, visitor flow, or other list",
    "Time-location or venue-based sample (for example, museum visitors)",
    "Snowball / peer referral",
    "Multiple or mixed sampling procedures",
    "Other / describe in details",
]
QUALITATIVE_COLLECTION_MODES = [
    "Individual or semi-structured interviews",
    "Focus groups or group discussions",
    "Classroom or field observations",
    "Think-aloud or cognitive interviews",
    "Case study or ethnographic fieldwork",
    "Open-ended survey questions",
    "Document, curriculum, or artifact analysis",
    "Visual elicitation or drawing activities",
    "Audio/video elicitation",
]
QUANTITATIVE_COLLECTION_MODES = [
    "Closed-ended questionnaire or survey",
    "Standardized or researcher-developed assessment",
    "Pre/post-test or repeated-measures assessment",
    "Classroom, school, or district administrative records",
    "Grades, attendance, enrollment, or course-taking records",
    "Digital learning platform or system logs",
    "Time-on-task or event-duration tracking",
    "Structured observation or rubric scores",
    "Experimental or quasi-experimental outcome measures",
    "Sensor, device, or other automated measurements",
]
QUALITATIVE_DATA_TYPES = [
    "Interview transcripts",
    "Focus-group transcripts",
    "Interview or discussion audio recordings",
    "Classroom or field notes",
    "Observation narratives",
    "Open-ended survey responses",
    "Student or educator written reflections",
    "Drawings, diagrams, or other visual work",
    "Student assignments, essays, or projects",
    "Portfolios or collections of student work",
    "Lesson plans or instructional materials",
    "Curriculum, textbooks, or learning artifacts",
    "Photographs or video recordings",
    "Think-aloud protocols",
    "Case-study or ethnographic records",
]
QUANTITATIVE_DATA_TYPES = [
    "Closed-ended survey responses",
    "Assessment item responses",
    "Test, quiz, or benchmark scores",
    "Grades or course outcomes",
    "Attendance or participation counts",
    "Enrollment, completion, or retention records",
    "Time-on-task or session-duration measures",
    "Digital clickstream, event, or platform logs",
    "Structured observation codes or rubric scores",
    "Behavioral event counts or frequency measures",
    "Intervention fidelity or implementation scores",
    "School, district, or administrative indicators",
    "Sensor or device measurements",
    "Longitudinal, repeated-measures, or growth data",
]
CROSS_CUTTING_DATA_TYPES = [
    "Survey instrument and codebook",
    "Data dictionary or variable documentation",
    "Sampling, recruitment, or consent documentation",
    "Intervention or instructional protocol",
    "Researcher analytic memos",
    "De-identification or data-processing log",
]
ACADEMIC_SUBJECT_AREAS = {
    "Mathematics": [
        "Arithmetic and numeracy",
        "Algebra",
        "Geometry",
        "Trigonometry",
        "Calculus",
        "Statistics and probability",
        "Applied mathematics",
        "Mathematics education",
    ],
    "Science": [
        "Agricultural science",
        "Astronomy and space science",
        "Biology and life science",
        "Chemistry",
        "Earth and environmental science",
        "Engineering and applied science",
        "Health and biomedical science",
        "Physics",
        "Science education",
    ],
    "Reading / English Language Arts": [
        "Reading and literacy",
        "Writing and composition",
        "Language and linguistics",
        "Literature",
        "English language learning",
        "Media and information literacy",
    ],
    "Social Studies / History": [
        "Civics and government",
        "Economics",
        "Geography",
        "History",
        "Psychology",
        "Sociology and anthropology",
    ],
    "Foreign Language Education": [
        "World languages",
        "Classical languages",
        "American Sign Language",
        "Heritage language learning",
        "English as an additional language",
    ],
    "Fine and Performing Arts": [
        "Visual arts",
        "Music",
        "Theater and drama",
        "Dance",
        "Media arts",
        "Arts integration",
    ],
    "Computer and Information Sciences": [
        "Computer science",
        "Information technology",
        "Data science",
        "Cybersecurity",
        "Artificial intelligence",
        "Computing education",
    ],
    "Business": [
        "Accounting",
        "Business administration and management",
        "Entrepreneurship",
        "Finance",
        "Marketing",
        "Operations and supply chain",
        "Business education",
    ],
    "Career and Technical Education": [
        "Agriculture, food, and natural resources",
        "Architecture and construction",
        "Arts, audio/video technology, and communications",
        "Business management and administration",
        "Education and training",
        "Engineering and technology",
        "Health science",
        "Hospitality and tourism",
        "Information technology",
        "Manufacturing",
        "Science, technology, engineering, and mathematics",
        "Transportation and logistics",
    ],
    "Health and Physical Education": [
        "Health education",
        "Physical education",
        "Public health",
        "Nutrition",
        "Kinesiology and exercise science",
    ],
    "Humanities": [
        "Philosophy and ethics",
        "Religious studies",
        "Classics",
        "Cultural studies",
        "Interdisciplinary humanities",
    ],
    "Psychology and Behavioral Sciences": [
        "Developmental psychology",
        "Cognitive psychology",
        "Social psychology",
        "Clinical and counseling psychology",
        "Behavioral science",
        "Neuroscience",
    ],
    "Sociology and Social Sciences": [
        "Sociology",
        "Social work",
        "Criminology",
        "Demography and population studies",
        "Social policy",
        "Community studies",
    ],
    "Anthropology": [
        "Cultural anthropology",
        "Archaeology",
        "Linguistic anthropology",
        "Biological anthropology",
        "Applied anthropology",
    ],
    "Communication and Media Studies": [
        "Communication",
        "Journalism",
        "Media studies",
        "Public communication",
        "Science communication",
    ],
    "Public Health and Health Sciences": [
        "Public health",
        "Epidemiology",
        "Health behavior",
        "Health services research",
        "Community health",
    ],
    "Human Development and Family Sciences": [
        "Human development",
        "Family studies",
        "Child and youth development",
        "Aging and lifespan studies",
    ],
    "Political Science and Public Policy": [
        "Political science",
        "Public administration",
        "Public policy",
        "Civic engagement",
    ],
    "Interdisciplinary / General Academic": [
        "Interdisciplinary studies",
        "General education",
        "Integrated STEM",
        "Other interdisciplinary area",
    ],
    "Other academic subject": [],
}
EDUCATION_LEVEL_OPTIONS = [
    "Early childhood / Pre-K",
    "Kindergarten",
    "Elementary / primary grades (1-5 or local equivalent)",
    "Middle grades / lower secondary (6-8 or local equivalent)",
    "High school / upper secondary (9-12 or local equivalent)",
    "Postsecondary undergraduate",
    "Postsecondary graduate / professional",
    "Adult basic or secondary education",
    "Adult continuing, workforce, or professional education",
    "Multiple formal education levels",
    "Informal / out-of-school learning",
    "Afterschool or expanded-learning program",
    "Community-based or youth organization",
    "Museum, library, science center, or cultural institution",
    "Home-based or family learning",
    "Non-formal workforce or apprenticeship learning",
    "Online or open learning outside a formal institution",
    "General public / community participants",
    "Museum, library, or science-center visitors",
    "Visitors to public events, exhibitions, or cultural sites",
    "Adult participants outside a formal learning program",
    "Multiple formal and informal settings",
    "Other / not listed",
]
UNDERGRADUATE_LEVEL_OPTIONS = [
    "Entry-level / introductory (typically first-year)",
    "Intermediate (typically second-year)",
    "Advanced undergraduate (typically third- or fourth-year)",
    "Upper-division / capstone",
    "Multiple undergraduate levels",
]
PROGRAM_TYPE_OPTIONS = [
    "Formal K-12 general education",
    "Special education / disability support services",
    "English learner / multilingual learner program",
    "Career and technical education (CTE)",
    "Advanced coursework / honors / gifted education",
    "Alternative, credit-recovery, or re-engagement program",
    "Early college, dual enrollment, or concurrent enrollment",
    "Undergraduate degree program — declared major",
    "Undergraduate degree program — non-major / undeclared",
    "Undergraduate certificate or non-degree program",
    "Graduate degree program — declared major / field",
    "Graduate professional or licensure program",
    "Community college or open-access program",
    "Adult basic education, GED, or high-school equivalency",
    "Workforce development, apprenticeship, or occupational training",
    "Afterschool, summer, or expanded-learning program",
    "Community-based, museum, library, or cultural learning program",
    "Informal / self-directed learning",
    "General public / community participation (no specific program)",
    "Museum, gallery, library, or science-center visitation",
    "Public event, exhibition, or festival participation",
    "Civic, cultural, or community organization",
    "Online, open, or non-formal learning program",
    "No specific program / general population",
    "Other / not listed",
]

def create_supabase_client() -> Client:
    """Create an isolated Supabase client for the current Streamlit session."""
    url = str(st.secrets["SUPABASE_URL"]).strip().rstrip("/")
    key = str(st.secrets["SUPABASE_KEY"]).strip()
    return create_client(url, key)


def store_auth_session(auth_session) -> None:
    auth_user = auth_session.user
    if auth_user is None:
        raise ValueError("Supabase returned an authentication session without a user.")
    st.session_state["supabase_auth"] = {
        "access_token": auth_session.access_token,
        "refresh_token": auth_session.refresh_token,
        "email": auth_user.email
    }


def authenticated_supabase_client() -> tuple[Client | None, str | None]:
    saved_session = st.session_state.get("supabase_auth")
    if not saved_session:
        return None, None

    try:
        client = create_supabase_client()
        response = client.auth.set_session(
            saved_session["access_token"],
            saved_session["refresh_token"]
        )
        if response.session:
            store_auth_session(response.session)
        auth_user = response.user or (response.session.user if response.session else None)
        if auth_user is None:
            st.session_state.pop("supabase_auth", None)
            return None, "Supabase could not validate the signed-in user."
        return client, auth_user.id
    except Exception as auth_error:
        st.session_state.pop("supabase_auth", None)
        return None, f"Your sign-in session expired or is no longer valid: {auth_error}"


def context_search_terms(value: str) -> list[str]:
    stop_words = {
        "about", "after", "among", "and", "are", "for", "from", "into",
        "its", "our", "that", "the", "their", "this", "through", "with",
    }
    return list(dict.fromkeys(
        token
        for token in "".join(
            character.lower() if character.isalnum() else " "
            for character in str(value)
        ).split()
        if len(token) > 2 and token not in stop_words
    ))


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
        },
        "Behavior": {
            "item": "Observed or recorded performance of the target educational behavior.",
            "scale": "Define the behavior, observation window, source, and coding or measurement rule."
        },
    },
    "Self-Determination Theory (SDT)": {
        "Autonomy": {
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
        },
        "Actual System Use": {
            "item": "Observed or recorded use of the learning system.",
            "scale": "Define the use event, observation window, source, and aggregation rule."
        }
    }
}
THEORY_MAP.update({
    "Health Belief Model (HBM)": {
        "Perceived Susceptibility": {},
        "Perceived Severity": {},
        "Perceived Threat": {},
        "Perceived Benefits": {},
        "Perceived Barriers": {},
        "Self-Efficacy": {},
        "Cues to Action": {},
        "Preventive Behavior": {},
    },
    "Social Cognitive Theory (SCT)": {
        "Personal Factors": {},
        "Environmental Factors": {},
        "Behavioral Factors": {},
        "Observational Learning": {},
        "Outcome Expectations": {},
        "Self-Efficacy": {},
        "Reinforcement": {},
    },
    "Self-Efficacy Theory": {
        "Self-Efficacy": {},
        "Mastery Experiences": {},
        "Vicarious Experiences": {},
        "Verbal Persuasion": {},
        "Emotional / Physiological Arousal": {},
    },
    "Transtheoretical Model (Stages of Change)": {
        "Precontemplation": {},
        "Contemplation": {},
        "Preparation": {},
        "Action": {},
        "Maintenance": {},
        "Termination": {},
        "Relapse / Stage Progression": {},
    },
    "Control Theory": {
        "Goal / Reference State": {},
        "Input / Perceived Current State": {},
        "Comparator / Discrepancy": {},
        "Output / Behavior Adjustment": {},
        "Feedback": {},
        "Environmental Impact": {},
        "Disturbances / Obstacles": {},
    },
    "Operant Conditioning": {
        "Positive Reinforcement": {},
        "Negative Reinforcement": {},
        "Positive Punishment": {},
        "Negative Punishment": {},
        "Behavioral Consequence": {},
    },
    "COM-B Model": {
        "Psychological Capability": {},
        "Physical Capability": {},
        "Physical Opportunity": {},
        "Social Opportunity": {},
        "Reflective Motivation": {},
        "Automatic Motivation": {},
        "Behavior": {},
    },
    "Theoretical Domains Framework (TDF)": {
        "Knowledge": {},
        "Skills": {},
        "Memory, Attention, and Decision Processes": {},
        "Behavioral Regulation": {},
        "Beliefs about Capabilities": {},
        "Beliefs about Consequences": {},
        "Intentions": {},
        "Optimism": {},
        "Goals": {},
        "Reinforcement": {},
        "Emotion": {},
        "Social / Professional Role and Identity": {},
        "Environmental Context and Resources": {},
        "Social Influences": {},
    },
})
THEORY_CITATIONS = {
    "Health Belief Model (HBM)": (
        "Rosenstock, I. M. (1974). The health belief model and preventive health behavior. "
        "Health Education Monographs, 2(4), 354–386."
    ),
    "Social Cognitive Theory (SCT)": (
        "Bandura, A. (1999). Social cognitive theory of personality. "
        "In Handbook of Personality (2nd ed., pp. 154–196)."
    ),
    "Self-Efficacy Theory": (
        "Bandura, A. (1977). Self-efficacy: Toward a unifying theory of behavioral change. "
        "Psychological Review, 84(2), 191–215."
    ),
    "Theory of Planned Behavior (TPB)": (
        "Ajzen, I. (1991). The theory of planned behavior. "
        "Organizational Behavior and Human Decision Processes, 50(2), 179–211."
    ),
    "Transtheoretical Model (Stages of Change)": (
        "Grimley, D., Prochaska, J. O., Velicer, W. F., Blais, L. M., & DiClemente, C. C. "
        "(1994). The transtheoretical model of change. In Changing the Self: Philosophies, "
        "Techniques, and Experiences (pp. 201–227)."
    ),
    "Self-Determination Theory (SDT)": (
        "Ryan, R. M., & Deci, E. L. (2000). Self-determination theory and the facilitation "
        "of intrinsic motivation, social development, and well-being. American Psychologist, 55, 68–78."
    ),
    "Control Theory": (
        "Carver, C. S., & Scheier, M. F. (1982). Control theory: A useful conceptual framework "
        "for personality-social, clinical, and health psychology. Psychological Bulletin, 92, 111–135."
    ),
    "Operant Conditioning": (
        "Skinner, B. F. (1953). Operant conditioning. [Citation as listed in the linked source.]"
    ),
    "COM-B Model": (
        "Michie, S., van Stralen, M. M., & West, R. (2011). Authors and year identified in "
        "the linked source; a full reference is not provided there."
    ),
    "Theoretical Domains Framework (TDF)": (
        "Atkins, L., Francis, J., Islam, R., O’Connor, D., Patey, A., Ivers, N., et al. "
        "(2017). A guide to using the Theoretical Domains Framework of behaviour change to "
        "investigate implementation problems. Implementation Science, 12(1), 1–18."
    ),
}


def citation_for_framework(framework: str) -> str:
    return THEORY_CITATIONS.get(
        framework,
        "No primary citation for this framework is listed in the linked source; add a citation.",
    )


MEASURE_CATALOG_PATH = Path(__file__).resolve().parent / "catalogs" / "measure_catalog.json"
MEASURE_CATALOG_REQUIRED_FIELDS = {
    "measure_id",
    "discipline",
    "study_area",
    "variable",
    "theory_framework",
    "measure_name",
    "population_context",
    "response_format",
    "scoring",
    "validity_evidence",
    "reliability_evidence",
    "citation",
    "doi_url",
    "source_url",
    "license",
    "notes",
}


def load_measure_catalog() -> list[dict]:
    with MEASURE_CATALOG_PATH.open(encoding="utf-8") as catalog_file:
        catalog = json.load(catalog_file)
    if not isinstance(catalog, dict) or not isinstance(catalog.get("measures"), list):
        raise ValueError("Catalog must be a JSON object containing a 'measures' list.")
    if catalog.get("catalog_version") != 1:
        raise ValueError("Unsupported measure catalog version.")
    for index, measure in enumerate(catalog["measures"]):
        if not isinstance(measure, dict):
            raise ValueError(f"Catalog entry {index + 1} must be a JSON object.")
        missing_fields = MEASURE_CATALOG_REQUIRED_FIELDS - measure.keys()
        if missing_fields:
            raise ValueError(
                f"Catalog entry {index + 1} is missing fields: "
                f"{', '.join(sorted(missing_fields))}."
            )
    return catalog["measures"]


def find_measure_suggestions(
    catalog: list[dict],
    variable: str,
    frameworks: list[str],
    study_areas: list[str],
) -> list[dict]:
    variable_key = variable.strip().casefold()
    framework_keys = {value.strip().casefold() for value in frameworks if value.strip()}
    study_area_keys = {value.strip().casefold() for value in study_areas if value.strip()}
    matches = []
    for measure in catalog:
        catalog_variable = str(measure["variable"]).strip().casefold()
        if catalog_variable not in {"", "*", variable_key}:
            continue
        catalog_frameworks = measure["theory_framework"]
        if isinstance(catalog_frameworks, str):
            catalog_frameworks = [catalog_frameworks] if catalog_frameworks else []
        catalog_framework_keys = {
            str(value).strip().casefold()
            for value in catalog_frameworks
            if str(value).strip()
        }
        if framework_keys and catalog_framework_keys and not framework_keys.intersection(catalog_framework_keys):
            continue
        catalog_disciplines = measure["discipline"]
        if isinstance(catalog_disciplines, str):
            catalog_disciplines = [catalog_disciplines] if catalog_disciplines else []
        catalog_discipline_keys = {
            str(value).strip().casefold()
            for value in catalog_disciplines
            if str(value).strip()
        }
        if study_area_keys and catalog_discipline_keys and not study_area_keys.intersection(catalog_discipline_keys):
            continue
        catalog_areas = measure["study_area"]
        if isinstance(catalog_areas, str):
            catalog_areas = [catalog_areas] if catalog_areas else []
        catalog_area_keys = {
            str(value).strip().casefold()
            for value in catalog_areas
            if str(value).strip()
        }
        if study_area_keys and catalog_area_keys and not study_area_keys.intersection(catalog_area_keys):
            continue
        matches.append(measure)
    return matches

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

# Engine selection sidebar routing
st.sidebar.header("⚙️ Core Controls")
app_mode = st.sidebar.radio(
    "Navigate Workspace Module:",
    [
        "About this app",
        "1. Study Metadata Schema Registry",
        "2. Variable Instrument Architect",
        "3. Community Data Repository Sync",
        "4. Descriptive & Scale Analytics",
        "5. Live Central Database Viewer"
    ],
    key="app_mode"
)

if "token_hash" in st.query_params:
    try:
        if st.query_params.get("type") != "email":
            raise ValueError("The sign-in link has an unsupported token type.")
        auth_client = create_supabase_client()
        auth_response = auth_client.auth.verify_otp({
            "token_hash": st.query_params["token_hash"],
            "type": st.query_params["type"]
        })
        if auth_response.session:
            store_auth_session(auth_response.session)
            st.session_state["auth_notice"] = "Email sign-in confirmed."
        else:
            raise ValueError("Supabase verified the link but did not return an active session.")
        st.query_params.clear()
    except Exception as auth_error:
        st.session_state["auth_error"] = f"Could not verify the sign-in link: {auth_error}"
        st.query_params.clear()

user_client, current_user_id = authenticated_supabase_client()

with st.sidebar:
    st.divider()
    st.subheader("🔐 Researcher account")
    if current_user_id:
        auth_email = st.session_state["supabase_auth"].get("email") or "Signed-in researcher"
        st.caption(f"Signed in as {auth_email}")
        if st.button("Sign out", use_container_width=True):
            try:
                if user_client:
                    user_client.auth.sign_out()
            finally:
                st.session_state.pop("supabase_auth", None)
                st.rerun()
    else:
        if st.session_state.get("auth_notice"):
            st.success(st.session_state.pop("auth_notice"))
        if st.session_state.get("auth_error"):
            st.error(st.session_state.pop("auth_error"))
        with st.form("email_magic_link_form"):
            login_email = st.text_input("Email address", key="login_email")
            send_magic_link = st.form_submit_button("Email me a sign-in link")
        if send_magic_link:
            try:
                redirect_url = str(st.secrets["APP_URL"]).strip().rstrip("/")
                if not login_email.strip() or not redirect_url:
                    raise ValueError("Enter a valid email address and configure APP_URL.")
                auth_client = create_supabase_client()
                auth_client.auth.sign_in_with_otp({
                    "email": login_email.strip(),
                    "options": {
                        "email_redirect_to": redirect_url,
                        "should_create_user": True
                    }
                })
                st.success("Check your email for a secure sign-in link.")
            except Exception as auth_error:
                st.error(f"Could not send the sign-in link: {auth_error}")

st.title("🔬 Open Educational Metadata Portal")
st.caption("Standardized Study Registries and Psychometric Instrument Architects under DCMES, IEEE LOM, and CEDS Standards.")

value_propositions = [
    (
        "1. Study Metadata Schema Registry",
        "📐 Enforcing Metadata Standards",
        "Standardizes metadata norms systematically across independent studies to ensure deep "
        "searchability and cross-institutional compatibility.",
        "1. Study Metadata Schema Registry",
        [
            "Describe the study, research team, population, and design.",
            "Record its content domain or topic and study context.",
            "Document ethics, permissions, and data-stewardship metadata.",
        ],
    ),
    (
        "2. Variable Instrument Architect",
        "🗺️ Theoretical-to-Variable Mapping",
        "Directly assists researchers in building out robust study designs derived from "
        "conceptual frameworks seamlessly linked to operational variables.",
        "2. Variable Instrument Architect",
        [
            "Find related study summaries shared by other researchers.",
            "Select frameworks and variables; define measurement and questionnaire metadata.",
            "Build a conceptual diagram and download variable matrices and a draft survey.",
        ],
    ),
    (
        "3. Community Data Repository Sync",
        "🌍 Global Open-Data Ingestion",
        "Bridges individual datasets directly onto a unified global sharing infrastructure "
        "for frictionless, public-facing discovery.",
        "3. Community Data Repository Sync",
        [
            "Review permissions, identifiers, and disclosure risks.",
            "Upload datasets to private or public storage with explicit confirmation.",
            "Review datasets available to your account.",
        ],
    ),
    (
        "4. Descriptive & Scale Analytics",
        "📊 Comparative Meta-Analytics",
        "Maps observed dataset columns to the theory-derived, demographic/contextual, and custom "
        "variables defined in Module 2, then supports descriptive, composite-score, reliability, "
        "and relationship analyses.",
        "4. Descriptive & Scale Analytics",
        [
            "Select a dataset and map its columns to Module 2 variables.",
            "Inspect distributions, descriptive statistics, and categorical responses.",
            "Review composite scores, reliability, correlations, and download a report.",
        ],
    ),
    (
        "5. Live Central Database Viewer",
        "🧪 Validated Measurement Registry",
        "Offers a vetted repository of reliable and psychometrically valid instruments to "
        "measure complex human and behavioral variables accurately.",
        "5. Live Central Database Viewer",
        [
            "Select a repository table available to your account.",
            "Browse authorized records and check whether the table contains data.",
            "Download the displayed table as CSV.",
        ],
    ),
]

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
        repo_path = "JLib271/OpenEdMetadata" 
        repo = g.get_repo(repo_path)
        
        # 3. Establish structural branch identifiers
        main_branch = repo.get_branch("main")
        unique_timestamp = int(time.time())
        unique_suffix = uuid.uuid4().hex[:8]
        new_branch_name = f"proposal-{suggestion_type.lower()}-{unique_timestamp}-{unique_suffix}"
        
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


def navigate_to_module(module: str) -> None:
    st.session_state["app_mode"] = module


def render_value_card(
    card: tuple[str, str, str, str, list[str]],
    show_open_button: bool = False,
) -> None:
    module_title, solution_title, description, module, actions = card
    with st.container(border=True):
        card_label, card_content = st.columns([1.4, 3.6], vertical_alignment="center")
        with card_label:
            if app_mode == module:
                st.success("Current module")
                st.markdown(f"### {module_title}")
            else:
                st.markdown(f"#### {module_title}")
        with card_content:
            st.markdown(f"**{solution_title}**")
            st.markdown(description)
            st.markdown("**What you'll do in this module:**")
            st.markdown("\n".join(f"- {action}" for action in actions))
            if show_open_button:
                st.button(
                    f"Open {module_title}",
                    key=f"open_{module.replace(' ', '_').replace('.', '')}",
                    on_click=navigate_to_module,
                    args=(module,),
                    type="primary"
                )


if app_mode == "About this app":
    st.header("🔬 Accelerating Human Science & Educational Research")
    st.markdown(
        "This platform is specifically engineered to resolve the most critical bottlenecks in "
        "human science research—particularly within educational ecosystems—by enforcing data "
        "structural integrity and empowering open-science collaboration."
    )
    for value_card in value_propositions:
        render_value_card(value_card, show_open_button=True)
else:
    st.button(
        "← About this app",
        key="back_to_about",
        on_click=navigate_to_module,
        args=("About this app",)
    )
    active_card = next(card for card in value_propositions if card[3] == app_mode)
    render_value_card(active_card)

st.markdown("---")

preview_mode = app_mode != "About this app" and not current_user_id
if preview_mode:
    st.info(
        "Module preview: this is the actual module interface. Enter your email in the sidebar "
        "to receive a secure sign-in link before saving information, submitting proposals, "
        "uploading datasets, or accessing account data."
    )

# ==========================================
# MODULE 1: STUDY-LEVEL METADATA REGISTRY
# ==========================================
if app_mode == "1. Study Metadata Schema Registry":
    st.header("1. Study Metadata Schema Registry")
    st.caption("Document the study, its design and population, and the ethical and data-governance context needed for responsible sharing.")
    st.markdown("---")
    
    # --- DYNAMIC AUTHOR TRACKING INITIALIZATION ---
    if "authors_list" not in st.session_state:
        st.session_state.authors_list = [{"name": "", "orcid": ""}]

    with st.container(border=True):
        st.subheader("Step 1 — Study Team")
        st.caption("Add study creators and their ORCID iDs. At least one author name is required.")

        updated_authors = []
        for idx, author in enumerate(st.session_state.authors_list):
            col_name, col_orcid, col_del = st.columns([2, 2, 0.5], vertical_alignment="bottom")

            with col_name:
                auth_name = st.text_input(
                    f"Author {idx + 1} Name",
                    value=author["name"],
                    key=f"auth_name_{idx}",
                    placeholder="e.g., Dr. Jane Doe",
                    help="Enter the author's full name as it should appear in the study record."
                )
            with col_orcid:
                auth_orcid = st.text_input(
                    f"Author {idx + 1} ORCID iD",
                    value=author["orcid"],
                    key=f"auth_orcid_{idx}",
                    placeholder="https://orcid.org/0000-0000-0000-0000",
                    help="Enter a full ORCID URL or ORCID identifier (format: 0000-0000-0000-0000)."
                )
            with col_del:
                if st.button(
                    "🗑️",
                    key=f"auth_del_{idx}",
                    disabled=len(st.session_state.authors_list) <= 1,
                    help="Remove this author."
                ):
                    st.session_state.authors_list.pop(idx)
                    st.rerun()

            updated_authors.append({"name": auth_name, "orcid": auth_orcid})

        st.session_state.authors_list = updated_authors
        if st.button("➕ Add Author", help="Add another study creator."):
            st.session_state.authors_list.append({"name": "", "orcid": ""})
            st.rerun()

    # --- MAIN SUBMISSION FORM ---
    with st.form("metadata_standards_form", clear_on_submit=False):
        with st.container(border=True):
            st.subheader("Step 2 — Study Identity")
            st.caption("Core Dublin Core metadata. Fields marked * are required.")
            title = st.text_input(
                "Study title (dc:title) *",
                placeholder="e.g., Impact of Open Textbooks on Course-Level Retention",
                help="Use the full, descriptive title that should appear in study catalogs."
            )
            detail_col1, detail_col2 = st.columns(2)
            with detail_col1:
                keywords = st.text_input(
                    "Subject keywords (dc:subject)",
                    placeholder="OER, student motivation, retention",
                    help="Separate keywords with commas; these improve study discovery."
                )
            with detail_col2:
                language = st.selectbox(
                    "Language (dc:language)",
                    options=["English (en)", "Spanish (es)", "French (fr)", "Other / Multilingual"],
                    help="Select the primary language used in the study materials."
                )
            study_identifier = st.text_input(
                "Study DOI or persistent identifier",
                placeholder="e.g., DOI or repository accession",
                help="Use the same persistent identifier in Module 2 when documenting variables and measures.",
            )
            context_col1, context_col2 = st.columns(2)
            with context_col1:
                institution = st.text_input(
                    "Institution or organization",
                    placeholder="e.g., Example University",
                )
            with context_col2:
                funding_source = st.text_input(
                    "Funding source",
                    placeholder="Name funder or enter Not funded",
                )
            description = st.text_area(
                "Description / abstract (dc:description)",
                placeholder="Summarize the research objectives, design, and findings...",
                help="Provide a concise summary of the study and its research context."
            )
            research_questions = st.text_area(
                "Research questions and aims",
                placeholder="List the primary research questions, objectives, or hypotheses.",
                help="Record the questions or aims that guide the study and its measures."
            )

        with st.container(border=True):
            st.subheader("Step 3 — Study Design and Context (DDI / CEDS)")
            st.caption(
                "Describe the unit, collection approach, sampling, and study timeline across human-science "
                "research, including studies in formal institutions, informal settings, and the general public."
            )
            ddi_col1, ddi_col2 = st.columns(2)
            with ddi_col1:
                unit_of_analysis = st.selectbox(
                    "Unit of analysis",
                    options=UNIT_OF_ANALYSIS_OPTIONS,
                    help="Identify the person, group, organization, place, event, or artifact about which observations are made."
                )
            with ddi_col2:
                sampling_procedure = st.selectbox(
                    "Sampling procedure",
                    options=SAMPLING_PROCEDURE_OPTIONS,
                    help="Select the approach used to recruit or select participants, visitors, groups, organizations, or sites."
                )
                time_method = st.selectbox(
                    "Study design / time method",
                    options=[
                        "Cross-sectional / Single Time Point Assessment",
                        "Longitudinal: Cohort Study / Repeated Measures",
                        "Longitudinal: Trend / Multiple Intervals",
                        "Experimental / Pre-Post Testing",
                        "Time Series Analysis"
                    ],
                    help="Choose the temporal design that best describes the study."
                )

        st.subheader("Step 4 — Study Scope and Population (CEDS)")
        st.caption(
            "Describe the study period, locations, settings, and people or other populations involved. "
            "This includes education research as well as human-science research with community members, "
            "the general public, museum visitors, and other informal-space participants."
        )
        with st.container(border=True):
            st.markdown("**Study period and location**")
            study_dates = st.date_input(
                "Study start and end dates",
                value=(),
                format="YYYY-MM-DD",
                help="Choose the start date and then the end date. Leave blank if dates are not known or cannot be shared.",
            )
            scope_col1, scope_col2 = st.columns(2)
            with scope_col1:
                state_origin = st.selectbox(
                    "State / geographic origin",
                    options=["National/Multi-State", "AK", "AL", "AR", "AZ", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "IA", "ID", "IL", "IN", "KS", "KY", "LA", "MA", "MD", "ME", "MI", "MN", "MO", "MS", "MT", "NC", "ND", "NE", "NH", "NJ", "NM", "NV", "NY", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VA", "VT", "WA", "WI", "WV", "WY"],
                    help="Choose the state or geographic scope where the study was conducted."
                )
            with scope_col2:
                locale_setting = st.selectbox(
                    "Locale",
                    options=[
                        "City", "Suburban", "Town", "Rural",
                        "Virtual / Online Environment", "Multiple / mixed locations",
                    ],
                    help="Choose the geographic or virtual setting type."
                )

        with st.container(border=True):
            st.markdown("**Population, age or education level, and participation context**")
            participant_populations = st.multiselect(
                "Participant population(s)",
                options=[
                    "General public / community members",
                    "Museum, gallery, library, or science-center visitors",
                    "Event, exhibition, or festival visitors",
                    "Children or youth",
                    "Adults",
                    "Older adults",
                    "Families or household groups",
                    "Students / learners",
                    "Teachers / educators",
                    "Researchers / professionals",
                    "Specific community or cultural group",
                    "Other / not listed",
                ],
                help="Select all populations included, whether or not participants are in a formal education program.",
            )
            study_settings = st.multiselect(
                "Study setting(s)",
                options=[
                    "K-12 school or classroom",
                    "College, university, or other postsecondary institution",
                    "Museum, gallery, or cultural institution",
                    "Library or science center",
                    "Community organization or public space",
                    "Home or family setting",
                    "Workplace or professional setting",
                    "Public event, exhibition, or festival",
                    "Online or virtual environment",
                    "Multiple settings",
                    "Other / not listed",
                ],
                help="Select where participation, observation, or data collection occurs.",
            )
            grade_level = st.multiselect(
                "Age / education level or learning setting",
                options=EDUCATION_LEVEL_OPTIONS,
                help="Use this for age-relevant or education context; general-public and visitor studies are included.",
            )
            undergraduate_level = st.multiselect(
                "Undergraduate level, if applicable",
                options=UNDERGRADUATE_LEVEL_OPTIONS,
                help="Select all undergraduate levels represented, from entry-level through advanced and capstone study.",
            )
            program_type = st.multiselect(
                "Program, organization, or participation context",
                options=PROGRAM_TYPE_OPTIONS,
                help="Select a formal program or an informal, community, visitor, or general-public participation context.",
            )

        with st.container(border=True):
            st.markdown("**Content domain or topic**")
            content_domain = st.text_input(
                "Content domain or topic",
                placeholder="e.g., climate science, teacher professional learning, community health",
                help="Describe the main subject or topic area of the study in your own words.",
                key="module1_content_domain",
            )

        # --- SUBMIT BUTTON & VALIDATION (INSIDE THE FORM CONTAINER) ---
        st.subheader("Step 5 — Ethics, Permissions, and Data Stewardship")
        st.caption(
            "Record researcher-reported governance context. These fields do not verify approvals "
            "or determine whether data may be shared."
        )
        ethics_col1, ethics_col2 = st.columns(2)
        with ethics_col1:
            review_status = st.selectbox(
                "Human-subjects / ethics review status",
                options=[
                    "Not yet assessed",
                    "Submitted / pending",
                    "Approved",
                    "Exempt determination received",
                    "Not required — determination received",
                    "Other / not listed",
                ],
            )
            consent_model = st.selectbox(
                "Participant consent or authorization",
                options=[
                    "Not yet assessed",
                    "Informed consent obtained",
                    "Parent/guardian permission and participant assent",
                    "Waiver or alteration approved",
                    "Not applicable — determination received",
                    "Other / not listed",
                ],
            )
        with ethics_col2:
            data_sensitivity = st.multiselect(
                "Data sensitivity and identifiers",
                options=[
                    "No direct identifiers expected",
                    "Direct identifiers",
                    "Indirect identifiers / small groups",
                    "Sensitive personal information",
                    "Education records",
                    "Not yet assessed",
                ],
            )
            sharing_plan = st.selectbox(
                "Planned data access",
                options=[
                    "Not yet assessed",
                    "No data sharing planned",
                    "Private — owner only",
                    "Controlled access through an external repository",
                    "Public release planned, pending review",
                ],
                help="This records a plan only. Module 3 separately requires permissions and privacy review before upload or public release.",
            )
        governance_notes = st.text_area(
            "Approval references, data-use restrictions, and governance notes",
            placeholder="Optional: oversight reference, agreement restrictions, retention or de-identification requirements.",
        )

        submit_metadata = st.form_submit_button("Save Study Metadata", disabled=preview_mode)
        
        if submit_metadata:
            has_author = any(auth["name"].strip() for auth in st.session_state.authors_list)
            
            if not title:
                st.error("Study title is required.")
            elif not has_author:
                st.error("At least one Creator/Author Name is required.")
            else:
                submission_status = None
                try:
                    with st.status("Connecting to Supabase and saving the study record...", expanded=False) as submission_status:
                        # Keep author details structured in the study description.
                        authors = [
                            {
                                "name": str(auth.get("name") or "").strip(),
                                "orcid": str(auth.get("orcid") or "").strip()
                            }
                            for auth in st.session_state.authors_list
                        ]
                        authors = [author for author in authors if author["name"] or author["orcid"]]
                        authors_string = ", ".join(
                            author["name"] for author in authors if author["name"]
                        )
                        study_date_range = study_dates if isinstance(study_dates, (tuple, list)) else ()
                        study_start_date = (
                            study_date_range[0].isoformat()
                            if len(study_date_range) >= 1 and study_date_range[0]
                            else ""
                        )
                        study_end_date = (
                            study_date_range[1].isoformat()
                            if len(study_date_range) >= 2 and study_date_range[1]
                            else ""
                        )
                        
                        # Preserve every form value in the existing studies table schema.
                        study_metadata = {
                            "authors": authors,
                            "study_doi_or_persistent_identifier": str(study_identifier or "").strip(),
                            "institution": str(institution or "").strip(),
                            "funding_source": str(funding_source or "").strip(),
                            "research_questions_and_aims": str(research_questions or "").strip(),
                            "subject_keywords": str(keywords or "").strip(),
                            "language": str(language or "").strip(),
                            "unit_of_analysis": str(unit_of_analysis or "").strip(),
                            "sampling_procedure": str(sampling_procedure or "").strip(),
                            "time_method": str(time_method or "").strip(),
                            "study_start_date": study_start_date,
                            "study_end_date": study_end_date,
                            "state_origin": str(state_origin or "").strip(),
                            "locale_setting": str(locale_setting or "").strip(),
                            "participant_populations": participant_populations or [],
                            "study_settings": study_settings or [],
                            "grade_level": grade_level or [],
                            "undergraduate_level": undergraduate_level or [],
                            "program_type": program_type or [],
                            "content_domain": str(content_domain or "").strip(),
                            "ethics_review_status": str(review_status or "").strip(),
                            "consent_or_authorization": str(consent_model or "").strip(),
                            "data_sensitivity_and_identifiers": data_sensitivity or [],
                            "planned_data_access": str(sharing_plan or "").strip(),
                            "governance_notes": str(governance_notes or "").strip()
                        }
                        description_record = {
                            "description": str(description or "").strip() or "No description provided.",
                            "metadata": study_metadata
                        }

                        # The documented Supabase table has five columns; keep this insert
                        # compatible while retaining the complete form as structured text.
                        db_payload = {
                            "study_title": str(title).strip(),
                            "principal_investigator": authors_string,
                            "institution": str(institution or "").strip(),
                            "funding_source": str(funding_source or "").strip(),
                            "study_description": json.dumps(description_record, ensure_ascii=False),
                            "user_id": current_user_id
                        }
                        
                        user_client.table("studies").insert(db_payload).execute()
                        submission_status.update(
                            label="Study record saved to Supabase.",
                            state="complete",
                            expanded=False
                        )
                        
                        # Reset authors list back to a clean default state for the next entry session
                        st.session_state.authors_list = [{"name": "", "orcid": ""}]
                    st.success(f"Study record saved: {title.strip()}")
                except Exception as form_db_error:
                    if submission_status is not None:
                        submission_status.update(
                            label="Could not save the study record.",
                            state="error",
                            expanded=True
                        )
                    st.error(f"Failed to transmit data to the central repository: {form_db_error}")


    # --- MODULE 1 EXTENSION PIPELINE BUTTON ---
    st.markdown("---")
    st.markdown("### 🚀 Propose Extensions to Core Study Metadata Architecture")
    st.caption("Suggest new Dublin Core (DCMES) descriptors, alternative CEDS geographic drop-down indicators, or updated standard options.")
    
    with st.expander("💡 Click to Draft a Metadata Schema Suggestion"):
        suggested_schema_field = st.text_input("Target Element / Field Code to Change", placeholder="e.g., CEDS Section 2 - Alternative Grade Classifications", key="mod1_suggest_field")
        suggested_schema_text = st.text_area("Detailed Suggestion / Additions Details", placeholder="Describe new drop-down selections, alternative labels, or documentation requirements...", key="mod1_suggest_text")
        
    if suggested_schema_field and suggested_schema_text:
            # Bypasses multi-line quotation leaks completely using isolated string tuples
            schema_payload = (
                f"**Study Metadata Architecture Amendment Proposal**\n\n"
                f"**Target Element:** {suggested_schema_field}\n\n"
                f"### PROPOSED ALTERNATIVE SELECTIONS / LABELS\n"
                f"```text\n{suggested_schema_text}\n```\n\n"
                f"---\n*Submitted securely via the Study Metadata Schema Registry Interface Box.*"
            )
            
            st.markdown("##### **Submit Change Directly to GitHub**")
            st.caption("Clicking the button below will automatically fork a branch, save your suggestion, and issue a formal pull request.")
            
            # This triggers your automated PyGithub pipeline function
            if st.button(
                "🚀 Push Proposal to GitHub as Pull Request",
                key="submit_mod1_pr_btn",
                disabled=preview_mode,
            ):
                with st.spinner("Talking to GitHub API, creating branch, and launching Pull Request..."):
                    safe_filename = f"metadata_proposal_{suggested_schema_field.lower().replace(' ', '_')}.txt"
                    summary_title = f"Update Metadata Section: {suggested_schema_field}"
                    
                    result_message = automate_github_pull_request(
                        suggestion_type="Metadata",
                        file_name=safe_filename,
                        file_content=schema_payload,
                        title_summary=summary_title
                    )
                    
                    if "❌" in result_message:
                        st.error(result_message)
                    else:
                        st.success(result_message)


# ==========================================
# MODULE 2: VARIABLE ARCHITECT & INSTRUMENT EXPORTER
# ==========================================
elif app_mode == "2. Variable Instrument Architect":
    st.header("2. Variable Instrument Architect")
    st.caption(
        "Select theories, models, or frameworks; review their associated factors; then plan "
        "how those factors will be measured in your study."
    )
    st.markdown("---")
    
    st.subheader("Study context (optional)")
    st.caption("Choose a saved Module 1 study to reference its context. Theory and measurement planning now happens here.")

    saved_studies = []
    if not preview_mode:
        try:
            saved_studies = (
                user_client.table("studies")
                .select("id,study_title,study_description,created_at")
                .eq("user_id", current_user_id)
                .order("created_at", desc=True)
                .execute()
                .data
                or []
            )
        except Exception as study_error:
            st.error(f"Could not load your saved Module 1 studies: {study_error}")

    selected_study = None
    study_metadata = {}
    saved_module2_plan = {}
    if saved_studies:
        selected_study = st.selectbox(
            "Saved study",
            options=saved_studies,
            format_func=lambda study: study.get("study_title") or "Untitled study",
            key="module2_source_study",
        )
        try:
            description_record = json.loads(selected_study.get("study_description") or "{}")
            if isinstance(description_record, dict):
                study_metadata = description_record.get("metadata", {})
                if not isinstance(study_metadata, dict):
                    study_metadata = {}
        except (TypeError, json.JSONDecodeError):
            st.warning("This study's saved metadata could not be read as structured JSON.")
            study_metadata = {}
        try:
            plan_response = (
                user_client.table("study_module2_plans")
                .select("plan_json")
                .eq("study_id", selected_study["id"])
                .eq("owner_id", current_user_id)
                .maybe_single()
                .execute()
            )
            if plan_response.data:
                plan_json = plan_response.data.get("plan_json", {})
                if isinstance(plan_json, str):
                    plan_json = json.loads(plan_json)
                if isinstance(plan_json, dict):
                    saved_module2_plan = plan_json
        except Exception as plan_error:
            st.error(
                "Could not load this study's saved Module 2 plan. Confirm that "
                "supabase/setup_auth_storage.sql has been applied: "
                f"{plan_error}"
            )
        with st.expander("Study context from Module 1"):
            st.write(f"**Study:** {selected_study.get('study_title') or 'Untitled study'}")
            st.write(f"**Persistent identifier:** {study_metadata.get('study_doi_or_persistent_identifier') or 'Not provided'}")
            st.write(f"**Unit of analysis:** {study_metadata.get('unit_of_analysis') or 'Not specified'}")
            st.write(f"**Population:** {', '.join(study_metadata.get('participant_populations', [])) or 'Not specified'}")
            st.write(f"**Study settings:** {', '.join(study_metadata.get('study_settings', [])) or 'Not specified'}")
            st.write(f"**Study period:** {study_metadata.get('study_start_date') or 'Not specified'} to {study_metadata.get('study_end_date') or 'Not specified'}")
    elif preview_mode:
        st.info("Sign in and save a study in Module 1 to include saved study context.")
        study_metadata = {
            "study_title": "Example study (preview only)",
            "unit_of_analysis": "Individual (person / participant)",
        }
    else:
        st.info("No saved studies found. You can still build a standalone theory and measurement draft.")
    repository_id = study_metadata.get("study_doi_or_persistent_identifier", "")
    unit_of_analysis = study_metadata.get("unit_of_analysis", "Not specified")
    sampling_method = study_metadata.get("sampling_procedure", "Not specified")
    sampling_procedure = ""
    if study_metadata.get("sampling_procedure"):
        sampling_procedure = str(study_metadata["sampling_procedure"])

    workflow_key = selected_study.get("id") if selected_study else ("preview" if preview_mode else "draft")
    st.subheader("Find previously shared studies with related context")
    st.caption(
        "Search summaries that researchers have explicitly shared. Use a topic, population, "
        "setting, or other context; results are design examples, not validated recommendations."
    )
    discovery_query = st.text_input(
        "Study context to search",
        value=str(
            saved_module2_plan.get("study_context", {}).get("content_domain")
            or study_metadata.get("content_domain", "")
            if isinstance(saved_module2_plan.get("study_context", {}), dict)
            else study_metadata.get("content_domain", "")
        ),
        placeholder="e.g., climate science education in high-school classrooms",
        key=f"module2_discovery_query_{workflow_key}",
    )
    search_terms = context_search_terms(discovery_query)
    if preview_mode:
        st.info("Sign in to search study summaries that researchers have explicitly shared for discovery.")
    elif search_terms:
        try:
            shared_studies = (
                user_client.table("study_discovery")
                .select(
                    "study_id,study_title,context_tags,study_metadata,published_at"
                )
                .order("published_at", desc=True)
                .limit(500)
                .execute()
                .data
                or []
            )
            scored_studies = []
            query_terms = set(search_terms)
            for shared_study in shared_studies:
                shared_terms = set(shared_study.get("context_tags") or [])
                overlap = query_terms & shared_terms
                if overlap:
                    score = len(overlap) / len(query_terms | shared_terms)
                    scored_studies.append((score, shared_study))
            scored_studies.sort(key=lambda result: result[0], reverse=True)
            if not shared_studies:
                st.info(
                    "No studies have been shared for context discovery yet. This search will show "
                    "opted-in study summaries as they become available."
                )
            elif not scored_studies:
                st.info("No shared study summaries matched these context terms.")
            else:
                for similarity, shared_study in scored_studies[:5]:
                    with st.expander(
                        f"{shared_study.get('study_title') or 'Shared study'} "
                        f"— context match {similarity:.0%}"
                    ):
                        metadata = shared_study.get("study_metadata") or {}
                        if isinstance(metadata, str):
                            try:
                                metadata = json.loads(metadata)
                            except json.JSONDecodeError:
                                metadata = {}
                        if isinstance(metadata, dict):
                            st.write(f"**Context:** {metadata.get('context_summary') or 'Not specified'}")
                            st.write(f"**Study design:** {metadata.get('time_method') or 'Not specified'}")
                            st.write(f"**Unit of analysis:** {metadata.get('unit_of_analysis') or 'Not specified'}")
                            for field, label in (
                                ("participant_populations", "Population"),
                                ("study_settings", "Setting"),
                                ("content_domain", "Content domain"),
                                ("selected_theories", "Frameworks"),
                            ):
                                values = metadata.get(field, [])
                                st.write(f"**{label}:** {', '.join(values) if isinstance(values, list) else values or 'Not specified'}")
                            shared_variables = metadata.get("variables", [])
                            if isinstance(shared_variables, list) and shared_variables:
                                st.markdown("**Shared variable and measurement metadata**")
                                st.dataframe(
                                    pd.DataFrame(shared_variables),
                                    hide_index=True,
                                    use_container_width=True,
                                )
                        st.caption(
                            "Use these records as design examples, not as evidence that a measure is "
                            "valid for your study. Item text and participant data are not shared."
                        )
        except Exception as discovery_error:
            st.error(
                "Could not search shared study summaries. Confirm that "
                "supabase/setup_auth_storage.sql has been applied: "
                f"{discovery_error}"
            )
    else:
        st.info("Enter a topic, population, setting, or other context to search shared studies.")

    st.subheader("Step 1 — Define study context and choose frameworks")
    st.markdown("**Describe the study's content and context**")
    st.caption(
        "This step supports a broad range of educational and social-science studies. Add a target "
        "behavior only when it is relevant to your study; it is not assumed to be the outcome."
    )
    saved_study_context = saved_module2_plan.get("study_context", {})
    if not isinstance(saved_study_context, dict):
        saved_study_context = {}
    content_domain = str(
        saved_study_context.get("content_domain")
        or study_metadata.get("content_domain", "")
    ).strip()
    if content_domain:
        st.write(f"**Content domain or topic from Module 1:** {content_domain}")
    target_action = st.text_input(
        "Target behavior / action (optional; if relevant)",
        value=str(saved_study_context.get("target_action", "")),
        placeholder="e.g., choose a lower-carbon travel option; leave blank if not relevant",
        key=f"module2_target_action_{workflow_key}",
    )
    context_description = st.text_input(
        "Specific context",
        value=str(saved_study_context.get("context", "")),
        placeholder="e.g., high-school science classrooms in rural communities",
        help="Describe the study population, setting, or circumstances; it need not describe a behavior.",
        key=f"module2_context_description_{workflow_key}",
    )
    timeframe = st.text_input(
        "Timeframe (optional; if relevant)",
        value=str(saved_study_context.get("timeframe", "")),
        placeholder="e.g., during the next semester",
        key=f"module2_timeframe_{workflow_key}",
    )
    content_tags = st.text_input(
        "Additional content tags (comma-separated)",
        value=str(saved_study_context.get("content_tags", "")),
        placeholder="e.g., sustainability, secondary education",
        key=f"module2_content_tags_{workflow_key}",
    )
    share_study_for_discovery = False
    if selected_study and not preview_mode:
        share_study_for_discovery = st.checkbox(
            "Share a limited study summary with signed-in researchers for context discovery",
            value=bool(saved_module2_plan.get("share_for_discovery", False)),
            help=(
                "Sharing includes the study title, selected study-design metadata, theory constructs, "
                "and measurement metadata. It never includes participant data or item text. "
                "Only share information you are authorized to make discoverable."
            ),
            key=f"module2_share_discovery_{workflow_key}",
        )
    st.markdown("**Select theories, models, or frameworks**")
    st.caption(
        "Choose one or more established frameworks. Each selection brings in its associated factors "
        "and the source citations listed for that framework. Review them as theory-informed starting points."
    )
    theory_choice_options = list(THEORY_MAP) + ["Other (write in)"]
    saved_frameworks = saved_module2_plan.get("selected_theories", [])
    if not isinstance(saved_frameworks, list):
        saved_frameworks = []
    saved_custom_frameworks = [
        framework for framework in saved_frameworks
        if framework not in THEORY_MAP
    ]
    default_theory_choices = [
        framework for framework in saved_frameworks if framework in THEORY_MAP
    ]
    if saved_custom_frameworks:
        default_theory_choices.append("Other (write in)")
    elif preview_mode:
        default_theory_choices = ["Theory of Planned Behavior (TPB)"]
    selected_theories = st.multiselect(
        "Theory, model, or framework",
        options=theory_choice_options,
        default=default_theory_choices,
        help="Select all theories, models, and frameworks that inform this study.",
        key=f"module2_theories_{workflow_key}",
    )
    other_theory_names = ""
    if "Other (write in)" in selected_theories:
        other_theory_names = st.text_input(
            "Other theory, model, or framework name(s)",
            value=", ".join(saved_custom_frameworks),
            placeholder="Enter names separated by commas",
            key=f"module2_other_theory_names_{workflow_key}",
        )
        st.text_area(
            "Other framework source and key factors",
            value=str(saved_module2_plan.get(
                "other_theory_sources",
                "",
            )),
            placeholder="Cite a source and list its established constructs or factors. Measurement recommendations will be added in a future update.",
            key=f"module2_other_theory_sources_{workflow_key}",
        )
    other_framework_sources = st.session_state.get(
        f"module2_other_theory_sources_{workflow_key}",
        str(saved_module2_plan.get("other_theory_sources", "")),
    )
    selected_theories = [
        theory for theory in selected_theories if theory != "Other (write in)"
    ] + [
        theory.strip()
        for theory in other_theory_names.split(",")
        if theory.strip()
    ]
    selected_theories = list(dict.fromkeys(selected_theories))
    st.caption(
        "Factors and suggested paths are starting points, not definitive accounts. Verify them "
        "against the cited primary literature and your study context."
    )
    selected_citations = [
        f"{framework}: {citation_for_framework(framework)}"
        for framework in selected_theories
        if framework in THEORY_MAP
    ]
    if "Other (write in)" in st.session_state.get(
        f"module2_theories_{workflow_key}", []
    ):
        custom_citation = str(other_framework_sources).strip()
        if custom_citation:
            selected_citations.append(f"Researcher-entered source: {custom_citation}")
    if selected_citations:
        st.caption("Sources for selected theories, models, and frameworks:")
        st.markdown(
            "\n".join(f"- {citation}" for citation in selected_citations),
            help="References are those cited in the linked theory guide; verify the source details before use.",
        )

    st.subheader("Step 2 — Select Theory-Aligned Variables")
    st.caption(
        "The selected frameworks provide a starting set of theory-aligned variables. Include or "
        "remove each one, then choose any relevant demographic and contextual variables. Construct "
        "identity is stored separately from study content domain and tags."
    )
    if "Theory of Planned Behavior (TPB)" in selected_theories:
        st.info(
            "The TPB example creates three context-personalized prompts per included construct, "
            "with response scale, language, scoring, source, and adaptation metadata. These are "
            "illustrative, app-generated items—not a validated questionnaire. Review and revise "
            "all wording and scoring before use."
        )
    try:
        measure_catalog = load_measure_catalog()
    except (OSError, json.JSONDecodeError, ValueError) as catalog_error:
        measure_catalog = []
        st.error(f"Could not load the research measure catalog: {catalog_error}")
    selected_study_areas = [content_domain] if content_domain.strip() else []
    legacy_subject_areas = study_metadata.get("academic_subject_areas", [])
    if isinstance(legacy_subject_areas, str):
        legacy_subject_areas = [legacy_subject_areas]
    if isinstance(legacy_subject_areas, list):
        selected_study_areas.extend(
            value for value in legacy_subject_areas if isinstance(value, str)
        )
    selected_constructs_by_theory = {}
    for framework in selected_theories:
        if framework not in THEORY_MAP:
            continue
        with st.expander(f"{framework} — theory-derived variables", expanded=True):
            saved_variable_names = {
                str(row.get("Concept_Construct", ""))
                for row in saved_module2_plan.get("variables", [])
                if isinstance(row, dict)
                and row.get("Framework_Source") == framework
            }
            factor_key = (
                f"module2_factor_selection_{workflow_key}_"
                f"{framework.replace(' ', '_')}"
            )
            selected_constructs_by_theory[framework] = st.multiselect(
                "Theory-derived variables to include",
                options=THEORY_MAP[framework],
                default=[
                    factor for factor in THEORY_MAP[framework]
                    if factor in saved_variable_names
                ] if saved_module2_plan else THEORY_MAP[framework],
                help="Select the framework variables to include in your plan and conceptual diagram.",
                key=factor_key,
            )
    demographic_variable_options = [
        "Age",
        "Gender identity",
        "Race and ethnicity",
        "Socioeconomic status",
        "Home language / English learner status",
        "Disability / special education status",
        "Grade or education level",
        "School, district, or institution",
        "Geographic setting",
        "Undergraduate major / field of study",
        "Major or non-major status",
        "First-generation college status",
        "Enrollment / course status",
        "Other demographic or contextual variable",
    ]
    selected_demographic_variables = st.multiselect(
        "Core demographic and contextual variables",
        options=demographic_variable_options,
        default=saved_module2_plan.get("selected_demographic_variables", []),
        help="Choose only variables relevant to this study. No variables are selected by default.",
        key=f"module2_demographics_{workflow_key}",
    )
    other_demographic_variables = ""
    if "Other demographic or contextual variable" in selected_demographic_variables:
        other_demographic_variables = st.text_input(
            "Specify other demographic or contextual variables",
            value=str(saved_module2_plan.get("other_demographic_variables", "")),
            placeholder="Enter variables separated by commas",
            key=f"module2_other_demographics_{workflow_key}",
        )
    variable_fields = [
        "Data_Type",
        "Framework_Source",
        "Framework_ID",
        "Theory_Citation",
        "Concept_Construct",
        "Construct_ID",
        "Variable_ID",
        "Variable_Label",
        "Construct_Domain",
        "Content_Domain",
        "Content_Tags",
        "Behavioral_Target",
        "Target_Action",
        "Context",
        "Timeframe",
        "Operational_Definition",
        "Expected_Role",
        "Question_Item_or_Indicator",
        "Item_Text",
        "Item_Text_2",
        "Item_Text_3",
        "Response_Scale_or_Representation",
        "Response_Scale",
        "Language",
        "Scoring",
        "Measurement_Recommendation",
        "Instrument_Name",
        "Instrument_Citation",
        "Source_Citation",
        "Source_URL",
        "Item_Source_Type",
        "Adaptation_Notes",
        "Validation_Status",
        "Validity_Evidence",
        "Reliability_Evidence",
    ]

    def stable_identifier(value: str) -> str:
        return "_".join(
            part for part in "".join(
                char if char.isalnum() else " " for char in str(value)
            ).casefold().split()
        )

    def framework_short_name(framework: str) -> str:
        known_abbreviations = {
            "Theory of Planned Behavior (TPB)": "TPB",
            "Self-Determination Theory (SDT)": "SDT",
            "Technology Acceptance Model (TAM)": "TAM",
            "Health Belief Model (HBM)": "HBM",
        }
        if framework in known_abbreviations:
            return known_abbreviations[framework]
        words = str(framework).replace("(", " ").replace(")", " ").split()
        return "".join(word[0] for word in words if word).upper() or "FRAMEWORK"

    def prepare_variable_metadata(row: dict) -> dict:
        row = dict(row)
        framework = str(row.get("Framework_Source") or "")
        construct = str(row.get("Concept_Construct") or "")
        content_domain = str(row.get("Content_Domain") or ""        )
        row["Framework_ID"] = row.get("Framework_ID") or stable_identifier(framework)
        row["Construct_ID"] = row.get("Construct_ID") or stable_identifier(construct)
        row["Content_Domain"] = content_domain
        row["Construct_Domain"] = row.get("Construct_Domain") or "Unassigned"
        row["Content_Tags"] = row.get("Content_Tags") or ""
        row["Item_Text"] = row.get("Item_Text") or row.get("Question_Item_or_Indicator") or ""
        row["Item_Text_2"] = row.get("Item_Text_2") or ""
        row["Item_Text_3"] = row.get("Item_Text_3") or ""
        row["Question_Item_or_Indicator"] = (
            row["Item_Text"] or row.get("Question_Item_or_Indicator") or ""
        )
        row["Response_Scale"] = (
            row.get("Response_Scale") or row.get("Response_Scale_or_Representation") or ""
        )
        row["Response_Scale_or_Representation"] = (
            row["Response_Scale"] or row.get("Response_Scale_or_Representation") or ""
        )
        row["Source_Citation"] = row.get("Source_Citation") or row.get("Instrument_Citation") or ""
        row["Source_URL"] = row.get("Source_URL") or ""
        row["Item_Source_Type"] = row.get("Item_Source_Type") or ""
        row["Adaptation_Notes"] = row.get("Adaptation_Notes") or ""
        row["Validation_Status"] = "Not validated by this app; researcher review required"
        if framework and construct and content_domain:
            row["Variable_Label"] = (
                f"{framework_short_name(framework)}_"
                f"{stable_identifier(construct)}_{stable_identifier(content_domain)}"
            )
        elif not row.get("Variable_Label"):
            row["Variable_Label"] = construct
        return row

    def tpb_example_items(construct: str) -> list[str]:
        action = target_action.strip() or "[target behavior]"
        context_phrase = f" in {context_description.strip()}" if context_description.strip() else ""
        timeframe_phrase = f" {timeframe.strip()}" if timeframe.strip() else ""
        behavior_phrase = f"{action}{context_phrase}{timeframe_phrase}"
        behavior_period = timeframe.strip() or "[timeframe]"
        if behavior_period.casefold().startswith(
            ("during ", "within ", "over ", "in ", "for ")
        ):
            behavior_period = behavior_period.split(" ", 1)[1]
        examples = {
            "Attitude Toward the Behavior": [
                f"It would be good for me to {behavior_phrase}.",
                f"It would be beneficial for me to {behavior_phrase}.",
                f"For me, {behavior_phrase} would be worthwhile.",
            ],
            "Subjective Norms": [
                f"People important to me think I should {behavior_phrase}.",
                f"People whose opinions I value would approve of my decision to {behavior_phrase}.",
                f"People like me are expected to {behavior_phrase}.",
            ],
            "Perceived Behavioral Control": [
                f"I am confident that I can {behavior_phrase}.",
                f"Whether I {behavior_phrase} is mostly under my control.",
                f"I have the resources and opportunities needed to {behavior_phrase}.",
            ],
            "Behavioral Intention": [
                f"I intend to {behavior_phrase}.",
                f"I plan to {behavior_phrase}.",
                f"I expect that I will {behavior_phrase}.",
            ],
            "Behavior": [
                f"During {behavior_period}, how often did you {action}{context_phrase}?",
                f"When an opportunity arose during {behavior_period}, how often did you {action}{context_phrase}?",
                f"How consistently did you {behavior_phrase}?",
            ],
        }
        return examples.get(construct, ["", "", ""])

    tpb_agreement_scale = (
        "1=Strongly disagree|2=Disagree|3=Neither agree nor disagree|"
        "4=Agree|5=Strongly agree"
    )
    tpb_behavior_scale = (
        "0=Never|1=Rarely|2=Sometimes|3=Often|4=Always"
    )
    tpb_source_citation = (
        "Ajzen, I. (1991). The theory of planned behavior. "
        "Organizational Behavior and Human Decision Processes, 50(2), 179–211."
    )

    active_items = []
    all_demographic_variables = [
        value for value in selected_demographic_variables
        if value != "Other demographic or contextual variable"
    ]
    all_demographic_variables.extend(
        value.strip()
        for value in other_demographic_variables.split(",")
        if value.strip()
    )
    catalog_suggestions_by_variable = {}
    for framework, constructs in selected_constructs_by_theory.items():
        for construct in constructs:
            suggestions = find_measure_suggestions(
                measure_catalog,
                construct,
                [framework],
                selected_study_areas,
            )
            if suggestions:
                catalog_suggestions_by_variable[(framework, construct)] = suggestions
    for demographic in all_demographic_variables:
        suggestions = find_measure_suggestions(
            measure_catalog,
            demographic,
            [],
            selected_study_areas,
        )
        if suggestions:
            catalog_suggestions_by_variable[("Core demographic / contextual", demographic)] = suggestions

    def measurement_recommendation(variable: str, framework: str) -> str:
        suggestion_count = len(
            catalog_suggestions_by_variable.get((framework, variable), [])
        )
        if suggestion_count:
            return (
                f"{suggestion_count} possible measure(s) are listed in the catalog. "
                "Review the cited sources above."
            )
        return "Placeholder — variable-specific measurement recommendations will be added here."

    with st.expander("Measure catalog suggestions", expanded=bool(catalog_suggestions_by_variable)):
        st.caption(
            f"Catalog source: `{MEASURE_CATALOG_PATH.relative_to(Path(__file__).resolve().parent)}`. "
            "Suggestions are matched to included variables, selected frameworks, and saved Module 1 "
            "subject areas when available. Review every source and permissions before adopting a measure."
        )
        if catalog_suggestions_by_variable:
            for (framework, variable), suggestions in catalog_suggestions_by_variable.items():
                st.markdown(f"**{variable}** — {framework}")
                st.dataframe(
                    pd.DataFrame([
                        {
                            "Measure": measure["measure_name"],
                            "Population / context": measure["population_context"],
                            "Response format": measure["response_format"],
                            "Scoring": measure["scoring"],
                            "Validity evidence": measure["validity_evidence"],
                            "Reliability evidence": measure["reliability_evidence"],
                            "Citation": measure["citation"],
                            "DOI / URL": measure["doi_url"] or measure["source_url"],
                            "License / terms": measure["license"],
                        }
                        for measure in suggestions
                    ]),
                    use_container_width=True,
                    hide_index=True,
                )
        elif measure_catalog:
            st.info(
                "The catalog has entries, but none match the currently included variables, "
                "selected frameworks, and study areas."
            )
        else:
            st.info(
                "No measures have been entered yet. Add verified records to "
                "`catalogs/measure_catalog.json`; follow the field guide in `catalogs/README.md`."
            )
    for framework in selected_theories:
        if framework not in THEORY_MAP:
            active_items.append({
                "Data_Type": "",
                "Framework_Source": framework,
                "Framework_ID": stable_identifier(framework),
                "Theory_Citation": other_framework_sources,
                "Concept_Construct": "Add framework factor / variable",
                "Construct_ID": "add_framework_factor_variable",
                "Variable_ID": "",
                "Variable_Label": "",
                "Construct_Domain": "Unassigned",
                "Content_Domain": "",
                "Content_Tags": "",
                "Behavioral_Target": "",
                "Target_Action": "",
                "Context": "",
                "Timeframe": "",
                "Operational_Definition": "",
                "Expected_Role": "",
                "Question_Item_or_Indicator": "",
                "Item_Text": "",
                "Item_Text_2": "",
                "Item_Text_3": "",
                "Response_Scale_or_Representation": "",
                "Response_Scale": "",
                "Language": "",
                "Scoring": "",
                "Measurement_Recommendation": (
                    "Placeholder — add the framework's factors and develop measurement recommendations."
                ),
                "Instrument_Name": "",
                "Instrument_Citation": "",
                "Source_Citation": "",
                "Source_URL": "",
                "Item_Source_Type": "",
                "Adaptation_Notes": "",
                "Validation_Status": "Not validated by this app; researcher review required",
                "Validity_Evidence": "",
                "Reliability_Evidence": "",
            })
    for framework, constructs in selected_constructs_by_theory.items():
        for construct in constructs:
            variable_id = "VAR_" + "_".join(
                part for part in "".join(
                    char if char.isalnum() else " " for char in construct
                ).upper().split()
            )
            active_items.append({
                "Data_Type": "",
                "Framework_Source": framework,
                "Framework_ID": stable_identifier(framework),
                "Theory_Citation": citation_for_framework(framework),
                "Concept_Construct": construct,
                "Construct_ID": stable_identifier(construct),
                "Variable_ID": variable_id,
                "Variable_Label": construct,
                "Construct_Domain": "Unassigned",
                "Content_Domain": content_domain,
                "Content_Tags": content_tags,
                "Behavioral_Target": target_action,
                "Target_Action": target_action,
                "Context": context_description,
                "Timeframe": timeframe,
                "Operational_Definition": "",
                "Expected_Role": "",
                "Question_Item_or_Indicator": "",
                "Item_Text": "",
                "Item_Text_2": "",
                "Item_Text_3": "",
                "Response_Scale_or_Representation": "",
                "Response_Scale": "",
                "Language": "",
                "Scoring": "",
                "Measurement_Recommendation": measurement_recommendation(
                    construct, framework
                ),
                "Instrument_Name": "",
                "Instrument_Citation": "",
                "Source_Citation": "",
                "Source_URL": "",
                "Item_Source_Type": "",
                "Adaptation_Notes": "",
                "Validation_Status": "Not validated by this app; researcher review required",
                "Validity_Evidence": "",
                "Reliability_Evidence": "",
            })
            old_plan_row = next(
                (
                    row for row in saved_module2_plan.get("variables", [])
                    if isinstance(row, dict)
                    and row.get("Framework_Source") == framework
                    and row.get("Concept_Construct") == construct
                ),
                {},
            )
            active_items[-1].update(
                {field: old_plan_row[field] for field in variable_fields if field in old_plan_row}
            )
            active_items[-1]["Content_Domain"] = (
                active_items[-1].get("Content_Domain") or content_domain
            )
            active_items[-1]["Content_Tags"] = (
                active_items[-1].get("Content_Tags") or content_tags
            )
            active_items[-1]["Behavioral_Target"] = (
                active_items[-1].get("Behavioral_Target") or target_action
            )
            active_items[-1]["Target_Action"] = (
                active_items[-1].get("Target_Action") or target_action
            )
            active_items[-1]["Context"] = (
                active_items[-1].get("Context") or context_description
            )
            active_items[-1]["Timeframe"] = (
                active_items[-1].get("Timeframe") or timeframe
            )
            if framework == "Theory of Planned Behavior (TPB)":
                example_items = tpb_example_items(construct)
                for item_field, example_item in zip(
                    ("Item_Text", "Item_Text_2", "Item_Text_3"),
                    example_items,
                ):
                    if not active_items[-1].get(item_field):
                        active_items[-1][item_field] = example_item
                active_items[-1]["Question_Item_or_Indicator"] = (
                    active_items[-1].get("Item_Text") or example_items[0]
                )
                active_items[-1]["Response_Scale"] = (
                    active_items[-1].get("Response_Scale")
                    or (
                        tpb_behavior_scale
                        if construct == "Behavior"
                        else tpb_agreement_scale
                    )
                )
                active_items[-1]["Response_Scale_or_Representation"] = (
                    active_items[-1]["Response_Scale"]
                )
                active_items[-1]["Language"] = (
                    active_items[-1].get("Language") or "English"
                )
                active_items[-1]["Scoring"] = (
                    active_items[-1].get("Scoring")
                    or (
                        "Report the frequency response for each behavior indicator; "
                        "do not assume the indicators form a validated scale."
                        if construct == "Behavior"
                        else (
                            "Example only: review item content and dimensionality; "
                            "calculate a mean only if justified by study-specific evidence."
                        )
                    )
                )
                active_items[-1]["Instrument_Name"] = (
                    active_items[-1].get("Instrument_Name")
                    or "Generic TPB questionnaire example (not validated)"
                )
                active_items[-1]["Source_Citation"] = (
                    active_items[-1].get("Source_Citation") or tpb_source_citation
                )
                active_items[-1]["Source_URL"] = (
                    active_items[-1].get("Source_URL")
                    or "https://doi.org/10.1016/0749-5978(91)90020-T"
                )
                active_items[-1]["Item_Source_Type"] = (
                    active_items[-1].get("Item_Source_Type")
                    or "App-generated generic example; unvalidated"
                )
                active_items[-1]["Adaptation_Notes"] = (
                    active_items[-1].get("Adaptation_Notes")
                    or "Illustrative wording only. Personalize to the defined behavior and context; "
                    "review comprehension, validity, reliability, and permissions before use."
                )
    for demographic in all_demographic_variables:
        active_items.append({
            "Data_Type": "",
            "Framework_Source": "Core demographic / contextual",
            "Framework_ID": "core_demographic_contextual",
            "Theory_Citation": "",
            "Concept_Construct": "Demographic / contextual",
            "Construct_ID": "core_demographic_contextual",
            "Variable_ID": f"DEM_{demographic.upper().replace(' ', '_').replace('/', '_')}",
            "Variable_Label": demographic,
            "Construct_Domain": "Demographic / contextual",
            "Content_Domain": "",
            "Content_Tags": "",
            "Behavioral_Target": "",
            "Target_Action": "",
            "Context": "",
            "Timeframe": "",
            "Operational_Definition": "",
            "Expected_Role": "Context / covariate",
            "Question_Item_or_Indicator": "",
            "Item_Text": "",
            "Response_Scale_or_Representation": "",
            "Response_Scale": "",
            "Language": "",
            "Scoring": "",
            "Measurement_Recommendation": measurement_recommendation(
                demographic, "Core demographic / contextual"
            ),
            "Instrument_Name": "",
            "Instrument_Citation": "",
            "Source_Citation": "",
            "Source_URL": "",
            "Item_Source_Type": "",
            "Adaptation_Notes": "",
            "Validation_Status": "Not validated by this app; researcher review required",
            "Validity_Evidence": "",
            "Reliability_Evidence": "",
        })

    conceptual_relationship_fields = [
        "From_Variable_or_Construct",
        "Relationship_or_Path",
        "To_Variable_or_Construct",
        "Expected_Direction_or_Form",
        "Applicable_Data_Type",
        "Theory_Source",
        "Theory_Citation_or_Evidence",
        "Rationale_or_Hypothesis",
    ]
    if active_items:
        st.markdown("**Included theory-derived, demographic, and contextual variables**")
        active_items = [prepare_variable_metadata(item) for item in active_items]
        active_edit_fields = [
            "Framework_Source",
            "Concept_Construct",
            "Variable_ID",
            "Variable_Label",
            "Content_Domain",
            "Content_Tags",
            "Behavioral_Target",
            "Target_Action",
            "Context",
            "Timeframe",
            "Operational_Definition",
            "Item_Text",
            "Item_Text_2",
            "Item_Text_3",
            "Response_Scale",
            "Language",
            "Scoring",
            "Instrument_Name",
            "Source_Citation",
            "Source_URL",
            "Item_Source_Type",
            "Adaptation_Notes",
            "Validation_Status",
            "Validity_Evidence",
            "Reliability_Evidence",
        ]
        active_edit_df = st.data_editor(
            pd.DataFrame(active_items, columns=variable_fields)[active_edit_fields],
            key=f"module2_construct_metadata_{workflow_key}",
            use_container_width=True,
            hide_index=True,
            disabled=[
                "Framework_Source",
                "Concept_Construct",
                "Variable_ID",
                "Variable_Label",
                "Validation_Status",
            ],
            column_config={
                "Content_Domain": st.column_config.TextColumn(
                    help="Study content domain, such as climate science; it does not change construct identity."
                ),
                "Item_Text": st.column_config.TextColumn(
                    "Item 1",
                    help="Researcher-selected or researcher-written item/indicator. The app does not validate it."
                ),
                "Item_Text_2": st.column_config.TextColumn("Item 2"),
                "Item_Text_3": st.column_config.TextColumn("Item 3"),
                "Source_Citation": st.column_config.TextColumn(
                    help="Citation or persistent identifier for the source measure/item."
                ),
            },
        )
        active_items = [
            prepare_variable_metadata(
                {**item, **active_edit_df.iloc[index].to_dict()}
            )
            for index, item in enumerate(active_items)
        ]
        st.caption(
            "Items and adaptations are researcher-reported; this app does not establish that "
            "they are validated, reliable, suitable, or permitted for reuse."
        )

    st.subheader("Step 3 — Add or Import Custom Variables")
    st.warning(
        "Use one row per variable. Record construct/framework identity separately from content "
        "domain, and document item source, language, scale, scoring, and adaptations where known. "
        "The sample row is removed automatically. User-written or adapted items are not validated by this app."
    )
    
    custom_template_df = pd.DataFrame(columns=variable_fields)
    custom_template_df.loc[0] = {
        "Data_Type": "Survey responses",
        "Framework_Source": "Framework name",
        "Framework_ID": "stable-framework-id",
        "Theory_Citation": "Author, year, DOI/URL",
        "Concept_Construct": "Sample construct",
        "Construct_ID": "sample-construct",
        "Variable_ID": "VAR_SAMPLE_ID",
        "Variable_Label": "Sample variable label",
        "Construct_Domain": "Cognitive (knowledge, beliefs, thinking)",
        "Content_Domain": "Climate science",
        "Content_Tags": "climate; science",
        "Behavioral_Target": "Climate-friendly behavior",
        "Target_Action": "Choose a lower-carbon travel option",
        "Context": "At school",
        "Timeframe": "Next month",
        "Operational_Definition": "Define how the construct is represented in the study.",
        "Expected_Role": "Predictor / outcome / mediator / moderator / context / covariate",
        "Question_Item_or_Indicator": "Example item or observable indicator",
        "Item_Text": "Example item or observable indicator",
        "Item_Text_2": "",
        "Item_Text_3": "",
        "Response_Scale_or_Representation": "1=Option A | 2=Option B | 3=Option C",
        "Response_Scale": "1=Option A | 2=Option B | 3=Option C",
        "Language": "English",
        "Scoring": "Describe scoring and any reverse coding",
        "Measurement_Recommendation": "Researcher review required",
        "Instrument_Name": "Instrument or measure name",
        "Instrument_Citation": "Author, year, source, DOI/URL",
        "Source_Citation": "Author, year, source, DOI/URL",
        "Source_URL": "https://example.org/source",
        "Item_Source_Type": "Existing / adapted / researcher-written",
        "Adaptation_Notes": "Describe changes from the source item",
        "Validation_Status": "Not validated by this app; researcher review required",
        "Validity_Evidence": "Validity type, population, estimate, source",
        "Reliability_Evidence": "Reliability statistic, population, estimate, source",
    }
    template_csv_bytes = custom_template_df.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="Download Custom Variable Template (CSV)",
        data=template_csv_bytes,
        file_name="custom_variables_schema_template.csv",
        mime="text/csv"
    )
    
    uploaded_custom_vars = st.file_uploader("Upload completed Custom Variables (CSV)", type=["csv"])
    
    uploaded_items = []
    uploaded_frameworks = []
    raw_csv_text = ""
    custom_vars_csv_valid = False
    saved_custom_variables = saved_module2_plan.get("custom_variables", [])
    if isinstance(saved_custom_variables, list):
        uploaded_items = [
            row for row in saved_custom_variables if isinstance(row, dict)
        ]
        uploaded_frameworks = list(dict.fromkeys(
            str(row.get("Framework_Source", "")).strip()
            for row in uploaded_items
            if str(row.get("Framework_Source", "")).strip()
        ))
    if uploaded_custom_vars is not None:
        try:
            raw_csv_text = uploaded_custom_vars.getvalue().decode("utf-8-sig", errors="replace")
            uploaded_df = pd.read_csv(io.StringIO(raw_csv_text))
            required_fields = [
                "Variable_ID", "Concept_Construct", "Variable_Label",
                "Framework_Source",
            ]
            
            if all(field in uploaded_df.columns for field in required_fields):
                custom_vars_csv_valid = True
                initial_count = len(uploaded_df)
                uploaded_df = uploaded_df[uploaded_df["Variable_ID"] != "VAR_SAMPLE_ID"]
                filtered_count = len(uploaded_df)
                if "Question_Item_Text" in uploaded_df.columns and "Question_Item_or_Indicator" not in uploaded_df.columns:
                    uploaded_df["Question_Item_or_Indicator"] = uploaded_df["Question_Item_Text"]
                if "Response_Scale_Options" in uploaded_df.columns and "Response_Scale_or_Representation" not in uploaded_df.columns:
                    uploaded_df["Response_Scale_or_Representation"] = uploaded_df["Response_Scale_Options"]
                if "Item_Text" not in uploaded_df.columns and "Question_Item_or_Indicator" in uploaded_df.columns:
                    uploaded_df["Item_Text"] = uploaded_df["Question_Item_or_Indicator"]
                if "Response_Scale" not in uploaded_df.columns and "Response_Scale_or_Representation" in uploaded_df.columns:
                    uploaded_df["Response_Scale"] = uploaded_df["Response_Scale_or_Representation"]
                if "Source_Citation" not in uploaded_df.columns and "Instrument_Citation" in uploaded_df.columns:
                    uploaded_df["Source_Citation"] = uploaded_df["Instrument_Citation"]
                for field in variable_fields:
                    if field not in uploaded_df.columns:
                        uploaded_df[field] = "Unassigned" if field == "Construct_Domain" else ""
                uploaded_df = uploaded_df[variable_fields].fillna("")
                uploaded_items = [
                    prepare_variable_metadata(row)
                    for row in uploaded_df.to_dict(orient="records")
                ]
                uploaded_df = pd.DataFrame(uploaded_items).reindex(columns=variable_fields)
                uploaded_frameworks = list(dict.fromkeys(
                    str(value).strip()
                    for value in uploaded_df["Framework_Source"].dropna()
                    if str(value).strip()
                ))
                
                if filtered_count < initial_count:
                    st.success(f"Imported {filtered_count} custom variable definitions. The sample row was removed.")
                else:
                    st.success(f"Imported {filtered_count} custom variable definitions.")
                
                st.dataframe(uploaded_df, use_container_width=True, hide_index=True)
            else:
                st.error("Required columns are missing. Use the downloaded custom variable template as a guide.")
        except Exception as e:
            st.error(f"Error parsing custom variable spreadsheet file: {e}")

    final_instrument_list = active_items + uploaded_items + st.session_state.session_instruments

    final_instrument_list = [
        prepare_variable_metadata(row) for row in final_instrument_list
    ]
    df_manifest = pd.DataFrame(final_instrument_list).reindex(columns=variable_fields)
    st.session_state["module2_variable_manifest"] = df_manifest.to_dict(orient="records")
    st.subheader("Step 4 — Build the Conceptual Framework")
    st.warning(
        "Building, editing, and saving a conceptual framework requires you to be signed in. "
        "You can view the diagram in preview mode, but editing and downloads are disabled."
    )
    st.caption(
        "The diagram includes every included theory-derived variable, demographic/context variable, "
        "and custom variable. Its IEO-inspired layout places demographic/context inputs on the left, "
        "intermediate variables in the center, and outcomes on the far right. Drag boxes to move "
        "them; click an arrow to select it and use the controls to edit, reverse, or delete it."
    )
    if final_instrument_list:
        theory_path_templates = {
            "Theory of Planned Behavior (TPB)": [
                ("Attitude Toward the Behavior", "Behavioral Intention", "Supports intention"),
                ("Subjective Norms", "Behavioral Intention", "Supports intention"),
                ("Perceived Behavioral Control", "Behavioral Intention", "Supports intention"),
                ("Behavioral Intention", "Behavior", "Predicts behavior"),
                ("Perceived Behavioral Control", "Behavior", "May directly predict behavior"),
            ],
            "Self-Determination Theory (SDT)": [
                ("Autonomy", "Intrinsic Motivation", "Supports motivation"),
                ("Competence", "Intrinsic Motivation", "Supports motivation"),
                ("Relatedness", "Intrinsic Motivation", "Supports motivation"),
            ],
            "Technology Acceptance Model (TAM)": [
                ("Perceived Ease of Use (PEOU)", "Perceived Usefulness (PU)", "Influences usefulness"),
                ("Perceived Ease of Use (PEOU)", "Behavioral Intention to Use", "Influences intention"),
                ("Perceived Usefulness (PU)", "Behavioral Intention to Use", "Influences intention"),
                ("Behavioral Intention to Use", "Actual System Use", "Predicts system use"),
            ],
            "Health Belief Model (HBM)": [
                ("Perceived Susceptibility", "Perceived Threat", "Contributes to perceived threat"),
                ("Perceived Severity", "Perceived Threat", "Contributes to perceived threat"),
                ("Perceived Threat", "Preventive Behavior", "May motivate action"),
                ("Perceived Benefits", "Preventive Behavior", "May support action"),
                ("Perceived Barriers", "Preventive Behavior", "May inhibit action"),
                ("Cues to Action", "Preventive Behavior", "May prompt action"),
                ("Self-Efficacy", "Preventive Behavior", "May support action"),
            ],
            "Self-Efficacy Theory": [
                ("Mastery Experiences", "Self-Efficacy", "May strengthen self-efficacy"),
                ("Vicarious Experiences", "Self-Efficacy", "May shape self-efficacy"),
                ("Verbal Persuasion", "Self-Efficacy", "May shape self-efficacy"),
                ("Emotional / Physiological Arousal", "Self-Efficacy", "May shape self-efficacy"),
            ],
            "Control Theory": [
                ("Goal / Reference State", "Comparator / Discrepancy", "Defines comparison standard"),
                ("Input / Perceived Current State", "Comparator / Discrepancy", "Provides current-state input"),
                ("Comparator / Discrepancy", "Output / Behavior Adjustment", "Guides adjustment"),
                ("Output / Behavior Adjustment", "Environmental Impact", "Changes current conditions"),
                ("Environmental Impact", "Input / Perceived Current State", "Provides feedback"),
                ("Disturbances / Obstacles", "Input / Perceived Current State", "Affects current state"),
            ],
            "Social Cognitive Theory (SCT)": [
                ("Personal Factors", "Behavioral Factors", "Reciprocal influence"),
                ("Environmental Factors", "Behavioral Factors", "Reciprocal influence"),
                ("Behavioral Factors", "Personal Factors", "Reciprocal influence"),
                ("Observational Learning", "Behavioral Factors", "Informs behavior"),
                ("Outcome Expectations", "Behavioral Factors", "Informs behavior"),
                ("Self-Efficacy", "Behavioral Factors", "Informs behavior"),
            ],
            "COM-B Model": [
                ("Psychological Capability", "Behavior", "Contributes to behavior"),
                ("Physical Capability", "Behavior", "Contributes to behavior"),
                ("Physical Opportunity", "Behavior", "Contributes to behavior"),
                ("Social Opportunity", "Behavior", "Contributes to behavior"),
                ("Reflective Motivation", "Behavior", "Contributes to behavior"),
                ("Automatic Motivation", "Behavior", "Contributes to behavior"),
            ],
        }
        model_records = df_manifest.fillna("").astype(str).to_dict(orient="records")
        model_nodes_by_id = {}
        model_node_ids_by_construct = {}
        node_occurrence_counts = {}

        def flow_id_segment(value: str) -> str:
            return "".join(char.lower() if char.isalnum() else "_" for char in value).strip("_")

        for index, row in enumerate(model_records):
            variable_label = (row.get("Variable_Label") or row.get("Concept_Construct") or "").strip()
            if not variable_label:
                continue
            data_type = row.get("Data_Type", "").strip()
            framework = row.get("Framework_Source", "").strip()
            construct = row.get("Concept_Construct", "").strip()
            variable_id = row.get("Variable_ID", "").strip()
            identity = f"{data_type}|{framework}|{variable_id}|{variable_label}"
            occurrence = node_occurrence_counts.get(identity, 0)
            node_occurrence_counts[identity] = occurrence + 1
            node_id = f"variable_{uuid.uuid5(uuid.NAMESPACE_URL, identity + '|' + str(occurrence)).hex[:16]}"
            model_nodes_by_id[node_id] = {
                "label": variable_label,
                "data_type": data_type,
                "framework": framework,
                "construct": construct,
                "expected_role": row.get("Expected_Role", ""),
                "variable_id": variable_id,
                "position": (0, 0),
            }
            model_node_ids_by_construct.setdefault((data_type, framework, construct), []).append(node_id)

        suggested_edges = {}
        for framework in selected_theories:
            if framework not in THEORY_MAP:
                continue
            for source_construct, target_construct, relationship_label in theory_path_templates.get(framework, []):
                source_ids = model_node_ids_by_construct.get(("", framework, source_construct), [])
                target_ids = model_node_ids_by_construct.get(("", framework, target_construct), [])
                for source_id in source_ids:
                    for target_id in target_ids:
                        edge_id = (
                            f"theory_{flow_id_segment(framework)}_"
                            f"{source_id}_{target_id}"
                        )
                        suggested_edges[edge_id] = {
                            "source": source_id,
                            "target": target_id,
                            "framework": framework,
                            "label": relationship_label,
                            "direction": "Theory-informed suggested relationship; verify direction and study context",
                        }

        outcome_constructs = {
            "Behavior",
            "Actual System Use",
            "Preventive Behavior",
            "Intrinsic Motivation",
            "Output / Behavior Adjustment",
        }
        outcomes = {
            node_id
            for node_id, details in model_nodes_by_id.items()
            if details["construct"] in outcome_constructs
            or "outcome" in details["expected_role"].lower()
        }
        incoming_sources = {}
        for details in suggested_edges.values():
            incoming_sources.setdefault(details["target"], []).append(details["source"])
        node_layers = {node_id: None for node_id in model_nodes_by_id}
        for node_id in outcomes:
            node_layers[node_id] = 0
        queue = list(outcomes)
        while queue:
            target_id = queue.pop(0)
            for source_id in incoming_sources.get(target_id, []):
                if node_layers[source_id] is None:
                    node_layers[source_id] = node_layers[target_id] + 1
                    queue.append(source_id)
        for index, (node_id, details) in enumerate(model_nodes_by_id.items()):
            role = details["expected_role"].lower()
            if details["construct"] == "Demographic / contextual" or any(
                term in role for term in ("input", "context", "covariate")
            ):
                x_position = 0
            elif node_id in outcomes:
                x_position = 1050
            else:
                distance_from_outcome = node_layers[node_id]
                x_position = (
                    max(250, 1050 - distance_from_outcome * 300)
                    if distance_from_outcome is not None else 550
                )
            details["position"] = (x_position, index * 120)

        flow_identity = selected_study.get("id") if selected_study else ("preview" if preview_mode else "draft")
        flow_state_key = f"module2_conceptual_flow_v2_{flow_identity}"
        seeded_edges_key = f"{flow_state_key}_seeded"
        edge_sources_key = f"{flow_state_key}_edge_sources"
        edge_directions_key = f"{flow_state_key}_edge_directions"
        edge_rationales_key = f"{flow_state_key}_edge_rationales"
        saved_diagram = saved_module2_plan.get("diagram", {})
        if not isinstance(saved_diagram, dict):
            saved_diagram = {}
        saved_positions = {
            node.get("id"): node.get("position")
            for node in saved_diagram.get("nodes", [])
            if isinstance(node, dict)
            and isinstance(node.get("id"), str)
            and isinstance(node.get("position"), (list, tuple))
            and len(node["position"]) == 2
        }
        node_objects = [
            StreamlitFlowNode(
                id=node_id,
                pos=tuple(saved_positions.get(node_id, details["position"])),
                data={
                    "content": (
                        f"**{details['label']}**  \n"
                        f"{details['construct']}"
                        + (f"  \n*{details['data_type']}*" if details["data_type"] else "")
                    ),
                },
                node_type="default",
                source_position="right",
                target_position="left",
                draggable=not preview_mode,
                connectable=not preview_mode,
                style={"width": 230, "padding": 10, "borderRadius": 8},
            )
            for node_id, details in model_nodes_by_id.items()
        ]
        seeded_ids = st.session_state.setdefault(seeded_edges_key, set())
        edge_sources = st.session_state.setdefault(edge_sources_key, {})
        edge_directions = st.session_state.setdefault(edge_directions_key, {})
        edge_rationales = st.session_state.setdefault(edge_rationales_key, {})
        if flow_state_key not in st.session_state:
            saved_edges = saved_diagram.get("edges", [])
            flow_edges = []
            if isinstance(saved_edges, list) and saved_edges:
                for edge in saved_edges:
                    if (
                        not isinstance(edge, dict)
                        or edge.get("source") not in model_nodes_by_id
                        or edge.get("target") not in model_nodes_by_id
                    ):
                        continue
                    edge_id = str(edge.get("id") or f"researcher_{uuid.uuid4().hex[:12]}")
                    flow_edges.append(StreamlitFlowEdge(
                        id=edge_id,
                        source=edge["source"],
                        target=edge["target"],
                        marker_end={"type": "arrowclosed", "width": 24, "height": 24},
                        label=str(edge.get("relationship") or "Researcher-proposed path"),
                        label_show_bg=True,
                        deletable=True,
                        style={"strokeWidth": 4},
                    ))
                    edge_sources[edge_id] = str(edge.get("theory_source", "Researcher-proposed"))
                    edge_directions[edge_id] = str(edge.get("expected_direction", ""))
                    edge_rationales[edge_id] = str(edge.get("rationale_or_hypothesis", ""))
                    if edge_id in suggested_edges:
                        seeded_ids.add(edge_id)
            else:
                flow_edges = [
                    StreamlitFlowEdge(
                        id=edge_id,
                        source=details["source"],
                        target=details["target"],
                        marker_end={"type": "arrowclosed", "width": 24, "height": 24},
                        label=details["label"],
                        label_show_bg=True,
                        deletable=True,
                        style={"strokeWidth": 4},
                    )
                    for edge_id, details in suggested_edges.items()
                ]
                seeded_ids.update(suggested_edges)
                edge_sources.update({
                    edge_id: details["framework"]
                    for edge_id, details in suggested_edges.items()
                })
                edge_directions.update({
                    edge_id: details["direction"]
                    for edge_id, details in suggested_edges.items()
                })
            st.session_state[flow_state_key] = StreamlitFlowState(node_objects, flow_edges)
        else:
            flow_state = st.session_state[flow_state_key]
            existing_nodes = {node.id: node for node in flow_state.nodes}
            synchronized_nodes = []
            for node in node_objects:
                existing = existing_nodes.get(node.id)
                if existing:
                    existing.data = node.data
                    existing.draggable = node.draggable
                    existing.connectable = node.connectable
                    synchronized_nodes.append(existing)
                else:
                    synchronized_nodes.append(node)
            flow_state.nodes = synchronized_nodes
            current_node_ids = set(model_nodes_by_id)
            flow_state.edges = [
                edge for edge in flow_state.edges
                if edge.source in current_node_ids and edge.target in current_node_ids
            ]
            active_suggested_ids = set(suggested_edges)
            removed_suggestions = seeded_ids - active_suggested_ids
            flow_state.edges = [
                edge for edge in flow_state.edges
                if edge.id not in removed_suggestions
            ]
            seeded_ids.intersection_update(active_suggested_ids)
            for edge_id, details in suggested_edges.items():
                if edge_id not in seeded_ids and not any(
                    edge.id == edge_id for edge in flow_state.edges
                ):
                    flow_state.edges.append(StreamlitFlowEdge(
                        id=edge_id,
                        source=details["source"],
                        target=details["target"],
                        marker_end={"type": "arrowclosed", "width": 24, "height": 24},
                        label=details["label"],
                        label_show_bg=True,
                        deletable=True,
                        style={"strokeWidth": 4},
                    ))
                    seeded_ids.add(edge_id)
                    edge_sources[edge_id] = details["framework"]
                    edge_directions[edge_id] = details["direction"]

        st.session_state[flow_state_key] = streamlit_flow(
            f"module2_conceptual_diagram_{flow_identity}",
            st.session_state[flow_state_key],
            layout=ManualLayout(),
            height=560,
            fit_view=True,
            allow_new_edges=not preview_mode,
            enable_edge_menu=False,
            enable_node_menu=False,
            enable_pane_menu=False,
            get_edge_on_click=True,
            pan_on_drag=False,
            style={
                "backgroundColor": "#eef6ff",
                "backgroundImage": "radial-gradient(#9ab6d8 1px, transparent 1px)",
                "backgroundSize": "20px 20px",
                "border": "1px solid #93a4b8",
                "borderRadius": "8px",
            },
            hide_watermark=True,
        )
        current_flow_state = st.session_state[flow_state_key]
        current_edges = list(current_flow_state.edges)
        if current_edges and not preview_mode:
            edge_labels = {
                edge.id: (
                    f"{model_nodes_by_id.get(edge.source, {}).get('label', edge.source)} "
                    f"({model_nodes_by_id.get(edge.source, {}).get('data_type', '')}) → "
                    f"{model_nodes_by_id.get(edge.target, {}).get('label', edge.target)} "
                    f"({model_nodes_by_id.get(edge.target, {}).get('data_type', '')})"
                )
                for edge in current_edges
            }
            selected_edge_id = current_flow_state.selected_id
            if selected_edge_id not in edge_labels:
                selected_edge_id = current_edges[0].id
            edge_selector_key = f"module2_selected_edge_{flow_identity}"
            selection_timestamp_key = f"{flow_state_key}_selection_timestamp"
            if st.session_state.get(selection_timestamp_key) != current_flow_state.timestamp:
                if current_flow_state.selected_id in edge_labels:
                    st.session_state[edge_selector_key] = current_flow_state.selected_id
                st.session_state[selection_timestamp_key] = current_flow_state.timestamp
            chosen_edge_id = st.selectbox(
                "Select a path (click an arrow in the diagram or choose it here)",
                options=list(edge_labels),
                format_func=lambda edge_id: edge_labels[edge_id],
                index=list(edge_labels).index(selected_edge_id),
                key=edge_selector_key,
            )
            chosen_edge = next(edge for edge in current_edges if edge.id == chosen_edge_id)
            pending_reversal_key = f"{flow_state_key}_pending_reversal"
            if st.session_state.get(pending_reversal_key) == chosen_edge_id:
                st.session_state.pop(
                    f"module2_edge_label_{flow_identity}_{chosen_edge_id}", None
                )
                st.session_state.pop(
                    f"module2_edge_rationale_{flow_identity}_{chosen_edge_id}", None
                )
                st.session_state.pop(pending_reversal_key, None)
            relationship_label = st.text_input(
                "Relationship label",
                value=chosen_edge.label or "",
                placeholder="For example: predicts, supports, moderates",
                key=f"module2_edge_label_{flow_identity}_{chosen_edge_id}",
            )
            relationship_rationale = st.text_area(
                "Rationale or hypothesis",
                value=edge_rationales.get(chosen_edge_id, ""),
                placeholder="Explain why this path is expected and cite the relevant theory or evidence.",
                key=f"module2_edge_rationale_{flow_identity}_{chosen_edge_id}",
            )
            save_col, reverse_col, delete_col = st.columns(3)
            with save_col:
                save_relationship = st.button(
                    "Save path label and rationale",
                    key=f"module2_save_edge_{flow_identity}",
                )
            with reverse_col:
                reverse_relationship = st.button(
                    "Reverse selected arrow",
                    key=f"module2_reverse_edge_{flow_identity}",
                )
            with delete_col:
                delete_relationship = st.button(
                    "Delete selected path",
                    key=f"module2_delete_edge_{flow_identity}",
                )
            if save_relationship:
                chosen_edge.label = relationship_label.strip()
                edge_rationales[chosen_edge_id] = relationship_rationale.strip()
            if reverse_relationship:
                chosen_edge.source, chosen_edge.target = chosen_edge.target, chosen_edge.source
                chosen_edge.label = "Researcher-reversed; review relationship label"
                edge_rationales.pop(chosen_edge_id, None)
                edge_directions[chosen_edge_id] = "Direction reversed by researcher; verify and document rationale"
                st.session_state[pending_reversal_key] = chosen_edge_id
                st.rerun()
            if delete_relationship:
                current_flow_state.edges = [
                    edge for edge in current_flow_state.edges if edge.id != chosen_edge_id
                ]
                edge_sources.pop(chosen_edge_id, None)
                edge_directions.pop(chosen_edge_id, None)
                edge_rationales.pop(chosen_edge_id, None)
                st.rerun()
        if current_flow_state.nodes and not preview_mode:
            with st.expander("Add a path without dragging connection handles"):
                node_options = list(model_nodes_by_id)
                node_labels = {
                    node_id: (
                        f"{model_nodes_by_id[node_id]['label']} "
                        f"({model_nodes_by_id[node_id]['data_type']})"
                    )
                    for node_id in node_options
                }
                add_source = st.selectbox(
                    "From variable",
                    options=node_options,
                    format_func=lambda node_id: node_labels[node_id],
                    key=f"module2_add_edge_source_{flow_identity}",
                )
                add_target = st.selectbox(
                    "To variable",
                    options=node_options,
                    format_func=lambda node_id: node_labels[node_id],
                    index=1 if len(node_options) > 1 else 0,
                    key=f"module2_add_edge_target_{flow_identity}",
                )
                if st.button("Add relationship arrow", key=f"module2_add_edge_{flow_identity}"):
                    if add_source == add_target:
                        st.error("Choose two different variables for a relationship.")
                    else:
                        edge_id = f"researcher_{uuid.uuid4().hex[:12]}"
                        current_flow_state.edges.append(StreamlitFlowEdge(
                            id=edge_id,
                            source=add_source,
                            target=add_target,
                            marker_end={"type": "arrowclosed", "width": 24, "height": 24},
                            label="Researcher-proposed",
                            label_show_bg=True,
                            deletable=True,
                            style={"strokeWidth": 4},
                        ))
                        edge_sources[edge_id] = "Researcher-proposed"
                        edge_directions[edge_id] = "Researcher-proposed; specify expected direction and conditions"
                        st.rerun()

        relationship_rows = []
        for edge in current_edges:
            source_details = model_nodes_by_id.get(edge.source, {})
            target_details = model_nodes_by_id.get(edge.target, {})
            relationship_rows.append({
                "From_Variable_or_Construct": source_details.get("label", edge.source),
                "Relationship_or_Path": edge.label or "Researcher-proposed path",
                "To_Variable_or_Construct": target_details.get("label", edge.target),
                "Expected_Direction_or_Form": edge_directions.get(
                    edge.id,
                    "Researcher-proposed; specify expected direction and conditions",
                ),
                "Applicable_Data_Type": source_details.get("data_type", ""),
                "Theory_Source": edge_sources.get(edge.id, "Researcher-proposed"),
                "Theory_Citation_or_Evidence": (
                    other_framework_sources
                    if edge_sources.get(edge.id) == "Researcher-proposed"
                    else citation_for_framework(edge_sources.get(edge.id, ""))
                ),
                "Rationale_or_Hypothesis": edge_rationales.get(edge.id, ""),
            })
        conceptual_relationships = pd.DataFrame(
            relationship_rows,
            columns=conceptual_relationship_fields,
        )
        if not current_edges:
            st.info(
                "No paths are shown yet. Select theory constructs to load suggested paths, "
                "or connect variables in the diagram to propose your own relationships."
            )
        else:
            st.dataframe(conceptual_relationships, use_container_width=True, hide_index=True)
        conceptual_framework_description = st.text_area(
            "Conceptual framework narrative",
            value=str(saved_module2_plan.get("narrative", "")),
            placeholder=(
                "Explain how the selected theory constructs become this study's variables, "
                "why the proposed paths are expected, and how the data types will evidence those relationships."
            ),
            disabled=preview_mode,
            key=f"module2_conceptual_narrative_{flow_identity}",
        )
        st.subheader("Step 5 — Review Variables and Measurement Metadata")
        st.caption(
            "Review the complete variable set represented in the diagram, including theory-derived, "
            "demographic/contextual, and custom variables. Review construct identity, study context, "
            "item and scale metadata, and all sources before using the exported draft."
        )
        st.dataframe(df_manifest, use_container_width=True, hide_index=True)
        diagram_nodes = [
            {
                "id": node.id,
                "variable_label": model_nodes_by_id.get(node.id, {}).get("label", ""),
                "data_type": model_nodes_by_id.get(node.id, {}).get("data_type", ""),
                "theory_construct": model_nodes_by_id.get(node.id, {}).get("construct", ""),
                "position": node.position,
            }
            for node in current_flow_state.nodes
        ]
        diagram_edges = [
            {
                "id": edge.id,
                "source": edge.source,
                "target": edge.target,
                "relationship": edge.label or "Researcher-proposed path",
                "theory_source": edge_sources.get(edge.id, "Researcher-proposed"),
                "expected_direction": edge_directions.get(edge.id, ""),
                "rationale_or_hypothesis": edge_rationales.get(edge.id, ""),
            }
            for edge in current_edges
        ]
        st.markdown("**Save this plan with the selected Module 1 study**")
        if selected_study and not preview_mode:
            if st.button(
                "Save Module 2 plan",
                key=f"module2_save_plan_{flow_identity}",
            ):
                plan_to_save = {
                    "schema_version": 1,
                    "selected_theories": selected_theories,
                    "other_theory_sources": str(other_framework_sources or ""),
                    "selected_demographic_variables": selected_demographic_variables,
                    "other_demographic_variables": other_demographic_variables,
                    "study_context": {
                        "content_domain": content_domain.strip(),
                        "target_action": target_action.strip(),
                        "context": context_description.strip(),
                        "timeframe": timeframe.strip(),
                        "content_tags": content_tags.strip(),
                    },
                    "share_for_discovery": share_study_for_discovery,
                    "variables": df_manifest.fillna("").astype(str).to_dict(orient="records"),
                    "custom_variables": (
                        pd.DataFrame(uploaded_items)
                        .fillna("")
                        .astype(str)
                        .to_dict(orient="records")
                    ),
                    "diagram": {
                        "nodes": diagram_nodes,
                        "edges": diagram_edges,
                    },
                    "narrative": conceptual_framework_description.strip(),
                }
                try:
                    (
                        user_client.table("study_module2_plans")
                        .upsert({
                            "study_id": selected_study["id"],
                            "owner_id": current_user_id,
                            "plan_json": plan_to_save,
                            "updated_at": time.strftime(
                                "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
                            ),
                        }, on_conflict="study_id")
                        .execute()
                    )
                    st.success("Module 2 plan saved with this Module 1 study.")
                    was_shared = bool(saved_module2_plan.get("share_for_discovery", False))
                    if share_study_for_discovery or was_shared:
                        try:
                            if share_study_for_discovery:
                                public_variable_fields = [
                                    "Framework_Source",
                                    "Concept_Construct",
                                    "Variable_Label",
                                    "Content_Domain",
                                    "Content_Tags",
                                    "Behavioral_Target",
                                    "Target_Action",
                                    "Context",
                                    "Timeframe",
                                    "Response_Scale",
                                    "Language",
                                    "Scoring",
                                    "Source_Citation",
                                    "Source_URL",
                                    "Instrument_Name",
                                    "Validation_Status",
                                ]
                                shared_variables = []
                                for variable in df_manifest.fillna("").astype(str).to_dict(
                                    orient="records"
                                ):
                                    shared_variables.append({
                                        field: variable.get(field, "")
                                        for field in public_variable_fields
                                        if variable.get(field, "")
                                    })
                                context_summary = "; ".join(
                                    f"{label}: {value}"
                                    for label, value in (
                                        ("Domain", content_domain),
                                        ("Target behavior", target_action),
                                        ("Context", context_description),
                                        ("Timeframe", timeframe),
                                        ("Tags", content_tags),
                                    )
                                    if value.strip()
                                )
                                published_metadata = {
                                    "context_summary": context_summary,
                                    "time_method": study_metadata.get("time_method", ""),
                                    "unit_of_analysis": study_metadata.get("unit_of_analysis", ""),
                                    "participant_populations": study_metadata.get(
                                        "participant_populations", []
                                    ),
                                    "study_settings": study_metadata.get("study_settings", []),
                                    "content_domain": content_domain.strip(),
                                    "selected_theories": selected_theories,
                                    "variables": shared_variables,
                                }
                                search_tags = context_search_terms(
                                    " ".join(
                                        [
                                            context_summary,
                                            " ".join(selected_theories),
                                            " ".join(selected_study_areas),
                                            " ".join(
                                                published_metadata["participant_populations"]
                                                if isinstance(
                                                    published_metadata["participant_populations"],
                                                    list,
                                                )
                                                else []
                                            ),
                                            " ".join(
                                                published_metadata["study_settings"]
                                                if isinstance(
                                                    published_metadata["study_settings"],
                                                    list,
                                                )
                                                else []
                                            ),
                                        ]
                                    )
                                )
                                (
                                    user_client.table("study_discovery")
                                    .upsert(
                                        {
                                            "study_id": selected_study["id"],
                                            "owner_id": current_user_id,
                                            "study_title": selected_study.get("study_title")
                                            or "Shared study",
                                            "context_tags": search_tags,
                                            "study_metadata": published_metadata,
                                        },
                                        on_conflict="study_id",
                                    )
                                    .execute()
                                )
                                st.success("The limited study summary is now discoverable to signed-in researchers.")
                            else:
                                (
                                    user_client.table("study_discovery")
                                    .delete()
                                    .eq("study_id", selected_study["id"])
                                    .eq("owner_id", current_user_id)
                                    .execute()
                                )
                                st.success("The study summary was removed from context discovery.")
                        except Exception as discovery_save_error:
                            st.error(
                                "The Module 2 plan was saved, but its study-discovery sharing "
                                "setting could not be updated. Confirm that "
                                "supabase/setup_auth_storage.sql has been applied: "
                                f"{discovery_save_error}"
                            )
                except Exception as save_error:
                    st.error(
                        "Could not save the Module 2 plan. Confirm that "
                        "supabase/setup_auth_storage.sql has been applied and that "
                        f"you still own this study: {save_error}"
                    )
        elif not preview_mode:
            st.info("Select a saved Module 1 study to save this plan. Drafts remain available for download.")
        diagram_json = json.dumps({
            "schema_version": 1,
            "nodes": diagram_nodes,
            "edges": diagram_edges,
            "narrative": conceptual_framework_description.strip(),
        }, ensure_ascii=False, indent=2).encode("utf-8")
        conceptual_csv = conceptual_relationships.to_csv(index=False).encode("utf-8")
        # --- MODULE 2 THEORY AND VARIABLE PROPOSAL ---
        st.markdown("---")
        st.markdown("### Suggest a Theory or Variable for the App")
        st.caption(
            "Submit the reviewed theory/variable map and conceptual relationships as a pull request "
            "for maintainer review. Accepted suggestions can be added to the app's catalog."
        )
        st.warning(
            "This proposal will be submitted to the public GitHub repository. Do not include "
            "participant information, private study details, unpublished results, or other sensitive content."
        )
        proposal_frameworks = list(dict.fromkeys(
            str(value).strip()
            for value in df_manifest["Framework_Source"].fillna("")
            if str(value).strip()
            and str(value).strip() not in {"Core demographic / contextual", "Unassigned"}
        ))
        proposal_frameworks = list(dict.fromkeys(proposal_frameworks + uploaded_frameworks))
        default_framework_names = ", ".join(proposal_frameworks)
        proposal_title = st.text_input(
            "Suggestion title",
            value=f"Theory and variable suggestion: {default_framework_names}" if default_framework_names else "",
            max_chars=120,
            key=f"module2_proposal_title_{selected_study.get('id') if selected_study else ('preview' if preview_mode else 'draft')}",
        )
        proposal_rationale = st.text_area(
            "Literature basis and reason for the suggestion",
            placeholder="Summarize the theory's established constructs and explain why this suggestion would help researchers.",
            key=f"module2_proposal_rationale_{selected_study.get('id') if selected_study else ('preview' if preview_mode else 'draft')}",
        )
        public_proposal_consent = st.checkbox(
            "I confirm this proposal contains no confidential or identifying information and may be published in a public GitHub pull request.",
            key=f"module2_public_proposal_consent_{selected_study.get('id') if selected_study else ('preview' if preview_mode else 'draft')}",
            disabled=preview_mode,
        )
        if st.button(
            "Submit Theory and Variable Suggestion for Review",
            key="submit_mod2_pr_btn",
            disabled=preview_mode or not public_proposal_consent,
        ):
            if not proposal_title.strip() or not proposal_rationale.strip():
                st.error("Enter a suggestion title and a literature basis before submitting.")
            else:
                proposal = {
                    "schema_version": 1,
                    "proposal_type": "theory_and_variable_catalog_suggestion",
                    "framework_names": proposal_frameworks,
                    "literature_basis_and_rationale": proposal_rationale.strip(),
                    "variables": (
                        df_manifest.fillna("")
                        .astype(str)
                        .to_dict(orient="records")
                    ),
                    "conceptual_relationships": (
                        conceptual_relationships.fillna("")
                        .astype(str)
                        .to_dict(orient="records")
                    ),
                    "conceptual_framework_narrative": conceptual_framework_description.strip(),
                    "conceptual_diagram": {
                        "nodes": diagram_nodes,
                        "edges": diagram_edges,
                    },
                    "submitted_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
                proposal_content = json.dumps(proposal, ensure_ascii=False, indent=2)
                with st.spinner("Creating a GitHub branch and pull request for maintainer review..."):
                    result_message = automate_github_pull_request(
                        suggestion_type="Framework",
                        file_name=f"module2_theory_variable_{uuid.uuid4().hex[:12]}.json",
                        file_content=proposal_content,
                        title_summary=proposal_title.strip(),
                    )
                if "❌" in result_message:
                    st.error(result_message)
                else:
                    st.success(result_message)
            
        st.markdown("---")
        st.subheader("Download Module 2 Matrices")
        download_col1, download_col2, download_col3 = st.columns(3)
        with download_col1:
            st.download_button(
                "Download Conceptual Framework Diagram (JSON)",
                data=diagram_json,
                file_name="conceptual_framework_diagram.json",
                mime="application/json",
                disabled=preview_mode,
                use_container_width=True,
            )
        with download_col2:
            st.download_button(
                "Download Theory and Variable Matrix (CSV)",
                data=df_manifest.to_csv(index=False).encode("utf-8"),
                file_name="theory_variable_data_type_map.csv",
                mime="text/csv",
                disabled=preview_mode,
                use_container_width=True,
            )
        with download_col3:
            st.download_button(
                "Download Conceptual Relationships Matrix (CSV)",
                data=conceptual_csv,
                file_name="conceptual_framework_relationships.csv",
                mime="text/csv",
                disabled=preview_mode,
                use_container_width=True,
            )
        st.subheader("Download Variable Matrices and Draft")
        csv_buffer = io.StringIO()
        df_manifest.to_csv(csv_buffer, index=False)
        st.download_button(
            "Download Variable and Measure Metadata (CSV)",
            data=csv_buffer.getvalue(),
            file_name="educational_study_metadata_sheet.csv",
            mime="text/csv",
            disabled=preview_mode,
            use_container_width=True,
        )

        txt_manifest = "=== VARIABLE AND MEASURE METADATA MANIFEST ===\n"
        txt_manifest += f"Study DOI / Persistent Identifier: {repository_id or 'Not provided'}\n"
        txt_manifest += f"Unit of Analysis: {unit_of_analysis}\n"
        txt_manifest += f"Sampling Procedure: {sampling_method}\n"
        txt_manifest += f"Sampling Details: {sampling_procedure or 'Not provided'}\n"
        txt_manifest += "=" * 60 + "\n\n"
        for _, row in df_manifest.iterrows():
            txt_manifest += f"DDI Variable ID:  {row['Variable_ID']}\n"
            txt_manifest += f"Framework ID:     {row.get('Framework_ID', '')}\n"
            txt_manifest += f"Concept/Construct: {row['Concept_Construct']}\n"
            txt_manifest += f"Construct ID:     {row.get('Construct_ID', '')}\n"
            txt_manifest += f"Variable Label:    {row['Variable_Label']}\n"
            txt_manifest += f"Operational Definition: {row.get('Operational_Definition', '')}\n"
            txt_manifest += f"Content Domain:    {row.get('Content_Domain', '')}\n"
            txt_manifest += f"Content Tags:      {row.get('Content_Tags', '')}\n"
            txt_manifest += f"Behavioral Target: {row.get('Behavioral_Target', '')}\n"
            txt_manifest += f"Target Action:     {row.get('Target_Action', '')}\n"
            txt_manifest += f"Context:           {row.get('Context', '')}\n"
            txt_manifest += f"Timeframe:         {row.get('Timeframe', '')}\n"
            txt_manifest += f"Data Type:         {row.get('Data_Type', '')}\n"
            txt_manifest += f"Theory Citation:   {row.get('Theory_Citation', '')}\n"
            txt_manifest += f"Item / Indicator:  {row.get('Item_Text') or row.get('Question_Item_or_Indicator', '')}\n"
            txt_manifest += f"Item 2:            {row.get('Item_Text_2', '')}\n"
            txt_manifest += f"Item 3:            {row.get('Item_Text_3', '')}\n"
            txt_manifest += f"Response Scale:    {row.get('Response_Scale') or row.get('Response_Scale_or_Representation', '')}\n"
            txt_manifest += f"Language:          {row.get('Language', '')}\n"
            txt_manifest += f"Scoring:           {row.get('Scoring', '')}\n"
            txt_manifest += f"Framework Source:  {row['Framework_Source']}\n"
            txt_manifest += f"Instrument:        {row.get('Instrument_Name', '')}\n"
            txt_manifest += f"Source Citation:   {row.get('Source_Citation') or row.get('Instrument_Citation', '')}\n"
            txt_manifest += f"Source URL:        {row.get('Source_URL', '')}\n"
            txt_manifest += f"Item Source Type:  {row.get('Item_Source_Type', '')}\n"
            txt_manifest += f"Adaptation Notes:  {row.get('Adaptation_Notes', '')}\n"
            txt_manifest += f"Validation Status: {row.get('Validation_Status', '')}\n"
            txt_manifest += f"Validity Evidence: {row.get('Validity_Evidence', '')}\n"
            txt_manifest += f"Reliability Evidence: {row.get('Reliability_Evidence', '')}\n"
            txt_manifest += "-" * 60 + "\n\n"
        st.download_button(
            "Download Technical Variable Manifest (TXT)",
            data=txt_manifest,
            file_name="technical_study_metadata_manifest.txt",
            mime="text/plain",
            disabled=preview_mode,
            use_container_width=True,
        )

        clean_survey = "=== DRAFT SURVEY FORM ===\n"
        if repository_id:
            clean_survey += f"Study DOI / Persistent Identifier: {repository_id}\n"
        clean_survey += f"Unit of Analysis: {unit_of_analysis}\n"
        clean_survey += f"Sampling Procedure: {sampling_method}\n"
        clean_survey += (
            "Instructions: Please read each question carefully and select or enter "
            "the option that best describes your response.\n"
        )
        clean_survey += (
            "Measurement notice: Items and adaptations are researcher-reported and are not "
            "validated by this app. Review item suitability, permissions, language, and scoring "
            "before administration.\n"
        )
        clean_survey += "=" * 60 + "\n\n"
        question_number = 0
        for _, row in df_manifest.iterrows():
            item_texts = [
                str(row.get(field) or "").strip()
                for field in ("Item_Text", "Item_Text_2", "Item_Text_3")
                if str(row.get(field) or "").strip()
            ]
            if not item_texts:
                legacy_item = str(row.get("Question_Item_or_Indicator") or "").strip()
                if legacy_item:
                    item_texts = [legacy_item]
            for item_text in item_texts:
                question_number += 1
                clean_survey += f"Q{question_number}. {item_text}\n"
                if row.get("Variable_Label"):
                    clean_survey += f"   Variable: {row.get('Variable_Label')}\n"
                if row.get("Language"):
                    clean_survey += f"   Language: {row.get('Language')}\n"
                options = str(row.get("Response_Scale") or row.get("Response_Scale_or_Representation", ""))
                if "|" in options:
                    for option in options.split("|"):
                        clean_survey += f"   [ ] {option.strip()}\n"
                elif "Continuous" in options:
                    clean_survey += "   [_______________________________________]\n"
                else:
                    clean_survey += f"   Options: {options}\n"
                if row.get("Scoring"):
                    clean_survey += f"   Scoring (researcher-defined): {row.get('Scoring')}\n"
                clean_survey += "\n"
        st.download_button(
            "Download Draft Survey Form (TXT)",
            data=clean_survey,
            file_name="clean_participant_survey_form.txt",
            mime="text/plain",
            disabled=preview_mode,
            use_container_width=True,
        )
    else:
        st.subheader("Step 5 — Review Variables and Measurement Metadata")
        st.info("No variables were selected or added. Select theory variables in Step 2 or add variables in Step 3.")
        st.info("No structural frameworks, demographic indicators, or custom variables selected yet.")

# ==========================================
# MODULE 3: COMMUNITY STORAGE SYNCHRONIZATION
# ==========================================
elif app_mode == "3. Community Data Repository Sync":
    st.header("🌐 Supabase Dataset Library")
    st.caption("Upload and manage datasets owned by your signed-in account, with a deliberate private or public access choice.")
    st.markdown("---")
    
    st.subheader("🔒 Permission and privacy review")
    st.warning(
        "Review consent, IRB requirements, data-use agreements, ownership, and disclosure risk "
        "with the appropriate people. These confirmations are not approval or a guarantee that "
        "data are safe to share."
    )
    check_authority = st.checkbox(
        "I have permission from the data owner and applicable consent/approvals for this upload."
    )
    check_identifiers = st.checkbox(
        "I reviewed direct and indirect identifiers, sensitive fields, and small groups."
    )
    check_risk = st.checkbox(
        "I selected an access level consistent with permissions and disclosure-risk review."
    )
    access_level = st.radio(
        "Dataset access",
        ["Private — owner only", "Public — anyone with the link"],
        help="Public files can be downloaded by anyone who obtains their URL; public release may be difficult to reverse."
    )
    public_release_confirmed = False
    if access_level.startswith("Public"):
        public_release_confirmed = st.checkbox(
            "I explicitly authorize public release and verified that the data owner, consent, agreements, and privacy review permit it."
        )
    
    st.markdown("---")
    st.subheader("Upload a dataset")
    dataset_title = st.text_input("Dataset title", placeholder="e.g., First-year student engagement survey")
    uploaded_data_file = st.file_uploader(
        "Choose a research dataset (.csv)",
        type=["csv"],
        max_upload_size=50,
        help="CSV files up to 50 MB. Public and private datasets are stored in separate Supabase buckets."
    )
    
    if uploaded_data_file is not None:
        try:
            uploaded_bytes = uploaded_data_file.getvalue()
            df_user_raw = pd.read_csv(io.BytesIO(uploaded_bytes))
            if df_user_raw.empty:
                raise ValueError("The uploaded CSV has no data rows.")
            st.success("CSV parsed successfully. Review the preview before syncing.")
            st.dataframe(df_user_raw.head(10), use_container_width=True)
            
            st.caption(
                f"{len(df_user_raw):,} rows · {len(df_user_raw.columns):,} columns · "
                f"{len(uploaded_bytes) / (1024 * 1024):.2f} MB"
            )

            ready_to_upload = (
                bool(dataset_title.strip())
                and check_authority
                and check_identifiers
                and check_risk
                and (not access_level.startswith("Public") or public_release_confirmed)
            )
            if ready_to_upload:
                if st.button(
                    "☁️ Upload dataset to Supabase",
                    type="primary",
                    disabled=preview_mode,
                ):
                    bucket_id = PUBLIC_DATASET_BUCKET if access_level.startswith("Public") else DATASET_BUCKET
                    safe_filename = os.path.basename(uploaded_data_file.name).replace("\\", "_")
                    object_path = f"{current_user_id}/{uuid.uuid4().hex}/{safe_filename}"
                    uploaded_object = False
                    try:
                        with st.status("Uploading dataset and recording ownership...", expanded=False) as upload_status:
                            user_client.storage.from_(bucket_id).upload(
                                path=object_path,
                                file=uploaded_bytes,
                                file_options={"content-type": "text/csv", "upsert": "false"}
                            )
                            uploaded_object = True
                            dataset_record = {
                                "owner_id": current_user_id,
                                "dataset_title": dataset_title.strip(),
                                "file_name": safe_filename,
                                "object_path": object_path,
                                "bucket_id": bucket_id,
                                "access_level": "public" if bucket_id == PUBLIC_DATASET_BUCKET else "private",
                                "row_count": len(df_user_raw),
                                "column_count": len(df_user_raw.columns),
                                "byte_size": len(uploaded_bytes)
                            }
                            user_client.table("study_datasets").insert(dataset_record).execute()
                            upload_status.update(label="Dataset uploaded and recorded.", state="complete")
                        if bucket_id == PUBLIC_DATASET_BUCKET:
                            public_url = user_client.storage.from_(bucket_id).get_public_url(object_path)
                            st.success("Dataset published. Anyone with its URL can download it.")
                            st.code(public_url)
                        else:
                            st.success("Dataset stored privately under your account.")
                    except Exception as upload_error:
                        cleanup_message = ""
                        if uploaded_object:
                            try:
                                user_client.storage.from_(bucket_id).remove([object_path])
                            except Exception as cleanup_error:
                                cleanup_message = f" The uploaded object could not be removed during cleanup: {cleanup_error}"
                        st.error(
                            f"Supabase upload failed: {upload_error}. Confirm the setup SQL and "
                            f"authenticated-user policies are applied.{cleanup_message}"
                        )
            else:
                st.warning("Enter a title and complete all required permission/privacy confirmations before uploading.")
        except pd.errors.EmptyDataError:
            st.error("The uploaded CSV is empty or does not contain a readable header row.")
        except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as e:
            st.error(f"Could not parse the uploaded CSV: {e}")
        except Exception as e:
            st.error(f"Error reading uploaded dataset: {e}")

    st.divider()
    st.subheader("Your datasets")
    if preview_mode:
        st.info("Sign in to view your dataset library. Preview example:")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "dataset_title": "Example student engagement survey",
                        "file_name": "engagement_survey.csv",
                        "access_level": "private",
                        "row_count": 120,
                        "column_count": 8,
                        "byte_size": 15360,
                    }
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        try:
            own_datasets = (
                user_client.table("study_datasets")
                .select("id,dataset_title,file_name,bucket_id,access_level,row_count,column_count,byte_size,created_at")
                .eq("owner_id", current_user_id)
                .order("created_at", desc=True)
                .execute()
                .data
            )
            if own_datasets:
                st.dataframe(pd.DataFrame(own_datasets), use_container_width=True, hide_index=True)
            else:
                st.info("No datasets have been uploaded to your account yet.")
        except Exception as library_error:
            st.error(f"Could not load your dataset library: {library_error}")

# ==========================================
# MODULE 4: DESCRIPTIVE & SCALE ANALYTICS
# ==========================================
elif app_mode == "4. Descriptive & Scale Analytics":
    st.header("📊 Descriptive & Scale Analytics")
    st.caption(
        "Analyze dataset columns in the context of your Module 2 theory-derived, "
        "demographic/contextual, and custom variable matrix."
    )
    st.markdown("---")
    
    # Ingest Data Sheet Mapping Workspace
    st.subheader("📂 1. Ingest Data Sheet Mapping Workspace")
    if preview_mode:
        available_datasets = []
        st.info("Sign in to select saved datasets. The synthetic sample is available in preview.")
    else:
        try:
            available_datasets = (
                user_client.table("study_datasets")
            .select("id,dataset_title,file_name,object_path,bucket_id,access_level,row_count,column_count,created_at")
            .order("created_at", desc=True)
            .execute()
            .data
            )
        except Exception as dataset_error:
            available_datasets = []
            st.error(f"Could not load authorized datasets from Supabase: {dataset_error}")

    data_source_options = ["Use Standard Synthetic Sample Dataset"]
    if available_datasets:
        data_source_options.insert(0, "Use a dataset from Supabase")
    data_source_options.append("Upload Custom Research Data Sheet (.csv)")
    data_source = st.radio("Analytics Dataset Source Selection:", data_source_options)
    
    st.info(
        "There are no required column names or theory prefixes. Use the Module 2 matrix to "
        "map numeric columns for scores and categorical columns for response distributions. "
        "The dataset needs at least one numeric analysis variable."
    )
    manifest_upload = st.file_uploader(
        "Optional: upload the Module 2 Theory and Variable Matrix (CSV)",
        type=["csv"],
        key="analytics_module2_manifest_upload",
        help="Use the matrix downloaded at the end of Module 2. A matrix created in this same app session is loaded automatically.",
    )
    module2_manifest = st.session_state.get("module2_variable_manifest", [])
    if manifest_upload is not None:
        try:
            imported_manifest = pd.read_csv(manifest_upload)
            required_manifest_fields = {
                "Variable_ID", "Variable_Label", "Framework_Source", "Concept_Construct"
            }
            if required_manifest_fields.issubset(imported_manifest.columns):
                module2_manifest = imported_manifest.fillna("").to_dict(orient="records")
                st.success(f"Loaded {len(module2_manifest)} variables from the Module 2 matrix.")
            else:
                st.error(
                    "The uploaded file is not a Module 2 variable matrix. It must include "
                    "Variable_ID, Variable_Label, Framework_Source, and Concept_Construct."
                )
        except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as matrix_error:
            st.error(f"Could not read the Module 2 variable matrix: {matrix_error}")
    
    st.markdown("---")
    df_analytics = None
    
    if data_source == "Use a dataset from Supabase" and available_datasets:
        try:
            selected_dataset = st.selectbox(
                "Select a dataset",
                available_datasets,
                format_func=lambda item: (
                    f"{item['dataset_title']} — {item['file_name']} "
                    f"({item['access_level']}, {item['row_count']} rows)"
                ),
                key="analytics_dataset_id"
            )
            file_bytes = user_client.storage.from_(selected_dataset["bucket_id"]).download(
                selected_dataset["object_path"]
            )
            df_analytics = pd.read_csv(io.BytesIO(file_bytes))
            st.info(f"Analyzing `{selected_dataset['file_name']}` from Supabase. Stored data is not modified.")
        except (KeyError, TypeError, pd.errors.EmptyDataError, pd.errors.ParserError) as e:
            st.error(f"Could not load the selected Supabase dataset: {e}")
        except Exception as e:
            st.error(f"Supabase denied or failed the dataset download: {e}")
    elif data_source == "Use Standard Synthetic Sample Dataset":
        st.info("This is synthetic demonstration data, not observed research data.")
        np.random.seed(42)
        n_samples = 100
        synthetic_data = {
            "Participant_ID": range(1, n_samples + 1),
            "Example_Context_Group": np.random.choice(
                ["Group A", "Group B"], size=n_samples
            ),
            "Example_Input_Item_1": np.random.choice([1, 2, 3, 4, 5], size=n_samples),
            "Example_Input_Item_2": np.random.choice([1, 2, 3, 4, 5], size=n_samples),
            "Example_Experience_Item_1": np.random.choice([1, 2, 3, 4, 5], size=n_samples),
            "Example_Outcome_Item_1": np.random.choice([1, 2, 3, 4, 5], size=n_samples),
            "Example_Outcome_Item_2": np.random.choice([1, 2, 3, 4, 5], size=n_samples),
            "Example_Context_Score": np.random.randint(0, 10, size=n_samples),
        }
        df_analytics = pd.DataFrame(synthetic_data)
    else:
        uploaded_analytics_file = st.file_uploader("Upload target tracking matrix sheet (.csv)", type=["csv"])
        if uploaded_analytics_file is not None:
            df_analytics = pd.read_csv(uploaded_analytics_file)

    if df_analytics is not None:
        numeric_columns = df_analytics.select_dtypes(include=[np.number]).columns
        if not any("ID" not in column for column in numeric_columns):
            st.warning("This dataset has no numeric analysis variables (excluding ID fields).")
            df_analytics = None
            
    if df_analytics is not None:
        st.subheader("📋 Dataset Workspace Snapshot")
        st.dataframe(df_analytics.head(10), use_container_width=True, hide_index=True)
        
        all_numeric_cols = df_analytics.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [c for c in all_numeric_cols if "ID" not in c.upper()]
        analysis_columns = [
            column for column in df_analytics.columns
            if "ID" not in column.upper()
        ]

        st.divider()
        st.subheader("📐 2. Map dataset columns to Module 2 variables")
        computed_scales_manifest = {}
        mapped_categorical_variables = {}
        if module2_manifest:
            module2_variables = [
                row for row in module2_manifest
                if str(row.get("Variable_ID", "")).strip()
                and (
                    str(row.get("Variable_Label", "")).strip()
                    or str(row.get("Concept_Construct", "")).strip()
                )
            ]
            if module2_variables and analysis_columns:
                mapping_df = pd.DataFrame([
                    {
                        "Variable_ID": str(row.get("Variable_ID", "")),
                        "Variable": str(row.get("Variable_Label") or row.get("Concept_Construct") or ""),
                        "Framework / source": str(row.get("Framework_Source", "")),
                        "Dataset columns": [],
                    }
                    for row in module2_variables
                ])
                st.caption(
                    "Choose dataset column(s) that represent each Module 2 variable. Numeric columns "
                    "can be combined into scores; categorical columns are summarized as response counts. "
                    "Mappings are researcher-defined, not inferred from column names."
                )
                mapping_source = (
                    str(selected_dataset.get("id", ""))
                    if data_source == "Use a dataset from Supabase"
                    else data_source
                )
                mapping_identity = uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"{mapping_source}|{','.join(analysis_columns)}",
                ).hex[:12]
                mapping_df = st.data_editor(
                    mapping_df,
                    key=f"module4_variable_mapping_{mapping_identity}",
                    hide_index=True,
                    use_container_width=True,
                    disabled=["Variable_ID", "Variable", "Framework / source"],
                    column_config={
                        "Dataset columns": st.column_config.MultiselectColumn(
                            "Dataset columns",
                            options=analysis_columns,
                            help="Select numeric item columns for a composite, or a categorical column for response counts.",
                        ),
                    },
                )
                for _, mapping in mapping_df.iterrows():
                    mapping_columns = mapping["Dataset columns"]
                    if not isinstance(mapping_columns, list):
                        mapping_columns = []
                    selected_items = [
                        column for column in mapping_columns
                        if column in analysis_columns
                    ]
                    if not selected_items:
                        continue
                    numeric_items = [
                        column for column in selected_items if column in numeric_cols
                    ]
                    categorical_items = [
                        column for column in selected_items if column not in numeric_cols
                    ]
                    variable_id = str(mapping["Variable_ID"])
                    score_column = (
                        "Module2_" + "".join(
                            char if char.isalnum() else "_" for char in variable_id
                        ).strip("_")
                    )
                    variable_label = str(mapping["Variable"])
                    variable_manifest_row = next(
                        (row for row in module2_variables if str(row["Variable_ID"]) == variable_id),
                        {},
                    )
                    if numeric_items:
                        df_analytics[score_column] = df_analytics[numeric_items].mean(axis=1)
                        scale_properties = {
                            "column": score_column,
                            "items": numeric_items,
                            "label": variable_label,
                            "framework": str(variable_manifest_row.get("Framework_Source", "")),
                        }
                    else:
                        scale_properties = None
                    if len(numeric_items) >= 2:
                        clean_items = df_analytics[numeric_items].dropna()
                        if len(clean_items) > 1:
                            item_variances = clean_items.var(ddof=1, axis=0).sum()
                            total_variance = clean_items.sum(axis=1).var(ddof=1)
                            if total_variance > 0:
                                alpha_val = (
                                    len(numeric_items) / (len(numeric_items) - 1)
                                ) * (1 - item_variances / total_variance)
                                scale_properties["alpha"] = alpha_val
                    if scale_properties:
                        computed_scales_manifest[variable_id] = scale_properties
                    if categorical_items:
                        mapped_categorical_variables[variable_id] = {
                            "label": variable_label,
                            "columns": categorical_items,
                            "framework": str(variable_manifest_row.get("Framework_Source", "")),
                        }
                mapped_variable_count = (
                    len(computed_scales_manifest) + len(mapped_categorical_variables)
                )
                if mapped_variable_count:
                    st.success(
                        f"Mapped {mapped_variable_count} Module 2 variable(s) to observed dataset columns."
                    )
            else:
                st.info("The Module 2 matrix has no variables to map, or this dataset has no usable columns.")
        else:
            st.info(
                "To map analytics to your study framework, select variables in Module 2 during this "
                "session or upload the Module 2 Theory and Variable Matrix CSV above."
            )
        if mapped_categorical_variables:
            st.markdown("**Categorical Module 2 variable response counts**")
            for variable in mapped_categorical_variables.values():
                for column in variable["columns"]:
                    st.caption(f"{variable['label']} — `{column}`")
                    counts = (
                        df_analytics[column]
                        .fillna("Missing")
                        .value_counts()
                        .rename_axis("Response")
                        .reset_index(name="Count")
                    )
                    st.dataframe(counts, use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("📊 3. Variable Distribution Explorer")
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
        st.subheader("🧮 4. Module 2 Variable Scores and Reliability")
        st.caption(
            "Composite scores use the selected numeric columns. Internal consistency is calculated "
            "only for variables mapped to two or more items; it is not inferred from framework names."
        )
        scale_summary_text = "=== CRONBACH'S ALPHA INTERNAL CONSISTENCY PROFILE ===\n"
        variables_with_alpha = [
            (variable_id, properties)
            for variable_id, properties in computed_scales_manifest.items()
            if "alpha" in properties
        ]
        if variables_with_alpha:
            for variable_id, properties in variables_with_alpha:
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.metric(
                        label=f"{properties['label']} Mean Score",
                        value=f"{df_analytics[properties['column']].mean():.2f}",
                    )
                with col_m2:
                    st.metric(
                        label=f"{properties['label']} Cronbach's Alpha (α)",
                        value=f"{properties['alpha']:.3f}",
                        help="Interpret reliability in light of the instrument, sample, and study context.",
                    )
                scale_summary_text += (
                    f"Variable: {properties['label']} ({variable_id})\n"
                    f"Framework: {properties['framework']}\n"
                    f"Mapped items: {', '.join(properties['items'])}\n"
                    f"Cronbach's alpha: {properties['alpha']:.4f}\n\n"
                )
        elif computed_scales_manifest:
            st.info(
                "Mapped variables have single items only. Cronbach's alpha requires at least "
                "two items for a variable."
            )
        else:
            st.info(
                "Map Module 2 variables to dataset columns above to calculate theory-aligned "
                "composite scores and reliability."
            )

        st.divider()
        st.subheader("🔗 5. Variable Relationship Matrix")
        correlation_method = st.selectbox(
            "Correlation method",
            options=["Spearman", "Pearson"],
            help="Spearman is appropriate for ordinal/ranked data; Pearson is for suitable continuous measures.",
            key="analytics_correlation_method",
        )
        correlation_targets = [
            properties["column"] for properties in computed_scales_manifest.values()
        ]
        correlation_targets.extend(
            column for column in numeric_cols if column not in correlation_targets
        )
        
        if len(correlation_targets) >= 2:
            correlation_matrix = df_analytics[correlation_targets].corr(
                method=correlation_method.lower()
            )
            friendly_labels = {
                column: properties["label"]
                for properties in computed_scales_manifest.values()
                for column in [properties["column"]]
            }
            clean_corr_matrix = correlation_matrix.rename(index=friendly_labels, columns=friendly_labels)
            
            st.markdown(f"**{correlation_method} Correlation Matrix:**")
            st.dataframe(clean_corr_matrix.style.background_gradient(cmap="coolwarm", axis=None).format("{:.3f}"), use_container_width=True)
        else:
            st.warning("Select or map at least two numeric variables to build a correlation matrix.")
            clean_corr_matrix = pd.DataFrame()

        st.divider()
        st.subheader("📥 6. Download Evaluation Compendium")
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
                ax_corr.set_title(f"{correlation_method} Correlation Matrix", pad=20)
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
    st.caption("Seeking custom calculations? Enter a metric or statistical test title below. If you don't know the code, our system will auto-generate a Python template for you!")
    
    suggested_stat_metric = st.text_input("Proposed Statistical Function Title", placeholder="e.g., Two-Way ANOVA, Chi-Square Test", key="mod4_metric")
    suggested_stat_code = st.text_area("Proposed Python Code block (Optional)", placeholder="Leave blank to let the system auto-create the statistical calculation template...", height=100, key="mod4_code")
    
    if suggested_stat_metric:
        if st.button(
            "🚀 Push Function to GitHub as Pull Request",
            key="submit_mod4_pr_btn",
            disabled=preview_mode,
        ):
            with st.spinner("Analyzing request and auto-generating statistical code block..."):
                
                # 1. AUTO-GENERATION ENGINE: Check if the user left the code block blank
                final_code_block = suggested_stat_code.strip()
                if not final_code_block:
                    metric_lower = suggested_stat_metric.lower()
                    
                    # Programmatic boilerplate generation rules based on common research models
                    if "anova" in metric_lower:
                        final_code_block = (
                            "import statsmodels.api as sm\n"
                            "from statsmodels.formula.api import ols\n\n"
                            "def calculate_custom_anova(df, dependent_var, independent_vars):\n"
                            "    # Auto-generated ANOVA formula wrapper\n"
                            "    formula = f'{dependent_var} ~ C({independent_vars[0]}) * C({independent_vars[1]})'\n"
                            "    model = ols(formula, data=df).fit()\n"
                            "    anova_table = sm.stats.anova_lm(model, typ=2)\n"
                            "    return anova_table"
                        )
                    elif "chi" in metric_lower or "square" in metric_lower:
                        final_code_block = (
                            "from scipy.stats import chi2_contingency\n\n"
                            "def calculate_custom_chisquare(df, col1, col2):\n"
                            "    # Auto-generated Chi-Square contingency analyzer\n"
                            "    contingency_table = pd.crosstab(df[col1], df[col2])\n"
                            "    chi2, p, dof, expected = chi2_contingency(contingency_table)\n"
                            "    return {'chi2_stat': chi2, 'p_value': p, 'degrees_of_freedom': dof}"
                        )
                    elif "regression" in metric_lower:
                        final_code_block = (
                            "import statsmodels.api as sm\n\n"
                            "def calculate_custom_regression(df, y_col, x_cols):\n"
                            "    # Auto-generated Linear Regression (OLS) model\n"
                            "    X = sm.add_constant(df[x_cols])\n"
                            "    y = df[y_col]\n"
                            "    model = sm.OLS(y, X).fit()\n"
                            "    return model.summary()"
                        )
                    else:
                        # Standard fail-safe mathematical descriptive vector blueprint
                        final_code_block = (
                            "import numpy as np\n"
                            "import scipy.stats as stats\n\n"
                            f"def calculate_{suggested_stat_metric.lower().replace(' ', '_')}(data_vector):\n"
                            f"    # Standard evaluation model for {suggested_stat_metric}\n"
                            "    clean_data = data_vector[~np.isnan(data_vector)]\n"
                            "    metric_mean = np.mean(clean_data)\n"
                            "    metric_variance = np.var(clean_data)\n"
                            "    return {'mean': metric_mean, 'variance': metric_variance}"
                        )
                
                # 2. Package the payload safely into an isolated string block
                analytics_payload = (
                    f"**Analytics Engine Function Enhancement Proposal**\n\n"
                    f"**Target Statistical Metric:** {suggested_stat_metric}\n\n"
                    f"### PROPOSED PYTHON ALGORITHM CODE\n"
                    f"```text\n{final_code_block}\n```\n\n"
                    f"---\n*Submitted securely via the Descriptive & Scale Analytics Suggestion Pipeline Interface.*"
                )
                
                # 3. Fire your global PyGithub worker function
                safe_filename = f"analytics_proposal_{suggested_stat_metric.lower().replace(' ', '_')}.txt"
                summary_title = f"Add Analytics Metric: {suggested_stat_metric}"
                
                result_message = automate_github_pull_request(
                    suggestion_type="Analytics",
                    file_name=safe_filename,
                    file_content=analytics_payload,
                    title_summary=summary_title
                )
                
                if "❌" in result_message:
                    st.error(result_message)
                else:
                    st.success(result_message)


# ==========================================
# MODULE 5: LIVE CENTRAL DATABASE VIEWER
# ==========================================
if app_mode == "5. Live Central Database Viewer":
    st.header("🗄️ Central Repository Live Database Viewer")
    st.caption("Read-only access to study and variable records visible to your signed-in account under Supabase Row Level Security.")
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

    target_table = str(st.session_state.get("active_db_view", "studies")).strip().lower()

    if preview_mode:
        st.subheader(f"📂 Preview: `{target_table}`")
        st.caption("Illustrative sample only — sign in to view authorized repository records.")
        if target_table == "studies":
            display_df = pd.DataFrame(
                [
                    {
                        "study_title": "Example: Student engagement and open learning",
                        "principal_investigator": "Example Research Team",
                        "institution": "Example University",
                        "funding_source": "Example Foundation",
                    }
                ]
            )
        else:
            display_df = pd.DataFrame(
                [
                    {
                        "variable_name": "Example learning engagement",
                        "variable_label": "Student engagement",
                        "data_type": "Ordinal",
                        "description": "Illustrative measure; not a real study record.",
                    }
                ]
            )
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        try:
            with st.spinner(f"Loading `{target_table}` records you are authorized to view..."):
                db_response = user_client.from_(target_table).select("*").execute()

                if db_response.data is not None:
                    display_df = pd.DataFrame(db_response.data)

                    st.subheader(f"📂 Connected Matrix: `{target_table}`")
                    if not display_df.empty:
                        st.dataframe(display_df, use_container_width=True, hide_index=True)

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
