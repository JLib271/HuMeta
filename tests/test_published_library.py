# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""The portal reads the library the HuMeta Library website publishes, and falls back safely."""
from __future__ import annotations

import gzip
import hashlib
import importlib.util
import io
import json
import tarfile
from pathlib import Path

import pytest

from oem import library as L

ROOT = Path(__file__).resolve().parent.parent


def _script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _archive(change=None) -> tuple[bytes, dict]:
    """A library.tar.gz and library.json like the website's, from the snapshot (optionally changed)."""
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w") as tar:
        for path in sorted(p for p in L.DEFAULT_LIBRARY_DIR.rglob("*") if p.is_file()):
            rel = path.relative_to(L.DEFAULT_LIBRARY_DIR).as_posix()
            if rel == "library.json":
                continue
            content = path.read_bytes()
            if change and rel in change:
                content = change[rel](content)
            info = tarfile.TarInfo("library/" + rel)
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
    packed = gzip.compress(raw.getvalue(), mtime=0)
    manifest = {"format": "humeta-library-archive", "archive": "library.tar.gz",
                "sha256": hashlib.sha256(packed).hexdigest(), "built": "2026-11-13", "counts": {}}
    return packed, manifest


def _rename_gci(content: bytes) -> bytes:
    record = json.loads(content)
    record["name"] = "Renamed upstream"
    return json.dumps(record).encode()


@pytest.fixture
def website(monkeypatch):
    """Serve an archive as the website would; returns a dict to change what it serves."""
    packed, manifest = _archive({"instruments/gci.json": _rename_gci})
    served = {"library.json": json.dumps(manifest).encode(), "library.tar.gz": packed, "fail": False, "calls": 0}

    def fetch(url, timeout):
        served["calls"] += 1
        if served["fail"]:
            raise OSError("offline")
        return served[url.rsplit("/", 1)[1]]

    monkeypatch.setattr(L, "_fetch", fetch)
    yield served
    L.use_snapshot()


def test_load_reads_the_snapshot_by_default():
    L.use_snapshot()
    assert L.default_root() == L.DEFAULT_LIBRARY_DIR
    assert L.Library.load().instrument("gci")["name"] != "Renamed upstream"


def test_use_published_switches_library_load(website, tmp_path):
    root = L.use_published(cache_dir=tmp_path)
    assert root != L.DEFAULT_LIBRARY_DIR
    assert L.Library.load().instrument("gci")["name"] == "Renamed upstream"


def test_cached_copy_is_reused(website, tmp_path):
    L.use_published(cache_dir=tmp_path)
    calls = website["calls"]
    L.use_published(cache_dir=tmp_path)
    assert website["calls"] == calls + 1  # only library.json the second time


def test_offline_keeps_the_snapshot(website, tmp_path):
    website["fail"] = True
    assert L.use_published(cache_dir=tmp_path) == L.DEFAULT_LIBRARY_DIR


def test_offline_keeps_the_last_good_copy(website, tmp_path):
    good = L.use_published(cache_dir=tmp_path)
    website["fail"] = True
    assert L.use_published(cache_dir=tmp_path) == good


def test_corrupt_download_is_rejected(website, tmp_path):
    website["library.tar.gz"] = b"not an archive"
    assert L.use_published(cache_dir=tmp_path) == L.DEFAULT_LIBRARY_DIR


def test_archive_outside_library_folder_is_rejected(tmp_path):
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w") as tar:
        info = tarfile.TarInfo("elsewhere/constructs.json")
        info.size = 2
        tar.addfile(info, io.BytesIO(b"{}"))
    with pytest.raises(ValueError):
        L.unpack_archive(gzip.compress(raw.getvalue()), tmp_path)


def test_update_library_from_a_built_site(tmp_path, monkeypatch):
    update = _script("update_library")
    target = tmp_path / "library"
    monkeypatch.setattr(update, "TARGET", target)
    packed, manifest = _archive({"instruments/gci.json": _rename_gci})
    site = tmp_path / "data"
    site.mkdir()
    (site / "library.tar.gz").write_bytes(packed)
    (site / "library.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert update.main(["--from", str(site), "--check"]) == 1
    assert update.main(["--from", str(site)]) == 0
    assert L.Library.load(target).instrument("gci")["name"] == "Renamed upstream"
    assert json.loads((target / "library.json").read_text())["sha256"] == manifest["sha256"]
    assert update.main(["--from", str(site), "--check"]) == 0


def test_snapshot_records_which_archive_it_is():
    manifest = json.loads((L.DEFAULT_LIBRARY_DIR / "library.json").read_text(encoding="utf-8"))
    assert manifest["format"] == "humeta-library-archive" and len(manifest["sha256"]) == 64


def test_old_website_address_forwards_every_page(tmp_path):
    redirects = _script("build_library_redirects")
    count = redirects.build(tmp_path)
    lib = L.Library.load(L.DEFAULT_LIBRARY_DIR)
    assert count == 5 + len(lib.instruments) + len(lib.frameworks) + len(lib.constructs)
    page = (tmp_path / "instruments" / "gci" / "index.html").read_text(encoding="utf-8")
    assert 'href="https://jlib271.github.io/humeta-library/instruments/gci/"' in page
    assert "jlib271.github.io/humeta-library/" in (tmp_path / "404.html").read_text(encoding="utf-8")


def test_policy_pages_are_published(tmp_path):
    redirects = _script("build_library_redirects")
    redirects.build(tmp_path)
    privacy = (tmp_path / "privacy" / "index.html").read_text(encoding="utf-8")
    terms = (tmp_path / "terms" / "index.html").read_text(encoding="utf-8")
    assert "<h1>HuMeta Portal privacy policy</h1>" in privacy and "<table>" in privacy
    assert "<h1>HuMeta Portal terms of service</h1>" in terms
