# Recommendations from the community

Researchers recommend theories, conceptual models and frameworks, instruments,
and corrections from **Module 2 (Framework and Measures)** in the HuMeta
Portal, using its **Recommend** tabs. Researchers who use GitHub can also use
the issue forms. Each recommendation arrives as a pull request that adds one
JSON file:

| Folder | What it holds | Where accepted content goes |
|---|---|---|
| `frameworks/` | Theories, lenses, conceptual models: name, kind, description, concepts, expected relationships, citation | `library/frameworks.json` |
| `instruments/` | Instruments: name, citation, constructs and subscales, access and license, evidence, the submitter's relationship to it | `library/instruments/<id>.json` |
| `corrections/` | Changes to an existing framework, instrument, or construct | the file being corrected |

Older free-text suggestions sit directly in this folder.

## Reviewing a recommendation

The pull request lists a checklist. In short:

1. **Check the source.** Confirm the citation and DOI, and that the concepts,
   relationships, constructs, and subscales match the publication.
2. **Link to constructs.** Map each concept or subscale to
   `library/constructs.json` where one fits (`construct_match`: exact, close,
   or related). Add a construct only when none fits.
3. **Respect licenses.** Never add item text without written permission or a
   documented license (`access.item_text_basis`). When a developer offers item
   text, confirm the license with them before adding items.
4. **Add it to the library** in the same pull request, or in a follow-up
   pull request that references this one. Then run
   `python scripts/validate_library.py`.
5. **Merge or close.** Merging the suggestion file keeps a public record of
   who recommended what. If you close a recommendation, say why.

Recommendations are public on GitHub from the moment they are submitted.
Contributors are told this before they submit.
