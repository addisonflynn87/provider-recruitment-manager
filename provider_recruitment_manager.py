###############################################################################
# Program Name: Provider Recruitment Manager v2.0                            #
#                                                                             #
# Purpose:                                                                    #
#     Recruitment management tool for locating and tracking English-speaking  #
#     doctors, diagnostic facilities, and per diem locations in the           #
#     Asia/Pacific region for medical evaluation appointments.                #
#     Features: collapsible side panel, embedded map with 100-mile radius     #
#     circles, color-coded need levels, city search, per diem and diagnostic  #
#     facility tracking, bulk search, and Google search integration.          #
#                                                                             #
# Author: Addison Flynn                                                       #
#                                                                             #
# Date: 4/29/2026                                                             #
#                                                                             #
# Version: 2.0                                                                #
#                                                                             #
###############################################################################
 
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import webbrowser
import csv
import math
from datetime import datetime
 
try:
    import tkintermapview
    MAP_AVAILABLE = True
except ImportError:
    MAP_AVAILABLE = False
 
# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
DATA_FILE = "recruitment_data.json"
 
COUNTRIES = [
    "Philippines", "Thailand", "Singapore", "Australia",
    "New Zealand", "Guam", "American Samoa", "CNMI",
    "Japan", "South Korea"
]
 
SPECIALTIES = [
    "General Medical", "Ophthalmologist", "Audiologist",
    "Psychiatry", "Neurologist", "Dental"
]
 
RECORD_TYPES = ["Doctor", "Diagnostic Facility", "Per Diem"]
 
NEED_LEVELS = ["OSR", "High Need", "Medium Need", "Low Need"]
 
PRIORITY_OPTIONS = ["High", "Medium", "Low"]
 
STATUS_OPTIONS = ["Have Provider", "Need Provider"]
 
# Color coding for need levels
NEED_COLORS = {
    "OSR":         "#dc3545",   # Red   — highest urgency
    "High Need":   "#fd7e14",   # Orange
    "Medium Need": "#ffc107",   # Yellow
    "Low Need":    "#198754",   # Green — lowest urgency
}
 
NEED_FG = {
    "OSR":         "white",
    "High Need":   "white",
    "Medium Need": "#1a2332",
    "Low Need":    "white",
}
 
COUNTRY_COORDS = {
    "Philippines":    (12.8797,   121.7740),
    "Thailand":       (15.8700,   100.9925),
    "Singapore":      (1.3521,    103.8198),
    "Australia":      (-25.2744,  133.7751),
    "New Zealand":    (-40.9006,  174.8860),
    "Guam":           (13.4443,   144.7937),
    "American Samoa": (-14.2710, -170.1322),
    "CNMI":           (15.0979,   145.6739),
    "Japan":          (36.2048,   138.2529),
    "South Korea":    (35.9078,   127.7669),
}
 
MILES_TO_KM = 1.60934
RADIUS_MILES = 100
 
 
# ─────────────────────────────────────────────────────────────────────────────
# DATA MANAGER
# ─────────────────────────────────────────────────────────────────────────────
class DataManager:
    def __init__(self):
        self.RECORDS = []
        self.load_data()
 
    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as F:
                    self.RECORDS = json.load(F)
            except Exception:
                self.RECORDS = []
        else:
            self.RECORDS = []
 
    def save_data(self):
        with open(DATA_FILE, "w") as F:
            json.dump(self.RECORDS, F, indent=4)
 
    def add_record(self, RECORD):
        RECORD["id"] = datetime.now().strftime("%Y%m%d%H%M%S%f")
        RECORD["date_added"] = datetime.now().strftime("%Y-%m-%d")
        self.RECORDS.append(RECORD)
        self.save_data()
 
    def update_record(self, RECORD_ID, UPDATED):
        for I, R in enumerate(self.RECORDS):
            if R["id"] == RECORD_ID:
                UPDATED["id"] = RECORD_ID
                UPDATED["date_added"] = R.get("date_added", "")
                self.RECORDS[I] = UPDATED
                self.save_data()
                return
 
    def delete_record(self, RECORD_ID):
        self.RECORDS = [R for R in self.RECORDS if R["id"] != RECORD_ID]
        self.save_data()
 
    def search_records(self, TYPE_FILTER=None, COUNTRY_FILTER=None,
                       SPECIALTY_FILTER=None, STATUS_FILTER=None,
                       NEED_FILTER=None, CITY_FILTER=None, TEXT_FILTER=None):
        RESULTS = self.RECORDS
 
        if TYPE_FILTER and TYPE_FILTER != "All Types":
            RESULTS = [R for R in RESULTS if R.get("record_type") == TYPE_FILTER]
        if COUNTRY_FILTER and COUNTRY_FILTER != "All Countries":
            RESULTS = [R for R in RESULTS if R.get("country") == COUNTRY_FILTER]
        if SPECIALTY_FILTER and SPECIALTY_FILTER != "All Specialties":
            RESULTS = [R for R in RESULTS if R.get("specialty") == SPECIALTY_FILTER]
        if STATUS_FILTER and STATUS_FILTER != "All Statuses":
            RESULTS = [R for R in RESULTS if R.get("status") == STATUS_FILTER]
        if NEED_FILTER and NEED_FILTER != "All Need Levels":
            RESULTS = [R for R in RESULTS if R.get("need_level") == NEED_FILTER]
        if CITY_FILTER and CITY_FILTER.strip():
            CITY_LOWER = CITY_FILTER.strip().lower()
            RESULTS = [R for R in RESULTS if
                       CITY_LOWER in R.get("city", "").lower()]
        if TEXT_FILTER and TEXT_FILTER.strip():
            T = TEXT_FILTER.strip().lower()
            RESULTS = [R for R in RESULTS if
                       T in R.get("name", "").lower() or
                       T in R.get("clinic", "").lower() or
                       T in R.get("city", "").lower()]
        return RESULTS
 
    def export_csv(self, FILEPATH):
        if not self.RECORDS:
            return False
        FIELDS = ["record_type", "name", "specialty", "country", "city",
                  "status", "need_level", "priority", "phone", "email",
                  "clinic", "lat", "lon", "notes", "date_added"]
        with open(FILEPATH, "w", newline="", encoding="utf-8") as F:
            WRITER = csv.DictWriter(F, fieldnames=FIELDS, extrasaction="ignore")
            WRITER.writeheader()
            WRITER.writerows(self.RECORDS)
        return True
 
 
