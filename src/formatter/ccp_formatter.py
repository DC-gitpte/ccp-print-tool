"""
CCP Formatter — converts PermitData into fixed-width 80-column
Cargo Clearance Permit pages per the gold standard layout.

Page structure (per gold standard):
  Every page starts with: separator + UNIQUE REF (top)
  Every page ends with: separator + UNIQUE REF + PG indicator (bottom)
  Page 1: Barcode area, permit no, title, header fields
  Page 2+: Consignment details, then declarant + conditions (all continuous)
"""

from src.models import PermitData, ConsignmentItem
from src.config import LINE_WIDTH_CHARS, MAX_ITEMS_PER_PAGE
from .condition_formatter import format_conditions_section

LINE_WIDTH = LINE_WIDTH_CHARS
SEPARATOR_LINE = "-" * LINE_WIDTH
LINES_PER_PAGE = 62


def format_ccp(permit: PermitData) -> list[list[str]]:
    """
    Format a PermitData into CCP pages.
    Returns a list of pages, each page being a list of 80-char lines.
    """
    all_content_lines = []

    all_content_lines.extend(_format_header_content(permit))
    all_content_lines.extend(_format_consignment_content(permit))
    all_content_lines.extend(_format_final_content(permit))

    pages = _paginate(all_content_lines, permit)
    return pages


def format_ccp_text(permit: PermitData) -> str:
    """Format CCP as text with form-feed page separators."""
    pages = format_ccp(permit)
    return "\f".join("\n".join(page) for page in pages)


def _paginate(content_lines: list[str], permit: PermitData) -> list[list[str]]:
    """Split content into pages with headers and footers."""
    urn_str = f"{permit.urn.entity_id} {permit.urn.date} {permit.urn.sequence}"
    usable_lines = LINES_PER_PAGE - 4

    pages: list[list[str]] = []
    idx = 0

    while idx < len(content_lines):
        page_content = content_lines[idx : idx + usable_lines]
        idx += usable_lines
        pages.append(page_content)

    total_pages = len(pages)
    final_pages: list[list[str]] = []

    for page_num, page_content in enumerate(pages, 1):
        page_lines: list[str] = []
        page_lines.append(_line(SEPARATOR_LINE))
        page_lines.append(_line(f"UNIQUE REF : {urn_str}"))

        page_lines.extend(page_content)

        padding_needed = LINES_PER_PAGE - len(page_lines) - 2
        for _ in range(max(0, padding_needed)):
            page_lines.append(_line(""))

        page_lines.append(_line(SEPARATOR_LINE))
        page_indicator = f"PG : {page_num} OF {total_pages}"
        page_lines.append(_line(f"UNIQUE REF : {urn_str:<50s}{permit_number_space(permit)}{page_indicator}"))

        final_pages.append(page_lines)

    return final_pages


def permit_number_space(permit: PermitData) -> str:
    return ""


def _line(text: str) -> str:
    """Pad or truncate to exactly LINE_WIDTH chars."""
    return text[:LINE_WIDTH].ljust(LINE_WIDTH)


def _format_date(date_str: str) -> str:
    """Convert CCYYMMDD to DD/MM/CCYY."""
    if len(date_str) >= 8:
        return f"{date_str[6:8]}/{date_str[4:6]}/{date_str[0:4]}"
    return date_str


def _format_amount(amount_str: str) -> str:
    """Format amount as right-aligned S$ value."""
    if not amount_str:
        return "S$             0.00"
    try:
        val = float(amount_str)
        formatted = f"{val:.2f}"
        return f"S${formatted:>17s}"
    except (ValueError, TypeError):
        return f"S${amount_str:>17s}"


