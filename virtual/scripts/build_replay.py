#!/usr/bin/env python3
"""Build the replay files behind pages/virtual.html (the virtual bridge).

Run from the repository root:

    python3 virtual/scripts/build_replay.py

Needs: python3 with pandas and numpy. Reads only files already in this repository:

  * operational/power-energy-2023/data/power_1min.csv.gz   whole cruise week, 1-minute means
  * operational/wave-shielding-2023/data/wave_radar_params.csv  wave radar during the wave-shielding test
    (31 Oct 2023 10:00-12:10 UTC, about 1/min; the test window is taken from vessel_1hz.csv.gz)

Writes:

  * virtual/data/replay-2023-w44.json      the week, one value per minute per topic
  * virtual/data/replay-2023-10-31-wave-test.json the wave radar values of the test

The 1 Hz day files (replay-<date>-1hz.json, all signals at 1 Hz for the whole week) are made from the raw
logger files by virtual/scripts/build_days.py.

All files use the message format described in virtual/README.md: every signal is a topic
(gunnerus/<system>/<unit>/<quantity>) with its own metadata (unit, crosswalk id, source tag, status),
so the same topics can later be published one value at a time over MQTT.
No values are interpolated; gaps stay null. The page may draw smooth motion between values,
which is display only.
"""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
WEEK = ROOT / "operational/power-energy-2023/data/power_1min.csv.gz"
FINE = ROOT / "operational/wave-shielding-2023/data/vessel_1hz.csv.gz"   # only its time column (the test window)
OUT = ROOT / "virtual/data"

FORMAT = "gunnerus-virtual/1"
NUC = "NUC logger, tag Gunnerus/"

# topic: (column, unit, decimals, crosswalk id, source tag or derivation, status, description)
WEEK_TOPICS = {
    "gunnerus/nav/gps/lat":          ("latitude_deg", "deg N", 5, "N01", NUC + "SeapathGPSGga/Latitude", "measured", "Latitude, mean of the minute (converted from ddmm.mmmm per sample)"),
    "gunnerus/nav/gps/lon":          ("longitude_deg", "deg E", 5, "N02", NUC + "SeapathGPSGga/Longitude", "measured", "Longitude, mean of the minute (converted from dddmm.mmmm per sample)"),
    "gunnerus/nav/gps/sog":          ("sog_kn", "kn", 2, "N03", NUC + "SeapathGPSVtg/SpeedKnots", "measured", "Speed over ground"),
    "gunnerus/nav/track/cog":        ("cog_track_deg", "deg", 0, "N05", "derived: bearing between the positions one minute before and after, when SOG >= 1 kn; otherwise empty", "derived", "Course over ground from the 1-minute track"),
    "gunnerus/ops/state":            ("mode", "-", None, None, "derived: power-energy-2023 rules (transit >= 8 kn, manoeuvring >= 0.5 kn, station keeping if azimuth rpm > 5, else stationary)", "derived", "Operating state"),
    "gunnerus/engine/1/load":        ("engine1_load_kw", "kW", 1, "E02", NUC + "Engine1/engine_load", "measured", "Engine 1 load"),
    "gunnerus/engine/1/fuel":        ("engine1_fuel_lph", "L/h", 1, "E03", NUC + "Engine1/fuel_consumption", "measured", "Engine 1 fuel rate (probably computed from load by the logger)"),
    "gunnerus/engine/1/speed":       ("engine1_speed_rpm", "rpm", 0, "E01", NUC + "Engine1/engine_speed", "measured", "Engine 1 speed"),
    "gunnerus/engine/2/load":        ("engine2_load_kw", "kW", 1, "E02", NUC + "Engine2/engine_load", "measured", "Engine 2 load"),
    "gunnerus/engine/2/fuel":        ("engine2_fuel_lph", "L/h", 1, "E03", NUC + "Engine2/fuel_consumption", "measured", "Engine 2 fuel rate (probably computed from load by the logger)"),
    "gunnerus/engine/2/speed":       ("engine2_speed_rpm", "rpm", 0, "E01", NUC + "Engine2/engine_speed", "measured", "Engine 2 speed"),
    "gunnerus/engine/3/load":        ("engine3_load_kw", "kW", 1, "E02", NUC + "Engine3/engine_load", "measured", "Engine 3 load"),
    "gunnerus/engine/3/fuel":        ("engine3_fuel_lph", "L/h", 1, "E03", NUC + "Engine3/fuel_consumption", "measured", "Engine 3 fuel rate (probably computed from load by the logger)"),
    "gunnerus/engine/3/speed":       ("engine3_speed_rpm", "rpm", 0, "E01", NUC + "Engine3/engine_speed", "measured", "Engine 3 speed"),
    "gunnerus/azimuth/port/rpm":     ("azi_port_rpmfeedback", "as logged", 1, "T03", NUC + "hcx_port_mp/RPMFeedback", "measured", "Port azimuth propeller speed feedback (unit not documented; rpm assumed)"),
    "gunnerus/azimuth/port/load":    ("azi_port_load_feedback", "as logged", 1, "T05", NUC + "hcx_port_mp/LoadFeedback", "measured", "Port azimuth load feedback (percent of 500 kW or kW: not documented)"),
    "gunnerus/azimuth/stbd/rpm":     ("azi_stbd_rpmfeedback", "as logged", 1, "T03", NUC + "hcx_stbd_mp/RPMFeedback", "measured", "Starboard azimuth propeller speed feedback (unit not documented; rpm assumed)"),
    "gunnerus/azimuth/stbd/load":    ("azi_stbd_load_feedback", "as logged", 1, "T05", NUC + "hcx_stbd_mp/LoadFeedback", "measured", "Starboard azimuth load feedback (percent of 500 kW or kW: not documented)"),
    "gunnerus/tunnel/bow/feedback":  ("tunnel_thruster_feedback_pct", "%", 0, "T11", NUC + "dpThruster/FeedbackProsent", "measured", "Bow tunnel thruster feedback (zero all week)"),
}