# ─────────────────────────────────────────────────────────────────────────────
# ADD / EDIT RECORD DIALOG
# ─────────────────────────────────────────────────────────────────────────────
class RecordDialog(tk.Toplevel):
    def __init__(self, PARENT, TITLE, RECORD=None):
        super().__init__(PARENT)
        self.title(TITLE)
        self.geometry("540x700")
        self.resizable(False, False)
        self.configure(bg="#1a2332")
        self.RESULT = None
        self.RECORD = RECORD or {}
        self._build_ui()
        self.grab_set()
        self.focus_set()
 
    def _build_ui(self):
        tk.Label(self, text=self.title(), font=("Segoe UI", 12, "bold"),
                 bg="#0d6efd", fg="white", pady=8).pack(fill="x")
 
        CANVAS = tk.Canvas(self, bg="#1a2332", highlightthickness=0)
        SCROLLBAR = ttk.Scrollbar(self, orient="vertical", command=CANVAS.yview)
        CANVAS.configure(yscrollcommand=SCROLLBAR.set)
        SCROLLBAR.pack(side="right", fill="y")
        CANVAS.pack(fill="both", expand=True)
 
        FRAME = tk.Frame(CANVAS, bg="#1a2332", padx=24, pady=10)
        CANVAS_WIN = CANVAS.create_window((0, 0), window=FRAME, anchor="nw")
 
        def on_configure(E):
            CANVAS.configure(scrollregion=CANVAS.bbox("all"))
            CANVAS.itemconfig(CANVAS_WIN, width=CANVAS.winfo_width())
 
        FRAME.bind("<Configure>", on_configure)
        CANVAS.bind("<Configure>", on_configure)
 
        def lbl(TEXT):
            tk.Label(FRAME, text=TEXT, font=("Segoe UI", 9, "bold"),
                     bg="#1a2332", fg="#adb5bd", anchor="w").pack(fill="x", pady=(8, 2))
 
        def entry_field(VAR):
            E = tk.Entry(FRAME, textvariable=VAR, font=("Segoe UI", 10),
                         bg="#2c3e50", fg="white", insertbackground="white",
                         relief="flat")
            E.pack(fill="x", pady=(0, 2))
            return E
 
        def combo_field(VAR, VALUES):
            C = ttk.Combobox(FRAME, textvariable=VAR, values=VALUES,
                              state="readonly", font=("Segoe UI", 10))
            C.pack(fill="x", pady=(0, 2))
            return C
 
        # Record Type
        lbl("Record Type *")
        self.TYPE_VAR = tk.StringVar(value=self.RECORD.get("record_type", RECORD_TYPES[0]))
        combo_field(self.TYPE_VAR, RECORD_TYPES)
 
        # Name
        lbl("Name *")
        self.NAME_VAR = tk.StringVar(value=self.RECORD.get("name", ""))
        entry_field(self.NAME_VAR)
 
        # Specialty (only relevant for doctors)
        lbl("Specialty")
        self.SPEC_VAR = tk.StringVar(value=self.RECORD.get("specialty", ""))
        combo_field(self.SPEC_VAR, [""] + SPECIALTIES)
 
        # Country
        lbl("Country *")
        self.COUNTRY_VAR = tk.StringVar(value=self.RECORD.get("country", COUNTRIES[0]))
        combo_field(self.COUNTRY_VAR, COUNTRIES)
 
        # City
        lbl("City / Region *")
        self.CITY_VAR = tk.StringVar(value=self.RECORD.get("city", ""))
        entry_field(self.CITY_VAR)
 
        # Clinic / Facility
        lbl("Clinic / Facility / Hotel Name")
        self.CLINIC_VAR = tk.StringVar(value=self.RECORD.get("clinic", ""))
        entry_field(self.CLINIC_VAR)
 
        # Phone
        lbl("Phone")
        self.PHONE_VAR = tk.StringVar(value=self.RECORD.get("phone", ""))
        entry_field(self.PHONE_VAR)
 
        # Email
        lbl("Email")
        self.EMAIL_VAR = tk.StringVar(value=self.RECORD.get("email", ""))
        entry_field(self.EMAIL_VAR)
 
        # Status
        lbl("Status *")
        self.STATUS_VAR = tk.StringVar(value=self.RECORD.get("status", STATUS_OPTIONS[0]))
        combo_field(self.STATUS_VAR, STATUS_OPTIONS)
 
        # Need Level
        lbl("Need Level *")
        self.NEED_VAR = tk.StringVar(value=self.RECORD.get("need_level", NEED_LEVELS[1]))
        NEED_CB = combo_field(self.NEED_VAR, NEED_LEVELS)
 
        # Need level color preview label
        self.NEED_COLOR_LBL = tk.Label(FRAME, text="", font=("Segoe UI", 8, "bold"),
                                        bg="#1a2332", fg="white", pady=3)
        self.NEED_COLOR_LBL.pack(fill="x")
 
        def update_need_preview(*args):
            VAL = self.NEED_VAR.get()
            COLOR = NEED_COLORS.get(VAL, "#1a2332")
            FG = NEED_FG.get(VAL, "white")
            self.NEED_COLOR_LBL.config(
                bg=COLOR, fg=FG,
                text=f"  ● {VAL}" if VAL else "")
 
        self.NEED_VAR.trace_add("write", update_need_preview)
        update_need_preview()
 
        # Priority
        lbl("Priority")
        self.PRIORITY_VAR = tk.StringVar(value=self.RECORD.get("priority", "Medium"))
        combo_field(self.PRIORITY_VAR, PRIORITY_OPTIONS)
 
        # Latitude / Longitude (for map pin)
        lbl("Latitude (for map pin — optional)")
        self.LAT_VAR = tk.StringVar(value=str(self.RECORD.get("lat", "")))
        entry_field(self.LAT_VAR)
 
        lbl("Longitude (for map pin — optional)")
        self.LON_VAR = tk.StringVar(value=str(self.RECORD.get("lon", "")))
        entry_field(self.LON_VAR)
 
        tk.Label(FRAME, text="💡 Tip: Search the location on Google Maps, right-click → copy coordinates",
                 font=("Segoe UI", 7), bg="#1a2332", fg="#6c757d",
                 wraplength=440, anchor="w").pack(fill="x")
 
        # Notes
        lbl("Notes")
        self.NOTES_TEXT = tk.Text(FRAME, font=("Segoe UI", 10), bg="#2c3e50",
                                   fg="white", insertbackground="white",
                                   relief="flat", height=4)
        self.NOTES_TEXT.pack(fill="x", pady=(0, 4))
        self.NOTES_TEXT.insert("1.0", self.RECORD.get("notes", ""))
 
        # Buttons
        BTN_FRAME = tk.Frame(FRAME, bg="#1a2332")
        BTN_FRAME.pack(fill="x", pady=10)
        tk.Button(BTN_FRAME, text="💾  Save", font=("Segoe UI", 10, "bold"),
                  bg="#0d6efd", fg="white", relief="flat", padx=16, pady=6,
                  cursor="hand2", command=self._save).pack(side="left", padx=4)
        tk.Button(BTN_FRAME, text="✖  Cancel", font=("Segoe UI", 10),
                  bg="#495057", fg="white", relief="flat", padx=16, pady=6,
                  cursor="hand2", command=self.destroy).pack(side="left", padx=4)
 
    def _save(self):
        if not self.NAME_VAR.get().strip():
            messagebox.showwarning("Missing Field", "Name is required.", parent=self)
            return
        if not self.CITY_VAR.get().strip():
            messagebox.showwarning("Missing Field", "City / Region is required.", parent=self)
            return
 
        LAT_VAL = None
        LON_VAL = None
        try:
            if self.LAT_VAR.get().strip():
                LAT_VAL = float(self.LAT_VAR.get().strip())
            if self.LON_VAR.get().strip():
                LON_VAL = float(self.LON_VAR.get().strip())
        except ValueError:
            messagebox.showwarning("Invalid Coordinates",
                                   "Latitude and Longitude must be numbers.", parent=self)
            return
 
        self.RESULT = {
            "record_type": self.TYPE_VAR.get(),
            "name":        self.NAME_VAR.get().strip(),
            "specialty":   self.SPEC_VAR.get(),
            "country":     self.COUNTRY_VAR.get(),
            "city":        self.CITY_VAR.get().strip(),
            "clinic":      self.CLINIC_VAR.get().strip(),
            "phone":       self.PHONE_VAR.get().strip(),
            "email":       self.EMAIL_VAR.get().strip(),
            "status":      self.STATUS_VAR.get(),
            "need_level":  self.NEED_VAR.get(),
            "priority":    self.PRIORITY_VAR.get(),
            "lat":         LAT_VAL,
            "lon":         LON_VAL,
            "notes":       self.NOTES_TEXT.get("1.0", "end").strip()
        }
        self.destroy()
 
 
