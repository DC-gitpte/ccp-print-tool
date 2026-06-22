from src.parser import parse_tradenet_response


def test_parse_permit_number(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    assert permit.permit_number == "IM6I011522Y"


def test_parse_message_type(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    assert permit.message_type == "INPPMT"


def test_parse_declaration_type(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    assert permit.declaration_type == "GTR"


def test_parse_urn(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    assert permit.urn.entity_id == "TESTUEN01E01T"
    assert permit.urn.date == "20260114"
    assert permit.urn.sequence == "0002"


def test_parse_validity_period(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    assert permit.validity_period.start_date == "20260114"
    assert permit.validity_period.end_date == "20260213"


def test_parse_importer(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    assert permit.importer.name == "SAMPLE LOGISTICS PTE LTD"
    assert permit.importer.entity_id == "TESTUEN01E01T"


def test_parse_declarant(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    assert permit.declarant.code == "2666666Z"
    assert permit.declarant.name == "JOHN TAN WEI MING"
    assert permit.declarant.telephone == "63111111"


def test_parse_transport(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    assert permit.transport.inward.conveyance_reference == "NW909"
    assert permit.transport.inward.mawb_oucr_obl == "01281069903"
    assert permit.transport.arrival_date == "20260114"
    assert permit.transport.loading_port == "USCVG"


def test_parse_items(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    assert len(permit.items) == 1
    item = permit.items[0]
    assert item.sequence_number == 1
    assert item.hs_code == "85243290"
    assert item.goods_description == "ELECTRONIC COMPONENTS - CIRCUIT BOARDS"
    assert item.origin_country == "US"
    assert item.brand_name == "UNBRANDED"
    assert item.model == "PCB-2026A"
    assert item.hs_quantity == "100.0000"
    assert item.hs_quantity_unit == "NMB"
    assert item.cif_fob_value == "1154.00"
    assert item.gst_amount == "103.86"


def test_parse_casc_products(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    item = permit.items[0]
    assert len(item.casc_products) == 1
    assert item.casc_products[0].code == "CUPAUDEXE"
    assert item.casc_products[0].quantity == "100.0000"
    assert item.casc_products[0].unit == "NMB"


def test_parse_conditions(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    assert len(permit.ca_conditions) == 1
    assert permit.ca_conditions[0].condition_code == "A59"
    assert "CUP" in permit.ca_conditions[0].description

    assert len(permit.sc_conditions) == 4
    assert permit.sc_conditions[0].condition_code == "Z10"
    assert permit.sc_conditions[-1].condition_code == "EEE"


def test_parse_summary(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    assert permit.summary.total_cif_fob_value == "1154.00"
    assert permit.summary.total_gst_amount == "103.86"
    assert permit.summary.total_amount_payable == "0.00"
    assert permit.cargo.total_outer_pack == "5"
    assert permit.cargo.total_outer_pack_unit == "CTN"
    assert permit.cargo.total_gross_weight == "25.500"
    assert permit.cargo.total_gross_weight_unit == "KGM"


def test_parse_invalid_xml():
    import pytest
    with pytest.raises(Exception):
        parse_tradenet_response(b"<invalid>not xml</")


def test_parse_empty_xml():
    import pytest
    with pytest.raises(Exception):
        parse_tradenet_response(b"")
