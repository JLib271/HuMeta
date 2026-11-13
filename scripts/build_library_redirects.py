#!/usr/bin/env python3
# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Build HuMeta's GitHub Pages site: the portal's policies, and forwarding for the old Library address.

The site is https://jlib271.github.io/HuMeta/. It holds:

* ``privacy/`` and ``terms/``: the HuMeta Portal's privacy policy and terms of
  service, from PRIVACY.md and TERMS.md (linked from the app and from its
  Google sign-in screen).
* Forwarding for the HuMeta Library website's old address, described below.

The website moved from https://jlib271.github.io/HuMeta/ to
https://jlib271.github.io/humeta-library/ when the library got its own
repository. Knowledge Commons deposits, papers, and DataCite records link to
the old pages, so this builds a small site for the old address: one forwarding
page for every record page and the site's other pages (with a canonical link
for search engines), and a 404 page that forwards any other path, such as a
download, to the same path at the new address.

    python scripts/build_library_redirects.py --out _site   (needs: pip install markdown)
"""
from __future__ import annotations

import argparse
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from oem.library import Library  # noqa: E402
from oem.vocab import LIBRARY_SITE_URL  # noqa: E402

OLD_PREFIX = "/HuMeta/"
STATIC_PAGES = ("", "compare/", "recommend/", "reference/", "about/")
#: The portal's policy pages: (folder, source file)
POLICY_PAGES = (("privacy", "PRIVACY.md"), ("terms", "TERMS.md"))


def policy_page(markdown_text: str) -> str:
    import markdown
    body = markdown.markdown(markdown_text, extensions=["tables"])
    title = escape(markdown_text.splitlines()[0].lstrip("# ").strip())
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  body {{ font-family: system-ui, -apple-system, "Segoe UI", sans-serif; line-height: 1.6; color: #1f2933;
         max-width: 46rem; margin: 2.5rem auto; padding: 0 1.25rem; }}
  h1 {{ font-size: 1.8rem; line-height: 1.25; }} h2 {{ margin-top: 2rem; font-size: 1.25rem; }}
  a {{ color: #1d4f91; }} table {{ border-collapse: collapse; width: 100%; font-size: 0.95rem; }}
  th, td {{ border: 1px solid #d5dbe1; padding: 0.45rem 0.6rem; text-align: left; vertical-align: top; }}
  th {{ background: #f2f5f8; }} footer {{ margin-top: 3rem; font-size: 0.9rem; color: #52606d; }}
</style>
</head>
<body>
<main>
{body}
</main>
<footer><a href="https://humeta.streamlit.app/">HuMeta Portal</a> ·
<a href="../privacy/">Privacy</a> · <a href="../terms/">Terms</a> ·
<a href="https://github.com/JLib271/HuMeta">Source</a></footer>
</body>
</html>
"""


def write_policies(out: Path) -> None:
    for folder, source in POLICY_PAGES:
        dest = out / folder / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(policy_page((ROOT / source).read_text(encoding="utf-8")), encoding="utf-8")


def page(target: str) -> str:
    t = escape(target, quote=True)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>The HuMeta Library has moved</title>
<link rel="canonical" href="{t}">
<meta http-equiv="refresh" content="0; url={t}">
<meta name="robots" content="noindex">
<script>location.replace({target!r} + location.search + location.hash);</script>
</head>
<body>
<p>The HuMeta Library has moved to <a href="{t}">{t}</a>.</p>
</body>
</html>
"""


def not_found_page() -> str:
    new = LIBRARY_SITE_URL
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>The HuMeta Library has moved</title>
<meta name="robots" content="noindex">
<script>
  var path = location.pathname;
  var rest = path.indexOf({OLD_PREFIX!r}) === 0 ? path.slice({len(OLD_PREFIX)}) : path.replace(/^\\//, "");
  location.replace({new!r} + rest + location.search + location.hash);
</script>
</head>
<body>
<p>The HuMeta Library has moved to <a href="{escape(new)}">{escape(new)}</a>.</p>
</body>
</html>
"""


def paths(lib: Library) -> list[str]:
    out = list(STATIC_PAGES)
    for kind, ids in (("instruments", lib.instruments), ("frameworks", lib.frameworks), ("constructs", lib.constructs)):
        out += [f"{kind}/{rid.replace('_', '-')}/" for rid in ids]
    return out


def build(out: Path, lib: Library | None = None) -> int:
    lib = lib or Library.load()
    out.mkdir(parents=True, exist_ok=True)
    (out / ".nojekyll").write_text("", encoding="utf-8")
    pages = paths(lib)
    for rel in pages:
        dest = out / rel / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(page(LIBRARY_SITE_URL + rel), encoding="utf-8")
    (out / "404.html").write_text(not_found_page(), encoding="utf-8")
    write_policies(out)
    return len(pages)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, default=ROOT / "_site")
    args = ap.parse_args(argv)
    print(f"Wrote the privacy and terms pages and {build(args.out)} forwarding pages to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
