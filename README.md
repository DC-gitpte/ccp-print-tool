# CCP Print Tool

Generates Cargo Clearance Permit (CCP) PDF documents from TradenetResponse XML messages, compliant with the Singapore TradeNet 4.1 specification (GTNFE 5).

## Features

- Upload XML, get a formatted CCP PDF with Code 128 barcode
- Progress bar showing generation status
- Web service (FastAPI) deployable via Docker/GitLab CI
- Standalone HTML version (no server required — runs entirely in browser)
- CLI mode for scripting

## Quick Start

### Web Service (Docker)

```bash
docker-compose up
# Open http://localhost:8000
```

### Web Service (Local Python)

```bash
pip install -e .
uvicorn src.main:app --host 0.0.0.0 --port 8000
# Open http://localhost:8000
```

### CLI

```bash
pip install -e .
ccp-print generate input.xml output.pdf
```

### Standalone HTML

Open `standalone/ccp-printer.html` in any browser. No installation needed — just an internet connection for CDN libraries (jsPDF, JsBarcode).

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Web UI |
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/ccp/generate` | Upload XML, get PDF |
| POST | `/api/v1/ccp/generate-text` | Upload XML, get plain text (debug) |

## Development

```bash
pip install -e ".[dev]"
pytest tests/
```

## Deployment (GitLab)

The `.gitlab-ci.yml` pipeline includes:
- **lint** — ruff check + format
- **test** — pytest with coverage
- **build** — Docker image pushed to registry
- **deploy** — staging (auto on main), production (manual on tags)

## CCP Format

- A4 page, 10mm margins, Courier 9.5pt monospace
- Fixed 80-column width per line
- Code 128 barcode (permit number) at top-right of first page
- Page 1: Header with parties, transport, financial totals
- Pages 2+: Consignment items (max 3 per page)
- Final page: Declarant block + conditions section

## Tech Stack

- Python 3.11+, FastAPI, lxml, fpdf2, python-barcode
- Standalone: jsPDF, JsBarcode (CDN)
