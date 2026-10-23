"""Original soundtrack for the showcase video, synthesised with numpy/scipy (no samples, no external audio).

Usage: python -I audio.py events.json out.wav
Cue times come from events.json (dumped from index.html by `node render.mjs events`).
Structure: drone and sparse pulses (emergence) | node ticks | accents on camera moves | riser into the neural scene |
96 BPM groove for the engineering montage | restrained evidence scene | crescendo, one impact, fade to silence.
"""
import json, sys, wave
import numpy as np
from scipy import signal

SR, DUR = 48000, 60.0
N = int(SR * DUR)
ev = json.load(open(sys.argv[1]))
rng = np.random.default_rng(7)
dry, wet = np.zeros((N, 2), np.float32), np.zeros((N, 2), np.float32)
T = np.arange(N, dtype=np.float32) / SR


def add(bus, start, sig, pan=0.0, gain=1.0):
    i = int(start * SR)
    if i >= N or i < 0:
        return
    n = min(len(sig), N - i)
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    bus[i:i + n, 0] += sig[:n] * gain * l
    bus[i:i + n, 1] += sig[:n] * gain * r


def tt(dur): return np.arange(int(dur * SR), dtype=np.float32) / SR
def lp(x, fc, order=4): return signal.sosfilt(signal.butter(order, fc, "low", fs=SR, output="sos"), x).astype(np.float32)
def hp(x, fc, order=4): return signal.sosfilt(signal.butter(order, fc, "high", fs=SR, output="sos"), x).astype(np.float32)
def bp(x, lo, hi): return signal.sosfilt(signal.butter(3, [lo, hi], "band", fs=SR, output="sos"), x).astype(np.float32)
def sstep(a, b, x): u = np.clip((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)
def noise(n): return rng.standard_normal(n).astype(np.float32)
def saw(f, t, harm=10): return sum(np.sin(2 * np.pi * k * f * t) / k for k in range(1, harm + 1)).astype(np.float32) * (2 / np.pi)


def riser(dur, f0, f1, bw=.6):
    """noise whose spectral centre sweeps f0 -> f1 (exponentially) over dur seconds"""
    n = int(dur * SR); x = noise(n)
    f, t, Z = signal.stft(x, SR, nperseg=2048)
    fc = f0 * (f1 / f0) ** np.clip(t / dur, 0, 1)
    G = np.exp(-(np.log2((f[:, None] + 1) / fc[None, :]) / bw) ** 2)
    y = signal.istft(Z * G, SR, nperseg=2048)[1][:n].astype(np.float32)
    return y / (np.abs(y).max() + 1e-9)


def kick(g=1.0):
    t = tt(.4); ph = 2 * np.pi * np.cumsum(48 + 90 * np.exp(-t * 28)) / SR
    return (np.sin(ph) * np.exp(-t / .13) * g).astype(np.float32)


def hat(g=1.0): t = tt(.06); return (hp(noise(len(t)), 7000) * np.exp(-t / .016) * g).astype(np.float32)


def clap(g=1.0):
    t = tt(.28); n = bp(noise(len(t)), 1400, 4200) * np.exp(-t / .07)
    return ((n + .5 * np.sin(2 * np.pi * 330 * t) * np.exp(-t / .03)) * g).astype(np.float32)


def bell(f, dur=1.6, g=1.0):
    t = tt(dur)
    return ((np.sin(2 * np.pi * f * t + 1.2 * np.sin(2 * np.pi * f * 2.01 * t) * np.exp(-t / .25)) * np.exp(-t / (dur / 4))) * g).astype(np.float32)


def pluck(f, g=1.0):
    t = tt(.7)
    return ((np.sin(2 * np.pi * f * t) + .35 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / .1)) * np.exp(-t / .2) * g).astype(np.float32)


def boom(dur=2.4, g=1.0):
    t = tt(dur); ph = 2 * np.pi * np.cumsum(30 + 40 * np.exp(-t * 3.2)) / SR
    th = lp(noise(len(t)), 140) * np.exp(-t / .35)
    return ((np.sin(ph) * np.exp(-t / .9) + .5 * th) * g).astype(np.float32)


# ---------- drone (A minor, slowly opening) ----------
VOX = [(55.0, -.2), (55.35, .2), (82.41, -.4), (82.0, .4), (110.0, 0.0), (130.81, .3), (164.81, -.3)]
dr = [np.zeros(N, np.float32), np.zeros(N, np.float32)]
for f, p in VOX:
    s = saw(f, T, 8); s = (s * (1 + .12 * np.sin(2 * np.pi * (.07 + .013 * f / 100) * T + f))).astype(np.float32)
    for c in (0, 1):
        dr[c] += s * (np.cos((p + 1) * np.pi / 4) if c == 0 else np.sin((p + 1) * np.pi / 4)) * (1.0 if f < 120 else .6)
