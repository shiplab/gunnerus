import sys, os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from rimg import IMG, ship2px, px2ship
def window(view,u0,u1,w0,w1,res):
    us=np.arange(u0,u1,res); ws=np.arange(w1,w0,-res)
    U,Wg=np.meshgrid(us,ws); px,py=ship2px(view,U,Wg)
    im=cv2.remap(IMG,px.astype(np.float32),py.astype(np.float32),cv2.INTER_LINEAR,borderValue=255)
    return us,ws,im<170
def col_runs(us,ws,ink):
    out=[]
    for j in range(ink.shape[1]):
        v=np.where(ink[:,j])[0]
        if len(v)==0: out.append(np.array([])); continue
        runs=np.split(v,np.where(np.diff(v)>1)[0]+1)
        out.append(np.array([ws[int(round(r.mean()))] for r in runs]))
    return out
def row_runs(us,ws,ink):
    out=[]
    for i in range(ink.shape[0]):
        v=np.where(ink[i])[0]
        if len(v)==0: out.append(np.array([])); continue
        runs=np.split(v,np.where(np.diff(v)>1)[0]+1)
        out.append(np.array([us[int(round(r.mean()))] for r in runs]))
    return out
def snap_curve(view,guess,res=0.01,win=0.08,step=0.05,pad=0.4):
    """guess: list of (u,w) in ship coords; returns snapped (u,w) every `step` along u"""
    g=np.array(sorted(guess)); u0,u1=g[:,0].min(),g[:,0].max()
    us,ws,ink=window(view,u0-0.05,u1+0.05,g[:,1].min()-pad,g[:,1].max()+pad,res)
    cols=col_runs(us,ws,ink); out=[]
    for u in np.arange(u0,u1+1e-9,step):
        wg=np.interp(u,g[:,0],g[:,1]); j=int(np.argmin(abs(us-u))); c=cols[j]
        if len(c)==0: continue
        k=np.argmin(abs(c-wg))
        if abs(c[k]-wg)<win: out.append((u,c[k]))
    return np.array(out)
def snap_points(view,pts,res=0.005,rad=0.1):
    out=[]
    for u,w in pts:
        us,ws,ink=window(view,u-rad,u+rad,w-rad,w+rad,res)
        yy,xx=np.where(ink)
        if len(yy)==0: out.append((u,w)); continue
        d=np.hypot(us[xx]-u,ws[yy]-w); i=np.argmin(d); out.append((us[xx[i]],ws[yy[i]]))
    return np.array(out)
