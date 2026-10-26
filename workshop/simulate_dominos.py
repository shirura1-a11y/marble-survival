import bpy,math,json
from mathutils import Matrix,Vector
import os
ROOT=os.path.dirname(os.path.abspath(__file__))
s=bpy.context.scene;s.frame_set(1)
keep=[]
for i in range(25):
 ob=bpy.data.objects['maple domino %02d'%i];world=ob.matrix_world.copy();ob.parent=None;ob.animation_data_clear();ob.matrix_world=world;keep.append(ob)
platform=bpy.data.objects['domino curved run base'];platform.location.y=-1.35;platform.dimensions.y=2.35;keep.append(platform)
for o in list(bpy.data.objects):
 if o not in keep:bpy.data.objects.remove(o,do_unlink=True)
for o in keep:
 bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.rigidbody.object_add();o.select_set(False)
 o.rigid_body.type='PASSIVE' if o==platform else 'ACTIVE';o.rigid_body.collision_shape='BOX';o.rigid_body.use_margin=True;o.rigid_body.collision_margin=.0005;o.rigid_body.friction=.6;o.rigid_body.restitution=.05;o.rigid_body.mass=.08
s.render.fps=60;s.frame_start=1;s.frame_end=360;s.rigidbody_world.point_cache.frame_start=1;s.rigidbody_world.point_cache.frame_end=360;s.rigidbody_world.substeps_per_frame=8;s.rigidbody_world.solver_iterations=50
first=keep[0];u=0;yaw=math.atan2(-1.1*math.pi,2.1);rot=Matrix.Rotation(yaw,4,'Z')@Matrix.Rotation(.15,4,'Y');first.matrix_world=Matrix.Translation(Vector((6.9,-.85,3.28)))@rot@Matrix.Translation((0,0,.33))
records=[];events={}
for f in range(1,361):
 s.frame_set(f);bpy.context.view_layer.update();row=[]
 for i,ob in enumerate(keep[:25]):
  m=ob.matrix_world.copy();p=m.translation;q=m.to_quaternion();row.append([*p,*q]);angle=math.acos(max(-1,min(1,m[2][2])))
  if angle>.18 and i not in events:events[i]=(f-1)/60
 records.append(row)
print('PHYSICS_EVENTS',events,flush=True)
json.dump({'fps':60,'events':events,'frames':records},open(ROOT+'/domino_physics.json','w'))
