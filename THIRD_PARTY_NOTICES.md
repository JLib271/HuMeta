# Third-party vocabularies and schemas

HuMeta reuses published classifications, vocabularies, and schemas so that
records work with the systems researchers already use. This file lists the
third-party material copied into this repository, its source, its license, and
what HuMeta changed. Standards that HuMeta only names or links to (for
example DataCite, Dublin Core, schema.org, or DDI-Codebook element names) are
listed with their links in `standard/humeta/profile.json` and are not copied
here.

## ANZSRC 2020 Fields of Research (disciplines)

* **Used in:** the `discipline` vocabulary in
  `standard/humeta/vocabularies.json` (23 divisions and 213 groups), and the
  `disciplines` tags in the HuMeta Instrument Library's `frameworks.json`
  (https://github.com/JLib271/humeta-library; snapshot in `library/`).
* **Source:** Australian and New Zealand Standard Research Classification
  (ANZSRC) 2020, Fields of Research. Australian Bureau of Statistics (ABS) and
  Stats NZ. Codes and labels taken from the code set published by the New
  Zealand Research Information System
  ([nzris-data-specifications](https://github.com/new-zealand-research-information-system/nzris-data-specifications),
  `code-sets-label-schemes/for-2020.csv`). Concept URIs:
  `https://linked.data.gov.au/def/anzsrc-for/2020/<code>`.
* **Copyright:** © Commonwealth of Australia 2020; © Crown Copyright New
  Zealand 2020.
* **License:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/),
  under which the ABS provides the material on its website
  ([ABS copyright and licence](https://www.abs.gov.au/website-privacy-copyright-and-disclaimer)).
* **Attribution:** Based on Australian Bureau of Statistics and Stats NZ
  material: ANZSRC 2020 Fields of Research.
* **Changes made by HuMeta:** used the division and group levels only (not
  the 1,967 fields); appended "(all)" to division labels; added a
  corresponding OECD Fields of Science (FOS) code to each term, which is
  HuMeta's own mapping and not part of ANZSRC; added ERIC descriptors carried
  over from HuMeta's earlier discipline list. ANZSRC is not endorsed by, and
  its custodians are not responsible for, this adaptation.

## TaDiRAH 2.0.3 (humanities research activities)

* **Used in:** the `tadirah_activity` vocabulary in
  `standard/humeta/vocabularies.json`.
* **Source:** TaDiRAH, Taxonomy of Digital Research Activities in the
  Humanities, version 2.0.3 (DARIAH;
  [github.com/dhtaxonomy/TaDiRAH](https://github.com/dhtaxonomy/TaDiRAH);
  concept URIs `https://vocabs.dariah.eu/tadirah/<id>`).
* **License:** [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)
  (as stated in the TaDiRAH SKOS file).
* **Changes made by HuMeta:** used the 36 second-level concepts, labeled with
  their top-level activity (for example "Analyzing: Content Analysis").

## DDI Alliance controlled vocabularies

* **Used in:** codes in `standard/humeta/vocabularies.json` mapped to the
  DDI vocabularies AnalysisUnit, SamplingProcedure, ModeOfCollection,
  TimeMethod, GeneralDataFormat, DataSourceType, and KindOfData.
* **Source:** DDI Alliance controlled vocabularies
  ([github.com/ddialliance/ddi-cv](https://github.com/ddialliance/ddi-cv)).
* **License:** CC BY 4.0, DDI Alliance.
* **Changes made by HuMeta:** HuMeta terms carry the DDI code and a match
  type (exact, close, related); HuMeta labels are its own.

## DDI-Codebook 2.5.1 XML Schema (tests only)

* **Used in:** `tests/schemas/ddi-codebook-2.5.1/`, to validate the
  DDI-Codebook export. Not part of the application.
* **License:** GNU Lesser General Public License 3.0, © 2014 DDI Alliance (see
  the files' headers and `LICENSE-LGPL-3.0.txt`). Unmodified copy.
