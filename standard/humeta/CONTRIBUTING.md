# Commenting on and changing the HuMeta profile

This repository is the home of the HuMeta profile: the one place where the standard is discussed,
changed, versioned, and released. The [HuMeta Portal](https://github.com/JLib271/HuMeta) uses a
released version of it.

## Commenting

Anyone can comment, with or without proposing a change:

- **Comment on an element or vocabulary:** open an issue with the *Comment on the profile* form.
  Name the element (for example `study.ethics.consent_for_sharing`) or vocabulary term.
- **Propose a change:** use the *Propose a change* form. Proposals are labeled `proposal` and stay
  open for at least 14 days of comment before a decision, as described in the profile's
  [Versioning and governance](README.md#8-versioning-and-governance) section.
- **CARE and Indigenous data governance** comments are especially welcome during the 1.0 public
  comment period.

## Which files to edit

| Edit | Don't edit (generated) |
|---|---|
| `profile.json`: elements, obligations, cardinality, alignments, field modules | `elements.md` |
| `vocabularies.json`: controlled vocabularies and their terms | `schema/humeta-record.schema.json` |
| `README.md`, `CHANGELOG.md`, `endorsement/` | `crosswalks/*.csv` (except `eric_descriptor_status.json`) |
| `examples/*.json` (example records) | `examples/*.datacite.json`, `examples/*.datacite.xml` |
| `stemedplus_disciplines.json` and its schema | |

The generated files are built by the HuMeta Portal's code, which implements the profile. After
editing a source file, regenerate them from a checkout of HuMeta:

```bash
git clone https://github.com/JLib271/HuMeta.git
pip install "jsonschema[format]>=4.18"
python HuMeta/scripts/build_profile_artifacts.py --profile-dir path/to/humeta-profile
```

The **Check** workflow runs the same command with `--check` on every pull request and fails if a
generated file is out of date, if an example record is invalid, or if the STEMEd+ discipline list
does not match its schema.

Record every change under **Unreleased** in `CHANGELOG.md`.

## Releasing a version

1. Move the **Unreleased** entries in `CHANGELOG.md` under the new version and date, and update
   `profile_version` in `profile.json`, the version line at the top of `README.md`, and
   `CITATION.cff`. Regenerate the derived files.
2. Merge to `main`, then tag the release, for example `v1.0.0-draft.2`, and publish a GitHub release
   with the CHANGELOG entries as its notes.
3. In HuMeta, update the portal to the new version:
   `python scripts/update_profile.py --version v1.0.0-draft.2`, run its tests, and open a pull request.

Version numbers follow the rules in the profile's
[Versioning and governance](README.md#8-versioning-and-governance) section. Version 1.0.0 will get a
DataCite DOI (resourceTypeGeneral `Standard`).

## The STEMEd+ discipline list

`stemedplus_disciplines.json` defines the disciplines used across the STEMEd+ Commons sites. Each
site downloads it from `main` when it builds, so a change merged here reaches every site within a
day. Each discipline maps to HuMeta (ANZSRC) discipline terms in `vocabularies.json`.