lo_l, lo_r, hi_l, hi_r = lp(dr[0], 240), lp(dr[1], 240), lp(dr[0], 900), lp(dr[1], 900)
open_ = (.25 + .5 * sstep(0, 20, T) + .25 * sstep(52, 56.4, T)).astype(np.float32)
lev = (sstep(0, 3.5, T) * (.55 + .2 * sstep(6, 8, T)) * (1 - .45 * sstep(30, 31, T) * (1 - sstep(54.5, 55.5, T))) * (1 - .25 * sstep(47.5, 49, T) * (1 - sstep(54.5, 55.5, T)))).astype(np.float32)
lev = lev * (1 + .45 * sstep(55.0, 56.4, T)) * (1 - sstep(57.0, 59.7, T)) * (1 - sstep(58.9, 59.9, T))
dry[:, 0] += (lo_l * (1 - open_) + hi_l * open_) * lev * .16
dry[:, 1] += (lo_r * (1 - open_) + hi_r * open_) * lev * .16
# violet shimmer for the neural scene and the finale
sh = (np.sin(2 * np.pi * 329.63 * T) + np.sin(2 * np.pi * 440.0 * T * 1.002) + .6 * np.sin(2 * np.pi * 659.26 * T)) * (.6 + .4 * np.sin(2 * np.pi * .21 * T)) * .5
shl = (sh * (sstep(21, 24, T) * (1 - sstep(29, 30.5, T)) * .5 + sstep(55.4, 56.6, T) * (1 - sstep(57.5, 59.6, T)) * .7)).astype(np.float32)
wet[:, 0] += shl * .05; wet[:, 1] += shl * .05

# ---------- scene 1: sparse pulses, node ticks, impact ----------
for k, s in enumerate(np.arange(.9, 7.0, 1.55)):
    add(wet, s, bell(1760 if k % 2 else 1318.5, .6, .05), pan=-.5 if k % 2 else .5)
SCALE = [0, 3, 5, 7, 10]
for n, s in enumerate(ev["nodeTimes"]):
    j, c = divmod(n, 9); f = 440 * 2 ** ((SCALE[(c + j) % 5] / 12) + (1 if j < 3 else 2 if j < 5 else 0) + (0 if c < 5 else 0))
    t = tt(.12); tick = np.sin(2 * np.pi * f * t) * np.exp(-t / .022) + .3 * hp(noise(len(t)), 5000) * np.exp(-t / .004)
    add(dry, s, tick.astype(np.float32), pan=-.7 + 1.4 * c / 8, gain=.07); add(wet, s, tick.astype(np.float32), pan=-.7 + 1.4 * c / 8, gain=.05)
im = ev["impacts"][0]
add(dry, im - 1.15, (riser(1.15, 600, 9000, .7) * np.linspace(0, 1, int(1.15 * SR)) ** 2).astype(np.float32), gain=.10)
add(dry, im, boom(2.6), gain=.62); add(wet, im, hp(noise(int(1.6 * SR)), 3000) * np.exp(-tt(1.6) / .45) * .05)

# ---------- scene 2: accents on the camera moves ----------
for s, f in [(8.0, 880.0), (10.0, 659.26), (12.9, 523.25), (15.8, 783.99), (18.2, 987.77)]:
    add(wet, s, bell(f, 2.0, .09), pan=.2); add(dry, s, bell(f, 1.4, .05), pan=.2)
for s in (9.6, 12.7, 15.6, 17.9):
    add(dry, s - .5, (riser(.9, 400, 3200, .8) * np.sin(np.linspace(0, np.pi, int(.9 * SR))) ** 2).astype(np.float32), gain=.05)

# ---------- scene 3: riser into the neural scene, data-flow plucks ----------
add(dry, 18.3, (riser(2.4, 300, 7000, .9) * np.linspace(0, 1, int(2.4 * SR)) ** 2.2).astype(np.float32), gain=.13)
add(dry, 20.7, boom(1.6, .3), gain=.4)
PENT = [220.0, 261.63, 293.66, 329.63, 392.0, 440.0, 523.25, 587.33, 659.26, 783.99, 880.0]
step = 60 / ev["bpm"] / 4
for k, s in enumerate(np.arange(24.6, 29.5, step)):
    if rng.random() < .62:
        f = PENT[int(rng.integers(0, len(PENT)))]; add(dry, s, pluck(f, .07), pan=rng.uniform(-.6, .6)); add(wet, s, pluck(f, .11), pan=rng.uniform(-.6, .6))
add(dry, 28.4, (riser(1.6, 500, 6000, .8) * np.linspace(0, 1, int(1.6 * SR)) ** 2).astype(np.float32), gain=.10)

