from src.parser import parse_tradenet_response
from src.formatter import format_ccp
from src.renderer import render_pdf


def test_render_produces_pdf(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    pages = format_ccp(permit)
    pdf_bytes = render_pdf(pages, permit_number=permit.permit_number)
    assert pdf_bytes[:4] == b"%PDF"
    assert len(pdf_bytes) > 1000


def test_render_without_barcode(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    pages = format_ccp(permit)
    pdf_bytes = render_pdf(pages, permit_number="")
    assert pdf_bytes[:4] == b"%PDF"


def test_render_multiple_pages(sample_xml):
    permit = parse_tradenet_response(sample_xml)
    pages = format_ccp(permit)
    assert len(pages) >= 2
    pdf_bytes = render_pdf(pages, permit_number=permit.permit_number)
    assert pdf_bytes[:4] == b"%PDF"
    assert len(pdf_bytes) > 5000
