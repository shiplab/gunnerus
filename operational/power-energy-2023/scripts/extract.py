#!/usr/bin/env python3
"""Rebuild operational/power-energy-2023 from the raw October 2023 cruise data.

    python3 operational/power-energy-2023/scripts/extract.py "<...>/Tokt uke 44 2023" [minute periods summary profile channels web figure]

With no step names every step runs, in that order. Needs pandas and numpy (matplotlib for `figure`).

Source: the five daily NUC logger exports (vessel data from nuc PC/second_try/Gunnerus-w44/copy1..copy5,
30 Oct - 3 Nov 2023), long format (time, tag, value). Only the power-chain tags are read.

Everything that is a choice of ours (mode thresholds, fuel density, CO2 factor) is a constant below
and is reported as such in the README and on the website.
"""
import json, os, re, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CASE = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(CASE))
DATA = os.path.join(CASE, "data")
WEB = os.path.join(ROOT, "pages", "assets", "operational", "power-energy-2023.json")

T0 = pd.Timestamp("2023-10-30 00:00:00", tz="UTC")
T1 = pd.Timestamp("2023-11-04 00:00:00", tz="UTC")   # exclusive

# ---- our choices (assumed, not measured) -------------------------------------------------------
V_STILL = 0.5      # kn  : below this, speed over ground is GPS noise (5,945 of 7,195 minutes are below 0.3 kn)
V_TRANSIT = 8.0    # kn  : edge of the cruise cluster (8-12 kn); 0.5-8 kn is acceleration/deceleration
AZI_ON = 5.0       # rpm : azimuth drive counted as running above this (idle < 0.5, running > 8: nothing between)
ENG_ON = 5.0       # kW  : engine counted as running above this (off < 1 kW, running > 20 kW)
FUEL_DENSITY = 0.85       # kg/L, marine gas oil, assumed (range 0.82-0.86)
CO2_FACTOR = 3.206        # t CO2 per t fuel, marine gas oil / diesel, tank-to-wake CO2 only, assumed
ENG_RATED_KW = 450.0      # kW  : rated power per engine, list of main equipment / specification (475 kW on the engine room arrangement), assumed
SPEED_BANDS = [(-1.0, 0.5, "under 0.5 kn"), (0.5, 3.0, "0.5 to 3 kn"), (3.0, 6.0, "3 to 6 kn"), (6.0, 8.0, "6 to 8 kn"), (8.0, 10.0, "8 to 10 kn"), (10.0, 99.0, "10 kn and above")]   # assumed bands
MODES = ["stationary", "station_keeping", "manoeuvring", "transit"]

TAGS = {
    "SeapathGPSVtg/SpeedKnots": "sog_kn",
    "SeapathGPSGga/Latitude": "latitude_deg",     # logged as NMEA ddmm.mmmm, converted to decimal degrees per sample in minute()
    "SeapathGPSGga/Longitude": "longitude_deg",   # logged as NMEA dddmm.mmmm, converted to decimal degrees per sample in minute()
    "hcx_port_mp/RPMFeedback": "azi_port_rpmfeedback",
    "hcx_port_mp/LoadFeedback": "azi_port_load_feedback",
    "hcx_stbd_mp/RPMFeedback": "azi_stbd_rpmfeedback",
    "hcx_stbd_mp/LoadFeedback": "azi_stbd_load_feedback",
    "dpThruster/FeedbackProsent": "tunnel_thruster_feedback_pct",
}
for n in (1, 2, 3):
    TAGS[f"Engine{n}/engine_load"] = f"engine{n}_load_kw"
    TAGS[f"Engine{n}/fuel_consumption"] = f"engine{n}_fuel_lph"
    TAGS[f"Engine{n}/engine_speed"] = f"engine{n}_speed_rpm"
POS_TAGS = ["SeapathGPSGga/Latitude", "SeapathGPSGga/Longitude"]
RAW_TAG = {v: "Gunnerus/" + k for k, v in TAGS.items()}
MEASURED = list(TAGS.values())


def iso(s):
    return s.dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def save(df, name, gz=True):
    os.makedirs(DATA, exist_ok=True)
    p = os.path.join(DATA, name + (".csv.gz" if gz else ".csv"))
    df = df.copy()
    for c in ("latitude_deg", "longitude_deg"):   # %.4g would cut 62.4747 to 62.47: write 5 decimals as text
        if c in df:
            df[c] = df[c].map(lambda x: "" if pd.isna(x) else f"{x:.5f}")
    df.to_csv(p, index=False, date_format="%Y-%m-%dT%H:%M:%SZ", float_format="%.4g")
    print("wrote", os.path.relpath(p, ROOT), len(df), "rows")