def _format_header_content(permit: PermitData) -> list[str]:
    """Format header page content (without page header/footer)."""
    lines: list[str] = []

    # Barcode area (blank lines for barcode space)
    lines.append(_line(""))
    lines.append(_line(""))
    lines.append(_line(""))

    # Permit number — right-aligned, bold
    lines.append(_line(f"{'':>56s}PERMIT NO : {permit.permit_number}"))

    # Blank lines
    lines.append(_line(""))
    lines.append(_line(""))

    # Title
    lines.append(_line(f"{'':>37s}CARGO CLEARANCE PERMIT"))
    lines.append(_line(""))

    # Message Type and Declaration Type
    msg_type_desc = _get_message_type_description(permit.message_type)
    dec_type_desc = _get_declaration_type_description(permit.declaration_type)
    lines.append(_line(f"MESSAGE TYPE      : {msg_type_desc}"))
    lines.append(_line(f"DECLARATION TYPE  : {dec_type_desc}"))
    lines.append(_line(""))

    # Importer + Validity Period
    validity_start = _format_date(permit.validity_period.start_date)
    validity_end = _format_date(permit.validity_period.end_date)

    lines.append(_line(f"IMPORTER:{'':<27s}VALIDITY PERIOD      : {validity_start} -"))
    lines.append(_line(f"{permit.importer.name[:35]:<36s}{'':<28s}{validity_end}"))
    lines.append(_line(f"{permit.importer.address_line1[:35]}"))

    # Entity ID + Total Gross Weight
    weight_str = f"{permit.cargo.total_gross_weight}/{permit.cargo.total_gross_weight_unit}"
    lines.append(_line(f"{permit.importer.entity_id[:17]:<36s}TOTAL GROSS WT/UNIT  :{weight_str:>17s}"))

    # Exporter + Totals
    pack_str = f"{permit.cargo.total_outer_pack}/{permit.cargo.total_outer_pack_unit}"
    lines.append(_line(f"EXPORTER:{'':<27s}TOTAL OUTER PACK/UNIT:{pack_str:>17s}"))
    lines.append(_line(f"{permit.exporter.name[:35]:<36s}TOT EXCISE DUT PAYABLE : {_format_amount(permit.summary.total_excise_duty)}"))
    lines.append(_line(f"{permit.exporter.address_line1[:35]:<36s}TOT CUSTOMS DUT PAYABLE: {_format_amount(permit.summary.total_customs_duty)}"))
    lines.append(_line(f"{permit.exporter.entity_id[:17]:<36s}TOT OTHER TAX PAYABLE  : {_format_amount(permit.summary.total_other_tax)}"))

    # Handling Agent + GST/Total
    lines.append(_line(f"HANDLING AGENT:{'':<22s}TOTAL GST AMOUNT     : {_format_amount(permit.summary.total_gst_amount)}"))
    lines.append(_line(f"{permit.handling_agent.name[:35]:<36s}TOTAL AMOUNT PAYABLE : {_format_amount(permit.summary.total_amount_payable)}"))
    lines.append(_line(f"{permit.handling_agent.address_line1[:35]:<36s}CARGO PACKING TYPE: {permit.cargo.packing_type_description[:23]}"))

    # Transport
    lines.append(_line(f"{permit.handling_agent.entity_id[:30]:<36s}IN TRANSPORT IDENTIFIER:"))
    lines.append(_line(f"{'':>36s}{permit.transport.inward.transport_identifier[:35]}"))

    conv_ref = permit.transport.inward.conveyance_reference[:17]
    lines.append(_line(f"PORT OF LOADING/NEXT PORT OF CALL:{'':<3s}CONVEYANCE REFERENCE NO: {conv_ref}"))
    lines.append(_line(f"{permit.transport.loading_port[:35]:<36s}OBL/MAWB NO:"))
    lines.append(_line(f"PORT OF DISCHARGE/FINAL PORT OF CALL: {permit.transport.inward.mawb_oucr_obl[:35]}"))

    arrival = _format_date(permit.transport.arrival_date)
    lines.append(_line(f"{permit.transport.discharge_port[:35]:<36s}ARRIVAL DATE         : {arrival}"))

    lines.append(_line(f"COUNTRY OF FINAL DESTINATION:{'':<8s}OU TRANSPORT IDENTIFIER:"))
    lines.append(_line(f"{permit.transport.final_destination_country[:35]:<36s}{permit.transport.outward.transport_identifier[:35]}"))

    out_conv = permit.transport.outward.conveyance_reference[:17]
    lines.append(_line(f"INWARD CARRIER AGENT:{'':<16s}CONVEYANCE REFERENCE NO: {out_conv}"))
    lines.append(_line(f"{permit.inward_carrier_agent.name[:35]:<36s}OBL/MAWB/UCR NO:"))
    lines.append(_line(f"{permit.inward_carrier_agent.address_line1[:35]:<36s}{permit.transport.outward.mawb_oucr_obl[:35]}"))

    departure = _format_date(permit.transport.departure_date)
    lines.append(_line(f"{permit.inward_carrier_agent.entity_id[:30]:<36s}DEPARTURE DATE       : {departure}"))

    lines.append(_line(f"OUTWARD CARRIER AGENT:"))
    cert_no = permit.licence_numbers[0] if permit.licence_numbers else ""
    lines.append(_line(f"{permit.outward_carrier_agent.name[:35]:<36s}CERTIFICATE NO: {cert_no[:17]}"))
    lines.append(_line(f"{permit.outward_carrier_agent.address_line1[:35]}"))
    lines.append(_line(f"{permit.outward_carrier_agent.entity_id[:30]}"))

    # Places
    lines.append(_line(""))
    lines.append(_line(f"PLACE OF RELEASE:{'':<20s}PLACE OF RECEIPT:"))
    lines.append(_line(f"{permit.cargo.release_location_name[:32]:<36s}{permit.cargo.receipt_location_name[:32]}"))
    lines.append(_line(f"{permit.cargo.release_location_code[:7]:<36s}{permit.cargo.receipt_location_code[:7]}"))

    # Licence / CPC
    lines.append(_line(f"LICENCE NO:{'':<25s}CUSTOMS PROCEDURE CODE (CPC) :"))
    for i in range(5):
        lic = permit.licence_numbers[i] if i < len(permit.licence_numbers) else ""
        cpc = permit.cpc_codes[i] if i < len(permit.cpc_codes) else ""
        if lic or cpc:
            lines.append(_line(f"{lic[:35]:<36s}{cpc[:35]}"))

    return lines


