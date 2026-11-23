# Status

Ziel: Kostenloser, quelloffener E-Rechnung-Konverter (PDF zu ZUGFeRD EN 16931, optional XRechnung) als
einzelne Windows-.exe, Kommandozeile und Python-Paket, mit Pflicht-Prüfformular und KoSIT-Prüfung ohne Java.

Stand 23.11.2026 (Version 0.1.0):
- Exe gebaut und auf der fiktiven Musterrechnung getestet, auch per Gegenprobe mit dem
  Java-KoSIT-Validator 1.6.3 (gleiches Ergebnis, gleiche Regelcodes in 11 Testdateien).
- Alles für Anwender auf Deutsch, neutrales eigenes Symbol, keine Firmenlogos.
- Repository vorbereitet für GitHub (README, AGENTS.md, llms.txt, Tests- und Release-Workflow).
- Noch nicht veröffentlicht.

Offen:
- Veröffentlichung auf GitHub, erstes Release v0.1.0 mit der .exe.
- Test mit weiteren Rechnungsvorlagen.
- PDF/A-Konformität wird nicht geprüft; Empfehlung ist der PDF/A-Export aus Word.
- Nicht unterstützt: 0 % USt, Reverse Charge, Rabatte, Gutschriften, andere Layouts.
