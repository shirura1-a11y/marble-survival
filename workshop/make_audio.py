"""Original score and procedural foley; no sampled or licensed music."""
import numpy as np, wave, json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SR=48000;D=70;N=SR*D;rng=np.random.default_rng(27)
music=np.zeros((N,2),np.float32);fx=np.zeros_like(music)
def add(dst,t,sig,gain=1,pan=0):
 i=round(t*SR)
 if i<0 or i>=N:return
 n=min(len(sig),N-i);sig=sig[:n]*gain
 # equal power stereo, never hard pan
 dst[i:i+n,0]+=sig*math.sqrt((1-pan)/2);dst[i:i+n,1]+=sig*math.sqrt((1+pan)/2)
def modal(freq,dur=1,wood=False):
 t=np.arange(int(SR*dur))/SR;y=np.zeros(len(t))
 ratios=[1,2.756,5.404,8.933] if wood else [1,2.01,3.94,5.33]
 for i,r in enumerate(ratios):
  decay=(3.6+i*3) if wood else (1.6+i*1.1)
  y+=sinphase(freq*r,t)*np.exp(-t*decay)/(1+i*2.3)
 y*=np.minimum(1,t/.002)
 return y.astype(np.float32)
def sinphase(f,t):return np.sin(2*np.pi*f*t)
def note(midi):return 440*2**((midi-69)/12)
# A light original 6/8 miniature: marimba melody, felt-like broken chords, and quiet pizzicato bass.
beat=60/104;bar=beat*3
progression=[[60,64,67,71],[57,60,64,67],[53,57,60,64],[55,59,62,67]]
melodies=[[76,79,81,79,76,74],[72,76,79,76,74,72],[77,76,72,69,72,76],[74,71,67,71,74,79]]
for b in range(39):
 tb=1+b*bar
 if tb>67:break
 chord=progression[b%4];mel=melodies[b%4]
 for k in range(6):
  tt=tb+k*beat/2
  # every fourth phrase leaves more space for the apparatus
  if not (b%8==7 and k in [2,4]):add(music,tt,modal(note(mel[k]+(0 if b<24 else 0)),.72,True),.075 if k%2==0 else .052,(-1)**k*.18)
  add(music,tt,modal(note(chord[k%4]),1.0,True),.032,.28 if k%2 else -.28)
 bass=note(chord[0]-24);t=np.arange(int(SR*.8))/SR
 sig=(np.sin(2*np.pi*bass*t)+.25*np.sin(2*np.pi*2*bass*t))*np.exp(-t*7)*np.minimum(1,t/.004)
 add(music,tb,sig,.11,-.05)
# Final warm cadence, no endless loop or abrupt ending.
for j,m in enumerate([60,64,67,72]):add(music,67+j*.12,modal(note(m),2.5,True),.065,j*.12-.18)
# Continuous rolling: low irregular contact rumble, with fine intermittent gritty ticks.
noise=rng.normal(size=N).astype(np.float32)
# Simple stable one-pole lowpass via FFT avoids dependence on scipy.
freqs=np.fft.rfftfreq(N,1/SR);spec=np.fft.rfft(noise);spec*=1/np.sqrt(1+(freqs/950)**4);roll=np.fft.irfft(spec,n=N).astype(np.float32)
t=np.arange(N,dtype=np.float32)/SR
env=np.zeros(N,np.float32)
for a,b,g in [(0,12.5,.022),(20.1,27.8,.025),(34,37,.024),(37,48,.012),(48,59,.013),(59,65,.02),(65,69,.009)]:
 mask=(t>=a)&(t<b);env[mask]=g*np.minimum(1,(t[mask]-a)*3)*np.minimum(1,(b-t[mask])*3)
roll*=env*(.7+.15*np.sin(t*23)+.12*np.sin(t*39.7))
fx[:,0]+=roll*.85;fx[:,1]+=np.roll(roll,27)*.85
# Contact sounds: each impact is an excited resonator plus a short filtered noise transient.
def knock(tt,g=.2,kind='wood',pitch=450,pan=0):
 dur=.35 if kind=='wood' else 1.8;x=np.arange(int(SR*dur))/SR
 if kind=='wood':
  sig=(np.sin(2*np.pi*pitch*x)*np.exp(-x*48)+.40*np.sin(2*np.pi*pitch*2.62*x)*np.exp(-x*70)+rng.normal(size=len(x))*.25*np.exp(-x*170));sig*=np.minimum(1,x/.0005)
 else:sig=modal(pitch,dur,False)
 add(fx,tt,sig,g,pan)
meta=json.load(open(ROOT/'film_metadata.json'))
knock(.28,.25,pitch=540);knock(.66,.30,pitch=310);knock(1.22,.20,pitch=680)
for i,tt in enumerate(meta['domino_hits']):knock(tt,.19+.02*np.sin(i),pitch=430+45*(i%4),pan=.15*np.sin(i*.2))
knock(12.3,.25,pitch=280);knock(19.35,.23,pitch=350);knock(20.4,.16,pitch=300)
knock(24.83,.18,pitch=510);knock(35.0,.16,pitch=460);knock(36.98,.14,pitch=460)
knock(27.95,.12,'metal',980)
# Tiny wooden pulley creaks and rope slips, synchronized to the cup descent.
for tt in np.arange(28.4,33,.41):
 x=np.arange(int(.11*SR))/SR;sig=np.sin(2*np.pi*(380*x+450*x*x))*np.exp(-x*27)*rng.normal(1,.2,len(x));add(fx,tt,sig,.023,.18)
knock(33.8,.17,'metal',760)
for i in range(8):knock(37+(i+.98)*11/8,.24-.009*i,pitch=520-i*26)
# Paper rustle has a distinct dry, high frequency texture, softer than the wood.
mask=(t>48)&(t<59);hi=noise-np.roll(noise,1);fx[mask,0]+=hi[mask]*.0025;fx[mask,1]+=np.roll(hi,19)[mask]*.0025
for i,tt in enumerate(meta['chime_hits']):knock(tt,.17,'metal',[1318.51,1567.98,2093][i],pan=i*.12-.12)
knock(64.15,.17,pitch=380)
for j in range(7):knock(65+j*.24,.065*np.exp(-j*.5),pitch=600+j*19)
# Music ducks slightly beneath the domino chain and final bell.
duck=np.ones(N,np.float32)
for a,b in [(12,20),(60,65)]:
 mask=(t>a)&(t<b);duck[mask]=.72
music*=duck[:,None]
y=music+fx
# Gentle room tail, short enough to keep each collision readable.
for delay,g in [(.037,.10),(.061,.065),(.097,.035)]:
 d=int(SR*delay);y[d:,0]+=fx[:-d,1]*g;y[d:,1]+=fx[:-d,0]*g
fade=np.minimum(1,t/.05)*np.minimum(1,(D-t)/1.0);y*=fade[:,None];y=np.tanh(y*1.8)/1.8
peak=float(np.max(np.abs(y)));y*=.86/max(.86,peak)
with wave.open(str(ROOT/'original_score_and_foley.wav'),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes((y*32767).astype('<i2').tobytes())
json.dump({'original_composition':True,'external_samples':False,'sample_rate':SR,'seconds':D,'peak':peak,'effects':['glass rolling on wood','domino impacts','seesaw release','pulley creak','stair impacts','paper rustle','three brass chimes']},open(ROOT/'audio_metadata.json','w'),indent=2)
print('AUDIO_COMPLETE',ROOT/'original_score_and_foley.wav')
