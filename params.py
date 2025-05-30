import os
import json
import math
import tkinter as tk
from tkinter import ttk, messagebox

# ─── CONFIGURATION ───────────────────────────────────────
PARAM_DIR    = r"C:\Users\Asus\Documents\FRI\4. godina\2. semestar\Napredna računarska grafika\Seminarska\parameters"
NUM_COLUMNS  = 2

# ─── LIST OF PARAMETERS ───────────────────────────────────
# key,    type,    default,             (optional) choices
PARAMS = [
    ("texture",                str,   "random", ["1", "2", "3", "4", "5", "6", "random"]),
    ("name",                   str,   "Log",    None),
    ("length",                 float, 5.0,      None),
    ("radius_start",           float, 0.5,      None),
    ("radius_center",          float, 0.45,     None),
    ("radius_end",             float, 0.4,      None),
    ("rings",                  int,   30,       None),
    ("verts_per_ring",         int,   80,       None),
    ("taper_shape",            str,   "quadratic", ["linear", "exponential", "quadratic"]),
    ("taper_rate",             float, 8.0,      None),
    ("curve_count",            int,   0,        None),
    ("curve_strength",         float, 0.3,      None),
    ("twist_angle",            float, 0.0,      None),
    ("twist_direction",        str,   "Z",      ["X", "Y", "Z"]),
    ("ellipse_ratio",          float, 1.1,      None),
    ("oval_region_fraction",   float, 0.8,      None),
    ("eccentricity_offset",    float, 0.5,      None),
    ("eccentricity_angle",     float, 0.0,      None),
    ("groove_count",           int,   2,        None),
    ("groove_width",           float, math.pi/4, None),
    ("groove_depth",           float, 0.02,     None),
    ("noise_scale",            float, 3.0,      None),
    ("bark_roughness_depth",   float, 0.1,      None),
    ("bark_roughness_level",   float, 1.0,      None),
    ("flange_count",           int,   3,        None),
    ("flange_width",           float, 0.05,     None),
    ("hue",                    float, 0.02,     None),
    ("saturation",             float, 1.1,      None),
    ("value",                  float, 1.05,     None),
    ("bump_strength",          float, 1.0,      None),
    ("disp_strength",          float, 0.05,     None),
]

# ─── METADATA: ranges & descriptions ─────────────────────
PARAM_METADATA = {
    "texture":                {"range": None,           "desc": "Which texture set to use: 1–6, or 'random' for a random choice."},
    "name":                   {"range": None,           "desc": "Unique identifier for this log (becomes JSON filename)."},
    "length":                 {"range": (0.1, 20.0),    "desc": "Total length of the log in Blender units."},
    "radius_start":           {"range": (0.01, 5.0),    "desc": "Radius at the base of the log."},
    "radius_center":          {"range": (0.01, 5.0),    "desc": "Middle radius before tapering to the end."},
    "radius_end":             {"range": (0.01, 5.0),    "desc": "Radius at the tip of the log."},
    "rings":                  {"range": (3, 200),       "desc": "Number of circular cross-sections along the length."},
    "verts_per_ring":         {"range": (3, 512),       "desc": "Number of vertices around each ring (controls smoothness)."},
    "taper_shape":            {"range": None,           "desc": "How the radius transitions: linear, exponential, or quadratic."},
    "taper_rate":             {"range": (0.1, 20.0),    "desc": "Controls the exponent when taper_shape is 'exponential'."},
    "curve_count":            {"range": (0, 10),        "desc": "Number of sine-cosine wave cycles along the log."},
    "curve_strength":         {"range": (0.0, 5.0),     "desc": "Amplitude of the curve deformation."},
    "twist_angle":            {"range": (0.0, 360.0),   "desc": "Total degrees of twist along the log."},
    "twist_direction":        {"range": None,           "desc": "Axis (X/Y/Z) around which the log twists."},
    "ellipse_ratio":          {"range": (0.1, 5.0),     "desc": "Ratio between X and Y when log cross-section is elliptical."},
    "oval_region_fraction":   {"range": (0.0, 1.0),     "desc": "Portion of the log (0–1) that is elliptical rather than circular."},
    "eccentricity_offset":    {"range": (0.0, 2.0),     "desc": "Offset of the log’s centerline for eccentric cross-sections."},
    "eccentricity_angle":     {"range": (0.0, 360.0),   "desc": "Rotation angle of that eccentric offset."},
    "groove_count":           {"range": (0, 20),        "desc": "How many bark grooves run along the log."},
    "groove_width":           {"range": (0.0, math.pi), "desc": "Angular width (in radians) of each groove."},
    "groove_depth":           {"range": (0.0, 1.0),     "desc": "Depth of the grooves carved into the bark."},
    "noise_scale":            {"range": (0.0, 10.0),    "desc": "Scale of Perlin noise applied to the surface."},
    "bark_roughness_depth":   {"range": (0.0, 1.0),     "desc": "Amplitude of noise displacement."},
    "bark_roughness_level":   {"range": (0.0, 5.0),     "desc": "Intensity multiplier for bark roughness."},
    "flange_count":           {"range": (0, 10),        "desc": "Number of raised flanges (rings) along the log."},
    "flange_width":           {"range": (0.0, 1.0),     "desc": "Thickness of those flanges."},
    "hue":                    {"range": (0.0, 1.0),     "desc": "Hue shift applied to bark texture."},
    "saturation":             {"range": (0.0, 2.0),     "desc": "Saturation multiplier for bark texture."},
    "value":                  {"range": (0.0, 2.0),     "desc": "Brightness multiplier for bark texture."},
    "bump_strength":          {"range": (0.0, 5.0),     "desc": "Strength of normal-map bump effect."},
    "disp_strength":          {"range": (0.0, 1.0),     "desc": "Strength of displacement map on bark."},
}

