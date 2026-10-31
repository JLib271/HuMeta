# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Controlled vocabularies and reference data used by the app (no Streamlit)."""

from __future__ import annotations

from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
PUBLISHED_DIR = APP_DIR / "published"
PUBLISHED_SUMMARIES_DIR = PUBLISHED_DIR / "study_summaries"
PUBLISHED_DATASETS_DIR = PUBLISHED_DIR / "datasets"
DEFAULT_GITHUB_REPO = "JLib271/OpenEdMetadata"
PUBLIC_DATASET_MAX_MB = 25
PROJECT_FILE_FORMAT = "openedmetadata-project"
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
