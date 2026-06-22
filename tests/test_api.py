import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from src.main import app

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_xml_bytes():
    return (FIXTURES_DIR / "sample_permit.xml").read_bytes()


@pytest.mark.anyio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


@pytest.mark.anyio
async def test_generate_pdf(sample_xml_bytes):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/ccp/generate",
            content=sample_xml_bytes,
            headers={"Content-Type": "application/xml"},
        )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"


@pytest.mark.anyio
async def test_generate_text(sample_xml_bytes):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/ccp/generate-text",
            content=sample_xml_bytes,
            headers={"Content-Type": "application/xml"},
        )
    assert r.status_code == 200
    assert "text/plain" in r.headers["content-type"]
    assert "CARGO CLEARANCE PERMIT" in r.text


@pytest.mark.anyio
async def test_generate_empty_body():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/ccp/generate",
            content=b"",
            headers={"Content-Type": "application/xml"},
        )
    assert r.status_code == 400


@pytest.mark.anyio
async def test_generate_invalid_xml():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/ccp/generate",
            content=b"<not valid xml",
            headers={"Content-Type": "application/xml"},
        )
    assert r.status_code == 400
