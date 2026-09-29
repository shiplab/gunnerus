"""
Build images/gunnerus-header.png, the banner at the top of the main README:
drawings (2D) | 3D model | operational data.

Run from the repository root:

    python3 images/make_header.py

Needs: python 3.9+, pillow, numpy, pandas, matplotlib, playwright (python, with Chromium),
poppler (pdftoppm). Fonts: Barlow Condensed and IBM Plex Mono .ttf/.woff files; pass their
folder with --fonts (default: system fallback). The 3D render loads three.js 0.169 from
jsDelivr unless --three points to a local copy of the "three" npm package.

Sources, all in this repository:
  2D   polarkonsult/GA Gunnerus Rev1.pdf (profile and 1-deck)
  3D   derived/3d/gunnerus.glb + gunnerus-parts.json, SFI colours as on the website
  Data operational/wave-shielding-2023 (heading, roll, incident and sheltered Hs)
"""
import argparse, glob, os, subprocess, sys, tempfile, threading, http.server, functools
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Website palette (pages/index.html)
PAPER, SHEET, INK, INK2, INK3 = "#f4f6f7", "#ffffff", "#0f1d2a", "#44545f", "#6b7a84"
RULE, RULE2, VIEWER, NTNU, PROP_INK = "#d3dbdf", "#e5eaec", "#e9eef0", "#00509e", "#6b5410"
SFI = {"hull": "#8fa3ad", "super": "#eef1f3", "g5": "#2f6fd0", "g7": "#2ca58d", "g2": "#7b5ea7",
       "outfit": "#bfc6cc", "g1": "#e4572e", "g4": "#e0a526"}

W, H, M, GUT = 2400, 820, 40, 30              # canvas, outer margin, gutter
CW = (W - 2 * M - 2 * GUT) // 3                # card width
CH = H - 2 * M                                 # card height
IMG_H = 612                                    # image area inside a card
CAPTIONS = [("DRAWINGS", "15 production drawings: DWG, DXF and PDF"),
            ("3D MODEL", "C-JOB model, coloured by SFI group"),
            ("OPERATIONAL DATA", "Wave-shielding experiment, 31 Oct 2023")]


def font(folder, name, size, fallback="DejaVuSans.ttf"):
    if folder:
        for f in sorted(glob.glob(os.path.join(folder, "**", name), recursive=True)):
            try:
                return ImageFont.truetype(f, size)
            except OSError:
                continue
    try:
        return ImageFont.truetype(fallback, size)
    except OSError:
        return ImageFont.load_default()


# ------------------------------------------------------------------ 2D panel
def drawings(tmp, w, h):
    pdf = os.path.join(ROOT, "polarkonsult", "GA Gunnerus Rev1.pdf")
    subprocess.run(["pdftoppm", "-r", "220", "-gray", "-png", pdf, os.path.join(tmp, "ga")], check=True)
    ga = Image.open(glob.glob(os.path.join(tmp, "ga*.png"))[0]).convert("L")
    k = 220 / 60                                # crop boxes measured on a 60 dpi render
    views = [ga.crop(tuple(int(v * k) for v in b)) for b in
             [(64, 120, 1365, 640), (180, 1672, 1352, 2012)]]    # profile, 1-deck
    pad = 34
    out = Image.new("RGB", (w, h), SHEET)
    inner = w - 2 * pad
    scaled = []
    for v in views:
        v = v.filter(ImageFilter.MinFilter(5))                  # thicken lines before shrinking
        v = v.resize((inner, round(v.height * inner / v.width)), Image.LANCZOS)
        v = ImageOps.autocontrast(v, cutoff=1)
        v = v.point(lambda p: 255 if p > 235 else int(p * 0.75))  # clean paper, darker ink
        scaled.append(v)
    gap = 26
    y = (h - sum(v.height for v in scaled) - gap) // 2
    ink = Image.new("RGB", (inner, 10), INK)
    for v in scaled:
        mask = ImageOps.invert(v)
        out.paste(ink.resize(v.size), (pad, y), mask)
        y += v.height + gap
    return out


