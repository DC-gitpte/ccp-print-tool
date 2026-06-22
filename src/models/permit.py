from dataclasses import dataclass, field


@dataclass
class URN:
    entity_id: str = ""
    date: str = ""
    sequence: str = ""


@dataclass
class ValidityPeriod:
    start_date: str = ""
    end_date: str = ""


@dataclass
class Party:
    entity_id: str = ""
    name: str = ""
    address_line1: str = ""
    address_line2: str = ""
    address_line3: str = ""


@dataclass
class Declarant:
    code: str = ""
    name: str = ""
    telephone: str = ""


@dataclass
class CargoInfo:
    packing_type: str = ""
    packing_type_description: str = ""
    release_location_code: str = ""
    release_location_name: str = ""
    receipt_location_code: str = ""
    receipt_location_name: str = ""
    total_gross_weight: str = ""
    total_gross_weight_unit: str = ""
    total_outer_pack: str = ""
    total_outer_pack_unit: str = ""


@dataclass
class TransportMeans:
    mode_code: str = ""
    conveyance_reference: str = ""
    transport_identifier: str = ""
    mawb_oucr_obl: str = ""
    hawb_hucr_hbl: str = ""


@dataclass
class TransportInfo:
    inward: TransportMeans = field(default_factory=TransportMeans)
    outward: TransportMeans = field(default_factory=TransportMeans)
    arrival_date: str = ""
    departure_date: str = ""
    loading_port: str = ""
    discharge_port: str = ""
    final_destination_country: str = ""


@dataclass
class CASCProduct:
    code: str = ""
    quantity: str = ""
    unit: str = ""


@dataclass
class ConsignmentItem:
    sequence_number: int = 0
    hs_code: str = ""
    goods_description: str = ""
    origin_country: str = ""
    brand_name: str = ""
    model: str = ""
    shipping_marks: str = ""
    in_hawb_hucr_hbl: str = ""
    in_mawb_oucr_obl: str = ""
    out_hawb_hucr_hbl: str = ""
    out_mawb_oucr_obl: str = ""
    hs_quantity: str = ""
    hs_quantity_unit: str = ""
    cif_fob_value: str = ""
    lsp_value: str = ""
    gst_amount: str = ""
    duty_quantity: str = ""
    duty_quantity_unit: str = ""
    unit_price: str = ""
    unit_price_currency: str = ""
    excise_duty: str = ""
    customs_duty: str = ""
    other_tax: str = ""
    current_lot_no: str = ""
    previous_lot_no: str = ""
    engine_chassis_no: str = ""
    manufacturer_name: str = ""
    invoice_number: str = ""
    casc_products: list[CASCProduct] = field(default_factory=list)
    outer_pack_qty: str = ""
    outer_pack_unit: str = ""
    inner_pack_qty: str = ""
    inner_pack_unit: str = ""


@dataclass
class PermitSummary:
    number_of_items: int = 0
    total_cif_fob_value: str = ""
    total_gst_amount: str = ""
    total_excise_duty: str = ""
    total_customs_duty: str = ""
    total_other_tax: str = ""
    total_amount_payable: str = ""
    total_outer_pack: str = ""
    total_outer_pack_unit: str = ""
    total_gross_weight: str = ""
    total_gross_weight_unit: str = ""


@dataclass
class Condition:
    agency_code: str = ""
    condition_code: str = ""
    description: str = ""


@dataclass
class PermitData:
    permit_number: str = ""
    message_type: str = ""
    declaration_type: str = ""
    declaration_indicator: str = ""
    previous_permit_number: str = ""
    urn: URN = field(default_factory=URN)
    validity_period: ValidityPeriod = field(default_factory=ValidityPeriod)
    importer: Party = field(default_factory=Party)
    exporter: Party = field(default_factory=Party)
    handling_agent: Party = field(default_factory=Party)
    inward_carrier_agent: Party = field(default_factory=Party)
    outward_carrier_agent: Party = field(default_factory=Party)
    freight_forwarder: Party = field(default_factory=Party)
    declarant: Declarant = field(default_factory=Declarant)
    declaring_agent: Party = field(default_factory=Party)
    cargo: CargoInfo = field(default_factory=CargoInfo)
    transport: TransportInfo = field(default_factory=TransportInfo)
    items: list[ConsignmentItem] = field(default_factory=list)
    summary: PermitSummary = field(default_factory=PermitSummary)
    ca_conditions: list[Condition] = field(default_factory=list)
    sc_conditions: list[Condition] = field(default_factory=list)
    ca_approval_datetime: str = ""
    permit_approval_datetime: str = ""
    licence_numbers: list[str] = field(default_factory=list)
    cpc_codes: list[str] = field(default_factory=list)
    containers: list[str] = field(default_factory=list)
    remarks: str = ""
