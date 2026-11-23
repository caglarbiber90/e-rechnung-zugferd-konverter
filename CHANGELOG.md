# Änderungen

## 0.1.0 (23.11.2026)

Erste Version.

- Windows-Programm als einzelne `.exe`: PDF-Rechnung wählen (auch per Ziehen und Ablegen), Angaben
  im Pflicht-Prüfformular kontrollieren, E-Rechnung erzeugen.
- ZUGFeRD 2.x / Factur-X, Profil EN 16931 (PDF mit eingebettetem `factur-x.xml`), optional XRechnung 3.0 (CII).
- Rechenprüfung (Positionen, Netto, Umsatzsteuer, Brutto) vor dem Erzeugen.
- Prüfung nach dem KoSIT-Regelwerk XRechnung 3.0.2 (2026-09-02) ohne Java, mit HTML-Prüfbericht;
  Ergebnisse gleich wie beim offiziellen Java-Validator 1.6.3.
- Verständliche deutsche Erklärungen für häufige Prüfregeln.
- Stammdaten für Rechnungssteller und Kunden.
- Erkennung von PDF/A mit Hinweis auf den PDF/A-Export aus Word.
- Kommandozeile `auslesen`, `erstellen`, `pruefen` mit JSON-Ausgabe für Automatisierung und KI-Agenten.