# ------------------------------------------------------------------ 1-minute means
def raw_folder(src):
    return os.path.join(src, "vessel data from nuc PC", "second_try", "Gunnerus-w44")


def minute(src):
    parts = []
    for k in range(1, 6):
        f = os.path.join(raw_folder(src), f"copy{k}")
        for ch in pd.read_csv(f, header=None, names=["t", "tag", "v"], chunksize=2_000_000, dtype=str):
            ch = ch[ch.tag.str.startswith("Gunnerus/")].copy()
            ch["tag"] = ch.tag.str.slice(9)
            ch = ch[ch.tag.isin(TAGS)].copy()
            ch["m"] = ch.t.str.slice(0, 16)
            ch["v"] = pd.to_numeric(ch.v, errors="coerce")
            pos = ch.tag.isin(POS_TAGS)   # NMEA ddmm.mmmm -> decimal degrees per sample, BEFORE averaging (a mean taken across 5 deg 59.9 min -> 6 deg 00.1 min would be wrong)
            deg = np.floor(ch.v[pos] / 100)
            ch.loc[pos, "v"] = deg + (ch.v[pos] - 100 * deg) / 60
            parts.append(ch.groupby(["m", "tag"]).v.agg(["sum", "count"]))
        print("read", f, file=sys.stderr)
    g = pd.concat(parts).groupby(level=[0, 1]).sum()
    g["mean"] = g["sum"] / g["count"]
    d = g["mean"].unstack("tag").rename(columns=TAGS)
    d.index = pd.to_datetime(d.index, utc=True, format="%Y-%m-%d %H:%M")
    d = d.reindex(pd.date_range(T0, T1, freq="1min", inclusive="left", name="time_utc"))
    d = d[(d.index >= T0) & (d.index < T1)]
    d.columns.name = None
    d = d.reset_index()
    d = derive(d)
    cols = ["time_utc", "mode"] + [c for c in MEASURED if c in d] + ["engines_running", "load_total_kw", "fuel_total_lph"]
    d = d[cols]
    save(d, "power_1min")
    cov = {c: round(float(d[c].notna().mean()), 4) for c in MEASURED if c in d}
    print("coverage (share of minutes with data):", cov, file=sys.stderr)
    return d


def derive(d):
    load = d[[f"engine{n}_load_kw" for n in (1, 2, 3)]]
    d["engines_running"] = (load > ENG_ON).sum(axis=1).where(load.notna().any(axis=1))
    d["load_total_kw"] = load.sum(axis=1, min_count=1)
    d["fuel_total_lph"] = d[[f"engine{n}_fuel_lph" for n in (1, 2, 3)]].sum(axis=1, min_count=1)
    azi = d[["azi_port_rpmfeedback", "azi_stbd_rpmfeedback"]].max(axis=1)
    mode = np.where(d.sog_kn >= V_TRANSIT, "transit",
           np.where(d.sog_kn >= V_STILL, "manoeuvring",
           np.where(azi > AZI_ON, "station_keeping", "stationary")))
    d["mode"] = pd.Series(mode, index=d.index).where(d.sog_kn.notna() & azi.notna(), "")
    return d


def load_minute():
    d = pd.read_csv(os.path.join(DATA, "power_1min.csv.gz"), parse_dates=["time_utc"])
    d["mode"] = d["mode"].fillna("")
    return d


# ------------------------------------------------------------------ periods (cases.csv)
def periods(d=None):
    d = load_minute() if d is None else d
    run = (d["mode"] != d["mode"].shift()).cumsum()
    rows = []
    for _, x in d.groupby(run):
        m = x["mode"].iloc[0]
        if not m:
            continue
        rows.append(dict(
            start_utc=x.time_utc.iloc[0], end_utc=x.time_utc.iloc[-1] + pd.Timedelta(minutes=1),
            duration_min=len(x), mode=m, mean_sog_kn=x.sog_kn.mean(), mean_load_total_kw=x.load_total_kw.mean(),
            mean_engines_running=x.engines_running.mean(), fuel_l=x.fuel_total_lph.sum() / 60))
    p = pd.DataFrame(rows)
    p.insert(0, "period", range(1, len(p) + 1))
    for c in ("start_utc", "end_utc"):
        p[c] = iso(p[c])
    for c in ("mean_sog_kn", "mean_load_total_kw", "mean_engines_running", "fuel_l"):
        p[c] = p[c].round(2)
    p.to_csv(os.path.join(CASE, "cases.csv"), index=False)
    print("wrote cases.csv", len(p), "periods")
    return p


