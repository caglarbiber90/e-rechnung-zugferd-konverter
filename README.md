# E-Rechnung-Konverter

Ein kleines Windows-Programm, das eine fertige PDF-Rechnung in eine **E-Rechnung nach ZUGFeRD 2.x
(Profil EN 16931)** umwandelt: Das PDF bleibt für Menschen lesbar, die Rechnungsdaten werden
zusätzlich als maschinenlesbares XML (`factur-x.xml`, Syntax UN/CEFACT CII) eingebettet.

- **Eine einzige `.exe`**: doppelklicken, Rechnung umwandeln, schließen.
- Keine Installation, keine Administratorrechte, kein Python und kein Java auf dem Zielrechner nötig.
- Alle Daten bleiben auf dem eigenen Rechner. Es wird nichts ins Internet gesendet.
- Prüfung nach dem amtlichen **KoSIT-Regelwerk** (XRechnung 3.0.2, enthält die EN-16931-Regeln),
  bevor eine Datei gespeichert wird.

## Warum?

Ab dem **1. Januar 2027** müssen Unternehmen mit mehr als 800.000 EUR Vorjahresumsatz im
Geschäftsverkehr mit anderen Unternehmen (B2B) E-Rechnungen nach EN 16931 ausstellen, ab dem
**1. Januar 2028** alle Unternehmen. Ein normales PDF aus Word reicht dann nicht mehr. ZUGFeRD im
Profil EN 16931 (oder höher) erfüllt die Anforderung; die Profile MINIMUM und BASIC WL nicht.

Wer seine Rechnungen bisher in Word schreibt, kann mit diesem Programm weiterarbeiten: Rechnung wie
gewohnt als PDF speichern, dann mit dem Konverter in eine E-Rechnung umwandeln.

## Bedienung

1. **PDF-Rechnung wählen**: Datei auswählen, in das Fenster ziehen oder direkt auf die `.exe` ziehen.
2. **Angaben prüfen**: Das Programm liest Rechnungsnummer, Datum, Leistungszeitraum, Empfänger,
   Bestellnummer, PSP-Element, Projekt, Positionen und Beträge aus dem PDF und zeigt alles in einem
   Formular. **Diese Prüfung ist Pflicht und wird nie übersprungen**: Wenn PDF und XML voneinander
   abweichen, gilt rechtlich das XML.
3. **Prüfen und erzeugen**: Das Programm rechnet nach (Positionen = Netto, Netto + USt = Brutto),
   erzeugt das XML, prüft es nach dem KoSIT-Regelwerk und speichert nur bei bestandener Prüfung:

   - `<Name>_E-Rechnung.pdf` (ZUGFeRD-Rechnung, neben dem Original)
   - `<Name>_E-Rechnung_Pruefbericht.html` (Prüfbericht)
   - optional `<Name>_XRechnung.xml` (nur für öffentliche Auftraggeber nötig)

   Fehler werden in einfachem Deutsch angezeigt, zum Beispiel „Die Bruttosumme ist nicht Netto +
   Umsatzsteuer (Regel BR-CO-15)“.

### Stammdaten

Beim ersten Start fragt das Programm einmalig die Daten des eigenen Büros ab (Name, Anschrift,
USt-IdNr., Steuernummer, Handelsregister, Ansprechpartner, IBAN, BIC). Kunden werden mit ihrer
Käuferreferenz gespeichert, sobald eine Rechnung für sie erzeugt wurde, und füllen beim nächsten Mal
das Formular vor. Alles liegt in einer JSON-Datei unter
`%APPDATA%\E-Rechnung-Konverter\stammdaten.json`.

### PDF/A

ZUGFeRD sieht als Trägerformat PDF/A-3 vor. Der normale PDF-Export von Word erzeugt **kein** PDF/A.
Das Programm erkennt das und weist darauf hin. Empfehlung: in Word *Speichern unter > PDF >
Optionen > „PDF/A-kompatibel“* wählen. Die erzeugte Datei trägt (wie bei der Bibliothek `factur-x`
üblich) die Kennzeichnung PDF/A-3B; ob sie wirklich PDF/A-konform ist, prüft das Programm **nicht**
(dafür wäre z. B. veraPDF nötig). Das eingebettete XML ist davon unabhängig gültig.

### Grenzen der Version 0.1

- Das Auslesen ist auf eine Word-Rechnungsvorlage abgestimmt („HONORARRECHNUNG Nr. …, Projekt: …“
  mit Feldern wie `Bestellnummer:`, `PSP:`, `Leistungsempfänger:`). Andere Layouts werden nicht
  erkannt; dann sind alle Felder von Hand auszufüllen. Neue Vorlagen lassen sich in
  `src/erechnung/extract.py` ergänzen (Liste `EXTRACTORS`).
