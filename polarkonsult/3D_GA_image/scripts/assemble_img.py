import numpy as np, trimesh, pickle, fast_simplification, os
parts=pickle.load(open('parts_img.pkl','rb'))
hull=trimesh.load('hull_img.ply')
vs,fs=fast_simplification.simplify(hull.vertices.astype(np.float32),hull.faces.astype(np.int64),target_reduction=0.8)
hull=trimesh.Trimesh(vs,fs,process=True); trimesh.repair.fix_normals(hull)

print('hull faces',len(hull.faces))
MAT={'navy':[24,43,74],'red':[150,40,35],'deck':[150,150,145],'white':[236,236,232],'glass':[30,40,52],'grey':[120,124,128],
     'black':[30,30,30],'orange':[232,110,30],'yellow':[235,180,40],'bronze':[180,140,70],'steel':[70,78,88]}
# split hull: bottom below design WL 2.5 m, deck faces (up-facing, above 4.2 m), topsides
bot_m=hull.slice_plane([0,0,2.5],[0,0,-1],cap=False)
up_m=hull.slice_plane([0,0,2.5],[0,0,1],cap=False)
c=up_m.triangles_center; n=up_m.face_normals
deckf=(n[:,2]>0.85)&(c[:,2]>4.0)
meshes={'Hull bottom':(bot_m,'red'),'Hull topside':(up_m.submesh([np.where(~deckf)[0]],append=True),'navy'),'Decks':(up_m.submesh([np.where(deckf)[0]],append=True),'deck')}
scene=trimesh.Scene(); objparts=[]
def mat(name):
    r,g,b=MAT[name]
    return trimesh.visual.material.PBRMaterial(name=name,baseColorFactor=[r/255,g/255,b/255,1.0],metallicFactor=0.0 if name!='glass' else 0.3,roughnessFactor=0.7 if name!='glass' else 0.2)
for gname,(sub,mn) in meshes.items():
    sub.visual=trimesh.visual.TextureVisuals(material=mat(mn))
    scene.add_geometry(sub,node_name=gname,geom_name=gname); objparts.append((gname,sub,mn))
for name,L in parts.items():
    bymat={}
    for m,mn in L: bymat.setdefault(mn,[]).append(m)
    for mn,ms in bymat.items():
        mm=trimesh.util.concatenate(ms); mm.visual=trimesh.visual.TextureVisuals(material=mat(mn))
        nm=f'{name} ({mn})' if len(bymat)>1 else name
        scene.add_geometry(mm,node_name=nm,geom_name=nm); objparts.append((nm,mm,mn))
os.makedirs('out_img',exist_ok=True)
# ship coords Z-up (metres, x fwd from AP/frame 0, y port, z above BL)
# OBJ with MTL
with open('out_img/Gunnerus_GA_image.mtl','w') as f:
    for k,(r,g,b) in MAT.items(): f.write(f'newmtl {k}\nKd {r/255:.3f} {g/255:.3f} {b/255:.3f}\nKa 0 0 0\nKs 0.1 0.1 0.1\nd 1.0\n\n')
with open('out_img/Gunnerus_GA_image.obj','w') as f:
    f.write('# RV Gunnerus 3D model reconstructed from a 300 dpi image of the GA Gunnerus Rev1 sheet only (polarkonsult/NTNU, CC BY-NC 4.0)\n# units: metres; x forward from AP (frame 0), y to port, z up from baseline\nmtllib Gunnerus_GA_image.mtl\n')
    off=1
    for nm,m,mn in objparts:
        f.write(f'o {nm.replace(" ","_")}\nusemtl {mn}\n')
        for v in m.vertices: f.write(f'v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n')
        for fc in m.faces+off: f.write(f'f {fc[0]} {fc[1]} {fc[2]}\n')
        off+=len(m.vertices)
allm=trimesh.util.concatenate([m for _,m,_ in objparts]); allm.export('out_img/Gunnerus_GA_image.stl')
# GLB in Y-up: (x, z, -y)
T=np.array([[1,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1]],float)
scene.apply_transform(T)
scene.export('out_img/Gunnerus_GA_image.glb')
hull_only=hull.copy(); hull_only.export('out_img/Gunnerus_GA_image_hull.stl')
for f in sorted(os.listdir('out_img')): print(f, round(os.path.getsize('out_img/'+f)/1e6,2),'MB')
print('bounds',allm.bounds)
