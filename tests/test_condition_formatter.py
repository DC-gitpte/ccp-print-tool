from src.models import Condition
from src.formatter.condition_formatter import format_conditions, format_conditions_section


def test_simple_condition():
    cond = Condition(agency_code="CA", condition_code="A59", description="SHORT MESSAGE.")
    lines = format_conditions([cond])
    assert len(lines) == 1
    assert "A59" in lines[0]
    assert "SHORT MESSAGE." in lines[0]
    assert len(lines[0]) == 80


def test_word_wrap():
    long_text = "WORD " * 20  # 100 chars, exceeds 73 first line
    cond = Condition(agency_code="SC", condition_code="Z10", description=long_text.strip())
    lines = format_conditions([cond])
    assert len(lines) >= 2
    assert "Z10" in lines[0]
    assert "WORD" in lines[0]
    for line in lines:
        assert len(line) == 80


def test_overflow_512_chars():
    text = "A" * 600
    cond = Condition(agency_code="CA", condition_code="TST", description=text)
    lines = format_conditions([cond])
    found_continuation = any("----" in line for line in lines)
    assert found_continuation


def test_conditions_section_structure():
    ca = [Condition(agency_code="CA", condition_code="A01", description="CA condition.")]
    sc = [Condition(agency_code="SC", condition_code="EEE", description="END OF CARGO CLEARANCE PERMIT.")]
    lines = format_conditions_section(ca, sc)
    assert "CONTROLLING AGENCY/CUSTOMS CONDITIONS" in lines[1]
    full_text = "\n".join(lines)
    assert "A01" in full_text
    assert "EEE" in full_text


def test_empty_conditions():
    lines = format_conditions([])
    assert lines == []
