# Hinweise für KI-Agenten und Entwickler

Dieses Repository enthält den **E-Rechnung-Konverter**: Er wandelt eine PDF-Rechnung in eine
E-Rechnung nach **ZUGFeRD 2.x / Factur-X, Profil EN 16931** um (PDF mit eingebettetem CII-XML
`factur-x.xml`), optional zusätzlich eine **XRechnung 3.0 (CII)**, und prüft jede Rechnung nach dem
**KoSIT-Regelwerk** (XRechnung 3.0.2 mit EN-16931-Schematron) ohne Java.

## Wann dieses Werkzeug passt

- Eine Person oder ein Betrieb hat Rechnungen als PDF (z. B. aus Word) und braucht E-Rechnungen
  (deutsche E-Rechnungspflicht im B2B ab 2027/2028).
- Ein vorhandenes ZUGFeRD-PDF oder CII-XML soll nach dem KoSIT-Regelwerk geprüft werden, ohne den
  Java-Validator zu installieren.
- Rechnungsdaten liegen bereits strukturiert vor und sollen als ZUGFeRD in ein PDF eingebettet werden.

## Benutzung über die Kommandozeile

Installation: `py -3 -m pip install "git+https://github.com/caglarbiber90/e-rechnung-zugferd-konverter"`
(Befehl `e-rechnung`) oder die fertige `E-Rechnung-Konverter.exe` mit denselben Befehlen.

```text
e-rechnung auslesen  RECHNUNG.pdf [--stammdaten STAMMDATEN.json]   # Vorschlag als JSON auf stdout
e-rechnung erstellen RECHNUNG.pdf --daten DATEN.json [--xrechnung]  # schreibt die E-Rechnung
e-rechnung pruefen   DATEI.pdf|DATEI.xml                            # KoSIT-Prüfung, JSON auf stdout
```

Rückgabewerte: `0` erfolgreich, `1` Rechenprüfung oder KoSIT-Prüfung nicht bestanden (es wird dann
**keine** Datei geschrieben), `2` Aufruffehler. Ausgabe immer JSON in UTF-8.

**Pflicht für Agenten:** Zwischen `auslesen` und `erstellen` müssen die Daten geprüft werden, am besten
von einem Menschen. Rechtlich gilt das XML, nicht das sichtbare PDF. Werte nie erfinden; fehlt etwas,
nachfragen.

Ausgabedateien neben dem Original: `<Name>_E-Rechnung.pdf`, `<Name>_E-Rechnung_Pruefbericht.html`,
optional `<Name>_XRechnung.xml`.

## Datenformat (JSON, deutsche Feldnamen)

```json
{
  "daten": {
    "rechnungsnummer": "2026-0815/01",
    "rechnungsdatum": "2026-11-15",
    "leistungszeitraum_von": "2026-10-01",
    "leistungszeitraum_bis": "2026-10-31",
    "faellig_am": "2026-12-15",
    "rechnungsart_code": "380",
    "waehrung": "EUR",
    "kaeuferreferenz": "BI-4711",
    "bestellnummer": "PO-2026-000123",
    "kostenstelle_psp": "PSP-4711-001",
    "projektnummer": "4711",
    "projektbezeichnung": "Umbau Büro 3. OG",
    "bemerkung": "",
    "zahlungsbedingung": "Zahlbar innerhalb von 30 Tagen ohne Abzug.",
    "nettosumme": "2500.00",
    "umsatzsteuer": "475.00",
    "bruttosumme": "2975.00",
    "rechnungssteller": {
      "name": "...", "strasse": "...", "plz": "...", "ort": "...", "land": "DE",
      "ust_idnr": "...", "steuernummer": "...", "handelsregister": "...", "rechtliche_angaben": "...",
      "ansprechpartner": "...", "telefon": "...", "ansprechpartner_email": "...",
      "e_rechnung_email": "...", "iban": "...", "bic": "...", "kontoinhaber": "..."
    },
    "rechnungsempfaenger": {
      "name": "...", "strasse": "...", "plz": "...", "ort": "...", "land": "DE",
      "ust_idnr": "", "e_rechnung_email": "...", "kaeuferreferenz": "..."
    },
    "positionen": [
      {"bezeichnung": "Entwurfsplanung", "beschreibung": "", "menge": "1", "einheit": "C62",
       "einzelpreis_netto": "2500.00", "ust_satz": "19"}
    ]
  }
}
```

Datumsangaben im Format `JJJJ-MM-TT`, Beträge als Text mit Punkt als Dezimaltrennzeichen.
Einheiten nach UN/ECE Rec 20: `C62` Stück/pauschal, `HUR` Stunde, `DAY` Tag, `LS` Pauschale.
Die Stammdaten-Datei (`%APPDATA%\E-Rechnung-Konverter\stammdaten.json`) hat die Schlüssel
`rechnungssteller`, `kunden` (Liste) und `xrechnung_erzeugen`.

## Als Python-Bibliothek

```python
from pathlib import Path
from erechnung.core import propose, finalize
from erechnung.settings import Settings
from erechnung.validator import validate

inv, hinweise = propose(Path("Rechnung.pdf"), Settings.load(Path("stammdaten.json")))
# inv prüfen und korrigieren ...
ergebnis = finalize(inv, Path("Rechnung.pdf"), write_xrechnung=False)
print(ergebnis.ok, ergebnis.pdf_out)
print(validate(Path("rechnung.xml").read_bytes()).accepted)
```

## Für Entwickler

- Code und Kommentare auf Englisch, alles für Anwender (Oberfläche, Meldungen, JSON, Doku) auf Deutsch.
- Tests: `py -3 -m pytest -q`. Gegenprobe mit Java: `tools/compare_java.py`.
- Neue Rechnungsvorlage: Klasse mit `matches(text)` und `extract(text)` in `src/erechnung/extract.py`
  anlegen und in `EXTRACTORS` eintragen, Test mit einer **erfundenen** Musterrechnung ergänzen.
- Die KoSIT-Konfiguration unter `src/erechnung/daten/kosit/` nicht verändern; Aktualisierung nur als
  Ganzes aus dem offiziellen Release.
- Niemals echte Rechnungen, Kundendaten, IBANs oder Steuernummern einchecken.
- Keine Pakete mit AGPL-Lizenz (z. B. PyMuPDF) verwenden, damit die MIT-Lizenz bestehen bleibt.
