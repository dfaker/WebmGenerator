
import subprocess as sp
import numpy as np

RATE = 44100
sample = r'C:\Users\baxter001\VideoEditor\music\Beat Banger ｜ Zoe The Hiena OST ｜ Official Visual [Uo7BnWKbKfA].mp3'

proc = sp.Popen(['ffmpeg', '-y', '-i', sample, '-ac', '1', '-filter_complex', "[0:a]anull,aresample={}:async=1".format(RATE), '-map', '0:a', '-c:a', 'pcm_u8', '-f', 'data', '-'],stdout=sp.PIPE)

dt = np.dtype(np.uint8)
dt = dt.newbyteorder('<')

outs,errs = proc.communicate()
outs = np.frombuffer(outs, dtype=dt).flatten()

ch = np.abs(np.fft.fft(outs))
ys = np.multiply(20, np.log10(ch))
xs = np.arange(len(outs), dtype=float)
y_avg = np.mean(ys)
    
low_freq = [ys[i] for i in range(len(xs))]
low_freq_avg = np.mean(low_freq)

bass = low_freq[:int(len(low_freq)/2)]
bass_avg = np.mean(bass)

beats = np.where(ys<bass_avg)
print(ys.shape)
print(beats[0].shape)
print((beats[0]/RATE).astype(int))