"""
LNO Calculator GUI
Interactive GUI for Lithium Nickel Oxide battery material calculations.
Run with: python lno_gui.py  OR  python -m lno_gui
"""

import tkinter as tk
from tkinter import ttk, messagebox, font
import sys
import os

# Add parent dir to path if running directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lno_calculator import (
    calculate_precursor,
    calculate_li_source,
    parse_formula,
    calculate_molar_mass,
    ELEMENT_MOLAR_MASS,
)

# ─── Color Palette ────────────────────────────────────────────────────────────
BG        = "#0f1117"
BG2       = "#1a1d27"
BG3       = "#22263a"
ACCENT    = "#5b8dee"
ACCENT2   = "#38d9a9"
WARN      = "#ffd166"
ERROR     = "#ef476f"
TEXT      = "#e8ecf4"
TEXT_DIM  = "#7a82a0"
BORDER    = "#2e3352"
SUCCESS   = "#06d6a0"

FONT_MONO = ("Consolas", 10)
FONT_BODY = ("Segoe UI", 10)
FONT_H1   = ("Segoe UI Semibold", 15)
FONT_H2   = ("Segoe UI Semibold", 11)
FONT_LABEL= ("Segoe UI", 9)
FONT_SMALL= ("Consolas", 9)


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(self.tip, text=self.text, bg="#2e3352", fg=TEXT,
                       font=FONT_SMALL, relief="flat", padx=8, pady=4,
                       wraplength=300, justify="left")
        lbl.pack()

    def hide(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


class LabeledEntry(tk.Frame):
    def __init__(self, parent, label, default="", tooltip=None,
                 width=28, hint=None, **kwargs):
        super().__init__(parent, bg=BG2, **kwargs)
        self.label_text = label

        lbl_row = tk.Frame(self, bg=BG2)
        lbl_row.pack(fill="x")
        tk.Label(lbl_row, text=label, bg=BG2, fg=TEXT_DIM,
                 font=FONT_LABEL).pack(side="left")
        if hint:
            tk.Label(lbl_row, text=hint, bg=BG2, fg=ACCENT,
                     font=FONT_SMALL).pack(side="right")

        self.var = tk.StringVar(value=default)
        self.entry = tk.Entry(self, textvariable=self.var,
                              bg=BG3, fg=TEXT, insertbackground=ACCENT,
                              relief="flat", font=FONT_MONO, width=width,
                              highlightthickness=1,
                              highlightbackground=BORDER,
                              highlightcolor=ACCENT)
        self.entry.pack(fill="x", pady=(2, 0))

        if tooltip:
            ToolTip(self.entry, tooltip)

    def get(self):
        return self.var.get().strip()

    def set(self, val):
        self.var.set(val)


class SectionFrame(tk.LabelFrame):
    def __init__(self, parent, title, **kwargs):
        super().__init__(parent, text=f"  {title}  ",
                         bg=BG2, fg=ACCENT, font=FONT_H2,
                         relief="flat", bd=1,
                         highlightbackground=BORDER,
                         highlightthickness=1,
                         padx=12, pady=10, **kwargs)


class ResultBox(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG3, relief="flat",
                         highlightbackground=BORDER,
                         highlightthickness=1, **kwargs)
        self.text = tk.Text(self, bg=BG3, fg=TEXT, font=FONT_MONO,
                            relief="flat", state="disabled",
                            wrap="word", height=14,
                            selectbackground=ACCENT,
                            padx=10, pady=8)
        scroll = ttk.Scrollbar(self, orient="vertical",
                               command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.text.pack(fill="both", expand=True)

        # Configure tags
        self.text.tag_configure("header",  foreground=ACCENT,  font=("Segoe UI Semibold", 11))
        self.text.tag_configure("value",   foreground=ACCENT2, font=("Consolas", 10, "bold"))
        self.text.tag_configure("label",   foreground=TEXT_DIM, font=FONT_SMALL)
        self.text.tag_configure("warn",    foreground=WARN)
        self.text.tag_configure("error",   foreground=ERROR,   font=("Consolas", 10, "bold"))
        self.text.tag_configure("success", foreground=SUCCESS, font=("Consolas", 10, "bold"))
        self.text.tag_configure("dim",     foreground=TEXT_DIM)
        self.text.tag_configure("sep",     foreground=BORDER)

    def clear(self):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")

    def append(self, line, tag=""):
        self.text.configure(state="normal")
        if tag:
            self.text.insert("end", line + "\n", tag)
        else:
            self.text.insert("end", line + "\n")
        self.text.configure(state="disabled")
        self.text.see("end")

    def write_result(self, lines):
        """lines: list of (text, tag) tuples"""
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        for text, tag in lines:
            if tag:
                self.text.insert("end", text + "\n", tag)
            else:
                self.text.insert("end", text + "\n")
        self.text.configure(state="disabled")
        self.text.see("1.0")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LNO Calculator  ·  Battery Material Synthesis")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(860, 700)

        self._build_header()
        self._build_notebook()
        self._build_status()

        self.update_idletasks()
        w, h = 960, 820
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=BG, pady=14)
        hdr.pack(fill="x", padx=20)

        tk.Label(hdr, text="⬡  LNO Calculator",
                 bg=BG, fg=ACCENT, font=("Segoe UI Semibold", 18)).pack(side="left")
        tk.Label(hdr, text="Battery Material Synthesis Tool",
                 bg=BG, fg=TEXT_DIM, font=("Segoe UI", 10)).pack(side="left", padx=16, pady=4)

        tk.Label(hdr, text="v1.0", bg=BG, fg=BORDER,
                 font=FONT_SMALL).pack(side="right")

        sep = tk.Frame(self, bg=BORDER, height=1)
        sep.pack(fill="x", padx=20)

    # ── Notebook (tabs) ───────────────────────────────────────────────────────
    def _build_notebook(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Custom.TNotebook",
                        background=BG, borderwidth=0, tabmargins=[0, 4, 0, 0])
        style.configure("Custom.TNotebook.Tab",
                        background=BG2, foreground=TEXT_DIM,
                        padding=[18, 8], font=("Segoe UI", 10),
                        borderwidth=0)
        style.map("Custom.TNotebook.Tab",
                  background=[("selected", BG3)],
                  foreground=[("selected", ACCENT)])

        self.nb = ttk.Notebook(self, style="Custom.TNotebook")
        self.nb.pack(fill="both", expand=True, padx=12, pady=8)

        self._tab_precursor()
        self._tab_li_source()
        self._tab_formula_tool()

    # ── Tab 1: Precursor ──────────────────────────────────────────────────────
    def _tab_precursor(self):
        frame = tk.Frame(self.nb, bg=BG)
        self.nb.add(frame, text="① Ni Precursor")

        pane = tk.Frame(frame, bg=BG)
        pane.pack(fill="both", expand=True, padx=16, pady=12)

        # LEFT: inputs
        left = tk.Frame(pane, bg=BG)
        left.pack(side="left", fill="y", padx=(0, 12))

        sec1 = SectionFrame(left, "Chemical Formulas")
        sec1.pack(fill="x", pady=(0, 10))

        self.e_spent = LabeledEntry(sec1, "Spent Powder Formula",
            default="Li0.7Ni0.63Co0.15Mn0.19O2",
            tooltip="Enter the full chemical formula of spent cathode powder.\nExample: Li0.7Ni0.63Co0.15Mn0.19O2",
            hint="e.g. Li0.7Ni0.63Co0.15Mn0.19O2")
        self.e_spent.pack(fill="x", pady=4)

        self.e_precursor = LabeledEntry(sec1, "Ni Precursor Formula",
            default="Ni(OH)2",
            tooltip="Enter the Ni source precursor formula.\nExample: Ni(OH)2",
            hint="e.g. Ni(OH)2")
        self.e_precursor.pack(fill="x", pady=4)

        sec2 = SectionFrame(left, "Target & Batch")
        sec2.pack(fill="x", pady=(0, 10))

        self.e_ni_pct = LabeledEntry(sec2, "Target Ni %  (e.g. 83 = 83%)",
            default="83",
            tooltip="Target nickel percentage in the final mixed Ni-rich powder.\nExample: 83 means 83% Ni among transition metals")
        self.e_ni_pct.pack(fill="x", pady=4)

        tk.Label(sec2, text="Batch mass — enter ONE, leave the other blank:",
                 bg=BG2, fg=TEXT_DIM, font=FONT_LABEL).pack(anchor="w", pady=(8, 2))

        row = tk.Frame(sec2, bg=BG2)
        row.pack(fill="x")
        self.e_spent_mass = LabeledEntry(row, "Spent Powder Mass (g)",
            default="", width=14,
            tooltip="Mass of spent powder in grams. Leave blank if using Precursor mass as basis.")
        self.e_spent_mass.pack(side="left", padx=(0, 8))

        self.e_prec_mass = LabeledEntry(row, "Precursor Mass (g)",
            default="", width=14,
            tooltip="Mass of Ni precursor in grams. Leave blank if using Spent Powder mass as basis.")
        self.e_prec_mass.pack(side="left")

        # Calculate button
        btn = tk.Button(left, text="▶  Calculate Precursor",
                        bg=ACCENT, fg="white", font=("Segoe UI Semibold", 11),
                        relief="flat", padx=16, pady=8, cursor="hand2",
                        activebackground="#4a7de0", activeforeground="white",
                        command=self._calc_precursor)
        btn.pack(fill="x", pady=12)

        # RIGHT: results
        right = tk.Frame(pane, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        tk.Label(right, text="Results", bg=BG, fg=TEXT_DIM,
                 font=FONT_H2).pack(anchor="w", pady=(0, 6))
        self.res_prec = ResultBox(right)
        self.res_prec.pack(fill="both", expand=True)

        # Pre-fill with placeholder
        self.res_prec.write_result([
            ("Fill in the formulas and press Calculate.", "dim"),
            ("", ""),
        ])

    # ── Tab 2: Li Source ──────────────────────────────────────────────────────
    def _tab_li_source(self):
        frame = tk.Frame(self.nb, bg=BG)
        self.nb.add(frame, text="② Li Source")

        pane = tk.Frame(frame, bg=BG)
        pane.pack(fill="both", expand=True, padx=16, pady=12)

        left = tk.Frame(pane, bg=BG)
        left.pack(side="left", fill="y", padx=(0, 12))

        sec1 = SectionFrame(left, "Li Source")
        sec1.pack(fill="x", pady=(0, 10))

        self.e_li_formula = LabeledEntry(sec1, "Li Source Formula",
            default="LiOH*H2O",
            tooltip="Li source chemical formula.\nExamples: LiOH·H2O  or  LiOH*H2O  or  Li2CO3",
            hint="e.g. LiOH*H2O or Li2CO3")
        self.e_li_formula.pack(fill="x", pady=4)

        self.e_li_ratio = LabeledEntry(sec1, "Target Li/Ni Stoichiometry",
            default="1.05",
            tooltip="Final Li stoichiometry relative to Ni.\nExample: 1.05 means Li:Ni = 1.05:1")
        self.e_li_ratio.pack(fill="x", pady=4)

        sec2 = SectionFrame(left, "Batch")
        sec2.pack(fill="x", pady=(0, 10))

        self.e_ni_rich_new = LabeledEntry(sec2, "Ni-rich Powder Mass (g)",
            default="100",
            tooltip="How much final Ni-rich mixed powder (spent + precursor) you want to process.")
        self.e_ni_rich_new.pack(fill="x", pady=4)

        tk.Label(sec2,
                 text="※ Run Tab ① first to set spent & precursor masses.",
                 bg=BG2, fg=WARN, font=FONT_SMALL).pack(anchor="w", pady=(6, 0))

        btn = tk.Button(left, text="▶  Calculate Li Source",
                        bg=ACCENT2, fg=BG, font=("Segoe UI Semibold", 11),
                        relief="flat", padx=16, pady=8, cursor="hand2",
                        activebackground="#2bc49a", activeforeground=BG,
                        command=self._calc_li_source)
        btn.pack(fill="x", pady=12)

        right = tk.Frame(pane, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        tk.Label(right, text="Results", bg=BG, fg=TEXT_DIM,
                 font=FONT_H2).pack(anchor="w", pady=(0, 6))
        self.res_li = ResultBox(right)
        self.res_li.pack(fill="both", expand=True)

        self.res_li.write_result([
            ("Complete Tab ① first, then fill in Li source details.", "dim"),
        ])

    # ── Tab 3: Formula Tool ───────────────────────────────────────────────────
    def _tab_formula_tool(self):
        frame = tk.Frame(self.nb, bg=BG)
        self.nb.add(frame, text="⚗  Formula Tool")

        pane = tk.Frame(frame, bg=BG)
        pane.pack(fill="both", expand=True, padx=16, pady=12)

        sec = SectionFrame(pane, "Parse & Inspect Chemical Formula")
        sec.pack(fill="x")

        self.e_formula_check = LabeledEntry(sec, "Chemical Formula",
            default="",
            tooltip="Enter any formula to parse and show element breakdown + molar mass.",
            hint="e.g. LiNi0.8Co0.1Mn0.1O2")
        self.e_formula_check.pack(fill="x", pady=4)

        btn = tk.Button(sec, text="Parse Formula",
                        bg=BG3, fg=ACCENT, font=FONT_BODY,
                        relief="flat", padx=12, pady=6, cursor="hand2",
                        highlightbackground=ACCENT, highlightthickness=1,
                        command=self._parse_formula_tool)
        btn.pack(anchor="w", pady=8)

        tk.Label(pane, text="Parsed Result", bg=BG, fg=TEXT_DIM,
                 font=FONT_H2).pack(anchor="w", pady=(12, 4))
        self.res_formula = ResultBox(pane)
        self.res_formula.pack(fill="both", expand=True)

        # Show element table on the right
        self._build_element_table(pane)

    def _build_element_table(self, parent):
        lf = SectionFrame(parent, "Supported Elements & Molar Masses")
        lf.pack(fill="x", pady=(12, 0))

        cols = 4
        items = sorted(ELEMENT_MOLAR_MASS.items())
        for i, (el, mm) in enumerate(items):
            r, c = divmod(i, cols)
            cell = tk.Frame(lf, bg=BG3, padx=8, pady=4)
            cell.grid(row=r, column=c, padx=3, pady=2, sticky="ew")
            tk.Label(cell, text=el, bg=BG3, fg=ACCENT,
                     font=("Consolas", 10, "bold"), width=3).pack(side="left")
            tk.Label(cell, text=f"{mm:.3f}", bg=BG3, fg=TEXT_DIM,
                     font=FONT_SMALL).pack(side="left", padx=4)
        for c in range(cols):
            lf.columnconfigure(c, weight=1)

    # ── Status bar ────────────────────────────────────────────────────────────
    def _build_status(self):
        sep = tk.Frame(self, bg=BORDER, height=1)
        sep.pack(fill="x")
        bar = tk.Frame(self, bg=BG, pady=6)
        bar.pack(fill="x", padx=16)
        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(bar, textvariable=self.status_var, bg=BG,
                 fg=TEXT_DIM, font=FONT_SMALL).pack(side="left")

    def _set_status(self, msg, color=TEXT_DIM):
        self.status_var.set(msg)

    # ── Calculation: Precursor ─────────────────────────────────────────────────
    def _calc_precursor(self):
        spent_f  = self.e_spent.get()
        prec_f   = self.e_precursor.get()
        ni_pct_s = self.e_ni_pct.get()
        spent_ms = self.e_spent_mass.get()
        prec_ms  = self.e_prec_mass.get()

        if not spent_f or not prec_f or not ni_pct_s:
            messagebox.showwarning("Missing Input",
                "Please fill in Spent Powder, Precursor formula, and Target Ni %.")
            return

        try:
            ni_pct = float(ni_pct_s)
        except ValueError:
            messagebox.showerror("Input Error", "Target Ni % must be a number.")
            return

        spent_mass = float(spent_ms) if spent_ms else None
        prec_mass  = float(prec_ms)  if prec_ms  else None

        if spent_mass is None and prec_mass is None:
            spent_mass = 1.0  # default basis

        try:
            r = calculate_precursor(spent_f, prec_f, ni_pct, spent_mass, prec_mass)
        except Exception as e:
            self.res_prec.write_result([
                ("⚠  Calculation Error", "error"),
                ("", ""),
                (str(e), "warn"),
            ])
            self._set_status(f"Error: {e}")
            return

        # Store for Li tab
        self._precursor_result = r

        lines = []
        lines.append(("━" * 52, "dim"))
        lines.append(("  PRECURSOR (Ni SOURCE) CALCULATION", "header"))
        lines.append(("━" * 52, "dim"))
        lines.append(("", ""))

        lines.append(("  Spent Powder", "label"))
        lines.append((f"    Formula:    {spent_f}", ""))
        lines.append((f"    Molar Mass: {r.molar_mass_spent:.4f} g/mol", ""))
        compo = "  ".join(f"{el}: {v:.4f}" for el, v in r.formula_spent.items())
        lines.append((f"    Elements:   {compo}", "dim"))
        lines.append(("", ""))

        lines.append(("  Ni Precursor", "label"))
        lines.append((f"    Formula:    {prec_f}", ""))
        lines.append((f"    Molar Mass: {r.molar_mass_precursor:.4f} g/mol", ""))
        compo2 = "  ".join(f"{el}: {v:.4f}" for el, v in r.formula_precursor.items())
        lines.append((f"    Elements:   {compo2}", "dim"))
        lines.append(("", ""))

        lines.append(("━" * 52, "dim"))
        lines.append(("  RESULTS", "header"))
        lines.append(("━" * 52, "dim"))
        lines.append(("", ""))
        lines.append((f"  Ratio:  1 g Spent Powder  →  {r.precursor_mass_per_g:.5f} g Precursor", ""))
        lines.append(("", ""))
        lines.append(("  Batch Calculation:", "label"))
        lines.append((f"    Spent Powder:    {r.spent_powder_mass:.4f} g", "value"))
        lines.append((f"    Ni Precursor:    {r.precursor_mass:.4f} g", "value"))
        lines.append((f"    Ni-rich Total:   {r.spent_powder_mass + r.precursor_mass:.4f} g", "value"))
        lines.append(("", ""))
        lines.append((f"  Target Ni%:  {ni_pct:.2f}%  ✓", "success"))
        lines.append(("", ""))
        lines.append(("  → Now go to Tab ② to calculate Li source.", "dim"))

        self.res_prec.write_result(lines)
        self._set_status(f"✓  Precursor calculated. Spent: {r.spent_powder_mass:.3f}g  Precursor: {r.precursor_mass:.3f}g")

    # ── Calculation: Li Source ─────────────────────────────────────────────────
    def _calc_li_source(self):
        if not hasattr(self, '_precursor_result'):
            messagebox.showwarning("Missing Data",
                "Please run Tab ① (Ni Precursor) first.")
            return

        li_f     = self.e_li_formula.get()
        li_rat_s = self.e_li_ratio.get()
        ni_new_s = self.e_ni_rich_new.get()

        if not li_f or not li_rat_s or not ni_new_s:
            messagebox.showwarning("Missing Input",
                "Please fill in all Li source fields.")
            return

        try:
            li_ratio = float(li_rat_s)
            ni_new   = float(ni_new_s)
        except ValueError:
            messagebox.showerror("Input Error", "Li ratio and batch mass must be numbers.")
            return

        try:
            r = calculate_li_source(self._precursor_result, li_f, li_ratio, ni_new)
            li_mm = calculate_molar_mass(parse_formula(li_f))
        except Exception as e:
            self.res_li.write_result([
                ("⚠  Calculation Error", "error"),
                ("", ""),
                (str(e), "warn"),
            ])
            self._set_status(f"Error: {e}")
            return

        pr = self._precursor_result
        lines = []
        lines.append(("━" * 52, "dim"))
        lines.append(("  Li SOURCE CALCULATION", "header"))
        lines.append(("━" * 52, "dim"))
        lines.append(("", ""))

        lines.append(("  Li Source", "label"))
        lines.append((f"    Formula:    {li_f}", ""))
        lines.append((f"    Molar Mass: {li_mm:.4f} g/mol", ""))
        lines.append((f"    Target Li/Ni ratio: {li_ratio:.4f}", ""))
        lines.append(("", ""))

        lines.append(("  Reference Batch (from Tab ①):", "label"))
        lines.append((f"    Spent Powder:  {pr.spent_powder_mass:.4f} g", ""))
        lines.append((f"    Ni Precursor:  {pr.precursor_mass:.4f} g", ""))
        lines.append((f"    Ni-rich Total: {r.ni_rich_mass:.4f} g", ""))
        lines.append(("", ""))

        lines.append(("━" * 52, "dim"))
        lines.append(("  RESULTS", "header"))
        lines.append(("━" * 52, "dim"))
        lines.append(("", ""))
        lines.append((f"  Li Source per g Ni-rich:  {r.li_source_mass_per_ni_rich:.5f} g/g", ""))
        lines.append(("", ""))
        lines.append(("  Scale to Target Batch:", "label"))
        lines.append((f"    Target Ni-rich Mass:  {ni_new:.4f} g", ""))
        lines.append((f"    Li Source Required:   {r.add_li_source_mass_per_target:.4f} g", "value"))
        lines.append(("", ""))
        lines.append(("  Summary:", "label"))
        lines.append((f"    {r.ni_rich_mass_new:.4f} g Ni-rich  +  {r.add_li_source_mass_per_target:.4f} g {li_f}", "success"))
        lines.append(("", ""))
        lines.append((f"  ✓  Li/Ni = {li_ratio:.4f}  achieved", "success"))

        self.res_li.write_result(lines)
        self._set_status(f"✓  Li source: {r.add_li_source_mass_per_target:.4f} g for {ni_new:.1f}g batch")

    # ── Formula Tool ──────────────────────────────────────────────────────────
    def _parse_formula_tool(self):
        formula = self.e_formula_check.get()
        if not formula:
            return
        try:
            parsed = parse_formula(formula)
            mm     = calculate_molar_mass(parsed)
        except Exception as e:
            self.res_formula.write_result([
                ("⚠  Parse Error", "error"),
                ("", ""),
                (str(e), "warn"),
            ])
            return

        lines = []
        lines.append(("━" * 44, "dim"))
        lines.append((f"  Formula: {formula}", "header"))
        lines.append(("━" * 44, "dim"))
        lines.append(("", ""))
        lines.append(("  Elements:", "label"))
        for el, ratio in sorted(parsed.items()):
            mm_el = ELEMENT_MOLAR_MASS.get(el, 0)
            contrib = mm_el * ratio
            lines.append((
                f"    {el:<4}  ×{ratio:.4f}  =  {contrib:.4f} g/mol  "
                f"({contrib/mm*100:.2f}%)",
                ""
            ))
        lines.append(("", ""))
        lines.append((f"  Total Molar Mass:  {mm:.4f} g/mol", "value"))

        self.res_formula.write_result(lines)


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
