# STEMEd+ Metadata Application Profile (STEMEd+ AP)

**Version:** 1.0.0-draft.1 · **Status:** Draft for community comment · **Namespace prefix:** `stemed`

The STEMEd+ Metadata Application Profile is a shared way to describe research
data, instruments, and studies in STEM education research and related fields,
including informal and public science learning. It adds what general-purpose
repository metadata leaves out:

* **Constructs measured**, from a shared, defined construct vocabulary
* **Population and context**: who participated, at what education level, in
  what kind of institution and community
* **Instructional setting**: modality, learning environment, and instructional
  approach
* **Evidence type**: study design, measurement (validity and reliability)
  evidence, and data collection methods
* **Consent and access**: human-subjects review, consent for participation and
  for data sharing, identifiability, sensitivity, and access level
* **CARE**: whether the resource involves Indigenous data and how Indigenous
  authority to control those data is exercised

Every record also carries standard citation metadata, and the profile defines
crosswalks to **DataCite Metadata Schema 4.7** and the **ERIC Thesaurus**, so
records work with DOI registration, repositories, and education indexes that
people already use.

## Contents of this folder

| File | What it is |
|---|---|
| `profile.json` | **Source.** Element definitions, obligations, DataCite mappings, rules |
| `vocabularies.json` | **Source.** Controlled vocabularies with permanent term codes and ERIC mappings |
| `../../library/constructs.json` | **Source.** The construct vocabulary (shared with the instrument library) |
| [`elements.md`](elements.md) | Readable reference for every element, rule, and vocabulary (generated) |
| `schema/stemed-ap-record.schema.json` | JSON Schema for records (generated) |
| `crosswalks/datacite-4.7.csv` | Element-to-DataCite crosswalk (generated) |
| `crosswalks/alignments.csv` | Every element's alignment to DataCite, Dublin Core, schema.org, ERIC and other standards, with match type (generated) |
| `crosswalks/eric.csv` | Vocabulary-to-ERIC descriptor crosswalk with verification status (generated) |
| `crosswalks/eric_descriptor_status.json` | Which ERIC descriptors have been verified, and how |
| `examples/` | Example record with its DataCite JSON and XML (fictional study) |
| `endorsement/` | Process and materials for community endorsement of version 1.0 |
| `CHANGELOG.md` | Version history |

Generated files are rebuilt with `python scripts/build_profile_artifacts.py`;
CI fails if they are out of date.

## 1. Scope

The profile describes **resources** produced or used in STEM education
research: datasets, instruments, study registrations, and related texts and
software. It applies to formal education (K-12, postsecondary, graduate,
adult), informal and public learning (museums, science centers, community and
out-of-school programs), and research with educators. It describes resources;
it does not contain participant data.

## 2. Record structure and conformance

A STEMEd+ record is a JSON object with two parts:

* `resource`: citation metadata aligned with DataCite (title, creators with
  ORCID iDs, publisher, publication year, resource type, identifier,
  description, keywords, language, license, funding, collection dates,
  geography, related resources)
* `stemed`: the profile's extension elements, grouped as `constructs`,
  `discipline`, `population`, `context`, `setting`, `evidence`, `ethics`, and
  `care`

A record **conforms** to version 1.0 of the profile when it (1) validates
against `schema/stemed-ap-record.schema.json`, (2) includes every mandatory
(M) element and every mandatory-if-applicable (MA) element whose condition
holds, and (3) triggers no rule of severity *error*. Warnings do not prevent
conformance but should be reviewed. The reference implementation of these
checks is `oem/profile.py` (`validate()`).

### Obligations

| Code | Meaning |
|---|---|
| M | Mandatory: every record |
| MA | Mandatory if applicable: required when its condition holds |
| R | Recommended |
| O | Optional |

### Element summary

