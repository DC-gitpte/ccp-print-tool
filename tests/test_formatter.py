from src.parser import parse_tradenet_response
from src.formatter import format_ccp, format_ccp_text


def test_format_produces_pages(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    pages = format_ccp(permit)
    assert len(pages) == 3  # header + 1 consignment + final


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


def test_consignment_page_has_item(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    pages = format_ccp(permit)
    consignment_text = "\n".join(pages[1])
    assert "85243290" in consignment_text
    assert "ELECTRONIC COMPONENTS" in consignment_text


def test_final_page_has_declarant(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    pages = format_ccp(permit)
    final_text = "\n".join(pages[-1])
    assert "JOHN TAN WEI MING" in final_text
    assert "2666666Z" in final_text


def test_final_page_has_conditions(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    pages = format_ccp(permit)
    final_text = "\n".join(pages[-1])
    assert "A59" in final_text
    assert "Z10" in final_text
    assert "END OF CARGO CLEARANCE PERMIT" in final_text


def test_text_output_uses_form_feed(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    text = format_ccp_text(permit)
    assert "\f" in text
    assert text.count("\f") == 2  # 3 pages = 2 separators


def test_page_numbering(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    pages = format_ccp(permit)
    assert "PG :  1 OF  3" in pages[0][10]
    assert "PG :  2 OF  3" in pages[1][0]
    assert "PG :  3 OF  3" in pages[2][0]