# Miros wave radar, about one value per minute: placed on the 1 Hz grid at its own second, null elsewhere
RADAR = "operational/wave-shielding-2023/data/wave_radar_params.csv"
MIROS = "Miros wave radar, wave-shielding case file wave_radar_params.csv, column "
RADAR_TOPICS = {
    "gunnerus/env/waves/hs_rangefinder": ("rangefinder_hm0_m", "m", 2, "N12", MIROS + "rangefinder_hm0_m", "measured", "Significant wave height, Miros RangeFinder (the value used in Wang et al. 2025)"),
    "gunnerus/env/waves/ts_rangefinder": ("rangefinder_ts_s", "s", 1, None, MIROS + "rangefinder_ts_s", "measured", "Significant wave period, Miros RangeFinder"),
    "gunnerus/env/waves/hs_wavex":       ("hm0_m", "m", 2, "N12", MIROS + "hm0_m", "measured", "Significant wave height, Miros WaveX (about 1.7 m against 0.7 m from the RangeFinder; see the case's known issues)"),
    "gunnerus/env/waves/tp_wavex":       ("tp1_s", "s", 1, None, MIROS + "tp1_s", "measured", "Peak period, Miros WaveX"),
    "gunnerus/env/waves/dir_wavex":      ("dp1_deg", "deg", 0, None, MIROS + "dp1_deg", "measured", "Peak wave direction, Miros WaveX (coming from)"),
}

def bearing(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def series(values, dec):
    out = []
    for v in values:
        if v is None or (isinstance(v, float) and np.isnan(v)):
            out.append(None)
        elif dec is None:
            out.append(v)
        elif dec == 0:
            out.append(int(round(float(v))))
        else:
            out.append(round(float(v), dec))
    return out


def meta(spec, rate):
    col, unit, dec, cw, src, status, desc = spec
    m = dict(unit=unit, status=status, source=src, rate=rate, description=desc)
    if cw:
        m["crosswalk"] = cw
    return m


def build_week():
    d = pd.read_csv(WEEK)
    lat, lon, sog = d.latitude_deg.values, d.longitude_deg.values, d.sog_kn.values
    cog = [None] * len(d)
    for i in range(1, len(d) - 1):
        if not np.isnan(sog[i]) and sog[i] >= 1.0 and not np.isnan(lat[i - 1]) and not np.isnan(lat[i + 1]):
            if (lat[i - 1], lon[i - 1]) != (lat[i + 1], lon[i + 1]):
                cog[i] = bearing(lat[i - 1], lon[i - 1], lat[i + 1], lon[i + 1])
    d["cog_track_deg"] = cog
    d["mode"] = d["mode"].where(d["mode"].notna(), None)
    topics, data = {}, {}
    for t, spec in WEEK_TOPICS.items():
        topics[t] = meta(spec, "1 min (mean of the logged samples)")
        vals = d[spec[0]].tolist()
        data[t] = series(vals, spec[2]) if spec[2] is not None else [v if isinstance(v, str) else None for v in vals]
    t0 = d.time_utc.iloc[0]
    return dict(format=FORMAT, id="replay-2023-w44", title="Gunnerus cruise week 44, 30 Oct - 3 Nov 2023, 1-minute values",
                t0=t0, dt=60, n=len(d), topics=topics, data=data,
                source="operational/power-energy-2023/data/power_1min.csv.gz",
                credit="Data provided by Robert Skulstad (NTNU); organised by Henrique M. Gaspar")


def build_waves():
    """Wave radar values of the wave-shielding test, on a 1 s grid over the test window (null between values)."""
    v = pd.read_csv(FINE, usecols=["time_utc"])
    t0s = pd.Timestamp(v.time_utc.iloc[0])
    r = pd.read_csv(ROOT / RADAR)
    sec = ((pd.to_datetime(r.time_utc) - t0s).dt.total_seconds()).round().astype(int)
    topics, data = {}, {}
    for t, spec in RADAR_TOPICS.items():
        arr = [None] * len(v)
        for k, val in zip(sec, pd.to_numeric(r[spec[0]], errors="coerce")):
            if 0 <= k < len(v) and not np.isnan(val):
                arr[k] = round(float(val), spec[2]) if spec[2] else int(round(float(val)))
        topics[t] = meta(spec, "about 1/min (radar processing interval)")
        data[t] = arr
    return dict(format=FORMAT, id="replay-2023-10-31-wave-test", title="Gunnerus 31 Oct 2023 10:00-12:10 UTC, wave radar during the wave-shielding test",
                t0=t0s.strftime("%Y-%m-%dT%H:%M:%SZ"), dt=1, n=len(v), topics=topics, data=data,
                source=RADAR,
                study="Wang et al. (2025), Ocean Engineering 320, 120189, doi:10.1016/j.oceaneng.2024.120189",
                credit="Data provided by Robert Skulstad (NTNU); see the wave-shielding case for the study and credits")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, obj in (("replay-2023-w44.json", build_week()), ("replay-2023-10-31-wave-test.json", build_waves())):
        p = OUT / name
        p.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
        print(f"wrote {p.relative_to(ROOT)}  {p.stat().st_size/1e3:.0f} kB  {len(obj['topics'])} topics x {obj['n']} steps")


if __name__ == "__main__":
    main()
