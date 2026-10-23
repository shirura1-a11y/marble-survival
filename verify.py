import json,subprocess,sys
from fractions import Fraction
p=sys.argv[1]
r=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',p]))
v=next(x for x in r['streams'] if x['codec_type']=='video');a=next(x for x in r['streams'] if x['codec_type']=='audio')
assert (v['width'],v['height'])==(1080,1920)
assert 30<=Fraction(v['r_frame_rate'])<=60
assert abs(float(r['format']['duration'])-60)<.05
assert v['codec_name']=='h264' and v['pix_fmt']=='yuv420p'
assert int(v['nb_read_frames'])==1800
assert a['codec_name']=='aac' and a['channels']==2
subprocess.run(['ffmpeg','-v','error','-i',p,'-f','null','-'],check=True)
print(json.dumps({'passed':True,'width':v['width'],'height':v['height'],'fps':v['r_frame_rate'],'frames':int(v['nb_read_frames']),'duration':r['format']['duration'],'bytes':int(r['format']['size']),'audio':a['codec_name']},indent=2))
