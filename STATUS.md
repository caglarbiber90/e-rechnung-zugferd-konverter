# Status

Ziel: Kostenloser, quelloffener E-Rechnung-Konverter (PDF zu ZUGFeRD EN 16931, optional XRechnung) als
einzelne Windows-.exe, Kommandozeile und Python-Paket, mit Pflicht-Prüfformular und KoSIT-Prüfung ohne Java.

Stand 23.11.2026 (Version 0.1.1):
- Exe gebaut und auf der fiktiven Musterrechnung getestet, auch per Gegenprobe mit dem
  Java-KoSIT-Validator 1.6.3 (gleiches Ergebnis, gleiche Regelcodes in 11 Testdateien).
- Alles für Anwender auf Deutsch, neutrales eigenes Symbol, keine Firmenlogos.
- Veröffentlicht am 23.11.2026: github.com/caglarbiber90/e-rechnung-zugferd-konverter, Release v0.1.0
  mit der in GitHub Actions gebauten .exe (Selbsttest im Workflow bestanden).

Offen:
- Bekanntmachen (Foren, LinkedIn, Listen); Texte vorbereiten, Çağlar veröffentlicht selbst.
- Test mit weiteren Rechnungsvorlagen.
- PDF/A-Konformität wird nicht geprüft; Empfehlung ist der PDF/A-Export aus Word.
- Nicht unterstützt: 0 % USt, Reverse Charge, Rabatte, Gutschriften, andere Layouts.
