# Contributing to HuMeta

Thank you for helping build shared infrastructure for research in education, the social sciences, and the humanities.
You do not need to be a programmer to contribute: researchers who add or check
instrument records are as important as people who write code.

By participating you agree to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Ways to contribute

| You are… | You could… |
|---|---|
| A researcher | Add an instrument to the library, check a record's `needs_check` items against the source, report a confusing form, suggest a response scale or standard variable |
| A developer | Fix a bug, pick up a [`good first issue`](../../issues?q=is%3Aopen+label%3A%22good+first+issue%22), add tests, improve accessibility |
| A methodologist | Review evidence records, propose naming or codebook conventions, improve de-identification checks |
| A user | Try the app on a real study plan and [open an issue](../../issues/new/choose) describing what got in the way |

See [ROADMAP.md](ROADMAP.md) for where the project is heading.

## Getting set up

```bash
git clone https://github.com/JLib271/HuMeta.git
cd HuMeta
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
streamlit run openscience.py
```

Before opening a pull request, run the same checks CI runs:

```bash
python -m pytest -v                       # unit tests + opens every app page headlessly
python scripts/validate_library.py        # instrument library checks
ruff check --select F,E9 openscience.py oem tests scripts
```

## How the code is organized

* `oem/` holds logic with **no Streamlit dependency** (`library.py`, `naming.py`,
  `codebook.py`, `vocab.py`). Put new logic here and test it in `tests/`.
* `oem/app/pages/` holds one file per app module, each with a `render()`
  function. Keep pages thin: they should collect input and call into `oem/`.
* `library/` is data, not code. See [library/README.md](library/README.md).

## Pull request workflow

1. Open or comment on an issue first for anything larger than a small fix, so
   effort isn't duplicated.
2. Create a branch from `main` (forks welcome).
3. Keep each pull request focused on one change, with tests for new logic.
4. Fill in the pull request template. CI must pass.
5. A maintainer reviews. Changes to `library/` content also need a check of
   the cited sources.

Commits should describe *why* a change was made. We use squash merges.

## Contributing to the instrument library

1. Copy an existing file in `library/instruments/` as a template.
2. Take every fact from the primary publication, list the pages you used in
   `info_sources`, and write descriptions in your own words.
3. Put anything you could not confirm in `review.needs_check` rather than
   guessing; use `null` for unknown numbers.
4. **Never add item text** unless the instrument's license or its developer
   permits it, and record that in `access.item_text_basis`. Never add answer
   keys unless `access.answer_key_shareable` is true.
5. Run `python scripts/validate_library.py`.

Library content is licensed CC BY-SA 4.0 (item text follows each instrument's
own license; see [library/LICENSE.md](library/LICENSE.md)). By contributing
library content you agree to release it under those terms.

## Data and privacy rules (important)

This project deals with human-subjects research. Contributions, issues,
pull requests and test fixtures must **never** contain participant data,
identifiable information, unpublished results, or confidential study details,
not even "fake" data copied from a real dataset. Use the synthetic data
helpers in the app or write obviously artificial values.

If you find sensitive information anywhere in the repository, do not open a
public issue; follow [SECURITY.md](SECURITY.md).

## Licensing of contributions

Code contributions are licensed under the project's
[AGPL-3.0-or-later](LICENSE) license (inbound = outbound): by submitting a pull
request you confirm you have the right to contribute the code under that
license. Library content contributions are CC BY-SA 4.0 as described above.

## Getting help

Open a [discussion or issue](../../issues/new/choose). Maintainers aim to respond
within a week.
