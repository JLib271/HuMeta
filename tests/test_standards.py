"""The credited standards stay in step with the profile."""
from oem import profile as P
from oem import standards


def test_every_profile_standard_is_credited_with_its_use():
    p = P.load()
    keys = {k for k in p.definition["standards"] if k != "humeta"}
    assert keys <= set(standards.PROFILE_USES), keys - set(standards.PROFILE_USES)
    assert {e["key"] for e in standards.entries(p) if e["key"]} == keys


def test_every_entry_has_a_group_link_and_use():
    for e in standards.entries():
        assert e["group"] in standards.GROUPS and e["url"].startswith("http") and e["use"]
    md = standards.markdown()
    assert "**Compared with**" in md and "NEON" in md and "DataCite Metadata Schema 4.7" in md
