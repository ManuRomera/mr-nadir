#!/usr/bin/env python3
"""Banda sonora y efectos de «Nádir» sintetizados desde cero (numpy + ffmpeg). Todo es obra original del módulo.

Paleta común: drones en re menor, resonancias metálicas inarmónicas, pings de sónar, hielo/agua filtrados y
reverberación de galería. Música: bucles sin costura de ~96 s. Ambientes: bucles de ~32 s. Disparos: 2–12 s.
Uso: python3 tools/audio.py [--only clave1,clave2]     ->  assets/audio/{musica,sfx}/<clave>.ogg (Opus)
"""
import argparse
import os
import subprocess
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "audio")
SR = 44100
D1 = 36.708  # re1


# ------------------------------------------------------------------ utilidades
def t_axis(sec):
    return np.arange(int(sec * SR)) / SR


def rng_for(key):
    return np.random.default_rng(sum(map(ord, key)) * 7919)


def noise(n, rng, color="white"):
    x = rng.standard_normal(n)
    if color == "white":
        return x
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = f[1]
    X /= np.sqrt(f) if color == "pink" else f
    y = np.fft.irfft(X, n)
    return y / (np.abs(y).max() + 1e-9)


def band(x, lo=None, hi=None, order=4):
    """Filtro paso-banda suave en frecuencia (Butterworth de magnitud, estático)."""
    n = len(x)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    m = np.ones_like(f)
    if lo:
        m *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1e-3)) ** (2 * order))
    if hi:
        m *= 1 / np.sqrt(1 + (f / hi) ** (2 * order))
    return np.fft.irfft(X * m, n)


def reso(x, fc, q=30):
    """Resonancia estrecha (campana gaussiana) en fc."""
    n = len(x)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    return np.fft.irfft(X * np.exp(-0.5 * ((f - fc) / (fc / q)) ** 2), n) * 4


def env_exp(n, decay):
    return np.exp(-np.arange(n) / (decay * SR))


def adsr(n, a, r):
    e = np.ones(n)
    na, nr = min(n, int(a * SR)), min(n, int(r * SR))
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def place(buf, ev, pos):
    pos = int(pos)
    if pos >= len(buf) or pos < 0:
        return
    end = min(len(buf), pos + len(ev))
    buf[pos:end] += ev[:end - pos]


def bell(freq, sec, rng, partials=(1, 2.76, 5.4, 8.93), decay=1.2):
    t = t_axis(sec)
    y = np.zeros_like(t)
    for i, p in enumerate(partials):
        y += np.sin(2 * np.pi * freq * p * t + rng.uniform(0, 6.28)) * np.exp(-t / (decay / (1 + i * 0.8))) / (1 + i)
    return y


def ping(freq, sec=4.0, decay=1.6):
    t = t_axis(sec)
    glide = freq * (1 + 0.004 * np.exp(-t * 3))
    return np.sin(2 * np.pi * np.cumsum(glide) / SR) * np.exp(-t / decay) * np.minimum(1, t * 200)


def thump(freq=52, sec=0.9, drop=2.0):
    t = t_axis(sec)
    f = freq * (1 + drop * np.exp(-t * 18))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6) * np.minimum(1, t * 400)


def burst(sec, rng, lo, hi, decay=0.05):
    n = int(sec * SR)
    return band(rng.standard_normal(n), lo, hi) * env_exp(n, decay)


def reverb(x, rng, sec=3.5, mix=0.35, dark=4000):
    """Convolución con una respuesta de galería sintética (estéreo decorrelado)."""
    n = int(sec * SR)
    out = []
    for ch in range(2):
        ir = rng.standard_normal(n) * np.exp(-np.arange(n) / (sec / 6.9 * SR))
        ir = band(ir, 80, dark)
        ir /= np.sqrt((ir ** 2).sum()) + 1e-9
        L = len(x) + n
        Nf = 1 << (L - 1).bit_length()
        out.append(np.fft.irfft(np.fft.rfft(x, Nf) * np.fft.rfft(ir, Nf), Nf)[:L])
    wet = np.stack(out, 1)
    dry = np.stack([np.pad(x, (0, n))] * 2, 1)
    dry /= np.sqrt((dry ** 2).mean()) + 1e-9
    wet /= np.sqrt((wet ** 2).mean()) + 1e-9
    return dry * (1 - mix) + wet * mix


