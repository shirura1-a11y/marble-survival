"""Deterministic, staged 3D marble race. Free CPU/EGL renderer; no remote API.
Constrained longitudinal dynamics and lateral collision impulses, with seeded
elimination choreography to guarantee the requested 100 -> 3 -> 1 story.
"""
import os
from pathlib import Path
os.environ.setdefault('LIBGL_ALWAYS_SOFTWARE','1')
os.environ.setdefault('MESA_SHADER_CACHE_DIR',str(Path('/tmp/marble-survival-mesa-cache')))
import argparse,json,math,subprocess,time,wave
from pathlib import Path
import numpy as np
import moderngl
P=argparse.ArgumentParser(); P.add_argument('--config',default='config/episode_001.json'); P.add_argument('--output',default='marble_survival_001.mp4'); P.add_argument('--seconds',type=float); P.add_argument('--still',type=float); A=P.parse_args()
cfg=json.load(open(A.config)); W,H,F=cfg['width'],cfg['height'],cfg['fps']; duration=A.seconds or cfg['duration']; rng=np.random.default_rng(cfg['seed'])
ctx=moderngl.create_standalone_context(backend='egl'); ctx.enable(moderngl.DEPTH_TEST); ctx.enable(moderngl.CULL_FACE)
fbo=ctx.simple_framebuffer((W,H)); fbo.use()
VS='''#version 330
in vec3 pos; in vec3 normal; in vec3 offset; in vec3 tint; in float radius;
uniform mat4 vp; out vec3 N; out vec3 world; out vec3 color; out vec3 local;
void main(){world=pos*radius+offset; N=normal; color=tint;local=pos;gl_Position=vp*vec4(world,1.0);}
'''
FS='''#version 330
in vec3 N;in vec3 world;in vec3 color;in vec3 local;uniform vec3 eye;uniform float clock;uniform int glass;out vec4 frag;
void main(){vec3 n=normalize(N);vec3 v=normalize(eye-world);vec3 l=normalize(vec3(-0.6,-0.4,1.0));float nd=max(dot(n,l),0.0);float fr=pow(1.0-max(dot(n,v),0.0),3.0);
vec3 c=color*(0.22+0.72*nd);float spec=pow(max(dot(reflect(-l,n),v),0.0),70.0);
if(glass==1){vec3 r=reflect(-v,n);float stripe=pow(max(0.0,sin(local.x*7.0+local.z*4.0+clock*2.0)),8.0);c=color*(0.16+nd*0.48)+color*stripe*0.32; c+=vec3(0.10,0.30,0.4)*fr;float soft=pow(max(dot(reflect(-normalize(vec3(0.7,0.1,1.0)),n),v),0.0),15.0);c+=vec3(0.40,0.68,0.9)*soft*0.6;c+=vec3(1.0)*spec*1.5; c+=vec3(0.6,0.9,1.0)*pow(max(dot(r,normalize(vec3(-0.4,-0.4,1))),0.0),170.0)*1.6; c=mix(c,vec3(0.3,0.75,0.9),fr*0.55);}else{c+=vec3(0.5)*spec*0.35;}
float fog=1.0-exp(-length(eye-world)*0.002);c=mix(c,vec3(0.025,0.045,0.09),fog);c=pow(c,vec3(0.85));frag=vec4(c,1.0);}
'''
prog=ctx.program(vertex_shader=VS,fragment_shader=FS)
def vao(data):
 b=ctx.buffer(np.asarray(data,'f4').tobytes()); inst=ctx.buffer(reserve=1000*7*4); v=ctx.vertex_array(prog,[(b,'3f 3f','pos','normal'),(inst,'3f 3f 1f /i','offset','tint','radius')]);return v,inst
# Unit sphere CCW triangles.
verts=[]
for i in range(16):
 for j in range(24):
  def pt(a,b):
   th=a*math.pi/16; ph=b*2*math.pi/24; return np.array([math.sin(th)*math.cos(ph),math.sin(th)*math.sin(ph),math.cos(th)])
  a,b,c,d=pt(i,j),pt(i+1,j),pt(i+1,j+1),pt(i,j+1)
  for p in (a,b,c,a,c,d):verts.append([*p,*p])
sv,si=vao(verts)
# Static course batches rebuilt per shot.
def tri_mesh(tris):
 out=[]
 for a,b,c in tris:
  n=np.cross(np.array(b)-a,np.array(c)-a);n=n/(np.linalg.norm(n)+1e-9)
  out.extend([[*a,*n],[*b,*n],[*c,*n]])
 return out

