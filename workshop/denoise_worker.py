import os,sys,json,ctypes,time
import numpy as np
import OpenEXR,PyOpenColorIO as OCIO,oidn
from PIL import Image
ROOT=os.path.dirname(os.path.abspath(__file__))
cfg=OCIO.Config.CreateFromFile('/usr/share/blender/datafiles/colormanagement/config.ocio')
cfg.addDisplayView('sRGB','Film','AgX Base sRGB','AgX - Medium High Contrast')
t=OCIO.DisplayViewTransform(src='Linear Rec.709',display='sRGB',view='Film')
look=OCIO.LookTransform(src='Linear Rec.709',dst='Linear Rec.709',looks='AgX - Medium High Contrast')
# AgX's look is a view look; use a legacy DisplayTransform with looks override via a named view if possible.
# Blender applies the AgX contrast look between the AgX log encoding and output transform.
# Construct the exact configured display pipeline with the requested look using a temporary view.
view=cfg.getView('sRGB','AgX') if hasattr(cfg,'getView') else None
cpu=cfg.getProcessor(t).getDefaultCPUProcessor()
dev=oidn.NewDevice();oidn.CommitDevice(dev)
lib=ctypes.CDLL(os.path.dirname(oidn.__file__)+'/lib.linux.x64/libOpenImageDenoise.so.1.4.3')
setb=lib.oidnSetFilter1b;setb.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_bool];setb.restype=None
for line in sys.stdin:
 try:
  frame=int(line.strip());data={}
  for name in ['color','albedo','normal']:
   path='/tmp/workshop-passes/'+name+('%04d'%frame)+'.exr'
   f=OpenEXR.File(path);ch=f.channels();a=(ch.get('RGBA',ch.get('RGB')).pixels if ('RGBA' in ch or 'RGB' in ch) else np.stack([ch[k].pixels for k in ['X','Y','Z']],axis=2));data[name]=np.ascontiguousarray(a[:,:,:3],dtype=np.float32)
  H,W,_=data['color'].shape;out=np.empty_like(data['color']);flt=oidn.NewFilter(dev,'RT')
  for name in data:oidn.SetSharedFilterImage(flt,name,data[name],oidn.FORMAT_FLOAT3,W,H)
  oidn.SetSharedFilterImage(flt,'output',out,oidn.FORMAT_FLOAT3,W,H);setb(flt,b'hdr',True);oidn.CommitFilter(flt);oidn.ExecuteFilter(flt);err=oidn.GetDeviceError(dev)
  if err:raise RuntimeError('OIDN error '+str(err))
  oidn.ReleaseFilter(flt);out*=2**.4;cpu.applyRGB(out)
  Image.fromarray((np.clip(out,0,1)*255+.5).astype(np.uint8)).save(ROOT+'/frames/%04d.png'%frame,compress_level=2)
  for name in data:os.unlink('/tmp/workshop-passes/'+name+('%04d'%frame)+'.exr')
  print(json.dumps({'frame':frame,'ok':True}),flush=True)
 except Exception as e:
  print(json.dumps({'ok':False,'error':repr(e)}),flush=True)
oidn.ReleaseDevice(dev)
