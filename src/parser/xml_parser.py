"""
XML Parser for TradenetResponse messages.

Parses TN4.1 XML and extracts permit data into the domain model.
Supports all 4 message families: IPT, INP, OUT, TNP.
"""

from lxml import etree

from src.models import (
    PermitData,
    Condition,
    Party,
    CargoInfo,
    TransportInfo,
    TransportMeans,
    ConsignmentItem,
    PermitSummary,
    URN,
    ValidityPeriod,
    CASCProduct,
)

NS = {
    "tn": "urn:crimsonlogic:tn:schema:xsd:TradenetResponse",
    "cbc": "urn:crimsonlogic:tn:schema:xsd:CommonBasicComponents-2",
    "cac": "urn:crimsonlogic:tn:schema:xsd:CommonAggregateComponents-2",
    "ipt": "urn:crimsonlogic:tn:schema:xsd:InPayment",
    "inp": "urn:crimsonlogic:tn:schema:xsd:InNonPayment",
    "out": "urn:crimsonlogic:tn:schema:xsd:OutwardDeclaration",
    "tnp": "urn:crimsonlogic:tn:schema:xsd:TranshipmentMovement",
    "app": "urn:crimsonlogic:tn:schema:xsd:ApprovalMessage",
}

MESSAGE_FAMILIES = {
    "InPaymentPermit": "ipt",
    "InNonPaymentPermit": "inp",
    "OutwardDeclarationPermit": "out",
    "TranshipmentMovementPermit": "tnp",
}


def parse_tradenet_response(xml_bytes: bytes) -> PermitData:
    """Parse a TradenetResponse XML into a PermitData domain object."""
    root = etree.fromstring(xml_bytes)
    permit_element, family_prefix = _find_permit_element(root)
    if permit_element is None:
        raise ValueError("No permit element found in TradenetResponse XML")

    declaration = _find_child(permit_element, "Declaration", family_prefix)
    permit_section = _find_child(permit_element, "Permit", "cac")
    if permit_section is None:
        permit_section = permit_element.find(".//{%s}Permit" % NS["cac"])

    permit_data = PermitData()

    if declaration is not None:
        _parse_header(declaration, permit_data, family_prefix)
        _parse_cargo(declaration, permit_data, family_prefix)
        _parse_transport(declaration, permit_data, family_prefix)
        _parse_parties(declaration, permit_data, family_prefix)
        _parse_items(declaration, permit_data, family_prefix)
        _parse_summary(declaration, permit_data, family_prefix)

    if permit_section is not None:
        _parse_permit_section(permit_section, permit_data)

    return permit_data


def _find_permit_element(root):
    """Find the permit element (InPaymentPermit, InNonPaymentPermit, etc.)."""
    for tag_suffix, prefix in MESSAGE_FAMILIES.items():
        ns_uri = NS[prefix]
        el = root.find(f".//{{{ns_uri}}}{tag_suffix}")
        if el is not None:
            return el, prefix

    for child in root.iter():
        tag = etree.QName(child.tag).localname if isinstance(child.tag, str) else ""
        if "Permit" in tag and "Approval" not in tag and "Condition" not in tag:
            for prefix, ns_uri in NS.items():
                if ns_uri in (child.tag or ""):
                    return child, prefix
            return child, "inp"

    return None, None


def _find_child(parent, local_name, ns_prefix):
    """Find a child element by local name within a namespace prefix."""
    if parent is None:
        return None
    ns_uri = NS.get(ns_prefix, "")
    el = parent.find(f"{{{ns_uri}}}{local_name}")
    if el is not None:
        return el
    for child in parent:
        child_local = etree.QName(child.tag).localname if isinstance(child.tag, str) else ""
        if child_local == local_name:
            return child
    return None


def _text(parent, xpath_local, ns_prefix="cbc") -> str:
    """Get text content of a child element."""
    if parent is None:
        return ""
    ns_uri = NS.get(ns_prefix, "")
    el = parent.find(f".//{{{ns_uri}}}{xpath_local}")
    if el is not None and el.text:
        return el.text.strip()
    for child in parent.iter():
        local = etree.QName(child.tag).localname if isinstance(child.tag, str) else ""
        if local == xpath_local and child.text:
            return child.text.strip()
    return ""


