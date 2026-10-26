import bpy,json,math,os
ROOT=os.path.dirname(os.path.abspath(__file__))
from mathutils import Vector
s=bpy.context.scene;ball=bpy.data.objects['hero marble / rolling assembly'];rods=[bpy.data.objects['hanging tuned brass tube'+suffix] for suffix in ['', '.001','.002']];best=[(1e9,None)]*3
for sample in range(round(59*240),round(64.5*240)):
 t=sample/240;f=t*24+1;s.frame_set(int(f),subframe=f-int(f));p=ball.matrix_world.translation
 for i,rod in enumerate(rods):
  dep=.68-i*.08;a=rod.matrix_world@Vector((0,0,-dep));b=rod.matrix_world@Vector((0,0,0));ab=b-a;u=max(0,min(1,(p-a).dot(ab)/ab.length_squared));gap=(p-(a+u*ab)).length-.225
  if gap<best[i][0]:best[i]=(gap,t)
print('CHIME_MIN_CLEARANCE_AND_TIME',best)
assert all(gap>-.003 for gap,t in best),best
assert all(gap<.003 for gap,t in best),best
hits=json.load(open(ROOT+'/film_metadata.json'))['chime_hits']
errors=[abs(t-h) for (gap,t),h in zip(best,hits)]
assert max(errors)<1/24,errors
json.dump({'passed':True,'min_clearance_and_time':best,'contact_tolerance':.003,'sampling_hz':240,'audio_event_error_seconds':errors},open(ROOT+'/chime_contact_check.json','w'),indent=2)