# ------------------------------------------------------------------ summary (derived)
def summarise(x):
    h = len(x) / 60
    kwh = x.load_total_kw.sum() / 60
    fuel = x.fuel_total_lph.sum() / 60
    return dict(hours=round(h, 2), mean_load_total_kw=round(x.load_total_kw.mean(), 1), mean_engines_running=round(x.engines_running.mean(), 2),
                energy_kwh=round(kwh, 0), fuel_l=round(fuel, 0),
                fuel_l_per_kwh=round(fuel / kwh, 4) if kwh else np.nan,
                co2_t_assumed=round(fuel * FUEL_DENSITY * CO2_FACTOR / 1000, 2))


def summary(d=None):
    d = load_minute() if d is None else d
    d = d[d["mode"] != ""].copy()
    d["day"] = d.time_utc.dt.strftime("%Y-%m-%d")
    rows = []
    for scope, key in (("week", None), ("day", "day")):
        groups = [("all", d)] if key is None else list(d.groupby("day"))
        for label, x in groups:
            for mode in ["all"] + MODES:
                y = x if mode == "all" else x[x["mode"] == mode]
                if len(y):
                    rows.append(dict(scope=scope, period=label, mode=mode, **summarise(y)))
    s = pd.DataFrame(rows)
    all_fuel = s[s["mode"] == "all"].set_index(["scope", "period"]).fuel_l
    tot = all_fuel[("week", "all")]
    s["fuel_share_pct"] = [round(100 * r.fuel_l / all_fuel[(r.scope, r.period)], 1) for r in s.itertuples()]
    s.to_csv(os.path.join(CASE, "summary.csv"), index=False)
    print("wrote summary.csv", len(s), "rows; week fuel", tot, "L")
    return s


# ------------------------------------------------------------------ profile.csv (shares of time, energy, fuel)
def _measures(x, tot):
    """hours, energy and fuel of the minutes in x, and their share of the totals in tot (all derived)."""
    h = len(x) / 60
    kwh = x.load_total_kw.sum() / 60
    fuel = x.fuel_total_lph.sum() / 60
    return dict(hours=round(h, 2), share_time_pct=round(100 * len(x) / len(tot), 2),
                energy_kwh=round(kwh, 0), share_energy_pct=round(100 * kwh / (tot.load_total_kw.sum() / 60), 2),
                fuel_l=round(fuel, 0), share_fuel_pct=round(100 * fuel / (tot.fuel_total_lph.sum() / 60), 2))


def profile(d=None):
    """Operating profile in shares: by mode, speed band, number of engines running, engine combination, and per engine.

    kind = mode | speed_band | engines_running | engine_combination   -> shares of time, energy and fuel of the period
    kind = engine                                                      -> per engine: hours running, energy and its share of the total engine energy,
                                                                          mean load while running (kW and % of the assumed rated power)
    kind = engine_by_mode                                              -> the same, within one operating mode (group = mode)
    """
    d = load_minute() if d is None else d
    d = d[d["mode"] != ""].copy()
    d["day"] = d.time_utc.dt.strftime("%Y-%m-%d")
    on = {n: d[f"engine{n}_load_kw"] > ENG_ON for n in (1, 2, 3)}
    d["combo"] = ["+".join(f"E{n}" for n in (1, 2, 3) if on[n].iloc[i]) or "none" for i in range(len(d))]
    d["band"] = pd.cut(d.sog_kn, [b[0] for b in SPEED_BANDS] + [SPEED_BANDS[-1][1]], labels=[b[2] for b in SPEED_BANDS], right=False)
    rows = []

    def engine_rows(x, kind, group, scope, label):
        tot_kwh = x.load_total_kw.sum() / 60
        for n in (1, 2, 3):
            ld = x[f"engine{n}_load_kw"]
            run = ld > ENG_ON
            kwh = ld.sum() / 60
            mean_run = ld[run].mean() if run.any() else np.nan
            rows.append(dict(scope=scope, period=label, kind=kind, group=group, category=f"engine{n}",
                             hours=round(run.sum() / 60, 2), share_time_pct=round(100 * run.sum() / len(x), 2) if len(x) else np.nan,
                             energy_kwh=round(kwh, 0), share_energy_pct=round(100 * kwh / tot_kwh, 2) if tot_kwh else np.nan,
                             fuel_l=round(x[f"engine{n}_fuel_lph"].sum() / 60, 0), share_fuel_pct=np.nan,
                             mean_load_running_kw=round(mean_run, 1) if run.any() else np.nan,
                             load_factor_running_pct_assumed=round(100 * mean_run / ENG_RATED_KW, 1) if run.any() else np.nan))

    for scope, key in (("week", None), ("day", "day")):
        groups = [("all", d)] if key is None else list(d.groupby("day"))
        for label, x in groups:
            for m in MODES:
                y = x[x["mode"] == m]
                if len(y):
                    rows.append(dict(scope=scope, period=label, kind="mode", group="", category=m, **_measures(y, x)))
                    engine_rows(y, "engine_by_mode", m, scope, label)
            for b in [b[2] for b in SPEED_BANDS]:
                y = x[x["band"] == b]
                rows.append(dict(scope=scope, period=label, kind="speed_band", group="", category=b, **_measures(y, x)))
            for k in range(0, 4):
                y = x[x.engines_running == k]
                if len(y):
                    rows.append(dict(scope=scope, period=label, kind="engines_running", group="", category=str(k), **_measures(y, x)))
            for c in sorted(x.combo.unique(), key=lambda c: (-len(x[x.combo == c]))):
                y = x[x.combo == c]
                rows.append(dict(scope=scope, period=label, kind="engine_combination", group="", category=c, **_measures(y, x)))
            engine_rows(x, "engine", "", scope, label)
    p = pd.DataFrame(rows)
    p.to_csv(os.path.join(CASE, "profile.csv"), index=False)
    print("wrote profile.csv", len(p), "rows")
    return p


