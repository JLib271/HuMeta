# STEMEd+ shared look

The look shared by the STEMEd+ sites on GitHub Pages (Jobs, Funding, Conferences, Digest,
Graduate Programs, and the HuMeta Library), matching https://stemedplus.org: a green band
with the white STEMEd+ Commons logo and a menu of the STEMEd+ sites, the Manrope typeface,
green accents, and rounded buttons.

| File | What it is |
|---|---|
| `stemedplus-theme.css` | Load after a site's own styles. Overrides colors, fonts, buttons, and the join box, and styles the green band. |
| `sp_bar.py` | `bar(current)` returns the green band's HTML, with the current site marked. |
| `stemedplus-commons-logo-white.png` | The logo in white, for the green band. |
| `manrope.woff` | Manrope (Latin subset), by the Manrope Project Authors, under the SIL Open Font License (`manrope-OFL.txt`). |

Each site keeps a copy of these files next to its `index.html`. When this folder changes, copy the
files into each site so they stay the same.
