# Superstructure & equipment of R/V Gunnerus, all dimensions measured on GA_Gunnerus_Rev1_300dpi.png (ship coords, metres)
import numpy as np, trimesh, pickle
from shapely.geometry import Polygon
def ext_xz(poly,y0,y1):
    m=trimesh.creation.extrude_polygon(Polygon(poly),height=y1-y0)
    m.apply_transform(np.array([[1,0,0,0],[0,0,1,y0],[0,1,0,0],[0,0,0,1]],float))
    if m.volume<0: m.invert()
    return m
def ext_xy(poly,z0,z1):
    m=trimesh.creation.extrude_polygon(Polygon(poly),height=z1-z0); m.apply_translation([0,0,z0]); return m
inter=lambda a,b: trimesh.boolean.intersection([a,b],engine='manifold')
def box(x0,x1,y0,y1,z0,z1):
    b=trimesh.creation.box(extents=[abs(x1-x0),abs(y1-y0),abs(z1-z0)]); b.apply_translation([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2]); return b
cyl=lambda p0,p1,r,sec=24: trimesh.creation.cylinder(radius=r,segment=[p0,p1],sections=sec)
def beam(p0,p1,w,h):
    p0=np.array(p0,float); p1=np.array(p1,float); d=p1-p0; L=np.linalg.norm(d)
    b=trimesh.creation.box(extents=[L,w,h])
    yaw=np.arctan2(d[1],d[0]); pitch=np.arctan2(d[2],np.hypot(d[0],d[1]))
    b.apply_transform(trimesh.transformations.rotation_matrix(-pitch,[0,1,0]))
    b.apply_transform(trimesh.transformations.rotation_matrix(yaw,[0,0,1]))
    b.apply_translation((p0+p1)/2); return b
parts={}
def add(n,m,mat): parts.setdefault(n,[]).append((m,mat))
# A-deck house: profile (outboard profile) x plan (A-deck plan)
ad_plan=[(14.5,3.42),(14.6,3.505),(25.72,3.505),(26.71,3.35),(26.71,-3.345),(25.72,-3.495),(14.5,-3.495)]
ad_prof=[(14.5,6.6),(26.71,6.6),(26.71,7.71),(25.44,8.76),(24.96,9.05),(24.56,9.085),(14.5,9.085)]
add('A-deck house',inter(ext_xy(ad_plan,6.5,9.2),ext_xz(ad_prof,-4,4)),'white')
# wheelhouse plan (wheelhouse plan view)
wh=[(13.415,-2.63),(13.415,2.66),(14.5,2.66),(14.5,3.0),(15.0,3.5),(20.27,3.505),(21.22,1.75),(21.22,-1.75),(20.27,-3.495),(15.0,-3.495),(14.5,-3.0),(14.5,-2.63)]
mid_prof=[(14.5,8.95),(21.32,8.95),(21.0,9.5),(20.8,9.5),(20.32,10.15),(14.5,10.15)]
add('Bridge deck house',inter(ext_xy(wh,8.9,10.2),ext_xz(mid_prof,-4,4)),'white')
wh_prof=[(14.5,10.15),(20.32,10.15),(21.16,11.39),(13.72,11.39)]
add('Wheelhouse',inter(ext_xy(wh,10.1,11.45),ext_xz(wh_prof,-4,4)),'white')
win=inter(ext_xy([(x,y*1.012) for x,y in wh],10.4,11.2),ext_xz([(13.85,10.4),(20.5,10.4),(21.05,11.2),(13.3,11.2)],-4,4))
add('Wheelhouse windows',win,'glass')
roof=inter(ext_xy([(x+(0.2 if x>17 else -0.2),y*1.06) for x,y in wh],11.39,11.665),ext_xz([(13.65,11.3),(21.6,11.3),(21.6,11.7),(13.65,11.7)],-4,4))
add('Wheelhouse',roof,'white')
# mast housing, mast, yards, radar, poles (profile + Section Fr.17)
add('Mast',ext_xz([(16.95,11.6),(18.2,12.4),(18.4,12.65),(20.5,12.65),(20.5,12.5),(19.4,12.3),(19.6,11.6)],-0.4,0.4),'white')
mast=trimesh.Trimesh(vertices=[[18.2,-0.4,12.6],[18.85,-0.4,12.6],[18.85,0.4,12.6],[18.2,0.4,12.6],[18.45,-0.03,17.0],[18.55,-0.03,17.0],[18.55,0.03,17.0],[18.45,0.03,17.0]],
  faces=[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]]); mast.fix_normals(); add('Mast',mast,'white')