| Element | Obl. | Vocabulary |
|---|---|---|
| `resource.title`, `.creators`, `.publisher`, `.publication_year`, `.resource_type` | M | DataCite resourceTypeGeneral |
| `stemed.constructs` | MA (datasets, instruments) | construct vocabulary |
| `stemed.discipline` | R | `discipline` |
| `stemed.population.participant_roles` | M | `participant_role` |
| `stemed.population.education_levels` | M | `education_level` |
| `stemed.population.undergraduate_levels`, `.description`, `.sample_size` | O / R / R | `undergraduate_level` |
| `stemed.context.institution_types`, `.locale` | R | `institution_type`, `locale` |
| `stemed.setting.modality`, `.learning_environments`, `.pedagogy` | R / R / O | `modality`, `learning_environment`, `pedagogy` |
| `stemed.evidence.study_designs` | MA (datasets, study registrations) | `study_design` |
| `stemed.evidence.measurement_evidence` | MA (instruments) | `measurement_evidence` |
| `stemed.evidence.data_collection_methods` | R | `data_collection_method` |
| `stemed.ethics.human_subjects_review`, `.consent_for_sharing`, `.identifiability`, `.access_level` | M | see vocabularies |
| `stemed.ethics.consent`, `.sensitivity_flags` | R | `consent`, `sensitivity_flag` |
| `stemed.care.indigenous_data` | M | `indigenous_data` |
| `stemed.care.governance`, `.statement` | MA (Indigenous data) | `indigenous_governance` |
| `stemed.care.local_contexts_project`, `.local_contexts_labels` | O | Local Contexts |

Full definitions, cardinalities, and DataCite mappings are in
[`elements.md`](elements.md).

## 3. Responsible-sharing rules

The profile encodes rules that connect consent, identifiability, review, and
Indigenous data governance to the access level a record declares:

| Rule | Severity | Requirement |
|---|---|---|
| R1 | error | Datasets and instruments list at least one construct measured |
| R2 | error | Datasets and study registrations list at least one study design |
| R3 | error | Instruments list at least one kind of measurement evidence |
| R4 | error | Open access requires de-identified, anonymous, aggregate, synthetic, or non-participant data |
| R5 | error | Open access requires consent for broad sharing (or no human-subjects data) |
| R6 | error | No open or registered access while human-subjects review is not assessed or pending |
| R7 | error | Indigenous data require a governance arrangement and a CARE statement |
| R8 | error | Indigenous data may be open only under a community agreement or tribal review approval |
| R9 | warning | Education records (FERPA): confirm institutional review before sharing |
| R10 | warning | Indigenous data status unknown |
| R11 | warning | A specific community or tribal college is involved: confirm Indigenous data status |
| R12 | warning | Direct identifiers must be removed before sharing |

These rules check consistency of what a researcher reports. They are not an
IRB, FERPA, or legal determination, and they do not replace review by an
institution or by Indigenous nations and communities.

## 4. CARE and Indigenous data governance

The `care` elements implement the CARE Principles for Indigenous Data
Governance (Collective benefit, Authority to control, Responsibility, Ethics;
Carroll et al., 2020). They ask whether a resource involves Indigenous data,
how Indigenous authority to control those data is exercised, and for a
statement of collective benefit and responsibility. They can point to
Local Contexts Traditional Knowledge or Biocultural Labels and Notices applied
by the community. Following CARE means deferring to Indigenous-led governance;
the profile records that governance but does not substitute for it. Revisions
to these elements should be made with Indigenous data governance experts.

## 5. Vocabularies

Vocabularies are in `vocabularies.json` and the construct vocabulary is in
`library/constructs.json`. Rules for maintaining them:

* Term codes are **permanent**. A code is never renamed or reused; a term that
  is no longer needed is marked deprecated in a later version.
* Each term has a label and, where applicable, ERIC descriptors.
* Vocabularies follow established standards where they exist; for example,
  measurement evidence uses the sources of validity evidence in the
  *Standards for Educational and Psychological Testing*.

## 6. Crosswalks

### Alignments

Every element in `profile.json` lists the standards it corresponds to, under
`alignments`, each with a match type: **exact** (same meaning), **close**
(≈, similar enough to map with care) or **related** (~, overlapping but not
interchangeable). Elements marked `STEMEd+` are defined by this profile and
have no equivalent in a general-purpose standard. The standards are listed in
the `standards` block of `profile.json`. The OpenEdMetadata app shows these
alignments beside each field, `elements.md` shows them per element, and
`crosswalks/alignments.csv` lists them all.

