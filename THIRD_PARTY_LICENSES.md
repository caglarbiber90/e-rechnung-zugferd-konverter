# Fremdbestandteile und Lizenzen

Die fertige `E-Rechnung-Konverter.exe` enthält die folgenden Bestandteile. Der eigene Code steht
unter der MIT-Lizenz (`LICENSE`).

| Bestandteil | Verwendung | Lizenz |
|---|---|---|
| KoSIT validator-configuration-xrechnung 3.0.2 (2026-09-02), `resources/kosit/` | Prüfszenarien, XRechnung-Schematron | Apache License 2.0 |
| EN-16931-Schematron 1.3.16 (CEN / ConnectingEurope), in der KoSIT-Konfiguration enthalten | Prüfregeln EN 16931 | European Union Public Licence (EUPL) 1.2 |
| UN/CEFACT CII D16B XML-Schema, in der KoSIT-Konfiguration enthalten | Schemaprüfung | UN/CEFACT, frei verwendbar |
| Saxon-HE (SaxonC-HE, Python-Paket `saxonche`), Saxonica | XSLT-Prozessor für die Schematron-Prüfung | Mozilla Public License 2.0 |
| `factur-x` (Akretion, Alexis de Lattre) | XML in PDF einbetten | BSD-Lizenz |
| `pypdf` | PDF-Text lesen, Metadaten | BSD-3-Clause |
| `lxml` (enthält libxml2/libxslt) | XML, Schemaprüfung | BSD-3-Clause (libxml2: MIT) |
| `python-stdnum` (Abhängigkeit von factur-x) | Prüfung von Kennnummern | GNU LGPL 2.1 oder neuer |
| `iso4217` (Abhängigkeit von factur-x) | Währungscodes | Public Domain |
| `requests` (Abhängigkeit von factur-x) | wird nicht genutzt, nur mitgeladen | Apache License 2.0 |
| `windnd` | Dateien ins Fenster ziehen | MIT |
| Python 3 mit tkinter (Tcl/Tk) | Laufzeit und Oberfläche | PSF License, Tcl/Tk-Lizenz (BSD-artig) |
| PyInstaller (Bootloader) | Erzeugung der einzelnen `.exe` | GPL 2.0 mit Ausnahme für erzeugte Programme |

Hinweise:

- Bewusst **nicht** verwendet: PyMuPDF (AGPL), damit der Code unter MIT stehen kann.
- LGPL- und MPL-Bestandteile liegen unverändert vor; ihr Quelltext ist bei den jeweiligen Projekten
  erhältlich. In der `.exe` werden sie beim Start in einen temporären Ordner entpackt und können dort
  ersetzt werden.
- Ein eventuell eingebundenes Firmenlogo (`branding/`) ist nicht Teil dieses Repositoriums und
  unterliegt den Rechten seines Inhabers.
