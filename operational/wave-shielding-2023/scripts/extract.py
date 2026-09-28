"""
Extract the RV Gunnerus wave-shielding experiment (31 Oct 2023, 10:00-12:10 UTC)
from the raw cruise data ("Tokt uke 44 2023") into the files in ../data.

Experiment, set-up and findings: Wang, T., Skulstad, R., Holmeset, F.T., Halse, K.H.,
Hildre, H.P., Zhang, H. (2025). Full-scale experimental research on wave shielding
effect of RV Gunnerus for offshore operations. Ocean Engineering 320, 120189.
https://doi.org/10.1016/j.oceaneng.2024.120189

Dataset organised by Jisang Ha and Henrique M. Gaspar (NTNU).

Usage:  python3 extract.py <path to "Tokt uke 44 2023"> [step ...]
Steps:  cases vessel seapath buoy crane radar airgap figure   (default: all)
Needs:  python 3.9+, pandas, numpy, matplotlib
"""
import sys, os, glob, json, math
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data")
FIG = os.path.join(HERE, "..", "figures")
T0 = pd.Timestamp("2023-10-31 10:00:00", tz="UTC")
T1 = pd.Timestamp("2023-10-31 12:10:00", tz="UTC")
FMT = "%.6g"

# Paper, Table 3: angle to wave 1 (main) and wave 2, per case
PAPER_ANGLES = {1: (90, 0), 2: (105, 15), 3: (120, 30), 4: (135, 45),
                5: (150, 60), 6: (165, 75), 7: (180, 90)}


def win(df, col="time_utc"):
    return df[(df[col] >= T0) & (df[col] < T1)].reset_index(drop=True)


def iso(s):
    return s.dt.strftime("%Y-%m-%dT%H:%M:%S.%f").str[:-3] + "Z"


def save(df, name, gz=True):
    df = df.copy()
    df["time_utc"] = iso(df["time_utc"])
    path = os.path.join(OUT, name + (".csv.gz" if gz else ".csv"))
    df.to_csv(path, index=False, float_format=FMT, compression="gzip" if gz else None)
    print(f"{name}: {len(df)} rows, {df.shape[1]} cols, {os.path.getsize(path)/1e6:.2f} MB")


def load_cases(src):
    """Case windows = the 7 segments prepared with the raw data (NUC/DP_all_seg)."""
    rows = []
    for i in range(1, 8):
        f = os.path.join(src, "time series motion prediction data", "NUC", "DP_all_seg",
                         f"2023_10_31_dp1_{i}.csv")
        t = pd.read_csv(f, usecols=["time"])["time"]
        rows.append((i, pd.Timestamp(t.iloc[0], tz="UTC"),
                     pd.Timestamp(t.iloc[-1], tz="UTC") + pd.Timedelta(seconds=1)))
    return rows


def tag_case(times, cases):
    c = np.zeros(len(times), dtype=int)
    for i, a, b in cases:
        c[((times >= a) & (times < b)).to_numpy()] = i
    return c


def ddmm_to_deg(x):
    d = np.floor(x / 100.0)
    return d + (x - 100.0 * d) / 60.0


def circ_mean(deg):
    r = np.deg2rad(deg.dropna())
    return (np.rad2deg(math.atan2(np.sin(r).mean(), np.cos(r).mean())) + 360) % 360


