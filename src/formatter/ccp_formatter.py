"""
CCP Formatter — converts PermitData into fixed-width 80-column
Cargo Clearance Permit pages as per TN4.1 DRS specification.

Page structure:
  Page 1: Header (permit details, parties, transport, totals)
  Page 2+: Consignment details (max 3 items per page)
  Last page: Containers, declarant block, conditions
"""

from src.models import PermitData, ConsignmentItem
from src.config import LINE_WIDTH_CHARS, MAX_ITEMS_PER_PAGE
from .condition_formatter import format_conditions_section

LINE_WIDTH = LINE_WIDTH_CHARS
SEPARATOR_LINE = "-" * LINE_WIDTH


def format_ccp(permit: PermitData) -> list[list[str]]:
    """
    Format a PermitData into CCP pages.
    Returns a list of pages, each page being a list of 80-char lines.
    """
    pages: list[list[str]] = []
    total_pages = _calculate_total_pages(permit)

    pages.append(_format_header_page(permit, page_num=1, total_pages=total_pages))

    item_pages = _format_consignment_pages(permit, total_pages)
    pages.extend(item_pages)

    last_page = _format_final_page(permit, len(pages) + 1, total_pages)
    pages.append(last_page)

    return pages


def format_ccp_text(permit: PermitData) -> str:
    """Format CCP as text with form-feed page separators."""
    pages = format_ccp(permit)
    return "\f".join("\n".join(page) for page in pages)