def box(center,size,angle=0):
 x,y,z=center; sx,sy,sz=np.array(size)/2;c,s=math.cos(angle),math.sin(angle)
 pts=[]
 for q in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]:
  a,b,d=np.array(q)*[sx,sy,sz];pts.append(np.array([x+c*a-s*b,y+s*a+c*b,z+d]))
 faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)];tris=[]
 for a,b,c,d in faces:tris.extend([(pts[a],pts[b],pts[c]),(pts[a],pts[c],pts[d])])
 return tri_mesh(tris)
# Mesh bucket by material.
steel=(.09,.16,.22);rail=(.05,.7,.8);gold=(1,.46,.06);pink=(.9,.07,.25)
stage_index=-1; batches=[]
def path(s,kind,lane=0):
 if kind=='spiral':
  spiral=next(x for x in cfg['stages'] if x['kind']=='spiral');theta=s*2*math.pi*spiral['turns']; r=spiral['radius']+lane;return np.array([r*math.cos(theta),r*math.sin(theta),17-17*s])
 length=next(x['length'] for x in cfg['stages'] if x['kind']==kind)
 return np.array([lane, s*length,16-16*s])
def tangent(s,kind):
 d=path(s+.0001,kind)-path(s-.0001,kind);return d/np.linalg.norm(d)
def make_stage(st):
 global batches
 for v,i in batches: v.release();i.release()
 batches=[];mesh={steel:[],rail:[],gold:[],pink:[]};kind=st['kind']
 if kind=='celebration':
  mesh[steel]+=box((0,0,-.7),(9,9,1.4));mesh[gold]+=box((0,0,.05),(6,6,.1))
 else:
  width=st['width']; segs=180 if kind=='spiral' else 120
  for j in range(segs):
   s0=j/segs;s1=(j+1)/segs;mid=(s0+s1)/2
   hole=kind=='hammer' and any(abs(mid*st['length']-p)<1.1 for p in st['pits'])
   if hole:
    # opening broken into edges; true visible void in centre
    spans=[(-width/2,-2.4),(2.4,width/2)]
   else:spans=[(-width/2,width/2)]
   for l,r in spans:
    a,b,c,d=path(s0,kind,l),path(s0,kind,r),path(s1,kind,r),path(s1,kind,l)
    # upward facing track, correct orientation varies with spiral
    if kind=='spiral': ts=[(a,b,c),(a,c,d)]
    else:ts=[(a,b,c),(a,c,d)]
    mesh[steel]+=tri_mesh(ts)
   for side in [-1,1]:
    # open bridge edges permit falls, remaining stages get rails
    if kind=='bridge' and j%12>5:continue
    p=path(mid,kind,side*width/2); ang=math.atan2(*(tangent(mid,kind)[1::-1]))
    length=np.linalg.norm(path(s1,kind)-path(s0,kind))*1.05
    mesh[rail]+=box(p+[0,0,.18],(length,.12,.2),ang)
   if j%12==0:
    p=path(mid,kind);mesh[steel]+=box(p+[0,0,-3],(.5,.5,6))
    if kind!='spiral':mesh[gold]+=box(p+[0,0,.015],(width,.10,.04))
  # Layered industrial ribs and distant ground grid give scale and depth.
  for q in np.arange(0,1,.1):
   p=path(float(q),kind)
   mesh[steel]+=box(p+[0,0,-.38],(width+.35,.32,.65))
  mesh[steel]+=box((0,25,-20),(140,180,.4))
  for q in range(-60,100,8):
   mesh[rail]+=box((q,25,-19.78),(.025,180,.025))
   mesh[rail]+=box((0,q,-19.78),(140,.025,.025))
  # Finish stripes.
  if kind=='final':
   for row in range(4):
    for col in range(10):
     p=path(.94+row*.008,kind,-2.25+col*.5);mesh[gold if (row+col)%2 else rail]+=box(p+[0,0,.02],(.48,.35,.04))
 for color,data in mesh.items():
  if not data:continue
  v,i=vao(data);i.write(np.array([[0,0,0,*color,1]],'f4').tobytes());batches.append((v,i))
