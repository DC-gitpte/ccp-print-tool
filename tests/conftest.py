from pathlib import Path
import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_xml():
    return (FIXTURES_DIR / "sample_permit.xml").read_bytes()