# ─────────────────────────────────────────────────────────────────────────────
# BULK SEARCH DIALOG
# ─────────────────────────────────────────────────────────────────────────────
class BulkSearchDialog(tk.Toplevel):
    def __init__(self, PARENT):
        super().__init__(PARENT)
        self.title("Bulk Search — Multiple Countries & Specialties")
        self.geometry("520x560")
        self.resizable(False, False)
        self.configure(bg="#1a2332")
        self.RESULT = None
        self._build_ui()
        self.grab_set()
 
    def _build_ui(self):
        tk.Label(self, text="🔎  Bulk Search", font=("Segoe UI", 12, "bold"),
                 bg="#0d6efd", fg="white", pady=8).pack(fill="x")
 
        MAIN = tk.Frame(self, bg="#1a2332", padx=20, pady=10)
        MAIN.pack(fill="both", expand=True)
 
        def section(TEXT):
            tk.Label(MAIN, text=TEXT, font=("Segoe UI", 9, "bold"),
                     bg="#1a2332", fg="#adb5bd", anchor="w"
                     ).pack(fill="x", pady=(10, 4))
 
        def listbox_section(ITEMS):
            F = tk.Frame(MAIN, bg="#1a2332")
            F.pack(fill="x")
            LB = tk.Listbox(F, selectmode="multiple", height=6,
                             bg="#2c3e50", fg="white", font=("Segoe UI", 10),
                             relief="flat", activestyle="dotbox",
                             selectbackground="#0d6efd", exportselection=False)
            SB = ttk.Scrollbar(F, orient="vertical", command=LB.yview)
            LB.configure(yscrollcommand=SB.set)
            for ITEM in ITEMS:
                LB.insert("end", ITEM)
            LB.pack(side="left", fill="both", expand=True)
            SB.pack(side="right", fill="y")
            return LB
 
        section("Countries (Ctrl+Click for multiple):")
        self.COUNTRY_LB = listbox_section(COUNTRIES)
        tk.Button(MAIN, text="Select All Countries", font=("Segoe UI", 8),
                  bg="#343a40", fg="white", relief="flat", cursor="hand2",
                  command=lambda: self.COUNTRY_LB.select_set(0, "end")
                  ).pack(anchor="w", pady=2)
 
        section("Specialties (Ctrl+Click for multiple):")
        self.SPEC_LB = listbox_section(SPECIALTIES)
        tk.Button(MAIN, text="Select All Specialties", font=("Segoe UI", 8),
                  bg="#343a40", fg="white", relief="flat", cursor="hand2",
                  command=lambda: self.SPEC_LB.select_set(0, "end")
                  ).pack(anchor="w", pady=2)
 
        section("Record Types:")
        self.TYPE_LB = listbox_section(RECORD_TYPES)
        tk.Button(MAIN, text="Select All Types", font=("Segoe UI", 8),
                  bg="#343a40", fg="white", relief="flat", cursor="hand2",
                  command=lambda: self.TYPE_LB.select_set(0, "end")
                  ).pack(anchor="w", pady=2)
 
        BTN_F = tk.Frame(self, bg="#1a2332")
        BTN_F.pack(fill="x", padx=20, pady=10)
        tk.Button(BTN_F, text="🔎  Run Bulk Search", font=("Segoe UI", 10, "bold"),
                  bg="#0d6efd", fg="white", relief="flat", padx=16, pady=6,
                  cursor="hand2", command=self._run).pack(side="left", padx=4)
        tk.Button(BTN_F, text="✖  Cancel", font=("Segoe UI", 10),
                  bg="#495057", fg="white", relief="flat", padx=16, pady=6,
                  cursor="hand2", command=self.destroy).pack(side="left", padx=4)
 
    def _run(self):
        SEL_C = [COUNTRIES[I] for I in self.COUNTRY_LB.curselection()]
        SEL_S = [SPECIALTIES[I] for I in self.SPEC_LB.curselection()]
        SEL_T = [RECORD_TYPES[I] for I in self.TYPE_LB.curselection()]
        if not SEL_C and not SEL_S and not SEL_T:
            messagebox.showwarning("Nothing Selected",
                                   "Select at least one option.", parent=self)
            return
        self.RESULT = {
            "countries":   SEL_C or COUNTRIES,
            "specialties": SEL_S or SPECIALTIES,
            "types":       SEL_T or RECORD_TYPES
        }
        self.destroy()
 
 
