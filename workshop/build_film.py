import bpy, math, random, os, sys, time, json
from mathutils import Vector,Euler
from mathutils.bvhtree import BVHTree
from math import sin, cos, pi
random.seed(41)
ROOT=os.path.dirname(os.path.abspath(__file__))
os.makedirs(ROOT+'/frames',exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
S=bpy.context.scene
S.render.engine='CYCLES'; S.cycles.samples=16; S.cycles.use_denoising=False
S.cycles.max_bounces=6; S.cycles.diffuse_bounces=3; S.cycles.glossy_bounces=3; S.cycles.transmission_bounces=6
S.cycles.transparent_max_bounces=6
S.render.resolution_x=540; S.render.resolution_y=960; S.render.resolution_percentage=100
S.render.fps=24; S.frame_start=1; S.frame_end=1680
S.render.image_settings.file_format='PNG'; S.render.image_settings.color_mode='RGB'; S.render.image_settings.compression=15
S.render.threads_mode='FIXED'; S.render.threads=5
S.view_settings.view_transform='AgX'; S.view_settings.look='AgX - Medium High Contrast'; S.view_settings.exposure=.4
S.world.color=(.18,.18,.18)
S.world.use_nodes=True; S.world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.75,.9,1); S.world.node_tree.nodes['Background'].inputs[1].default_value=.28

def mat(name,color,rough=.45,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 return m

def timber(name,c1,c2):
 m=mat(name,c1,.43); n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
 tex=n.new('ShaderNodeTexCoord'); mp=n.new('ShaderNodeVectorMath');mp.operation='MULTIPLY';mp.inputs[1].default_value=(1.2,48,55);l.new(tex.outputs['Generated'],mp.inputs[0])
 noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=3;noise.inputs['Detail'].default_value=3;noise.inputs['Roughness'].default_value=.72;l.new(mp.outputs[0],noise.inputs[0])
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.18;ramp.color_ramp.elements[0].color=(*c1,1);ramp.color_ramp.elements[1].position=.82;ramp.color_ramp.elements[1].color=(*c2,1);l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.025;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
 return m
wood=timber('honey oak / long open grain',(.21,.10,.038),(.57,.34,.14))
pale=timber('unfinished maple',(.48,.30,.14),(.78,.59,.34))
dark=timber('walnut end grain',(.07,.028,.012),(.25,.12,.045))
table=timber('old workbench / satin worn timber',(.19,.105,.055),(.40,.26,.13))
red=mat('faded brick paint',(.43,.085,.052),.73)
blue=mat('faded teal paint',(.075,.26,.28),.65)
cream=mat('warm folded drawing paper',(.80,.74,.59),.85)
metal=mat('brushed brass',(.49,.32,.11),.3,.78)
steel=mat('satin steel',(.47,.50,.49),.26,.85)
cordmat=mat('natural flax twine',(.40,.31,.17),.95)
black=mat('graphite',(.018,.022,.021),.8)
wall=mat('chalk plaster',(.64,.60,.48),.95)
glass=mat('clear soda glass',(.86,.97,.96),.075)
p=glass.node_tree.nodes.get('Principled BSDF');p.inputs['Transmission Weight'].default_value=1;p.inputs['IOR'].default_value=1.48
core=mat('marble teal ribbon',(.015,.25,.26),.18);core.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value=.2
amber=mat('marble honey ribbon',(.65,.23,.026),.18)

def cube(name,loc,scale,ma,bevel=.035):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if ma:o.data.materials.append(ma)
 if bevel:
  b=o.modifiers.new('hand sanded corners','BEVEL');b.width=bevel;b.segments=3
  o.modifiers.new('weighted face normals','WEIGHTED_NORMAL')
 return o

def cyl(name,loc,r,depth,ma,rot=(0,0,0)):
 bpy.ops.mesh.primitive_cylinder_add(vertices=40,radius=r,depth=depth,location=loc,rotation=rot);o=bpy.context.object;o.name=name;o.data.materials.append(ma)
 b=o.modifiers.new('soft machined edge','BEVEL');b.width=.018;b.segments=2;o.modifiers.new('weighted normals','WEIGHTED_NORMAL');return o

def sphere(name,loc,r,ma):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,radius=r,location=loc);o=bpy.context.object;o.name=name;o.data.materials.append(ma)
 for f in o.data.polygons:f.use_smooth=True
 return o

