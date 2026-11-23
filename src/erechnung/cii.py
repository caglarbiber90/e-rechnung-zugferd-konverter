"""Build UN/CEFACT CII D16B XML (EN 16931 / ZUGFeRD 2.x profile EN16931, optional XRechnung 3.0)."""
from __future__ import annotations

from decimal import Decimal

from lxml import etree

from .checks import vat_breakdown
from .model import Invoice, money

NS = {
    "rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
    "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
    "qdt": "urn:un:unece:uncefact:data:standard:QualifiedDataType:100",
    "udt": "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100",
}

GUIDELINE_EN16931 = "urn:cen.eu:en16931:2017"
GUIDELINE_XRECHNUNG = "urn:cen.eu:en16931:2017#compliant#urn:xeinkauf.de:kosit:xrechnung_3.0"
PEPPOL_PROCESS = "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"


def _q(tag):
    p, t = tag.split(":")
    return "{%s}%s" % (NS[p], t)


def _sub(parent, tag, text=None, **attrib):
    el = etree.SubElement(parent, _q(tag), attrib)
    if text is not None:
        el.text = str(text)
    return el


def _opt(parent, tag, text, **attrib):
    """Only write the element if there is a value (empty elements are forbidden)."""
    if text is not None and str(text).strip():
        return _sub(parent, tag, str(text).strip(), **attrib)
    return None


def _date(parent, tag, d):
    _sub(_sub(parent, tag), "udt:DateTimeString", d.strftime("%Y%m%d"), format="102")


def _num(d: Decimal, max_dec=4) -> str:
    d = Decimal(d).quantize(Decimal(1).scaleb(-max_dec)).normalize()
    s = format(d, "f")
    return s


def _amt(d) -> str:
    return format(money(d), "f")


def _address(parent, p):
    adr = _sub(parent, "ram:PostalTradeAddress")
    _opt(adr, "ram:PostcodeCode", p.zip)
    _opt(adr, "ram:LineOne", p.street)
    _opt(adr, "ram:CityName", p.city)
    _sub(adr, "ram:CountryID", (p.country or "DE").upper())


