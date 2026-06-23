"""
PDF Renderer — converts formatted CCP text pages into a monospace PDF.

Per TDS41-MDS-CCP-M spec:
- Courier font at 12 CPI (10pt)
- Code 39 barcode, 1.5"-3.1" length, 0.45"-0.55" height, 3:1 wide-to-narrow
- Permit number printed in Bold below barcode
- Condition codes printed in Bold
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
    BARCODE_TYPE,
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

import re

CONDITION_CODE_PATTERN = re.compile(r"^[A-Z0-9-]{1,4}\s{0,3} - ")


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

            if _should_bold_line(safe_line, permit_number):
                pdf.set_font(FONT_NAME, style="B", size=FONT_SIZE_PT)
                pdf.cell(w=USABLE_WIDTH_MM, h=LINE_HEIGHT_MM, text=safe_line)
                pdf.set_font(FONT_NAME, size=FONT_SIZE_PT)
            else:
                pdf.cell(w=USABLE_WIDTH_MM, h=LINE_HEIGHT_MM, text=safe_line)

            y += LINE_HEIGHT_MM

    buffer = BytesIO()
    pdf.output(buffer)

    if barcode_path:
        Path(barcode_path).unlink(missing_ok=True)

    return buffer.getvalue()


def _should_bold_line(line: str, permit_number: str) -> bool:
    """Determine if a line should be rendered in bold per spec."""
    stripped = line.strip()
    if permit_number and f"PERMIT NO" in line and permit_number in line:
        return True
    if CONDITION_CODE_PATTERN.match(stripped):
        return True
    return False


def _generate_barcode_image(permit_number: str) -> str:
    """Generate a Code 39 barcode PNG for the permit number."""
    code39 = barcode.get_barcode_class(BARCODE_TYPE)

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

    barcode_instance = code39(permit_number, writer=writer, add_checksum=False)

    tmp = tempfile.NamedTemporaryFile(suffix="", prefix="ccp_barcode_", delete=False)
    tmp.close()
    return barcode_instance.save(tmp.name)
