#!/usr/bin/env python3
"""Build pages/assets/explorer/explorer.json, the cross-reference index behind pages/explorer.html.

Everything is read from this repository; run from the repository root:

    python3 pages/tools/build_explorer_data.py

Needs: python3 with pandas and numpy, and `pdftotext` (poppler).

What it links, and how:
  * 3D model parts        derived/3d/gunnerus-parts.json (SFI group and C-JOB list item per node)
  * Main equipment list   extended/CJOB/docs/List of Main Equipment Rev0.pdf, parsed (items 1-127)
  * Specification         extended/CJOB/docs/Specification Rev0.pdf, lines that name a list item
  * Drawings              text found in each drawing's DXF, matched to list items with the
                          keyword patterns in KEYWORDS below (the matched text is kept as evidence)
  * GA metadata           metadata/gunnerus_metadata.json, equipment entries linked by hand (META_LINKS)
  * Weight calculation    extended/CJOB/docs/Weight Calculation Rev0.xlsx, SFI main groups 2-9
  * Operational data      operational/wave-shielding-2023, channels linked to parts by name,
                          reduced to 10-s means for the sparklines
  * Known issues          the README "Known issues" table, linked by hand (ISSUES)
Matches are only as good as the drawing text and the keyword patterns: review them when either changes.
"""
import gzip, json, re, subprocess, sys, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "pages/assets/explorer/explorer.json"
CASE = ROOT / "operational/wave-shielding-2023"

# ----------------------------------------------------------------------------------------------
# Drawings (same slugs as the thumbnails in pages/assets/thumbs)
DRAWINGS = [
    ("ga-gunnerus", "General arrangement", "polarkonsult", "GA Gunnerus Rev1", "pk"),
    ("tank-plan", "Tank plan", "polarkonsult", "Tank Plan Rev1", "pk"),
    ("lines-plan", "Lines plan", "polarkonsult", "Lines Plan Rev0", "pk"),
    ("profile-and-plan", "Profile and plan", "polarkonsult", "Profile and Plan Rev0", "pk"),
    ("midship-section", "Midship section", "polarkonsult", "Midship Section Rev0", "pk"),
    ("shell-expansion", "Shell expansion", "polarkonsult", "Shell Expansion Rev0", "pk"),
    ("engine-room-arrangement", "Engine room arrangement", "extended/CJOB", "Engine Room Arrangement Rev0", "cj"),
    ("construction-plan-deck-and-double-bottom", "Construction plan, deck and double bottom", "extended/CJOB", "Construction Plan Deck and Double Bottom Rev0", "cj"),
    ("construction-plan-longitudinal-section", "Construction plan, longitudinal section", "extended/CJOB", "Construction Plan Longitudinal Section Rev0", "cj"),
    ("construction-plan-transverse-section", "Construction plan, transverse section", "extended/CJOB", "Construction Plan Transverse Section Rev0", "cj"),
    ("draught-and-hullmarks", "Draught and hullmarks", "extended/CJOB", "Draught and Hullmarks Rev0", "cj"),
    ("freeboard-plan", "Freeboard plan", "extended/CJOB", "Freeboard Plan Rev0", "cj"),
    ("retractable-telescopic-divers-platform-arrangement", "Diver's platform arrangement", "extended/CJOB", "Retractable Telescopic Diver's Platform Arrangement Rev0", "cj"),
    ("safety-fire-zone-plan", "Safety fire zone plan", "extended/CJOB", "Safety Fire Zone Plan Rev0", "cj"),
    ("tank-arrangement", "Tank arrangement", "extended/CJOB", "Tank Arrangement Rev0", "cj"),
]