### DataCite Metadata Schema 4.7

Resource elements map directly to DataCite properties. Profile vocabularies
map to `subjects` with a `subjectScheme` (e.g. "STEMEd+ Constructs") and a
`valueURI` for each term; ERIC descriptors are added as subjects with
`subjectScheme` "ERIC Thesaurus". Study designs, methods, and population
descriptions become a `Methods` description. Ethics, access, and CARE
information becomes `Other` descriptions and `rightsList` entries. For
datasets, the instrument used is linked with `relationType` `IsCollectedBy`
(added in DataCite 4.5 for instruments), and its publication with
`References`. Sample size maps to `sizes`, collection dates to a `Collected`
date range, and places to `geoLocationPlace`. The generated XML for the
example validates against the official DataCite 4.7 XML Schema (tested in
CI). See `crosswalks/datacite-4.7.csv`.

### ERIC Thesaurus

Every construct and vocabulary term with an ERIC equivalent lists one or more
ERIC descriptors (`crosswalks/eric.csv`). Descriptors were checked against the
ERIC Thesaurus on 2026-11-01; retired descriptors (shown in ERIC in italics
with a year) are replaced by their current equivalents. Descriptors that could
not yet be confirmed are marked *unverified* and are **excluded from exports**
until confirmed with `scripts/verify_eric_descriptors.py` against the official
thesaurus download.

### Other targets

Knowledge Commons Works and other InvenioRDM repositories, Dublin Core, and
schema.org are candidate future targets. Because the profile is defined as
data, adding a crosswalk does not change the profile.

## 7. Implementations

* **OpenEdMetadata app**: Module 1 is the profile form for a study; Module 3
  adds the constructs measured (suggested from the Module 2 variable plan),
  checks the rules, and exports DataCite and ERIC metadata.
* **`oem/profile.py`**: reference Python implementation (validation, DataCite
  JSON/XML, ERIC descriptors), with tests in `tests/test_profile.py`.
* **JSON Schema** for use in any language.

## 8. Versioning and governance

The profile uses semantic versioning. **Patch** releases fix wording or add
crosswalk entries; **minor** releases add optional elements or vocabulary
terms; **major** releases change mandatory elements or remove anything.
Proposed changes are opened as issues labeled `proposal` and left open for at
least 14 days of comment (see [GOVERNANCE.md](../../GOVERNANCE.md)). Version
1.0.0 will be released after a public comment period and submitted for
endorsement; see [`endorsement/`](endorsement/).

## 9. License and citation

The profile (this folder and the construct vocabulary) is licensed under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), like the rest
of the library. Code implementing it is AGPL-3.0-or-later. Cite as:

> Libarkin, J. C., & STEMEd+ contributors. (2026). *STEMEd+ Metadata
> Application Profile* (Version 1.0.0-draft.1). OpenEdMetadata.
> https://github.com/JLib271/OpenEdMetadata/tree/main/standard/stemed-ap

A DOI will be registered for version 1.0.0 (DataCite resourceTypeGeneral
`Standard`).

## References

* American Educational Research Association, American Psychological
  Association, & National Council on Measurement in Education. (2014).
  *Standards for educational and psychological testing.* AERA.
* Carroll, S. R., et al. (2020). The CARE Principles for Indigenous Data
  Governance. *Data Science Journal, 19*(1), 43.
  https://doi.org/10.5334/dsj-2020-043
* DataCite Metadata Working Group. (2026). *DataCite Metadata Schema
  Documentation for the Publication and Citation of Research Data and Other
  Research Outputs* (Version 4.7). DataCite e.V. https://schema.datacite.org/
* Education Resources Information Center. *ERIC Thesaurus.*
  https://eric.ed.gov/?ti=all
* Global Indigenous Data Alliance. *CARE Principles for Indigenous Data
  Governance.* https://www.gida-global.org/care
* Local Contexts. *Traditional Knowledge and Biocultural Labels and Notices.*
  https://localcontexts.org/