# ---------------------------------------------------------------- vessel (NUC)
VESSEL_NAMES = {
    "SeapathGPSGga/Latitude": "lat_deg", "SeapathGPSGga/Longitude": "lon_deg",
    "SeapathGPSVbw/LonGroundSpeed": "speed_long_kn", "SeapathGPSVbw/TransGroundSpeed": "speed_trans_kn",
    "SeapathGPSVtg/CourseTrue": "cog_deg", "SeapathGPSVtg/SpeedKnots": "sog_kn",
    "SeapathGPSVtg/SpeedKmHr": "sog_kmh",
    "SeapathMRU/Heading": "heading_deg", "SeapathMRU/Roll": "roll_deg",
    "SeapathMRU/Pitch": "pitch_deg", "SeapathMRU/Heave": "heave_m",
    "SeapathMRU_rates/RollRate": "roll_rate_degs", "SeapathMRU_rates/PitchRate": "pitch_rate_degs",
    "SeapathMRU_rates/YawRate": "yaw_rate_degs", "SeapathMRU_rates/VertVel": "heave_rate_ms",
    "dpWind/Wind_Direction": "wind_dir_deg", "dpWind/Wind_Speed": "wind_speed_kn",
    "Crane1/slewing_angle": "crane_slewing_angle_deg",
    "Crane1/main_boom_angle": "crane_main_boom_angle_deg",
    "Crane1/outer_boom_angle": "crane_outer_boom_angle_deg",
    "Crane1/extension_length_outer_boom": "crane_extension_outer_boom",
    "Crane1/dp_main_cyl": "crane_dp_main_cyl",
    "dpThruster/FeedbackProsent": "tunnel_thruster_feedback_pct",
    "dpThruster/ThrusterSetpunktProsent": "tunnel_thruster_setpoint_pct",
}


def vessel_name(tag):
    t = tag.replace("Gunnerus/", "")
    if t in VESSEL_NAMES:
        return VESSEL_NAMES[t]
    grp, sig = t.split("/", 1)
    snake = "".join("_" + ch.lower() if ch.isupper() and i and not sig[i-1].isupper() and sig[i-1] != "_" else ch.lower()
                    for i, ch in enumerate(sig))
    if grp.startswith("hcx_port"):
        return "azi_port_" + snake
    if grp.startswith("hcx_stbd"):
        return "azi_stbd_" + snake
    return grp.lower() + "_" + snake


def vessel(src, cases):
    f = os.path.join(src, "vessel data from nuc PC", "second_try", "Gunnerus-w44", "copy2")
    keep = []
    for ch in pd.read_csv(f, header=None, names=["t", "tag", "v"], chunksize=1_000_000, dtype=str):
        m = (ch.t >= "2023-10-31 10:00") & (ch.t < "2023-10-31 12:10")
        if m.any():
            keep.append(ch[m])
    d = pd.concat(keep)
    d["time_utc"] = pd.to_datetime(d.t, utc=True, format="ISO8601").dt.floor("s")
    d["v"] = pd.to_numeric(d.v, errors="coerce")
    d = d.sort_values(["t"]).groupby(["time_utc", "tag"]).v.last().unstack("tag")
    d = d.reindex(pd.date_range(T0, T1, freq="1s", inclusive="left", name="time_utc"))
    d.columns = [vessel_name(c) for c in d.columns]
    for c in ["lat_deg", "lon_deg"]:
        d[c] = ddmm_to_deg(d[c])
    first = ["lat_deg", "lon_deg", "heading_deg", "roll_deg", "pitch_deg", "heave_m",
             "roll_rate_degs", "pitch_rate_degs", "yaw_rate_degs", "heave_rate_ms",
             "cog_deg", "sog_kn", "sog_kmh", "speed_long_kn", "speed_trans_kn",
             "wind_dir_deg", "wind_speed_kn"]
    first = [c for c in first if c in d.columns]
    rest = sorted(c for c in d.columns if c not in first)
    d = d[first + rest].reset_index()
    d.insert(1, "case", tag_case(d.time_utc, cases))
    save(d, "vessel_1hz")
    return d


# ------------------------------------------------------------- seapath (2 Hz)
def seapath(src, cases):
    f = os.path.join(src, "time series motion prediction data", "SeaPath", "DP", "2023_10_31_dp1.csv")
    s = pd.read_csv(f, usecols=["seconds", "latitude", "longitude", "height", "heave", "northVelocity",
                                "eastVelocity", "downVelocity", "roll", "pitch", "heading",
                                "rollRate", "pitchRate", "yawRate"])
    d = pd.DataFrame({"time_utc": pd.to_datetime(s.seconds, unit="s", utc=True)})
    d["lat_deg"], d["lon_deg"] = s.latitude, s.longitude
    d["height_m"] = s.height / 100
    d["heave_down_m"] = s.heave / 100
    d["vel_north_ms"], d["vel_east_ms"], d["vel_down_ms"] = s.northVelocity / 100, s.eastVelocity / 100, s.downVelocity / 100
    d["roll_deg"], d["pitch_deg"], d["heading_deg"] = s.roll, s.pitch, s.heading
    d["roll_rate_degs"], d["pitch_rate_degs"], d["yaw_rate_degs"] = s.rollRate, s.pitchRate, s.yawRate
    d = win(d)
    d.insert(1, "case", tag_case(d.time_utc, cases))
    save(d, "seapath_2hz")