# ─────────────────────────────────────────────────────────────────────────────
# MAP WINDOW
# ─────────────────────────────────────────────────────────────────────────────
class MapWindow(tk.Toplevel):
    def __init__(self, PARENT, DATA_MANAGER):
        super().__init__(PARENT)
        self.title("🗺️  Interactive Map — Asia/Pacific Provider Network")
        self.geometry("1100x720")
        self.configure(bg="#1a2332")
        self.DATA = DATA_MANAGER
        self.CIRCLE_REFS = []
        self.MARKER_REFS = []
        self._build_ui()
 
    def _build_ui(self):
        # Header
        tk.Label(self, text="🗺️  Interactive Provider Map — 100-Mile Radius Coverage",
                 font=("Segoe UI", 12, "bold"), bg="#0d6efd", fg="white",
                 pady=8).pack(fill="x")
 
        # Controls bar
        CTRL = tk.Frame(self, bg="#0d1b2a", pady=6)
        CTRL.pack(fill="x")
 
        tk.Label(CTRL, text="Jump to Country:",
                 font=("Segoe UI", 9), bg="#0d1b2a", fg="#adb5bd"
                 ).pack(side="left", padx=(10, 4))
 
        self.JUMP_VAR = tk.StringVar(value=COUNTRIES[0])
        JUMP_CB = ttk.Combobox(CTRL, textvariable=self.JUMP_VAR,
                                values=COUNTRIES, state="readonly", width=18)
        JUMP_CB.pack(side="left", padx=4)
 
        tk.Button(CTRL, text="Go", font=("Segoe UI", 9, "bold"),
                  bg="#0d6efd", fg="white", relief="flat", padx=10,
                  cursor="hand2", command=self._jump_to_country
                  ).pack(side="left", padx=4)
 
        tk.Label(CTRL, text="|", bg="#0d1b2a", fg="#495057"
                 ).pack(side="left", padx=6)
 
        tk.Button(CTRL, text="📍 Show All Pins", font=("Segoe UI", 9),
                  bg="#343a40", fg="white", relief="flat", padx=8,
                  cursor="hand2", command=self._plot_all_pins
                  ).pack(side="left", padx=4)
 
        tk.Button(CTRL, text="🔵 Toggle 100-Mile Circles", font=("Segoe UI", 9),
                  bg="#343a40", fg="white", relief="flat", padx=8,
                  cursor="hand2", command=self._toggle_circles
                  ).pack(side="left", padx=4)
 
        tk.Button(CTRL, text="🗑️ Clear All", font=("Segoe UI", 9),
                  bg="#343a40", fg="white", relief="flat", padx=8,
                  cursor="hand2", command=self._clear_map
                  ).pack(side="left", padx=4)
 
        # Legend
        LEG = tk.Frame(self, bg="#0d1b2a", pady=4)
        LEG.pack(fill="x")
        tk.Label(LEG, text="Need Level:  ", font=("Segoe UI", 8),
                 bg="#0d1b2a", fg="#adb5bd").pack(side="left", padx=(10, 0))
        for LEVEL, COLOR in NEED_COLORS.items():
            FG = NEED_FG[LEVEL]
            tk.Label(LEG, text=f"  {LEVEL}  ", font=("Segoe UI", 8, "bold"),
                     bg=COLOR, fg=FG, padx=4, pady=2
                     ).pack(side="left", padx=3)
        tk.Label(LEG, text="   🔵 = 100-mile radius", font=("Segoe UI", 8),
                 bg="#0d1b2a", fg="#adb5bd").pack(side="left", padx=10)
 
        # Map widget or fallback
        MAP_FRAME = tk.Frame(self, bg="#1a2332")
        MAP_FRAME.pack(fill="both", expand=True, padx=8, pady=8)
 
        if MAP_AVAILABLE:
            self.MAP_WIDGET = tkintermapview.TkinterMapView(
                MAP_FRAME, width=1080, height=560, corner_radius=8)
            self.MAP_WIDGET.pack(fill="both", expand=True)
            self.MAP_WIDGET.set_position(15.0, 125.0)
            self.MAP_WIDGET.set_zoom(4)
            self.CIRCLES_VISIBLE = False
            self._plot_all_pins()
        else:
            self._fallback_map(MAP_FRAME)
 
    def _fallback_map(self, PARENT):
        """Shown if tkintermapview is not installed."""
        tk.Label(PARENT,
                 text=("⚠️  tkintermapview is not installed.\n\n"
                       "Run this in Command Prompt to enable the map:\n\n"
                       "    pip install tkintermapview\n\n"
                       "Then restart the app."),
                 font=("Segoe UI", 11), bg="#1a2332", fg="#ffc107",
                 justify="center").pack(expand=True)
 
    def _get_pin_color(self, RECORD):
        NEED = RECORD.get("need_level", "Medium Need")
        COLOR_MAP = {
            "OSR":         "red",
            "High Need":   "orange",
            "Medium Need": "yellow",
            "Low Need":    "green",
        }
        return COLOR_MAP.get(NEED, "gray")
 
    def _plot_all_pins(self):
        if not MAP_AVAILABLE:
            return
        for M in self.MARKER_REFS:
            M.delete()
        self.MARKER_REFS.clear()
 
        for R in self.DATA.RECORDS:
            LAT = R.get("lat")
            LON = R.get("lon")
            if LAT is not None and LON is not None:
                try:
                    LABEL = (f"{R.get('name','?')}\n"
                             f"{R.get('record_type','')} | {R.get('specialty','')}\n"
                             f"{R.get('city','')} | {R.get('need_level','')}")
                    MARKER = self.MAP_WIDGET.set_marker(
                        float(LAT), float(LON),
                        text=R.get("name", ""),
                        marker_color_circle=self._get_pin_color(R),
                        marker_color_outside=self._get_pin_color(R)
                    )
                    self.MARKER_REFS.append(MARKER)
                except Exception:
                    pass
 
    def _toggle_circles(self):
        if not MAP_AVAILABLE:
            return
        if self.CIRCLES_VISIBLE:
            self._clear_circles()
            self.CIRCLES_VISIBLE = False
        else:
            self._draw_circles()
            self.CIRCLES_VISIBLE = True
 
    def _draw_circles(self):
        """Draw a 100-mile radius polygon around each pinned record."""
        if not MAP_AVAILABLE:
            return
        self._clear_circles()
        RADIUS_KM = RADIUS_MILES * MILES_TO_KM
        RADIUS_DEG = RADIUS_KM / 111.0   # approx degrees per km
 
        for R in self.DATA.RECORDS:
            LAT = R.get("lat")
            LON = R.get("lon")
            if LAT is None or LON is None:
                continue
            try:
                LAT = float(LAT)
                LON = float(LON)
                LON_DEG = RADIUS_DEG / max(math.cos(math.radians(LAT)), 0.01)
                POINTS = []
                STEPS = 72  # smoothness of circle
                for I in range(STEPS):
                    ANGLE = math.radians(I * (360 / STEPS))
                    P_LAT = LAT + RADIUS_DEG * math.sin(ANGLE)
                    P_LON = LON + LON_DEG * math.cos(ANGLE)
                    POINTS.append((P_LAT, P_LON))
                POLY = self.MAP_WIDGET.set_polygon(
                    POINTS,
                    fill_color=None,
                    outline_color="#0d6efd",
                    border_width=2,
                    name=f"circle_{R['id']}"
                )
                self.CIRCLE_REFS.append(POLY)
            except Exception:
                pass
 
    def _clear_circles(self):
        for C in self.CIRCLE_REFS:
            try:
                C.delete()
            except Exception:
                pass
        self.CIRCLE_REFS.clear()
 
    def _clear_map(self):
        self._clear_circles()
        for M in self.MARKER_REFS:
            try:
                M.delete()
            except Exception:
                pass
        self.MARKER_REFS.clear()
        self.CIRCLES_VISIBLE = False
 
    def _jump_to_country(self):
        if not MAP_AVAILABLE:
            return
        COUNTRY = self.JUMP_VAR.get()
        COORDS = COUNTRY_COORDS.get(COUNTRY)
        if COORDS:
            self.MAP_WIDGET.set_position(COORDS[0], COORDS[1])
            self.MAP_WIDGET.set_zoom(6)
 
 
