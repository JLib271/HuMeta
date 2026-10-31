# STEMEd+ Instrument Library

A community-curated, version-controlled library of STEM education research
instruments: what each one measures, its versions and adaptations, how it is
scored, how it can be accessed, and the reliability and validity evidence
reported for it in different populations.

The library describes instruments. It never stores item text, unless an
instrument's terms explicitly allow republishing, and even then it links
instead of copying by default.

## Layout

```
library/
  constructs.json              shared construct vocabulary (what things measure)
  instruments/<id>.json        one file per instrument
  evidence/<instrument-id>/<record-id>.json
                               one file per reliability/validity result
  items/<instrument-id>/<version-id>.json
                               the items in one version: always a crosswalk,
                               plus item text only where permitted
  schema/                      JSON Schemas for all three
scripts/validate_library.py    run before opening a PR
```

## The three record types

**Constructs** (`constructs.json`) are the shared vocabulary that links
instruments, Module 2 variables, and evidence. Each has an id, a definition in
our own words, synonyms used to match free-text searches, and optionally the
Module 2 variable keys (from `schema_config.json`) it corresponds to. Add a
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
(contributed from a study run through the OpenEdMetadata app). Both use the
same format, so evidence across populations can be compared side by side.

**Item files** (`items/<instrument-id>/<version-id>.json`) list a version's
items by stable `item_id` and position `number`. An unchanged item keeps the
same `item_id` in every version's file, so items line up across versions
automatically; a changed item gets a new `item_id` and a `derived_from` link
saying how it changed (reworded, domain word swapped, options changed,
translated, ...). Item text (`stem`, option `text`) is accepted only when the
instrument permits it, and correct answers (`is_correct`) only when
`access.answer_key_shareable` is true. The validator enforces both.

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

## Relationship to `catalogs/measure_catalog.json`

The existing flat catalog read by Module 2 is superseded by this library once
Module 2 is updated to read `library/`. Until then, the two are independent.
