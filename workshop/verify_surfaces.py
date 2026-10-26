import bpy,json,os
from mathutils.bvhtree import BVHTree
ROOT=os.path.dirname(os.path.abspath(__file__))
s=bpy.context.scene;ball=bpy.data.objects['hero marble / rolling assembly'];dg=bpy.context.evaluated_depsgraph_get()
def bvh(names):
 verts=[];faces=[]
 for name in names:
  obj=bpy.data.objects[name];ev=obj.evaluated_get(dg);mesh=ev.to_mesh();offset=len(verts);verts.extend([ev.matrix_world@v.co for v in mesh.vertices]);faces.extend([tuple(offset+i for i in f.vertices) for f in mesh.polygons]);ev.to_mesh_clear()
 return BVHTree.FromPolygons(verts,faces)
s.frame_set(1)
cup=bvh(['cup landing rail maple rail','cup landing rail maple rail.001'])
last=bvh(['last straight maple rail','last straight maple rail.001'])
bowl=bvh(['hand turned walnut finishing bowl'])
paper=bvh(['folded paper winding trough'])
def gaps(tree,start,end):
 result=[]
 for i in range(round(start*240),round(end*240)+1):
  t=i/240;f=t*24+1;s.frame_set(int(f),subframe=f-int(f));distance=tree.find_nearest(ball.matrix_world.translation)[3];result.append((distance-.18,t))
 return result
report={}
for name,tree,a,b in [('cup_rail',cup,35,36.5),('last_rail',last,59,63.7),('paper',paper,48.1,58.8),('bowl_rest',bowl,64.2,69.95)]:
 values=gaps(tree,a,b);lo=min(values);hi=max(values);report[name]={'minimum_gap':lo,'maximum_gap':hi};print(name,lo,hi,flush=True)
 assert lo[0]>-.005,(name,'penetration',lo)
 assert hi[0]<.005,(name,'floating',hi)
air=gaps(bowl,63.8,64.2);assert min(air)[0]>-.005,('bowl approach',min(air));report['bowl_approach']={'minimum_gap':min(air)}
cup_values=[]
for sample in range(round(28.3*120),round(34.95*120)):
 t=sample/120;f=t*24+1;s.frame_set(int(f),subframe=f-int(f));tree=bvh(['thin brass weighing cup']);gap=tree.find_nearest(ball.matrix_world.translation)[3]-.18;cup_values.append((gap,t))
assert min(cup_values)[0]>-.005,('cup shell',min(cup_values))
report['cup_shell']={'minimum_gap':min(cup_values)}
report['passed']=True;report['tolerance']=.005;report['sampling_hz']=240
json.dump(report,open(ROOT+'/surface_contact_check.json','w'),indent=2)
print('SURFACE_CONTACTS_PASSED',flush=True)
