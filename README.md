# Open Educational Metadata 🔬

An open-source, community-driven web interface and psychometric validation engine designed to standardize, align, and process educational survey data. This ecosystem natively implements the **Good, Rattan, & Dweck (2012) Sense of Belonging to Math Scale** alongside the **Canadian Institutes of Health Research (CIHR) Multi-Dimensional Gender Variables Framework**.

---

## 🔒 3-Tier Security & Privacy Architecture
To ensure compliance with institutional review boards (IRBs) and strict student data privacy standards, the portal segregates data into three operational tiers:

*   **Tier 1: Public Study Metadata (Domain-Agnostic)**  
    Captures high-level study characteristics (such as methodology, investigator, and institutional context) using unified metadata schemas across **Dublin Core**, **DDI**, and **IEEE LOM** standards. This tier contains no participant-level fields and is entirely safe for public index discovery.
*   **Tier 2: Confidential Student Roster (Local processing)**  
    Handles individual student responses, multi-dimensional socio-demographic indicators, scale configurations, and open unstructured text notes. **Privacy Guardrail Active:** All data parsed in this tier stays on the user's local machine inside volatile browser memory variables. No data is transmitted across the internet, logged to cookies, or stored in a persistent cloud infrastructure.
*   **Tier 3: Public Anonymized Aggregates (Open Out-Port)**  
    Calculates macro-level demographic matrices, mean subscale summaries, and automated scale reliability diagnostics. Researchers can click a button to download this fully scrubbed open-science data bundle as a `.csv` or `.txt` manifest to publish directly to public registries (e.g., OSF, ICPSR).

---

## 📋 Standardized Data Schema Dictionary
For the internal calculation engine to process, score, and evaluate your datasets automatically, your local input CSV files must contain the following standard variable column headers. 

### 1. Identity & Demographic Keys
*   `StudentID`: Unique alphanumeric tracker code used to separate participant rows.
*   `Gender_Identity`: Structural identifier matching CIHR dimensions (`Woman`, `Man`, `Non-binary`, `Prefer not to answer`, or researcher-defined custom parameters).

### 2. Good et al. (2012) Belonging Subscales (1–5 Likert scale)
Your input data file can use any combination of short or long versions of the scale. The engine adapts instantly to whatever items are present:
*   **Membership Items:** `Belong_Community`, `Member_Math_World`, `Connected_Math`, `Fit_In_Math`
*   **Acceptance Items:** `Feel_Accepted`, `Feel_Valued`, `Feel_Excluded` *(Reverse-scored)*, `Feel_Neglected` *(Reverse-scored)*, `Feel_Appreciated`
*   **Affect Items:** `Feel_Anxious` *(Reverse-scored)*, `Feel_Comfortable`, `Feel_Inadequate` *(Reverse-scored)*, `Feel_At_Ease`, `Feel_Tense` *(Reverse-scored)*, `Feel_Confident`, `Feel_Stressed` *(Reverse-scored)*
*   **Trust Items:** `Trust_Instructors`, `Trust_Evaluation`, `Trust_Materials`, `No_Need_To_Prove_Self`, `Instructors_Committed`
*   **Desire to Fade Items:** `Try_To_Say_Little`, `Wish_Invisible`, `Fade_To_Background`, `Avoid_Attention` *(Note: Desire to Fade items are inverted by the engine so that a higher final score indicates positive belonging).*

### 3. Qualitative Research Notes
*   `Qualitative_Notes`: A text column for open unstructured observations, student survey comments, or teacher contextual field notes.

---

## 🛠️ Local Installation & Development
If you wish to run this gateway locally on your own computer rather than using the live hosted cloud url, use your Mac terminal command-line interface:

1. **Clone or download this repository** code structure onto your system workspace.
2. **Install dependencies:** Run the setup requirements command block to load python libraries:
   ```bash
   pip install streamlit pandas numpy plotly
   ```
3. **Launch the web server engine:** Move to your target folder and activate the client app UI:
   ```bash
   streamlit run openscience.py
   ```

---

## 📈 Analytics Suite
The calculation engine automatically performs the following actions on your active local data sessions:
*   **Adaptive Item-Level Averaging:** Missing columns or short-scale modifications are evaluated seamlessly. Omissions do not skew calculations or penalize overall scores.
*   **Automated Inversion Inverting:** Items marked as reverse-coded are inverted mathematically behind the scenes (`6 - entry_score`) before building averages.
*   **Cronbach's Alpha Reliability Check:** Evaluates internal consistency parameters (\(\alpha\)) dynamically on subscales with two or more variables, alerting researchers to the structural reliability of their short forms.
*   **Dynamic Column Verification Checker:** Displays a live validation matrix flagging missing variable headers and matching keys to prevent run calculation crashes.

---

## 💡 How to Suggest New Metadata Columns
Open Educational Metadata is designed to be fully customizable as education research evolves. If your local study tracks unique parameters (such as First Generation Status, Language Learner Indicators, or Socioeconomic Indices), please contribute them back to the ecosystem:

1. Open your live app portal tab.
2. Navigate to **Tier 2** → **"Propose New Schema Columns"** form sheet.
3. Submit your column name key, subscale alignment category, and educational research justification.
4. Download the updated text data manifest package at the bottom of the page and submit a **GitHub Pull Request (PR)** or log an issue containing your suggestion text bundle!

---

## 📄 License & Terms
Distributed under the **MIT License**. Other research institutions and education task forces are explicitly granted legal permission to copy, alter, scale, and redistribute this platform, provided proper attribution credit is maintained.
