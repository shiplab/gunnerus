#!/usr/bin/env python3
"""Build the 1 Hz day files behind pages/virtual.html from the raw NUC logger export.

    python3 virtual/scripts/build_days.py "<...>/Tokt uke 44 2023/vessel data from nuc PC/second_try/Gunnerus-w44" [copy1 copy2 ...] [--out DIR]

The raw folder holds one file per UTC day (copy1 = 30 Oct ... copy5 = 3 Nov 2023), long format
`time, tag, value`, newest row first, about 260 MB each. The raw files are not in the repository.
Needs: python3 with pandas and numpy. About 20-40 s per day.

Writes virtual/data/replay-<yyyy-mm-dd>-1hz.json, one per day, message format gunnerus-virtual/1
(see virtual/README.md) with encoding "changes":

  * every topic is put on a 1-second grid from 00:00:00 UTC: the last logged sample in each second;
  * the logger writes on change, so a value holds until the next one; only the seconds where the
    value changes are stored, as {"t": [seconds since the previous entry], "v": [value x 10^dec]};
  * where no sample arrives for more than GAP_S seconds, a null is stored GAP_S seconds after the last
    sample, so a real gap shows as "no data" instead of an old value.

No values are interpolated. Position is logged as NMEA ddmm.mmmm and converted per sample.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
GAP_S = 30
FORMAT = "gunnerus-virtual/1"
NUC = "NUC logger, tag Gunnerus/"

# raw tag: (topic, unit, decimals, crosswalk id, status, description)
TAGS = {
    "SeapathGPSGga/Latitude":      ("gunnerus/nav/gps/lat", "deg N", 6, "N01", "Latitude (converted from ddmm.mmmm)"),
    "SeapathGPSGga/Longitude":     ("gunnerus/nav/gps/lon", "deg E", 6, "N02", "Longitude (converted from dddmm.mmmm)"),
    "SeapathGPSVtg/SpeedKnots":    ("gunnerus/nav/gps/sog", "kn", 2, "N03", "Speed over ground"),
    "SeapathGPSVtg/CourseTrue":    ("gunnerus/nav/gps/cog", "deg", 1, "N05", "Course over ground (noisy at near-zero speed)"),
    "SeapathMRU/Heading":          ("gunnerus/nav/mru/heading", "deg", 1, "N06", "Heading, true"),
    "SeapathMRU/Roll":             ("gunnerus/nav/mru/roll", "deg", 2, "N07", "Roll"),
    "SeapathMRU/Pitch":            ("gunnerus/nav/mru/pitch", "deg", 2, "N08", "Pitch"),
    "SeapathMRU/Heave":            ("gunnerus/nav/mru/heave", "m", 2, "N09", "Heave (sign convention as logged)"),
    "SeapathMRU_rates/YawRate":    ("gunnerus/nav/mru/yaw_rate", "deg/s", 2, None, "Rate of turn"),
    "dpWind/Wind_Speed":           ("gunnerus/env/wind/speed", "kn", 1, "N10", "Wind speed (DP wind sensor; relative or true not documented)"),
    "dpWind/Wind_Direction":       ("gunnerus/env/wind/dir", "deg", 0, "N11", "Wind direction (DP wind sensor; reference not documented)"),
    "hcx_port_mp/AzimuthFeedback": ("gunnerus/azimuth/port/angle", "as logged", 1, "T01", "Port azimuth angle feedback (degrees assumed; zero reference not documented)"),
    "hcx_port_mp/AzimuthOrder":    ("gunnerus/azimuth/port/angle_order", "as logged", 1, "T02", "Port azimuth angle order"),
    "hcx_port_mp/RPMFeedback":     ("gunnerus/azimuth/port/rpm", "as logged", 1, "T03", "Port azimuth propeller speed feedback (rpm assumed)"),
    "hcx_port_mp/LoadFeedback":    ("gunnerus/azimuth/port/load", "as logged", 1, "T05", "Port azimuth load feedback (percent of 500 kW or kW: not documented)"),
    "hcx_stbd_mp/AzimuthFeedback": ("gunnerus/azimuth/stbd/angle", "as logged", 1, "T01", "Starboard azimuth angle feedback (degrees assumed; zero reference not documented)"),
    "hcx_stbd_mp/AzimuthOrder":    ("gunnerus/azimuth/stbd/angle_order", "as logged", 1, "T02", "Starboard azimuth angle order"),
    "hcx_stbd_mp/RPMFeedback":     ("gunnerus/azimuth/stbd/rpm", "as logged", 1, "T03", "Starboard azimuth propeller speed feedback (rpm assumed)"),
    "hcx_stbd_mp/LoadFeedback":    ("gunnerus/azimuth/stbd/load", "as logged", 1, "T05", "Starboard azimuth load feedback (percent of 500 kW or kW: not documented)"),
    "dpThruster/FeedbackProsent":  ("gunnerus/tunnel/bow/feedback", "%", 0, "T11", "Bow tunnel thruster feedback"),
    "Crane1/slewing_angle":        ("gunnerus/crane/main/slew", "deg", 0, "C05", "Crane slewing angle"),
    "Crane1/main_boom_angle":      ("gunnerus/crane/main/boom", "deg", 0, "C02", "Crane main boom angle"),
    "Crane1/outer_boom_angle":     ("gunnerus/crane/main/outer_boom", "deg", 0, "C03", "Crane outer boom angle (sign convention differs from the main boom)"),
    "Crane1/extension_length_outer_boom": ("gunnerus/crane/main/extension", "as logged", 0, "C04", "Outer boom extension (documented in m; values suggest cm)"),
    "Crane1/dp_main_cyl":          ("gunnerus/crane/main/cyl_dp", "as logged", 0, "C01", "Main cylinder differential pressure"),
}
ENGINE = {  # tag suffix: (quantity, unit, decimals, crosswalk id, description)
    "engine_load": ("load", "kW", 1, "E02", "load"),
    "fuel_consumption": ("fuel", "L/h", 1, "E03", "fuel rate (probably computed from load by the logger)"),
    "engine_speed": ("speed", "rpm", 0, "E01", "speed"),
    "coolant_temperature": ("coolant_temp", "°C (as logged)", 1, "E06", "coolant temperature"),
    "lube_oil_temperature": ("lube_oil_temp", "°C (as logged)", 1, "E05", "lube oil temperature"),
    "lube_oil_pressure": ("lube_oil_press", "bar (as logged)", 2, "E04", "lube oil pressure"),
    "boost_pressure": ("boost_press", "bar (as logged)", 2, "E07", "boost pressure"),
    "exhaust_temperature1": ("exhaust_temp_1", "°C (as logged)", 0, "E08", "exhaust temperature, bank 1"),
    "exhaust_temperature2": ("exhaust_temp_2", "°C (as logged)", 0, "E09", "exhaust temperature, bank 2"),
}
for n in (1, 2, 3):
    for suf, (q, unit, dec, cw, desc) in ENGINE.items():
        TAGS[f"Engine{n}/{suf}"] = (f"gunnerus/engine/{n}/{q}", unit, dec, cw, f"Engine {n} {desc}")


def ddmm(v):
    d = np.floor(v / 100.0)
    return d + (v - d * 100.0) / 60.0


def encode(sec, val, dec):
    """Change list on the 1 s grid: value changes and gaps longer than GAP_S."""
    ts, vs, last_t, last_v, prev = [], [], 0, None, None
    scale = 10 ** dec
    for s, v in zip(sec, val):
        s = int(s)
        if prev is not None and s - prev > GAP_S and last_v is not None:
            ts.append(prev + GAP_S - last_t); vs.append(None); last_t = prev + GAP_S; last_v = None
        iv = int(round(v * scale))
        if iv != last_v:
            ts.append(int(s) - last_t); vs.append(iv); last_t = int(s); last_v = iv
        prev = s
    if prev is not None and prev < 86399 - GAP_S and last_v is not None:
        ts.append(prev + GAP_S - last_t); vs.append(None)
    return {"t": ts, "v": vs}


def build_day(path, out_dir):
    df = pd.read_csv(path, header=None, names=["time", "tag", "value"], dtype={"time": str, "tag": str, "value": str})
    df = df[df.tag.str.startswith("Gunnerus/")]
    df["tag"] = df.tag.str.slice(9)
    df = df[df.tag.isin(TAGS)]
    df["value"] = pd.to_numeric(df.value, errors="coerce")
    df = df.dropna(subset=["value"])
    day = df.time.str.slice(0, 10).mode().iloc[0]
    df = df[df.time.str.slice(0, 10) == day]
    t = df.time.str
    df["sec"] = t.slice(11, 13).astype(int) * 3600 + t.slice(14, 16).astype(int) * 60 + t.slice(17, 19).astype(int)
    df = df.sort_values("time", kind="stable")
    for tag in ("SeapathGPSGga/Latitude", "SeapathGPSGga/Longitude"):
        m = df.tag == tag
        df.loc[m, "value"] = ddmm(df.loc[m, "value"].values)
    last = df.groupby(["tag", "sec"], sort=True).value.last()
    topics, data = {}, {}
    for tag, (topic, unit, dec, cw, desc) in TAGS.items():
        meta = dict(unit=unit, status="measured", source=NUC + tag, rate="as logged (on change), last sample per second", description=desc, scale=dec)
        if cw:
            meta["crosswalk"] = cw
        topics[topic] = meta
        if tag in last.index.get_level_values(0):
            s = last.loc[tag]
            data[topic] = encode(s.index.values, s.values, dec)
        else:
            data[topic] = {"t": [], "v": []}
    obj = dict(format=FORMAT, id=f"replay-{day}-1hz", title=f"Gunnerus {day}, NUC logger at 1 Hz", t0=f"{day}T00:00:00Z", dt=1, n=86400,
               encoding="changes", gap_s=GAP_S, topics=topics, data=data, source=f"raw NUC logger export, file {Path(path).name} (not in the repository)",
               credit="Data provided by Robert Skulstad (NTNU); organised by Henrique M. Gaspar")
    out = Path(out_dir) / f"replay-{day}-1hz.json"
    out.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
    n = {k: len(v["t"]) for k, v in data.items()}
    print(f"{Path(path).name} -> {out.name}  {out.stat().st_size/1e6:.1f} MB  entries: heading {n['gunnerus/nav/mru/heading']}, roll {n['gunnerus/nav/mru/roll']}, heave {n['gunnerus/nav/mru/heave']}")


def main():
    args = [a for a in sys.argv[1:]]
    out = ROOT / "virtual/data"
    if "--out" in args:
        k = args.index("--out"); out = Path(args[k + 1]); del args[k:k + 2]
    raw = Path(args[0])
    names = args[1:] or sorted(p.name for p in raw.iterdir() if re.fullmatch(r"copy\d", p.name))
    Path(out).mkdir(parents=True, exist_ok=True)
    for name in names:
        build_day(raw / name, out)


if __name__ == "__main__":
    main()