def _parse_header(declaration, permit_data: PermitData, family_prefix: str):
    """Parse the declaration header."""
    header = _find_child(declaration, "Header", family_prefix)
    if header is None:
        return

    permit_data.message_type = _text(header, "CommonAccessReference")
    permit_data.declaration_type = _text(header, "DeclarationType")
    permit_data.previous_permit_number = _text(header, "PreviousPermitNumber")
    permit_data.declaration_indicator = _text(header, "DeclarationIndicator")
    permit_data.remarks = _text(header, "FreeText")

    urn_el = _find_child(header, "UniqueReferenceNumber", "cac")
    if urn_el is not None:
        permit_data.urn = URN(
            entity_id=_text(urn_el, "ID"),
            date=_text(urn_el, "Date"),
            sequence=_text(urn_el, "SequenceNumeric"),
        )


def _parse_cargo(declaration, permit_data: PermitData, family_prefix: str):
    """Parse cargo information."""
    cargo_el = _find_child(declaration, "Cargo", family_prefix)
    if cargo_el is None:
        return

    cargo = permit_data.cargo
    cargo.packing_type = _text(cargo_el, "CargoPackingType")

    release_el = _find_child(cargo_el, "ReleaseLocation", "cac")
    if release_el is not None:
        cargo.release_location_code = _text(release_el, "LocationCode")
        cargo.release_location_name = _text(release_el, "LocationName")

    receipt_el = _find_child(cargo_el, "ReceiptLocation", "cac")
    if receipt_el is not None:
        cargo.receipt_location_code = _text(receipt_el, "LocationCode")
        cargo.receipt_location_name = _text(receipt_el, "LocationName")


def _parse_transport(declaration, permit_data: PermitData, family_prefix: str):
    """Parse transport information."""
    transport_el = _find_child(declaration, "Transport", family_prefix)
    if transport_el is None:
        return

    transport = permit_data.transport

    inward_el = _find_child(transport_el, "InwardTransport", "cac")
    if inward_el is not None:
        means_el = _find_child(inward_el, "TransportMeans", "cac")
        if means_el is not None:
            mode_el = _find_child(means_el, "TransportMode", "cac")
            if mode_el is not None:
                transport.inward.mode_code = _text(mode_el, "ModeCode")
                transport.inward.conveyance_reference = _text(
                    mode_el, "ConveyanceReferenceNumber"
                )
            transport.inward.mawb_oucr_obl = _text(means_el, "MAWBOUCROBLNumber")
        transport.arrival_date = _text(inward_el, "ArrivalDate")
        transport.loading_port = _text(inward_el, "LoadingPort")

    outward_el = _find_child(transport_el, "OutwardTransport", "cac")
    if outward_el is not None:
        means_el = _find_child(outward_el, "TransportMeans", "cac")
        if means_el is not None:
            mode_el = _find_child(means_el, "TransportMode", "cac")
            if mode_el is not None:
                transport.outward.mode_code = _text(mode_el, "ModeCode")
                transport.outward.conveyance_reference = _text(
                    mode_el, "ConveyanceReferenceNumber"
                )
            transport.outward.mawb_oucr_obl = _text(means_el, "MAWBOUCROBLNumber")
        transport.departure_date = _text(outward_el, "DepartureDate")
        transport.discharge_port = _text(outward_el, "DischargePort")


def _parse_parties(declaration, permit_data: PermitData, family_prefix: str):
    """Parse party information."""
    party_el = _find_child(declaration, "Party", family_prefix)
    if party_el is None:
        return

    dec_el = _find_child(party_el, "DeclarantParty", "cac")
    if dec_el is not None:
        person_el = _find_child(dec_el, "PersonInformation", "cac")
        if person_el is not None:
            permit_data.declarant.code = _text(person_el, "CodeValue")
            permit_data.declarant.name = _text(person_el, "Name")
        permit_data.declarant.telephone = _text(dec_el, "Telephone")

    da_el = _find_child(party_el, "DeclaringAgentParty", "cac")
    if da_el is not None:
        permit_data.declaring_agent = _parse_party_element(da_el)

    imp_el = _find_child(party_el, "ImporterParty", "cac")
    if imp_el is not None:
        permit_data.importer = _parse_party_element(imp_el)

    exp_el = _find_child(party_el, "ExporterParty", "cac")
    if exp_el is not None:
        permit_data.exporter = _parse_party_element(exp_el)

    ff_el = _find_child(party_el, "FreightForwarderParty", "cac")
    if ff_el is not None:
        permit_data.freight_forwarder = _parse_party_element(ff_el)

    ica_el = _find_child(party_el, "InwardCarrierAgentParty", "cac")
    if ica_el is not None:
        permit_data.inward_carrier_agent = _parse_party_element(ica_el)

    oca_el = _find_child(party_el, "OutwardCarrierAgentParty", "cac")
    if oca_el is not None:
        permit_data.outward_carrier_agent = _parse_party_element(oca_el)

    ha_el = _find_child(party_el, "HandlingAgentParty", "cac")
    if ha_el is not None:
        permit_data.handling_agent = _parse_party_element(ha_el)


