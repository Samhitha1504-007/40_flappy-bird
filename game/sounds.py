import math
from array import array

import pygame


class _Silent:
    """Stand-in used when audio is unavailable."""
    def play(self):
        pass


def _samples(freq_start, freq_end, duration, volume, square=True):
    """Return 16-bit samples for a tone that sweeps from freq_start to freq_end."""
    sample_rate, _size, channels = pygame.mixer.get_init()
    n = int(sample_rate * duration)
    attack = max(1, int(0.005 * sample_rate))  # 5 ms fade-in avoids clicks
    amp = 32767 * volume
    buf = array("h")
    phase = 0.0
    for i in range(n):
        t = i / n
        freq = freq_start + (freq_end - freq_start) * t
        phase += 2 * math.pi * freq / sample_rate
        s = math.sin(phase)
        if square:
            s = 1.0 if s >= 0 else -1.0
        env = min(1.0, i / attack) * (1.0 - t)  # fade in, then fade out to 0
        buf.extend([int(amp * s * env)] * channels)  # one value per channel
    return buf


class Sounds:
    def __init__(self):
        self.flap = self.score = self.die = _Silent()
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            if pygame.mixer.get_init()[1] != -16:  # samples are signed 16-bit
                return
            self.flap = pygame.mixer.Sound(buffer=_samples(500, 900, 0.08, 0.20))
            self.score = pygame.mixer.Sound(buffer=_samples(880, 880, 0.06, 0.20, square=False)
                                                   + _samples(1320, 1320, 0.10, 0.20, square=False))
            self.die = pygame.mixer.Sound(buffer=_samples(400, 80, 0.45, 0.25))
        except pygame.error:
            pass  # no audio device: the silent stand-ins remain