# ------------------------------------------------------------------ 3D panel
RENDER_HTML = """<!doctype html><html><head><meta charset="utf-8">
<script type="importmap">{"imports":{"three":"THREE/build/three.module.js","three/addons/":"THREE/examples/jsm/"}}</script>
<style>html,body{margin:0;background:transparent}canvas{display:block}</style></head><body>
<canvas id="c" width="1400" height="1100"></canvas>
<script type="module">
import * as THREE from "three";
import {GLTFLoader} from "three/addons/loaders/GLTFLoader.js";
import {MeshoptDecoder} from "three/addons/libs/meshopt_decoder.module.js";
import {RoomEnvironment} from "three/addons/environments/RoomEnvironment.js";
const canvas=document.getElementById("c");
const r=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true,preserveDrawingBuffer:true});
r.setSize(1400,1100,false);r.toneMapping=THREE.NeutralToneMapping;
const scene=new THREE.Scene();scene.environment=new THREE.PMREMGenerator(r).fromScene(new RoomEnvironment(),0.04).texture;
scene.add(new THREE.HemisphereLight(0xffffff,0x5a6a74,0.8));
const sun=new THREE.DirectionalLight(0xffffff,1.4);sun.position.set(-20,40,25);scene.add(sun);
const cam=new THREE.PerspectiveCamera(30,1400/1100,0.1,1000);
const COLORS=SFI_COLORS;
const table=await (await fetch("/derived/3d/gunnerus-parts.json")).json();const by=Object.fromEntries(table.map(t=>[t.node,t]));
const g=await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).loadAsync("/derived/3d/gunnerus.glb");
g.scene.traverse(o=>{const i=by[o.name];if(i)o.traverse(m=>{if(m.isMesh){m.material=m.material.clone();m.material.side=THREE.DoubleSide;m.material.color.set(COLORS[i.group_key])}})});
scene.add(g.scene);
const box=new THREE.Box3().setFromObject(g.scene),c=box.getCenter(new THREE.Vector3()),rad=box.getBoundingSphere(new THREE.Sphere()).radius;
const vf=cam.fov*Math.PI/180,hf=2*Math.atan(Math.tan(vf/2)*cam.aspect);
cam.position.copy(c.clone().add(new THREE.Vector3(1,.42,1.05).normalize().multiplyScalar(rad/Math.sin(Math.min(vf,hf)/2)*0.78)));cam.lookAt(c);
r.render(scene,cam);window.DONE=true;
</script></body></html>"""


