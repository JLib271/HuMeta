name: Secure Code Suggestion PR Gateway

on:
  repository_dispatch:
    types: [propose_custom_schema]

jobs:
  generate-proposal-pr:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write # Required to open formal PR reviews
      
    steps:
      # 1. Pull down repository files
      - name: Checkout Source Code Tree
        uses: actions/checkout@v4
        with:
          ref: main

      # 2. Configure Python environment dependencies
      - name: Setup Python environment
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install Ingestion Dependencies
        run: pip install pandas

      # 3. Inject event data payloads directly into the parsing engine execution runtime
      - name: Run Schema Processing Script Engine
        env:
          FRAMEWORK_NAME: \${{ github.event.client_payload.framework_name }}
          CSV_CONTENT: \${{ github.event.client_payload.csv_content }}
        run: python .github/scripts/parse_csv_suggestion.py

      # 4. Generate Pull Request for Admin Review (The Human-in-the-Loop)
      - name: Create Pull Request for Admin Review
        uses: peter-evans/create-pull-request@v6
        with:
          token: \${{ secrets.GITHUB_TOKEN }}
          commit-message: "propose: add user custom framework schema elements to openscience.py"
          committer: GitHub <noreply@github.com>
          author: github-actions[bot] <github-actions[bot]@://github.com>
          branch: proposal-schema-\${{ github.run_id }}
          title: "[Schema Update] Propose Framework: \${{ github.event.client_payload.framework_name }}"
          body: |
            🤖 **Automated Data Processing Report:**
            This Pull Request was generated automatically from a user-uploaded custom variables CSV template file on your metadata portal webpage.
            
            ### Actions Required by Admin (Human-in-the-Loop):
            1. Click on the **"Files changed"** tab above to review the additions to the `THEORY_MAP` block inside `openscience.py`.
            2. If the variables, definitions, and item texts are scientifically sound, click **"Merge Pull Request"**.
            3. Streamlit Cloud will immediately pick up the merge and push the new theoretical framework live to your dashboard.
          labels: |
            community-suggestion
            human-review-required