# ─── TOOLTIP HELPER ──────────────────────────────────────
class ToolTip:
    """Creates a tooltip for a given widget as you hover."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self._enter)
        widget.bind("<Leave>", self._leave)

    def _enter(self, event=None):
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert") if self.widget.bbox("insert") else (0,0,0,0)
        x += self.widget.winfo_rootx() + 20
        y += self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         wraplength=300)
        label.pack(ipadx=1, pady=1)

    def _leave(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

# ─── PARAM EDITOR UI ──────────────────────────────────────
class ParamEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Procedural Log Parameter Editor")
        self.entries = {}
        self._build_ui()

    def _build_ui(self):
        frm = ttk.Frame(self, padding=10)
        frm.grid(row=0, column=0, sticky="nsew")

        total = len(PARAMS)
        rows_per_col = math.ceil(total / NUM_COLUMNS)

        for idx, (key, typ, default, choices) in enumerate(PARAMS):
            col = idx // rows_per_col
            row = idx % rows_per_col

            # build label with range if available
            meta = PARAM_METADATA.get(key, {})
            rng = meta.get("range")
            range_str = f" [{rng[0]}–{rng[1]}]" if rng else ""
            label = ttk.Label(frm, text=key + range_str)
            label.grid(row=row, column=col*2, padx=5, pady=2, sticky="e")

            # build input widget
            if choices:
                widget = ttk.Combobox(frm, values=choices, state="readonly")
                widget.set(default)
            else:
                widget = ttk.Entry(frm)
                widget.insert(0, str(default))

            widget.grid(row=row, column=col*2 + 1, padx=5, pady=2, sticky="we")
            self.entries[key] = (widget, typ)

            # attach tooltip if description exists
            desc = meta.get("desc")
            if desc:
                ToolTip(widget, desc)

        # Save & Help buttons
        btn_frame = ttk.Frame(frm)
        btn_frame.grid(
            row=rows_per_col + 1,
            column=0,
            columnspan=NUM_COLUMNS * 2,
            pady=(10, 0),
            sticky="we"
        )
        save_btn = ttk.Button(btn_frame, text="Save", command=self.save_json)
        save_btn.pack(side="left", expand=True, fill="x", padx=(0,5))
        help_btn = ttk.Button(btn_frame, text="Help", command=self.show_help)
        help_btn.pack(side="left", expand=True, fill="x", padx=(5,0))

        # allow columns to expand
        for c in range(NUM_COLUMNS * 2):
            frm.columnconfigure(c, weight=1)
        self.columnconfigure(0, weight=1)

    def save_json(self):
        data = {}
        try:
            for key, (widget, typ) in self.entries.items():
                val = widget.get()
                data[key] = typ(val) if typ in (int, float) else val
        except ValueError as e:
            messagebox.showerror("Invalid input", str(e))
            return

        os.makedirs(PARAM_DIR, exist_ok=True)
        filename = f"{data.get('name', 'LogParameters')}.json"
        out_path = os.path.join(PARAM_DIR, filename)

        try:
            with open(out_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            messagebox.showerror("Save Error", str(e))
            return

        messagebox.showinfo("Saved", f"Parameters written to:\n{out_path}")

    def show_help(self):
        """Pop up a window listing all params with their meaning & ranges."""
        lines = []
        for key, meta in PARAM_METADATA.items():
            rng = meta.get("range")
            rstr = f" (range {rng[0]}–{rng[1]})" if rng else ""
            lines.append(f"{key}{rstr}: {meta['desc']}")
        help_text = "\n".join(lines)
        # use a scrollable text widget if very long
        win = tk.Toplevel(self)
        win.title("Parameter Help")
        txt = tk.Text(win, wrap="word", width=60, height=20)
        txt.insert("1.0", help_text)
        txt.config(state="disabled")
        txt.pack(expand=True, fill="both", padx=10, pady=10)
        ttk.Button(win, text="Close", command=win.destroy).pack(pady=(0,10))

if __name__ == "__main__":
    ParamEditor().mainloop()