# Palette, identity preserved through all stages.
import colorsys
colors=np.array([colorsys.hsv_to_rgb((i*.61803398875)%1,.80,.95) for i in range(cfg['marbles'])])
order=rng.permutation(cfg['marbles']); survivors=[list(range(cfg['marbles']))]+[list(order[:st['survivors']]) for st in cfg['stages'][:4]]
# Small deterministic physical integration on course coordinates, 120Hz.
trajectories=[];events=[]
for k,st in enumerate(cfg['stages'][:4]):
 ids=survivors[k];n=len(ids);end_ids=set(survivors[k+1]);kind=st['kind'];secs=st['end']-st['start'];steps=int(secs*120)+1
 lane=np.array([(j%10-4.5)*1.05 for j in range(n)]) if k==0 else rng.uniform(-st['width']*.32,st['width']*.32,n)
 lane=np.clip(lane,-st['width']/2+.5,st['width']/2-.5);vel=rng.normal(0,.25,n)
 lag=np.array([(j//10)*.009 for j in range(n)]) if k==0 else rng.uniform(0,.10,n)
 drop=np.array([99 if idx in end_ids else rng.uniform(.27,.88) for idx in ids]); side=rng.choice([-1,1],n)
 if kind=='final':
  losing=np.flatnonzero(drop<1)
  for q,j in enumerate(losing):drop[j]=.70+q*.23
 states=np.zeros((steps,n,3),dtype='f4'); dt=1/120
 for step in range(steps):
  t=step*dt;u=t/secs;progress=np.clip(u*1.12-lag,0,1.04)
  # track guide force, wall restitution, sweeper impulses.
  vel+=(-lane*.8-vel*.8+np.sin(t*2+np.arange(n))*1.6)*dt;lane+=vel*dt
  for j in range(n):
   if u<drop[j]:
    edge=st['width']/2-.48
    if abs(lane[j])>edge:lane[j]=np.sign(lane[j])*edge;vel[j]*=-.8
  # Neighbour marble contacts in local longitudinal coordinates.
  dx=lane[:,None]-lane[None,:];dy=(progress[:,None]-progress[None,:])*(110 if kind=='spiral' else st.get('length',68))
  dist=np.sqrt(dx*dx+dy*dy);mask=(dist>0)&(dist<.84)
  impulses=np.where(mask,(.84-dist)*8*np.where(dx>=0,1.,-1.),0.)
  vel+=impulses.sum(axis=1)*dt*25
  for j in range(n):
   p=path(float(progress[j]),kind,float(lane[j]));p[2]+=.44
   if u>drop[j]:
    fall=(u-drop[j])*secs
    edge=st['width']/2+.45
    outward=min(1,fall*4)
    lane_out=lane[j]*(1-outward)+side[j]*edge*outward
    p=path(float(progress[j]),kind,float(lane_out));p[2]+=.44
    p+=np.array([side[j]*max(0,fall-.25)*1.5,fall*.6,-4.9*max(0,fall-.25)**2])
   states[step,j]=p
 trajectories.append((ids,states))
 for j in range(n):
  if drop[j]<1:events.append((st['start']+float(drop[j])*secs,'fall'))
 for h in st.get('hammers',[]): events.append((st['start']+h/st.get('length',68)*secs,'hit'))
print('simulation ready',flush=True)
def look(eye,target):
 f=(target-eye);f/=np.linalg.norm(f);r=np.cross(f,[0,0,1]);r/=np.linalg.norm(r);u=np.cross(r,f);m=np.eye(4);m[:3,:3]=[r,u,-f];m[:3,3]=-m[:3,:3]@eye;return m
aspect=W/H;f=1/math.tan(math.radians(48)/2);proj=np.array([[f/aspect,0,0,0],[0,f,0,0],[0,0,-1.002,-.2002],[0,0,-1,0]])
def draw_instances(v,i,instances,glass):
 if not len(instances):return
 i.write(np.array(instances,'f4').tobytes());prog['glass'].value=glass;v.render(instances=len(instances))
# Dynamic obstacle cube reusable.
cv,ci=vao(box((0,0,0),(1,1,1)))
def render(t):
 global stage_index
 k=next((j for j,st in enumerate(cfg['stages']) if st['start']<=t<st['end']),4);st=cfg['stages'][k];kind=st['kind'];u=(t-st['start'])/(st['end']-st['start'])
 if stage_index!=k:make_stage(st);stage_index=k
 if k<4:
  ids,states=trajectories[k];idx=min(int((t-st['start'])*120),len(states)-1);positions=states[idx]
  live=positions[positions[:,2]>-5]; center=np.median(live,axis=0) if len(live) else path(min(u,1),kind)
  # close following perspective; broad starting view narrows into the chase.
  if kind=='spiral':
   center=path(min(u*1.04,.98),kind); ang=u*2*math.pi*st['turns']+.6; eye=center+np.array([math.cos(ang)*21,math.sin(ang)*21,17]);target=center+[0,0,-1]
  else:
   dist=30 if k==0 and t<3 else 23 if k==0 else 22 if k==2 else 19
   eye=center+np.array([math.sin(t*.23)*5,-dist,dist*.88]);target=center+np.array([0,5,0])
 else:
  center=np.array([0,0,1]);eye=np.array([math.sin(u*1.7)*10,-15*math.cos(u*1.0),10]);target=center
 prog['vp'].write((proj@look(eye,target)).astype('f4').T.tobytes());prog['eye'].value=tuple(eye);prog['clock'].value=t
 fbo.clear(.016,.025,.055,1,depth=1);prog['glass'].value=0
 for v,i in batches:v.render(instances=1)
 # Animated hammers as bars + striking spherical heads, moving transverse to course.
 if k<4:
  for h in st.get('hammers',[]):
   p=path(h/st['length'],kind);ang=t*2.4+h;end=p+np.array([math.cos(ang)*st['width']*.49,math.sin(ang)*1.6,1.0])
   # thin vertical spindle and rounded heads
   draw_instances(sv,si,[[*end,*pink,.90],[*(p+[0,0,.6]),*gold,.45]],0)
   # rotated bar mesh updated (very small geometry)
   mesh=box(p+[0,0,.7],(st['width']*.9,.35,.35),ang);v,i=vao(mesh);draw_instances(v,i,[[0,0,0,*pink,1]],0);v.release();i.release()
  balls=[[*p,*colors[idx],cfg['radius']] for idx,p in zip(ids,positions) if p[2]>-30]
  draw_instances(sv,si,balls,1)
 else:
  draw_instances(sv,si,[[0,0,1.0,*colors[order[0]],.95]],1)
  conf=[]
  for j in range(220):
   age=(t-57+j*.013)%3;ang=j*2.39996;rad=age*3.0;z=1+age*7-age*age*2.6
   conf.append([math.cos(ang)*rad,math.sin(ang)*rad,z,*colors[j%len(colors)],.055+(j%3)*.018])
  draw_instances(cv,ci,conf,0)
 return fbo.read(components=3)
# Entirely synthesized stereo Foley (no music, speech, or licensed assets).
def audio(output,seconds):
 sr=48000;size=int(seconds*sr);aud=np.zeros((size,2),np.float32);arng=np.random.default_rng(cfg['seed']+1)
 def add(t,signal,pan=0):
  p=int(t*sr);n=min(len(signal),size-p)
  if p<0 or n<=0:return
  aud[p:p+n,0]+=signal[:n]*math.sqrt((1-pan)/2);aud[p:p+n,1]+=signal[:n]*math.sqrt((1+pan)/2)
 for t in np.arange(.04,min(seconds,57),.075):
  d=.045;x=np.arange(int(sr*d))/sr;freq=arng.uniform(900,3400);sig=np.sin(2*np.pi*freq*x)*np.exp(-x*110)*arng.uniform(.018,.065);add(t,sig,float(arng.uniform(-.85,.85)))
 for t,kind in events:
  x=np.arange(int(sr*.55))/sr
  if kind=='hit':sig=(np.sin(2*np.pi*170*x)+.45*np.sin(2*np.pi*415*x))*np.exp(-x*13)*.24
  else:sig=arng.normal(0,1,len(x))*np.exp(-x*11)*.045+np.sin(2*np.pi*(850*x-500*x*x))*np.exp(-x*8)*.035
  add(t,sig,float(arng.uniform(-.9,.9)))
 # gate release and victory chime/firework.
 x=np.arange(int(sr*.6))/sr;add(.05,arng.normal(0,1,len(x))*np.exp(-x*20)*.20)
 for j,freq in enumerate([523.25,659.25,783.99,1046.5]):
  x=np.arange(int(sr*2))/sr;add(57+j*.12,(np.sin(2*np.pi*freq*x)+.25*np.sin(2*np.pi*freq*2.01*x))*np.exp(-x*2.4)*.15)
 peak=float(np.max(np.abs(aud)));aud*=.88/max(peak,.88);fade=np.minimum(1,np.arange(size)/480)*np.minimum(1,(size-np.arange(size))/2400);aud*=fade[:,None]
 with wave.open(str(output),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes((aud*32767).astype('<i2').tobytes())
if A.still is not None:
 from PIL import Image
 Image.frombytes('RGB',(W,H),render(A.still)).transpose(Image.Transpose.FLIP_TOP_BOTTOM).save(A.output)
else:
 out=Path(A.output);out.parent.mkdir(parents=True,exist_ok=True);wav=out.with_suffix('.wav');audio(wav,duration)
 cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(F),'-i','-','-i',str(wav),'-vf','vflip','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-t',str(duration),'-movflags','+faststart',str(out)]
 process=subprocess.Popen(cmd,stdin=subprocess.PIPE);begin=time.time()
 for frame in range(round(duration*F)):
  process.stdin.write(render(frame/F))
  if frame%30==0:print(f'{frame}/{round(duration*F)} frames; {time.time()-begin:.1f}s',flush=True)
 process.stdin.close();code=process.wait();wav.unlink();assert code==0
 print('completed',out,flush=True)
