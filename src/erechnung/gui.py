"""tkinter user interface (German): light sidebar, warm terracotta accent."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import tkinter as tk
import traceback
from dataclasses import fields
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import __version__
from .checks import computed_totals, fmt
from .core import finalize, output_paths, propose
from .messages_de import explain
from .model import Buyer, Invoice, Line, Seller
from .resources import resource_path
from .settings import Settings, settings_path

APP = "E-Rechnung-Konverter"

# palette
BG = "#ffffff"
SIDE = "#fafaf8"
INK = "#1e2126"
MUTED = "#6a6f77"
LINE = "#e6e5e1"
LINE_INPUT = "#8c9096"
ACCENT = "#bd5a31"
ACCENT_HOVER = "#a34a26"
ACCENT_SOFT = "#f8f0ea"
ACCENT_TEXT = "#9a4522"
OK, OK_BG = "#2f7045", "#e6f2ea"
WARN_INK, WARN_BG = "#8a5300", "#fdf3dc"
ERR_BG = "#fbeae5"
SURFACE2 = "#fafaf8"
FONT = "Segoe UI"

SELLER_FIELDS = [
    ("name", "Firmenname *"), ("street", "Straße und Hausnummer *"), ("zip", "PLZ *"), ("city", "Ort *"),
    ("country", "Land *"), ("vat_id", "USt-IdNr."), ("tax_no", "Steuernummer"),
    ("register_id", "Handelsregister (z. B. HRB 12345)"),
    ("legal_info", "Rechtliche Angaben (Geschäftsführung, Amtsgericht)"),
    ("contact", "Ansprechpartner"), ("phone", "Telefon"), ("contact_email", "E-Mail Ansprechpartner"),
    ("email", "E-Mail-Adresse für E-Rechnungen"), ("iban", "IBAN *"), ("bic", "BIC"),
    ("account_name", "Kontoinhaber"),
]
BUYER_FIELDS = [
    ("name", "Name *"), ("street", "Straße und Hausnummer *"), ("zip", "PLZ *"), ("city", "Ort *"),
    ("country", "Land *"), ("vat_id", "USt-IdNr. des Kunden"),
    ("email", "E-Mail-Adresse für E-Rechnungen des Kunden"),
]
INVOICE_FIELDS = [
    ("number", "Rechnungsnummer *"), ("issue_date", "Rechnungsdatum * (TT.MM.JJJJ)"),
    ("period_start", "Leistungszeitraum von"), ("period_end", "Leistungszeitraum bis"),
    ("due_date", "Fällig am"), ("payment_terms", "Zahlungsbedingung"),
    ("buyer_reference", "Käuferreferenz / Leitweg-ID"), ("order_ref", "Bestellnummer"),
    ("accounting_ref", "PSP-Element / Kostenstelle"), ("project_id", "Projektnummer"),
    ("project_name", "Projektbezeichnung"), ("note", "Bemerkung"),
]
DATE_FIELDS = {"issue_date", "period_start", "period_end", "due_date"}
UNITS = ["C62", "LS", "HUR", "DAY", "MON", "MTK", "MTR"]
STEPS = ["PDF-Rechnung wählen", "Angaben prüfen", "Ergebnis"]


def de_dec(s: str) -> Decimal:
    s = (s or "").strip().replace("€", "").replace(" ", "")
    if not s:
        return Decimal(0)
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    return Decimal(s)


def dec_de(d) -> str:
    q = Decimal(d)
    s = f"{q:,.2f}" if q == q.quantize(Decimal("0.01")) else f"{q:,}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def num_de(d) -> str:
    return format(Decimal(d).normalize(), "f").replace(".", ",")


def parse_date(s: str):
    s = (s or "").strip()
    if not s:
        return None
    for f in ("%d.%m.%Y", "%Y-%m-%d", "%d.%m.%y"):
        try:
            return datetime.strptime(s, f).date()
        except ValueError:
            pass
    raise ValueError(f"Datum nicht lesbar: „{s}“ (bitte TT.MM.JJJJ).")


def open_path(p: Path):
    try:
        os.startfile(str(p))  # type: ignore[attr-defined]
    except Exception:
        subprocess.Popen(["explorer", str(p)])


def setup_style(root: tk.Tk):
    st = ttk.Style(root)
    st.theme_use("clam")
    base = (FONT, 10)
    import tkinter.font as tkfont
    for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
        tkfont.nametofont(name).configure(family=FONT, size=10)
    st.configure(".", background=BG, foreground=INK, font=base, bordercolor=LINE,
                 focuscolor=ACCENT, troughcolor=LINE)
    st.configure("TFrame", background=BG)
    st.configure("Side.TFrame", background=SIDE)
    st.configure("Card.TFrame", background=BG, bordercolor=LINE, relief="solid", borderwidth=1)
    st.configure("TLabel", background=BG, foreground=INK)
    st.configure("Side.TLabel", background=SIDE, foreground=INK)
    st.configure("Muted.TLabel", foreground=MUTED, font=(FONT, 9))
    st.configure("SideMuted.TLabel", background=SIDE, foreground=MUTED, font=(FONT, 9))
    st.configure("SideTitle.TLabel", background=SIDE, foreground=MUTED, font=(FONT, 8, "bold"))
    st.configure("Mark.TLabel", background=SIDE, foreground=INK, font=(FONT, 12, "bold"))
    st.configure("H1.TLabel", font=(FONT, 15, "bold"))
    st.configure("H2.TLabel", font=(FONT, 11, "bold"))
    st.configure("Card.TLabel", background=BG)
    st.configure("TEntry", fieldbackground="#ffffff", bordercolor=LINE_INPUT, lightcolor=LINE_INPUT,
                 darkcolor=LINE_INPUT, padding=(8, 5), insertcolor=INK)
    st.map("TEntry", bordercolor=[("focus", ACCENT)], lightcolor=[("focus", ACCENT)],
           darkcolor=[("focus", ACCENT)])
    st.configure("TCombobox", fieldbackground="#ffffff", bordercolor=LINE_INPUT, lightcolor=LINE_INPUT,
                 darkcolor=LINE_INPUT, padding=(6, 4), arrowcolor=INK, background="#ffffff")
    st.map("TCombobox", bordercolor=[("focus", ACCENT)], fieldbackground=[("readonly", "#ffffff")])
    st.configure("TButton", background="#ffffff", foreground=INK, bordercolor=LINE_INPUT,
                 lightcolor="#ffffff", darkcolor="#ffffff", padding=(14, 7), font=(FONT, 10))
    st.map("TButton", background=[("active", "#f0efec"), ("disabled", "#e9e9e6")],
           foreground=[("disabled", MUTED)])
    st.configure("Accent.TButton", background=ACCENT, foreground="#ffffff", bordercolor=ACCENT,
                 lightcolor=ACCENT, darkcolor=ACCENT, font=(FONT, 10, "bold"), padding=(18, 9))
    st.map("Accent.TButton", background=[("active", ACCENT_HOVER), ("disabled", "#e9e9e6")],
           bordercolor=[("active", ACCENT_HOVER)], lightcolor=[("active", ACCENT_HOVER)],
           darkcolor=[("active", ACCENT_HOVER)], foreground=[("disabled", MUTED)])
    st.configure("Side.TButton", background=SIDE, bordercolor=LINE)
    st.configure("TCheckbutton", background=BG, foreground=INK, indicatorbackground="#ffffff",
                 indicatorforeground=ACCENT)
    st.map("TCheckbutton", background=[("active", BG)], indicatorbackground=[("selected", ACCENT)],
           indicatorforeground=[("selected", "#ffffff")])
    st.configure("TNotebook", background=BG, bordercolor=LINE, tabmargins=(0, 0, 0, 0))
    st.configure("TNotebook.Tab", background=BG, foreground=MUTED, bordercolor=LINE,
                 lightcolor=BG, padding=(16, 8), font=(FONT, 10))
    st.map("TNotebook.Tab", background=[("selected", ACCENT_SOFT)],
           foreground=[("selected", ACCENT_TEXT)], lightcolor=[("selected", ACCENT)],
           font=[("selected", (FONT, 10, "bold"))])
    st.configure("TLabelframe", background=BG, bordercolor=LINE)
    st.configure("TLabelframe.Label", background=BG, foreground=MUTED, font=(FONT, 9, "bold"))
    st.configure("Vertical.TScrollbar", background=SURFACE2, bordercolor=LINE, arrowcolor=MUTED)


class Form(ttk.Frame):
    """Label + entry grid bound to StringVars (optionally in two column pairs)."""

    WIDE = ("legal_info", "note", "payment_terms", "project_name", "name", "street")

    def __init__(self, master, spec, columns=1):
        super().__init__(master, padding=(16, 12))
        self.vars: dict[str, tk.StringVar] = {}
        per_col = -(-len(spec) // columns)
        for i, (key, label) in enumerate(spec):
            col, row = divmod(i, per_col)
            ttk.Label(self, text=label).grid(row=row, column=col * 2, sticky="w", pady=3,
                                             padx=(0 if col == 0 else 28, 12))
            v = tk.StringVar()
            width = (34 if columns > 1 else 64) if key in self.WIDE else (22 if columns > 1 else 36)
            ttk.Entry(self, textvariable=v, width=width).grid(row=row, column=col * 2 + 1, sticky="w", pady=3)
            self.vars[key] = v

    def get(self, key):
        return self.vars[key].get().strip()

    def set(self, key, value):
        self.vars[key].set("" if value is None else str(value))


class SettingsDialog(tk.Toplevel):
    def __init__(self, master, settings: Settings, first_run=False):
        super().__init__(master, background=BG)
        self.title("Stammdaten des Rechnungsstellers")
        self.settings = settings
        self.transient(master)
        ttk.Label(self, text="Stammdaten des Rechnungsstellers", style="H1.TLabel",
                  padding=(16, 14, 16, 0)).pack(anchor="w")
        intro = ("Willkommen. Bitte tragen Sie einmalig die Daten Ihres Büros ein. Sie werden gespeichert "
                 "und in jede E-Rechnung übernommen." if first_run else
                 "Diese Angaben werden in jede E-Rechnung übernommen.")
        ttk.Label(self, text=intro + " Felder mit * sind Pflicht.", style="Muted.TLabel", wraplength=620,
                  padding=(16, 4)).pack(anchor="w")
        self.form = Form(self, SELLER_FIELDS, columns=2)
        self.form.pack(fill="both", expand=True)
        for key, _ in SELLER_FIELDS:
            self.form.set(key, getattr(settings.seller, key))
        ttk.Label(self, style="Muted.TLabel", padding=(16, 0),
                  text=f"Gespeichert in: {settings_path()}").pack(anchor="w")
        bar = ttk.Frame(self, padding=16)
        bar.pack(fill="x")
        ttk.Button(bar, text="Speichern", style="Accent.TButton", command=self.save).pack(side="right")
        ttk.Button(bar, text="Abbrechen", command=self.destroy).pack(side="right", padx=8)
        self.grab_set()

    def save(self):
        s = Seller(**{k: self.form.get(k) for k, _ in SELLER_FIELDS})
        s.iban = s.iban.replace(" ", "").upper()
        s.country = (s.country or "DE").upper()
        self.settings.seller = s
        self.settings.save()
        self.destroy()


class LinesTable(ttk.Frame):
    COLS = [("name", "Bezeichnung *", 22), ("description", "Beschreibung", 28), ("quantity", "Menge", 6),
            ("unit", "Einheit", 5), ("price", "Einzelpreis netto", 11), ("vat_rate", "USt %", 5)]

    def __init__(self, master, on_change):
        super().__init__(master, padding=(16, 12))
        self.rows: list[dict[str, tk.StringVar]] = []
        self.widgets: list[list[tk.Widget]] = []
        self.on_change = on_change
        for c, (_, label, _w) in enumerate(self.COLS):
            ttk.Label(self, text=label, style="Muted.TLabel").grid(row=0, column=c, sticky="w", padx=2)
        ttk.Label(self, text="Betrag netto", style="Muted.TLabel").grid(row=0, column=len(self.COLS), sticky="e")
        bar = ttk.Frame(self)
        bar.grid(row=999, column=0, columnspan=8, sticky="w", pady=(8, 0))
        ttk.Button(bar, text="+ Position", command=lambda: self.add(Line())).pack(side="left")
        ttk.Button(bar, text="Letzte Position entfernen", command=self.remove_last).pack(side="left", padx=8)
        ttk.Label(bar, style="Muted.TLabel", text="Einheiten: C62 Stück/pauschal · LS Pauschale · "
                                                  "HUR Stunde · DAY Tag · MON Monat").pack(side="left", padx=8)

    def add(self, ln: Line):
        r = len(self.rows) + 1
        vars_, ws = {}, []
        vals = {"name": ln.name, "description": ln.description, "quantity": num_de(ln.quantity),
                "unit": ln.unit, "price": dec_de(ln.price), "vat_rate": num_de(ln.vat_rate)}
        for c, (key, _l, w) in enumerate(self.COLS):
            v = tk.StringVar(value=vals[key])
            v.trace_add("write", lambda *_: self.on_change())
            e = (ttk.Combobox(self, textvariable=v, width=w, values=UNITS) if key == "unit"
                 else ttk.Entry(self, textvariable=v, width=w))
            e.grid(row=r, column=c, sticky="we", padx=2, pady=2)
            vars_[key] = v
            ws.append(e)
        total = ttk.Label(self, text="", width=13, anchor="e")
        total.grid(row=r, column=len(self.COLS), sticky="e", padx=(6, 0))
        ws.append(total)
        self.rows.append(vars_)
        self.widgets.append(ws)
        self.on_change()

    def remove_last(self):
        if self.rows:
            for w in self.widgets.pop():
                w.destroy()
            self.rows.pop()
            self.on_change()

    def clear(self):
        while self.rows:
            self.remove_last()

    def lines(self) -> list[Line]:
        out = []
        for i, r in enumerate(self.rows, 1):
            try:
                out.append(Line(name=r["name"].get().strip(), description=r["description"].get().strip(),
                                quantity=de_dec(r["quantity"].get() or "1"),
                                unit=r["unit"].get().strip() or "C62",
                                price=de_dec(r["price"].get()), vat_rate=de_dec(r["vat_rate"].get() or "19")))
            except InvalidOperation:
                raise ValueError(f"Position {i}: Zahl nicht lesbar (Menge, Preis oder USt %).")
        return out

    def refresh_totals(self):
        for r, ws in zip(self.rows, self.widgets):
            try:
                ws[-1].configure(text=fmt(Line(quantity=de_dec(r["quantity"].get() or "1"),
                                               price=de_dec(r["price"].get())).net))
            except Exception:
                ws[-1].configure(text="?")


class Banner(tk.Frame):
    """Coloured message box (info / warn / ok / error)."""

    COLORS = {"info": ("#e6f0fa", "#1f4f80"), "warn": (WARN_BG, WARN_INK), "ok": (OK_BG, OK),
              "error": (ERR_BG, ACCENT_TEXT), "neutral": (SURFACE2, INK)}

    def __init__(self, master):
        super().__init__(master, background=SURFACE2, highlightthickness=1, highlightbackground=LINE)
        self.title = tk.Label(self, anchor="w", justify="left", font=(FONT, 10, "bold"), background=SURFACE2)
        self.title.pack(fill="x", padx=14, pady=(10, 2))
        self.body = tk.Label(self, anchor="w", justify="left", font=(FONT, 10), background=SURFACE2,
                             wraplength=820)
        self.body.pack(fill="x", padx=14, pady=(0, 10))

    def show(self, kind: str, title: str, lines: list[str]):
        bg, fg = self.COLORS[kind]
        self.configure(background=bg, highlightbackground=bg)
        self.title.configure(text=title, background=bg, foreground=fg)
        self.body.configure(text="\n".join(f"•  {x}" for x in lines), background=bg, foreground=INK)
        if lines:
            self.body.pack(fill="x", padx=14, pady=(0, 10))
        else:
            self.body.pack_forget()


class App(tk.Tk):
    def __init__(self, initial_pdf: str | None = None):
        super().__init__()
        self.title(APP)
        self.geometry("1180x800")
        self.minsize(980, 640)
        self.configure(background=BG)
        try:
            self.iconbitmap(default=str(resource_path("icon", "app.ico")))
        except Exception:
            pass
        setup_style(self)
        self.settings = Settings.load()
        self.pdf_path: Path | None = None
        self.last_outcome = None
        self.max_step = 0
        self._build()
        self.show_step(0)
        self._enable_drop()
        if not self.settings.seller.name:
            self.after(300, lambda: self.edit_settings(first_run=True))
        if initial_pdf:
            self.after(500, lambda: self.load_pdf(Path(initial_pdf)))

    # ---------- sidebar ----------
    def _build(self):
        side = ttk.Frame(self, style="Side.TFrame", width=250)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        tk.Frame(self, background=LINE, width=1).pack(side="left", fill="y")

        head = ttk.Frame(side, style="Side.TFrame", padding=(16, 18, 16, 14))
        head.pack(fill="x")
        self._logo = tk.PhotoImage(file=str(resource_path("icon", "logo.png")))
        tk.Label(head, image=self._logo, background=SIDE).pack(side="left")
        txt = ttk.Frame(head, style="Side.TFrame")
        txt.pack(side="left", padx=10)
        ttk.Label(txt, text="E-Rechnung", style="Mark.TLabel").pack(anchor="w")
        ttk.Label(txt, text="PDF zu ZUGFeRD", style="SideMuted.TLabel").pack(anchor="w")
        tk.Frame(side, background=LINE, height=1).pack(fill="x", padx=12)

        ttk.Label(side, text="ABLAUF", style="SideTitle.TLabel", padding=(20, 16, 0, 6)).pack(anchor="w")
        self.step_btns = []
        for i, name in enumerate(STEPS):
            f = tk.Frame(side, background=SIDE, cursor="hand2")
            f.pack(fill="x", padx=10, pady=1)
            num = tk.Label(f, text=str(i + 1), width=2, font=(FONT, 10, "bold"), background=SIDE)
            num.pack(side="left", padx=(8, 6), pady=8)
            lbl = tk.Label(f, text=name, anchor="w", font=(FONT, 10), background=SIDE)
            lbl.pack(side="left", fill="x", expand=True)
            for w in (f, num, lbl):
                w.bind("<Button-1>", lambda _e, i=i: self.show_step(i) if i <= self.max_step else None)
            self.step_btns.append((f, num, lbl))

        foot = ttk.Frame(side, style="Side.TFrame", padding=16)
        foot.pack(side="bottom", fill="x")
        ttk.Button(foot, text="Stammdaten …", style="Side.TButton",
                   command=self.edit_settings).pack(fill="x")
        ttk.Label(foot, style="SideMuted.TLabel", wraplength=210, justify="left",
                  text=f"Version {__version__}\nZUGFeRD 2.x · Profil EN 16931\nPrüfung nach KoSIT-Regelwerk "
                       "(XRechnung 3.0.2)").pack(anchor="w", pady=(12, 0))

        self.main = ttk.Frame(self)
        self.main.pack(side="left", fill="both", expand=True)
        self.pages = [self._page_choose(), self._page_review(), self._page_result()]

    def show_step(self, i: int):
        self.max_step = max(self.max_step, i)
        for p in self.pages:
            p.pack_forget()
        self.pages[i].pack(fill="both", expand=True)
        for j, (f, num, lbl) in enumerate(self.step_btns):
            active = j == i
            bg = ACCENT_SOFT if active else SIDE
            fg = ACCENT_TEXT if active else (INK if j <= self.max_step else MUTED)
            for w in (f, num, lbl):
                w.configure(background=bg)
            num.configure(foreground=fg)
            lbl.configure(foreground=fg, font=(FONT, 10, "bold" if active else "normal"))

    def _page(self, title, subtitle):
        p = ttk.Frame(self.main, padding=(28, 22, 28, 18))
        ttk.Label(p, text=title, style="H1.TLabel").pack(anchor="w")
        ttk.Label(p, text=subtitle, style="Muted.TLabel", wraplength=860, justify="left").pack(anchor="w",
                                                                                            pady=(2, 14))
        return p

    # ---------- page 1 ----------
    def _page_choose(self):
        p = self._page("PDF-Rechnung wählen",
                       "Aus einer fertigen PDF-Rechnung wird eine E-Rechnung im ZUGFeRD-Format: "
                       "das PDF bleibt lesbar, die Rechnungsdaten werden zusätzlich als XML eingebettet.")
        drop = tk.Frame(p, background=SURFACE2, highlightthickness=2, highlightbackground=LINE,
                        highlightcolor=LINE)
        drop.pack(fill="x", pady=(4, 18), ipady=34)
        tk.Label(drop, text="PDF-Datei hierher ziehen", font=(FONT, 14, "bold"), background=SURFACE2,
                 foreground=INK).pack(pady=(26, 4))
        tk.Label(drop, text="oder", font=(FONT, 10), background=SURFACE2, foreground=MUTED).pack()
        ttk.Button(drop, text="PDF-Datei auswählen …", style="Accent.TButton",
                   command=self.choose_pdf).pack(pady=(8, 10))
        self.file_lbl = tk.Label(drop, text="", font=(FONT, 9), background=SURFACE2, foreground=MUTED)
        self.file_lbl.pack()
        self.drop_zone = drop

        ttk.Label(p, text="So funktioniert es", style="H2.TLabel").pack(anchor="w", pady=(4, 6))
        for n, t in [("1", "Das Programm liest die Angaben aus dem PDF (Rechnungsnummer, Beträge, Empfänger …)."),
                     ("2", "Sie prüfen alle Angaben und korrigieren sie bei Bedarf. Rechtlich gilt das "
                           "eingebettete XML, deshalb ist diese Prüfung Pflicht."),
                     ("3", "Das Programm rechnet nach, prüft nach dem amtlichen KoSIT-Regelwerk und speichert "
                           "„<Name>_E-Rechnung.pdf“ und einen Prüfbericht neben dem Original.")]:
            row = ttk.Frame(p)
            row.pack(anchor="w", pady=3)
            tk.Label(row, text=n, width=2, font=(FONT, 9, "bold"), background=ACCENT_SOFT,
                     foreground=ACCENT_TEXT).pack(side="left", padx=(0, 10))
            ttk.Label(row, text=t, wraplength=780, justify="left").pack(side="left")
        return p

    # ---------- page 2 ----------
    def _page_review(self):
        p = self._page("Angaben prüfen",
                       "Bitte alle Felder prüfen und bei Bedarf korrigieren. Rechtlich gilt das XML in der "
                       "E-Rechnung, nicht das sichtbare PDF.")
        self.review_file = ttk.Label(p, text="", style="Muted.TLabel")
        self.review_file.pack(anchor="w", pady=(0, 8))
        self.notes = Banner(p)
        self.notes.pack(fill="x", pady=(0, 12))

        bottom = ttk.Frame(p)
        bottom.pack(side="bottom", fill="x", pady=(12, 0))
        ttk.Button(bottom, text="Zurück", command=lambda: self.show_step(0)).pack(side="left")
        self.xr_var = tk.BooleanVar(value=self.settings.write_xrechnung)
        ttk.Checkbutton(bottom, variable=self.xr_var,
                        text="Zusätzlich XRechnung-Datei erzeugen (nur für öffentliche Auftraggeber)"
                        ).pack(side="left", padx=16)
        self.go_btn = ttk.Button(bottom, text="Prüfen und E-Rechnung erzeugen", style="Accent.TButton",
                                 command=self.generate)
        self.go_btn.pack(side="right")
        self.status = ttk.Label(p, text="", style="Muted.TLabel")
        self.status.pack(side="bottom", anchor="e")

        nb = self.review_nb = ttk.Notebook(p)
        nb.pack(fill="both", expand=True)
        self.inv_form = Form(nb, INVOICE_FIELDS, columns=2)
        nb.add(self.inv_form, text="Rechnung")

        bf = ttk.Frame(nb)
        row = ttk.Frame(bf, padding=(16, 12, 16, 0))
        row.pack(fill="x")
        ttk.Label(row, text="Gespeicherten Kunden übernehmen:").pack(side="left")
        self.buyer_pick = ttk.Combobox(row, width=46, state="readonly")
        self.buyer_pick.pack(side="left", padx=8)
        self.buyer_pick.bind("<<ComboboxSelected>>", self.pick_buyer)
        self.buyer_form = Form(bf, BUYER_FIELDS)
        self.buyer_form.pack(fill="x")
        self.save_buyer = tk.BooleanVar(value=True)
        ttk.Checkbutton(bf, padding=(16, 4), variable=self.save_buyer,
                        text="Kunden mit Käuferreferenz in den Stammdaten speichern").pack(anchor="w")
        nb.add(bf, text="Rechnungsempfänger")

        pf = ttk.Frame(nb)
        self.lines = LinesTable(pf, self.update_totals)
        self.lines.pack(fill="x", anchor="n")
        sums = ttk.LabelFrame(pf, text="  SUMMEN LAUT PDF  ", padding=12)
        sums.pack(fill="x", padx=16, pady=12)
        self.sum_vars = {}
        for i, (k, lbl) in enumerate([("net_total", "Nettosumme"), ("vat_total", "Umsatzsteuer"),
                                      ("gross_total", "Bruttosumme")]):
            ttk.Label(sums, text=lbl).grid(row=i, column=0, sticky="w", pady=2)
            v = tk.StringVar()
            v.trace_add("write", lambda *_: self.update_totals())
            ttk.Entry(sums, textvariable=v, width=16, justify="right").grid(row=i, column=1, padx=10, pady=2)
            self.sum_vars[k] = v
        self.calc_lbl = tk.Label(sums, text="", justify="left", anchor="w", background=SURFACE2,
                                 foreground=INK, font=(FONT, 10), padx=12, pady=8)
        self.calc_lbl.grid(row=0, column=2, rowspan=3, sticky="nsw", padx=20)
        nb.add(pf, text="Positionen und Summen")

        sf = ttk.Frame(nb, padding=16)
        ttk.Label(sf, style="Muted.TLabel",
                  text="Diese Angaben stammen aus den Stammdaten. Ändern über „Stammdaten …“ links unten."
                  ).pack(anchor="w", pady=(0, 8))
        self.seller_lbl = ttk.Label(sf, justify="left")
        self.seller_lbl.pack(anchor="w")
        nb.add(sf, text="Rechnungssteller")
        self.refresh_seller()
        self.refresh_buyers()
        return p

    # ---------- page 3 ----------
    def _page_result(self):
        p = self._page("Ergebnis", "Ergebnis der Rechenprüfung und der Prüfung nach dem KoSIT-Regelwerk.")
        self.result_banner = Banner(p)
        self.result_banner.pack(fill="x", pady=(0, 12))
        self.result_notes = Banner(p)
        bar = ttk.Frame(p)
        bar.pack(side="bottom", fill="x")
        self.btn_back = ttk.Button(bar, text="Zurück zu den Angaben", command=lambda: self.show_step(1))
        self.btn_back.pack(side="left")
        self.btn_next = ttk.Button(bar, text="Nächste Rechnung", style="Accent.TButton",
                                   command=self.reset)
        self.btn_next.pack(side="right")
        self.btn_report = ttk.Button(bar, text="Prüfbericht öffnen",
                                     command=lambda: open_path(self.last_outcome.report_out))
        self.btn_folder = ttk.Button(bar, text="Ordner öffnen",
                                     command=lambda: open_path(self.last_outcome.pdf_out.parent))
        return p

    # ---------- helpers ----------
    def _enable_drop(self):
        try:
            import windnd

            def dropped(files):
                paths = [f.decode("mbcs") if isinstance(f, bytes) else f for f in files]
                pdfs = [x for x in paths if x.lower().endswith(".pdf")]
                if pdfs:
                    self.after(10, lambda: self.load_pdf(Path(pdfs[0])))
                else:
                    self.after(10, lambda: messagebox.showinfo(APP, "Bitte eine PDF-Datei ablegen."))
            windnd.hook_dropfiles(self, func=dropped)
        except Exception:
            pass

    def refresh_seller(self):
        s = self.settings.seller
        self.seller_lbl.configure(text="\n".join(
            f"{lbl.rstrip(' *')}:  {getattr(s, k) or '–'}" for k, lbl in SELLER_FIELDS))

    def refresh_buyers(self):
        self.buyer_pick.configure(values=[b.name for b in self.settings.buyers])

    def pick_buyer(self, _evt=None):
        b = self.settings.find_buyer(self.buyer_pick.get())
        if b:
            for k, _ in BUYER_FIELDS:
                self.buyer_form.set(k, getattr(b, k))
            if b.buyer_reference:
                self.inv_form.set("buyer_reference", b.buyer_reference)

    def edit_settings(self, first_run=False):
        dlg = SettingsDialog(self, self.settings, first_run)
        self.wait_window(dlg)
        self.refresh_seller()

    def choose_pdf(self):
        p = filedialog.askopenfilename(title="PDF-Rechnung wählen", filetypes=[("PDF-Dateien", "*.pdf")])
        if p:
            self.load_pdf(Path(p))

    def load_pdf(self, path: Path):
        if not path.exists() or path.suffix.lower() != ".pdf":
            messagebox.showerror(APP, f"Keine PDF-Datei: {path}")
            return
        try:
            inv, notes = propose(path, self.settings)
        except Exception as e:
            messagebox.showerror(APP, f"Das PDF konnte nicht gelesen werden:\n{e}")
            return
        self.pdf_path = path
        self.file_lbl.configure(text=f"Zuletzt gewählt: {path.name}")
        self.review_file.configure(text=f"Datei: {path}")
        self.fill(inv)
        warn = any(n.startswith("ACHTUNG") or "kein PDF/A" in n or "nicht" in n for n in notes)
        self.notes.show("warn" if warn else "info", "Hinweise zum gelesenen PDF", notes)
        self.status.configure(text="")
        self.show_step(1)

    def reset(self):
        self.pdf_path = None
        self.max_step = 0
        self.show_step(0)

    def fill(self, inv: Invoice):
        for k, _ in INVOICE_FIELDS:
            v = getattr(inv, k)
            self.inv_form.set(k, v.strftime("%d.%m.%Y") if k in DATE_FIELDS and v else v)
        for k, _ in BUYER_FIELDS:
            self.buyer_form.set(k, getattr(inv.buyer, k))
        self.lines.clear()
        for ln in inv.lines or [Line()]:
            self.lines.add(ln)
        for k in self.sum_vars:
            self.sum_vars[k].set(dec_de(getattr(inv, k)))

    def collect(self) -> Invoice:
        inv = Invoice()
        for k, _ in INVOICE_FIELDS:
            val = self.inv_form.get(k)
            setattr(inv, k, parse_date(val) if k in DATE_FIELDS else val)
        b = Buyer(**{k: self.buyer_form.get(k) for k, _ in BUYER_FIELDS})
        b.country = (b.country or "DE").upper()
        b.buyer_reference = inv.buyer_reference
        inv.buyer = b
        inv.seller = self.settings.seller
        inv.lines = self.lines.lines()
        try:
            for k, v in self.sum_vars.items():
                setattr(inv, k, de_dec(v.get()))
        except InvalidOperation:
            raise ValueError("Eine Summe ist keine gültige Zahl.")
        return inv

    def update_totals(self):
        if not hasattr(self, "calc_lbl"):
            return
        self.lines.refresh_totals()
        try:
            net, vat, gross = computed_totals(Invoice(lines=self.lines.lines()))
            ok = all(abs(de_dec(self.sum_vars[k].get()) - v) <= Decimal("0.01")
                     for k, v in (("net_total", net), ("vat_total", vat), ("gross_total", gross)))
            self.calc_lbl.configure(
                text=f"Aus den Positionen berechnet\nNetto {fmt(net)}   ·   USt {fmt(vat)}   ·   Brutto {fmt(gross)}\n"
                     + ("✓ stimmt mit den Summen laut PDF überein" if ok else "✗ weicht von den Summen laut PDF ab"),
                background=OK_BG if ok else ERR_BG)
        except Exception:
            self.calc_lbl.configure(text="Positionen oder Summen enthalten ungültige Zahlen.", background=ERR_BG)

    def generate(self):
        try:
            inv = self.collect()
        except ValueError as e:
            messagebox.showerror(APP, str(e))
            return
        out_pdf, _, _ = output_paths(self.pdf_path)
        if out_pdf.exists() and not messagebox.askyesno(APP, f"„{out_pdf.name}“ existiert bereits. Überschreiben?"):
            return
        if self.save_buyer.get() and inv.buyer.name:
            self.settings.upsert_buyer(Buyer(**{f.name: getattr(inv.buyer, f.name) for f in fields(Buyer)}))
        self.settings.write_xrechnung = self.xr_var.get()
        self.settings.save()
        self.refresh_buyers()
        self.go_btn.configure(state="disabled")
        self.status.configure(text="Prüfe nach dem KoSIT-Regelwerk und erzeuge die E-Rechnung … bitte warten.")
        holder = {}

        def work():
            try:
                holder["oc"] = finalize(inv, self.pdf_path, self.xr_var.get())
            except Exception as e:
                holder["err"] = f"{e}\n\n{traceback.format_exc(limit=3)}"

        t = threading.Thread(target=work, daemon=True)
        t.start()

        def poll():
            if t.is_alive():
                self.after(200, poll)
                return
            self.go_btn.configure(state="normal")
            self.status.configure(text="")
            self.show_outcome(holder)

        poll()

    def show_outcome(self, holder):
        for b in (self.btn_report, self.btn_folder):
            b.pack_forget()
        self.result_notes.pack_forget()
        if "err" in holder:
            self.result_banner.show("error", "Unerwarteter Fehler. Es wurde nichts gespeichert.", [holder["err"]])
        else:
            oc = self.last_outcome = holder["oc"]
            if oc.problems:
                self.result_banner.show("error", "Die Rechenprüfung hat Probleme gefunden. Es wurde nichts gespeichert.",
                                        oc.problems)
            elif not oc.ok:
                self.result_banner.show(
                    "error", "Die E-Rechnung hat die KoSIT-Prüfung nicht bestanden. Es wurde nichts gespeichert.",
                    [explain(m.code, m.text) for m in oc.result.errors])
            else:
                files = [f"E-Rechnung:  {oc.pdf_out}", f"Prüfbericht:  {oc.report_out}"]
                if oc.xr_out:
                    files.append(f"XRechnung:  {oc.xr_out}")
                self.result_banner.show("ok", "Fertig. Die E-Rechnung hat die KoSIT-Prüfung bestanden.", files)
                extra = list(oc.notes)
                if oc.result_xr is not None and not oc.result_xr.accepted:
                    extra += [explain(m.code, m.text) for m in oc.result_xr.errors]
                if extra:
                    self.result_notes.show("warn", "Bitte beachten", extra)
                    self.result_notes.pack(fill="x")
                self.btn_report.pack(side="right", padx=8)
                self.btn_folder.pack(side="right")
        self.show_step(2)


def main():
    pdf = next((a for a in sys.argv[1:] if a.lower().endswith(".pdf")), None)
    App(pdf).mainloop()
