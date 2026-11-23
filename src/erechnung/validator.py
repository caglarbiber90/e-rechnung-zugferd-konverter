"""KoSIT-equivalent validation without Java.

Runs the same artefacts the KoSIT validator uses (validator-configuration-xrechnung):
XML Schema (lxml/libxml2) and the pre-compiled Schematron XSLTs (Saxon-HE via saxonche),
then applies the scenario's customLevel overrides and the accept/reject rule of
resources/default-report.xsl:
  - any XML Schema error           -> reject
  - any message with level "error" -> reject (flag fatal/error, after customLevel)
  - otherwise                      -> accept
"""
from __future__ import annotations

import html
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

from .resources import resource_path

SCN_NS = {"s": "http://www.xoev.de/de/validator/framework/1/scenarios"}
SVRL_NS = "http://purl.oclc.org/dsdl/svrl"


@dataclass
class Message:
    level: str  # error | warning | information
    code: str
    text: str
    location: str = ""
    source: str = ""


@dataclass
class Result:
    scenario: str
    accepted: bool
    messages: list[Message] = field(default_factory=list)

    @property
    def errors(self):
        return [m for m in self.messages if m.level == "error"]

    @property
    def warnings(self):
        return [m for m in self.messages if m.level == "warning"]


@dataclass
class Scenario:
    name: str
    guideline: str
    xsd: Path
    schematrons: list[tuple[str, Path]]
    custom_levels: dict[str, str]


def _config_dir() -> Path:
    return resource_path("kosit")


def load_scenarios() -> list[Scenario]:
    base = _config_dir()
    tree = etree.parse(str(base / "scenarios.xml"))
    out = []
    for sc in tree.getroot().findall("s:scenario", SCN_NS):
        match = sc.findtext("s:match", namespaces=SCN_NS) or ""
        if "CrossIndustryInvoice" not in match:
            continue
        # guideline literal between the last pair of single quotes
        guideline = match.split("'")[-2]
        xsd = base / sc.find("s:validateWithXmlSchema/s:resource/s:location", SCN_NS).text.strip()
        schs = [
            (r.findtext("s:name", namespaces=SCN_NS).strip(),
             base / r.findtext("s:location", namespaces=SCN_NS).strip())
            for r in sc.findall("s:validateWithSchematron/s:resource", SCN_NS)
        ]
        levels = {cl.text.strip(): cl.get("level")
                  for cl in sc.findall("s:createReport/s:customLevel", SCN_NS)}
        out.append(Scenario(sc.findtext("s:name", namespaces=SCN_NS).strip(),
                            guideline, xsd, schs, levels))
    return out


_schema_cache: dict[Path, etree.XMLSchema] = {}
_xslt_cache: dict[Path, object] = {}
_proc = None


def _schema(path: Path) -> etree.XMLSchema:
    if path not in _schema_cache:
        _schema_cache[path] = etree.XMLSchema(etree.parse(str(path)))
    return _schema_cache[path]


def _xslt(path: Path):
    global _proc
    from saxonche import PySaxonProcessor
    if _proc is None:
        _proc = PySaxonProcessor(license=False)
    if path not in _xslt_cache:
        x = _proc.new_xslt30_processor()
        _xslt_cache[path] = x.compile_stylesheet(stylesheet_file=str(path))
    return _xslt_cache[path]


def _level(flag: str | None, role: str | None) -> str:
    vals = {flag, role}
    if vals & {"fatal", "error"}:
        return "error"
    if vals & {"warning", "warn"}:
        return "warning"
    if vals & {"information", "info"}:
        return "information"
    return "error"


def _run_schematron(xml_bytes: bytes, xsl: Path, source: str) -> list[Message]:
    exe = _xslt(xsl)
    doc = _proc.parse_xml(xml_text=xml_bytes.decode("utf-8"))
    svrl = exe.transform_to_string(xdm_node=doc)
    root = etree.fromstring(svrl.encode("utf-8"))
    msgs = []
    for el in root.iter("{%s}failed-assert" % SVRL_NS, "{%s}successful-report" % SVRL_NS):
        text = " ".join("".join(el.find("{%s}text" % SVRL_NS).itertext()).split()) \
            if el.find("{%s}text" % SVRL_NS) is not None else ""
        msgs.append(Message(_level(el.get("flag"), el.get("role")),
                            el.get("id") or "UNSPECIFIC", text, el.get("location", ""), source))
    return msgs


