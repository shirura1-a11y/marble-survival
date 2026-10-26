import json,subprocess,sys,hashlib
from fractions import Fraction
from pathlib import Path
p=Path(sys.argv[1])
r=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(p)]))
v=next(x for x in r['streams'] if x['codec_type']=='video');a=next(x for x in r['streams'] if x['codec_type']=='audio')
assert (v['width'],v['height'])==(720,1280)
assert Fraction(v['width'],v['height'])==Fraction(9,16)
assert Fraction(v['r_frame_rate'])==24
assert abs(float(r['format']['duration'])-70)<.05
assert v['codec_name']=='h264' and v['pix_fmt']=='yuv420p'
assert int(v['nb_read_frames'])==1680
assert a['codec_name']=='aac' and a['channels']==2 and int(a['sample_rate'])==48000
subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(p),'-f','null','-'],check=True)
result={'passed':True,'width':720,'height':1280,'fps':24,'frames':1680,'duration':r['format']['duration'],'bytes':int(r['format']['size']),'audio':'AAC stereo 48 kHz','full_decode':'passed','sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
print(json.dumps(result,indent=2))
p.with_suffix('.verification.json').write_text(json.dumps(result,indent=2)+'\n')