def model3d(tmp, w, h, three):
    import json
    from playwright.sync_api import sync_playwright
    three_url = "/_three" if three else "https://cdn.jsdelivr.net/npm/three@0.169.0"
    html = RENDER_HTML.replace("THREE/", three_url + "/").replace("SFI_COLORS", json.dumps(SFI))
    page = os.path.join(ROOT, "_header_render.html")
    open(page, "w").write(html)

    class H(http.server.SimpleHTTPRequestHandler):
        def translate_path(self, path):
            if three and path.startswith("/_three/"):
                return os.path.join(three, path[len("/_three/"):].split("?")[0])
            return super().translate_path(path)
        def log_message(self, *a):
            pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(H, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    shot = os.path.join(tmp, "ship.png")
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
            pg = b.new_page(viewport={"width": 1400, "height": 1100})
            pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/_header_render.html")
            pg.wait_for_function("window.DONE", timeout=180000)
            pg.locator("#c").screenshot(path=shot, omit_background=True)
            b.close()
    finally:
        srv.shutdown()
        os.remove(page)
    ship = Image.open(shot)
    ship = ship.crop(ship.getbbox())
    s = min((w - 40) / ship.width, (h - 30) / ship.height)
    ship = ship.resize((round(ship.width * s), round(ship.height * s)), Image.LANCZOS)
    out = Image.new("RGB", (w, h), VIEWER)
    out.paste(ship, ((w - ship.width) // 2, (h - ship.height) // 2 + 6), ship)
    return out


# ---------------------------------------------------------- operational panel
def operational(tmp, w, h, fonts):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    if fonts:
        for f in glob.glob(os.path.join(fonts, "**", "*.ttf"), recursive=True):
            font_manager.fontManager.addfont(f)
    case = os.path.join(ROOT, "operational", "wave-shielding-2023")
    v = pd.read_csv(os.path.join(case, "data", "vessel_1hz.csv.gz"), parse_dates=["time_utc"])
    rp = pd.read_csv(os.path.join(case, "data", "wave_radar_params.csv"), parse_dates=["time_utc"]).dropna(subset=["rangefinder_hm0_m"])
    cs = pd.read_csv(os.path.join(case, "cases.csv"), parse_dates=["start_utc", "end_utc"])
    res = pd.read_csv(os.path.join(case, "results.csv"))
    t0 = v.time_utc.iloc[0]
    mins = lambda t: (t - t0).dt.total_seconds() / 60
    dpi = 100
    fig, axs = plt.subplots(3, 1, figsize=(w / dpi, h / dpi), dpi=dpi, sharex=True, facecolor=SHEET)
    plt.rcParams["font.family"] = ["IBM Plex Mono", "DejaVu Sans Mono"]
    rows = [(mins(v.time_utc), v.heading_deg, "Heading (°)", 1.8), (mins(v.time_utc), v.roll_deg, "Roll (°)", 0.6), (None, None, "Hs (m)", 2.2)]
    for ax, (x, y, lab, lw) in zip(axs, rows):
        ax.set_facecolor(SHEET)
        for _, c in cs.iterrows():
            ax.axvspan(mins(pd.Series([c.start_utc])).iloc[0], mins(pd.Series([c.end_utc])).iloc[0], color=RULE2, lw=0, zorder=0)
        if x is not None:
            ax.plot(x, y, color=NTNU, lw=lw)
        else:
            ax.plot(mins(rp.time_utc), rp.rangefinder_hm0_m, color=NTNU, lw=lw)
            for _, c in cs.iterrows():
                hs = res.loc[res.case == c.case, "shielded_hs_m"].iloc[0]
                a, b = (mins(pd.Series([c.start_utc])).iloc[0], mins(pd.Series([c.end_utc])).iloc[0])
                ax.plot([a, b], [hs, hs], color=PROP_INK, lw=4, solid_capstyle="butt")
            ax.text(129, 0.775, "incident", color=NTNU, ha="right", va="center", fontsize=15)
            ax.text(129, 0.615, "sheltered (paper)", color=PROP_INK, ha="right", va="center", fontsize=15)
            ax.set_ylim(0.6, 0.8)
            ax.set_yticks([0.65, 0.7, 0.75])
        ax.set_ylabel(lab, color=INK2, fontsize=16, labelpad=8)
        ax.tick_params(colors=INK3, labelsize=13, length=0)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.grid(axis="y", color=RULE, lw=0.8)
    axs[0].set_ylim(60, 180)
    axs[1].set_ylim(-8, 8)
    for _, c in cs.iterrows():
        a, b = (mins(pd.Series([c.start_utc])).iloc[0], mins(pd.Series([c.end_utc])).iloc[0])
        axs[0].text((a + b) / 2, 186, str(c.case), ha="center", va="bottom", color=INK2, fontsize=14)
    axs[-1].set_xlim(0, 130)
    axs[-1].set_xticks([0, 30, 60, 90, 120], ["10:00", "10:30", "11:00", "11:30", "12:00"])
    fig.subplots_adjust(left=0.14, right=0.97, top=0.93, bottom=0.07, hspace=0.28)
    path = os.path.join(tmp, "op.png")
    fig.savefig(path, dpi=dpi, facecolor=SHEET)
    plt.close(fig)
    return Image.open(path).convert("RGB").resize((w, h), Image.LANCZOS)


# ----------------------------------------------------------------- compose
def rounded(img, r):
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, img.width - 1, img.height - 1), r, fill=255)
    return mask


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", help="folder with Barlow Condensed and IBM Plex Mono font files")
    ap.add_argument("--three", help="local path to the 'three' npm package (default: jsDelivr)")
    ap.add_argument("--ship", help="use this 3D render (PNG with transparency) instead of rendering")
    ap.add_argument("--out", default=os.path.join(ROOT, "images", "gunnerus-header.png"))
    a = ap.parse_args()
    tmp = tempfile.mkdtemp()
    panels = [drawings(tmp, CW, IMG_H)]
    if a.ship:
        ship = Image.open(a.ship)
        ship = ship.crop(ship.getbbox())
        s = min((CW - 40) / ship.width, (IMG_H - 30) / ship.height)
        ship = ship.resize((round(ship.width * s), round(ship.height * s)), Image.LANCZOS)
        p = Image.new("RGB", (CW, IMG_H), VIEWER)
        p.paste(ship, ((CW - ship.width) // 2, (IMG_H - ship.height) // 2 + 6), ship)
        panels.append(p)
    else:
        panels.append(model3d(tmp, CW, IMG_H, a.three))
    panels.append(operational(tmp, CW, IMG_H, a.fonts))

    eyebrow = font(a.fonts, "ibm-plex-mono-latin-500-normal.*", 20, "DejaVuSansMono.ttf")
    title = font(a.fonts, "barlow-condensed-latin-600-normal.*", 38, "DejaVuSans-Bold.ttf")
    canvas = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(canvas)
    for i, (img, (eb, tt)) in enumerate(zip(panels, CAPTIONS)):
        x = M + i * (CW + GUT)
        card = Image.new("RGB", (CW, CH), SHEET)
        card.paste(img, (0, 0))
        cd = ImageDraw.Draw(card)
        cd.line((0, IMG_H, CW, IMG_H), fill=RULE, width=2)
        ex = 28
        for ch in eb:                                     # tracked (letter-spaced) eyebrow
            cd.text((ex, IMG_H + 30), ch, font=eyebrow, fill=INK3)
            ex += cd.textlength(ch, font=eyebrow) + 3
        cd.text((28, IMG_H + 62), tt, font=title, fill=INK)
        canvas.paste(card, (x, M), rounded(card, 18))
        d.rounded_rectangle((x, M, x + CW - 1, M + CH - 1), 18, outline=RULE, width=2)
    canvas.save(a.out, optimize=True)
    print(f"{os.path.relpath(a.out, ROOT)}: {canvas.size[0]}x{canvas.size[1]}, {os.path.getsize(a.out)/1e3:.0f} kB")


if __name__ == "__main__":
    main()