def loopify(st, L, fade):
    """st (N,2) con N >= L+fade -> bucle de L muestras sin costura."""
    y = st[:L].copy()
    F = int(fade * SR)
    w = np.linspace(0, 1, F)[:, None]
    y[:F] = st[L:L + F] * (1 - w) + y[:F] * w
    return y


def master(st, rms_db=-20, peak=0.8):
    st = st - st.mean(0)
    rms = np.sqrt((st ** 2).mean()) + 1e-9
    st = st * (10 ** (rms_db / 20) / rms)
    return np.tanh(st / peak) * peak  # limitador suave


def save(st, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path[:-4] + ".wav"
    data = (np.clip(st, -1, 1) * 32767).astype(np.int16)
    with wave.open(tmp, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-c:a", "libopus", "-b:a", "112k" if "musica" in path else "96k", path], check=True)
    os.remove(tmp)


# ------------------------------------------------------------------ música
MUSICA = {
    # clave: (raíz Hz, brillo 0-1, bpm del pulso o 0, pings/min, textura, tensión 0-1)
    "exploracion": (D1, 0.25, 0, 3, "radar", 0.2),
    "turno": (D1, 0.35, 66, 2, "maquina", 0.15),
    "superficie": (D1 * 1.5, 0.3, 0, 4, "vacio", 0.25),
    "control": (D1, 0.45, 0, 2, "electrico", 0.45),
    "galerias": (D1 * 0.75, 0.3, 0, 3, "hielo", 0.55),
    "cria": (D1 * 0.75, 0.2, 44, 1, "organico", 0.75),
    "refugio": (D1, 0.25, 0, 1, "respiracion", 0.6),
    "bomba": (D1, 0.4, 84, 2, "metal", 0.55),
    "contrarreloj": (D1, 0.55, 104, 4, "metal", 0.95),
    "final": (D1 * 1.5, 0.3, 0, 2, "vacio", 0.1),
}


def drone(t, root, bright, rng, tension):
    y = np.zeros_like(t)
    third = 2.0 * (1.0595 if tension > 0.7 else 1.0)
    for base, w in ((root, 1.0), (root * 1.5, 0.55), (root * third, 0.35)):
        for k in range(1, 28):
            amp = w / k * np.exp(-k / (2 + 10 * bright))
            lfo = 1 + 0.45 * np.sin(2 * np.pi * rng.uniform(0.01, 0.06) * t + rng.uniform(0, 6.28))
            det = 1 + rng.uniform(-0.002, 0.002)
            y += amp * lfo * np.sin(2 * np.pi * base * k * det * t + rng.uniform(0, 6.28))
    return y / (np.abs(y).max() + 1e-9)


def pad(t, root, rng, tension):
    chord = [4, 4 * 1.189, 4 * 1.498, 4 * 2.245] if tension < 0.6 else [4, 4 * 1.059, 4 * 1.498, 4 * 1.414]
    y = np.zeros_like(t)
    for c in chord:
        for d in (-0.003, 0.003):
            swell = 0.5 + 0.5 * np.sin(2 * np.pi * rng.uniform(0.008, 0.02) * t + rng.uniform(0, 6.28))
            y += np.sin(2 * np.pi * root * c * (1 + d) * t) * swell ** 2
    return y / (np.abs(y).max() + 1e-9)


def normal(x):
    return x / (np.sqrt((x ** 2).mean()) + 1e-9) * 0.3


def textura(kind, n, rng, t):
    if kind == "radar":
        return normal(band(noise(n, rng, "pink"), 200, 1500)) * 0.5
    if kind == "maquina":
        hum = sum(np.sin(2 * np.pi * 50 * k * t) / k for k in range(1, 6))
        return normal(hum) * 0.4 + normal(band(rng.standard_normal(n), 100, 600)) * 0.3
    if kind == "vacio":
        return normal(band(noise(n, rng, "pink"), 40, 300) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.03 * t)))
    if kind == "electrico":
        buzz = sum(np.sin(2 * np.pi * 100 * k * t + k) / k ** 1.3 for k in range(1, 14))
        return normal(buzz) * 0.35
    if kind == "hielo":
        crack = np.zeros(n)
        for _ in range(int(n / SR * 0.4)):
            place(crack, burst(0.4, rng, 1500, 7000, 0.03) * rng.uniform(0.2, 1), rng.integers(0, n))
        return normal(band(noise(n, rng, "pink"), 300, 2500)) * 0.4 + normal(crack) * 0.6
    if kind == "organico":
        g = band(rng.standard_normal(n), 80, 400) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.7 * t + np.sin(2 * np.pi * 0.11 * t) * 3)) ** 3
        clicks = np.zeros(n)
        for _ in range(int(n / SR * 2)):
            place(clicks, burst(0.05, rng, 2000, 6000, 0.008) * rng.uniform(0.3, 1), rng.integers(0, n))
        return normal(g) * 0.9 + normal(clicks) * 0.5
    if kind == "respiracion":
        y = np.zeros(n)
        for _ in range(5):
            rate = rng.uniform(0.18, 0.32)
            envb = np.maximum(0, np.sin(2 * np.pi * rate * t + rng.uniform(0, 6.28))) ** 2
            y += band(rng.standard_normal(n), 300, 2000) * envb * rng.uniform(0.4, 1)
        return normal(y) * 0.6
    if kind == "metal":
        return normal(band(noise(n, rng, "pink"), 60, 800)) * 0.5
    return np.zeros(n)


