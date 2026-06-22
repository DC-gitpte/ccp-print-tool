"""
CCP Print Tool — FastAPI application.

Generates Cargo Clearance Permit (CCP) PDFs from TradenetResponse XML.

Usage:
  Service: uvicorn src.main:app --host 0.0.0.0 --port 8000
  CLI:     ccp-print generate input.xml output.pdf
"""

import sys
import logging
from pathlib import Path

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from src.parser import parse_tradenet_response, parse_permit_file
from src.formatter import format_ccp, format_ccp_text
from src.renderer import render_pdf

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent.parent / "static"

app = FastAPI(
    title="CCP Print Tool",
    description="Generates Cargo Clearance Permit (CCP) PDFs from TradenetResponse XML",
    version="1.0.0",
)


@app.get("/")
async def serve_ui():
    """Serve the CCP generator UI."""
    return FileResponse(STATIC_DIR / "index.html")


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "service": "ccp-print-tool", "version": "1.0.0"}


@app.post(
    "/api/v1/ccp/generate",
    response_class=Response,
    responses={
        200: {"content": {"application/pdf": {}}},
        400: {"description": "Invalid XML"},
        422: {"description": "Missing required permit fields"},
    },
)
async def generate_ccp_pdf(request: Request):
    """Generate a CCP PDF from TradenetResponse XML or JSON."""
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="Request body is empty")

    content_type = request.headers.get("content-type", "")
    filename = ""
    if "json" in content_type:
        filename = "input.json"

    try:
        permit_data = parse_permit_file(body, filename)
    except Exception as e:
        logger.error("Parse error: %s", e)
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")

    if not permit_data.permit_number:
        raise HTTPException(status_code=422, detail="Missing required field: permit_number")

    pages = format_ccp(permit_data)
    pdf_bytes = render_pdf(pages, permit_number=permit_data.permit_number)

    filename = f"CCP_{permit_data.permit_number}.pdf"
    logger.info("Generated CCP PDF: %s (%d bytes)", filename, len(pdf_bytes))

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post(
    "/api/v1/ccp/generate-text",
    response_class=PlainTextResponse,
    responses={
        200: {"content": {"text/plain": {}}},
        400: {"description": "Invalid XML"},
        422: {"description": "Missing required permit fields"},
    },
)
async def generate_ccp_text(request: Request):
    """Generate CCP as plain text (debug mode)."""
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="Request body is empty")

    content_type = request.headers.get("content-type", "")
    filename = "input.json" if "json" in content_type else ""

    try:
        permit_data = parse_permit_file(body, filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")

    if not permit_data.permit_number:
        raise HTTPException(status_code=422, detail="Missing required field: permit_number")

    text = format_ccp_text(permit_data)
    return PlainTextResponse(content=text, media_type="text/plain; charset=utf-8")


def cli():
    """CLI entry point: ccp-print generate <input.xml> <output.pdf>"""
    if len(sys.argv) < 4 or sys.argv[1] != "generate":
        print("Usage: ccp-print generate <input.xml> <output.pdf>")
        sys.exit(1)

    input_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3])

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    file_bytes = input_path.read_bytes()
    permit_data = parse_permit_file(file_bytes, input_path.name)
    pages = format_ccp(permit_data)
    pdf_bytes = render_pdf(pages, permit_number=permit_data.permit_number)

    output_path.write_bytes(pdf_bytes)
    print(f"CCP generated: {output_path} ({len(pdf_bytes)} bytes)")


if __name__ == "__main__":
    cli()
