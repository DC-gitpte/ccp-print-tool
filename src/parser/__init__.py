from .xml_parser import parse_tradenet_response
from .json_parser import parse_json_permit


def parse_permit_file(data: bytes, filename: str = "") -> "PermitData":
    """Auto-detect format (JSON or XML) and parse accordingly."""
    stripped = data.lstrip()
    if filename.lower().endswith(".json") or stripped.startswith(b"{"):
        return parse_json_permit(data)
    return parse_tradenet_response(data)


__all__ = ["parse_tradenet_response", "parse_json_permit", "parse_permit_file"]
