# Recommendations from the community

Researchers recommend theories, conceptual models and frameworks, instruments,
and corrections from **Module 2 (Framework and Measures)** in the HuMeta
Portal, using its **Recommend** tabs. Researchers who use GitHub can also use
the issue forms. Each recommendation arrives as a pull request that adds one
JSON file:

| Folder | What it holds | Where accepted content goes |
|---|---|---|
| `frameworks/` | Theories, lenses, conceptual models: name, kind, description, constructs (each with an optional shared construct and instruments that measure it), expected relationships, citation | `library/frameworks.json` |
| `instruments/` | Instruments: name, citation, an **alignment table** mapping the whole instrument or each subscale (with its items) to the construct it measures, access and license, evidence, the submitter's relationship to it | `library/instruments/<id>.json` |
| `corrections/` | Changes to an existing framework, instrument, or construct | the file being corrected |

Older free-text suggestions sit directly in this folder.

## Reviewing a recommendation

The pull request lists a checklist. In short:

1. **Check the source.** Confirm the citation and DOI, and that the
   constructs, relationships, subscales, and items match the publication.
2. **Decide the mappings.** Which instruments (and subscales) map to which
   constructs, and which theory constructs link to shared constructs, is
   decided by the **HuMeta governance committee**, not by one person. The
   recommendation's alignment table is a proposal. Record each decision in
   the instrument's `construct_mapping` (`status`, `decided_on`,
   `decided_by`). Until the committee is formed, mappings stay
   `provisional`. Add a shared construct only when none fits.
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