# Drawing-text patterns per C-JOB list item (matched against upper-cased DXF text).
# Items not listed here have no reliable label on any drawing.
KEYWORDS = {
    1: r"\bMOB\b|RESCUE BOAT|CAPACITY: 6 PERSONS", 2: r"DAVIT", 3: r"LIFE ?RAFT|CAPACITY: 25 PERSONS",
    4: r"SURVIVAL SUIT|\bSUITS\b", 5: r"WORK VEST", 6: r"LIFE ?JACKET|REDNINGSVEST", 7: r"LIFE ?BUOY",
    8: r"\bEPIRB\b|EMERGENCY POSITION INDICATING", 9: r"\bSART\b|RADAR TRANSPONDER", 10: r"AIRCRAFT",
    11: r"FIRE ALARM|DETECTION AND ALARM|AUTOMATIC FIRE ALARM", 12: r"\bCO2\b",
    13: r"FIRE RESISTANT PROTECTING|FIREMAN", 14: r"SEARCH ?LIGHT|FLOODLIGHT", 15: r"EMBARKATION LADDER",
    16: r"PYROTECHN|ROCKET|DISTRESS SIGNAL", 17: r"WINDLASS", 18: r"\bANCHOR\b|\bANCHORS\b",
    19: r"ANCHOR WINCH", 20: r"BOLLARD",
    21: r"HYDROPHORE PUMP", 22: r"HYDROPHORE TANK", 23: r"HEATER", 24: r"CIRCULATION PUMP",
    25: r"WATER SAMPLING", 26: r"FIRE ?PUMP", 27: r"BALLAST PUMP", 28: r"HYDRAULICS? PUMP", 29: r"HYDRAULICS? PUMP",
    30: r"HYDRAULICS? OIL TANK", 31: r"BOX COOLER", 32: r"BOX COOLER", 33: r"SEA WATER PUMP FOR HYDR",
    34: r"SEWAGE TREATMENT", 35: r"BILGE PUMP", 36: r"PUMPS? UNIT",
    37: r"BILGE PUMP", 38: r"SEPTIC/GREY WATER DISCHARGE", 39: r"SLUDGE DISCHARGE", 40: r"HYDROPHORE TANK",
    41: r"HYDROPHORE PUMP", 42: r"VALVE CHEST - FUEL", 43: r"FUEL OIL TRANSFER PUMP", 44: r"VALVE CHEST - BALLAST",
    45: r"TUNED FILTER", 46: r"PORT SIDE STEERING GEAR TANK", 47: r"PORT SIDE PM AZIMUTH DRIVE",
    48: r"PORT SIDE CENTRAL SHAFT TANK", 49: r"PORT SIDE PM AZIMUTH DRIVE", 50: r"SB SIDE CENTRAL SHAFT TANK",
    51: r"SB SIDE PM AZIMUTH DRIVE", 52: r"WATER UNIT", 53: r"HOT ?WATER TANK", 54: r"AIR COMPRESSOR",
    55: r"AIR TANK", 56: r"CHILLER", 57: r"HYDRAULIC GENERATOR", 58: r"SEPARATOR",
    59: r"FUEL OIL TRANSFER PUMP", 60: r"STRAINER", 61: r"PREFILTER", 62: r"VALVE CHEST", 63: r"FUEL OIL SEPARATOR",
    64: r"GEAR OIL COOLER", 65: r"SEA WATER PUMP FOR HYDR", 66: r"GEAR OIL COOLER", 67: r"^HYDR(AULIC)?\.? OIL COOLER",
    68: r"BOX COOLER", 69: r"BOX COOLER", 70: r"COOLING UNIT", 71: r"COMPRESSED AIR\b(?! BREADTHING)",
    72: r"MAIN ENGINE|DIESEL SET", 73: r"(?<!HYDRAULIC )\bGENERATOR\b|DIESEL SET GEN", 74: r"STEERING GEAR",
    75: r"BOW ?THRUSTER|MARKING OF THRUSTER", 76: r"AZIPOD|PM AZIMUTH DRIVE",
    77: r"\bCRANE\b|KRAN", 78: r"\bCTD\b", 79: r"LIFE ?BOAT CRANE|DAVIT", 80: r"A-FRAME|GANTRY",
    81: r"A-FRAME", 82: r"\bROV\b", 83: r"TRAWL", 84: r"NET DRUM", 85: r"\bCRANE\b|KRAN",
    86: r"\bCTD\b", 87: r"DIVING PLATFORM|DIVER'S PLATFORM|PLATFORM 1500X800", 88: r"HYDRAULIC AGGREGATE",
    89: r"CAPSTAN", 90: r"WORK ?BOAT",
    91: r"BATTERY BOX", 92: r"TRANSFORMER|TRAFO", 93: r"MAIN SWITCHB", 94: r"FREQ(UENCY)?\.? CONV(ERTER)?\.?(?! BOW)",
    95: r"FREQUENCY CONVERTER BOWTHRUSTER", 96: r"STARTER BOX", 97: r"EL\. CABINET",
    98: r"DYNAMIC POSITIONING|\bDP\b", 99: r"HIPAP", 101: r"HIPAP", 110: r"\bRADAR\b(?! TRANSPONDER)",
    111: r"RADAR TRANSPONDER|\bSART\b", 112: r"\bLOG\b", 113: r"ECHO ?SOUNDER|TRANSDUCERS FOR ECHO",
    114: r"ECHO ?SOUNDER|TRANSDUCERS FOR ECHO", 119: r"\bAIS\b", 121: r"GMDSS", 122: r"\bVHF\b",
}

# Drawings left out of the equipment text search. The lines plan DXF also carries a copy of the
# GA deck-plan labels outside the printed sheet, so every GA label would be counted twice.
SKIP_TEXT_SEARCH = {"lines-plan"}

# Item lists per 3D part where gunnerus-parts.json gives one range for both drives
PART_ITEMS = {"part19": [46, 47, 48, 49, 76], "part20": [50, 51, 76]}

# GA metadata equipment entries (by index) -> 3D parts and list items. Only confident links.
META_LINKS = {
    1: {"parts": ["part03"], "items": [77, 85]},
    2: {"parts": ["part02"], "items": [80], "note": "Linked by position: the stern gantry is the stern A-frame."},
    6: {"parts": ["part19", "part20"], "items": [47, 49, 51, 76], "note": "The metadata calls these cycloidal propulsors; the engine room arrangement shows PM azimuth drives. See Known issues."},
    7: {"parts": ["part21"], "items": [72]},
    8: {"parts": [], "items": [93]},
    9: {"parts": [], "items": [94]},
    10: {"parts": ["part08"], "items": []},
    12: {"parts": ["part15", "part16"], "items": [1, 2]},
}

# Known issues (README) -> parts / items / weight groups
ISSUES = [
    {"id": "dup-cranes", "title": "Duplicate cranes in the equipment list",
     "text": "Items 77 and 85 are both a main deck crane, and items 78 and 86 both a CTD crane.", "items": [77, 78, 85, 86]},
    {"id": "dup-azi", "title": "Azimuth drives listed more than once",
     "text": "Items 47 and 49 are both named “Port Side PM Azimuth Drive”; item 76 lists the same drives again as “Azipod 500 kW”.", "items": [47, 49, 51, 76]},
    {"id": "engine-rating", "title": "Main engine rating",
     "text": "450 kW in the list of main equipment (item 72) and the specification; 475 kW on the engine room arrangement.", "items": [72]},
    {"id": "meta-propulsion", "title": "Propulsion in the GA metadata",
     "text": "The metadata infers cycloidal propulsors from the GA geometry. That is wrong: the engine room arrangement identifies PM azimuth drives, port and starboard.", "items": [47, 49, 51, 76]},
    {"id": "deadweight", "title": "Deadweight", "text": "164 t on the GA drawing; 169 t on the lines plan and engine room arrangement.", "groups": ["2"]},
    {"id": "depth-a", "title": "Depth to A-deck", "text": "6.60 m on the GA drawing; 6.687 m on the lines plan and engine room arrangement.", "groups": ["2"]},
    {"id": "tanks", "title": "Tank list in the metadata", "text": "Does not reconcile with the capacity totals. Use Tank Plan Rev1 (tanks 1–15, 202.42 m³ net) instead.", "groups": ["2"]},
    {"id": "weight-ref", "title": "Broken references in the weight calculation",
     "text": "Row 8 (ship common systems) of the weight calculation spreadsheet shows #REF! in three cells; its weight and centre of gravity still compute.", "groups": ["8"]},
]

# Drawings whose subject is a whole 3D group (independent of the text search)
GROUP_DRAWINGS = {
    "hull": ["lines-plan", "shell-expansion", "midship-section", "profile-and-plan", "construction-plan-deck-and-double-bottom",
             "construction-plan-longitudinal-section", "construction-plan-transverse-section", "draught-and-hullmarks",
             "tank-plan", "tank-arrangement", "freeboard-plan"],
    "super": ["ga-gunnerus", "construction-plan-deck-and-double-bottom", "construction-plan-longitudinal-section", "freeboard-plan", "safety-fire-zone-plan"],
    "outfit": ["ga-gunnerus", "safety-fire-zone-plan", "freeboard-plan"],
    "g1": ["safety-fire-zone-plan", "ga-gunnerus"],
    "g4": ["engine-room-arrangement"],
    "g5": ["ga-gunnerus", "retractable-telescopic-divers-platform-arrangement"],
}

# Weight calculation groups -> 3D group keys (SFI main group of each 3D group)
WEIGHT_TO_3D = {"2": ["hull", "super"], "3": ["g5"], "4": ["g7", "g2"], "5": ["outfit", "g1"], "6": ["g4"]}

# Operational channels -> parts (by column prefix) and list items
CHANNEL_PARTS = [
    (r"^crane_", ["part03"], [77, 85]),
    (r"^azi_port_", ["part19"], [47, 76]),
    (r"^azi_stbd_", ["part20"], [51, 76]),
    (r"^engine\d_", ["part21"], [72]),
    (r"^tunnel_thruster_", ["part23"], [75]),
    (r"^(heading|roll|pitch|heave|yaw)", [], [100, 102, 108]),
    (r"^(lat|lon|cog|sog|speed)", [], [100, 108]),
    (r"^wind_", [], [98]),
]
KEY_CHANNELS = {  # shown as sparklines first
    "part03": ["crane_slewing_angle_deg", "crane_main_boom_angle_deg", "hook_acc_rms"],
    "part19": ["azi_port_rpmfeedback", "azi_port_load_feedback", "azi_port_azimuth_feedback"],
    "part20": ["azi_stbd_rpmfeedback", "azi_stbd_load_feedback", "azi_stbd_azimuth_order"],
    "part21": ["engine1_engine_load", "engine2_engine_load", "engine3_engine_load", "engine1_fuel_consumption"],
    "part23": ["tunnel_thruster_feedback_pct"],
    "g7": ["heading_deg", "roll_deg", "pitch_deg", "heave_m", "wind_speed_kn"],
}


def pdf_pages(path):
    txt = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True, check=True).stdout
    return txt.split("\f")


def dxf_texts(path):
    """TEXT / MTEXT / ATTRIB strings of a DXF, formatting codes stripped."""
    out, ent = [], None
    lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    for k in range(0, len(lines) - 1, 2):
        code, val = lines[k].strip(), lines[k + 1].rstrip("\r")
        if code == "0":
            ent = val.strip()
        elif code in ("1", "3") and ent in ("TEXT", "MTEXT", "ATTRIB", "ATTDEF"):
            s = re.sub(r"\\[A-Za-z][^;\\]*;|\\P|\^J|\^I|[{}]", " ", val)
            s = re.sub(r"\s+", " ", s).strip()
            if s:
                out.append(s.upper())
    return out


def parse_equipment():
    pages = pdf_pages(ROOT / "extended/CJOB/docs/List of Main Equipment Rev0.pdf")
    items, grp = {}, None
    for pno, page in enumerate(pages, 1):
        for line in page.split("\n"):
            g = re.match(r"^\s{20,}(\d)\.\s+(.+?)\s*$", line)
            if g:
                grp = (int(g[1]), g[2].strip())
                continue
            m = re.match(r"^\s*(\d{1,3})\.\s+(\S.*?)\s{2,}(\d+(?: set)?)\s*(?:\s{2,}(.*))?$", line)
            if m:
                items[int(m[1])] = dict(no=int(m[1]), name=m[2].strip(), qty=m[3], note=(m[4] or "").strip(), group=grp[0], group_name=grp[1], page=pno)
    # item 19 is split over three lines in the PDF
    items[19] = dict(no=19, name="Anchor Winch 2-AV-4.0-KN", qty="2", note="20 m/min, 2 x 12,5m Ø22mm K2 chain/ 210m Ø22mm wire", group=2, group_name="Anchoring, mooring and towing equipment", page=4)
    assert sorted(items) == list(range(1, 128)), "equipment list parse failed"
    return [items[k] for k in sorted(items)]


def parse_spec(items):
    """Map list items to specification lines that name them (section, page, detail)."""
    pages = pdf_pages(ROOT / "extended/CJOB/docs/Specification Rev0.pdf")
    rows, section = [], None
    for pno, page in enumerate(pages, 1):
        for line in page.split("\n"):
            s = line.strip()
            h = re.match(r"^(\d\.\d(?:\.\d)?)\s+(\S.*)$", s)
            if h and not re.search(r"\.{5}", s):
                section = f"{h[1]} {h[2]}"
            elif re.match(r"^[A-Z][A-Z ,]{6,}$", s) and "SPECIFICATION" not in s:
                section = s[0] + s[1:].lower()
            if s:
                rows.append((pno, section, s, len(line) - len(line.lstrip())))
    norm = lambda s: re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()
    out = {}
    for it in items:
        key = norm(re.sub(r"\(.*?\)", "", it["name"]))
        key = {"azipod 500 kw": "azipods", "main engine": "diesel engines", "cran ctd": "ctd crane", "side monted a frame 4 t swl hydraulic": "side monted a frame",
               "stern mounted a frame 6 t hydraulic": "stern mounted a frame", "anchor winch 2 av 4 0 kn": "anchor winch", "life rafts": "life rafts",
               "anchors hpp ac 14 495 kg": "bow anchors", "bow tunnel thruster 200 kw": "bow thruster", "generator": "generators", "rescue boat davit": "rescue boat davit",
               "hydraulic diving platform 500 kg 1 5m x 0 8m": "hydraulic diving platform", "capstan 8t 220bar d 410 d 320 l 300": "capstan",
               "trawl winches 6t": "trawl winches", "port side pm azimuth drive": "azipods", "sb side pm azimuth drive": "azipods",
               "windlass": "winch with 2 drums"}.get(key, key)
        if len(key) < 3:
            continue
        for k0, (pno, sec, s, ind) in enumerate(rows):
            ns = norm(s)
            if pno < 5 or not sec or sec.startswith(("2.3", "2.4", "2.7", "2.8", "2.9", "2.12")):
                continue
            if ns.startswith(key) or (len(key) > 5 and key in ns):
                detail = re.split(r"\s{3,}", s, maxsplit=1)
                text = s if len(detail) == 1 else f"{detail[0]}: {detail[1]}"
                if len(detail) == 1 and len(s) > 45:  # prose: complete the sentence
                    k = k0
                    while s[0].islower() and k > 0 and rows[k - 1][1] == sec and not rows[k - 1][2].endswith("."):
                        k -= 1
                        text = rows[k][2] + " " + text
                        if rows[k][2][0].isupper():
                            break
                    k = k0
                    while not text.endswith(".") and k + 1 < len(rows) and rows[k + 1][1] == sec:
                        k += 1
                        text += " " + rows[k][2]
                elif len(detail) == 2:  # table row: add wrapped continuation lines of the value column
                    k = k0
                    while k + 1 < len(rows) and rows[k + 1][3] > 40 and rows[k + 1][0] == pno:
                        k += 1
                        text += " " + rows[k][2]
                out.setdefault(it["no"], dict(section=sec, page=pno, text=re.sub(r"\s+", " ", text)))
                break
    return out


def parse_weights():
    z = zipfile.ZipFile(ROOT / "extended/CJOB/docs/Weight Calculation Rev0.xlsx")
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    shared = [("".join(t.text or "" for t in si.iter(f"{{{ns['m']}}}t"))) for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", ns)]
    sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    rows = []
    for r in sheet.iter(f"{{{ns['m']}}}row"):
        vals = {}
        for c in r.findall("m:c", ns):
            col = re.match(r"[A-Z]+", c.get("r"))[0]
            v = c.find("m:v", ns)
            if v is None:
                continue
            vals[col] = shared[int(v.text)] if c.get("t") == "s" else v.text
        rows.append(vals)
    out, total = [], None
    for v in rows:
        if v.get("B") == "LIGHT SHIP WEIGHT" or v.get("A") == "LIGHT SHIP WEIGHT":
            total = v
        if v.get("A", "").strip().isdigit() and "B" in v:
            num = lambda k: float(v[k]) if k in v and re.match(r"^-?[\d.eE+-]+$", str(v[k])) else None
            out.append(dict(code=v["A"].strip(), name=v["B"].strip().capitalize(), t=round(num("C"), 2), lcg=num("G"), tcg=num("H"), vcg=num("I"),
                            ref_error=any(str(x).startswith("#REF") for x in v.values())))
    return out


def reduce_series(t, y, step=10):
    """10-s means on the case grid; None where no data."""
    s = pd.Series(y.values, index=t).resample(f"{step}s").mean()
    return s


def operational(parts_idx):
    v = pd.read_csv(CASE / "data/vessel_1hz.csv.gz", parse_dates=["time_utc"])
    ch = pd.read_csv(CASE / "channels.csv")
    cases = pd.read_csv(CASE / "cases.csv")
    t = v["time_utc"]
    t0 = t.iloc[0].floor("10s")
    grid = pd.date_range(t0, t.iloc[-1], freq="10s")
    channels = {}
    for _, row in ch[ch.file == "vessel_1hz.csv.gz"].iterrows():
        col = row["column"]
        if col not in v:
            continue
        parts, items = [], []
        for pat, p, it in CHANNEL_PARTS:
            if re.match(pat, col):
                parts, items = p, it
                break
        y = pd.to_numeric(v[col], errors="coerce")
        n = int(y.notna().sum())
        cover = n / len(y)
        rec = dict(file=row["file"], col=col, unit=row["unit"], desc=row["description"], source=row["source"], rate=row["rate"],
                   parts=parts, items=items, n=n, cover=round(cover, 3))
        if n:
            rec.update(mean=float(y.mean()), std=float(y.std()), min=float(y.min()), max=float(y.max()))
            rec["constant"] = bool(y.min() == y.max())
        if cover >= 0.2 and not rec.get("constant"):
            s = pd.Series(y.values, index=t).resample("10s").mean().reindex(grid)
            rec["spark"] = [None if np.isnan(x) else float(f"{x:.4g}") for x in s.values]
        channels[col] = rec
    # crane-hook IMU: RMS of the acceleration without gravity, per 10 s
    imu = pd.read_csv(CASE / "data/crane_tip_imu.csv.gz", usecols=["time_utc", "user_acc_x_g", "user_acc_y_g", "user_acc_z_g"], parse_dates=["time_utc"])
    a = np.sqrt(imu.user_acc_x_g ** 2 + imu.user_acc_y_g ** 2 + imu.user_acc_z_g ** 2) * 9.80665
    rms = np.sqrt((pd.Series(a.values ** 2, index=imu.time_utc)).resample("10s").mean()).reindex(grid)
    channels["hook_acc_rms"] = dict(file="crane_tip_imu.csv.gz", col="user_acc_x_g, user_acc_y_g, user_acc_z_g", unit="m/s2",
        desc="Crane-hook acceleration without gravity, RMS of the magnitude over 10 s (derived here from the iPhone IMU on the hook)",
        source="iPhone IMU (SensorLog) on the crane hook", rate="~16.7 Hz, reduced to 10 s", parts=["part03"], items=[77, 85],
        n=int(len(imu)), cover=1.0, mean=float(np.nanmean(rms)), std=float(np.nanstd(rms)), min=float(np.nanmin(rms)), max=float(np.nanmax(rms)),
        spark=[None if np.isnan(x) else float(f"{x:.4g}") for x in rms.values], derived=True)
    case_list = []
    for _, c in cases.iterrows():
        s = (pd.Timestamp(c.start_utc) - t0).total_seconds()
        e = (pd.Timestamp(c.end_utc) - t0).total_seconds()
        case_list.append(dict(case=int(c.case), start=s, end=e, heading=float(c.mean_heading_deg), wave1=int(c.angle_to_wave1_deg), wave2=int(c.angle_to_wave2_deg)))
    return dict(id="wave-shielding-2023", title="Wave-shielding experiment, 31 Oct 2023",
                study="Wang et al. (2025), Ocean Engineering 320, 120189", doi="10.1016/j.oceaneng.2024.120189",
                t0=t0.strftime("%Y-%m-%dT%H:%M:%SZ"), dt=10, n=len(grid), cases=case_list, channels=channels,
                other_sensors=[
                    dict(name="LainePoiss wave buoy", where="In the water on the sheltered (starboard) side, not on the ship", file="wave_buoy_50hz.csv.gz"),
                    dict(name="Miros WaveX and RangeFinder", where="Position on the ship not documented in this repository", file="wave_radar_params.csv"),
                ])


def main():
    parts = json.loads((ROOT / "derived/3d/gunnerus-parts.json").read_text())
    meta = json.loads((ROOT / "metadata/gunnerus_metadata.json").read_text())
    items = parse_equipment()
    spec = parse_spec(items)
    weights = parse_weights()

    # parts <-> items
    def item_numbers(s):
        out = []
        for tok in re.split(r"[,/]", s or ""):
            tok = tok.strip()
            r = re.match(r"^(\d+)\s*[–-]\s*(\d+)$", tok)
            if r:
                out += list(range(int(r[1]), int(r[2]) + 1))
            elif tok.isdigit():
                out.append(int(tok))
        return out
    for p in parts:
        p["items"] = PART_ITEMS.get(p["node"], item_numbers(p.get("item")))
        p["tentative"] = "tentative" in (p.get("label") or "")
        p["label"] = (p.get("label") or "").replace(" (identification tentative)", "") or None
    item_parts = {}
    for p in parts:
        for n in p["items"]:
            item_parts.setdefault(n, []).append(p["node"])

    # drawings text
    dtexts = {}
    for slug, title, d, f, src in DRAWINGS:
        dtexts[slug] = dxf_texts(ROOT / d / f"{f}.dxf")
        print(f"{len(dtexts[slug]):5d} text strings  {f}", file=sys.stderr)
    item_draw = {}
    for no, pat in KEYWORDS.items():
        rx = re.compile(pat)
        for slug, ts in dtexts.items():
            if slug in SKIP_TEXT_SEARCH:
                continue
            hits = sorted({s for s in ts if rx.search(s) and len(s) < 90})
            if hits:
                item_draw.setdefault(no, []).append(dict(slug=slug, hits=hits[:4], n=sum(1 for s in ts if rx.search(s))))

    # GA metadata
    meta_eq = []
    for i, e in enumerate(meta["equipment_inventory"]):
        link = META_LINKS.get(i, {"parts": [], "items": []})
        meta_eq.append(dict(i=i, item=e["item"], location=e.get("location"), sfi=e.get("sfi_subgroup"), sfi_desc=e.get("sfi_desc"),
                            vis=e.get("vis_gmod_ref"), notes=e.get("notes"), capacity=e.get("capacity"), confidence=e.get("confidence"),
                            source=e.get("source"), supplier=e.get("supplier"), parts=link["parts"], items=link["items"], link_note=link.get("note")))
    item_meta = {}
    for m in meta_eq:
        for n in m["items"]:
            item_meta.setdefault(n, []).append(m["i"])

    op = operational(parts)
    item_ch = {}
    for k, c in op["channels"].items():
        for n in c["items"]:
            item_ch.setdefault(n, []).append(k)

    item_issue = {}
    for iss in ISSUES:
        for n in iss.get("items", []):
            item_issue.setdefault(n, []).append(iss["id"])

    for it in items:
        n = it["no"]
        it.update(parts=item_parts.get(n, []), drawings=item_draw.get(n, []), spec=spec.get(n), meta=item_meta.get(n, []),
                  channels=item_ch.get(n, []), issues=item_issue.get(n, []))

    groups = {}
    for p in parts:
        g = groups.setdefault(p["group_key"], dict(key=p["group_key"], sfi=p["sfi"], name=p["group"], nodes=[]))
        g["nodes"].append(p["node"])
    for k, g in groups.items():
        g["drawings"] = GROUP_DRAWINGS.get(k, [])
    for w in weights:
        w["groups3d"] = WEIGHT_TO_3D.get(w["code"], [])

    data = dict(
        generated_by="pages/tools/build_explorer_data.py",
        drawings=[dict(slug=s, title=t, dir=d, file=f, src=src) for s, t, d, f, src in DRAWINGS],
        documents=dict(equipment="extended/CJOB/docs/List of Main Equipment Rev0.pdf", spec="extended/CJOB/docs/Specification Rev0.pdf",
                       weight="extended/CJOB/docs/Weight Calculation Rev0.xlsx", metadata="metadata/gunnerus_metadata.json"),
        groups=list(groups.values()), parts=parts, items=items, meta=meta_eq, weights=weights, issues=ISSUES,
        key_channels=KEY_CHANNELS, operational=op,
        dimensions={k: v for k, v in meta["main_dimensions"].items() if not k.startswith(("_", "sfi", "vis"))},
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size/1e3:.0f} kB)", file=sys.stderr)
    # summary
    cnt = lambda k: sum(1 for i in items if i[k])
    print(f"items 127 | 3D {cnt('parts')} | drawings {cnt('drawings')} | spec {cnt('spec')} | GA meta {cnt('meta')} | sensors {cnt('channels')}", file=sys.stderr)


if __name__ == "__main__":
    main()
