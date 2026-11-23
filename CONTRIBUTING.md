# Mitmachen

Danke für Ihr Interesse! Beiträge aller Art sind willkommen: Fehlermeldungen, neue Rechnungsvorlagen,
bessere Erklärungen von Prüfregeln, Tests und Code.

## Wichtigste Regel: keine echten Daten

Bitte **niemals** echte Rechnungen, Kundennamen, Adressen, IBANs, Steuernummern oder USt-IdNrn.
hochladen, auch nicht in Fehlermeldungen oder Bildschirmfotos. Erfundene Beispieldaten nach dem Muster
von `tools/make_sample.py` verwenden.

## Fehler melden

Unter [Issues](https://github.com/caglarbiber90/e-rechnung-zugferd-konverter/issues) bitte angeben:

- Version (unten links im Programmfenster),
- was Sie getan haben und was passiert ist,
- die Regelcodes aus dem Prüfbericht (z. B. `BR-CO-15`), falls vorhanden.

## Neue Rechnungsvorlage

1. Erfundene Musterrechnung im Layout der Vorlage erzeugen (siehe `tools/make_sample.py`).
2. In `src/erechnung/extract.py` eine Klasse mit `matches(text)` und `extract(text)` anlegen und in
   `EXTRACTORS` eintragen.
3. Test in `tests/` ergänzen, `py -3 -m pytest -q` ausführen.

## Entwicklung

```powershell
py -3 -m pip install --user -e ".[dev]"
py -3 -m pytest -q
```

- Code und Kommentare auf Englisch, alles für Anwender auf Deutsch.
- Keine AGPL-Pakete (z. B. PyMuPDF), damit der Code unter MIT bleibt.
- Die KoSIT-Konfiguration (`src/erechnung/daten/kosit/`) nur als Ganzes aus einem offiziellen Release
  aktualisieren und danach die Gegenprobe `tools/compare_java.py` laufen lassen.
