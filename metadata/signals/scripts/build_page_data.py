#!/usr/bin/env python3
"""Build pages/assets/signals/signals.json for the signals page (pages/signals.html).

    python3 metadata/signals/scripts/build_page_data.py

Reads: gunnerus-signal-crosswalk.csv, translator-test/*, data/*.csv.gz and the power and energy case
(operational/power-energy-2023/data/power_1min.csv.gz). Needs pandas and numpy.
"""
import csv, json, os, re, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SIG = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(SIG))
OUT = os.path.join(ROOT, "pages", "assets", "signals", "signals.json")

GROUPS = {"E": "Engine 1 (Nogva, Modbus)", "P": "Power management (Siemens PMS)", "T": "Thrusters and drives", "N": "Navigation and environment", "C": "Crane (Palfinger)"}

# which data file and column carries which signal (secondary entries are other years of the same signal)
DATA = {
    "E01": [("engine2019", "ME1_EngineSpeed"), ("power2023", "engine1_speed_rpm")],
    "E02": [("engine2019", "ME1_POWER"), ("power2023", "engine1_load_kw")],
    "E03": [("engine2019", "ME1_FuelRate"), ("power2023", "engine1_fuel_lph")],
    "E04": [("engine2019", "ME1_LOPress")], "E05": [("engine2019", "ME1_LubOilTemp")], "E06": [("engine2019", "ME1_coolantTemp")],
    "E07": [("engine2019", "ME1_Boostpress")], "E08": [("engine2019", "ME1_ExhaustTemp1")], "E09": [("engine2019", "ME1_ExhaustTemp2")],
    "E10": [("engine2019", "ME1_StartBatt")], "E11": [("engine2019", "ME1_BackupBatt")], "E12": [("engine2019", "ME1_Hours")],
    "E13": [("engine2019", "m2InsideTemp")],
    "T01": [("docking2019", "port_thr_angle_fb")], "T02": [("docking2019", "port_thr_angle_order")],
    "T03": [("docking2019", "port_thr_rpm_fb"), ("power2023", "azi_port_rpmfeedback")], "T04": [("docking2019", "port_thr_rpm_order")],
    "T05": [("power2023", "azi_port_load_feedback")],
    "T11": [("docking2019", "tunnel_thr_force_percent_fb"), ("power2023", "tunnel_thruster_feedback_pct")],
    "N01": [("docking2019", "latitude"), ("power2023", "latitude_deg")], "N02": [("docking2019", "longitude"), ("power2023", "longitude_deg")],
    "N03": [("power2023", "sog_kn")], "N04": [("docking2019", "surge_speed")], "N06": [("docking2019", "heading")],
    "N07": [("docking2019", "roll")], "N08": [("docking2019", "pitch")], "N09": [("docking2019", "heave")],
}
EXTRA = {"engine2019": ["ME2_LOPress", "ME2_coolantTemp", "ME2_LubOilTemp", "ME2_StartBatt", "ME1_StartBatt"]}  # for the documents-against-data panel

DATASETS = {
    "engine2019": dict(file="data/engine_2019_1min.csv.gz", label="Nogva engine log, 21 Nov 2019, 08:30–14:10 (as logged, time zone not stated)", step_s=60, out_step=1, how="1-minute means of the 1 Hz log"),
    "docking2019": dict(file="data/docking_2019_10s.csv.gz", label="Ship docking log, 9 Nov 2019, 08:20–10:30 (as logged, time zone not stated)", step_s=10, out_step=1, how="10-second means of the 1 Hz log"),
    "power2023": dict(file=os.path.join(ROOT, "operational/power-energy-2023/data/power_1min.csv.gz"), label="Cruise week, 30 Oct – 3 Nov 2023 (UTC)", step_s=600, out_step=10, how="10-minute means of the 1-minute series of the power and energy case"),
}


sys.path.insert(0, os.path.join(SIG, "translator-test"))
import grade as G  # per-item checks use the same rules as grade.py


def check(sid, a):
    """kind/unit/sfi checks of one answer against our crosswalk (None = not graded for this item)."""
    t = G.cw[sid]
    k = (a['quantity_kind'] + ' ' + a.get('component', '')).lower()
    kind = any(w in k for w in G.KIND.get(t['quantity_kind'], [t['quantity_kind'].lower()]))
    tu = G.truth_unit(sid)
    unit = None if (sid in G.SHOULD or sid in G.FORMAT or not tu) else (G.nu(a['canonical_unit']) == tu)
    sf = t['sfi_code']; s = str(a.get('sfi_code', '')).replace(' ', '')
    sfi = (s[:3] == sf[:3]) if (sf and len(sf) >= 3 and sid not in G.SHOULD and sid not in G.FORMAT) else None
    fl = bool(a.get('needs_human'))
    if sid in G.SHOULD:
        trap = fl
    elif sid in G.FORMAT:
        trap = fl or 'ddmm' in a['canonical_unit'].lower() or 'min' in a['canonical_unit'].lower()
    else:
        trap = None
    return dict(kind=kind, unit=unit, sfi=sfi, trap=trap)


RAW = "The dump gives a raw integer and no unit or scaling."
TRAP_WHY = {
    "E07": "Two versions of the vendor list give different scaling: x10 and x100.",
    "P01": RAW, "P02": RAW + " Sign convention also unstated.", "P03": RAW, "P04": RAW, "P05": RAW,
    "P06": RAW + " Scaling and sign convention unstated.", "P07": RAW, "P08": RAW,
    "P09": RAW + " Unclear whether it totals all generators or one switchboard section.",
    "T03": "The documentation says both percent (limits 203 and -203) and plus or minus 203 rpm.",
    "T05": "The documentation gives percent and kW (0-500) at once; not decidable from the documents.",
    "T10": "The vendor states no unit or scaling.",
    "N01": "Logged as degrees and decimal minutes (ddmm.mmmm), not decimal degrees. Averaging across a degree boundary gives false positions.",
    "N02": "Logged as degrees and decimal minutes (dddmm.mmmm), not decimal degrees.",
}


