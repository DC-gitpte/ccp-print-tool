"""
Condition formatter for CCP printing.

Rules from TN4.1 FE Vendor Guide:
- First line: [Code 4 chars][" - "][Text 73 chars max]
- Subsequent lines: [Text 80 chars max]
- Max 512 chars per occurrence; overflow splits with "----" continuation code
- Word wrap at whole-word boundaries
"""

from src.models import Condition

LINE_WIDTH = 80
CODE_WIDTH = 4
SEPARATOR = " - "
SEPARATOR_WIDTH = 3
FIRST_LINE_TEXT_WIDTH = LINE_WIDTH - CODE_WIDTH - SEPARATOR_WIDTH  # 73
SUBSEQUENT_LINE_TEXT_WIDTH = LINE_WIDTH
MAX_CHARS_PER_OCCURRENCE = 512


def format_conditions(conditions: list[Condition]) -> list[str]:
    """Format a list of conditions into fixed-width 80-column lines."""
    lines: list[str] = []
    for condition in conditions:
        lines.extend(_format_single_condition(condition))
    return lines


def format_conditions_section(
    ca_conditions: list[Condition], sc_conditions: list[Condition]
) -> list[str]:
    """Format the full conditions section (CA first, then SC)."""
    lines: list[str] = []
    lines.append("-" * LINE_WIDTH)
    lines.append("CONTROLLING AGENCY/CUSTOMS CONDITIONS")

    for condition in ca_conditions:
        lines.extend(_format_single_condition(condition))

    for condition in sc_conditions:
        lines.extend(_format_single_condition(condition))

    return lines


def _format_single_condition(condition: Condition) -> list[str]:
    """Format a single condition which may span multiple occurrences."""
    code = condition.condition_code
    description = condition.description
    occurrences = _split_into_occurrences(description)
    lines: list[str] = []

    for i, occurrence_text in enumerate(occurrences):
        display_code = code if i == 0 else "----"
        lines.extend(_format_occurrence(display_code, occurrence_text))

    return lines


def _split_into_occurrences(description: str) -> list[str]:
    """Split description into chunks of max 512 characters."""
    if len(description) <= MAX_CHARS_PER_OCCURRENCE:
        return [description]

    chunks: list[str] = []
    remaining = description
    while remaining:
        if len(remaining) <= MAX_CHARS_PER_OCCURRENCE:
            chunks.append(remaining)
            break
        chunks.append(remaining[:MAX_CHARS_PER_OCCURRENCE])
        remaining = remaining[MAX_CHARS_PER_OCCURRENCE:]

    return chunks


def _format_occurrence(code: str, text: str) -> list[str]:
    """Format a single occurrence into 80-column lines."""
    lines: list[str] = []
    padded_code = code.ljust(CODE_WIDTH)
    prefix = padded_code + SEPARATOR

    text_lines = _wrap_text_to_lines(text)

    for i, text_line in enumerate(text_lines):
        if i == 0:
            line = prefix + text_line.ljust(FIRST_LINE_TEXT_WIDTH)
        else:
            line = text_line.ljust(SUBSEQUENT_LINE_TEXT_WIDTH)
        lines.append(line[:LINE_WIDTH])

    return lines


def _wrap_text_to_lines(text: str) -> list[str]:
    """Wrap text respecting CCP format rules."""
    if not text:
        return [""]

    if "......" in text or "\n" in text:
        return _wrap_preformatted(text)

    return _wrap_words(text)


def _wrap_preformatted(text: str) -> list[str]:
    """Handle specially formatted text by splitting at fixed positions."""
    lines: list[str] = []
    pos = 0
    line_num = 0

    while pos < len(text):
        width = FIRST_LINE_TEXT_WIDTH if line_num == 0 else SUBSEQUENT_LINE_TEXT_WIDTH
        lines.append(text[pos : pos + width])
        pos += width
        line_num += 1

    return lines


def _wrap_words(text: str) -> list[str]:
    """Wrap text at word boundaries."""
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current_line = ""
    line_num = 0

    for word in words:
        max_width = FIRST_LINE_TEXT_WIDTH if line_num == 0 else SUBSEQUENT_LINE_TEXT_WIDTH

        if not current_line:
            current_line = word
        elif len(current_line) + 1 + len(word) <= max_width:
            current_line += " " + word
        else:
            lines.append(current_line)
            line_num += 1
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines
