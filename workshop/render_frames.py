import bpy,sys,os,time,glob,subprocess,json
import numpy as np

ROOT=os.path.dirname(os.path.abspath(__file__))
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=4;s.cycles.use_denoising=False
s.cycles.max_bounces=5;s.cycles.glossy_bounces=3;s.cycles.transmission_bounces=4
s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
s.render.threads_mode='FIXED';s.render.threads=5
layer=s.view_layers[0];layer.use_pass_normal=True;layer.use_pass_diffuse_color=True
s.use_nodes=True;n=s.node_tree.nodes;n.clear();r=n.new('CompositorNodeRLayers')
for output,socket in [('color','Image'),('albedo','DiffCol'),('normal','Normal')]:
 node=n.new('CompositorNodeOutputFile');node.base_path='/tmp/workshop-passes';node.format.file_format='OPEN_EXR';node.format.color_depth='32';node.file_slots[0].path=output;s.node_tree.links.new(r.outputs[socket],node.inputs[0])
comp=n.new('CompositorNodeComposite');s.node_tree.links.new(r.outputs['Image'],comp.inputs[0])
os.makedirs('/tmp/workshop-passes',exist_ok=True)
worker=subprocess.Popen(['/workspace/marble-survival/.venv/bin/python',ROOT+'/denoise_worker.py'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
start=int(args[0]) if args else 1;end=int(args[1]) if len(args)>1 else 1680;stride=int(args[2]) if len(args)>2 else 2
begin=time.time();done=0
frames=([1,73,289,385,481,553,697,817,1009,1153,1345,1537,1633] if os.environ.get('WORKSHOP_QA')=='1' else range(start,end+1,stride))
for frame in frames:
 target=ROOT+'/frames/%04d.png'%frame
 if os.path.exists(target):continue
 t0=time.time();s.frame_set(frame);bpy.ops.render.render(write_still=False)
 worker.stdin.write(str(frame)+'\n');worker.stdin.flush();reply=json.loads(worker.stdout.readline());assert reply.get('ok'),reply
 done+=1
 print('PROGRESS frame=%d/%d elapsed=%.1f frame_seconds=%.2f'%(frame,end,time.time()-begin,time.time()-t0),flush=True)
 if frame==start:
  print('DENOISED_TEST_SAVED',target,flush=True)
worker.stdin.close();assert worker.wait()==0