def _format_consignment_content(permit: PermitData) -> list[str]:
    """Format consignment details content."""
    lines: list[str] = []

    # Continuation header
    lines.append(_line(f"PERMIT NO    : {permit.permit_number:<11s}     ======================"))
    lines.append(_line(f"{'':>38s}(CONTINUATION PAGE)"))
    lines.append(_line(""))
    lines.append(_line("CONSIGNMENT DETAILS"))
    lines.append(_line(SEPARATOR_LINE))

    # Column headers
    lines.append(_line("S/NO  HS CODE    CURRENT LOT NO            PREVIOUS LOT NO"))
    lines.append(_line("MARKING  CTY OF ORIGIN  BRAND NAME        MODEL"))
    lines.append(_line("PACKING/GOODS DESCRIPTION                 HS QUANTITY & UNIT"))
    lines.append(_line(f"{'':>50s}CIF/FOB VALUE (S$)"))
    lines.append(_line(f"{'':>50s}GST AMOUNT (S$)"))
    lines.append(_line("MANUFACTURER'S NAME"))
    lines.append(_line(SEPARATOR_LINE))

    # Items
    for item in permit.items:
        lines.extend(_format_item(item))
        lines.append(_line(SEPARATOR_LINE))

    return lines


def _format_item(item: ConsignmentItem) -> list[str]:
    """Format a single consignment item per gold standard."""
    lines: list[str] = []

    # Line 1: S/No + HS Code
    sno = f"{item.sequence_number:5d}"
    lines.append(_line(f" {sno} {item.hs_code[:10]}"))

    # Line 2: Marking + Country + Brand
    marks = item.shipping_marks[:4] if item.shipping_marks else ""
    lines.append(_line(f" {marks:<4s}  {item.origin_country[:2]:<2s}   {item.brand_name[:35]}"))

    # Line 3: Packing/Goods description + HS Quantity
    goods = item.goods_description[:50]
    hs_qty = f"{item.hs_quantity} {item.hs_quantity_unit}".strip()
    if hs_qty:
        lines.append(_line(f"{goods:<50s}{hs_qty:>30s}"))
    else:
        lines.append(_line(f"{goods}"))

    # Line 4: CIF/FOB value
    if item.cif_fob_value:
        lines.append(_line(f"{'':>64s}{item.cif_fob_value:>16s}"))

    # Line 5: GST amount
    if item.gst_amount:
        lines.append(_line(f"{'':>64s}{item.gst_amount:>16s}"))

    # Line 6: Manufacturer
    if item.manufacturer_name:
        lines.append(_line(f"{item.manufacturer_name[:50]}"))

    # CA/SC Products
    for casc in item.casc_products:
        lines.append(_line(f"        {casc.code:<17s}                       {casc.quantity} {casc.unit}"))

    return lines


