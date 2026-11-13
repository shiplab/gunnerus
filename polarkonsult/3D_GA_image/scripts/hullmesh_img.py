import sys; sys.path.insert(0,'.')
import numpy as np, cv2, trimesh, fast_simplification
from scipy.ndimage import distance_transform_edt as edt
from skimage.measure import marching_cubes
import hull_img as h
BWT_AFT=float(__import__('json').load(open('decks.json'))['bulwark_aft']) if __import__('os').path.exists('decks.json') else 5.11
D=0.025; DX=0.05
Y=np.arange(0,5.1,D); Z=np.arange(-1.0,9.2,D); XS=np.arange(-1.05,35.45,DX)
def rast(poly):
    img=np.zeros((len(Z),len(Y)),np.uint8)
    q=np.c_[(poly[:,0]-Y[0])/D,(poly[:,1]-Z[0])/D]
    cv2.fillPoly(img,[np.round(q*16).astype(np.int32)],1,shift=4); return img.astype(bool)
def sdf(m): return ((edt(~m)-edt(m))*D).astype(np.float32)
def closed(p):  # close a CL->top polyline along CL
    return np.vstack([[[0,p[0,1]]],p,[[0,9.0]]])
# profile carve sdf in (x,z)
PX=XS; pim=np.zeros((len(Z),len(PX)),np.uint8)
q=np.c_[(h.prof_poly[:,0]-PX[0])/DX,(h.prof_poly[:,1]-Z[0])/D]
cv2.fillPoly(pim,[np.round(q*16).astype(np.int32)],1,shift=4); pm=pim.astype(bool)
psdf=(edt(~pm,sampling=(D,DX))-edt(pm,sampling=(D,DX))).astype(np.float32)
ZZ=Z[:,None]+0*Y[None,:]
F=np.empty((len(XS),len(Z),len(Y)),np.float32)
for i,x in enumerate(XS):
    xc=min(max(x,-1.0),35.3)
    a,f,w=h.section(xc)
    s=None
    if w<1: s_a=sdf(rast(closed(a)))
    if w>0: s_f=sdf(rast(closed(f)))
    s=s_a if w==0 else (s_f if w==1 else (1-w)*s_a+w*s_f)
    sk=h.skeg(xc)
    if sk is not None: s=np.minimum(s,sdf(rast(sk)))
    deck=4.115 if x<12.305 else 6.687
    bwt=BWT_AFT if x<12.305 else (7.52 if x>=22.8 else deck)
    hull=np.maximum(s,ZZ-deck)
    band=np.minimum(np.maximum(s,-0.12-s),np.maximum(s,(x+1.0)-0.12))
    bw=np.maximum.reduce([band,ZZ-bwt,(deck-0.04)-ZZ])
    f_=np.minimum(hull,bw)
    if x>30.0: f_=np.maximum(f_,psdf[:,i][:,None])
    F[i]=np.maximum(f_,-1.0-x)
Ff=np.concatenate([F[:,:,::-1][:,:,:-1],F],axis=2); del F
Yf=np.concatenate([-Y[::-1][:-1],Y])
Ff=np.pad(Ff,1,constant_values=1.0)
v,fc,_,_=marching_cubes(Ff,0.0,spacing=(DX,D,D)); del Ff
v-=np.array([DX,D,D])
V=np.c_[XS[0]+v[:,0], Yf[0]+v[:,2], Z[0]+v[:,1]]
m=trimesh.Trimesh(V,fc[:,::-1],process=True)
print('raw',len(m.faces))
vs,fs=fast_simplification.simplify(m.vertices.astype(np.float32),m.faces.astype(np.int64),target_reduction=0.9)
m2=trimesh.Trimesh(vs,fs,process=True); trimesh.repair.fix_normals(m2)
print('dec',len(m2.faces),m2.bounds.round(3).tolist())
m2.export('hull_img.ply')
for T in (2.5,2.787):
    sub=m2.slice_plane([0,0,T],[0,0,-1],cap=True); print(T,'disp t',round(sub.volume*1.025,1))