# ---------------------------------------------------------- wave buoy (50 Hz)
def buoy(src, cases):
    base = os.path.join(src, "Wave buoy data", "LainePoiss (small buoy)", "31oct_first_location")
    files = sorted(glob.glob(os.path.join(base, "decompressed", "raw_2023_10_31_09_23_NR*.txt")))
    head = open(files[0]).readline()             # "2023.10.31 09:23:46 UTC, ..."
    start = pd.Timestamp(head.split(" UTC")[0].replace(".", "-", 2), tz="UTC")
    b = pd.concat([pd.read_csv(f, skiprows=1) for f in files], ignore_index=True)
    d = pd.DataFrame({"time_utc": start + pd.to_timedelta(b["Time (ms)"], unit="ms")})
    ren = {"AccX (m/s2)": "acc_x_ms2", "AccY (m/s2)": "acc_y_ms2", "AccZ (m/s2)": "acc_z_ms2",
           "Pitch (deg)": "pitch_deg", "Roll (deg)": "roll_deg", "Yaw (deg)": "yaw_deg",
           "Latitude (deg)": "lat_deg", "Longitude (deg)": "lon_deg", "hAcc (mm)": "gps_hacc_mm",
           "Satellites": "gps_satellites", "Temperature (°C)": "temperature_c"}
    for k, v in ren.items():
        d[v] = b[k]
    d = win(d)
    d.insert(1, "case", tag_case(d.time_utc, cases))
    save(d, "wave_buoy_50hz")

    # on-board wave parameters, one row per ~22-min block
    web = [l.split() for l in open(os.path.join(base, "web_sent", "web.txt")) if l.startswith("2023-10-31")]
    rows = []
    for wf, w in zip(sorted(glob.glob(os.path.join(base, "waveparam_lte", "wp_LTE_*.txt"))), web):
        lines = open(wf).read().splitlines()
        hdr, val = lines[0].split(","), lines[1].split(",")
        i = hdr.index("cf[0..17]")
        names = hdr[:i] + hdr[i+1:]
        vals = val[:i] + val[i+18:]
        r = dict(zip(names, vals))
        r["time_utc"] = pd.Timestamp(w[0] + " " + w[1], tz="UTC")
        rows.append(r)
    p = pd.DataFrame(rows)
    keep = {"Latitude (deg)": "lat_deg", "Longitude (deg)": "lon_deg", "Hm0 (m)": "hm0_m",
            "Hmax_up (m)": "hmax_m", "Peakper (s)": "tp_s", "Tm01 (s)": "tm01_s", "Tm02 (s)": "tm02_s",
            "Tmm10 (s)": "tm_10_s", "Pdirnaut (deg)": "peak_dir_deg", "Meandir (deg)": "mean_dir_deg",
            "Spread (deg)": "spread_deg"}
    q = pd.DataFrame({"time_utc": p.time_utc})
    for k, v in keep.items():
        q[v] = pd.to_numeric(p[k])
    save(q, "wave_buoy_params", gz=False)