def _parse_party_element(el) -> Party:
    """Parse a party element into a Party dataclass."""
    party = Party()
    id_el = _find_child(el, "PartyIdentification", "cac")
    if id_el is not None:
        party.entity_id = _text(id_el, "ID")
    name_el = _find_child(el, "PartyName", "cac")
    if name_el is not None:
        party.name = _text(name_el, "Name")
    addr_el = _find_child(el, "PartyAddress", "cac")
    if addr_el is not None:
        party.address_line1 = _text(addr_el, "StreetName")
        party.address_line2 = _text(addr_el, "CityName")
        party.address_line3 = _text(addr_el, "PostalZone")
    return party


def _parse_items(declaration, permit_data: PermitData, family_prefix: str):
    """Parse consignment items."""
    ns_uri = NS.get(family_prefix, "")

    for item_el in declaration.iter():
        local = etree.QName(item_el.tag).localname if isinstance(item_el.tag, str) else ""
        if local != "Item":
            continue
        if ns_uri and ns_uri not in (item_el.tag or ""):
            continue

        item = ConsignmentItem()
        seq = _text(item_el, "ItemSequenceNumeric")
        item.sequence_number = int(seq) if seq.isdigit() else 0
        item.hs_code = _text(item_el, "ItemHarmonizedSystemCode")
        item.goods_description = _text(item_el, "GoodsDescription")
        item.origin_country = _text(item_el, "OriginCountry")
        item.brand_name = _text(item_el, "BrandName")
        item.model = _text(item_el, "ModelDescription")
        item.in_hawb_hucr_hbl = _text(item_el, "InHAWBHUCRHBLNumber")
        item.in_mawb_oucr_obl = _text(item_el, "InMAWBOUCROBLNumber")
        item.out_hawb_hucr_hbl = _text(item_el, "OutHAWBHUCRHBLNumber")
        item.out_mawb_oucr_obl = _text(item_el, "OutMAWBOUCROBLNumber")
        item.invoice_number = _text(item_el, "ItemInvoiceNumber")

        marks_el = _find_child(item_el, "ShippingMarksInformation", "cac")
        if marks_el is not None:
            item.shipping_marks = _text(marks_el, "ShippingMarks")

        qty_el = _find_child(item_el, "ItemQuantity", "cac")
        if qty_el is not None:
            hs_qty_el = None
            for child in qty_el.iter():
                cl = etree.QName(child.tag).localname if isinstance(child.tag, str) else ""
                if "HarmonizedSystemQuantity" in cl:
                    hs_qty_el = child
                    break
            if hs_qty_el is not None:
                item.hs_quantity = (hs_qty_el.text or "").strip()
                item.hs_quantity_unit = hs_qty_el.get("unitCode", "")

        tv_el = _find_child(item_el, "TransactionValue", "cac")
        if tv_el is not None:
            item.cif_fob_value = _text(tv_el, "ItemCIFFOBValue")
            item.lsp_value = _text(tv_el, "LastSellingPriceValue")
            price_el = _find_child(tv_el, "UnitPriceValue", "cac")
            if price_el is not None:
                amt_el = None
                for child in price_el.iter():
                    cl = etree.QName(child.tag).localname if isinstance(child.tag, str) else ""
                    if cl == "Amount":
                        amt_el = child
                        break
                if amt_el is not None:
                    item.unit_price = (amt_el.text or "").strip()
                    item.unit_price_currency = amt_el.get("currencyID", "")

        tariff_el = _find_child(item_el, "Tariff", "cac")
        if tariff_el is not None:
            gst_el = _find_child(tariff_el, "GoodsAndServicesTax", "cac")
            if gst_el is not None:
                item.gst_amount = _text(gst_el, "GoodsAndServicesTaxAmount")
            customs_el = _find_child(tariff_el, "CustomsDuty", "cac")
            if customs_el is not None:
                item.customs_duty = _text(customs_el, "CustomsDutyAmount")
            excise_el = _find_child(tariff_el, "ExciseDuty", "cac")
            if excise_el is not None:
                item.excise_duty = _text(excise_el, "ExciseDutyAmount")

        for child in item_el.iter():
            cl = etree.QName(child.tag).localname if isinstance(child.tag, str) else ""
            if cl == "CASCProduct":
                casc = CASCProduct()
                casc.code = _text(child, "CASCProductCode")
                qty_child = None
                for sub in child.iter():
                    sl = etree.QName(sub.tag).localname if isinstance(sub.tag, str) else ""
                    if "CASCProductQuantity" in sl:
                        qty_child = sub
                        break
                if qty_child is not None:
                    casc.quantity = (qty_child.text or "").strip()
                    casc.unit = qty_child.get("unitCode", "")
                item.casc_products.append(casc)

        permit_data.items.append(item)


