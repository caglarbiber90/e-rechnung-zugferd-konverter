"""Cross-check: run the Java KoSIT validator and the Python validator on the same XML files
and compare accept/reject and the set of (rule code, level).

Usage: py -3 tools/compare_java.py <validator.jar> <file.xml> [...]
"""
import subprocess, sys, tempfile, os
from pathlib import Path
from lxml import etree
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from erechnung.validator import validate, resource_path

REP = {"rep": "http://www.xoev.de/de/validator/varl/1"}

def java(jar, xml):
    cfg = resource_path("kosit")
    out = Path(tempfile.mkdtemp())
    empty = out / "empty"; empty.write_text("")
    with open(empty) as stdin:
        subprocess.run(["java", "-jar", jar, "-s", str(cfg / "scenarios.xml"), "-r", str(cfg),
                        "-o", str(out), str(xml)], stdin=stdin, capture_output=True)
    rep = etree.parse(str(out / (Path(xml).stem + "-report.xml")))
    acc = bool(rep.xpath("/rep:report/rep:assessment/rep:accept", namespaces=REP))
    msgs = set()
    for m in rep.xpath("//rep:message", namespaces=REP):
        code = m.get("code")
        if code and code.startswith("cvc-"):
            code = "XSD"
        msgs.add((code, m.get("level")))
    return acc, msgs

def main():
    jar, files = sys.argv[1], sys.argv[2:]
    ok = True
    for f in files:
        ja, jm = java(jar, f)
        r = validate(Path(f).read_bytes())
        pm = {(m.code, m.level) for m in r.messages}
        # XSD messages: compare only presence, texts differ between Xerces and libxml2
        same = ja == r.accepted and pm == jm
        ok &= same
        print(f"{'OK ' if same else 'DIFF'} {Path(f).name}: java={'accept' if ja else 'reject'} "
              f"python={'accept' if r.accepted else 'reject'}")
        print("     codes:", sorted(c for c, _ in pm if c != 'XSD'), "XSD" if ('XSD','error') in pm else "")
        if not same:
            print("     only java:", sorted(jm - pm)); print("     only python:", sorted(pm - jm))
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
