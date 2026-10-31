// Builds virtual/data/gunnerus-outline.json: silhouettes of R/V Gunnerus (from above, from astern, from the side)
// and the approximate positions of the azimuth drives, bow thruster and crane, for the plan view and the motion
// drawings of pages/virtual.html.
//
//   npm install @gltf-transform/core@4 @gltf-transform/extensions@4 meshoptimizer@0.21.0
//   node virtual/scripts/build_outline.mjs derived/3d/gunnerus.glb derived/3d/gunnerus-parts.json virtual/data/gunnerus-outline.json
//
// The model is the C-JOB 3D model, simplified by NTNU (derived/3d/, meshopt-compressed). Each silhouette is the
// envelope of the mesh vertices in slices of 0.25-0.5 m; slices with few vertices are widened to their neighbours.
// Positions are bounding boxes of the model parts, so they are approximate.
// Model axes: x along the ship (m, aft end of hull at about -1.1, bow at 35.3), y up (m), z transverse (port negative).
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { MeshoptDecoder } from 'meshoptimizer';
import fs from 'fs';
await MeshoptDecoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.decoder': MeshoptDecoder});
const doc = await io.read(process.argv[2]);
const parts = JSON.parse(fs.readFileSync(process.argv[3]));
const nodes = doc.getRoot().listNodes().filter(n => n.getMesh());
const pts = {};   // part -> Float32Array xyz
nodes.forEach((n, i) => {
  const W = n.getWorldMatrix(), out = [];
  for (const p of n.getMesh().listPrimitives()) { const a = p.getAttribute('POSITION'), v = [0,0,0];
    for (let k = 0; k < a.getCount(); k++) { a.getElement(k, v);
      out.push(W[0]*v[0]+W[4]*v[1]+W[8]*v[2]+W[12], W[1]*v[0]+W[5]*v[1]+W[9]*v[2]+W[13], W[2]*v[0]+W[6]*v[1]+W[10]*v[2]+W[14]); } }
  pts[parts[i].node] = out;
});
const r2 = x => Math.round(x * 100) / 100;
function envelope(prof, w) {      // widen each slice to the extremes of its neighbours, so sparse slices do not cut notches
  return prof.map((p, i) => { let lo = p[1], hi = p[2];
    for (let j = Math.max(0, i - w); j <= Math.min(prof.length - 1, i + w); j++) { lo = Math.min(lo, prof[j][1]); hi = Math.max(hi, prof[j][2]); }
    return [p[0], r2(lo), r2(hi)]; });
}
function profile(keys, axisA, axisB, step, fnLo, fnHi) {   // bins along axisA: [a, lo(b), hi(b)]
  const bins = new Map();
  for (const k of keys) { const a = pts[k]; for (let i = 0; i < a.length; i += 3) {
    const A = a[i + axisA], B = a[i + axisB], key = Math.round(A / step);
    const c = bins.get(key) || [Infinity, -Infinity]; c[0] = Math.min(c[0], B); c[1] = Math.max(c[1], B); bins.set(key, c); } }
  return [...bins.entries()].sort((p, q) => p[0] - q[0]).map(([k, [lo, hi]]) => [r2(k * step), r2(lo), r2(hi)]);
}
const ALL = parts.map(p => p.node), HULL = ['part00'], SUPER = ['part01'];
const ABOVE = ALL.filter(k => !['part19','part20','part21','part22','part23'].includes(k));  // outside of the hull
const bbox = k => { const a = pts[k]; const mn=[1e9,1e9,1e9], mx=[-1e9,-1e9,-1e9];
  for (let i=0;i<a.length;i+=3) for (let j=0;j<3;j++){ mn[j]=Math.min(mn[j],a[i+j]); mx[j]=Math.max(mx[j],a[i+j]); } return {min:mn.map(r2), max:mx.map(r2)}; };
const out = {
  source: "derived/3d/gunnerus.glb (C-JOB 3D model, simplified by NTNU). Silhouettes from the mesh vertices; positions approximate.",
  axes: "x along the ship from the aft end of the model (m, bow positive), y up (m), z transverse (m, starboard positive)",
  plan_hull: envelope(profile(HULL, 0, 2, 0.5), 1),       // [x, z min, z max]
  plan_super: envelope(profile(SUPER, 0, 2, 0.5), 2),
  side: envelope(profile(ABOVE.concat(['part19','part20']), 0, 1, 0.25), 1),    // [x, y min, y max]
  stern: envelope(profile(ABOVE, 1, 2, 0.4), 1),           // [y, z min, z max]
  stern_hull: envelope(profile(HULL, 1, 2, 0.4), 1),
  items: {
    azimuth_port: bbox('part19'), azimuth_stbd: bbox('part20'), bow_thruster: bbox('part23'),
    crane: bbox('part03'), engines: bbox('part21'), generators: bbox('part22'), mast: bbox('part08')
  }
};
fs.writeFileSync(process.argv[4], JSON.stringify(out));
console.log('points', out.plan_hull.length, out.plan_super.length, out.side.length, out.stern.length, fs.statSync(process.argv[4]).size);
console.log(JSON.stringify(out.items));
console.log('side y range', Math.min(...out.side.map(p=>p[1])), Math.max(...out.side.map(p=>p[2])));