- Nur Normalsteuersatz-Rechnungen (Kategorie S, z. B. 19 % oder 7 %). Steuerfreie Leistungen,
  Reverse Charge, Rabatte/Zuschläge auf Belegebene und Gutschriften werden noch nicht unterstützt.
- Eingescannte PDFs ohne Text können nicht ausgelesen werden.

## Prüfung ohne Java

Der offizielle KoSIT-Validator ist ein Java-Programm. Damit die `.exe` ohne Java auskommt, führt der
Konverter **dieselben Prüfdateien** direkt aus:

1. XML-Schema (CII D16B) mit `lxml`,
2. die vorkompilierten Schematron-Stylesheets der KoSIT-Konfiguration (EN 16931 CII und ggf.
   XRechnung CII) mit Saxon-HE (`saxonche`),
3. die Bewertungsregel des KoSIT-Berichts (`customLevel`-Anpassungen aus `scenarios.xml`;
   abgelehnt, sobald eine Meldung der Stufe „Fehler“ vorliegt).

Gleichwertigkeit wurde mit dem Java-Validator 1.6.3 und derselben Konfiguration geprüft
(`tools/compare_java.py`): Für die fiktive Musterrechnung und absichtlich fehlerhafte Varianten
liefern beide Prüfungen dasselbe Ergebnis und dieselben Regelcodes.

| Variante | Ergebnis (beide) | Regelcodes |
|---|---|---|
| gültig (EN 16931 und XRechnung) | bestanden | keine |
| falsche Bruttosumme | nicht bestanden | BR-CO-15, BR-CO-16 |
| leere IBAN | nicht bestanden | BR-50 (+ bei XRechnung PEPPOL-EN16931-R008, BR-DE-19) |
| fehlende Käuferreferenz (XRechnung) | nicht bestanden | BR-DE-15 |
| falscher XML-Aufbau | nicht bestanden | Schemafehler |

## Selbst bauen

Voraussetzungen: Windows, Python 3.12 oder neuer.

```powershell
py -3 -m pip install --user -r requirements-dev.txt
py -3 tools/make_sample.py          # fiktive Musterrechnung + Musterstammdaten
py -3 -m pytest -q tests            # Tests
py -3 -m PyInstaller --noconfirm erechnung.spec
```

Ergebnis: `dist\E-Rechnung-Konverter.exe` (ca. 70 MB, der größte Teil ist Saxon-HE).

Prüfen der fertigen `.exe` ohne Oberfläche (schreibt `selftest.log` neben das PDF):

```powershell
dist\E-Rechnung-Konverter.exe --selftest tests\sample\Musterrechnung.pdf tests\sample\stammdaten.json
```

Gegenprobe mit dem Java-Validator (Java 17 und die
[KoSIT-Validator-Datei](https://github.com/itplr-kosit/validator/releases) nötig):

```powershell
py -3 tools/write_variants.py build\varianten
py -3 tools/compare_java.py <Pfad>\validator-1.6.3-standalone.jar build\varianten\*.xml
```

### Eigenes Erscheinungsbild (optional)

Ohne weitere Dateien zeigt das Programm ein neutrales Zeichen. Ein eigenes Logo und eine eigene
Wortmarke für den internen Gebrauch lassen sich vor dem Bauen erzeugen; der Ordner `branding/` ist
von Git ausgeschlossen:

```powershell
py -3 -m pip install --user pillow
py -3 tools/make_branding.py <logo.png> "FIRMENNAME"
```

## Projektaufbau

| Datei | Aufgabe |
|---|---|
| `src/erechnung/extract.py` | Felder aus dem PDF-Text lesen (erweiterbar) |
| `src/erechnung/cii.py` | CII-XML erzeugen (EN 16931, optional XRechnung 3.0) |
| `src/erechnung/checks.py` | Rechenprüfung vor dem Erzeugen |
| `src/erechnung/validator.py` | KoSIT-Prüfung ohne Java |
| `src/erechnung/pdf.py` | PDF/A-Erkennung, Einbetten mit `factur-x` |
| `src/erechnung/gui.py` | Oberfläche (tkinter) |
| `resources/kosit/` | KoSIT-Prüfkonfiguration XRechnung 3.0.2 (2026-09-02), unverändert |

## Lizenz

Der eigene Code steht unter der [MIT-Lizenz](LICENSE). Die mitgelieferten Fremdbestandteile
(KoSIT-Konfiguration, EN-16931-Schematron, Saxon-HE, factur-x, pypdf, lxml u. a.) haben eigene
Lizenzen, siehe [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

Alle Namen, Adressen, Steuernummern und Bankdaten in `tests/sample/` sind erfunden.

Dieses Programm ersetzt keine steuerliche Beratung. Bitte jede erzeugte Rechnung vor dem Versand
prüfen.