# ---------- scenes 4-5: engineering groove (96 BPM, panel switches every 4 beats) ----------
beat = 60 / ev["bpm"]
BASS = [55.0, 55.0, 65.41, 55.0, 55.0, 55.0, 82.41, 73.42]
for b in range(int(round((40.0 - 30.0) / beat))):
    s = 30.0 + b * beat; bar_start = (b % 4 == 0); gain = 1.0 if b < 16 else .6
    add(dry, s, kick(.55 * (1.15 if bar_start else 1.0)), gain=gain)
    add(dry, s + beat / 2, hat(.07), pan=.35, gain=gain); add(dry, s, hat(.03), pan=-.3, gain=gain)
    if b % 2 == 1: add(dry, s, clap(.14), pan=.05, gain=gain); add(wet, s, clap(.12), gain=gain)
    for h in range(2):
        f = BASS[(b * 2 + h) % 8]; t = tt(beat / 2 * .9)
        bs = lp(saw(f, t, 6), 420 + 700 * sstep(30, 37, 30 + b * beat)) * np.exp(-t / .22) * .11
        add(dry, s + h * beat / 2, bs.astype(np.float32))
for s, f in [(30.0, 110.0), (32.5, 164.81), (35.0, 220.0), (37.5, 329.63)]:
    add(dry, s, boom(1.2, .5), gain=.5); add(wet, s, bell(f * 4, 1.4, .1), pan=.3)
    add(dry, s - .6, (riser(.6, 800, 5000, .8) * np.linspace(0, 1, int(.6 * SR)) ** 2).astype(np.float32), gain=.06)
for s, f in [(40.0, 392.0), (42.8, 523.25), (45.7, 659.26)]:
    add(wet, s, bell(f, 2.2, .1), pan=-.2); add(dry, s, bell(f, 1.4, .06), pan=-.2)
for b in range(int(round(8.0 / beat))):  # quiet pulse through the interface scene
    s = 40.0 + b * beat
    if b % 2 == 0: add(dry, s, kick(.28), gain=.55 * (1 - sstep(46.5, 48, s)))
    add(dry, s + beat / 2, hat(.04), pan=.3, gain=.5 * (1 - sstep(46.5, 48, s)))

# ---------- scene 6: restrained ----------
for s in (48.6, 51.1, 53.6):
    add(dry, s, boom(1.8, .22), gain=.5); add(wet, s + .02, bell(220.0, 2.4, .08), pan=-.3)
for s, f in [(52.0, 987.77), (52.28, 880.0), (52.56, 783.99), (52.84, 659.26), (53.12, 587.33)]:
    add(wet, s, bell(f, 1.6, .045), pan=.35)

# ---------- scene 7: crescendo, one impact, fade ----------
add(dry, 55.0, (riser(1.4, 200, 9000, .9) * np.linspace(0, 1, int(1.4 * SR)) ** 2.4).astype(np.float32), gain=.2)
imp = ev["impacts"][1]
add(dry, imp, boom(2.8, 1.0), gain=.8); add(wet, imp, hp(noise(int(2.2 * SR)), 2500) * np.exp(-tt(2.2) / .6) * .07)
for f, g in [(110.0, .07), (164.81, .05), (220.0, .05), (329.63, .035), (493.88, .02)]:
    pad = np.sin(2 * np.pi * f * T) * sstep(55.6, 57.0, T) * (1 - sstep(57.8, 59.7, T))
    wet[:, 0] += pad * g * .8; wet[:, 1] += pad * g * .8

# ---------- reverb send, master ----------
tr = tt(3.2); ir = noise(len(tr)) * np.exp(-tr / .85) * (1 - np.exp(-tr / .02)); ir = lp(ir, 5200).astype(np.float32); ir /= np.abs(ir).sum() * .12
rev = np.stack([signal.fftconvolve(wet[:, c], ir)[:N] for c in range(2)], 1).astype(np.float32)
mix = dry + rev * .9 + wet * .12
mix = np.stack([hp(mix[:, c], 28, 2) for c in range(2)], 1)
mix = np.tanh(mix * 1.15) / 1.15
mix *= sstep(0, 1.0, T)[:, None] * (1 - sstep(59.0, 59.98, T))[:, None]
peak = float(np.abs(mix).max()); mix *= (10 ** (-2.0 / 20)) / peak
pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
with wave.open(sys.argv[2], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
rms = [float(20 * np.log10(np.sqrt(np.mean(mix[int(a * SR):int((a + 5) * SR)] ** 2)) + 1e-9)) for a in range(0, 60, 5)]
print("peak dBFS %.2f, rms/5s:" % (20 * np.log10(np.abs(mix).max())), [round(x, 1) for x in rms], "tail(last 50ms) max %.5f" % float(np.abs(mix[-int(.05 * SR):]).max()))
