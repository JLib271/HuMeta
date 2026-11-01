# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reference data used by the app (no Streamlit): file locations and the theory and
framework dictionaries used by Module 2. Study metadata vocabularies live in the
STEMEd+ profile (standard/stemed-ap/vocabularies.json)."""

from __future__ import annotations

from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
PUBLISHED_DIR = APP_DIR / "published"
PUBLISHED_SUMMARIES_DIR = PUBLISHED_DIR / "study_summaries"
PUBLISHED_DATASETS_DIR = PUBLISHED_DIR / "datasets"
DEFAULT_GITHUB_REPO = "JLib271/OpenEdMetadata"
PUBLIC_DATASET_MAX_MB = 25
PROJECT_FILE_FORMAT = "openedmetadata-project"

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