def detect_guideline(xml_bytes: bytes) -> str:
    root = etree.fromstring(xml_bytes)
    ids = root.xpath("/rsm:CrossIndustryInvoice/rsm:ExchangedDocumentContext/"
                     "ram:GuidelineSpecifiedDocumentContextParameter/ram:ID/text()",
                     namespaces={"rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
                                 "ram": "urn:un:unece:uncefact:data:standard:"
                                        "ReusableAggregateBusinessInformationEntity:100"})
    return ids[0].strip() if ids else ""


def validate(xml_bytes: bytes) -> Result:
    try:
        doc = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as e:
        return Result("-", False, [Message("error", "XML", f"XML nicht wohlgeformt: {e}", source="XML")])
    guideline = detect_guideline(xml_bytes)
    scen = next((s for s in load_scenarios() if s.guideline == guideline), None)
    if scen is None:
        return Result("-", False, [Message(
            "error", "NO-SCENARIO",
            f"Kein KoSIT-Prüfszenario für Guideline '{guideline}' gefunden.", source="Szenario")])
    msgs: list[Message] = []
    schema = _schema(scen.xsd)
    if not schema.validate(doc):
        for err in schema.error_log:
            msgs.append(Message("error", "XSD", err.message, f"Zeile {err.line}", "XML Schema"))
    else:
        # KoSIT only runs Schematron on schema-valid documents
        for name, xsl in scen.schematrons:
            msgs.extend(_run_schematron(xml_bytes, xsl, name))
    for m in msgs:
        if m.code in scen.custom_levels:
            m.level = scen.custom_levels[m.code]
    accepted = not any(m.level == "error" for m in msgs)
    return Result(scen.name, accepted, msgs)


LEVEL_DE = {"error": "Fehler", "warning": "Warnung", "information": "Information"}


def _section(title: str, res: Result) -> str:
    rows = "".join(
        f"<tr class='{m.level}'><td>{LEVEL_DE.get(m.level, m.level)}</td><td>{html.escape(m.code)}</td>"
        f"<td>{html.escape(m.text)}</td><td><small>{html.escape(m.location)}</small></td></tr>"
        for m in res.messages)
    verdict = "bestanden" if res.accepted else "NICHT bestanden"
    table = (f"<table><tr><th>Stufe</th><th>Regel</th><th>Meldung (Originaltext des Regelwerks)</th><th>Ort</th></tr>{rows}</table>"
             if rows else "<p>Keine Meldungen.</p>")
    return (f"<h2>{html.escape(title)}: {verdict}</h2><p>Szenario: {html.escape(res.scenario)}<br>"
            f"Fehler: {len(res.errors)}, Warnungen: {len(res.warnings)}</p>{table}")


def report_html(sections: list[tuple[str, Result]], notes: list[str] | None = None) -> str:
    body = "".join(_section(t, r) for t, r in sections)
    if notes:
        body += "<h2>Hinweise</h2><ul>" + "".join(f"<li>{html.escape(n)}</li>" for n in notes) + "</ul>"
    return f"""<!doctype html><html lang="de"><meta charset="utf-8"><title>Prüfbericht E-Rechnung</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;margin:2em;max-width:60em}}
td{{border-bottom:1px solid #ddd;padding:4px;vertical-align:top}}
.error td:first-child{{color:#b00;font-weight:bold}}.warning td:first-child{{color:#a60}}</style>
<h1>Prüfbericht E-Rechnung</h1>
<p>Regelwerk: KoSIT validator-configuration-xrechnung 3.0.2 (2026-09-02, enthält EN16931-Schematron 1.3.16),
ausgeführt mit Saxon-HE und lxml im E-Rechnung-Konverter.</p>
{body}</html>"""