def musica(key):
    root, bright, bpm, pings, tex, tension = MUSICA[key]
    rng = rng_for(key)
    L, fade = 96, 6
    sec = L + fade + 1
    t = t_axis(sec)
    n = len(t)
    mono = normal(drone(t, root, bright, rng, tension)) * 1.6
    mono += normal(pad(t, root, rng, tension)) * (0.5 + 0.4 * (1 - tension))
    mono += textura(tex, n, rng, t)
    if bpm:
        step = 60 / bpm
        k = 0
        hits = np.zeros(n)
        while k * step < sec:
            if key == "cria":
                place(hits, thump(42, 1.2, 1.2) * 0.9, k * step * SR)
                place(hits, thump(38, 1.2, 1.0) * 0.6, (k * step + 0.32) * SR)
            elif tex == "metal":
                jit = rng.uniform(-0.04, 0.04) if key == "bomba" else 0
                place(hits, thump(55, 0.6, 2.5) * 0.7, (k * step + jit) * SR)
                if rng.random() < (0.35 if key == "bomba" else 0.6):
                    place(hits, bell(rng.choice([180, 211, 247]), 1.5, rng, decay=0.5) * 0.25, (k * step + step / 2) * SR)
            else:
                place(hits, thump(50, 0.8, 1.5) * 0.45, k * step * SR)
            k += 1
        mono += normal(hits) * (0.9 if key != "turno" else 0.5)
    pl = np.zeros(n)
    for _ in range(max(1, int(pings * sec / 60))):
        f = rng.choice([587.3, 880.0, 1174.7, 1318.5]) if tension < 0.7 else rng.choice([622.3, 932.3, 1244.5])
        place(pl, ping(f, 5, 1.8), rng.uniform(0, sec - 5) * SR)
    mono += normal(pl) * 0.35
    if key == "contrarreloj":
        sh = np.zeros(n)
        for o in range(5):
            ph = (o + t / sec) % 5
            f = 110 * 2 ** ph
            sh += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * ph / 5) ** 2
        mono += normal(sh) * 0.3
    st = reverb(mono, rng, 4.5, 0.4, 3500)
    st = loopify(st, int(L * SR), fade)
    return master(st, -21)


# ------------------------------------------------------------------ efectos
def amb_loop(fn, key, L=32, fade=3, rms=-24):
    rng = rng_for(key)
    sec = L + fade + 1
    mono = fn(t_axis(sec), int(sec * SR), rng)
    st = reverb(mono, rng, 2.5, 0.3, 5000)
    return master(loopify(st, int(L * SR), fade), rms)


