# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""The Library website builds, links work, and item text follows the access rules."""

from __future__ import annotations

import csv
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import unquote

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_library_site as B  # noqa: E402
from oem.library import Library  # noqa: E402
from oem.vocab import library_page_url  # noqa: E402


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    out = tmp_path_factory.mktemp("site") / "_site"
    B.main(["--out", str(out)])
    return out


def test_every_record_has_a_page(site):
    lib = Library.load()
    for iid in lib.instruments:
        assert (site / "instruments" / B.slug(iid) / "index.html").is_file()
    for fid, fw in lib.frameworks.items():
        if fw.get("kind") in ("theory", "lens"):
            assert (site / "frameworks" / B.slug(fid) / "index.html").is_file()
    for cid in lib.constructs:
        assert (site / "constructs" / B.slug(cid) / "index.html").is_file()
    for page in ("index.html", "reference/index.html", "about/index.html", "404.html", "sitemap.xml"):
        assert (site / page).is_file()


def test_page_urls_match_the_app(site):
    lib = Library.load()
    iid = next(iter(lib.instruments))
    assert library_page_url("instruments", iid).endswith(B.Site.url("instruments", iid))


def test_internal_links_resolve(site):
    bad = []
    for page in site.rglob("*.html"):
        if page.name == "404.html":
            continue
        for url in re.findall(r'(?:href|src)="([^"]+)"', page.read_text(encoding="utf-8")):
            if url.startswith(("http", "mailto:", "#")):
                continue
            target = (page.parent / unquote(url.split("#")[0].split("?")[0])).resolve()
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                bad.append((str(page.relative_to(site)), url))
    assert not bad, bad[:5]


def test_downloads(site):
    lib = Library.load()
    with (site / "data" / "instruments.csv").open(encoding="utf-8") as f:
        assert len(list(csv.DictReader(f))) == len(lib.instruments)
    with (site / "data" / "evidence.csv").open(encoding="utf-8") as f:
        assert len(list(csv.DictReader(f))) == len(lib.evidence)
    for iid in lib.instruments:
        assert json.loads((site / "data" / "instruments" / f"{iid}.json").read_text(encoding="utf-8"))["id"] == iid
    index = json.loads(re.search(r'<script type="application/json" id="index">(.*?)</script>',
                                 (site / "index.html").read_text(encoding="utf-8"), re.S).group(1))
    assert {r["type"] for r in index} == {"instrument", "theory", "construct"}


def _fake_library(tmp_path, shareable: bool) -> Path:
    """A copy of the library with one instrument whose item text sharing is switched on or off."""
    root = tmp_path / "library"
    shutil.copytree(ROOT / "library", root)
    path = root / "instruments" / "gci.json"
    rec = json.loads(path.read_text(encoding="utf-8"))
    rec["access"]["item_text_shareable"] = shareable
    path.write_text(json.dumps(rec), encoding="utf-8")
    return root


@pytest.mark.parametrize("shareable", [True, False])
def test_item_text_and_images_follow_access(tmp_path, shareable):
    out = tmp_path / "_site"
    B.main(["--out", str(out), "--library", str(_fake_library(tmp_path, shareable))])
    html = (out / "instruments" / "gci" / "index.html").read_text(encoding="utf-8")
    stem = json.loads((ROOT / "library" / "items" / "gci" / "gci-v4-2014.json").read_text(encoding="utf-8"))["items"][0]["stem"]
    figures = list((out / "instruments" / "gci" / "figures").glob("*.png")) if (out / "instruments" / "gci" / "figures").exists() else []
    if shareable:
        assert B.h(stem) in html and figures
    else:
        assert B.h(stem) not in html and not figures
        assert "Item text is not republished here" in html


def test_answer_keys_never_shown_without_permission(site):
    lib = Library.load()
    for iid, inst in lib.instruments.items():
        if not inst.get("access", {}).get("answer_key_shareable"):
            html = (site / "instruments" / B.slug(iid) / "index.html").read_text(encoding="utf-8")
            assert ">correct</span>" not in html


def test_instrument_filters(site):
    html = (site / "index.html").read_text(encoding="utf-8")
    for facet in ("itype", "resp", "level", "disc"):
        assert f'data-facet="{facet}"' in html
    index = json.loads(re.search(r'id="index">(.*?)</script>', html, re.S).group(1))
    assert all("facets" in r for r in index if r["type"] == "instrument")


def test_compare_page_and_profiles(site):
    html = (site / "compare" / "index.html").read_text(encoding="utf-8")
    lib = Library.load()
    assert html.count("<tr data-") == len(lib.instruments)
    page = (site / "instruments" / "mslq" / "index.html").read_text(encoding="utf-8")
    assert 'id="profile"' in page and "15 values, 0.52 to 0.93; guide &gt; 0.7" in page
    assert (site / "data" / "evidence_profiles.csv").is_file()
    assert 'id="rubric"' in (site / "about" / "index.html").read_text(encoding="utf-8")
