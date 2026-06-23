from pathlib import Path
import pytest
from src.parser.json_parser import parse_json_permit
from src.parser import parse_permit_file
from src.formatter import format_ccp
from src.renderer import render_pdf

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_json():
    return (FIXTURES_DIR / "sample_outward.json").read_bytes()


def test_parse_permit_number(sample_json):
    permit = parse_json_permit(sample_json)
    assert permit.permit_number == "OD8X021912K"


def test_parse_message_type(sample_json):
    permit = parse_json_permit(sample_json)
    assert permit.message_type == "OUTPMT"


def test_parse_declaration_type(sample_json):
    permit = parse_json_permit(sample_json)
    assert permit.declaration_type == "DRT"


def test_parse_urn(sample_json):
    permit = parse_json_permit(sample_json)
    assert permit.urn.entity_id == "199780090E"
    assert permit.urn.date == "20260507"
    assert permit.urn.sequence == "1801"


def test_parse_validity_period(sample_json):
    permit = parse_json_permit(sample_json)
    assert permit.validity_period.start_date == "20260506"
    assert permit.validity_period.end_date == "20260607"


def test_parse_exporter(sample_json):
    permit = parse_json_permit(sample_json)
    assert permit.exporter.name == "UPTON ELECTRONICS PTE LTD"
    assert permit.exporter.entity_id == "201266621F"
    assert permit.exporter.address_line1 == "TANG AVENUE 5"


def test_parse_declarant(sample_json):
    permit = parse_json_permit(sample_json)
    assert permit.declarant.name == "TAN SEE POH"
    assert permit.declarant.code == "S7645819X"
    assert permit.declarant.telephone == "90117289"


def test_parse_declaring_agent(sample_json):
    permit = parse_json_permit(sample_json)
    assert permit.declaring_agent.name == "LEE SENG FREIGHTS AND SHIPPING"
    assert permit.declaring_agent.entity_id == "198921349G"


def test_parse_transport(sample_json):
    permit = parse_json_permit(sample_json)
    assert permit.transport.inward.conveyance_reference == "799880"
    assert permit.transport.inward.mawb_oucr_obl == "80100089992"
    assert permit.transport.arrival_date == "20260506"
    assert permit.transport.outward.transport_identifier == "PZ908123"
    assert permit.transport.outward.conveyance_reference == "1009019I3FAGRQO"
    assert permit.transport.departure_date == "20260510"
    assert permit.transport.discharge_port == "COZZZ"
    assert permit.transport.final_destination_country == "COLOMBIA"


def test_parse_containers(sample_json):
    permit = parse_json_permit(sample_json)
    assert len(permit.containers) == 2
    assert "29001" in permit.containers[0]
    assert "29002" in permit.containers[1]


def test_parse_items(sample_json):
    permit = parse_json_permit(sample_json)
    assert len(permit.items) == 1
    item = permit.items[0]
    assert item.sequence_number == 1
    assert item.hs_code == "63025910"
    assert item.goods_description == "TABLE LINEN NOT KNITTED OR CROCHETED OF FLAX"
    assert item.brand_name == "UNBRAND"
    assert item.cif_fob_value == "979000"
    assert item.gst_amount == "9000"
    assert item.hs_quantity == "200000"
    assert item.hs_quantity_unit == "KGM"


def test_parse_conditions(sample_json):
    permit = parse_json_permit(sample_json)
    assert len(permit.sc_conditions) == 1
    assert permit.sc_conditions[0].condition_code == "A01"
    assert "SINGAPORE CUSTOMS" in permit.sc_conditions[0].description


def test_parse_summary(sample_json):
    permit = parse_json_permit(sample_json)
    assert permit.summary.total_cif_fob_value == "979000"
    assert permit.summary.total_gst_amount == "9000"
    assert permit.summary.total_customs_duty == "20000"
    assert permit.summary.total_amount_payable == "9000"


def test_auto_detect_json(sample_json):
    permit = parse_permit_file(sample_json, "test.json")
    assert permit.permit_number == "OD8X021912K"


def test_auto_detect_json_by_content(sample_json):
    permit = parse_permit_file(sample_json, "")
    assert permit.permit_number == "OD8X021912K"


def test_full_pipeline_json_to_pdf(sample_json):
    permit = parse_json_permit(sample_json)
    pages = format_ccp(permit)
    assert len(pages) >= 2
    pdf_bytes = render_pdf(pages, permit_number=permit.permit_number)
    assert pdf_bytes[:4] == b"%PDF"


def test_all_lines_80_chars_json(sample_json):
    permit = parse_json_permit(sample_json)
    pages = format_ccp(permit)
    for page_idx, page in enumerate(pages):
        for line_idx, line in enumerate(page):
            assert len(line) == 80, f"Page {page_idx+1}, line {line_idx+1}: got {len(line)} chars"