def one_shot(fn, key, sec, rms=-18, rev=0.25):
    rng = rng_for(key)
    mono = fn(t_axis(sec), int(sec * SR), rng)
    mono = mono * adsr(len(mono), 0.003, min(0.4, sec / 4))
    st = reverb(mono, rng, 2.2, rev, 5000)
    return master(st, rms)


def f_hum(t, n, rng):
    return sum(np.sin(2 * np.pi * 50 * k * (1 + 0.0005 * np.sin(2 * np.pi * 0.3 * t)) * t) / k ** 1.2 for k in range(1, 10)) + band(rng.standard_normal(n), 2000, 6000) * 0.02


def f_ventilador(t, n, rng):
    speed = 1 + 0.08 * np.sin(2 * np.pi * 0.05 * t) + 0.04 * np.sin(2 * np.pi * 0.31 * t)
    blade = 0.6 + 0.4 * np.sin(2 * np.pi * np.cumsum(17 * speed) / SR) ** 2
    rattle = (np.sin(2 * np.pi * 0.21 * t) > 0.92).astype(float) * band(rng.standard_normal(n), 800, 3000) * 0.3
    return band(rng.standard_normal(n), 80, 1800) * blade + rattle


def f_bomba_b4(t, n, rng):
    motor = sum(np.sin(2 * np.pi * 118 * k * t) / k for k in range(1, 7))
    chug = (0.5 + 0.5 * np.sin(2 * np.pi * 1.3 * t)) ** 4
    return motor * 0.3 + band(rng.standard_normal(n), 60, 500) * chug * 1.2


def f_bomba_p2(t, n, rng):
    y = sum(np.sin(2 * np.pi * 96 * k * t) / k for k in range(1, 6)) * 0.25
    pos = 0.0
    while pos < len(t) / SR:
        place(y, thump(70, 0.5, 3) * rng.uniform(0.7, 1.1) + burst(0.5, rng, 300, 2500, 0.04)[:int(0.5 * SR)] * 0.4, pos * SR)
        pos += rng.uniform(0.55, 1.15)
    return y


def drip_layer(n, rng, rate):
    y = np.zeros(n)
    for _ in range(int(n / SR * rate)):
        f = rng.uniform(900, 2400)
        tt = t_axis(0.25)
        d = np.sin(2 * np.pi * np.cumsum(f * (1 + 0.6 * np.exp(-tt * 40))) / SR) * np.exp(-tt * 28)
        place(y, d * rng.uniform(0.2, 1), rng.integers(0, n))
    return y


def f_goteo(t, n, rng):
    return drip_layer(n, rng, 1.6) + band(noise(n, rng, "pink"), 400, 3000) * 0.05


def scrape_layer(n, rng, density=1.0, close=1.0):
    """Raspado de dentículos: trenes de chasquidos irregulares (25–55 por segundo) con cuerpo metálico resonante."""
    y = np.zeros(n)
    pos = int(rng.uniform(0, 0.5) * SR)
    while pos < n:
        dur = rng.uniform(0.5, 2.4)
        rate = rng.uniform(25, 55)
        tt = 0.0
        sw = rng.uniform(0.3, 1.0)
        while tt < dur:
            k = int(rng.uniform(0.003, 0.009) * SR)
            amp = np.sin(np.pi * tt / dur) ** 0.7 * rng.uniform(0.3, 1.0) * sw
            click = band(rng.standard_normal(k + 64), rng.uniform(1200, 2500), rng.uniform(4500, 8000))[:k] * env_exp(k, 0.002) * amp
            place(y, click, pos + tt * SR)
            tt += 1 / rate * rng.uniform(0.5, 1.6)
        pos += int((dur + rng.uniform(0.4, 3.5) / density) * SR)
    body = np.zeros(n)
    for fc in (420.0, 610.0, 980.0):
        body += reso(y, fc, 18)
    return y + body * 0.35 * close


def f_raspado(t, n, rng):
    return scrape_layer(n, rng, 0.8, 0.8)


def f_cria_latido(t, n, rng):
    y = np.zeros(n)
    k = 0
    while k * 1.35 < len(t) / SR:
        place(y, thump(40, 1.0, 0.8) * 0.9 + burst(1.0, rng, 120, 700, 0.12) * 0.5, k * 1.35 * SR)
        k += 1
    return y + drip_layer(n, rng, 0.6) * 0.5


