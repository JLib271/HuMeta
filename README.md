# Open Educational Metadata Platform 🔬🌐

An advanced, open-source, community-driven web interface and psychometric validation engine designed to standardize, align, and process educational survey data. This ecosystem is fully integrated with a live Postgres database and programmatic GitOps deployment pipelines, turning research tracking into a seamless cloud experience.

## 🔗 Live Application Access
The platform is fully compiled and deployed in a live cloud container:
👉 **[Open Educational Metadata Portal](https://streamlit.app)**

---

## 🛠️ Key Architectural Layout (Modules 1–5)

The system is split into five core functional layers managed by interactive sidebar navigation:

1. **Study Metadata Schema Registry (Module 1):** Ingests core study metadata frames following strict Dublin Core Metadata Element Set (DCMES) criteria and pipes entries instantly into cloud storage.
2. **Variable Instrument Architect (Module 2):** Connects variable definitions, properties, and continuous Likert scaling matrices directly to structural parent fields. Supports custom CSV asset template schema ingestion.
3. **Community Data Repository Sync (Module 3):** Monitors connection integrity metrics, tracking encrypted data streams flowing across connected community workspace warehouses.
4. **Descriptive & Scale Analytics Engine (Module 4):** Evaluates multi-item measurement configurations via an automated **Cronbach's Alpha Internal Consistency Profile**, computes background styled correlation heatmaps, compiles customized PDF summary reports via ReportLab, and features a smart template generator that automatically writes code files for newly proposed statistical test metrics.
5. **Central Repository Live Database Viewer (Module 5):** Provides direct, read-only analytical access to active relational PostgreSQL tuples streaming straight from cloud tables, complete with direct `.csv` file download streaming engines.

---

## 🤖 Integrated GitOps Pull Request Automation
Rather than forcing researchers to manage complex command-line actions or leave the portal to copy-paste suggestions, Modules 1, 2, and 4 connect directly to the GitHub API via a secure **Personal Access Token (PAT)**. 

When a structural change or new analysis function is requested:
1. The application automatically forks an independent branch off the head of the `main` branch.
2. It saves the formatted data proposal into the `/suggestions` folder.
3. It issues an official, structured **Pull Request (PR)**, allowing repository maintainers to seamlessly review and merge community additions into the core codebase with a single click.
4. **Smart Template Engine:** If a user proposes an analytical calculation inside Module 4 but leaves the code block blank, the system automatically writes a clean statistical template script (e.g., using `scipy.stats` or `statsmodels`) and appends it to the Pull Request automatically.

---

## 📊 Core Cloud Architecture (Supabase Schema)

Data persistence is managed via an active cloud **Supabase** instance. The database utilizes a strictly connected relational cascade pattern (`ON DELETE CASCADE`) to bind survey parameters to core studies in the `public` schema layer:

```sql
-- 1. Parent Studies Ingestion Table
create table public.studies (
    id uuid primary key default gen_random_uuid(),
    study_title text not null,
    principal_investigator text,
    institution text,
    funding_source text,
    study_description text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 2. Child Variables Dictionary Table
create table public.variables (
    id uuid primary key default gen_random_uuid(),
    study_id uuid references public.studies(id) on delete cascade,
    variable_name text not null,
    variable_label text,
    data_type text,
    measurement_unit text,
    description text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);
```

---

## ⚙️ Secrets Deployment Configuration

To host this application or configure an independent Streamlit Community Cloud mirror instance, populate your **App Secrets (`.toml`)** file inside your workspace management panel using this format:

```toml
# Cloud Data Warehouse Connection Tokens
SUPABASE_URL = "https://supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." # Extended anon/public client API key

# GitOps Automation Security Token
GITHUB_PAT = "ghp_YourPersonalAccessTokenFromGitHub..."
```

---

## 🚀 Local Installation & Setup

To run this application locally on your workstation for development or extension testing:

1. **Clone the Repository:**
   ```bash
   git clone https://github.com
   cd openedmetadata
   ```

2. **Configure Environment Secrets:**
   Create a local directory configuration folder `.streamlit/` and place a `secrets.toml` file inside it containing your active keys:
   ```bash
   mkdir .streamlit
   touch .streamlit/secrets.toml
   ```

3. **Install Dependencies:**
   Ensure your Python environment is completely up to date and load the required library stack:
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the Engine:**
   Run the boot sequence via your local Streamlit compiler:
   ```bash
   streamlit run openscience.py
   ```

---

## 📜 Dependencies Checklist (`requirements.txt`)
The minimal library environment grid required for this portal consists of:
```text
streamlit>=1.30.0
pandas>=2.0.0
numpy>=1.24.0
supabase>=2.3.0
PyGithub>=2.1.0
matplotlib>=3.7.0
reportlab>=4.0.0
scipy>=1.10.0
statsmodels>=0.14.0
```

---

## 📄 License & Terms
Distributed under the **MIT License**. Other research institutions and education task forces are explicitly granted legal permission to copy, alter, scale, and redistribute this platform, provided proper attribution credit is maintained.

