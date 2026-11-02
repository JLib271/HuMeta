# Instrument Library content license

The OpenEdMetadata application code is under the GNU AGPL v3.0 (see `/LICENSE`).
The contents of this `library/` folder are licensed separately, as follows.

## 1. Library records: CC BY-SA 4.0

Instrument records, evidence records, the construct vocabulary, and item
crosswalk data (item IDs, numbering, response types, links between versions)
are licensed under the
[Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/).
You may reuse and adapt them, including commercially, if you credit the
library and release adapted material under the same license.

Suggested attribution: *HuMeta Instrument Library, HuMeta Portal
(https://github.com/JLib271/OpenEdMetadata).*

The JSON Schemas in `library/schema/` are part of the library content and
are also CC BY-SA 4.0, so others can adopt the record format. The validator in
`scripts/` is code and falls under the repository's AGPL v3.0.

## 2. Item text: each instrument's own license

Item text (question stems, answer options and figures in
`library/items/`) is **not** covered by section 1. Each instrument's item text
is released under the license recorded in its instrument record at
`access.item_text_basis.license`, and you must follow that license when
reusing it. Item text is included only when that field is filled in.

| Instrument | Item text license |
|---|---|
| Geoscience Concept Inventory v.4 (2014) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) (share-alike), released by the developer |
| Climate Change Concept Inventory (Libarkin et al., 2018) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) (share-alike), released by the lead developer |
| Motivated Strategies for Learning Questionnaire | Public domain; credit the authors |
| COPUS | CC BY-NC-SA 3.0 (noncommercial, share-alike) |

Instruments not listed here have no item text in the library.

## 3. Answer keys

Answer keys are not part of this library unless an instrument record sets
`access.answer_key_shareable` to true.

Nothing in this library is legal advice or a determination that a use is
permitted; check each instrument's terms for your use.