def _parse_summary(declaration, permit_data: PermitData, family_prefix: str):
    """Parse the summary section."""
    summary_el = _find_child(declaration, "Summary", family_prefix)
    if summary_el is None:
        return

    s = permit_data.summary
    num_items = _text(summary_el, "NumberOfItems")
    s.number_of_items = int(num_items) if num_items.isdigit() else 0
    s.total_cif_fob_value = _text(summary_el, "TotalCIFFOBValue")

    cargo = permit_data.cargo
    for child in summary_el.iter():
        cl = etree.QName(child.tag).localname if isinstance(child.tag, str) else ""
        if "TotalOuterPack" in cl:
            cargo.total_outer_pack = (child.text or "").strip()
            cargo.total_outer_pack_unit = child.get("unitCode", "")
        elif "TotalGrossWeight" in cl:
            cargo.total_gross_weight = (child.text or "").strip()
            cargo.total_gross_weight_unit = child.get("unitCode", "")

    tariff_el = _find_child(summary_el, "TotalTariff", "cac")
    if tariff_el is not None:
        s.total_gst_amount = _text(tariff_el, "TotalGoodsAndServicesTaxAmount")
        s.total_amount_payable = _text(tariff_el, "TotalAmountPayable")
        s.total_customs_duty = _text(tariff_el, "TotalCustomsDutyAmount")
        s.total_excise_duty = _text(tariff_el, "TotalExciseDutyAmount")
        s.total_other_tax = _text(tariff_el, "TotalOtherTaxAmount")


def _parse_permit_section(permit_section, permit_data: PermitData):
    """Parse the Permit section (approval details + conditions)."""
    permit_data.permit_number = _text(permit_section, "PermitNumber")
    permit_data.ca_approval_datetime = _text(permit_section, "CAApprovalDatetime")
    permit_data.permit_approval_datetime = _text(permit_section, "PermitApprovalDatetime")

    vp_el = _find_child(permit_section, "PermitValidityPeriod", "cac")
    if vp_el is not None:
        permit_data.validity_period = ValidityPeriod(
            start_date=_text(vp_el, "StartDate"),
            end_date=_text(vp_el, "EndDate"),
        )

    for child in permit_section.iter():
        cl = etree.QName(child.tag).localname if isinstance(child.tag, str) else ""
        if cl == "CAApprovalCondition":
            cond = Condition(
                agency_code=_text(child, "AgencyCode"),
                condition_code=_text(child, "ConditionCode"),
                description=_text(child, "ConditionDescription"),
            )
            permit_data.ca_conditions.append(cond)
        elif cl == "SCApprovalCondition":
            cond = Condition(
                agency_code=_text(child, "AgencyCode"),
                condition_code=_text(child, "ConditionCode"),
                description=_text(child, "ConditionDescription"),
            )
            permit_data.sc_conditions.append(cond)
