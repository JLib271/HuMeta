"""DDI-Codebook 2.5 export, validated against the official DDI Alliance schema (DDI-Codebook 2.5.1,
LGPL-3.0, vendored in tests/schemas/ddi-codebook-2.5.1)."""

import json
from pathlib import Path

import pytest

from oem import ddi
from oem import plan as P
from oem.library import Library

etree = pytest.importorskip("lxml.etree")
ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "standard" / "humeta" / "examples"
NS = {"d": ddi.DDI_NS}


@pytest.fixture(scope="module")
def lib():
    return Library.load()


@pytest.fixture(scope="module")
def schema():
    return etree.XMLSchema(etree.parse(str(ROOT / "tests" / "schemas" / "ddi-codebook-2.5.1" / "codebook.xsd")))


@pytest.fixture(scope="module")
def plan(lib):
    plan = P.empty_plan()
    plan["frameworks"] = ["sdt"]
    plan["constructs"] = P.framework_constructs(lib, ["sdt"])
    plan["measures"] = [{"construct": "sdt.autonomy", "kind": "question", "text": f"Autonomy item {i}", "scale_id": "agree5"}
                        for i in (1, 2)] + [{"construct": "sdt.relatedness", "kind": "code", "label": "Mentions friends",
                                             "text": "Talks about peers."}]
    plan["standard_variables"] = ["participant_id"]
    plan["timepoints"] = ["pre", "post"]
    return P.normalize(plan, lib)


def parse(xml):
    return etree.fromstring(xml.encode("utf-8"))


@pytest.mark.parametrize("name", ["climate-inventory-dataset", "online-discourse-dataset", "archival-letters-collection"])
@pytest.mark.parametrize("with_plan", [False, True])
def test_export_is_valid_ddi_codebook(lib, schema, plan, name, with_plan):
    record = json.loads((EXAMPLES / f"{name}.json").read_text())
    doc = parse(ddi.to_ddi_codebook_xml(record, plan if with_plan else None, lib))
    assert schema.validate(doc), schema.error_log
    assert doc.findtext("d:stdyDscr/d:citation/d:titlStmt/d:titl", namespaces=NS) == record["resource"]["title"]


def test_social_science_fields_use_ddi_elements(lib):
    record = json.loads((EXAMPLES / "online-discourse-dataset.json").read_text())
    record["social_science"].update(ddi_record="https://example.org/ddi/123", response_rate="RR3 = 41%",
                                    geographic_unit="County")
    doc = parse(ddi.to_ddi_codebook_xml(record, None, lib))
    summary = "d:stdyDscr/d:stdyInfo/d:sumDscr/"
    assert doc.find(summary + "d:dataKind/d:concept", NS).text == "Mixed"
    assert doc.findtext(summary + "d:universe", namespaces=NS).startswith("Public English-language posts")
    assert doc.findtext(summary + "d:geogUnit", namespaces=NS) == "County"
    assert doc.findtext("d:stdyDscr/d:method/d:anlyInfo/d:respRate", namespaces=NS) == "RR3 = 41%"
    assert doc.findtext("d:stdyDscr/d:method/d:dataColl/d:weight", namespaces=NS).startswith("No weights")
    assert doc.find("d:stdyDscr/d:citation/d:holdings", NS).get("URI") == "https://example.org/ddi/123"
    sampling = doc.find("d:stdyDscr/d:method/d:dataColl/d:sampProc/d:concept", NS)
    assert sampling.text == "Nonprobability.Purposive" and sampling.get("vocab") == "DDI SamplingProcedure"


def test_variables_carry_codes_questions_and_constructs(lib, plan):
    record = json.loads((EXAMPLES / "climate-inventory-dataset.json").read_text())
    doc = parse(ddi.to_ddi_codebook_xml(record, plan, lib))
    names = [v.get("name") for v in doc.findall("d:dataDscr/d:var", NS)]
    assert names == [v.name for v in P.build_codebook(lib, plan).variables]
    item = doc.find("d:dataDscr/d:var[@name='autonomy_01_pre']", NS)
    assert item.findtext("d:qstn/d:qstnLit", namespaces=NS) == "Autonomy item 1"
    assert item.findtext("d:concept", namespaces=NS) == "Autonomy"
    assert [c.get("missing") for c in item.findall("d:catgry", NS)][-2:] == ["Y", "Y"]
    groups = doc.findall("d:dataDscr/d:varGrp", NS)
    assert len(groups) == 2  # one per construct and measure, across timepoints
    assert len(groups[0].get("var").split()) == 4
