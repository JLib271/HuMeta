# Contributing to HuMeta

Thank you for helping build shared infrastructure for research in education, the social sciences, and the humanities.
You do not need to be a programmer to contribute: researchers who add or check
instrument records are as important as people who write code.

By participating you agree to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Ways to contribute

| You are… | You could… |
|---|---|
| A researcher | Recommend a theory, framework, or instrument (Module 2's **Recommend** tabs, no GitHub needed), add an instrument to the library, check a record's `needs_check` items against the source, report a confusing form, suggest a response scale or standard variable |
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
ruff check --select F,E9 openscience.py oem tests scripts
```

## How the code is organized

* `oem/` holds logic with **no Streamlit dependency** (`library.py`, `naming.py`,
  `codebook.py`, `vocab.py`). Put new logic here and test it in `tests/`.
* `oem/app/pages/` holds one file per app module, each with a `render()`
  function. Keep pages thin: they should collect input and call into `oem/`.
* `library/` is a snapshot of the published [HuMeta Instrument Library](https://github.com/JLib271/humeta-library); change the library there.

## Pull request workflow

1. Open or comment on an issue first for anything larger than a small fix, so
   effort isn't duplicated.
2. Create a branch from `main` (forks welcome).
3. Keep each pull request focused on one change, with tests for new logic.
4. Fill in the pull request template. CI must pass.
5. A maintainer reviews. Changes to `library/` content also need a check of
   the cited sources.

Commits should describe *why* a change was made. We use squash merges.

## Recommending theories, frameworks, and instruments

The easiest way is in the app: **Module 2 → Recommend a theory or framework**,
**Recommend an instrument**, or **Suggest a correction**. You sign in, fill in a
short structured form, and the app opens a pull request for review. You don't
need a GitHub account. The pull request opens in the
[HuMeta Instrument Library](https://github.com/JLib271/humeta-library) (analysis
recommendations open here, in `suggestions/analyses/`). People who use GitHub
can use the library's issue forms instead, from the
[Library website's Recommend page](https://jlib271.github.io/humeta-library/recommend/).

## Contributing to the instrument library

The library has its own repository,
[humeta-library](https://github.com/JLib271/humeta-library); see its
[CONTRIBUTING.md](https://github.com/JLib271/humeta-library/blob/main/CONTRIBUTING.md).
`library/` here is a snapshot of the published library: don't edit it here
(refresh it with `python scripts/update_library.py`).

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
