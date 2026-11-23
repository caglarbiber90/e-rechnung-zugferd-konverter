"""Plain-German explanations for the most common KoSIT / EN 16931 rule codes."""

PLAIN = {
    "BR-01": "Die Spezifikationskennung fehlt (technischer Fehler im Werkzeug).",
    "BR-02": "Die Rechnungsnummer fehlt.",
    "BR-03": "Das Rechnungsdatum fehlt.",
    "BR-05": "Die Währung fehlt.",
    "BR-06": "Der Name des Rechnungsstellers fehlt (Stammdaten).",
    "BR-07": "Der Name des Rechnungsempfängers fehlt.",
    "BR-08": "Die Anschrift des Rechnungsstellers fehlt (Stammdaten).",
    "BR-09": "Das Land des Rechnungsstellers fehlt (Stammdaten).",
    "BR-10": "Die Anschrift des Rechnungsempfängers fehlt.",
    "BR-11": "Das Land des Rechnungsempfängers fehlt.",
    "BR-16": "Die Rechnung hat keine Position.",
    "BR-21": "Eine Position hat keine Nummer.",
    "BR-25": "Eine Position hat keine Bezeichnung.",
    "BR-49": "Die Zahlungsart fehlt.",
    "BR-50": "Die IBAN fehlt (Stammdaten des Rechnungsstellers).",
    "BR-CO-10": "Die Summe der Positionen stimmt nicht mit der Nettosumme überein.",
    "BR-CO-13": "Die steuerpflichtige Summe stimmt nicht.",
    "BR-CO-14": "Die Umsatzsteuer-Summe stimmt nicht mit der Steueraufschlüsselung überein.",
    "BR-CO-15": "Die Bruttosumme ist nicht Netto + Umsatzsteuer.",
    "BR-CO-16": "Der Zahlbetrag stimmt nicht mit der Bruttosumme überein.",
    "BR-CO-25": "Bei einem positiven Zahlbetrag muss ein Fälligkeitsdatum oder eine Zahlungsbedingung angegeben sein.",
    "BR-S-08": "Die Bemessungsgrundlage zum Steuersatz stimmt nicht mit den Positionen überein.",
    "BR-S-09": "Der Steuerbetrag zum Steuersatz ist falsch berechnet.",
    "BR-DE-1": "Zahlungsanweisungen fehlen.",
    "BR-DE-2": "Kontaktdaten des Rechnungsstellers fehlen (Stammdaten: Ansprechpartner, Telefon, E-Mail).",
    "BR-DE-3": "Der Ort des Rechnungsstellers fehlt (Stammdaten).",
    "BR-DE-4": "Die Postleitzahl des Rechnungsstellers fehlt (Stammdaten).",
    "BR-DE-5": "Der Ansprechpartner des Rechnungsstellers fehlt (Stammdaten).",
    "BR-DE-6": "Die Telefonnummer des Ansprechpartners fehlt (Stammdaten).",
    "BR-DE-7": "Die E-Mail-Adresse des Ansprechpartners fehlt (Stammdaten).",
    "BR-DE-8": "Der Ort des Rechnungsempfängers fehlt.",
    "BR-DE-9": "Die Postleitzahl des Rechnungsempfängers fehlt.",
    "BR-DE-15": "Die Käuferreferenz (Leitweg-ID oder Bestellzeichen des Kunden) fehlt. Für XRechnung ist sie Pflicht.",
    "BR-DE-16": "Steuernummer oder USt-IdNr. des Rechnungsstellers fehlt (Stammdaten).",
    "BR-DE-19": "Die IBAN ist ungültig.",
    "PEPPOL-EN16931-R008": "Ein Feld ist leer. Leere Felder sind in der E-Rechnung nicht erlaubt.",
    "PEPPOL-EN16931-R010": "Die elektronische Adresse (E-Mail) des Rechnungsempfängers fehlt.",
    "PEPPOL-EN16931-R020": "Die elektronische Adresse (E-Mail) des Rechnungsstellers fehlt (Stammdaten).",
    "XSD": "Der XML-Aufbau entspricht nicht dem Schema (technischer Fehler, bitte melden).",
}


def explain(code: str, original: str) -> str:
    plain = PLAIN.get(code)
    if plain:
        return f"{plain} (Regel {code})"
    return f"Prüfregel {code} ist nicht erfüllt. Originaltext des Regelwerks: {original}"
