# HuMeta Instrument Library

A community-curated, version-controlled library of research instruments,
starting with STEM education research and growing with the social sciences
and humanities: what each one measures, its versions and adaptations, how it is
scored, how it can be accessed, and the reliability and validity evidence
reported for it in different populations.

The library describes instruments. It never stores item text, unless an
instrument's terms explicitly allow republishing, and even then it links
instead of copying by default.

## Layout

```
library/
  constructs.json              shared construct vocabulary (what things measure)
  frameworks.json              theories, theoretical lenses, and framework approaches
                               used by Module 2, with each theory's constructs
  instruments/<id>.json        one file per instrument
  evidence/<instrument-id>/<record-id>.json
                               one file per reliability/validity result
  items/<instrument-id>/<version-id>.json
                               the items in one version: always a crosswalk,
                               plus item text only where permitted
  schema/                      JSON Schemas for all three
scripts/validate_library.py    run before opening a PR
```

## Speaking HuMeta

The library describes instruments and evidence samples with the HuMeta
standard's own vocabularies ([`vocabularies.json`](https://github.com/JLib271/humeta-profile/blob/main/vocabularies.json), copied in `standard/humeta/`), so an
instrument and a study described with HuMeta use the same words:

| Library field | HuMeta vocabulary |
|---|---|
| `disciplines` (instruments, theories, evidence samples) | `discipline` (ANZSRC 2020 Fields of Research, or `discipline_general`) |
| `education_levels`, evidence `sample.education_level` | `education_level` (ISCED-based) |
| `settings`, evidence `sample.setting` | `learning_environment` |
| `participants`, evidence `sample.participants` | `participant_role`: who the instrument gathers data about (for an observation protocol, the people observed) |
| evidence `sample.institution_type` | `institution_type` |
| `instrument_type` (library's own, finer) | maps to `data_collection_method` (`oem/instrument_metadata.py`) |
| rubric categories and criteria | map to `measurement_evidence` (`humeta_evidence` in `evidence_rubric.json`) |

`scripts/validate_library.py` rejects terms that are not current (unknown or
deprecated) in the HuMeta vocabulary. To add a term the library needs, add it to
the HuMeta vocabulary, with a changelog entry, rather than to the library.

**DataCite.** Each instrument record is also published as DataCite 4.7 metadata
(`oem/instrument_metadata.py`; `data/datacite/<id>.json` on the Library
website), and its Library page embeds a schema.org description. The instrument
is typed `Text` with resource type "Research instrument: ..." (KCWorks files
instruments as Text document > Other; DataCite's `Instrument` type is meant for
physical devices). Creators come from `developers`; subjects are the HuMeta
constructs, disciplines (with ANZSRC and FOS codes), education levels (with
ISCED), settings, participants, data collection method, and measurement
evidence; related identifiers link its papers (IsDescribedBy) and KCWorks
deposit. A dataset collected with the instrument points back to it
(IsCollectedBy), as the HuMeta Portal's dataset export already does.

## The three record types

**Constructs** (`constructs.json`) are the shared vocabulary that links
instruments, Module 2 variables, and evidence. Each has an id, a definition in
our own words, synonyms used to match free-text searches, and optionally the
variable keys from the earlier Module 2 that it corresponds to (used only to
convert old variable plans). Add a
construct only when no existing one fits; prefer adding a synonym.

**Instruments** (`instruments/<id>.json`) hold:
- `versions`: each language, discipline adaptation, or revision, with its own
  item count, response format, and scoring. Evidence attaches to a version,
  because an adapted instrument is not automatically as reliable as the
  original.
- `dimensions`: subscales, factors, or code groups. `basis` records *why* a
  dimension exists: `empirical_factor` (supported by factor analysis),
  `design_category` (a content blueprint that is not a validated subscale),
  or `coding_category` (a group of observation codes).
- `form_type`: `fixed_form` (everyone takes the same items) or `item_bank`
  (users assemble subtests from a pool, like the GCI). For banks, `item_count`
  is the pool size and `subtest_length` the recommended subtest size.
- `access`: how to obtain it, and whether item text may be republished.
  `item_text_shareable: true` requires `item_text_basis`: an open license,
  public domain status, or written permission, with where it is documented.
  Being freely downloadable is not by itself permission to republish.
- `review`: status plus a `needs_check` list of open questions.

**Evidence** (`evidence/<instrument-id>/<id>.json`) is one statistic, for one
version (and optionally one dimension), in one sample, from one source.
`source.kind` is `published` (needs a citation) or `platform_derived`
(contributed from a study run through the HuMeta Portal). Both use the
same format, so evidence across populations can be compared side by side.

**Evidence profile and rubric** (`evidence_rubric.json`). Every instrument is
checked against a reliability and validity rubric with eleven categories (I Item
reliability, II Forms reliability, III Item analysis, IV Pre-item content
validity, V Post-item content validity, VI Communication validity, VII Cultural
validity, VIII Scale analysis, IX Criterion and construct validity, X
Multiple-choice item writing, XI Likert-type item writing), each with lettered
criteria. `oem/evidence.py` builds the profile:

- Evidence records meet criteria through their type and statistic (a
  `cronbach_alpha` record meets I.A and I.B; a `test_retest` record meets II.C;
  `item_bias` meets VII.C). Numbers in the rubric (alpha > 0.7, item
  separation > 0.9) are guides, not cut-offs: a criterion counts when a value
  was measured, and the reported values (or range, `statistic.min`/`max`) are
  shown next to the guide.
- An evidence record can list further criteria in `rubric`
  (e.g. `{"category": "scale_analysis", "criterion": "B"}`).
- Criteria that are not statistics (literature review, think-alouds, expert
  review, item-writing rules) go in the instrument's `rubric_review`, with a
  source.
- `source.independent` says whether the evidence comes from the instrument's
  developers (`false`) or from others (`true`).

The profile reports which categories have evidence, the reported values,
the number of samples, and independent evidence. It does not combine them into
one score. Inter-rater agreement is reliability evidence the rubric does not
score (it was written for tests and surveys), so it is shown alongside.

**STEMEd+ Commons deposits** (`commons_records`). Links to deposits about the
instrument on Knowledge Commons Works, ideally in the HuMeta Instrument Library collection
(https://works.hcommons.org/collections/humetainstrumentlibrary/, part of STEMEd+): the instrument, its
manual, a paper, or a link record, with the license chosen at deposit. When the
rights holder deposits the instrument itself under an open license, that
deposit can serve as the `access.item_text_basis` (basis `open_license`, with
the deposit as the evidence).
To fill in an entry from a deposit link (title, DOI, license, collection):
`python scripts/kcworks_lookup.py <link> --kind manual`. When someone recommends
an instrument through the issue form, a workflow runs the same lookup and
comments on the issue.

**Development basis.** An instrument does not need a theory. `development.basis`
records whether it was built from a theory (`framework_ids` or `theory_named`),
from a definition of what to measure, or for a practical need, or that the
sources do not say.

**Item files** (`items/<instrument-id>/<version-id>.json`) list a version's
items by stable `item_id` and position `number`. An unchanged item keeps the
same `item_id` in every version's file, so items line up across versions
automatically; a changed item gets a new `item_id` and a `derived_from` link
saying how it changed (reworded, domain word swapped, options changed,
translated, ...). Item text (`stem`, option `text`) is accepted only when the
instrument permits it, and correct answers (`is_correct`) only when
`access.answer_key_shareable` is true. The validator enforces both.

**Response scales** (`scales.json`) are shared code lists such as `agree5`
(1 = Strongly disagree … 5 = Strongly agree), plus library-wide missing-value
codes (-99 = no response, -98 = not administered). Items and variables point
to a `scale_id` instead of restating labels, so every study codes the same
scale the same way.

**Standard variables** (`standard_variables.json`) are demographic and context
variables with fixed names, wording and codes, for example `participant_id`,
`age_years`, `race_eth` (the 2024 federal combined race/ethnicity question)
and `consent_share`. Each has a `sensitivity` rating (`direct_identifier`,
`quasi_identifier`, `sensitive`, `none`) used to flag variables that need
review before data are shared.

**Variable names** are generated, not typed, using the rules in
`oem/naming.py`: `<instrument prefix>_<item_id>` (e.g. `gci_q05`), one 0/1
variable per option for select-all items (`gci_q01_c`), fixed names for
standard variables, and `_pre` / `_post` / `_t1` … suffixes for repeated
measures. Each instrument's `variable_prefix` must be unique and never change
once data exist.

## Review status

| Status | Meaning |
|---|---|
| `draft` | Entered, not yet reviewed. `needs_check` lists what to verify. |
| `community_submitted` | Submitted through a PR or the app; awaiting a maintainer. |
| `maintainer_reviewed` | A maintainer checked it for format and plausibility. |
| `source_verified` | Every fact checked against the cited source. `needs_check` must be empty. |

The app should show the status next to every record. A listing in this
library is never a claim that an instrument is valid for a particular study.

## Contributing

1. Copy an existing record as a template.
2. Fill it from the primary publication. Put the pages you used in
   `info_sources`, write descriptions in your own words, and list anything you
   couldn't confirm in `review.needs_check` rather than guessing. Use `null` for
   unknown numbers.
3. Run `python scripts/validate_library.py` (requires `pip install jsonschema`).
4. Open a pull request. The **Validate instrument library** GitHub Action runs
   the same check.

Never include item text from restricted instruments, participant data, or
unpublished results.

## License

Library records are CC BY-SA 4.0. Item text is released under each
instrument's own license (`access.item_text_basis.license`), which the
validator requires before any item text is accepted. See
[`LICENSE.md`](LICENSE.md).

## Frameworks

`frameworks.json` lists the theories, theoretical lenses, and framework
approaches offered in Module 2 (Framework and Measures). A theory lists its
constructs, each optionally linked to a shared construct in `constructs.json`
(`shared_construct_id`, with `shared_construct_match`: exact, close, or
related), and its expected paths between constructs, which start the Module 2
diagram. Lenses (for example sociocultural theory or critical race theory)
have no fixed constructs; researchers add their own.
`own` and `exploratory` entries cover a researcher's own framework and
inductive work with no framework chosen in advance. `citation_status: added`
marks citations added by maintainers that a reviewer should confirm.
`disciplines` lists the ANZSRC 2020 Fields of Research divisions or groups (HuMeta discipline vocabulary) where a
framework is widely used, for browsing in Module 2. `status: draft` marks
frameworks whose description, constructs, relationships, and links to shared
constructs still need review by experts in the field. Every theory and lens is
a draft for now; the governance committee removes the mark once it is reviewed.
Frameworks are recorded in a study's HuMeta profile
(`study.design.frameworks`).

## Who decides which instruments measure which constructs

An instrument record's `construct_ids` (and each dimension's `construct_ids`)
say which shared constructs it is recorded as measuring, and
`construct_mapping.status` says whether that mapping has been reviewed. All
mappings are `provisional` until the HuMeta governance committee approves them
(`approved`, with `decided_on` and `decided_by`). The same applies to the links
from a theory's constructs to shared constructs in `frameworks.json`. In
Module 2, researchers see these mappings as candidates, with their status, and
decide for themselves whether an instrument fits their construct.

## Relationship to `catalogs/measure_catalog.json`

Module 2 now reads instruments from this library. The older flat catalog is
only shown in the Module 6 viewer and will be retired.