# ---------------------------------------------------- crane-tip IMU (~17 Hz)
def crane(src, cases):
    f = os.path.join(src, "Crane accelerometers data", "2023-10-31_10_22_44_my_iOS_device.csv")
    ren = {"locationLatitude": "lat_deg", "locationLongitude": "lon_deg",
           "accelerometerAccelerationX": "acc_x_g", "accelerometerAccelerationY": "acc_y_g",
           "accelerometerAccelerationZ": "acc_z_g",
           "gyroRotationX": "gyro_x_rads", "gyroRotationY": "gyro_y_rads", "gyroRotationZ": "gyro_z_rads",
           "motionRoll": "att_roll_rad", "motionPitch": "att_pitch_rad", "motionYaw": "att_yaw_rad",
           "motionUserAccelerationX": "user_acc_x_g", "motionUserAccelerationY": "user_acc_y_g",
           "motionUserAccelerationZ": "user_acc_z_g",
           "motionGravityX": "gravity_x_g", "motionGravityY": "gravity_y_g", "motionGravityZ": "gravity_z_g"}
    c = pd.read_csv(f, usecols=["loggingTime"] + list(ren), low_memory=False)   # device/IP columns dropped
    d = pd.DataFrame({"time_utc": pd.to_datetime(c.loggingTime, unit="s", utc=True)})
    for k, v in ren.items():
        d[v] = pd.to_numeric(c[k], errors="coerce")
    d = win(d)
    d.insert(1, "case", tag_case(d.time_utc, cases))
    save(d, "crane_tip_imu")


# --------------------------------------------------------- Miros wave radar
def radar(src, cases):
    f = os.path.join(src, "miros wave data", "wave parameters", "miros_wave_params_31_oct.csv")
    m = pd.read_csv(f, skiprows=[0, 1], low_memory=False)
    m.columns = ["Timestamp", "Dp2-t", "Dp1-t", "Tp1", "Dm1-t", "Hm0", "Tm01", "Dm2-t", "Tp2",
                 "freq_res", "spectrum", "status", "rf_Hm0", "rf_Ts", "point_spectrum"]
    m["time_utc"] = pd.to_datetime(m.Timestamp, utc=True)
    m = win(m)
    p = m[["time_utc"]].copy()
    ren = {"Hm0": "hm0_m", "Tp1": "tp1_s", "Dp1-t": "dp1_deg", "Tm01": "tm01_s", "Tp2": "tp2_s",
           "Dp2-t": "dp2_deg", "Dm1-t": "dm1_deg", "Dm2-t": "dm2_deg", "rf_Hm0": "rangefinder_hm0_m",
           "rf_Ts": "rangefinder_ts_s"}
    for k, v in ren.items():
        p[v] = pd.to_numeric(m[k], errors="coerce")
    p = p.dropna(axis=1, how="all")
    p = p[p.drop(columns="time_utc").notna().any(axis=1)].reset_index(drop=True)
    p.insert(1, "case", tag_case(p.time_utc, cases))
    save(p, "wave_radar_params", gz=False)

    rows = []
    for t, s in zip(m.time_utc, m.spectrum):
        if not isinstance(s, str):
            continue
        j = json.loads(s)
        a = np.array(j["data"], dtype=float)          # [direction][frequency]
        a[a <= -999] = np.nan
        dirs = j["directionStart"] + j["directionResolution"] * np.arange(j["directionCount"])
        fr = j["frequencyStart"] + j["frequencyResolution"] * np.arange(j["frequencyCount"])
        r = {"time_utc": t, "heading_deg": j.get("heading")}
        for di, dv in enumerate(dirs):
            for fi, fv in enumerate(fr):
                r[f"S_d{int(dv):03d}_f{fv:.2f}"] = a[di, fi]
        rows.append(r)
    d = pd.DataFrame(rows)
    d.insert(1, "case", tag_case(d.time_utc, cases))
    save(d, "wave_radar_spectra")


def airgap(src, cases):
    f = os.path.join(src, "miros wave data", "rangefinder_air_gap", "miros_rangefinder_air_gap_31_oct.csv")
    a = pd.read_csv(f, skiprows=[0, 1])
    d = pd.DataFrame({"time_utc": pd.to_datetime(a.Timestamp, utc=True), "air_gap_m": a.Range})
    d = win(d)
    d.insert(1, "case", tag_case(d.time_utc, cases))
    save(d, "air_gap_2hz")


