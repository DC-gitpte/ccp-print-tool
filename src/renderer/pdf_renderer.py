"""
PDF Renderer — converts formatted CCP text pages into a monospace PDF
with Code 128 barcode on the first page.
"""

import tempfile
from io import BytesIO
from pathlib import Path

import barcode
from barcode.writer import ImageWriter
from fpdf import FPDF

from src.config import (
    PAGE_WIDTH_MM,
    PAGE_HEIGHT_MM,
    MARGIN_LEFT_MM,
    MARGIN_RIGHT_MM,
    MARGIN_TOP_MM,
    MARGIN_BOTTOM_MM,
    USABLE_WIDTH_MM,
    FONT_NAME,
    FONT_SIZE_PT,
    LINE_HEIGHT_MM,
    BARCODE_WIDTH_MM,
    BARCODE_HEIGHT_MM,
    BARCODE_X_MM,
    BARCODE_Y_MM,
    BARCODE_MODULE_WIDTH,
    BARCODE_MODULE_HEIGHT,
    BARCODE_FONT_SIZE,
    BARCODE_TEXT_DISTANCE,
    BARCODE_QUIET_ZONE,
)


def render_pdf(pages: list[list[str]], permit_number: str = "") -> bytes:
    """
    Render CCP pages into a PDF document.

    Args:
        pages: List of pages, each page being a list of 80-char text lines.
        permit_number: Permit number to encode as barcode on first page.

    Returns:
        PDF file content as bytes.
    """
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.set_margins(MARGIN_LEFT_MM, MARGIN_TOP_MM, MARGIN_RIGHT_MM)

    barcode_path = None
    if permit_number:
        barcode_path = _generate_barcode_image(permit_number)

    for page_idx, page_lines in enumerate(pages):
        pdf.add_page()
        pdf.set_font(FONT_NAME, size=FONT_SIZE_PT)

        if page_idx == 0 and barcode_path:
            pdf.image(
                barcode_path,
                x=BARCODE_X_MM,
                y=BARCODE_Y_MM,
                w=BARCODE_WIDTH_MM,
                h=BARCODE_HEIGHT_MM,
            )

        y = MARGIN_TOP_MM
        for line in page_lines:
            if y + LINE_HEIGHT_MM > PAGE_HEIGHT_MM - MARGIN_BOTTOM_MM:
                pdf.add_page()
                pdf.set_font(FONT_NAME, size=FONT_SIZE_PT)
                y = MARGIN_TOP_MM

            pdf.set_xy(MARGIN_LEFT_MM, y)
            safe_line = line.encode("latin-1", errors="replace").decode("latin-1")
            pdf.cell(w=USABLE_WIDTH_MM, h=LINE_HEIGHT_MM, text=safe_line)
            y += LINE_HEIGHT_MM

    buffer = BytesIO()
    pdf.output(buffer)

    if barcode_path:
        Path(barcode_path).unlink(missing_ok=True)

    return buffer.getvalue()


def _generate_barcode_image(permit_number: str) -> str:
    """Generate a Code 128 barcode PNG for the permit number."""
    code128 = barcode.get_barcode_class("code128")

    writer = ImageWriter()
    writer.set_options(
        {
            "module_width": BARCODE_MODULE_WIDTH,
            "module_height": BARCODE_MODULE_HEIGHT,
            "font_size": BARCODE_FONT_SIZE,
            "text_distance": BARCODE_TEXT_DISTANCE,
            "quiet_zone": BARCODE_QUIET_ZONE,
        }
    )

    barcode_instance = code128(permit_number, writer=writer)

    tmp = tempfile.NamedTemporaryFile(suffix="", prefix="ccp_barcode_", delete=False)
    tmp.close()
    return barcode_instance.save(tmp.name)