def build_cii(inv: Invoice, guideline: str = GUIDELINE_EN16931) -> bytes:
    s, b = inv.seller, inv.buyer
    root = etree.Element(_q("rsm:CrossIndustryInvoice"), nsmap=NS)

    ctx = _sub(root, "rsm:ExchangedDocumentContext")
    if guideline == GUIDELINE_XRECHNUNG:
        _sub(_sub(ctx, "ram:BusinessProcessSpecifiedDocumentContextParameter"), "ram:ID", PEPPOL_PROCESS)
    _sub(_sub(ctx, "ram:GuidelineSpecifiedDocumentContextParameter"), "ram:ID", guideline)

    doc = _sub(root, "rsm:ExchangedDocument")
    _sub(doc, "ram:ID", inv.number)
    _sub(doc, "ram:TypeCode", inv.type_code)
    _date(doc, "ram:IssueDateTime", inv.issue_date)
    if inv.note.strip():
        _sub(_sub(doc, "ram:IncludedNote"), "ram:Content", inv.note.strip())
    if s.legal_info.strip():
        reg = _sub(doc, "ram:IncludedNote")
        _sub(reg, "ram:Content", s.legal_info.strip())
        _sub(reg, "ram:SubjectCode", "REG")

    tx = _sub(root, "rsm:SupplyChainTradeTransaction")
    for i, ln in enumerate(inv.lines, 1):
        item = _sub(tx, "ram:IncludedSupplyChainTradeLineItem")
        _sub(_sub(item, "ram:AssociatedDocumentLineDocument"), "ram:LineID", str(i))
        prod = _sub(item, "ram:SpecifiedTradeProduct")
        _sub(prod, "ram:Name", ln.name.strip())
        _opt(prod, "ram:Description", ln.description)
        _sub(_sub(_sub(item, "ram:SpecifiedLineTradeAgreement"), "ram:NetPriceProductTradePrice"),
             "ram:ChargeAmount", _num(ln.price))
        _sub(_sub(item, "ram:SpecifiedLineTradeDelivery"), "ram:BilledQuantity", _num(ln.quantity),
             unitCode=ln.unit or "C62")
        lset = _sub(item, "ram:SpecifiedLineTradeSettlement")
        ltax = _sub(lset, "ram:ApplicableTradeTax")
        _sub(ltax, "ram:TypeCode", "VAT")
        _sub(ltax, "ram:CategoryCode", "S")
        _sub(ltax, "ram:RateApplicablePercent", _num(ln.vat_rate, 2))
        _sub(_sub(lset, "ram:SpecifiedTradeSettlementLineMonetarySummation"),
             "ram:LineTotalAmount", _amt(ln.net))

    agr = _sub(tx, "ram:ApplicableHeaderTradeAgreement")
    _opt(agr, "ram:BuyerReference", inv.buyer_reference)
    sp = _sub(agr, "ram:SellerTradeParty")
    _sub(sp, "ram:Name", s.name)
    if s.register_id.strip():
        _sub(_sub(sp, "ram:SpecifiedLegalOrganization"), "ram:ID", s.register_id.strip())
    if s.contact.strip() or s.phone.strip() or s.contact_email.strip():
        con = _sub(sp, "ram:DefinedTradeContact")
        _opt(con, "ram:PersonName", s.contact)
        if s.phone.strip():
            _sub(_sub(con, "ram:TelephoneUniversalCommunication"), "ram:CompleteNumber", s.phone.strip())
        if s.contact_email.strip():
            _sub(_sub(con, "ram:EmailURIUniversalCommunication"), "ram:URIID", s.contact_email.strip())
    _address(sp, s)
    if s.email.strip():
        _sub(_sub(sp, "ram:URIUniversalCommunication"), "ram:URIID", s.email.strip(), schemeID="EM")
    if s.vat_id.strip():
        _sub(_sub(sp, "ram:SpecifiedTaxRegistration"), "ram:ID", s.vat_id.strip(), schemeID="VA")
    if s.tax_no.strip():
        _sub(_sub(sp, "ram:SpecifiedTaxRegistration"), "ram:ID", s.tax_no.strip(), schemeID="FC")

    bp = _sub(agr, "ram:BuyerTradeParty")
    _sub(bp, "ram:Name", b.name)
    _address(bp, b)
    if b.email.strip():
        _sub(_sub(bp, "ram:URIUniversalCommunication"), "ram:URIID", b.email.strip(), schemeID="EM")
    if b.vat_id.strip():
        _sub(_sub(bp, "ram:SpecifiedTaxRegistration"), "ram:ID", b.vat_id.strip(), schemeID="VA")

    if inv.order_ref.strip():
        _sub(_sub(agr, "ram:BuyerOrderReferencedDocument"), "ram:IssuerAssignedID", inv.order_ref.strip())
    if inv.project_id.strip():
        proj = _sub(agr, "ram:SpecifiedProcuringProject")
        _sub(proj, "ram:ID", inv.project_id.strip())
        _sub(proj, "ram:Name", inv.project_name.strip() or inv.project_id.strip())

    _sub(tx, "ram:ApplicableHeaderTradeDelivery")

    st = _sub(tx, "ram:ApplicableHeaderTradeSettlement")
    _sub(st, "ram:PaymentReference", inv.number)
    _sub(st, "ram:InvoiceCurrencyCode", inv.currency)
    pm = _sub(st, "ram:SpecifiedTradeSettlementPaymentMeans")
    _sub(pm, "ram:TypeCode", "58")  # SEPA credit transfer
    if s.iban.strip():
        acc = _sub(pm, "ram:PayeePartyCreditorFinancialAccount")
        _sub(acc, "ram:IBANID", s.iban.replace(" ", "").upper())
        _opt(acc, "ram:AccountName", s.account_name or s.name)
        if s.bic.strip():
            _sub(_sub(pm, "ram:PayeeSpecifiedCreditorFinancialInstitution"), "ram:BICID", s.bic.strip())

    breakdown = vat_breakdown(inv)
    single = len(breakdown) == 1
    for rate, (basis, tax) in sorted(breakdown.items()):
        t = _sub(st, "ram:ApplicableTradeTax")
        _sub(t, "ram:CalculatedAmount", _amt(inv.vat_total if single else tax))
        _sub(t, "ram:TypeCode", "VAT")
        _sub(t, "ram:BasisAmount", _amt(basis))
        _sub(t, "ram:CategoryCode", "S")
        _sub(t, "ram:RateApplicablePercent", _num(rate, 2))
    if inv.period_start and inv.period_end:
        per = _sub(st, "ram:BillingSpecifiedPeriod")
        _date(per, "ram:StartDateTime", inv.period_start)
        _date(per, "ram:EndDateTime", inv.period_end)
    if inv.payment_terms.strip() or inv.due_date:
        terms = _sub(st, "ram:SpecifiedTradePaymentTerms")
        _opt(terms, "ram:Description", inv.payment_terms)
        if inv.due_date:
            _date(terms, "ram:DueDateDateTime", inv.due_date)
    line_total = money(sum((ln.net for ln in inv.lines), Decimal(0)))
    tot = _sub(st, "ram:SpecifiedTradeSettlementHeaderMonetarySummation")
    _sub(tot, "ram:LineTotalAmount", _amt(line_total))
    _sub(tot, "ram:TaxBasisTotalAmount", _amt(inv.net_total))
    _sub(tot, "ram:TaxTotalAmount", _amt(inv.vat_total), currencyID=inv.currency)
    _sub(tot, "ram:GrandTotalAmount", _amt(inv.gross_total))
    _sub(tot, "ram:DuePayableAmount", _amt(inv.gross_total))
    if inv.accounting_ref.strip():
        _sub(_sub(st, "ram:ReceivableSpecifiedTradeAccountingAccount"), "ram:ID", inv.accounting_ref.strip())

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True)