# ------------------------------------------------------------------ channels.csv
CH = [  # column, unit, description, status, raw/derivation
    ("time_utc", "ISO 8601 UTC", "Start of the minute", "-", ""),
    ("mode", "-", "Operating mode of the minute: stationary, station_keeping, manoeuvring, transit (rules in README); empty if speed or azimuth rpm is missing", "derived", f"sog_kn >= {V_TRANSIT} -> transit; >= {V_STILL} -> manoeuvring; else station_keeping if max(azimuth rpm) > {AZI_ON} else stationary"),
    ("sog_kn", "knots", "Speed over ground", "measured", ""),
    ("latitude_deg", "degrees N", "Position latitude (GPS GGA); logged as ddmm.mmmm, converted to decimal degrees; mean of the minute", "measured", ""),
    ("longitude_deg", "degrees E", "Position longitude (GPS GGA); logged as dddmm.mmmm, converted to decimal degrees; mean of the minute", "measured", ""),
    ("azi_port_rpmfeedback", "as logged", "Port azimuth drive, rpm feedback (rpm assumed)", "measured", ""),
    ("azi_port_load_feedback", "as logged", "Port azimuth drive, load feedback", "measured", ""),
    ("azi_stbd_rpmfeedback", "as logged", "Starboard azimuth drive, rpm feedback (rpm assumed)", "measured", ""),
    ("azi_stbd_load_feedback", "as logged", "Starboard azimuth drive, load feedback", "measured", ""),
    ("tunnel_thruster_feedback_pct", "%", "Tunnel thruster feedback (zero all week)", "measured", ""),
]
for n in (1, 2, 3):
    CH += [(f"engine{n}_load_kw", "kW", f"Engine {n} load (kW per NTNU e-infrastructure page)", "measured", ""),
           (f"engine{n}_fuel_lph", "L/h", f"Engine {n} fuel consumption; correlates 1.00 with load, so probably computed from load by the logger, not metered", "measured (logged)", ""),
           (f"engine{n}_speed_rpm", "rpm", f"Engine {n} speed", "measured", "")]
CH += [("engines_running", "count", f"Engines with load above {ENG_ON:g} kW", "derived", "count of engineN_load_kw > threshold"),
       ("load_total_kw", "kW", "Sum of the three engine loads", "derived", "engine1+2+3 load"),
       ("fuel_total_lph", "L/h", "Sum of the three engine fuel consumptions", "derived", "engine1+2+3 fuel")]


def channels():
    rows = []
    for col, unit, desc, status, how in CH:
        base = col
        src = ""
        if col in RAW_TAG:
            src = f"NUC logger, tag {RAW_TAG[col]}"
        elif how:
            src = "derived: " + how
        rows.append(dict(file="power_1min.csv.gz", column=col, unit=unit, description=desc, source=src,
                         rate="1 min (mean of the logged samples in the minute)" if col != "time_utc" else "", status=status))
    pd.DataFrame(rows).to_csv(os.path.join(CASE, "channels.csv"), index=False)
    print("wrote channels.csv", len(rows), "rows")