# ─────────────────────────────────────────────────────────────────────────────
# MAIN APPLICATION
# ─────────────────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Provider Recruitment Manager v2.0 — Asia/Pacific")
        self.geometry("1300x820")
        self.minsize(1000, 680)
        self.configure(bg="#1a2332")
        self.DATA = DataManager()
        self.PANEL_VISIBLE = True
        self._apply_styles()
        self._build_ui()
        self._refresh_table()
 
    # ── Styles ────────────────────────────────────────────────────────────────
    def _apply_styles(self):
        STYLE = ttk.Style(self)
        STYLE.theme_use("clam")
        STYLE.configure("Treeview",
                         background="#2c3e50", foreground="white",
                         rowheight=28, fieldbackground="#2c3e50",
                         font=("Segoe UI", 9))
        STYLE.configure("Treeview.Heading",
                         background="#0d6efd", foreground="white",
                         font=("Segoe UI", 9, "bold"))
        STYLE.map("Treeview", background=[("selected", "#0d6efd")])
        STYLE.configure("TCombobox", fieldbackground="#2c3e50",
                         background="#2c3e50", foreground="white")
 
    # ── Build UI ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        HEADER = tk.Frame(self, bg="#0d1b2a", height=58)
        HEADER.pack(fill="x")
        HEADER.pack_propagate(False)
 
        self.TOGGLE_BTN = tk.Button(
            HEADER, text="☰", font=("Segoe UI", 14), bg="#0d1b2a", fg="white",
            relief="flat", cursor="hand2", padx=10,
            command=self._toggle_panel)
        self.TOGGLE_BTN.pack(side="left", padx=(8, 0))
 
        tk.Label(HEADER, text="✈  Provider Recruitment Manager — Asia/Pacific",
                 font=("Segoe UI", 13, "bold"), bg="#0d1b2a", fg="white"
                 ).pack(side="left", padx=10)
        tk.Label(HEADER, text="Doctors • Diagnostic Facilities • Per Diems",
                 font=("Segoe UI", 9), bg="#0d1b2a", fg="#6c757d"
                 ).pack(side="left")
 
        # Body
        self.BODY = tk.Frame(self, bg="#1a2332")
        self.BODY.pack(fill="both", expand=True)
 
        self._build_side_panel()
        self._build_main_panel()
 
        # Status bar
        self.STATUS_VAR = tk.StringVar(value="Ready.")
        tk.Label(self, textvariable=self.STATUS_VAR, font=("Segoe UI", 8),
                 bg="#0d1b2a", fg="#6c757d", anchor="w", padx=10
                 ).pack(fill="x", side="bottom")
 
    # ── Collapsible Side Panel ────────────────────────────────────────────────
    def _build_side_panel(self):
        self.SIDE_PANEL = tk.Frame(self.BODY, bg="#0d1b2a", width=270)
        self.SIDE_PANEL.pack(side="left", fill="y")
        self.SIDE_PANEL.pack_propagate(False)
 
        # Scrollable inner frame
        CANVAS = tk.Canvas(self.SIDE_PANEL, bg="#0d1b2a",
                            highlightthickness=0, width=270)
        SB = ttk.Scrollbar(self.SIDE_PANEL, orient="vertical",
                            command=CANVAS.yview)
        CANVAS.configure(yscrollcommand=SB.set)
        SB.pack(side="right", fill="y")
        CANVAS.pack(fill="both", expand=True)
 
        INNER = tk.Frame(CANVAS, bg="#0d1b2a")
        CANVAS.create_window((0, 0), window=INNER, anchor="nw")
        INNER.bind("<Configure>",
                   lambda E: CANVAS.configure(
                       scrollregion=CANVAS.bbox("all")))
 
        def section_title(TEXT):
            tk.Label(INNER, text=TEXT, font=("Segoe UI", 8, "bold"),
                     bg="#0d1b2a", fg="#6c757d", anchor="w", padx=14, pady=6
                     ).pack(fill="x")
 
        def make_label(TEXT):
            tk.Label(INNER, text=TEXT, font=("Segoe UI", 8, "bold"),
                     bg="#0d1b2a", fg="#adb5bd", anchor="w", padx=14
                     ).pack(fill="x", pady=(6, 2))
 
        def make_combo(VAR, VALUES):
            CB = ttk.Combobox(INNER, textvariable=VAR,
                               values=VALUES, state="readonly", width=26)
            CB.pack(padx=14, fill="x")
            return CB
 
        def make_entry(VAR):
            E = tk.Entry(INNER, textvariable=VAR, font=("Segoe UI", 10),
                          bg="#2c3e50", fg="white", insertbackground="white",
                          relief="flat", width=26)
            E.pack(padx=14, fill="x")
            return E
 
        # ── FILTER SECTION ──
        section_title("🔍  FILTERS")
 
        make_label("Record Type")
        self.F_TYPE = tk.StringVar(value="All Types")
        CB_TYPE = make_combo(self.F_TYPE, ["All Types"] + RECORD_TYPES)
        CB_TYPE.bind("<<ComboboxSelected>>", lambda E: self._refresh_table())
 
        make_label("Country")
        self.F_COUNTRY = tk.StringVar(value="All Countries")
        CB_C = make_combo(self.F_COUNTRY, ["All Countries"] + COUNTRIES)
        CB_C.bind("<<ComboboxSelected>>", lambda E: self._refresh_table())
 
        make_label("Specialty")
        self.F_SPEC = tk.StringVar(value="All Specialties")
        CB_S = make_combo(self.F_SPEC, ["All Specialties"] + SPECIALTIES)
        CB_S.bind("<<ComboboxSelected>>", lambda E: self._refresh_table())
 
        make_label("Status")
        self.F_STATUS = tk.StringVar(value="All Statuses")
        CB_ST = make_combo(self.F_STATUS, ["All Statuses"] + STATUS_OPTIONS)
        CB_ST.bind("<<ComboboxSelected>>", lambda E: self._refresh_table())
 
        make_label("Need Level")
        self.F_NEED = tk.StringVar(value="All Need Levels")
        CB_N = make_combo(self.F_NEED, ["All Need Levels"] + NEED_LEVELS)
        CB_N.bind("<<ComboboxSelected>>", lambda E: self._refresh_table())
 
        make_label("City Search")
        self.F_CITY = tk.StringVar()
        make_entry(self.F_CITY).bind("<KeyRelease>",
                                     lambda E: self._refresh_table())
 
        make_label("Name / Clinic Search")
        self.F_TEXT = tk.StringVar()
        make_entry(self.F_TEXT).bind("<KeyRelease>",
                                     lambda E: self._refresh_table())
 
        tk.Button(INNER, text="↺  Reset All Filters",
                  font=("Segoe UI", 9), bg="#343a40", fg="white",
                  relief="flat", cursor="hand2", pady=5,
                  command=self._reset_filters
                  ).pack(padx=14, pady=8, fill="x")
 
        # ── Need Level Color Legend ──
        tk.Frame(INNER, bg="#2c3e50", height=1).pack(fill="x", padx=14, pady=4)
        section_title("🎨  NEED LEVEL GUIDE")
        for LEVEL, COLOR in NEED_COLORS.items():
            FG = NEED_FG[LEVEL]
            tk.Label(INNER, text=f"  ● {LEVEL}", font=("Segoe UI", 9, "bold"),
                     bg=COLOR, fg=FG, anchor="w", padx=14, pady=3
                     ).pack(fill="x", padx=14, pady=2)
 
        # ── ACTIONS SECTION ──
        tk.Frame(INNER, bg="#2c3e50", height=1).pack(fill="x", padx=14, pady=8)
        section_title("⚡  ACTIONS")
 
        def action_btn(TEXT, CMD, COLOR="#0d6efd"):
            tk.Button(INNER, text=TEXT, font=("Segoe UI", 9, "bold"),
                      bg=COLOR, fg="white", relief="flat", cursor="hand2",
                      pady=7, command=CMD
                      ).pack(padx=14, pady=3, fill="x")
 
        action_btn("➕  Add New Record",          self._add_record)
        action_btn("✏️   Edit Selected",           self._edit_record,    "#198754")
        action_btn("🗑️   Delete Selected",         self._delete_record,  "#dc3545")
        action_btn("🔎  Bulk Search",              self._bulk_search,    "#6f42c1")
        action_btn("🌐  Search Online (Google)",   self._online_search,  "#fd7e14")
        action_btn("🗺️   Open Interactive Map",    self._open_map,       "#20c997")
        action_btn("📤  Export to CSV",            self._export_csv,     "#0dcaf0")
 
        # ── Stats ──
        tk.Frame(INNER, bg="#2c3e50", height=1).pack(fill="x", padx=14, pady=8)
        section_title("📊  STATISTICS")
        self.STATS_LBL = tk.Label(INNER, text="", font=("Segoe UI", 8),
                                   bg="#0d1b2a", fg="#adb5bd",
                                   anchor="w", padx=14, justify="left")
        self.STATS_LBL.pack(fill="x", pady=(0, 12))
 
    # ── Toggle Panel ──────────────────────────────────────────────────────────
    def _toggle_panel(self):
        if self.PANEL_VISIBLE:
            self.SIDE_PANEL.pack_forget()
            self.TOGGLE_BTN.config(text="▶")
            self.PANEL_VISIBLE = False
        else:
            self.SIDE_PANEL.pack(side="left", fill="y", before=self.MAIN_PANEL)
            self.TOGGLE_BTN.config(text="☰")
            self.PANEL_VISIBLE = True
 
    # ── Main Panel (Table) ────────────────────────────────────────────────────
    def _build_main_panel(self):
        self.MAIN_PANEL = tk.Frame(self.BODY, bg="#1a2332")
        self.MAIN_PANEL.pack(side="left", fill="both", expand=True,
                              padx=10, pady=10)
 
        COLS = ("Type", "Name", "Specialty", "Country", "City",
                "Status", "Need Level", "Priority", "Phone", "Date Added")
 
        TREE_FRAME = tk.Frame(self.MAIN_PANEL, bg="#1a2332")
        TREE_FRAME.pack(fill="both", expand=True)
 
        self.TREE = ttk.Treeview(TREE_FRAME, columns=COLS,
                                  show="headings", selectmode="browse")
        WIDTHS = [110, 160, 120, 110, 100, 100, 100, 70, 110, 90]
        for COL, W in zip(COLS, WIDTHS):
            self.TREE.heading(COL, text=COL,
                               command=lambda C=COL: self._sort_col(C))
            self.TREE.column(COL, width=W, minwidth=60)
 
        # Need level color tags
        self.TREE.tag_configure("OSR",         background="#3a1a1a", foreground="#ff6b6b")
        self.TREE.tag_configure("High Need",   background="#3a2a1a", foreground="#ffb347")
        self.TREE.tag_configure("Medium Need", background="#3a3a1a", foreground="#ffd700")
        self.TREE.tag_configure("Low Need",    background="#1a3a2a", foreground="#6fcf97")
 
        VSB = ttk.Scrollbar(TREE_FRAME, orient="vertical",
                             command=self.TREE.yview)
        HSB = ttk.Scrollbar(TREE_FRAME, orient="horizontal",
                             command=self.TREE.xview)
        self.TREE.configure(yscrollcommand=VSB.set,
                             xscrollcommand=HSB.set)
        VSB.pack(side="right", fill="y")
        HSB.pack(side="bottom", fill="x")
        self.TREE.pack(fill="both", expand=True)
        self.TREE.bind("<Double-1>", lambda E: self._edit_record())
 
        self.COUNT_LBL = tk.Label(self.MAIN_PANEL, text="",
                                   font=("Segoe UI", 8), bg="#1a2332",
                                   fg="#6c757d", anchor="e")
        self.COUNT_LBL.pack(fill="x")
 
    # ── Refresh Table ─────────────────────────────────────────────────────────
    def _refresh_table(self, OVERRIDE=None):
        for ROW in self.TREE.get_children():
            self.TREE.delete(ROW)
 
        RESULTS = OVERRIDE if OVERRIDE is not None else \
            self.DATA.search_records(
                TYPE_FILTER=self.F_TYPE.get(),
                COUNTRY_FILTER=self.F_COUNTRY.get(),
                SPECIALTY_FILTER=self.F_SPEC.get(),
                STATUS_FILTER=self.F_STATUS.get(),
                NEED_FILTER=self.F_NEED.get(),
                CITY_FILTER=self.F_CITY.get(),
                TEXT_FILTER=self.F_TEXT.get()
            )
 
        for R in RESULTS:
            NEED = R.get("need_level", "Medium Need")
            self.TREE.insert("", "end", iid=R["id"], tags=(NEED,),
                              values=(
                                  R.get("record_type", ""),
                                  R.get("name", ""),
                                  R.get("specialty", ""),
                                  R.get("country", ""),
                                  R.get("city", ""),
                                  R.get("status", ""),
                                  R.get("need_level", ""),
                                  R.get("priority", ""),
                                  R.get("phone", ""),
                                  R.get("date_added", "")
                              ))
 
        self.COUNT_LBL.config(text=f"Showing {len(RESULTS)} record(s)")
        self._update_stats()
 
    def _update_stats(self):
        TOTAL = len(self.DATA.RECORDS)
        DOCS = sum(1 for R in self.DATA.RECORDS if R.get("record_type") == "Doctor")
        DIAG = sum(1 for R in self.DATA.RECORDS
                   if R.get("record_type") == "Diagnostic Facility")
        PD   = sum(1 for R in self.DATA.RECORDS if R.get("record_type") == "Per Diem")
        OSR  = sum(1 for R in self.DATA.RECORDS if R.get("need_level") == "OSR")
        HIGH = sum(1 for R in self.DATA.RECORDS if R.get("need_level") == "High Need")
        self.STATS_LBL.config(
            text=(f"Total Records:       {TOTAL}\n"
                  f"Doctors:             {DOCS}\n"
                  f"Diagnostic:          {DIAG}\n"
                  f"Per Diems:           {PD}\n"
                  f"─────────────────\n"
                  f"OSR (Critical):      {OSR}\n"
                  f"High Need:           {HIGH}"))
 
    def _reset_filters(self):
        self.F_TYPE.set("All Types")
        self.F_COUNTRY.set("All Countries")
        self.F_SPEC.set("All Specialties")
        self.F_STATUS.set("All Statuses")
        self.F_NEED.set("All Need Levels")
        self.F_CITY.set("")
        self.F_TEXT.set("")
        self._refresh_table()
 
    def _sort_col(self, COL):
        DATA_LIST = [(self.TREE.set(K, COL), K)
                     for K in self.TREE.get_children("")]
        DATA_LIST.sort()
        for IDX, (_, K) in enumerate(DATA_LIST):
            self.TREE.move(K, "", IDX)
 
    # ── CRUD ─────────────────────────────────────────────────────────────────
    def _add_record(self):
        DLG = RecordDialog(self, "Add New Record")
        self.wait_window(DLG)
        if DLG.RESULT:
            self.DATA.add_record(DLG.RESULT)
            self._refresh_table()
            self.STATUS_VAR.set(f"✅ Added: {DLG.RESULT['name']}")
 
    def _edit_record(self):
        SEL = self.TREE.selection()
        if not SEL:
            messagebox.showinfo("No Selection", "Select a record to edit.")
            return
        RID = SEL[0]
        REC = next((R for R in self.DATA.RECORDS if R["id"] == RID), None)
        if not REC:
            return
        DLG = RecordDialog(self, "Edit Record", REC)
        self.wait_window(DLG)
        if DLG.RESULT:
            self.DATA.update_record(RID, DLG.RESULT)
            self._refresh_table()
            self.STATUS_VAR.set(f"✏️ Updated: {DLG.RESULT['name']}")
 
    def _delete_record(self):
        SEL = self.TREE.selection()
        if not SEL:
            messagebox.showinfo("No Selection", "Select a record to delete.")
            return
        RID = SEL[0]
        REC = next((R for R in self.DATA.RECORDS if R["id"] == RID), None)
        if messagebox.askyesno("Confirm Delete",
                                f"Delete '{REC.get('name', 'this record')}'?"):
            self.DATA.delete_record(RID)
            self._refresh_table()
            self.STATUS_VAR.set("🗑️ Record deleted.")
 
    # ── Bulk Search ───────────────────────────────────────────────────────────
    def _bulk_search(self):
        DLG = BulkSearchDialog(self)
        self.wait_window(DLG)
        if DLG.RESULT:
            RESULTS = [R for R in self.DATA.RECORDS
                       if R.get("country") in DLG.RESULT["countries"]
                       and (not DLG.RESULT["specialties"] or
                            R.get("specialty") in DLG.RESULT["specialties"])
                       and R.get("record_type") in DLG.RESULT["types"]]
            self._refresh_table(OVERRIDE=RESULTS)
            self.STATUS_VAR.set(f"🔎 Bulk search: {len(RESULTS)} results")
 
    # ── Online Search ─────────────────────────────────────────────────────────
    def _online_search(self):
        COUNTRY = self.F_COUNTRY.get()
        SPEC    = self.F_SPEC.get()
        TYPE    = self.F_TYPE.get()
        CITY    = self.F_CITY.get().strip()
 
        COUNTRY_T = "" if COUNTRY == "All Countries"   else COUNTRY
        SPEC_T    = "" if SPEC    == "All Specialties" else SPEC
        TYPE_T    = "" if TYPE    == "All Types"        else TYPE
        CITY_T    = CITY
 
        QUERY = f"English speaking {SPEC_T} {TYPE_T} {CITY_T} {COUNTRY_T} medical evaluation".strip()
        URL = f"https://www.google.com/search?q={QUERY.replace(' ', '+')}"
        webbrowser.open(URL)
        self.STATUS_VAR.set(f"🌐 Google: {QUERY}")
 
    # ── Map ───────────────────────────────────────────────────────────────────
    def _open_map(self):
        MapWindow(self, self.DATA)
 
    # ── Export ────────────────────────────────────────────────────────────────
    def _export_csv(self):
        FP = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile="Records_Export.csv",
            title="Export Records")
        if FP:
            if self.DATA.export_csv(FP):
                messagebox.showinfo("Export Complete",
                                    f"Exported successfully to:\n{FP}")
                self.STATUS_VAR.set(f"📤 Exported to {FP}")
            else:
                messagebox.showwarning("Nothing to Export",
                                       "No records in the database.")
 
 
# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    APP = App()
    APP.mainloop()
