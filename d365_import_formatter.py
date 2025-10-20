# d365_builder_v2.py
import json, sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

DB_PATH = "d365_builder.db"
DASHBOARD_DB = "drafting_tools.db"  # tie into existing Project Management DB
# If you want to auto-prime defaults from your workbook JSON, set this to the path:
WORKBOOK_JSON = "D365 IMPORT.json"  # same folder as this script, or adjust path

# ---------------- DB ----------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS jobs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_no TEXT NOT NULL,
        job_name TEXT,
        drafter TEXT,
        created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        kind TEXT NOT NULL,
        part_number TEXT NOT NULL,
        description TEXT NOT NULL,
        bom TEXT NOT NULL,
        template TEXT NOT NULL,
        product_type TEXT NOT NULL,
        params_json TEXT NOT NULL,
        created_at TEXT,
        FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE)""")
    conn.commit(); conn.close()

def insert_job(job_no, job_name, drafter):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("INSERT INTO jobs(job_no,job_name,drafter,created_at) VALUES(?,?,?,?)",
              (job_no, job_name, drafter, datetime.utcnow().isoformat()))
    conn.commit(); jid = c.lastrowid; conn.close(); return jid

def list_jobs():
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT id,job_no,job_name,drafter,created_at FROM jobs ORDER BY id DESC")
    rows = c.fetchall(); conn.close(); return rows

def insert_items(job_id, rows):
    """rows: list of dicts with keys (kind, pn, desc, bom, template, ptype, params)"""
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    for r in rows:
        c.execute("""INSERT INTO items(job_id,kind,part_number,description,bom,template,product_type,params_json,created_at)
                     VALUES(?,?,?,?,?,?,?,?,?)""",
                  (job_id, r["kind"], r["pn"], r["desc"], r["bom"], r["template"],
                   r["ptype"], json.dumps(r["params"]), datetime.utcnow().isoformat()))
    conn.commit(); conn.close()

def list_items(job_id):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("""SELECT id,kind,part_number,description,bom,template,product_type,params_json,created_at
                FROM items WHERE job_id=? ORDER BY id DESC""", (job_id,))
    rows = c.fetchall(); conn.close(); return rows

# -------------- Helpers -------------
def fmt_pn(job_no, dash): return f"{job_no}-{str(dash)}"
def fmt_bom(pn): return f"{pn}-000"

# Tank inch table based on your L/M table (L=feet, M=(L*12)-offset)
def tank_inches_from_feet(ft:int)->float:
    if ft in (4,5,6): return ft*12 + 0.25
    if 7 <= ft <= 12: return ft*12 - 0.5
    if 13 <= ft <= 16: return ft*12 - 1.25
    if 17 <= ft <= 21: return ft*12 - 2
    if 22 <= ft <= 24: return ft*12 - 2
    if 25 <= ft <= 30: return ft*12 - 2.75
    if 31 <= ft <= 35: return ft*12 - 3.5
    return ft*12  # fallback

# Try to sniff some defaults from the workbook JSON (optional)
def load_workbook_defaults(path: str):
    defaults = {
        "heater": {
            "dash":"01",
            "diam":["",30,42,54,60,76,84,96],
            "height":["",7,8,8.5,9,10,11,12,13,14,15,16,17,18,19,20],
            "model":["", "GP","RM","TE","TE-NSF"],
            "material":["","304","316","AL6XN"],
            "stack_diam":["",12,18,24,30,36],
            "flange_inlet":["",1,1.25,1.5,2,2.5,3,4,6],
            "gas_size":["",1,1.5,2,2.5,3],
            "gas_mount":["","BM","FM"],
            "btu":["",1.2,2,3,4.5,5.5,6,7,8,9,9.9,10,10.5,11,12,12.5,15,18,19,20,21,25,30],
            "hand":["","LEFT","RIGHT"],
            "label":["","A","B","C","D","1","2","3","4"]
        },
        "tank": {
            "dash":"03",
            "diam":["",48,54,60,66,72,78,84,90,96,102,108,114,120,126,132,138,144,150,156,162,168],
            "height_ft":["",3,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35],
            "type":["","HW","TW","CW","CMF","RO","WW","EQ"],
            "material":["","304","316"]
        },
        "pump": {
            "dash":"05",
            "count":["","SIMPLEX","DUPLEX","TRIPLEX","QUADPLEX"],
            "pressure":["","LP","MP","HP"],
            "type":["","HW","TW","CW","CMF","RO","WW"],
            "hp":["",0.5,0.75,1,2,3,5,7.5,10,15,20,25,30,40,50,60,75,100],
            "len":[55,60,70], "wid":[27,30,36], "hei":[99,120,150],
            "material":["","304","316"]
        }
    }
    try:
        p = Path(path)
        if not p.exists(): return defaults
        with p.open("r", encoding="utf-8") as f: data = json.load(f)

        def val(sheet, addr):
            v = data.get(sheet, {}).get(addr, {})
            return v.get("value") if "value" in v else v.get("formula")

        # Heater seeds
        diam = val("Import Heater (A)","I4"); hgt = val("Import Heater (A)","I5")
        model = val("Import Heater (A)","I8"); mat = val("Import Heater (A)","I9")
        stack_d = val("Import Heater (A)","I6"); flange = val("Import Heater (A)","I7")
        gas_sz = val("Import Heater (A)","I10"); gas_mt = val("Import Heater (A)","I11")
        btu = val("Import Heater (A)","I12"); hand = val("Import Heater (A)","I13")
        for (k,v) in [("diam",diam),("height",hgt),("model",model),("material",mat),
                      ("stack_diam",stack_d),("flange_inlet",flange),
                      ("gas_size",gas_sz),("gas_mount",gas_mt),
                      ("btu",btu),("hand",hand)]:
            if v is not None and v not in defaults["heater"][k]:
                defaults["heater"][k].append(v)

        # Tank seeds
        t_diam = val("Import Tank (A)","H4"); t_h = val("Import Tank (A)","H5")
        t_type = val("Import Tank (A)","H7"); t_mat = val("Import Tank (A)","H6")
        for (k,v) in [("diam",t_diam),("height_ft",t_h),("type",t_type),("material",t_mat)]:
            if v is not None and v not in defaults["tank"][k]:
                defaults["tank"][k].append(v)

        # Pump seeds
        p_cnt = val("Pump","G3"); p_pres = val("Pump","G4"); p_type = val("Pump","G5")
        p_hp = val("Pump","G6"); p_mat = val("Pump","G7")
        p_len = val("Pump","G8"); p_wid = val("Pump","G9"); p_hei = val("Pump","G10")
        seeds = [("count",p_cnt),("pressure",p_pres),("type",p_type),
                 ("hp",p_hp),("material",p_mat),("len",p_len),("wid",p_wid),("hei",p_hei)]
        for (k,v) in seeds:
            if v is not None and v not in defaults["pump"][k]:
                defaults["pump"][k].append(v)

    finally:
        # Ensure uniqueness & sort where sensible
        for k in defaults["heater"]:
            if isinstance(defaults["heater"][k], list):
                defaults["heater"][k] = sorted(list(dict.fromkeys(defaults["heater"][k])), key=str)
        for k in defaults["tank"]:
            if isinstance(defaults["tank"][k], list):
                defaults["tank"][k] = sorted(list(dict.fromkeys(defaults["tank"][k])), key=str)
        for k in defaults["pump"]:
            if isinstance(defaults["pump"][k], list):
                defaults["pump"][k] = sorted(list(dict.fromkeys(defaults["pump"][k])), key=str)
        return defaults

# -------------- Generators --------------
@dataclass
class HeaterParams:
    job_no: str
    dash: str
    diameter_in: int
    height_in: int
    model: str
    material: str
    stack_diam_in: int
    flange_inlet_in: int
    gas_train_size_in: int
    gas_train_mount: str
    btu_mmbtu: float
    hand: str
    label: str  # "0" for none or "A/B"

def gen_heater_all(p: HeaterParams):
    """Return the 7 rows (FAB, .1 WELD, .2 SHELL, .3 STACK, .4 GAS TRAIN, .5 MOD PIPING, .1-A PRECUT)"""
    label = p.label.strip()
    has_lbl = (label not in ("", "0", "0.0"))

    # Determine SINGLE/DUAL by BTU
    singledual = "SINGLE" if float(p.btu_mmbtu) < 15 else "DUAL"

    rows = []
    def add_row(suffix, desc, template, ptype):
        pn = fmt_pn(p.job_no, f"{p.dash}{suffix}")
        rows.append({
            "kind":"heater","pn":pn,"desc":desc,"bom":fmt_bom(pn),
            "template":template,"ptype":ptype,"params":asdict(p)
        })

    # FAB (B3/C3)
    if has_lbl:
        desc_fab = f"HEATER {label}, FAB, {p.diameter_in}X{p.height_in}, {p.model}, {p.material}"
    else:
        desc_fab = f"HEATER, FAB, {p.diameter_in}X{p.height_in}, {p.model}, {p.material}"
    add_row("", desc_fab, "FG FAB", "Item")

    # .1 WELD (B4/C4)
    if has_lbl:
        d = f"HEATER {label}, WELD, {p.diameter_in}X{p.height_in}, {p.material}"
    else:
        d = f"HEATER, WELD, {p.diameter_in}X{p.height_in}, {p.material}"
    add_row(".1", d, "Sub Assy", "Pegged Supply")

    # .2 SHELL (B5/C5)
    if has_lbl:
        d = f"HEATER {label}, SHELL, {p.diameter_in}X{p.height_in}, {p.material}"
    else:
        d = f"HEATER, SHELL, {p.diameter_in}X{p.height_in}, {p.material}"
    add_row(".2", d, "Sub Assy", "Phantom")

    # .3 STACK (B6/C6) => {stack_diam}X{stack_height}, W/{flange}FL
    stack_height = tank_inches_from_feet(p.height_in if isinstance(p.height_in,int) else int(p.height_in))
    d = f"HEATER{f' {label}' if has_lbl else ''}, STACK, {p.stack_diam_in}X{int(stack_height)}, W/{p.flange_inlet_in}FL"
    add_row(".3", d, "Sub Assy", "Phantom")

    # .4 GAS TRAIN (B7/C7) => includes size, mount, SIEMENS, MBTU, hand
    d = (f"GAS TRAIN{f', HTR {label}' if has_lbl else ''}, "
         f"{p.gas_train_size_in}, {p.gas_train_mount}, SIEMENS, {p.btu_mmbtu}MBTU, {p.hand}")
    add_row(".4", d, "Sub Assy", "Pegged Supply")

    # .5 MOD PIPING (B8/C8): IF Single -> I17; else I18 with SINGLE/DUAL mention
    if singledual == "SINGLE":
        d = f"HEATER{f' {label}' if has_lbl else ''}, MOD PIPING, {p.model}"
    else:
        d = f"HEATER{f' {label}' if has_lbl else ''}, MOD PIPING, {singledual}, {p.model}"
    add_row(".5", d, "Sub Assy", "Phantom")

    # .1-A PRECUT (B10/C10)
    d = f"PRECUT HTR{p.diameter_in}, {p.stack_diam_in}STACK, 11GA, {p.material}"
    add_row(".1-A", d, "Sub Assy", "Phantom")

    return rows

@dataclass
class TankParams:
    job_no: str
    dash: str
    diameter_in: int
    height_ft: int
    type_code: str
    material: str

def gen_tank_all(p: TankParams):
    rows=[]
    def add_row(suffix, desc, template, ptype):
        pn = fmt_pn(p.job_no, f"{p.dash}{suffix}")
        rows.append({
            "kind":"tank","pn":pn,"desc":desc,"bom":fmt_bom(pn),
            "template":template,"ptype":ptype,"params":asdict(p)
        })

    # Main FAB (A3/B3)
    d0 = f"TANK, {p.diameter_in}X{p.height_ft}, {p.type_code}, {p.material}"
    add_row("", d0, "FG FAB", "Item")

    # .1 SHELL uses Tank Inches from table (A4/B4 with H8)
    inches = tank_inches_from_feet(int(p.height_ft))
    d1 = f"TANK, SHELL, {p.diameter_in}X{inches:.2f}, {p.material}"
    add_row(".1", d1, "Sub Assy", "Phantom")

    # -A PRECUT
    dA = f"PRECUT TANK{p.diameter_in}X{p.height_ft}, 11GA, {p.material}"
    add_row("-A", dA, "Sub Assy", "Phantom")

    return rows

@dataclass
class PumpParams:
    job_no: str
    dash: str
    pump_count: str
    pressure: str
    type_code: str
    hp: float
    frame_len_in: int
    frame_w_in: int
    frame_h_in: int
    material: str

def gen_pump_all(p: PumpParams):
    rows=[]
    def add_row(suffix, desc, template, ptype):
        pn = fmt_pn(p.job_no, f"{p.dash}{suffix}")
        rows.append({
            "kind":"pump","pn":pn,"desc":desc,"bom":fmt_bom(pn),
            "template":template,"ptype":ptype,"params":asdict(p)
        })

    # Main line (A2/B2) => omit pressure when LP
    if p.pressure.upper()=="LP":
        d0 = f"PUMP, {p.pump_count}, {p.type_code}, {p.hp}HP"
    else:
        d0 = f"PUMP, {p.pump_count}, {p.pressure}, {p.type_code}, {p.hp}HP"
    add_row("", d0, "FG FAB", "Item")

    # .1 SKID (A3/B3)
    d1 = f"PUMP SKID, {p.pump_count}, {p.frame_len_in}X{p.frame_w_in}X{p.frame_h_in}, {p.material}"
    add_row(".1", d1, "Sub Assy", "Phantom")

    # .1-A PRECUT (A4/B4) => gauge depends on count (SIMPLEX = 11GA else 3/16PL)
    gauge = "11GA" if p.pump_count.upper()=="SIMPLEX" else "3/16PL"
    dA = f"PRECUT, {p.pump_count} PUMP SKID, {gauge}"
    add_row(".1-A", dA, "Sub Assy", "Phantom")

    return rows

# -------------- UI --------------
class App(tk.Tk):
    def __init__(self, defaults):
        super().__init__()
        self.title("D365 Builder")
        self.geometry("1200x780")
        # start maximized so native window icons still work for resizing
        try:
            self.state('zoomed')
        except Exception:
            pass
        self.defaults = defaults
        self.current_job = {"id":None, "job_no":"", "job_name":"", "drafter":""}

        # status bar
        self.status_var = tk.StringVar(value="Ready")

        # Main layout: left projects pane + right notebook
        root_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        root_pane.pack(fill="both", expand=True)

        self.left_projects = ttk.Frame(root_pane, padding=6)
        right_holder = ttk.Frame(root_pane)
        root_pane.add(self.left_projects, weight=0)
        root_pane.add(right_holder, weight=1)

        # Seed options into DB if empty, then merge saved Settings from DB into defaults
        try:
            self.ensure_options_seeded()
            self.apply_options_from_db_to_defaults()
        except Exception:
            pass

        # Left: Active Projects list
        self.build_projects_list(self.left_projects)

        # Right: Notebook
        nb = ttk.Notebook(right_holder); nb.pack(fill="both", expand=True)
        self.t_heater = ttk.Frame(nb)
        self.t_tank = ttk.Frame(nb); self.t_pump = ttk.Frame(nb); self.t_report = ttk.Frame(nb); self.t_settings = ttk.Frame(nb)
        nb.add(self.t_heater, text="Heater")
        nb.add(self.t_tank, text="Tank"); nb.add(self.t_pump, text="Pump")
        nb.add(self.t_report, text="Report"); nb.add(self.t_settings, text="Settings")

        self.build_heater(); self.build_tank(); self.build_pump(); self.build_report(); self.build_settings()
        self.refresh_projects()

        # status bar at bottom
        status_bar = ttk.Label(self, textvariable=self.status_var, anchor="w")
        status_bar.pack(fill="x")

    # -- Projects from drafting_tools.db
    def build_projects_list(self, parent):
        ttk.Label(parent, text="Active Projects", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.projects_tree = ttk.Treeview(parent, columns=("id","job_no","customer"), show="headings", height=20)
        for col,w in [("job_no",120),("customer",220)]:
            self.projects_tree.heading(col, text=col)
            self.projects_tree.column(col, width=w, anchor="w")
        # hide id
        self.projects_tree.heading("id", text="id")
        self.projects_tree.column("id", width=0, stretch=False)
        self.projects_tree.pack(fill="y", expand=False)
        self.projects_tree.bind("<<TreeviewSelect>>", self.on_select_project)

        btns = ttk.Frame(parent); btns.pack(fill="x", pady=(6,0))
        ttk.Button(btns, text="Refresh", command=self.refresh_projects).pack(side="left")

    def refresh_projects(self):
        for i in self.projects_tree.get_children(): self.projects_tree.delete(i)
        try:
            conn = sqlite3.connect(DASHBOARD_DB)
            c = conn.cursor()
            c.execute(
                """
                SELECT p.id, p.job_number, COALESCE(p.customer_name, '')
                FROM projects p
                LEFT JOIN release_to_dee rd ON rd.project_id = p.id
                WHERE NOT (
                    (COALESCE(p.released_to_dee, rd.release_date) IS NOT NULL AND COALESCE(p.released_to_dee, rd.release_date) != '')
                    OR rd.is_completed = 1
                    OR (p.completion_date IS NOT NULL AND p.completion_date != '')
                )
                ORDER BY CAST(p.job_number AS INTEGER) ASC
                """
            )
            rows = c.fetchall(); conn.close()
        except Exception:
            rows = []
        for r in rows:
            pid, jn, cust = r
            self.projects_tree.insert("", "end", values=(pid, jn, cust))

    def on_select_project(self, *_):
        sel = self.projects_tree.selection()
        if not sel: return
        vals = self.projects_tree.item(sel[0], "values")
        self.current_job = {"id": int(vals[0]), "job_no": str(vals[1]), "job_name":"", "drafter":""}
        self.lbl_job_heater.configure(text=f"Job #{self.current_job['job_no']}")
        self.lbl_job_tank.configure(text=f"Job #{self.current_job['job_no']}")
        self.lbl_job_pump.configure(text=f"Job #{self.current_job['job_no']}")
        self.lbl_job_report.configure(text=f"Job #{self.current_job['job_no']}")
        self.refresh_report()

    # (Removed internal Jobs tab; using Active Projects from drafting_tools.db)

    # -- Form utilities
    def cb(self, parent, values, var, width=18):
        cb = ttk.Combobox(parent, values=[str(v) for v in values], textvariable=var, width=width)
        cb.state(["!disabled","readonly"])  # dropdown but still we allow programmatic set; user can type by toggling
        return cb

    # -- Heater
    def build_heater(self):
        pad=10; f=ttk.Frame(self.t_heater, padding=pad); f.pack(fill="both", expand=True)
        left = ttk.LabelFrame(f, text="Heater Parameters", padding=pad); left.pack(side="left", fill="y")
        self.lbl_job_heater = ttk.Label(left, text="Job # (select a job)"); self.lbl_job_heater.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,8))

        dh = self.defaults["heater"]
        self.h_dash=tk.StringVar(value=dh["dash"])
        self.h_diam=tk.StringVar(value=str(dh["diam"][0])); self.h_hgt=tk.StringVar(value=str(dh["height"][0]))
        self.h_model=tk.StringVar(value=dh["model"][0]); self.h_mat=tk.StringVar(value=str(dh["material"][0]))
        self.h_stack=tk.StringVar(value=str(dh["stack_diam"][0])); self.h_flange=tk.StringVar(value=str(dh["flange_inlet"][0]))
        self.h_gsize=tk.StringVar(value=str(dh["gas_size"][0])); self.h_gmount=tk.StringVar(value=dh["gas_mount"][0])
        self.h_btu=tk.StringVar(value=str(dh["btu"][0])); self.h_hand=tk.StringVar(value=dh["hand"][0])
        self.h_label=tk.StringVar(value=dh["label"][0])

        self.cmb_heater = {}
        rows = [
            ("Dash Number", ttk.Entry(left, textvariable=self.h_dash, width=8), "dash"),
            ("Heater Diameter", self.cb(left, dh["diam"], self.h_diam), "diameter_in"),
            ("Heater Height", self.cb(left, dh["height"], self.h_hgt), "height_in"),
            ("Stack Diameter", self.cb(left, dh["stack_diam"], self.h_stack), "stack_diam_in"),
            ("Flange Inlet", self.cb(left, dh["flange_inlet"], self.h_flange), "flange_inlet_in"),
            ("Heater Model", self.cb(left, dh["model"], self.h_model, 22), "model"),
            ("Material", self.cb(left, dh["material"], self.h_mat), "material"),
            ("Gas Train Size", self.cb(left, dh["gas_size"], self.h_gsize), "gas_train_size_in"),
            ("Gas Train Mount", self.cb(left, dh["gas_mount"], self.h_gmount), "gas_train_mount"),
            ("BTU", self.cb(left, dh["btu"], self.h_btu), "btu_mmbtu"),
            ("Hand", self.cb(left, dh["hand"], self.h_hand), "hand"),
            ("Heater A/B", self.cb(left, dh["label"], self.h_label), "label"),
        ]
        for r,(label_widget, widget, key_name) in enumerate(rows, start=1):
            ttk.Label(left, text=label_widget).grid(row=r, column=0, sticky="e", padx=4, pady=4)
            widget.grid(row=r, column=1, sticky="w", padx=4, pady=4)
            if isinstance(widget, ttk.Combobox):
                self.cmb_heater[key_name] = widget

        btns=ttk.Frame(left); btns.grid(row=len(rows)+1, column=0, columnspan=2, pady=(8,0))
        ttk.Button(btns, text="Preview 7 Heater Lines", command=self.preview_heater).pack(side="left", padx=4)
        ttk.Button(btns, text="Save To Job", command=self.save_heater).pack(side="left", padx=4)

        self.heater_table = ResultTable(f, "Heater Output (7 rows)")
        self.heater_table.frame.pack(side="left", fill="both", expand=True, padx=(pad,0))

    def heater_params(self):
        if not self.current_job["id"]:
            messagebox.showerror("No Job", "Select or create a job first."); return None
        return HeaterParams(
            job_no=self.current_job["job_no"], dash=self.h_dash.get(),
            diameter_in=int(float(self.h_diam.get())), height_in=int(float(self.h_hgt.get())),
            model=self.h_model.get(), material=str(self.h_mat.get()),
            stack_diam_in=int(float(self.h_stack.get())), flange_inlet_in=int(float(self.h_flange.get())),
            gas_train_size_in=int(float(self.h_gsize.get())), gas_train_mount=self.h_gmount.get(),
            btu_mmbtu=float(self.h_btu.get()), hand=self.h_hand.get(), label=self.h_label.get()
        )

    def preview_heater(self):
        p = self.heater_params()
        if not p:
            return
        rows = gen_heater_all(p)
        self.heater_table.load(rows)

    def save_heater(self):
        p = self.heater_params()
        if not p:
            return
        rows = gen_heater_all(p)
        insert_items(self.current_job["id"], rows)
        self.refresh_report()
        self.set_status("Heater lines saved")

    # -- Tank
    def build_tank(self):
        pad=10; f=ttk.Frame(self.t_tank, padding=pad); f.pack(fill="both", expand=True)
        left = ttk.LabelFrame(f, text="Tank Parameters", padding=pad); left.pack(side="left", fill="y")
        self.lbl_job_tank = ttk.Label(left, text="Job # (select a job)"); self.lbl_job_tank.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,8))

        dt = self.defaults["tank"]
        self.t_dash=tk.StringVar(value=dt["dash"]); self.t_diam=tk.StringVar(value=str(dt["diam"][0]))
        self.t_hft=tk.StringVar(value=str(dt["height_ft"][0])); self.t_type=tk.StringVar(value=dt["type"][0])
        self.t_mat=tk.StringVar(value=str(dt["material"][0]))

        self.cmb_tank = {}
        rows = [
            ("Dash #", ttk.Entry(left, textvariable=self.t_dash, width=8), None),
            ("Tank Diameter", self.cb(left, dt["diam"], self.t_diam), "diameter_in"),
            ("Tank Height", self.cb(left, dt["height_ft"], self.t_hft), "height_ft"),
            ("Material", self.cb(left, dt["material"], self.t_mat), "material"),
            ("Type", self.cb(left, dt["type"], self.t_type, 16), "type"),
        ]
        for r,(label_widget, widget, key_name) in enumerate(rows, start=1):
            ttk.Label(left, text=label_widget).grid(row=r, column=0, sticky="e", padx=4, pady=4)
            widget.grid(row=r, column=1, sticky="w", padx=4, pady=4)
            if isinstance(widget, ttk.Combobox) and key_name:
                self.cmb_tank[key_name] = widget

        btns=ttk.Frame(left); btns.grid(row=len(rows)+1, column=0, columnspan=2, pady=(8,0))
        ttk.Button(btns, text="Preview 3 Tank Lines", command=self.preview_tank).pack(side="left", padx=4)
        ttk.Button(btns, text="Save To Job", command=self.save_tank).pack(side="left", padx=4)

        self.tank_table = ResultTable(f, "Tank Output (3 rows)")
        self.tank_table.frame.pack(side="left", fill="both", expand=True, padx=(pad,0))

    def tank_params(self):
        if not self.current_job["id"]:
            messagebox.showerror("No Job", "Select or create a job first."); return None
        return TankParams(
            job_no=self.current_job["job_no"], dash=self.t_dash.get(),
            diameter_in=int(float(self.t_diam.get())), height_ft=int(float(self.t_hft.get())),
            type_code=self.t_type.get(), material=str(self.t_mat.get())
        )

    def preview_tank(self):
        p = self.tank_params()
        if not p:
            return
        rows = gen_tank_all(p)
        self.tank_table.load(rows)

    def save_tank(self):
        p = self.tank_params()
        if not p:
            return
        rows = gen_tank_all(p)
        insert_items(self.current_job["id"], rows)
        self.refresh_report()
        self.set_status("Tank lines saved")

    # -- Pump
    def build_pump(self):
        pad=10; f=ttk.Frame(self.t_pump, padding=pad); f.pack(fill="both", expand=True)
        left = ttk.LabelFrame(f, text="Pump Parameters", padding=pad); left.pack(side="left", fill="y")
        self.lbl_job_pump = ttk.Label(left, text="Job # (select a job)"); self.lbl_job_pump.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,8))

        dp = self.defaults["pump"]
        self.p_dash=tk.StringVar(value=dp["dash"]); self.p_cnt=tk.StringVar(value=dp["count"][0])
        self.p_pres=tk.StringVar(value=dp["pressure"][0]); self.p_type=tk.StringVar(value=dp["type"][0])
        self.p_hp=tk.StringVar(value=str(dp["hp"][0])); self.p_len=tk.StringVar(value=str(dp["len"][0]))
        self.p_wid=tk.StringVar(value=str(dp["wid"][0])); self.p_hei=tk.StringVar(value=str(dp["hei"][0]))
        self.p_mat=tk.StringVar(value=str(dp["material"][0]))

        self.cmb_pump = {}
        rows = [
            ("Dash #", ttk.Entry(left, textvariable=self.p_dash, width=8), None),
            ("# of Pumps", self.cb(left, dp["count"], self.p_cnt, 16), "pump_count"),
            ("Pump Pressure", self.cb(left, dp["pressure"], self.p_pres, 10), "pressure"),
            ("Type", self.cb(left, dp["type"], self.p_type, 12), "type"),
            ("HP", ttk.Entry(left, textvariable=self.p_hp, width=8), None),
            ("Material", self.cb(left, dp["material"], self.p_mat), "material"),
            ("Skid Length", ttk.Entry(left, textvariable=self.p_len, width=10), None),
            ("Skid Width", ttk.Entry(left, textvariable=self.p_wid, width=10), None),
            ("Skid Height", ttk.Entry(left, textvariable=self.p_hei, width=10), None),
        ]
        for r,(label_widget, widget, key_name) in enumerate(rows, start=1):
            ttk.Label(left, text=label_widget).grid(row=r, column=0, sticky="e", padx=4, pady=4)
            widget.grid(row=r, column=1, sticky="w", padx=4, pady=4)
            if isinstance(widget, ttk.Combobox) and key_name:
                self.cmb_pump[key_name] = widget

        btns=ttk.Frame(left); btns.grid(row=len(rows)+1, column=0, columnspan=2, pady=(8,0))
        ttk.Button(btns, text="Preview 3 Pump Lines", command=self.preview_pump).pack(side="left", padx=4)
        ttk.Button(btns, text="Save To Job", command=self.save_pump).pack(side="left", padx=4)

        self.pump_table = ResultTable(f, "Pump Output (3 rows)")
        self.pump_table.frame.pack(side="left", fill="both", expand=True, padx=(pad,0))

    def pump_params(self):
        if not self.current_job["id"]:
            messagebox.showerror("No Job", "Select or create a job first."); return None
        return PumpParams(
            job_no=self.current_job["job_no"], dash=self.p_dash.get(),
            pump_count=self.p_cnt.get(), pressure=self.p_pres.get(),
            type_code=self.p_type.get(), hp=float(self.p_hp.get()),
            frame_len_in=int(float(self.p_len.get())), frame_w_in=int(float(self.p_wid.get())),
            frame_h_in=int(float(self.p_hei.get())), material=str(self.p_mat.get())
        )

    def preview_pump(self):
        p = self.pump_params()
        if not p:
            return
        rows = gen_pump_all(p)
        self.pump_table.load(rows)

    def save_pump(self):
        p = self.pump_params()
        if not p:
            return
        rows = gen_pump_all(p)
        insert_items(self.current_job["id"], rows)
        self.refresh_report()
        self.set_status("Pump lines saved")

    # -- Report tab
    def build_report(self):
        pad=10; f=ttk.Frame(self.t_report, padding=pad); f.pack(fill="both", expand=True)
        top = ttk.Frame(f); top.pack(fill="x")
        self.lbl_job_report = ttk.Label(top, text="Job # (select a job)", font=("Segoe UI", 10, "bold"))
        self.lbl_job_report.pack(side="left")

        self.report_tree = ttk.Treeview(f, columns=("id","kind","pn","desc","bom","template","ptype","created"),
                                        show="headings", height=18)
        for col,w in [("id",50),("kind",90),("pn",150),("desc",520),("bom",170),("template",100),("ptype",120),("created",200)]:
            self.report_tree.heading(col, text=col); self.report_tree.column(col, width=w, stretch=(col=="desc"))
        self.report_tree.pack(fill="both", expand=True, pady=(8,8))

        btns=ttk.Frame(f); btns.pack(fill="x")
        ttk.Button(btns, text="Copy PN", command=lambda:self.copy_col("pn")).pack(side="left", padx=4)
        ttk.Button(btns, text="Copy Desc", command=lambda:self.copy_col("desc")).pack(side="left", padx=4)
        ttk.Button(btns, text="Copy BOM", command=lambda:self.copy_col("bom")).pack(side="left", padx=4)
        ttk.Button(btns, text="Export Job JSON", command=self.export_job_json).pack(side="right", padx=4)

    def refresh_report(self):
        for i in self.report_tree.get_children(): self.report_tree.delete(i)
        if not self.current_job["id"]: return
        rows = list_items(self.current_job["id"])
        # sort by part number ascending with numeric-aware parsing
        def pn_key(r):
            pn = r[2]
            # split like 33371-01.1-A -> (base,dash,rest)
            try:
                base, rest = pn.split('-', 1)
                num = []
                acc = ''
                for ch in rest:
                    if ch.isdigit(): acc += ch
                    else:
                        if acc:
                            num.append(int(acc)); acc=''
                        num.append(ch)
                if acc:
                    num.append(int(acc))
                return (int(base), num)
            except Exception:
                return (pn,)
        rows_sorted = sorted(rows, key=pn_key)
        for row in rows_sorted:
            _id,kind,pn,desc,bom,template,ptype,params,created = row
            self.report_tree.insert("", "end", values=(_id,kind,pn,desc,bom,template,ptype,created))

    def col_index(self,key):
        cols=["id","kind","pn","desc","bom","template","ptype","created"]; return cols.index(key)

    def copy_col(self,key):
        sel = self.report_tree.selection()
        if not sel: messagebox.showerror("No selection","Pick a row."); return
        vals = self.report_tree.item(sel[0],"values")
        self.clipboard_clear(); self.clipboard_append(vals[self.col_index(key)]); self.update()
        self.set_status(f"Copied {key.upper()}")

    def export_job_json(self):
        if not self.current_job["id"]: messagebox.showerror("No Job","Pick a job."); return
        rows = list_items(self.current_job["id"])
        payload=[]
        for r in rows:
            _id,kind,pn,desc,bom,template,ptype,params,created = r
            payload.append({"id":_id,"kind":kind,"part_number":pn,"description":desc,"bom":bom,
                            "template":template,"product_type":ptype,"params":json.loads(params),"created_at":created})
        out = {"job": self.current_job, "items": payload}
        # Default to project directory if available
        initialdir = None
        try:
            conn = sqlite3.connect(DASHBOARD_DB); c = conn.cursor()
            c.execute("SELECT job_directory FROM projects WHERE id=?", (self.current_job["id"],))
            r = c.fetchone(); conn.close()
            if r and r[0]: initialdir = r[0]
        except Exception:
            pass
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialdir=initialdir,
            initialfile=f"job_{self.current_job['job_no']}.json",
            filetypes=(("JSON files","*.json"),("All files","*.*"))
        )
        if not filename:
            self.set_status("Export cancelled")
            return
        Path(filename).write_text(json.dumps(out, indent=2), encoding="utf-8")
        self.set_status(f"Exported {filename}")

    # -- Settings tab to edit dropdown options
    def build_settings(self):
        pad=10; f=ttk.Frame(self.t_settings, padding=pad); f.pack(fill="both", expand=True)
        ttk.Label(f, text="Edit dropdown options (comma-separated) and Save", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(f, text="Tip: use <blank> to add an empty option to any list.", foreground="#555").pack(anchor="w", pady=(2,6))
        grid = ttk.Frame(f); grid.pack(fill="both", expand=True, pady=(8,0))

        self.opt_vars = {
            # Heater: 11 dropdowns
            "heater_diam": tk.StringVar(value=",".join([str(x) for x in self.defaults["heater"]["diam"]])),
            "heater_height": tk.StringVar(value=",".join([str(x) for x in self.defaults["heater"]["height"]])),
            "heater_model": tk.StringVar(value=",".join(self.defaults["heater"]["model"])),
            "heater_material": tk.StringVar(value=",".join([str(x) for x in self.defaults["heater"]["material"]])),
            "heater_stack_diam": tk.StringVar(value=",".join([str(x) for x in self.defaults["heater"]["stack_diam"]])),
            "heater_flange": tk.StringVar(value=",".join([str(x) for x in self.defaults["heater"]["flange_inlet"]])),
            "heater_gassize": tk.StringVar(value=",".join([str(x) for x in self.defaults["heater"]["gas_size"]])),
            "heater_gasmount": tk.StringVar(value=",".join(self.defaults["heater"]["gas_mount"])),
            "heater_btu": tk.StringVar(value=",".join([str(x) for x in self.defaults["heater"]["btu"]])),
            "heater_hand": tk.StringVar(value=",".join(self.defaults["heater"]["hand"])),
            "heater_label": tk.StringVar(value=",".join(self.defaults["heater"]["label"])),
            # Tank: 4 dropdowns
            "tank_diam": tk.StringVar(value=",".join([str(x) for x in self.defaults["tank"]["diam"]])),
            "tank_height_ft": tk.StringVar(value=",".join([str(x) for x in self.defaults["tank"]["height_ft"]])),
            "tank_type": tk.StringVar(value=",".join(self.defaults["tank"]["type"])),
            "tank_material": tk.StringVar(value=",".join([str(x) for x in self.defaults["tank"]["material"]])),
            # Pump: 8 dropdowns
            "pump_count": tk.StringVar(value=",".join(self.defaults["pump"]["count"])),
            "pump_pressure": tk.StringVar(value=",".join(self.defaults["pump"]["pressure"])),
            "pump_type": tk.StringVar(value=",".join(self.defaults["pump"]["type"])),
            "pump_hp": tk.StringVar(value=",".join([str(x) for x in self.defaults["pump"]["hp"]])),
            "pump_material": tk.StringVar(value=",".join([str(x) for x in self.defaults["pump"]["material"]])),
        }

        def row(label, key, r):
            ttk.Label(grid, text=label).grid(row=r, column=0, sticky="e", padx=6, pady=6)
            ttk.Entry(grid, textvariable=self.opt_vars[key], width=70).grid(row=r, column=1, sticky="w", padx=6, pady=6)
        r=0
        # Heater section header and divider
        ttk.Label(grid, text="Heater Settings", font=("Segoe UI", 10, "bold")).grid(row=r, column=0, columnspan=2, sticky="w", padx=6, pady=(4,2)); r+=1
        ttk.Separator(grid, orient="horizontal").grid(row=r, column=0, columnspan=2, sticky="ew", padx=6, pady=(0,6)); r+=1
        # Heater
        row("Heater Diameters", "heater_diam", r); r+=1
        row("Heater Heights", "heater_height", r); r+=1
        row("Heater Models", "heater_model", r); r+=1
        row("Heater Materials", "heater_material", r); r+=1
        row("Heater Stack Diameters", "heater_stack_diam", r); r+=1
        row("Heater Flange Inlets", "heater_flange", r); r+=1
        row("Heater Gas Sizes", "heater_gassize", r); r+=1
        row("Heater Gas Mounts", "heater_gasmount", r); r+=1
        row("Heater BTU", "heater_btu", r); r+=1
        row("Heater Hands", "heater_hand", r); r+=1
        row("Heater Labels (0/A/B)", "heater_label", r); r+=1
        # Tank section header and divider
        ttk.Label(grid, text="Tank Settings", font=("Segoe UI", 10, "bold")).grid(row=r, column=0, columnspan=2, sticky="w", padx=6, pady=(8,2)); r+=1
        ttk.Separator(grid, orient="horizontal").grid(row=r, column=0, columnspan=2, sticky="ew", padx=6, pady=(0,6)); r+=1
        # Tank
        row("Tank Diameters", "tank_diam", r); r+=1
        row("Tank Heights (ft)", "tank_height_ft", r); r+=1
        row("Tank Types", "tank_type", r); r+=1
        row("Tank Materials", "tank_material", r); r+=1
        # Pump section header and divider
        ttk.Label(grid, text="Pump Settings", font=("Segoe UI", 10, "bold")).grid(row=r, column=0, columnspan=2, sticky="w", padx=6, pady=(8,2)); r+=1
        ttk.Separator(grid, orient="horizontal").grid(row=r, column=0, columnspan=2, sticky="ew", padx=6, pady=(0,6)); r+=1
        # Pump
        row("Pump Counts", "pump_count", r); r+=1
        row("Pump Pressures", "pump_pressure", r); r+=1
        row("Pump Types", "pump_type", r); r+=1
        row("Pump HP", "pump_hp", r); r+=1
        row("Pump Materials", "pump_material", r); r+=1

        btns = ttk.Frame(f); btns.pack(fill="x", pady=(8,0))
        ttk.Button(btns, text="Save Options", command=self.save_options).pack(side="left")
        ttk.Button(btns, text="Reload Options", command=self.reload_options).pack(side="left", padx=6)
        ttk.Button(btns, text="Load Recommended", command=self.load_recommended_options).pack(side="left")

    def save_options(self):
        # persist to d365_builder.db simple key/value table
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS d365_options (key TEXT PRIMARY KEY, value TEXT)")
        for k,v in self.opt_vars.items():
            c.execute("INSERT OR REPLACE INTO d365_options(key,value) VALUES(?,?)", (k, v.get()))
        conn.commit(); conn.close()
        self.set_status("Options saved")
        # apply immediately to defaults + UI and reflect in Settings fields
        self.apply_options_from_db_to_defaults(); self.update_combobox_values(); self.refresh_settings_fields()

    def reload_options(self):
        # load from db, update defaults and comboboxes
        try:
            conn = sqlite3.connect(DB_PATH); c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS d365_options (key TEXT PRIMARY KEY, value TEXT)")
            c.execute("SELECT key,value FROM d365_options")
            data = dict(c.fetchall()); conn.close()
        except Exception:
            data = {}
        def splitcsv(s):
            items = []
            for raw in s.split(','):
                token = raw.strip()
                if token == "<blank>" or token == "[blank]":
                    items.append("")
                elif token:
                    items.append(token)
            return items
        # Heater lists
        if "heater_diam" in data:
            self.defaults["heater"]["diam"] = splitcsv(data["heater_diam"]) or self.defaults["heater"]["diam"]
        if "heater_height" in data:
            self.defaults["heater"]["height"] = splitcsv(data["heater_height"]) or self.defaults["heater"]["height"]
        if "heater_model" in data:
            self.defaults["heater"]["model"] = splitcsv(data["heater_model"]) or self.defaults["heater"]["model"]
        if "heater_material" in data:
            self.defaults["heater"]["material"] = splitcsv(data["heater_material"]) or self.defaults["heater"]["material"]
        if "heater_stack_diam" in data:
            self.defaults["heater"]["stack_diam"] = splitcsv(data["heater_stack_diam"]) or self.defaults["heater"]["stack_diam"]
        if "heater_flange" in data:
            self.defaults["heater"]["flange_inlet"] = splitcsv(data["heater_flange"]) or self.defaults["heater"]["flange_inlet"]
        if "heater_gassize" in data:
            self.defaults["heater"]["gas_size"] = splitcsv(data["heater_gassize"]) or self.defaults["heater"]["gas_size"]
        if "heater_gasmount" in data:
            self.defaults["heater"]["gas_mount"] = splitcsv(data["heater_gasmount"]) or self.defaults["heater"]["gas_mount"]
        if "heater_btu" in data:
            self.defaults["heater"]["btu"] = splitcsv(data["heater_btu"]) or self.defaults["heater"]["btu"]
        if "heater_hand" in data:
            self.defaults["heater"]["hand"] = splitcsv(data["heater_hand"]) or self.defaults["heater"]["hand"]
        if "heater_label" in data:
            self.defaults["heater"]["label"] = splitcsv(data["heater_label"]) or self.defaults["heater"]["label"]
        # Tank lists
        if "tank_diam" in data:
            self.defaults["tank"]["diam"] = splitcsv(data["tank_diam"]) or self.defaults["tank"]["diam"]
        if "tank_height_ft" in data:
            self.defaults["tank"]["height_ft"] = splitcsv(data["tank_height_ft"]) or self.defaults["tank"]["height_ft"]
        if "tank_type" in data:
            self.defaults["tank"]["type"] = splitcsv(data["tank_type"]) or self.defaults["tank"]["type"]
        if "tank_material" in data:
            self.defaults["tank"]["material"] = splitcsv(data["tank_material"]) or self.defaults["tank"]["material"]
        # Pump lists
        if "pump_count" in data:
            self.defaults["pump"]["count"] = splitcsv(data["pump_count"]) or self.defaults["pump"]["count"]
        if "pump_pressure" in data:
            self.defaults["pump"]["pressure"] = splitcsv(data["pump_pressure"]) or self.defaults["pump"]["pressure"]
        if "pump_type" in data:
            self.defaults["pump"]["type"] = splitcsv(data["pump_type"]) or self.defaults["pump"]["type"]
        if "pump_hp" in data:
            self.defaults["pump"]["hp"] = splitcsv(data["pump_hp"]) or self.defaults["pump"]["hp"]
        # pump frame dimensions are inputs, not editable dropdown sets
        if "pump_material" in data:
            self.defaults["pump"]["material"] = splitcsv(data["pump_material"]) or self.defaults["pump"]["material"]
        self.set_status("Options reloaded")
        self.update_combobox_values(); self.refresh_settings_fields()

    def joincsv(self, seq):
        out=[]
        for v in seq:
            s=str(v).strip()
            if s=="": s="<blank>"
            out.append(s)
        return ",".join(out)

    def ensure_options_seeded(self):
        """Always seed/overwrite options table with defaults (including <blank>)."""
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS d365_options (key TEXT PRIMARY KEY, value TEXT)")
        seeds = {
            # Heater (11)
            "heater_diam": self.joincsv(self.defaults["heater"]["diam"]),
            "heater_height": self.joincsv(self.defaults["heater"]["height"]),
            "heater_model": self.joincsv(self.defaults["heater"]["model"]),
            "heater_material": self.joincsv(self.defaults["heater"]["material"]),
            "heater_stack_diam": self.joincsv(self.defaults["heater"]["stack_diam"]),
            "heater_flange": self.joincsv(self.defaults["heater"]["flange_inlet"]),
            "heater_gassize": self.joincsv(self.defaults["heater"]["gas_size"]),
            "heater_gasmount": self.joincsv(self.defaults["heater"]["gas_mount"]),
            "heater_btu": self.joincsv(self.defaults["heater"]["btu"]),
            "heater_hand": self.joincsv(self.defaults["heater"]["hand"]),
            "heater_label": self.joincsv(self.defaults["heater"]["label"]),
            # Tank (4)
            "tank_diam": self.joincsv(self.defaults["tank"]["diam"]),
            "tank_height_ft": self.joincsv(self.defaults["tank"]["height_ft"]),
            "tank_type": self.joincsv(self.defaults["tank"]["type"]),
            "tank_material": self.joincsv(self.defaults["tank"]["material"]),
            # Pump (5 editable sets)
            "pump_count": self.joincsv(self.defaults["pump"]["count"]),
            "pump_pressure": self.joincsv(self.defaults["pump"]["pressure"]),
            "pump_type": self.joincsv(self.defaults["pump"]["type"]),
            "pump_hp": self.joincsv(self.defaults["pump"]["hp"]),
            "pump_material": self.joincsv(self.defaults["pump"]["material"]),
        }
        for k,v in seeds.items():
            c.execute("INSERT OR REPLACE INTO d365_options(key,value) VALUES(?,?)", (k, v))
        conn.commit(); conn.close()

    def load_recommended_options(self):
        """Force-seed DB with the current defaults lists and reload UI."""
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS d365_options (key TEXT PRIMARY KEY, value TEXT)")
        seeds = {
            "heater_diam": self.joincsv(self.defaults["heater"]["diam"]),
            "heater_height": self.joincsv(self.defaults["heater"]["height"]),
            "heater_model": self.joincsv(self.defaults["heater"]["model"]),
            "heater_material": self.joincsv(self.defaults["heater"]["material"]),
            "heater_stack_diam": self.joincsv(self.defaults["heater"]["stack_diam"]),
            "heater_flange": self.joincsv(self.defaults["heater"]["flange_inlet"]),
            "heater_gassize": self.joincsv(self.defaults["heater"]["gas_size"]),
            "heater_gasmount": self.joincsv(self.defaults["heater"]["gas_mount"]),
            "heater_btu": self.joincsv(self.defaults["heater"]["btu"]),
            "heater_hand": self.joincsv(self.defaults["heater"]["hand"]),
            "heater_label": self.joincsv(self.defaults["heater"]["label"]),
            "tank_diam": self.joincsv(self.defaults["tank"]["diam"]),
            "tank_height_ft": self.joincsv(self.defaults["tank"]["height_ft"]),
            "tank_type": self.joincsv(self.defaults["tank"]["type"]),
            "tank_material": self.joincsv(self.defaults["tank"]["material"]),
            "pump_count": self.joincsv(self.defaults["pump"]["count"]),
            "pump_pressure": self.joincsv(self.defaults["pump"]["pressure"]),
            "pump_type": self.joincsv(self.defaults["pump"]["type"]),
            "pump_hp": self.joincsv(self.defaults["pump"]["hp"]),
            "pump_material": self.joincsv(self.defaults["pump"]["material"]),
        }
        for k,v in seeds.items():
            c.execute("INSERT OR REPLACE INTO d365_options(key,value) VALUES(?,?)", (k, v))
        conn.commit(); conn.close()
        self.set_status("Recommended options loaded")
        self.apply_options_from_db_to_defaults(); self.update_combobox_values(); self.refresh_settings_fields()

    def apply_options_from_db_to_defaults(self):
        """Load saved options from d365_options into defaults before UI build (no opt_vars dependency)."""
        try:
            conn = sqlite3.connect(DB_PATH); c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS d365_options (key TEXT PRIMARY KEY, value TEXT)")
            c.execute("SELECT key,value FROM d365_options")
            rows = c.fetchall(); conn.close()
        except Exception:
            rows = []
        def splitcsv(s):
            items=[]
            for raw in s.split(','):
                t=raw.strip()
                if t in ("<blank>","[blank]"): items.append("")
                elif t: items.append(t)
            return items
        data = dict(rows)
        if not data:
            return
        # mirror the same keys handled in reload_options
        if "heater_diam" in data:
            self.defaults["heater"]["diam"] = splitcsv(data["heater_diam"]) or self.defaults["heater"]["diam"]
        if "heater_height" in data:
            self.defaults["heater"]["height"] = splitcsv(data["heater_height"]) or self.defaults["heater"]["height"]
        if "heater_model" in data:
            self.defaults["heater"]["model"] = splitcsv(data["heater_model"]) or self.defaults["heater"]["model"]
        if "heater_material" in data:
            self.defaults["heater"]["material"] = splitcsv(data["heater_material"]) or self.defaults["heater"]["material"]
        if "heater_stack_diam" in data:
            self.defaults["heater"]["stack_diam"] = splitcsv(data["heater_stack_diam"]) or self.defaults["heater"]["stack_diam"]
        if "heater_flange" in data:
            self.defaults["heater"]["flange_inlet"] = splitcsv(data["heater_flange"]) or self.defaults["heater"]["flange_inlet"]
        if "heater_gassize" in data:
            self.defaults["heater"]["gas_size"] = splitcsv(data["heater_gassize"]) or self.defaults["heater"]["gas_size"]
        if "heater_gasmount" in data:
            self.defaults["heater"]["gas_mount"] = splitcsv(data["heater_gasmount"]) or self.defaults["heater"]["gas_mount"]
        if "heater_btu" in data:
            self.defaults["heater"]["btu"] = splitcsv(data["heater_btu"]) or self.defaults["heater"]["btu"]
        if "heater_hand" in data:
            self.defaults["heater"]["hand"] = splitcsv(data["heater_hand"]) or self.defaults["heater"]["hand"]
        if "heater_label" in data:
            self.defaults["heater"]["label"] = splitcsv(data["heater_label"]) or self.defaults["heater"]["label"]

        if "tank_diam" in data:
            self.defaults["tank"]["diam"] = splitcsv(data["tank_diam"]) or self.defaults["tank"]["diam"]
        if "tank_height_ft" in data:
            self.defaults["tank"]["height_ft"] = splitcsv(data["tank_height_ft"]) or self.defaults["tank"]["height_ft"]
        if "tank_type" in data:
            self.defaults["tank"]["type"] = splitcsv(data["tank_type"]) or self.defaults["tank"]["type"]
        if "tank_material" in data:
            self.defaults["tank"]["material"] = splitcsv(data["tank_material"]) or self.defaults["tank"]["material"]

        if "pump_count" in data:
            self.defaults["pump"]["count"] = splitcsv(data["pump_count"]) or self.defaults["pump"]["count"]
        if "pump_pressure" in data:
            self.defaults["pump"]["pressure"] = splitcsv(data["pump_pressure"]) or self.defaults["pump"]["pressure"]
        if "pump_type" in data:
            self.defaults["pump"]["type"] = splitcsv(data["pump_type"]) or self.defaults["pump"]["type"]
        if "pump_hp" in data:
            self.defaults["pump"]["hp"] = splitcsv(data["pump_hp"]) or self.defaults["pump"]["hp"]
        if "pump_material" in data:
            self.defaults["pump"]["material"] = splitcsv(data["pump_material"]) or self.defaults["pump"]["material"]

    def set_status(self, text):
        self.status_var.set(text)

    def update_combobox_values(self):
        # Apply defaults back to comboboxes while preserving current selection when possible
        def apply_combo(combo, values, var):
            if combo is None:
                return
            combo["values"] = [str(v) for v in values]
            cur = var.get()
            if str(cur) in [str(v) for v in values]:
                combo.set(str(cur))
            elif values:
                combo.set(str(values[0]))
        dh = self.defaults["heater"]
        if hasattr(self, 'cmb_heater'):
            apply_combo(self.cmb_heater.get("diameter_in"), dh["diam"], self.h_diam)
            apply_combo(self.cmb_heater.get("height_in"), dh["height"], self.h_hgt)
            apply_combo(self.cmb_heater.get("model"), dh["model"], self.h_model)
            apply_combo(self.cmb_heater.get("material"), dh["material"], self.h_mat)
            apply_combo(self.cmb_heater.get("stack_diam_in"), dh["stack_diam"], self.h_stack)
            apply_combo(self.cmb_heater.get("flange_inlet_in"), dh["flange_inlet"], self.h_flange)
            apply_combo(self.cmb_heater.get("gas_train_size_in"), dh["gas_size"], self.h_gsize)
            apply_combo(self.cmb_heater.get("gas_train_mount"), dh["gas_mount"], self.h_gmount)
            apply_combo(self.cmb_heater.get("btu_mmbtu"), dh["btu"], self.h_btu)
            apply_combo(self.cmb_heater.get("hand"), dh["hand"], self.h_hand)
            apply_combo(self.cmb_heater.get("label"), dh["label"], self.h_label)

        dt = self.defaults["tank"]
        if hasattr(self, 'cmb_tank'):
            apply_combo(self.cmb_tank.get("diameter_in"), dt["diam"], self.t_diam)
            apply_combo(self.cmb_tank.get("height_ft"), dt["height_ft"], self.t_hft)
            apply_combo(self.cmb_tank.get("type"), dt["type"], self.t_type)
            apply_combo(self.cmb_tank.get("material"), dt["material"], self.t_mat)

        dp = self.defaults["pump"]
        if hasattr(self, 'cmb_pump'):
            apply_combo(self.cmb_pump.get("pump_count"), dp["count"], self.p_cnt)
            apply_combo(self.cmb_pump.get("pressure"), dp["pressure"], self.p_pres)
            apply_combo(self.cmb_pump.get("type"), dp["type"], self.p_type)
            # HP and frame dimensions are Entry fields; skip if not comboboxes
            apply_combo(self.cmb_pump.get("hp"), dp.get("hp", []), self.p_hp)
            apply_combo(self.cmb_pump.get("frame_len_in"), dp.get("len", []), self.p_len)
            apply_combo(self.cmb_pump.get("frame_w_in"), dp.get("wid", []), self.p_wid)
            apply_combo(self.cmb_pump.get("frame_h_in"), dp.get("hei", []), self.p_hei)
            apply_combo(self.cmb_pump.get("material"), dp["material"], self.p_mat)

    def refresh_settings_fields(self):
        """Update Settings tab entry fields (opt_vars) from current defaults so changes are visible."""
        if not hasattr(self, 'opt_vars'):
            return
        d = self.defaults
        # Heater
        self.opt_vars["heater_diam"].set(
            ",".join([str(x) for x in d["heater"]["diam"]])
        )
        self.opt_vars["heater_height"].set(
            ",".join([str(x) for x in d["heater"]["height"]])
        )
        self.opt_vars["heater_model"].set(
            ",".join([str(x) for x in d["heater"]["model"]])
        )
        self.opt_vars["heater_material"].set(
            ",".join([str(x) for x in d["heater"]["material"]])
        )
        self.opt_vars["heater_stack_diam"].set(
            ",".join([str(x) for x in d["heater"]["stack_diam"]])
        )
        self.opt_vars["heater_flange"].set(
            ",".join([str(x) for x in d["heater"]["flange_inlet"]])
        )
        self.opt_vars["heater_gassize"].set(
            ",".join([str(x) for x in d["heater"]["gas_size"]])
        )
        self.opt_vars["heater_gasmount"].set(
            ",".join([str(x) for x in d["heater"]["gas_mount"]])
        )
        self.opt_vars["heater_btu"].set(
            ",".join([str(x) for x in d["heater"]["btu"]])
        )
        self.opt_vars["heater_hand"].set(
            ",".join([str(x) for x in d["heater"]["hand"]])
        )
        self.opt_vars["heater_label"].set(
            ",".join([str(x) for x in d["heater"]["label"]])
        )
        # Tank
        self.opt_vars["tank_diam"].set(
            ",".join([str(x) for x in d["tank"]["diam"]])
        )
        self.opt_vars["tank_height_ft"].set(
            ",".join([str(x) for x in d["tank"]["height_ft"]])
        )
        self.opt_vars["tank_type"].set(
            ",".join([str(x) for x in d["tank"]["type"]])
        )
        self.opt_vars["tank_material"].set(
            ",".join([str(x) for x in d["tank"]["material"]])
        )
        # Pump
        self.opt_vars["pump_count"].set(
            ",".join([str(x) for x in d["pump"]["count"]])
        )
        self.opt_vars["pump_pressure"].set(
            ",".join([str(x) for x in d["pump"]["pressure"]])
        )
        self.opt_vars["pump_type"].set(
            ",".join([str(x) for x in d["pump"]["type"]])
        )
        self.opt_vars["pump_hp"].set(
            ",".join([str(x) for x in d["pump"]["hp"]])
        )
        self.opt_vars["pump_material"].set(
            ",".join([str(x) for x in d["pump"]["material"]])
        )

# ---- Result table widget (with Copy buttons) ----
class ResultTable:
    def __init__(self, parent, title):
        self.frame = ttk.LabelFrame(parent, text=title, padding=10)
        cols=("pn","desc","bom","template","ptype")
        self.tree = ttk.Treeview(self.frame, columns=cols, show="headings", height=16)
        self.tree.heading("pn", text="Item Number"); self.tree.column("pn", width=160)
        self.tree.heading("desc", text="Description"); self.tree.column("desc", width=560)
        self.tree.heading("bom", text="BOM"); self.tree.column("bom", width=170)
        self.tree.heading("template", text="Template"); self.tree.column("template", width=110)
        self.tree.heading("ptype", text="Product Type"); self.tree.column("ptype", width=120)
        self.tree.pack(fill="both", expand=True)
        btns = ttk.Frame(self.frame); btns.pack(fill="x", pady=(6,0))
        ttk.Button(btns, text="Copy PN", command=lambda:self.copy_col("pn")).pack(side="left", padx=4)
        ttk.Button(btns, text="Copy Desc", command=lambda:self.copy_col("desc")).pack(side="left", padx=4)
        ttk.Button(btns, text="Copy BOM", command=lambda:self.copy_col("bom")).pack(side="left", padx=4)

    def load(self, rows):
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in rows:
            self.tree.insert("", "end", values=(r["pn"], r["desc"], r["bom"], r["template"], r["ptype"]))

    def copy_col(self, key):
        sel = self.tree.selection()
        if not sel: messagebox.showerror("No selection","Pick a row."); return
        col_map={"pn":0,"desc":1,"bom":2}
        vals = self.tree.item(sel[0],"values")
        text = vals[col_map[key]]
        r = self.frame.winfo_toplevel()
        r.clipboard_clear(); r.clipboard_append(text); r.update()
        messagebox.showinfo("Copied", f"Copied {key.upper()}")

# -------------- Main --------------
if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='D365 Import Formatter')
    parser.add_argument('--job', type=str, help='Job number to preload')
    args = parser.parse_args()
    
    init_db()
    defaults = load_workbook_defaults(WORKBOOK_JSON)
    app = App(defaults)
    
    # If job number provided, show it in the interface
    if args.job:
        print(f"D365 Import Formatter opened with job number: {args.job}")
    
    app.mainloop()