def _calculate_total_pages(permit: PermitData) -> int:
    num_items = len(permit.items)
    item_pages = max(1, (num_items + MAX_ITEMS_PER_PAGE - 1) // MAX_ITEMS_PER_PAGE)
    return 1 + item_pages + 1


def _line(text: str) -> str:
    """Pad or truncate to exactly LINE_WIDTH chars."""
    return text[:LINE_WIDTH].ljust(LINE_WIDTH)


def _format_date(date_str: str) -> str:
    """Convert CCYYMMDD to DD/MM/CCYY."""
    if len(date_str) >= 8:
        return f"{date_str[6:8]}/{date_str[4:6]}/{date_str[0:4]}"
    return date_str


def _format_amount(amount_str: str) -> str:
    """Format amount with S$ prefix."""
    if not amount_str:
        return "S$0.00"
    try:
        val = float(amount_str)
        return f"S${val:,.2f}"
    except (ValueError, TypeError):
        return f"S${amount_str}"


def _format_header_page(permit: PermitData, page_num: int, total_pages: int) -> list[str]:
    """Format first page: header information."""
    lines: list[str] = []

    for _ in range(5):
        lines.append(_line(""))

    permit_no_line = " " * 56 + f"PERMIT NO : {permit.permit_number}"
    lines.append(_line(permit_no_line))

    for _ in range(4):
        lines.append(_line(""))

    page_indicator = f"PG : {page_num:2d} OF {total_pages:2d}"
    title_line = " " * 37 + "CARGO CLEARANCE PERMIT" + " " * 8 + page_indicator
    lines.append(_line(title_line))

    lines.append(_line(""))
    lines.append(_line(""))

    msg_type_desc = _get_message_type_description(permit.message_type)
    lines.append(_line(f"MESSAGE TYPE      : {msg_type_desc}"))

    dec_type_desc = _get_declaration_type_description(permit.declaration_type)
    lines.append(_line(f"DECLARATION TYPE  : {dec_type_desc}"))

    lines.append(_line(""))
    lines.append(_line(""))

    # Importer + Validity
    validity_start = _format_date(permit.validity_period.start_date)
    validity_end = _format_date(permit.validity_period.end_date)

    lines.append(_line(f" {'IMPORTER:':<35s}VALIDITY PERIOD      : {validity_start} -"))
    lines.append(_line(f" {permit.importer.name[:35]:<35s}                       {validity_end}"))
    lines.append(_line(f" {permit.importer.address_line1[:35]:<35s}"))

    weight_str = f"{permit.cargo.total_gross_weight}/{permit.cargo.total_gross_weight_unit}"
    lines.append(_line(f" {permit.importer.entity_id[:17]:<35s}TOTAL GROSS WT/UNIT  : {weight_str}"))

    # Exporter + Totals
    pack_str = f"{permit.cargo.total_outer_pack}/{permit.cargo.total_outer_pack_unit}"
    lines.append(_line(f" {'EXPORTER:':<35s}TOTAL OUTER PACK/UNIT: {pack_str}"))
    lines.append(
        _line(f" {permit.exporter.name[:35]:<35s}TOT EXCISE DUT PAYABLE : {_format_amount(permit.summary.total_excise_duty)}")
    )
    lines.append(
        _line(f" {permit.exporter.address_line1[:35]:<35s}TOT CUSTOMS DUT PAYABLE: {_format_amount(permit.summary.total_customs_duty)}")
    )
    lines.append(
        _line(f" {permit.exporter.entity_id[:17]:<35s}TOT OTHER TAX PAYABLE  : {_format_amount(permit.summary.total_other_tax)}")
    )

    # Handling Agent + GST/Total
    lines.append(
        _line(f" {'HANDLING AGENT:':<35s}TOTAL GST AMT          : {_format_amount(permit.summary.total_gst_amount)}")
    )
    lines.append(
        _line(f" {permit.handling_agent.name[:35]:<35s}TOTAL AMOUNT PAYABLE   : {_format_amount(permit.summary.total_amount_payable)}")
    )
    lines.append(
        _line(f" {permit.handling_agent.address_line1[:35]:<35s}CARGO PACKING TYPE: {permit.cargo.packing_type_description[:23]}")
    )
    lines.append(_line(f" {permit.handling_agent.entity_id[:30]:<35s}IN TRANSPORT IDENTIFIER:"))

    in_transport = permit.transport.inward.transport_identifier[:35]
    lines.append(_line(f" {'':<35s}{in_transport}"))

    # Ports + Transport
    conv_ref = permit.transport.inward.conveyance_reference[:17]
    lines.append(_line(f" {'PORT OF LOADING/NEXT PORT OF CALL:':<35s}CONVEYANCE REFERENCE NO: {conv_ref}"))
    lines.append(_line(f" {permit.transport.loading_port[:35]:<35s}OBL/MAWB NO:"))
    lines.append(_line(f" {'PORT OF DISCHARGE/FINAL PORT OF CALL':<35s}{permit.transport.inward.mawb_oucr_obl[:35]}"))

    arrival = _format_date(permit.transport.arrival_date)
    lines.append(_line(f" {permit.transport.discharge_port[:35]:<35s}ARRIVAL DATE         : {arrival}"))

    lines.append(_line(f" {'COUNTRY OF FINAL DESTINATION:':<35s}OU TRANSPORT IDENTIFIER:"))
    lines.append(_line(f" {permit.transport.final_destination_country[:35]:<35s}{permit.transport.outward.transport_identifier[:35]}"))

    out_conv = permit.transport.outward.conveyance_reference[:17]
    lines.append(_line(f" {'INWARD CARRIER AGENT:':<35s}CONVEYANCE REFERENCE NO: {out_conv}"))
    lines.append(_line(f" {permit.inward_carrier_agent.name[:35]:<35s}OBL/MAWB/UCR NO:"))
    lines.append(_line(f" {permit.inward_carrier_agent.address_line1[:35]:<35s}{permit.transport.outward.mawb_oucr_obl[:35]}"))

    departure = _format_date(permit.transport.departure_date)
    lines.append(_line(f" {permit.inward_carrier_agent.entity_id[:30]:<35s}DEPARTURE DATE       : {departure}"))

    # Outward carrier agent
    lines.append(_line(f" {'OUTWARD CARRIER AGENT:':<35s}"))
    cert_no = permit.licence_numbers[0] if permit.licence_numbers else ""
    lines.append(_line(f" {permit.outward_carrier_agent.name[:35]:<35s}CERTIFICATE NO: {cert_no[:17]}"))
    lines.append(_line(f" {permit.outward_carrier_agent.address_line1[:35]:<35s}"))
    lines.append(_line(f" {permit.outward_carrier_agent.entity_id[:30]:<35s}"))

    # Places
    lines.append(_line(f" {'PLACE OF RELEASE:':<35s}PLACE OF RECEIPT:"))
    lines.append(
        _line(f" {permit.cargo.release_location_name[:32]:<35s}{permit.cargo.receipt_location_name[:32]}")
    )
    lines.append(_line(""))
    lines.append(_line(""))

    # Licence / CPC
    lines.append(_line(f" {'LICENCE NO:':<35s}CUSTOMS PROCEDURE CODE (CPC) :"))
    for i in range(5):
        lic = permit.licence_numbers[i] if i < len(permit.licence_numbers) else ""
        cpc = permit.cpc_codes[i] if i < len(permit.cpc_codes) else ""
        lines.append(_line(f" {lic[:35]:<35s}{cpc[:35]}"))

    lines.append(_line(SEPARATOR_LINE))

    urn_str = f"{permit.urn.entity_id} {permit.urn.date} {permit.urn.sequence}"
    lines.append(_line(f" UNIQUE REF : {urn_str}"))

    return lines


def _format_consignment_pages(permit: PermitData, total_pages: int) -> list[list[str]]:
    """Format consignment detail pages."""
    pages: list[list[str]] = []
    items = permit.items

    for page_start in range(0, len(items), MAX_ITEMS_PER_PAGE):
        page_items = items[page_start : page_start + MAX_ITEMS_PER_PAGE]
        page_num = len(pages) + 2
        pages.append(_format_single_consignment_page(permit, page_items, page_num, total_pages))

    if not pages:
        pages.append(_format_single_consignment_page(permit, [], 2, total_pages))

    return pages


def _format_single_consignment_page(
    permit: PermitData,
    items: list[ConsignmentItem],
    page_num: int,
    total_pages: int,
) -> list[str]:
    """Format a single consignment detail page."""
    lines: list[str] = []

    page_indicator = f"PG : {page_num:2d} OF {total_pages:2d}"
    lines.append(_line(" " * 37 + "CARGO CLEARANCE PERMIT" + " " * 8 + page_indicator))
    lines.append(_line(f" PERMIT NO    : {permit.permit_number:<11s}     ======================"))
    lines.append(_line(" " * 38 + "(CONTINUATION PAGE)"))
    lines.append(_line(""))

    lines.append(_line(" CONSIGNMENT DETAILS"))
    lines.append(_line(SEPARATOR_LINE))
    lines.append(_line(" S/NO HS CODE   CURRENT LOT NO            PREVIOUS LOT NO"))
    lines.append(_line(" MARKING  CTY OF ORIGIN  BRAND NAME        MODEL"))
    lines.append(_line(" IN MAWB/OUCR/OBL                         OUT MAWB/OUCR/OBL"))
    lines.append(_line(" IN HAWB/HUCR/HBL                         OUT HAWB/HUCR/HBL"))
    lines.append(_line(" PACKING/GOODS DESCRIPTION                HS QUANTITY & UNIT"))
    lines.append(_line("                                           CIF/FOB VALUE (S$)"))
    lines.append(_line("                                           LSP VALUE (S$)"))
    lines.append(_line("                                           GST AMOUNT (S$)"))
    lines.append(_line("                                           DUT QTY/WT/VOL & UNIT"))
    lines.append(_line("                                           UNIT PRICE & CODE"))
    lines.append(_line("                                           EXCISE DUTY PAYABLE (S$)"))
    lines.append(_line("                                           CUSTOMS DUTY PAYABLE(S$)"))
    lines.append(_line("                                           OTHER TAX PAYABLE(S$)"))
    lines.append(_line(" MANUFACTURER'S NAME"))
    lines.append(_line(SEPARATOR_LINE))

    for item in items:
        lines.extend(_format_item(item))
        lines.append(_line(SEPARATOR_LINE))

    urn_str = f"{permit.urn.entity_id} {permit.urn.date} {permit.urn.sequence}"
    lines.append(_line(f" UNIQUE REF : {urn_str}"))

    return lines


def _format_item(item: ConsignmentItem) -> list[str]:
    """Format a single consignment item."""
    lines: list[str] = []

    sno = f"{item.sequence_number:5d}"
    lines.append(_line(f" {sno}  {item.hs_code[:10]:<10s}  {item.current_lot_no[:30]:<30s}{item.previous_lot_no}"))

    marks = item.shipping_marks[:4] if item.shipping_marks else ""
    lines.append(_line(f" {marks:<4s}  {item.origin_country[:2]:<2s}   {item.brand_name[:35]:<35s}{item.model}"))

    lines.append(_line(f" {item.in_mawb_oucr_obl[:35]:<40s}{item.out_mawb_oucr_obl}"))
    lines.append(_line(f" {item.in_hawb_hucr_hbl[:35]:<40s}{item.out_hawb_hucr_hbl}"))

    packing = f"{item.outer_pack_qty} {item.outer_pack_unit} {item.inner_pack_qty} {item.inner_pack_unit}".strip()
    hs_qty = f"{item.hs_quantity} {item.hs_quantity_unit}".strip()
    lines.append(_line(f" {packing:<20s}                                   {hs_qty[:20]}"))

    lines.append(_line(f" {item.goods_description[:50]:<50s}{item.cif_fob_value:>14s}"))
    lines.append(_line(f" {'':<50s}{item.lsp_value:>14s}"))
    lines.append(_line(f" {'':<50s}{item.gst_amount:>14s}"))

    duty_qty = f"{item.duty_quantity} {item.duty_quantity_unit}".strip()
    lines.append(_line(f" {'':<50s}{duty_qty[:20]:>20s}"))

    unit_price = f"{item.unit_price} {item.unit_price_currency}".strip()
    lines.append(_line(f" {'':<50s}{unit_price[:20]:>20s}"))

    lines.append(_line(f" {'':<50s}{item.excise_duty:>14s}"))
    lines.append(_line(f" {'':<50s}{item.customs_duty:>14s}"))
    lines.append(_line(f" {'':<50s}{item.other_tax:>14s}"))
    lines.append(_line(f" {item.manufacturer_name[:50]}"))

    for casc in item.casc_products:
        lines.append(_line(f"        {casc.code:<17s}                       {casc.quantity} {casc.unit}"))

    if item.engine_chassis_no:
        lines.append(_line(f"        {item.engine_chassis_no}"))

    return lines


def _format_final_page(permit: PermitData, page_num: int, total_pages: int) -> list[str]:
    """Format the final page with declarant and conditions."""
    lines: list[str] = []

    page_indicator = f"PG : {page_num:2d} OF {total_pages:2d}"
    lines.append(_line(" " * 37 + "CARGO CLEARANCE PERMIT" + " " * 8 + page_indicator))
    lines.append(_line(f" PERMIT NO    : {permit.permit_number:<11s}     ======================"))
    lines.append(_line(" " * 38 + "(CONTINUATION PAGE)"))
    lines.append(_line(""))

    if permit.containers:
        lines.append(_line(" CONSIGNMENT DETAILS (Cont'd)"))
        lines.append(_line(SEPARATOR_LINE))
        for container in permit.containers:
            lines.append(_line(f" {container}"))
        lines.append(_line(""))

    lines.append(_line(SEPARATOR_LINE))
    lines.append(
        _line(" NO UNAUTHORISED ADDITION/AMENDMENT TO THIS PERMIT MAY BE MADE AFTER APPROVAL")
    )
    lines.append(_line(SEPARATOR_LINE))

    da_name = permit.declaring_agent.name
    lines.append(_line(f" NAME OF COMPANY: {da_name[:50]}"))
    if len(da_name) > 50:
        lines.append(_line(f"                  {da_name[50:100]}"))

    dec_name = permit.declarant.name
    lines.append(_line(f" DECLARANT NAME : {dec_name[:50]}"))
    if len(dec_name) > 50:
        lines.append(_line(f"                  {dec_name[50:100]}"))

    lines.append(_line(f" DECLARANT CODE : {permit.declarant.code[:17]}"))
    lines.append(_line(f" TEL NO         : {permit.declarant.telephone[:25]}"))

    lines.append(_line(SEPARATOR_LINE))
    condition_lines = format_conditions_section(permit.ca_conditions, permit.sc_conditions)
    lines.extend(_line(cl) for cl in condition_lines)

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
        "GST": "GOODS AND SERVICES TAX",
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
