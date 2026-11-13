# Hull of R/V Gunnerus from the raster image only (all inputs traced from GA_Gunnerus_Rev1_300dpi.png)
import numpy as np, pickle, os
from scipy.interpolate import PchipInterpolator
D0=os.path.dirname(os.path.abspath(__file__))
L=pickle.load(open(os.path.join(D0,'prof_lines.pkl'),'rb'))
WL=pickle.load(open(os.path.join(D0,'waterlines.pkl'),'rb'))
def clean(c):
    c=np.array(sorted(map(tuple,c))); _,i=np.unique(np.round(c[:,0],3),return_index=True); return c[i]
wlT=clean(WL['WL_T'][1])
wlD=clean(np.vstack([WL['WL_D'][1],[(x,4.8) for x in np.arange(-1.0,21.0,0.5)],[(32.68,0.0)]]))
wlD_f=PchipInterpolator(wlD[:,0],wlD[:,1])
wlA=clean(np.vstack([WL['WL_A'][1]*[1,4.8/WL['WL_A'][1][:5,1].mean()],[(x,4.8) for x in np.arange(12.3,22.9,0.5)]]))
wlA[:,1]=np.minimum(wlA[:,1],4.8)
wlTop=clean(np.vstack([WL['WL_top'][1],[(x,4.8) for x in np.arange(-1.0,12.3,0.5)]]))
def interp(c,x):
    if x<c[0,0] or x>c[-1,0]: return None
    return float(np.interp(x,c[:,0],c[:,1]))
lineA=clean(L['A']); Bfit=np.polyfit(L['B'][:,0],L['B'][:,1],1); B=lambda x: float(np.polyval(Bfit,x))
lineE=clean(np.vstack([L['E'],[(20.0,0.4)]]))
bow=L['bow'][:24]
XA_END=lineA[-1,0]
def zkeel(x):
    if x<=XA_END: return float(np.interp(x,lineA[:,0],lineA[:,1]))
    if x<=bow[1,0]: return B(x)
    lower=bow[:9]
    if x<=lower[-1,0]: return float(np.interp(x,lower[:,0],lower[:,1]))
    return 1.9
prof_poly=np.vstack([[[-1.0,9.0]],lineA,[[x,B(x)] for x in np.arange(XA_END+0.2,31.0,0.5)],bow,[[35.26,7.52],[35.4,9.0]]])
# Fr.17 template, shifted so its CL bottom equals the profile CL bottom at x = 8.5 m
bot,side=pickle.load(open(os.path.join(D0,'sec_raw.pkl'),'rb'))
pos=bot[(bot[:,2]>0.05)]; by,bz=pos[:,0],pos[:,1]
z0=float(np.interp(0.1,by,bz))
tun=(by>0.15)&(by<1.8); k=float(np.polyfit(by[tun],bz[tun]-z0,1)[0])
sy=side[:,1]*-1; sz=side[:,0]   # port-free side (left in image) -> |y|
m=(sz-z0>0.3)&(sz-z0<1.7); bil=np.array(sorted(zip(sz[m]-z0,np.minimum(np.abs(side[m,1]),4.8))))
inner=float(by[(by>1.6)&(by<2.1)][np.argmax(bz[(by>1.6)&(by<2.1)])])   # skeg inner edge = highest point of tunnel roof
outer=float(bil[0,1]); y_bil0=outer; z_bil0=bil[0,0]
def z_rel(y):
    y=np.asarray(y,float)
    return np.where(y<=inner,k*np.minimum(y,inner),k*inner+(z_bil0-k*inner)*(y-inner)/(y_bil0-inner))
def bilge_y(zr): return np.interp(zr,bil[:,0],bil[:,1],left=bil[0,1],right=4.8)
SK=np.array([(y,z-z0) for y,z in zip(by,bz) if inner<=y<=outer])
SHIFT=zkeel(8.5)-z0
ZT_raw=None
ZD,ZA,ZTOP=4.287,6.687,7.52
# height of the tank-top waterline: where its Fr.17 half-breadth meets the Fr.17 bilge
yT17=interp(wlT,8.5); ZT=float(z0+np.interp(yT17,bil[:,1],bil[:,0]))+SHIFT
def section(x):
    zk=zkeel(x)
    bT=interp(wlT,x); bD=float(np.clip(wlD_f(min(x,32.68)),0.25,4.8)) if x<=32.68 else 0.25
    bA=interp(wlA,x) or (4.8 if x<12.3 else 0.25); bTop=interp(wlTop,x) or 0.25
    a=1.0
    if bT is not None and x<26 and zk<ZT and bT<4.75:
        zr=float(z_rel(min(bT,y_bil0-1e-3))) if bT<y_bil0 else float(np.interp(bT,bil[:,1],bil[:,0]))
        a=float(np.clip((ZT-zk)/max(zr,0.2),0.6,1.6))
    ys=np.linspace(0,y_bil0,25); aft=[(y,zk+a*float(z_rel(y))) for y in ys]
    zz=np.linspace(z_bil0,bil[-1,0],20); aft+=[(float(bilge_y(z)),zk+a*z) for z in zz]
    aft=np.array(aft+[(4.8,ZD),(4.8,9.0)])
    pts=[(0.0,zk),(max(0.0,(bT or 0)-1.4)*0.5,zk+0.06)]
    if bT is not None and zk<ZT-0.05: pts.append((bT,ZT))
    if x>31.5:
        lin=(bT if bT is not None else 0.0); lin=lin+(bA-lin)*(ZD-ZT)/(ZA-ZT)
        t=float(np.clip((x-31.5)/1.18,0,1)); bD=(1-t)*(float(wlD_f(min(x,32.68))) if x<=32.68 else 0.0)+t*lin
    pts.append((bD,ZD)); pts+=[(bA,ZA),(bTop,ZTOP),(bTop,9.0)]
    pts=np.array(pts); pts[2:,0]=np.maximum.accumulate(pts[2:,0])
    d=np.r_[0,np.cumsum(np.hypot(*np.diff(pts,axis=0).T))]; keep=np.r_[True,np.diff(d)>1e-6]; pts,d=pts[keep],d[keep]
    t=np.linspace(0,d[-1],80)
    fore=np.c_[PchipInterpolator(d,pts[:,0])(t),PchipInterpolator(d,pts[:,1])(t)]
    w=float(np.clip((x-21.0)/5.0,0,1))
    return aft,fore,w
X_SKEG_AFT=float(L['E'][0,0])
def skeg(x):
    if x<X_SKEG_AFT or x>17.0: return None
    zk=float(np.interp(x,lineE[:,0],lineE[:,1]))
    yc=float(SK[np.argmin(SK[:,1]),0])
    hull_at=zkeel(x)+float(z_rel(yc)); dep=hull_at-zk
    if dep<0.02: return None
    d17=-SK[:,1].min()+float(z_rel(yc)); f=dep/d17; wf=np.sqrt(min(f,1.0))
    pts=[(yc+(y-yc)*wf, hull_at+(zr-float(z_rel(yc)))*f) for y,zr in SK]
    pts=pts+[(pts[-1][0],hull_at+0.3),(pts[0][0],hull_at+0.3)]
    return np.array(pts)
if __name__=='__main__':
    print('deadrise k=%.3f  skeg inner %.2f outer %.2f  bottom rel %.3f  z_T=%.3f  shift %.3f'%(k,inner,outer,SK[:,1].min(),ZT,SHIFT))
    print('B line: z = %.4f x + %.3f'%tuple(Bfit), ' skeg aft end x=%.2f'%X_SKEG_AFT, ' yc=%.2f'%SK[np.argmin(SK[:,1]),0])