def _format_final_content(permit: PermitData) -> list[str]:
    """Format declarant block and conditions."""
    lines: list[str] = []

    # Blank lines between items and declarant
    lines.append(_line(""))
    lines.append(_line(""))

    # Containers (if any)
    if permit.containers:
        lines.append(_line(SEPARATOR_LINE))
        for container in permit.containers:
            lines.append(_line(f"{container}"))

    lines.append(_line(SEPARATOR_LINE))
    lines.append(_line("NO UNAUTHORISED ADDITION/AMENDMENT TO THIS PERMIT MAY BE MADE AFTER APPROVAL"))
    lines.append(_line(SEPARATOR_LINE))

    # Declarant block
    lines.append(_line(""))
    da_name = permit.declaring_agent.name
    lines.append(_line(f"NAME OF COMPANY: {da_name[:50]}"))
    lines.append(_line(""))
    lines.append(_line(f"DECLARANT NAME : {permit.declarant.name[:50]}"))
    lines.append(_line(""))
    lines.append(_line(f"DECLARANT CODE : {permit.declarant.code[:17]}"))
    lines.append(_line(f"TEL NO         : {permit.declarant.telephone[:25]}"))

    # Conditions
    lines.append(_line(SEPARATOR_LINE))
    lines.append(_line("CONTROLLING AGENCY/CUSTOMS CONDITIONS"))

    all_conditions = permit.ca_conditions + permit.sc_conditions
    for cond in all_conditions:
        cond_lines = _format_condition_gold(cond.condition_code, cond.description)
        lines.extend(cond_lines)

    return lines


def _format_condition_gold(code: str, description: str) -> list[str]:
    """Format a condition per gold standard: CODE - text, word-wrapped."""
    lines: list[str] = []
    prefix = f"{code:<4s} - "
    first_width = LINE_WIDTH - len(prefix)
    subsequent_width = LINE_WIDTH

    words = description.split()
    if not words:
        lines.append(_line(prefix))
        return lines

    current = ""
    is_first = True

    for word in words:
        max_w = first_width if is_first else subsequent_width
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= max_w:
            current += " " + word
        else:
            if is_first:
                lines.append(_line(prefix + current))
                is_first = False
            else:
                lines.append(_line(current))
            current = word

    if current:
        if is_first:
            lines.append(_line(prefix + current))
        else:
            lines.append(_line(current))

    return lines


def _get_message_type_description(msg_type: str) -> str:
    descriptions = {
        "IPTDEC": "IN-PAYMENT DECLARATION",
        "IPTUPD": "IN-PAYMENT UPDATE",
        "IPTPMT": "IN-PAYMENT PERMIT",
        "IPTUPT": "IN-PAYMENT UPDATED PERMIT",
        "INPDEC": "IN-NON-PAYMENT DECLARATION",
        "INPUPD": "IN-NON-PAYMENT UPDATE",
        "INPPMT": "IN-NON-PAYMENT PERMIT",
        "INPUPT": "IN-NON-PAYMENT UPDATED PERMIT",
        "OUTDEC": "OUTWARD DECLARATION",
        "OUTUPD": "OUTWARD UPDATE",
        "OUTPMT": "OUTWARD PERMIT",
        "OUTUPT": "OUTWARD UPDATED PERMIT",
        "TNPDEC": "TRANSHIPMENT/MOVEMENT DECLARATION",
        "TNPUPD": "TRANSHIPMENT/MOVEMENT UPDATE",
        "TNPPMT": "TRANSHIPMENT/MOVEMENT PERMIT",
        "TNPUPT": "TRANSHIPMENT/MOVEMENT UPDATED PERMIT",
    }
    return descriptions.get(msg_type, msg_type)


def _get_declaration_type_description(dec_type: str) -> str:
    descriptions = {
        "GST": "GST (INCLUDING DUTY EXEMPTION)",
        "DUT": "DUTY",
        "DNG": "DANGEROUS GOODS",
        "BKT": "BLANKET",
        "APS": "APPROVED PREMISES/SCHEME",
        "GTR": "GOVT TO GOVT TRANSFER",
        "SHO": "SHUT-OUT",
        "DES": "DESTRUCTION",
        "REX": "RE-EXPORT",
        "SFZ": "STORING IN FREE TRADE ZONE",
        "TCS": "TEMPORARY CONSIGNMENT STORES",
        "TCR": "TRANSHIPMENT CARGO REMOVAL",
        "TCE": "TEMPORARY EXHIBITION",
        "TCO": "TEMPORARY OUTWARD",
        "TCI": "TRANSHIPMENT CARGO IN",
        "DRT": "DUTY (OUTWARD)",
        "TTI": "THROUGH TRANSIT INWARD",
        "TTF": "THROUGH TRANSIT FORWARD",
        "IGM": "INWARD GATEWAY MOVEMENT",
        "REM": "REMOVAL",
        "BRE": "BONDED RE-EXPORT",
    }
    return descriptions.get(dec_type, dec_type)
