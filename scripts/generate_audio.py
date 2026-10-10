"""Генерация городского звукового фона (без внешних зависимостей).

Создаёт:
  godot/assets/audio/ambient_city.wav — зацикленный городской гул
  godot/assets/audio/footstep_1..3.wav — шаги (три варианта)

Запуск: python3 scripts/generate_audio.py
"""
import array
import math
import os
import random
import wave

AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         '..', 'godot', 'assets', 'audio')


def write_wav(path, rate, samples):
    with wave.open(path, 'w') as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        frames = array.array('h')
        for sample in samples:
            frames.append(int(max(-1.0, min(1.0, sample)) * 32767))
        handle.writeframes(frames.tobytes())


def make_loop(source, fade):
    """Обрезает хвост длиной `fade`, склеивая его с началом без щелчка."""
    n = len(source) - fade
    out = list(source[:n - fade])
    for i in range(n - fade, n):
        w = (i - (n - fade)) / fade
        out.append((1.0 - w) * source[i] + w * source[i - (n - fade)])
    return out


def ambient_city():
    rate = 22050
    duration = 12.0
    fade = int(rate * 0.4)
    total = int(rate * duration) + fade
    rnd = random.Random(20261010)
    # Бурая шумовая волна — низкочастотный гул города (трафик, вентили).
    brown = 0.0
    raw = []
    for _ in range(total):
        brown = (brown + 0.02 * rnd.uniform(-1.0, 1.0)) * 0.9995
        raw.append(brown)
    # Однополюсный фильтр — смягчает гул.
    lowpass = 0.0
    smoothed = []
    for value in raw:
        lowpass += 0.08 * (value - lowpass)
        smoothed.append(lowpass)
    peak = max(abs(v) for v in smoothed) or 1.0
    looped = make_loop([v / peak for v in smoothed], fade)
    n = len(looped)
    final = []
    for i in range(n):
        t = i / rate
        # Медленное «дыхание» города (период 6 с делит 12 с ровно).
        swell = 0.85 + 0.15 * math.sin(2.0 * math.pi * t / 6.0 - 1.3)
        # Слабый трансформаторный гул 55 Гц (660 периодов в 12 с).
        hum = 0.018 * math.sin(2.0 * math.pi * 55.0 * t)
        final.append(0.5 * (looped[i] * swell + hum))
    write_wav(os.path.join(AUDIO_DIR, 'ambient_city.wav'), rate, final)


def footstep(seed, path):
    rate = 44100
    duration = 0.18
    n = int(rate * duration)
    rnd = random.Random(seed)
    frequency = rnd.uniform(72.0, 105.0)
    white = [rnd.uniform(-1.0, 1.0) for _ in range(n + 1)]
    samples = []
    for i in range(n):
        t = i / rate
        # Глухой удар подошвы + короткий шумовой щелчок.
        thump = 0.6 * math.exp(-t / 0.030) * math.sin(2.0 * math.pi * frequency * t)
        tick = (white[i + 1] - white[i]) * math.exp(-t / 0.011) * 0.5
        samples.append(thump + tick)
    peak = max(abs(v) for v in samples) or 1.0
    write_wav(path, rate, [v / peak * 0.8 for v in samples])


def main():
    os.makedirs(AUDIO_DIR, exist_ok=True)
    ambient_city()
    for i in range(1, 4):
        footstep(11 * i, os.path.join(AUDIO_DIR, 'footstep_%d.wav' % i))
    print('AUDIO_OK: ambient_city.wav + 3 footstep variants')


if __name__ == '__main__':
    main()
