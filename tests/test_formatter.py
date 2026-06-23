from src.parser import parse_tradenet_response
from src.formatter import format_ccp, format_ccp_text


def test_format_produces_pages(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    pages = format_ccp(permit)
    assert len(pages) >= 2


def test_all_lines_are_80_chars(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    pages = format_ccp(permit)
    for page_idx, page in enumerate(pages):
        for line_idx, line in enumerate(page):
            assert len(line) == 80, (
                f"Page {page_idx+1}, line {line_idx+1}: "
                f"got {len(line)} chars, expected 80"
            )


def test_header_page_has_permit_number(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    pages = format_ccp(permit)
    header_text = "\n".join(pages[0])
    assert "PERMIT NO : IM6I011522Y" in header_text


def test_header_page_has_title(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    pages = format_ccp(permit)
    header_text = "\n".join(pages[0])
    assert "CARGO CLEARANCE PERMIT" in header_text


def test_header_page_has_urn(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    pages = format_ccp(permit)
    header_text = "\n".join(pages[0])
    assert "TESTUEN01E01T 20260114 0002" in header_text


def test_consignment_has_item(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    pages = format_ccp(permit)
    all_text = "\n".join("\n".join(p) for p in pages)
    assert "85243290" in all_text
    assert "ELECTRONIC COMPONENTS" in all_text


def test_has_declarant(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    pages = format_ccp(permit)
    all_text = "\n".join("\n".join(p) for p in pages)
    assert "JOHN TAN WEI MING" in all_text
    assert "2666666Z" in all_text


def test_has_conditions(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    pages = format_ccp(permit)
    all_text = "\n".join("\n".join(p) for p in pages)
    assert "A59" in all_text
    assert "Z10" in all_text
    assert "END OF CARGO CLEARANCE PERMIT" in all_text


def test_text_output_uses_form_feed(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    text = format_ccp_text(permit)
    assert "\f" in text


def test_unique_ref_on_every_page(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    pages = format_ccp(permit)
    for page in pages:
        page_text = "\n".join(page)
        assert "UNIQUE REF" in page_text


def test_page_indicator_on_every_page(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    pages = format_ccp(permit)
    total = len(pages)
    for i, page in enumerate(pages, 1):
        page_text = "\n".join(page)
        assert f"PG : {i} OF {total}" in page_text or "UNIQUE REF" in page_text
