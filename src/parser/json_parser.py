"""
JSON Parser for GTNFE 5 backend API permit data.

Maps the flat JSON structure from the declaration processing system
into the shared PermitData domain model.
"""

import json

from src.models import (
    PermitData,
    Condition,
    Party,
    Declarant,
    CargoInfo,
    TransportInfo,
    TransportMeans,
    ConsignmentItem,
    PermitSummary,
    URN,
    ValidityPeriod,
    CASCProduct,
)

MSG_TYPE_MAP = {
    "IPT": "IPTPMT",
    "INP": "INPPMT",
    "OUT": "OUTPMT",
    "TNP": "TNPPMT",
}


def parse_json_permit(data: bytes) -> PermitData:
    """Parse a JSON permit payload into a PermitData domain object."""
    raw = json.loads(data)
    details = raw.get("details", {})

    permit = PermitData()
    permit.permit_number = raw.get("permit_number", "") or ""
    permit.declaration_type = raw.get("declaration_type", "") or ""

    msg_type = raw.get("message_type", "") or ""
    permit.message_type = MSG_TYPE_MAP.get(msg_type, msg_type)

    # URN
    urn_date = details.get("dateOfCreationInUrn", "") or ""
    permit.urn = URN(
        entity_id=details.get("declaringEntityIdInUrn", "") or "",
        date=_date_to_ccyymmdd(urn_date),
        sequence=str(details.get("sequenceNumberInUrn", 0) or 0).zfill(4),
    )

    # Validity period from outcomes
    outcomes = details.get("outcomes", [])
    if outcomes:
        outcome = outcomes[0]
        permit.validity_period = ValidityPeriod(
            start_date=_date_to_ccyymmdd(outcome.get("permitValidityStartDate", "") or ""),
            end_date=_date_to_ccyymmdd(outcome.get("permitValidityEndDate", "") or ""),
        )
        permit.permit_approval_datetime = outcome.get("permitApprovalDateTime", "") or ""

    # Parties
    permit.declaring_agent = Party(
        entity_id=details.get("declaringAgentEntityId", "") or "",
        name=details.get("declaringAgentName", "") or "",
    )

    permit.declarant = Declarant(
        code=details.get("declarantCode", "") or "",
        name=details.get("declarantName", "") or "",
        telephone=details.get("declarantContactNumber", "") or "",
    )

    permit.importer = Party(
        entity_id=details.get("importerEntityId", "") or "",
        name=details.get("importerName", "") or "",
    )

    permit.exporter = Party(
        entity_id=details.get("exporterEntityId", "") or "",
        name=details.get("exporterName", "") or "",
        address_line1=_get_address(details.get("exporterAddress")),
    )

    permit.handling_agent = Party(
        entity_id=details.get("handlingAgentEntityId", "") or "",
        name=details.get("handlingAgentName", "") or "",
    )

    permit.inward_carrier_agent = Party(
        entity_id=details.get("inwardCarrierAgentEntityId", "") or "",
        name=details.get("inwardCarrierAgentName", "") or "",
    )

    permit.outward_carrier_agent = Party(
        entity_id=details.get("outwardCarrierAgentEntityId", "") or "",
        name=details.get("outwardCarrierAgentName", "") or "",
    )

    permit.freight_forwarder = Party(
        entity_id=details.get("freightForwarderEntityId", "") or "",
        name=details.get("freightForwarderName", "") or "",
    )

    # Cargo
    permit.cargo = CargoInfo(
        packing_type=str(details.get("cargoPackingType", "") or ""),
        release_location_code=details.get("placeOfReleaseCode", "") or "",
        release_location_name=details.get("placeOfReleaseNameAddress", "") or "",
        receipt_location_code=details.get("placeOfReceiptCode", "") or "",
        receipt_location_name=details.get("placeOfReceiptNameAddress", "") or "",
        total_outer_pack=str(details.get("totalOuterPack", "") or ""),
        total_outer_pack_unit=details.get("totalOuterPackUnit", "") or "",
        total_gross_weight=str(details.get("totalGrossWeight", "") or ""),
        total_gross_weight_unit=details.get("totalGrossWeightUnit", "") or "",
    )

    # Transport
    permit.transport = TransportInfo(
        inward=TransportMeans(
            mode_code=str(details.get("inwardModeOfTransport", "") or ""),
            conveyance_reference=details.get("inwardConveyanceReferenceNumber", "") or "",
            transport_identifier=details.get("inwardTransportId", "") or "",
            mawb_oucr_obl=details.get("inwardMawbOucrOblNumber", "") or "",
        ),
        outward=TransportMeans(
            mode_code=str(details.get("outwardModeOfTransport", "") or ""),
            conveyance_reference=details.get("outwardConveyanceReferenceNumber", "") or "",
            transport_identifier=details.get("outwardTransportId", "") or "",
            mawb_oucr_obl=details.get("outwardMawbOucrOblNumber", "") or "",
        ),
        arrival_date=_date_to_ccyymmdd(details.get("dateOfArrival", "") or ""),
        departure_date=_date_to_ccyymmdd(details.get("dateOfDeparture", "") or ""),
        loading_port=details.get("portOfLoading", "") or details.get("nextPortOfCall", "") or "",
        discharge_port=details.get("portOfDischarge", "") or "",
        final_destination_country=details.get("countryOfFinalDestination", "") or "",
    )

    # Containers
    for c in details.get("containers", []):
        container_str = c.get("containerNumber", "") or ""
        if container_str:
            seal = c.get("shipperSealNumber", "") or ""
            type_size = c.get("containerTypeSize", "") or ""
            permit.containers.append(f"{container_str} {type_size} {seal}".strip())

    # Items
    for item_data in details.get("items", []):
        item = ConsignmentItem(
            sequence_number=item_data.get("sequenceNumber", 0) or 0,
            hs_code=item_data.get("hsCode", "") or "",
            goods_description=item_data.get("goodsDescription", "") or "",
            origin_country=item_data.get("countryOfOriginOfGoods", "") or "",
            brand_name=item_data.get("brandName", "") or "",
            model=item_data.get("model", "") or "",
            shipping_marks=item_data.get("marksNumbers", "") or "",
            in_hawb_hucr_hbl=item_data.get("inwardHawbHucrHblNumber", "") or "",
            in_mawb_oucr_obl=item_data.get("inwardMawbOucrOblNumber", "") or "",
            out_hawb_hucr_hbl=item_data.get("outwardHawbHucrHblNumber", "") or "",
            out_mawb_oucr_obl=item_data.get("outwardMawbOucrOblNumber", "") or "",
            hs_quantity=str(item_data.get("hsQuantity", "") or ""),
            hs_quantity_unit=item_data.get("hsQuantityUnit", "") or "",
            cif_fob_value=str(item_data.get("itemCifFobValue", "") or ""),
            lsp_value=str(item_data.get("itemLspValue", "") or ""),
            gst_amount=str(item_data.get("gstAmount", "") or ""),
            excise_duty=str(item_data.get("exciseDutyAmount", "") or ""),
            customs_duty=str(item_data.get("customsDutyAmount", "") or ""),
            other_tax=str(item_data.get("otherTaxAmount", "") or ""),
            unit_price=str(item_data.get("unitPrice", "") or ""),
            unit_price_currency=item_data.get("unitPriceCurrencyCode", "") or "",
            current_lot_no=item_data.get("currentLotNumber", "") or "",
            previous_lot_no=item_data.get("previousLotNumber", "") or "",
            manufacturer_name="",
            invoice_number=item_data.get("itemInvoiceNumber", "") or "",
            outer_pack_qty=str(item_data.get("outerPackQuantity", "") or ""),
            outer_pack_unit=str(item_data.get("outerPackQuantityUnit", "") or ""),
            inner_pack_qty=str(item_data.get("inPackQuantity", "") or ""),
            inner_pack_unit=str(item_data.get("inPackQuantityUnit", "") or ""),
            duty_quantity=str(item_data.get("dutiableQuantityWeightVolume", "") or ""),
            duty_quantity_unit=item_data.get("dutiableQuantityWeightVolumeUnit", "") or "",
        )

        for casc_data in item_data.get("caScProducts", []):
            item.casc_products.append(CASCProduct(
                code=casc_data.get("code", "") or "",
                quantity=str(casc_data.get("quantity", "") or ""),
                unit=casc_data.get("unit", "") or "",
            ))

        permit.items.append(item)

    # Summary
    permit.summary = PermitSummary(
        number_of_items=details.get("totalNumberOfItems", 0) or 0,
        total_cif_fob_value=str(details.get("totalCifFobValue", "") or ""),
        total_gst_amount=str(details.get("totalGstAmount", "") or ""),
        total_excise_duty=str(details.get("totalExciseDutyPayable", "") or ""),
        total_customs_duty=str(details.get("totalCustomsDutyPayable", "") or ""),
        total_other_tax=str(details.get("totalOtherTaxPayable", "") or ""),
        total_amount_payable=str(details.get("totalAmountPayable", "") or ""),
    )

    # Conditions from outcomes
    for outcome in outcomes:
        for cond_data in outcome.get("outcomeApprovalConditions", []):
            agency = cond_data.get("approvalAgency", "") or ""
            cond = Condition(
                agency_code=agency,
                condition_code=cond_data.get("approvalConditionCode", "") or "",
                description=cond_data.get("message", "") or "",
            )
            if agency == "CA":
                permit.ca_conditions.append(cond)
            else:
                permit.sc_conditions.append(cond)

    # Remarks
    permit.remarks = details.get("generalRemarksTraderRemarks", "") or ""

    return permit


def _date_to_ccyymmdd(date_str: str) -> str:
    """Convert YYYY-MM-DD to CCYYMMDD. Pass through if already CCYYMMDD."""
    if not date_str:
        return ""
    if "-" in date_str:
        parts = date_str.split("T")[0].split("-")
        if len(parts) == 3:
            return parts[0] + parts[1] + parts[2]
    return date_str


def _get_address(addr_obj) -> str:
    """Extract address line from address object."""
    if not addr_obj or not isinstance(addr_obj, dict):
        return ""
    return addr_obj.get("streetNumberPoBox", "") or ""
