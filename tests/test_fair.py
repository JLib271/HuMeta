from oem import fair

EXPECTED = ["F1", "F2", "F3", "F4", "A1", "A1.1", "A1.2", "A2", "I1", "I2", "I3", "R1", "R1.1", "R1.2", "R1.3"]


def test_every_fair_principle_is_covered_once():
    assert [p[0] for p in fair.PRINCIPLES] == EXPECTED
    assert all(p[3] in fair.STATUSES and p[1] and p[2] for p in fair.PRINCIPLES)


def test_partly_met_rows_say_what_is_missing():
    for pid, _, how, status in fair.PRINCIPLES:
        if status == "Partly":
            assert any(w in how for w in ("not yet", "still", "awaiting")), pid


def test_table_renders_every_row():
    table = fair.markdown_table()
    assert table.count("\n") == len(EXPECTED) + 1 and "| **R1.3** |" in table and "◐ Partly" in table