def curve(name,pts,r,ma):
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.resolution_u=2;d.bevel_depth=r;d.bevel_resolution=3
 s=d.splines.new('POLY');s.points.add(len(pts)-1)
 for q,p in zip(s.points,pts):q.co=(*p,1)
 o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.data.materials.append(ma);return o

def beam(name,a,b,width,thick,ma):
 a,b=Vector(a),Vector(b);o=cube(name,(a+b)/2,((b-a).length,width,thick),ma,.025);o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('X','Z');return o

def rail(name,pts,width=.54):
 # two rounded wooden rods support the marble in a real open groove
 for side in [-1,1]:curve(name+' maple rail',[(x,y+side*.13,z-.22) for x,y,z in pts],.075,pale)
 # cross ties, underside and trestles
 for i in range(0,len(pts),max(1,len(pts)//8)):
  x,y,z=pts[i];cube(name+' joint',(x,y,z-.355),(.20,width,.12),wood,.02)
 for i in [0,len(pts)//2,len(pts)-1]:
  x,y,z=pts[i];h=z-.42
  if h>.1:
   cube(name+' upright',(x,y+.44,h/2),(.20,.20,h),pale,.025);cube(name+' foot',(x,y+.44,.10),(.65,.6,.2),wood,.03)
   cyl('dark screw head',(x,y+.44,h-.05),.038,.015,steel)

def tween(o,attr,values):
 for t,v in values:
  setattr(o,attr,v);o.keyframe_insert(data_path=attr,frame=round(t*24)+1)
 if o.animation_data:
  for fc in o.animation_data.action.fcurves:
   for k in fc.keyframe_points:k.interpolation='BEZIER';k.handle_left_type='AUTO_CLAMPED';k.handle_right_type='AUTO_CLAMPED'

# A real tabletop built from individual boards, with visible seams and tiny surface marks.
for j in range(14):cube('workbench plank',(12,(j-6.5)*1.05,-.20),(36,1.035,.4),table,.025)
for j in range(50):
 x=random.uniform(-3,28);y=random.uniform(-5.5,6);curve('hairline bench scratch',[(x,y,.008),(x+random.uniform(.03,.22),y+.012,.008)],.0015,dark)
cube('rear plaster wall',(12,8.6,5),(40,.2,11),wall,.02)
# Large offscreen window, soft morning light and broad rectangular reflection in glass.
def area(name,loc,power,color,size,target):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.color=color;d.shape='RECTANGLE';d.size=size;d.size_y=size*.70;o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('north window / warm soft daylight',(8,-4,12),2600,(1,.89,.72),5,(10,0,1))
area('white card fill',(15,5,8),850,(.79,.87,1),8,(14,0,2))
area('long window highlight',(23,-2,9),1800,(1,.91,.76),6,(22,0,1))
# Quiet workshop dressing stays beyond the focus plane.
for x in [1,9,17,25]:
 cube('paper offcut',(x,4,.018),(1.7,1.15,.025),cream,.01).rotation_euler.z=.15
 for k in range(3):cyl('spare wooden dowel',(x+.15*k,4.8,.15),.065,1.8,pale,(0,pi/2,.13*k))
 for k in range(2):cube('spare domino',(x+k*.3,3.7,.12),(.22,.55,.22),pale,.025)
for x in [4,14,23]:
 o=cyl('carpenter pencil',(x,3.1,.08),.055,1.4,red,(0,pi/2,.3));cyl('graphite point',(x-.73,2.87,.08),.025,.15,black,(0,pi/2,.3))
# Marble shell and colored glass ribbons rotate together.
marble=bpy.data.objects.new('hero marble / rolling assembly',None);bpy.context.collection.objects.link(marble)
sphere('glass outer shell',(0,0,0),.18,glass).parent=marble
for j,ma in enumerate([core,amber,core]):
 pts=[]
 for k in range(51):
  u=k/50;z=(u-.5)*.29;r=.10*math.sqrt(max(0,1-(z/.16)**2));a=u*pi*1.6+j*2*pi/3;pts.append((r*cos(a),r*sin(a),z))
 curve('twisted internal glass ribbon',pts,.031,ma).parent=marble
# Opening: a domino knocks the support from a miniature balance beam.
startz=4.9
cyl('opening fulcrum',(-.15,0,4.52),.18,.7,dark,(pi/2,0,0))
cube('opening fulcrum stand',(-.15,.3,2.20),(.25,.3,4.4),wood)
tip=cube('opening tipper',(-.15,0,4.76),(1.15,.55,.12),pale)
tween(tip,'rotation_euler',[(0,(0,-.12,0)),(.45,(0,-.12,0)),(1.1,(0,.22,0)),(3,(0,.22,0))])
lever=cube('opening domino',(-.80,.1,4.99),(.15,.4,.65),red)
tween(lever,'rotation_euler',[(0,(0,0,0)),(.25,(0,.12,0)),(.65,(0,1.15,0))])
rail('first flowing slope',[(.1+i*.12,.24*sin(i*.12),4.84-i*.019) for i in range(56)])
# The marble parks on a latched seesaw while a domino chain carries the action around it.
seepivot=(8,0,3.75)
cyl('seesaw axle',seepivot,.11,1.0,steel,(pi/2,0,0))
for yy in [-.42,.42]:
 cube('seesaw A-frame foot',(8,yy,.12),(1.2,.27,.24),dark)
 beam('seesaw diagonal',(7.55,yy,.24),(8,yy,3.75),.2,.2,pale);beam('seesaw diagonal',(8.45,yy,.24),(8,yy,3.75),.2,.2,pale)
seesaw=bpy.data.objects.new('balanced seesaw pivot',None);bpy.context.collection.objects.link(seesaw);seesaw.location=seepivot
for yy in [-.13,.13]:
 o=cube('seesaw rail',(0,yy,0),(3.3,.15,.15),pale);o.parent=seesaw
for xx in [-1.5,0,1.5]:
 o=cube('seesaw cross piece',(xx,0,-.12),(.16,.55,.12),wood);o.parent=seesaw
weight=cube('seesaw counterweight',(1.25,0,-.34),(.45,.58,.45),dark);weight.parent=seesaw
stop=cube('seesaw end stop',(-1.55,0,.17),(.12,.5,.35),dark);stop.parent=seesaw
# Initial uphill tilt retains marble; released after the domino pulse.
tween(seesaw,'rotation_euler',[(0,(0,-.18,0)),(19,(0,-.18,0)),(21,(0,.48,0)),(25,(0,.48,0))])
dominos=[];domino_times=[]
for i in range(25):
 u=i/24;x=6.9+2.1*u;y=-.85-1.1*sin(u*pi);z=3.28
 base=bpy.data.objects.new('domino hinge %02d'%i,None);bpy.context.collection.objects.link(base);base.location=(x,y,z);yaw=math.atan2(-1.1*pi*cos(u*pi),2.1);base.rotation_euler.z=yaw
 o=cube('maple domino %02d'%i,(0,0,.33),(.045,.28,.66),[pale,pale,red,pale,blue][i%5],.022);o.parent=base
 # fall in path direction
 t=12.5+i*.255;domino_times.append(t)
 ds=math.sqrt((2.1/24)**2+(1.1*pi*cos(u*pi)/24)**2);contact=math.asin(max(.01,ds-.045)/.66)
 tween(base,'rotation_euler',[(0,(0,0,yaw)),(t,(0,0,yaw)),(t+.255,(0,contact,yaw)),(t+.75,(0,1.37,yaw))])
 dominos.append(base)
beam('domino curved run base',(6.65,-1.35,3.19),(9.25,-1.35,3.19),2.35,.17,wood)
for xx in [6.8,9.1]:cube('domino platform support',(xx,-1.4,1.55),(.25,.25,3.1),pale)
# A small striker transfers the marble impulse to the first domino.
striker=cube('domino initiating paddle',(6.9,-.46,3.9),(.18,.75,.4),dark)
tween(striker,'rotation_euler',[(0,(0,0,0)),(12.1,(0,0,0)),(12.6,(.45,0,0))])
# Last domino tugs the wooden catch, unbalancing the seesaw.
catch=cube('sliding seesaw catch',(8.8,.40,3.85),(.20,.8,.18),red)
tween(catch,'location',[(0,(8.8,.40,3.85)),(18.8,(8.8,.40,3.85)),(19.4,(8.8,1.1,3.85))])
curve('catch pull cord',[(9,-.8,3.3),(9.3,-.4,3.4),(8.8,.6,3.35)],.012,cordmat)
# A lower rail delivers marble to a small hinged brass cup suspended on a pulley.
rail('seesaw exit',[(9.5+i*.085,0,3.22-i*.002) for i in range(30)])
pulleyx=12.4
for yy in [-.8,.8]:
 cube('pulley tower upright',(12.65+yy,.8,2.9),(.22,.22,5.8),wood)
 cube('pulley tower foot',(12.65+yy,.8,.12),(.95,.5,.24),dark)
beam('pulley crossbar',(11.65,.8,5.75),(13.65,.8,5.75),.22,.24,pale)
wheel=cyl('grooved wooden pulley',(12.65,0,5.5),.42,.22,dark,(pi/2,0,0))
for yy in [-.14,.14]:cyl('pulley rim',(12.65,yy,5.5),.46,.05,pale,(pi/2,0,0))
cyl('pulley brass hub',(12.65,-.20,5.5),.12,.10,metal,(pi/2,0,0))
cup=bpy.data.objects.new('hinged brass weighing cup',None);bpy.context.collection.objects.link(cup)
# open cup mesh with solid wall thickness, never a sealed cylinder
verts=[];faces=[]
for z,r in [(0,.25),(.16,.32)]:
 for i in range(48):a=2*pi*i/48;verts.append((r*cos(a),r*sin(a),z))
for i in range(48):j=(i+1)%48;faces.append((i,j,j+48,i+48))
faces.append(tuple(range(47,-1,-1)));mesh=bpy.data.meshes.new('open cup');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new('thin brass weighing cup',mesh);bpy.context.collection.objects.link(o);o.data.materials.append(metal);o.parent=cup;cupshell=o
sol=o.modifiers.new('thin sheet brass','SOLIDIFY');sol.thickness=.025
for yy in [-.3,.3]:curve('cup suspension',[(0,yy,.35),(0,yy,.9),(0,0,1.1)],.014,steel).parent=cup
# cup lowers as marble weight raises the wooden gate; it tips on a fixed peg at the bottom.
tween(cup,'location',[(0,(12.2,0,2.82)),(28,(12.2,0,2.82)),(33,(12.2,0,2.10)),(36,(12.2,0,2.10))])
tween(cupshell,'rotation_euler',[(0,(0,0,0)),(33,(0,0,0)),(34.3,(0,.75,0)),(36,(0,.75,0))])
gate=cube('lifted maple gate',(13.6,0,2.00),(.16,.82,.8),pale)
tween(gate,'location',[(0,(13.6,0,2)),(28,(13.6,0,2)),(33,(13.6,0,2.72)),(70,(13.6,0,2.72))])
for yy in [-.48,.48]:cube('gate guide',(13.6,yy,1.7),(.24,.16,3.4),dark)
# Rope is updated each frame with taut vertical sides and a semicircular wrap.
rope=curve('taut pulley cord',[(12.2,0,3.92),(12.2,0,5.5),(13.1,0,5.5),(13.1,0,2.1),(13.6,0,2.4)],.015,cordmat)
rail('cup landing rail',[(12.45+i*.095,0,2.18-i*.0106) for i in range(18)])
# Eight real wooden stairs: each landing remains visible while the ball falls in a gravity arc.
steps=[]
for i in range(8):
 x=14.3+i*.57;top=1.82-i*.19;cube('maple stair tread %02d'%i,(x,0,top-.075),(.57,.74,.15),pale)
 for yy in [-.33,.33]:cube('stair side cheek',(x,yy,top+.08),(.57,.06,.16),wood,.012)
 cube('stair riser',(x+.27,0,top-.18),(.045,.68,.25),wood,.01)
 if i%2==0:cube('stair leg',(x,.40,(top-.18)/2),(.14,.16,top-.18),dark)
 steps.append((x,top))
# Paper channel: folded, slightly imperfect cream paper, with brick-red outer faces.
paperpts=[]
for i in range(91):
 u=i/90;paperpts.append((18.81+u*4.69,.62*sin(u*pi*2),.35-u*.04))
verts=[]
for x,y,z in paperpts:
 verts.extend([(x,y-.32,z+.23),(x,y-.23,z-.05),(x,y+.23,z-.05),(x,y+.32,z+.23)])
faces=[]
for i in range(len(paperpts)-1):
 for k in range(3):faces.append((4*i+k,4*i+k+1,4*(i+1)+k+1,4*(i+1)+k))
faces=[tuple(reversed(face)) for face in faces]
mesh=bpy.data.meshes.new('creased paper trough');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new('folded paper winding trough',mesh);bpy.context.collection.objects.link(o);o.data.materials.append(cream);sol=o.modifiers.new('paper has physical thickness','SOLIDIFY');sol.thickness=.012
for i in [10,32,54,76]:
 x,y,z=paperpts[i];cube('paper supporting offcut',(x,y,z/2-.04),(.34,.65,z-.08),pale,.02)
# Short bell bridge and a handmade shallow wooden catch bowl.
rail('last straight',[(23.5+i*.062,0,.44-i*.004) for i in range(26)])
for i in range(3):
 xx=24.05+i*.3
 # suspended steel chime tube, struck in sequence
 depth=.68-i*.08
 tube=cyl('hanging tuned brass tube',(xx,.21,.30+depth/2),.045,depth,metal)
 for vertex in tube.data.vertices:vertex.co.z-=depth/2
 tube.location.z+=depth/2
 curve('chime suspension',[(xx,.21,.30+depth),(xx,.1,1.30)],.009,cordmat)
 tween(tube,'rotation_euler',[(0,(0,0,0)),([60.45,61.38,62.31][i],(0,0,0)),([60.45,61.38,62.31][i]+.12,(.16,0,0)),([60.45,61.38,62.31][i]+1,(-.05,0,0)),([60.45,61.38,62.31][i]+3,(0,0,0))])
beam('chime frame',(23.8,.1,1.35),(25,.1,1.35),.15,.14,dark)
for xx in [23.8,25]:cube('chime upright',(xx,.5,.65),(.13,.15,1.3),pale)
# bowl from concentric rings, smooth turned surface
verts=[];faces=[]
for j in range(15):
 u=j/14;r=.05+.72*u;z=.09+.08*u*u
 for i in range(64):a=2*pi*i/64;verts.append((25.6+r*cos(a),r*sin(a),z))
for j in range(14):
 for i in range(64):a=j*64+i;b=j*64+(i+1)%64;faces.append((a,b,b+64,a+64))
faces.append(tuple(range(63,-1,-1)))
faces=[tuple(reversed(face)) for face in faces]
me=bpy.data.meshes.new('turned bowl profile');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('hand turned walnut finishing bowl',me);bpy.context.collection.objects.link(o);o.data.materials.append(dark);mod=o.modifiers.new('solid turned wall','SOLIDIFY');mod.thickness=.06
for p in me.polygons:p.use_smooth=True
# Replay a real Bullet rigid-body bake for domino contacts, with editorial slow motion.
physics_path=ROOT+'/domino_physics.json'
physics_events=None
if os.path.exists(physics_path):
 physical=json.load(open(physics_path));physical_scale=(18.62-12.5)/float(physical['events']['24'])
 physics_events=[12.5+float(physical['events'][str(i)])*physical_scale for i in range(25)]
 domino_times=[]
 for i in range(25):
  ob=bpy.data.objects['maple domino %02d'%i];ob.parent=None;ob.animation_data_clear();ob.rotation_mode='QUATERNION'
  pose=physical['frames'][0][i];ob.location=pose[:3];ob.rotation_quaternion=pose[3:]
  if i==0:ob.rotation_quaternion=Euler((0,0,math.atan2(-1.1*pi,2.1))).to_quaternion()
  for frame in [1,12.3*24+1]:ob.keyframe_insert('location',frame=frame);ob.keyframe_insert('rotation_quaternion',frame=frame)
  onset=None
  for f,row in enumerate(physical['frames']):
   pose=row[i];tt=12.5+f/physical['fps']*physical_scale;ob.location=pose[:3];ob.rotation_quaternion=pose[3:];frame=tt*24+1
   ob.keyframe_insert('location',frame=frame);ob.keyframe_insert('rotation_quaternion',frame=frame)
   q=ob.rotation_quaternion;angle=math.acos(max(-1,min(1,1-2*(q.x*q.x+q.y*q.y))))
   if onset is None and angle>.025:onset=tt
  domino_times.append(onset)
  for fc in ob.animation_data.action.fcurves:
   for key in fc.keyframe_points:key.interpolation='LINEAR'

# Movement is contact-aligned, with rolling angles from distance and gravity-shaped stair drops.
# The mechanism animation is choreographed; it is not presented as a measured rigid-body experiment.
def smooth(u):return u*u*(3-2*u)
def lerp(a,b,u):return Vector(a).lerp(Vector(b),u)
def bowl_center_z(r):
 slope=2*.08*r/(.77*.77)
 return .27+.08*(r/.77)**2+.18*(math.sqrt(1+slope*slope)-1)
def ballpos(t):
 if t<1.2:
  u=max(0,t/1.2);return Vector((-.55+.60*u*u,0,4.95-.10*u*u))
 if t<11.8:
  u=(t-1.2)/10.6;q=55*(u**1.22);return Vector((.1+q*.12,.24*sin(q*.12),4.84-q*.019))
 if t<12.6:
  u=(t-11.8)/.8;return lerp((6.7,.10,3.795),(6.85,0,3.795),smooth(u))
 if t<19.6:return Vector((6.85,0,3.795))
 if t<24.8:
  u=(t-19.6)/5.2;theta=-.18+.66*smooth(min(1,u*3));xx=-1.15+2.83*(u*u);return Vector((8+xx*cos(theta),0,3.75-xx*sin(theta)+.25))
 if t<27.8:
  u=(t-24.8)/3;return lerp((9.52,0,3.22),(12.13,0,3.16),u)
 if t<33:
  z=2.82-.72*smooth(max(0,(t-28)/5));return Vector((12.2,0,z+.18+.16*max(0,1-(t-27.8)/.4)**2))
 if t<35:
  u=(t-33)/2;return Vector((12.2+.38*u*u,0,2.28-.1145*u*u))
 if t<37:
  u=(t-35)/2;x=12.58+1.67*u;return Vector((x,0,max(2.0,2.18-(x-12.45)*.0106/.095)))
 if t<48:
  u=(t-37)/11*8;i=min(7,int(u));q=u-i;x,top=steps[i]
  # rolling tread, then ballistic edge drop; acceleration is positive under gravity.
  if q<.55:return Vector((x-.05+q/.55*.335,0,top+.18))
  a=(q-.55)/.45;return Vector((x+.285+a*.235,0,top+.18-.19*a*a))
 if t<59:
  u=(t-48)/11;q=u*90;return Vector((18.81+u*4.69,.62*sin(u*pi*2),.35-u*.04+.13))
 if t<63.8:
  u=(t-59)/4.8;return lerp((23.5,0,.44),(25.05,0,.34),u)
 if t<65:
  u=(t-63.8)/1.2;x=25.05+.83*u;dt=t-63.8;z=max(.34-(.1/4.8)*dt-.5*.93*dt*dt,bowl_center_z(abs(x-25.6)));return Vector((x,0,z))
 u=t-65;r=.28*math.exp(-u*.8);a=u;return Vector((25.6+r*cos(a),r*sin(a),bowl_center_z(r)))

def cam_target(t):
 # Lead the eye into the domino transfer, then return smoothly to the hero.
 p=ballpos(t)
 if 12<t<20:
  u=max(0,min(1,(t-12.7)/6.3))
  if physics_events:
   idx=0.0
   for j in range(24):
    if t>=physics_events[j]:idx=j+max(0,min(1,(t-physics_events[j])/(physics_events[j+1]-physics_events[j]+.00001)))
   u=idx/24
  q=Vector((6.95+2.05*u,-.85-1.1*sin(u*pi),3.63))
  w=smooth(max(0,min(1,(t-12)/1.2)))*(1-smooth(max(0,min(1,(t-18.5)/1.5))))
  p=p.lerp(q,w)
 if 27.8<t<34:
  u=max(0,min(1,(t-28)/5));q=Vector((12.35,0,3.5-.25*smooth(u)))
  w=smooth(max(0,min(1,(t-27.8)/1.2)))*(1-smooth(max(0,min(1,(t-32)/2))))
  p=p.lerp(q,w)
 return p
def clear_cup_contact(p):
 ob=bpy.data.objects['thin brass weighing cup'].evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ob.to_mesh()
 tree=BVHTree.FromPolygons([ob.matrix_world@v.co for v in mesh.vertices],[tuple(face.vertices) for face in mesh.polygons]);ob.to_mesh_clear()
 for _ in range(8):
  point,normal,index,distance=tree.find_nearest(p)
  if distance>=.1802:break
  direction=p-point
  if direction.length<.000001:direction=normal.copy()
  direction.normalize();p+=direction*(.1802-distance)
 return p

# Bake motion and camera once: no dependency on runtime Python handlers in the saved .blend.
bpy.ops.object.camera_add();cam=bpy.context.object;cam.name='macro tracking camera';S.camera=cam;cam.data.lens=48;cam.data.sensor_width=36;cam.data.dof.use_dof=True;cam.data.dof.aperture_fstop=5.6
focus=bpy.data.objects.new('camera focus plane',None);bpy.context.collection.objects.link(focus);cam.data.dof.focus_object=focus
prev=ballpos(0);angle=0
for f in range(1,1681):
 t=(f-1)/24;S.frame_set(f);p=ballpos(t)
 if 27.8<=t<35:p=clear_cup_contact(p)
 angle+=(p-prev).length/.18;prev=p
 marble.location=p;marble.rotation_euler=(angle*.1,angle,angle*.04);marble.keyframe_insert('location',frame=f);marble.keyframe_insert('rotation_euler',frame=f)
 target=cam_target(t)
 # consistent screen direction, no whip pans; slightly wider during the pulley reveal
 wide=1+.23*max(0,1-abs(t-30)/5)
 offset=Vector((1.65,-4.2,3.65))*wide
 if t>65:offset*=1+.10*smooth((t-65)/5)
 cam.location=target+offset;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();focus.location=target
 cam.keyframe_insert('location',frame=f);cam.keyframe_insert('rotation_euler',frame=f);focus.keyframe_insert('location',frame=f)
# Linear per-frame baked transforms prevent interpolation overshoot.
for o in [marble,cam,focus]:
 for fc in o.animation_data.action.fcurves:
  for k in fc.keyframe_points:k.interpolation='LINEAR'
# Ropes have shape keys for the cup/gate endpoints, preserving tautness.
# use a frame handler for the setup render, and bake a separate mesh animation via shape keys.
# A single stationary wrap with moving hanging segments is enough for the rope's visible path.
bpy.data.objects.remove(rope,do_unlink=True)
curve('pulley wrap',[(12.65+.45*cos(pi-pi*i/32),0,5.5+.45*sin(pi-pi*i/32)) for i in range(33)],.015,cordmat)
left=curve('cup side taut rope',[(12.2,0,3.92),(12.2,0,5.5)],.015,cordmat)
right=curve('gate side taut rope',[(13.1,0,5.5),(13.1,0,2.4),(13.6,0,2.4)],.015,cordmat)
# animate curve points directly
for t,u in [(0,0),(28,0),(33,1),(70,1)]:
 left.data.splines[0].points[0].co=(12.2,0,3.92-.72*u,1);left.data.splines[0].points[0].keyframe_insert('co',frame=round(t*24)+1)
 for i in [1,2]:
  pt=right.data.splines[0].points[i];pt.co.z=2.4+.72*u;pt.keyframe_insert('co',frame=round(t*24)+1)
for t,a in [(0,0),(28,0),(33,1.6),(70,1.6)]:wheel.rotation_euler=(pi/2,a,0);wheel.keyframe_insert('rotation_euler',frame=round(t*24)+1)
S.render.filepath=ROOT+'/frames/'
S.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/workshop_chain.blend')
json.dump({'duration':70,'fps':24,'frames':1680,'size':[540,960],'domino_hits':domino_times,'domino_rigid_body':bool(physics_events),'stair_hits':[37+i*11/8 for i in range(8)],'chime_hits':[60.45,61.38,62.31],'note':'Original digitally constructed miniature; Rigid-body domino contacts retimed in slow motion; other mechanisms are staged with gravity-shaped trajectories. Not live-action or a full apparatus simulation.'},open(ROOT+'/film_metadata.json','w'),indent=2)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if '--preview' in args:
 S.cycles.samples=16;S.render.resolution_percentage=75
 for t in [0,8,16,22,30,42,53,62,68]:
  S.frame_set(round(t*24)+1);S.render.filepath=ROOT+'/look_%02d.png'%t;bpy.ops.render.render(write_still=True)