add('Mast',cyl([18.5,0,17.0],[18.5,0,17.4],0.06,12),'grey')
for z,hw in [(16.25,1.0),(14.4,0.75)]: add('Mast',box(18.46,18.54,-hw,hw,z-0.04,z+0.04),'grey')
add('Mast',cyl([20.1,0,12.8],[20.1,0,13.25],0.18),'grey'); add('Mast',box(19.12,21.2,-0.15,0.15,13.25,13.4),'grey')
add('Mast',cyl([14.05,-2.25,11.6],[14.05,-2.25,14.15],0.06,12),'grey')
add('Mast',cyl([16.7,0.0,11.6],[16.7,0.0,15.6],0.04,12),'grey')
# funnel (wheelhouse plan + Section Fr.17), port side
add('Funnel',box(15.5,17.2,2.52,3.43,9.0,12.45),'white')
for xp in (15.93,16.46,16.9): add('Funnel',cyl([xp,3.05,12.45],[xp,3.05,13.0],0.14,16),'black')
# liferafts on A-deck house roof
for ys in (3.93,-3.93): add('Liferafts',cyl([15.9,ys,9.36],[17.25,ys,9.36],0.36,20),'white')
# forecastle: rescue boat (athwartships), crane, windlass
boat=trimesh.creation.capsule(height=2.6,radius=0.95,count=[16,16]); boat.apply_scale([1.0,1.0,0.62])
boat.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[1,0,0])); boat.apply_translation([30.5,-0.15,8.0])
add('Rescue boat',boat,'orange')
add('Forecastle crane',cyl([28.14,2.68,6.687],[28.14,2.68,8.3],0.28),'yellow')
add('Forecastle crane',beam([28.14,2.68,8.3],[30.45,0.0,10.0],0.25,0.3),'yellow')
add('Windlass',box(27.9,29.0,-1.0,1.0,6.687,7.4),'grey')
# aft deck: hangar, knuckle crane, RIB, A-frame, A-deck crane with stowed boom, winches
add('Hangar',box(8.25,12.295,-2.77,3.23,4.115,6.985),'white')
add('Aft crane',cyl([5.7,-2.75,4.115],[5.7,-2.75,5.6],0.45),'yellow')
add('Aft crane',beam([3.9,-2.75,5.24],[6.62,-2.75,7.44],0.5,0.55),'yellow')
rib=trimesh.creation.capsule(height=4.0,radius=0.75,count=[16,16]); rib.apply_scale([1,1.0,0.6])
rib.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,1,0])); rib.apply_translation([4.95,2.85,4.115+0.75])
add('Work boat',rib,'orange')
for ys in (3.1,-3.1): add('A-frame',beam([-0.82,ys,4.115],[-1.62,ys,10.3],0.28,0.3),'yellow')
add('A-frame',box(-1.85,-1.4,-3.3,3.3,9.9,10.3),'yellow')
add('A-deck crane',cyl([14.05,3.9,6.687],[14.05,3.9,8.0],0.3),'yellow')
add('A-deck crane',beam([13.9,3.9,9.45],[6.85,3.9,9.45],0.3,0.32),'yellow')
add('A-deck crane',beam([14.05,3.9,8.0],[13.6,3.9,9.45],0.35,0.35),'yellow')
for ys in (2.5,-2.6): add('Winches',box(12.36,13.4,ys-0.5,ys+0.5,6.687,7.5),'grey')
# ducted azimuth thrusters (inboard profile + view from aft)
for ys in (2.70,-2.70):
    duct=trimesh.creation.annulus(r_min=0.947,r_max=1.228,height=1.5,sections=40)
    duct.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2,[0,1,0])); duct.apply_translation([-0.15,ys,0.556]); add('Thrusters',duct,'steel')
    pod=trimesh.creation.icosphere(subdivisions=3,radius=1.0); pod.apply_scale([0.7,0.3,0.3]); pod.apply_translation([-0.1,ys,0.556]); add('Thrusters',pod,'steel')
    add('Thrusters',box(-0.5,0.6,ys-0.25,ys+0.25,1.6,2.1),'steel')
    add('Thrusters',box(-0.25,0.05,ys-0.08,ys+0.08,0.55,1.7),'steel')
    for k in range(4):
        bl=box(-0.05,0.05,-0.12,0.12,0.0,0.92); a=k*np.pi/2+0.4
        bl.apply_transform(trimesh.transformations.rotation_matrix(a,[1,0,0])); bl.apply_translation([-0.75,ys,0.556]); add('Thrusters',bl,'bronze')
# open railing on forecastle side between deck step and solid bulwark
for ys in (4.72,-4.72):
    add('Railings',cyl([12.3,ys,7.7],[23.0,ys,7.7],0.03,8),'grey'); add('Railings',cyl([12.3,ys,7.3],[23.0,ys,7.3],0.02,8),'grey')
    for xs in np.arange(12.5,23.0,1.0): add('Railings',cyl([xs,ys,6.687],[xs,ys,7.7],0.025,8),'grey')
for xg in (19.25,20.75,22.25,23.75,25.25,26.75):
    for ys in (4.80,-4.80): add('Portholes',cyl([xg,ys*0.995,5.75],[xg,ys*1.006,5.75],0.17,20),'glass')
for xa,xb in [(20.1,21.02),(21.92,22.84),(23.7,24.62)]:
    for ys in (1,-1): add('Windows',box(xa,xb,min(ys*3.45,ys*3.55),max(ys*3.45,ys*3.55),7.76,8.4),'glass')
pickle.dump(parts,open('parts_img.pkl','wb'))
print({k:len(v) for k,v in parts.items()})