# ------------------------------------------------------------------ website JSON
def web(d=None, s=None, p=None, pr=None):
    d = load_minute() if d is None else d
    s = pd.read_csv(os.path.join(CASE, "summary.csv")) if s is None else s
    p = pd.read_csv(os.path.join(CASE, "cases.csv")) if p is None else p
    pr = pd.read_csv(os.path.join(CASE, "profile.csv")) if pr is None else pr
    code = {m: i for i, m in enumerate(MODES)}

    def arr(col, nd=0):
        v = d[col].round(nd) if nd else d[col].round(0)
        return [None if np.isnan(x) else (float(x) if nd else int(x)) for x in v]
    out = dict(
        id="power-energy-2023", title="Power and energy profile, 30 Oct - 3 Nov 2023",
        t0=d.time_utc.iloc[0].strftime("%Y-%m-%dT%H:%M:%SZ"), dt=60, n=len(d),
        modes=MODES, mode=[code.get(m, -1) if m else -1 for m in d["mode"]],
        sog=arr("sog_kn", 1),
        lat=arr("latitude_deg", 4), lon=arr("longitude_deg", 4),
        load=[arr(f"engine{n}_load_kw") for n in (1, 2, 3)],
        fuel=[arr(f"engine{n}_fuel_lph", 1) for n in (1, 2, 3)],
        rpm=[arr(f"engine{n}_speed_rpm") for n in (1, 2, 3)],
        azi_rpm=[arr("azi_port_rpmfeedback"), arr("azi_stbd_rpmfeedback")],
        thresholds=dict(v_still_kn=V_STILL, v_transit_kn=V_TRANSIT, azi_on_rpm=AZI_ON, eng_on_kw=ENG_ON),
        assumptions=dict(fuel_density_kg_per_l=FUEL_DENSITY, co2_t_per_t_fuel=CO2_FACTOR, engine_rated_kw=ENG_RATED_KW),
        profile=json.loads(pr.round(2).to_json(orient="records")),
        periods=json.loads(p.to_json(orient="records")),
        summary=json.loads(s.to_json(orient="records")),
    )
    os.makedirs(os.path.dirname(WEB), exist_ok=True)
    with open(WEB, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print("wrote", os.path.relpath(WEB, ROOT), round(os.path.getsize(WEB) / 1e3), "kB")


# ------------------------------------------------------------------ figure
def figure(d=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    d = load_minute() if d is None else d
    t = d.time_utc
    col = {"stationary": "#bfc6cc", "station_keeping": "#2ca58d", "manoeuvring": "#e0a526", "transit": "#2f6fd0"}
    fig, ax = plt.subplots(4, 1, figsize=(12, 8), sharex=True, gridspec_kw=dict(height_ratios=[0.5, 1, 1, 1]))
    for m, c in col.items():
        ax[0].fill_between(t, 0, 1, where=(d["mode"] == m), color=c, step="post", label=m.replace("_", " "))
    ax[0].set_yticks([]); ax[0].legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.9), frameon=False, fontsize=8)
    ax[1].plot(t, d.sog_kn, lw=0.7, color="#333"); ax[1].set_ylabel("speed over ground, kn")
    for n, c in zip((1, 2, 3), ("#e0a526", "#2f6fd0", "#7b5ea7")):
        ax[2].plot(t, d[f"engine{n}_load_kw"], lw=0.7, color=c, label=f"engine {n}")
    ax[2].set_ylabel("engine load, kW"); ax[2].legend(ncol=3, frameon=False, fontsize=8, loc="upper left")
    ax[3].plot(t, d.azi_port_rpmfeedback, lw=0.7, color="#2ca58d", label="port"); ax[3].plot(t, d.azi_stbd_rpmfeedback, lw=0.7, color="#7b5ea7", label="starboard")
    ax[3].set_ylabel("azimuth drive rpm (as logged)"); ax[3].legend(ncol=2, frameon=False, fontsize=8, loc="upper left")
    for a in ax[1:]:
        a.grid(alpha=0.25)
    ax[3].set_xlabel("UTC, 30 Oct - 3 Nov 2023")
    fig.tight_layout()
    os.makedirs(os.path.join(CASE, "figures"), exist_ok=True)
    fig.savefig(os.path.join(CASE, "figures", "overview.png"), dpi=130)
    print("wrote figures/overview.png")


STEPS = ["minute", "periods", "summary", "profile", "channels", "web", "figure"]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = sys.argv[1]
    steps = sys.argv[2:] or STEPS
    d = None
    if "minute" in steps:
        d = minute(src)
    for st in steps:
        if st == "periods": periods(d)
        elif st == "summary": summary(d)
        elif st == "profile": profile(d)
        elif st == "channels": channels()
        elif st == "web": web(d)
        elif st == "figure": figure(d)
        elif st != "minute": sys.exit(f"unknown step {st}")