def f_respiraciones(t, n, rng):
    y = np.zeros(n)
    for i in range(6):
        rate = rng.uniform(0.2, 0.34)
        e = np.maximum(0, np.sin(2 * np.pi * rate * t + rng.uniform(0, 6.28))) ** 1.5
        y += band(rng.standard_normal(n), 250, 2200) * e * rng.uniform(0.3, 1)
    for _ in range(3):
        place(y, burst(0.35, rng, 200, 1800, 0.08) * 2.5, rng.integers(0, n - SR))
    return y


def f_casco(t, n, rng):
    rate = 0.26
    e = np.maximum(0, np.sin(2 * np.pi * rate * t)) ** 1.3
    br = band(rng.standard_normal(n), 400, 2600) * e
    clicks = np.zeros(n)
    k = 0
    while k / rate < len(t) / SR:
        place(clicks, burst(0.02, rng, 2000, 8000, 0.004) * 0.6, (k / rate) * SR)
        k += 1
    return br + clicks + sum(np.sin(2 * np.pi * 60 * j * t) / j for j in range(1, 4)) * 0.01


def f_rover(t, n, rng):
    whine = np.sin(2 * np.pi * np.cumsum(410 + 6 * np.sin(2 * np.pi * 0.4 * t)) / SR) * 0.12
    rumble = band(rng.standard_normal(n), 25, 220) * (0.7 + 0.3 * np.abs(np.sin(2 * np.pi * 2.1 * t)))
    return whine + rumble


def f_alarma_lenta(t, n, rng):
    y = np.zeros(n)
    k = 0
    while k * 2.4 < len(t) / SR:
        for j, f in enumerate((660, 495)):
            tt = t_axis(0.35)
            place(y, np.sign(np.sin(2 * np.pi * f * tt)) * adsr(len(tt), 0.01, 0.05) * 0.5, (k * 2.4 + j * 0.4) * SR)
        k += 1
    return band(y, 200, 2500)


def f_radar(t, n, rng):
    return ping(1318.5, len(t) / SR, 1.2) + ping(1318.5 * 1.5, len(t) / SR, 0.6) * 0.2


def f_temblor(t, n, rng):
    env = np.minimum(1, t / 1.0) * np.exp(-np.maximum(0, t - 2.5) / 1.5)
    y = band(rng.standard_normal(n), 15, 140) * env * 2
    for _ in range(25):
        place(y, burst(0.15, rng, 600, 4000, 0.03) * rng.uniform(0.1, 0.5), rng.uniform(0.3, 4) * SR)
    return y


def f_alarma_presion(t, n, rng):
    f = 520 + 280 * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 2.5 * t)))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * (np.sin(2 * np.pi * 5 * t) > -0.2) * 0.6


def f_alarma_co2(t, n, rng):
    y = np.zeros(n)
    for k in range(3):
        tt = t_axis(0.18)
        place(y, np.sin(2 * np.pi * 2093 * tt) * adsr(len(tt), 0.005, 0.03), (0.1 + k * 0.28) * SR)
    return y


def f_siseo(t, n, rng):
    env = np.minimum(1, t / 0.6) * (0.8 + 0.2 * np.sin(2 * np.pi * 7 * t))
    return band(rng.standard_normal(n), 2500, 12000) * env


def f_golpe(t, n, rng):
    y = bell(97, len(t) / SR, rng, (1, 1.47, 2.09, 2.56, 3.93, 5.11), 1.4)
    place(y, burst(0.2, rng, 100, 3000, 0.05) * 2, 0)
    return y


def f_chirrido(t, n, rng):
    y = scrape_layer(n, rng, 3, 1.2)
    walk = np.cumsum(rng.standard_normal(n)) / np.sqrt(n) * 900
    f = 3400 + walk - walk.mean()
    gate = np.convolve((rng.random(n) < 0.08).astype(float), np.ones(int(SR * 0.03)), "same").clip(0, 1)
    sq = np.sin(2 * np.pi * np.cumsum(f) / SR) * gate * 0.08
    return y + band(sq, 1500, 9000) * adsr(n, 0.2, 0.6)


