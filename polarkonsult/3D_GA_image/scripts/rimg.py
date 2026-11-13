# Image-only toolkit: everything is measured from GA_Gunnerus_Rev1_300dpi.png
import cv2, numpy as np, json, os
IMG=cv2.imread(os.path.join(os.path.dirname(os.path.abspath(__file__)),'GA_Gunnerus_Rev1_300dpi.png'),0)
INK=IMG<160
H,W=IMG.shape
def show_px(x0,y0,x1,y1,out,grid=500,maxw=2000):
    c=cv2.cvtColor(IMG[y0:y1,x0:x1],cv2.COLOR_GRAY2BGR)
    f=min(1.0,maxw/(x1-x0)); c=cv2.resize(c,None,fx=f,fy=f,interpolation=cv2.INTER_AREA)
    for g in range((x0//grid+1)*grid,x1,grid):
        u=int((g-x0)*f); cv2.line(c,(u,0),(u,c.shape[0]),(0,0,255),1); cv2.putText(c,str(g),(u+2,14),0,0.45,(0,0,255),1)
    for g in range((y0//grid+1)*grid,y1,grid):
        v=int((g-y0)*f); cv2.line(c,(0,v),(c.shape[1],v),(255,0,0),1); cv2.putText(c,str(g),(2,v-2),0,0.45,(255,0,0),1)
    cv2.imwrite(out,c)
# ---------- calibration (filled in by calib.json once measured) ----------
CAL=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'calib.json'))) if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)),'calib.json')) else None
def px2ship(view,px,py):
    c=CAL; m=c['m_per_px']; v=c['views'][view]
    x=(np.asarray(px)-v.get('px0',c['px0']))*m*v.get('sx',1)+v.get('x0',0.0)
    w=(v['py0']-np.asarray(py))*m
    return x,w
def ship2px(view,x,w):
    c=CAL; m=c['m_per_px']; v=c['views'][view]
    px=(np.asarray(x)-v.get('x0',0.0))/(m*v.get('sx',1))+v.get('px0',c['px0'])
    py=v['py0']-np.asarray(w)/m
    return px,py
def show_ship(view,u0,u1,w0,w1,res,out,grid=0.25,label=1.0):
    """resample image into ship-coordinate window (u horizontal, w vertical) with metre grid"""
    us=np.arange(u0,u1,res); ws=np.arange(w1,w0,-res)
    U,Wg=np.meshgrid(us,ws)
    px,py=ship2px(view,U,Wg)
    img=cv2.remap(IMG,px.astype(np.float32),py.astype(np.float32),cv2.INTER_AREA if False else cv2.INTER_LINEAR,borderValue=255)
    c=cv2.cvtColor(img,cv2.COLOR_GRAY2BGR)
    for g in np.arange(np.ceil(u0/grid)*grid,u1,grid):
        major=abs(g/label-round(g/label))<1e-6; p=int((g-u0)/res)
        cv2.line(c,(p,0),(p,c.shape[0]),(0,0,255) if major else (205,205,255),1)
        if major: cv2.putText(c,'%g'%g,(p+2,14),0,0.45,(0,0,255),1)
    for g in np.arange(np.ceil(w0/grid)*grid,w1,grid):
        major=abs(g/label-round(g/label))<1e-6; p=int((w1-g)/res)
        cv2.line(c,(0,p),(c.shape[1],p),(255,0,0) if major else (255,215,215),1)
        if major: cv2.putText(c,'%g'%g,(2,p-2),0,0.45,(255,0,0),1)
    cv2.imwrite(out,c)