def sig(x, n=4):
    return None if x is None or pd.isna(x) else float(f"{x:.{n}g}")


def main():
    cw = list(csv.DictReader(open(os.path.join(SIG, "gunnerus-signal-crosswalk.csv"), encoding="utf-8")))
    key = json.load(open(os.path.join(SIG, "translator-test", "key.json")))  # X id -> signal id
    inv = {v: k for k, v in key.items()}
    A = {a["item"]: a for a in json.load(open(os.path.join(SIG, "translator-test", "armA_answers.json")))}
    B = {a["item"]: a for a in json.load(open(os.path.join(SIG, "translator-test", "armB_answers.json")))}

    frames, stats, ds_out = {}, {}, {}
    for name, d in DATASETS.items():
        df = pd.read_csv(os.path.join(SIG, d["file"]) if not os.path.isabs(d["file"]) else d["file"])
        tcol = df.columns[0]
        t = pd.to_datetime(df[tcol].str.replace("Z", "", regex=False))
        df = df.drop(columns=[tcol]).apply(pd.to_numeric, errors="coerce")
        df.index = t
        frames[name] = df
        ds_out[name] = dict(label=d["label"], how=d["how"], start=t.iloc[0].strftime("%Y-%m-%dT%H:%M:%S"), step_s=d["step_s"], n_full=len(df), series={})
    need = {}
    for sid, lst in DATA.items():
        for ds, col in lst:
            need.setdefault(ds, set()).add(col)
    for ds, cols in EXTRA.items():
        need.setdefault(ds, set()).update(cols)
    for ds, cols in need.items():
        df = frames[ds]; k = DATASETS[ds]["out_step"]
        for col in sorted(cols):
            s = df[col]
            nd = 9 if "itude" in col else 4
            stats[(ds, col)] = dict(min=sig(s.min(), nd), max=sig(s.max(), nd), mean=sig(s.mean(), nd), n=int(s.notna().sum()))
            m = s.groupby(np.arange(len(s)) // k).mean() if k > 1 else s
            ds_out[ds]["series"][col] = [sig(v, 9 if "itude" in col else 4) for v in m.tolist()]

    signals = []
    for r in cw:
        sid = r["id"]; x = inv[sid]
        rec = dict(id=sid, group=sid[0], concept=r["concept"], system=r["system"], sfi_code=r["sfi_code"], sfi_name=r["sfi_name"], vis_level1=r["vis_gmod_level1"],
                   quantity_kind=r["quantity_kind"], unit=r["canonical_unit"], native=dict(nogva=r["native_nogva_modbus"], hemos=r["native_hemos"], nuc=r["native_nuc_2023"], asset2019=r["native_asset_model_2019"], other=r["native_other_source"]),
                   documented=r["documented_unit_or_scaling"], logged_2023=(r["in_nuc_cruise_week"] == "yes"), derived=(r["in_nuc_cruise_week"] == "derived"),
                   mean_interval_s=(float(r["mean_interval_s"]) if re.match(r"^[\d.]+$", r["mean_interval_s"] or "") else None),
                   logged_range_5d=r["logged_range_5d"], note=r["note"])
        for k in rec["native"]:
            if rec["native"][k].startswith("(not logged)"):
                rec["native"][k] = ""
        if sid == "N12":  # third-party wave sensor: keep the row, not the vendor source details
            rec["native"]["other"] = ""
            rec["note"] = "Third-party sensor; details not published here."
        m = re.search(r"normal ([\d.]+)-([\d.]+)", r["documented_unit_or_scaling"])
        if m:
            rec["normal_band"] = [float(m.group(1)), float(m.group(2))]
        rec["trap"] = "should_flag" if sid in G.SHOULD else ("format" if sid in G.FORMAT else "")
        rec["trap_why"] = TRAP_WHY.get(sid, "")
        rec["data"] = [dict(dataset=ds, col=col, **stats[(ds, col)]) for ds, col in DATA.get(sid, [])]
        rec["translator"] = {arm: dict(kind=a[x]["quantity_kind"], unit=a[x]["canonical_unit"], sfi=str(a[x]["sfi_code"]), flag=bool(a[x]["needs_human"]), ok=check(sid, a[x]), confidence=a[x].get("confidence"), question=a[x].get("question", "")) for arm, a in (("A", A), ("B", B))}
        signals.append(rec)

    vendors = [dict(name="Siemens PMS (PROFIBUS DP)", listed=686, logged=0), dict(name="Rolls-Royce HEMOS (MQTT)", listed=308, logged=64),
               dict(name="Nogva engines (Modbus TCP)", listed=37, logged=27), dict(name="Palfinger crane (Modbus TCP)", listed=6, logged=5)]
    out = dict(signals=signals, datasets=ds_out, groups=GROUPS, vendors=vendors, logger_tags=81,
               extra_stats={f"{ds}:{col}": stats[(ds, col)] for ds, cols in EXTRA.items() for col in cols})
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
    print("wrote", os.path.relpath(OUT, ROOT), os.path.getsize(OUT) // 1024, "kB;", len(signals), "signals")


if __name__ == "__main__":
    main()
