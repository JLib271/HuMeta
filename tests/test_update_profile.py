# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""scripts/update_profile.py keeps standard/humeta/ equal to a humeta-profile release."""
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("update_profile", ROOT / "scripts" / "update_profile.py")
update_profile = importlib.util.module_from_spec(spec)
spec.loader.exec_module(update_profile)


@pytest.fixture
def release(tmp_path, monkeypatch):
    """A fake release (the current copy plus a .github folder) and an empty target."""
    source = tmp_path / "humeta-profile-v9"
    shutil.copytree(ROOT / "standard" / "humeta", source)
    (source / ".github" / "workflows").mkdir(parents=True)
    (source / ".github" / "workflows" / "check.yml").write_text("name: Check\n")
    target = tmp_path / "standard" / "humeta"
    monkeypatch.setattr(update_profile, "TARGET", target)
    return source, target


def test_lock_names_a_tagged_release():
    lock = json.loads((ROOT / "humeta-profile.json").read_text())
    assert lock["repository"] == "JLib271/humeta-profile"
    assert lock["version"].startswith("v")


def test_copy_from_release_skips_github_and_then_matches(release):
    source, target = release
    assert update_profile.main(["--from", str(source), "--check"]) == 1
    assert update_profile.main(["--from", str(source)]) == 0
    assert (target / "profile.json").is_file()
    assert not (target / ".github").exists()
    assert update_profile.main(["--from", str(source), "--check"]) == 0


def test_check_reports_edits_and_extra_files(release):
    source, target = release
    update_profile.main(["--from", str(source)])
    (target / "README.md").write_text("edited by hand\n")
    (target / "stray.txt").write_text("x\n")
    diffs = update_profile.differences(source)
    assert "differs: README.md" in diffs
    assert "extra:   stray.txt" in diffs


def test_incomplete_release_leaves_copy_untouched(release):
    source, target = release
    update_profile.main(["--from", str(source)])
    before = (target / "profile.json").read_bytes()
    (source / "profile.json").unlink()
    assert update_profile.main(["--from", str(source)]) == 1
    assert (target / "profile.json").read_bytes() == before