def f_compuerta(t, n, rng):
    y = band(rng.standard_normal(n), 3000, 11000) * np.exp(-t / 0.8) * 0.6
    y += np.sin(2 * np.pi * np.cumsum(140 + 40 * t) / SR) * ((t > 0.6) & (t < 3.0)) * 0.4
    place(y, bell(70, 1.5, rng, (1, 1.8, 2.7), 0.6) * 1.2 + thump(48, 1.5, 2) * 1.5, 3.0 * SR)
    return y


def f_arranque(t, n, rng):
    f = 120 + 330 * (1 - np.exp(-t / 1.2))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.3 + band(rng.standard_normal(n), 30, 250) * np.minimum(1, t / 1.5)


def f_soldadura(t, n, rng):
    crackle = (rng.random(n) < 0.02) * rng.standard_normal(n) * 4
    return band(crackle + rng.standard_normal(n) * 0.2, 1500, 12000) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 3 * t)))


def f_terminal(t, n, rng):
    y = np.zeros(n)
    for _ in range(18):
        place(y, burst(0.03, rng, 2000, 7000, 0.006), rng.uniform(0, 2.2) * SR)
    for k, f in enumerate((1568, 2093, 1760)):
        tt = t_axis(0.09)
        place(y, np.sin(2 * np.pi * f * tt) * 0.4, (2.3 + k * 0.12) * SR)
    return y


def f_estatica(t, n, rng):
    st = band(rng.standard_normal(n), 300, 3400) * (0.6 + 0.4 * (rng.random(n) > 0.995))
    place(st, np.sin(2 * np.pi * 1200 * t_axis(0.12)) * 0.3, 0)
    return st


def f_serrat(t, n, rng):
    st = band(rng.standard_normal(n), 300, 3400) * 0.35
    sc = np.zeros(n)
    pos = 1.5
    while pos < len(t) / SR - 1:
        ln = int(0.55 * SR)
        g = (np.sin(2 * np.pi * 9 * t_axis(0.55)) > 0) * adsr(ln, 0.03, 0.1)
        wet = band(rng.standard_normal(ln), 700, 2600) * g + reso(rng.standard_normal(ln), 330, 20) * g * 0.5
        place(sc, wet, pos * SR)
        pos += rng.uniform(1.1, 1.6)
    return st + band(sc, 300, 3400) * 1.4


AMBIENTES = {"hum": f_hum, "ventilador": f_ventilador, "bomba-b4": f_bomba_b4, "bomba-p2": f_bomba_p2, "goteo": f_goteo,
             "raspado": f_raspado, "cria-latido": f_cria_latido, "respiraciones": f_respiraciones, "casco-respiracion": f_casco,
             "rover-motor": f_rover, "alarma-lenta": f_alarma_lenta}
DISPAROS = {"radar-ping": (f_radar, 4), "temblor": (f_temblor, 6), "alarma-presion": (f_alarma_presion, 4), "alarma-co2": (f_alarma_co2, 2),
            "siseo": (f_siseo, 4), "golpe-metal": (f_golpe, 4), "chirrido": (f_chirrido, 3.5), "raspado-fuerte": (lambda t, n, r: scrape_layer(n, r, 2, 1.5), 6),
            "compuerta": (f_compuerta, 4.5), "rover-arranque": (f_arranque, 4), "soldadura": (f_soldadura, 5), "terminal": (f_terminal, 3),
            "radio-estatica": (f_estatica, 4), "radio-serrat": (f_serrat, 12)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    only = set(a.only.split(",")) if a.only else None

    def ok(k):
        return not only or k in only
    for k in MUSICA:
        if ok(k):
            save(musica(k), os.path.join(OUT, "musica", k + ".ogg"))
            print("música", k, flush=True)
    for k, fn in AMBIENTES.items():
        if ok(k):
            save(amb_loop(fn, k, rms=-28 if k == "hum" else -24), os.path.join(OUT, "sfx", k + ".ogg"))
            print("ambiente", k, flush=True)
    for k, (fn, sec) in DISPAROS.items():
        if ok(k):
            save(one_shot(fn, k, sec), os.path.join(OUT, "sfx", k + ".ogg"))
            print("disparo", k, flush=True)


if __name__ == "__main__":
    main()