# ------------------------------------------------------------------- cases
def write_cases(src, cases):
    v = pd.read_csv(os.path.join(OUT, "vessel_1hz.csv.gz"), usecols=["case", "heading_deg"]) \
        if os.path.exists(os.path.join(OUT, "vessel_1hz.csv.gz")) else None
    rows = []
    for i, a, b in cases:
        r = {"case": i, "start_utc": a.strftime("%Y-%m-%dT%H:%M:%SZ"), "end_utc": b.strftime("%Y-%m-%dT%H:%M:%SZ"),
             "duration_s": int((b - a).total_seconds()),
             "angle_to_wave1_deg": PAPER_ANGLES[i][0], "angle_to_wave2_deg": PAPER_ANGLES[i][1]}
        if v is not None:
            r["mean_heading_deg"] = round(circ_mean(v.heading_deg[v.case == i]), 1)
        rows.append(r)
    pd.DataFrame(rows).to_csv(os.path.join(HERE, "..", "cases.csv"), index=False)
    print("cases.csv written")


# ------------------------------------------------------------------ figure
def figure(src, cases):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ink, muted, grid, band = "#0b0b0b", "#52514e", "#e4e3df", "#f0efeb"
    c1, c2 = "#2a78d6", "#eb6834"
    v = pd.read_csv(os.path.join(OUT, "vessel_1hz.csv.gz"), parse_dates=["time_utc"])
    rp = pd.read_csv(os.path.join(OUT, "wave_radar_params.csv"), parse_dates=["time_utc"])
    rf = rp.dropna(subset=["rangefinder_hm0_m"])
    panels = [("heading_deg", "Heading (deg)"), ("roll_deg", "Roll (deg)"),
              ("pitch_deg", "Pitch (deg)"), ("heave_m", "Heave (m)"), (None, "Hs (m)")]
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": muted, "axes.labelcolor": ink,
                         "xtick.color": muted, "ytick.color": muted})
    f, axs = plt.subplots(len(panels), 1, figsize=(10, 9), sharex=True, facecolor="#fcfcfb")
    for ax, (col, lab) in zip(axs, panels):
        ax.set_facecolor("#fcfcfb")
        for i, a, b in cases:
            if i % 2:
                ax.axvspan(a, b, color=band, lw=0, zorder=0)
        if col:
            ax.plot(v.time_utc, v[col], color=c1, lw=0.6 if col != "heading_deg" else 1.5)
        else:
            ax.plot(rf.time_utc, rf.rangefinder_hm0_m, color=c1, lw=1.5, marker="o", ms=3,
                    label="Incident, Miros RangeFinder")
            res = pd.read_csv(os.path.join(HERE, "..", "results.csv"))
            for k, (i, a, b) in enumerate(cases):
                hs = res.loc[res.case == i, "shielded_hs_m"].iloc[0]
                ax.plot([a, b], [hs, hs], color=c2, lw=2.5, solid_capstyle="butt",
                        label="Sheltered side, per case (paper Table 5)" if k == 0 else None)
            ax.legend(loc="upper right", frameon=False, fontsize=8)
        ax.set_ylabel(lab)
        ax.grid(axis="y", color=grid, lw=0.6)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    for i, a, b in cases:
        axs[0].text(a + (b - a) / 2, 1.02, f"Case {i}", transform=axs[0].get_xaxis_transform(),
                    ha="center", va="bottom", color=ink, fontsize=8)
    axs[-1].set_xlim(T0, T1)
    axs[-1].xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%H:%M", tz="UTC"))
    axs[-1].set_xlabel("31 October 2023, UTC")
    f.suptitle("RV Gunnerus wave-shielding experiment: 7 heading cases", x=0.01, ha="left",
               color=ink, fontsize=11)
    f.text(0.01, 0.955, "Experiment: Wang et al. (2025), Ocean Engineering 320, 120189. "
           "Data: RV Gunnerus operational repository.", ha="left", color=muted, fontsize=8)
    f.tight_layout(rect=(0, 0, 1, 0.95))
    os.makedirs(FIG, exist_ok=True)
    f.savefig(os.path.join(FIG, "overview.png"), dpi=150)
    print("figures/overview.png written")


if __name__ == "__main__":
    src = sys.argv[1]
    steps = sys.argv[2:] or ["vessel", "seapath", "buoy", "crane", "radar", "airgap", "cases", "figure"]
    os.makedirs(OUT, exist_ok=True)
    cases = load_cases(src)
    for s in steps:
        {"vessel": vessel, "seapath": seapath, "buoy": buoy, "crane": crane, "radar": radar,
         "airgap": airgap, "cases": write_cases, "figure": figure}[s](src, cases)
