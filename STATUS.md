# Status

Ziel: Eine einzelne Windows-.exe, die eine Word-PDF-Rechnung in eine ZUGFeRD-E-Rechnung
(Profil EN 16931) umwandelt, mit Pflicht-Prüfformular und KoSIT-Prüfung ohne Java.

Stand 23.11.2026 (Version 0.1.0):
- Exe gebaut und auf der fiktiven Musterrechnung getestet, auch per Gegenprobe mit dem
  Java-KoSIT-Validator 1.6.3 (gleiches Ergebnis, gleiche Regelcodes).
- Oberfläche auf Deutsch, warme Farbpalette (Akzent Terrakotta); Firmenlogo nur im lokalen Ordner branding/.
- Noch nicht öffentlich auf GitHub.

Offen:
- Antwort der Buchhaltung: Werden die Rechnungen in Word oder in einem Rechnungsprogramm geschrieben?
- Test mit echten Büro-Rechnungen (nur lokal, nie einchecken).
- PDF/A-Konformität wird nicht geprüft; Empfehlung ist der PDF/A-Export aus Word.
- Nicht unterstützt: 0 % USt, Reverse Charge, Rabatte, Gutschriften, andere Layouts.
