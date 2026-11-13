#!/usr/bin/env python3
# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Forward the HuMeta Library website's old address to its new one.

The website moved from https://jlib271.github.io/HuMeta/ to
https://jlib271.github.io/humeta-library/ when the library got its own
repository. Knowledge Commons deposits, papers, and DataCite records link to
the old pages, so this builds a small site for the old address: one forwarding
page for every record page and the site's other pages (with a canonical link
for search engines), and a 404 page that forwards any other path, such as a
download, to the same path at the new address.

    python scripts/build_library_redirects.py --out _site
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
    return len(pages)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, default=ROOT / "_site")
    args = ap.parse_args(argv)
    print(f"Wrote {build(args.out)} forwarding pages to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
