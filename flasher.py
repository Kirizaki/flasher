import queue
import sys
import time
import numpy as np
import sounddevice as sd
import pygame

# Audio
SR = 44100
BLOCKSIZE = 1024
CHANNELS = 1

# Beat detection
ENERGY_HISTORY = 43
SENSITIVITY_MULT = 2.0       # lower = more sensitive
MIN_INTERVAL_SEC = 0.12

# Display
WIN_W, WIN_H = 800, 600
FLASH_MS = 120
FPS = 60

# Gain control (logarithmic scale)
GAIN_STEP_DB = 1.0
GAIN_MIN_DB = -20.0
GAIN_MAX_DB = 20.0

# Sensitivity control
SENS_STEP = 0.1
SENS_MIN = 1.0
SENS_MAX = 5.0

# UI timing
BAR_TIMEOUT = 2.0

audio_q = queue.Queue()


def audio_callback(indata, frames, time_info, status):
    if status:
        pass
    mono = indata.mean(axis=1) if indata.ndim > 1 else indata
    audio_q.put(mono)


def rms(block):
    return np.sqrt(np.mean(block.astype(np.float64) ** 2))


class BeatDetector:
    def __init__(self, history, sensitivity_mult, min_interval):
        self.history = history
        self.sensitivity_mult = sensitivity_mult
        self.min_interval = min_interval
        self.energies = []
        self.last_beat_time = 0

    def process(self, energy, now=None):
        if now is None:
            now = time.time()
        avg_energy = np.mean(self.energies) if self.energies else 0
        beat = False
        if len(self.energies) >= self.history and avg_energy > 0:
            if energy > avg_energy * self.sensitivity_mult:
                if now - self.last_beat_time >= self.min_interval:
                    beat = True
                    self.last_beat_time = now
        self.energies.append(energy)
        if len(self.energies) > self.history:
            self.energies.pop(0)
        return beat, avg_energy


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H), flags=pygame.RESIZABLE)
    clock = pygame.time.Clock()
    pygame.display.set_caption("Beat Flash with Gain & Sensitivity Control")

    font = pygame.font.SysFont(None, 24)

    bd = BeatDetector(ENERGY_HISTORY, SENSITIVITY_MULT, MIN_INTERVAL_SEC)

    stream = sd.InputStream(channels=CHANNELS, samplerate=SR, blocksize=BLOCKSIZE, callback=audio_callback)
    stream.start()

    flash_until = 0
    gain_db = 0.0
    sens_mult = SENSITIVITY_MULT
    show_bars_until = 0
    buffer = np.zeros(0, dtype=np.float32)

    try:
        running = True
        while running:
            now = time.time()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                elif ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        running = False
                    elif ev.key == pygame.K_UP:
                        gain_db = min(gain_db + GAIN_STEP_DB, GAIN_MAX_DB)
                        show_bars_until = now + BAR_TIMEOUT
                    elif ev.key == pygame.K_DOWN:
                        gain_db = max(gain_db - GAIN_STEP_DB, GAIN_MIN_DB)
                        show_bars_until = now + BAR_TIMEOUT
                    elif ev.key == pygame.K_RIGHT:
                        sens_mult = min(sens_mult + SENS_STEP, SENS_MAX)
                        bd.sensitivity_mult = sens_mult
                        show_bars_until = now + BAR_TIMEOUT
                    elif ev.key == pygame.K_LEFT:
                        sens_mult = max(sens_mult - SENS_STEP, SENS_MIN)
                        bd.sensitivity_mult = sens_mult
                        show_bars_until = now + BAR_TIMEOUT

            try:
                while True:
                    block = audio_q.get_nowait()
                    buffer = np.concatenate((buffer, block))
            except queue.Empty:
                pass

            while len(buffer) >= BLOCKSIZE:
                gain_lin = 10 ** (gain_db / 20.0)
                proc_block = buffer[:BLOCKSIZE] * gain_lin
                buffer = buffer[BLOCKSIZE:]
                energy = rms(proc_block)
                beat, _ = bd.process(energy, time.time())
                if beat:
                    flash_until = time.time() + FLASH_MS / 1000.0

            if time.time() < flash_until:
                screen.fill((255, 255, 255))
            else:
                screen.fill((0, 0, 0))

            # Draw bars + numbers
            if time.time() < show_bars_until:
                bar_w = int(WIN_W * 0.6)
                bar_h = 20
                bar_x = (WIN_W - bar_w) // 2

                # Gain bar
                bar_y1 = WIN_H - 100
                pygame.draw.rect(screen, (20, 20, 20), (bar_x, bar_y1, bar_w, bar_h))
                gain_ratio = (gain_db - GAIN_MIN_DB) / (GAIN_MAX_DB - GAIN_MIN_DB)
                pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y1, int(bar_w * gain_ratio), bar_h))
                gain_text = font.render(f"Gain: {gain_db:.1f} dB", True, (255, 255, 255))
                screen.blit(gain_text, (bar_x, bar_y1 - 22))

                # Sensitivity bar
                bar_y2 = WIN_H - 50
                pygame.draw.rect(screen, (20, 20, 20), (bar_x, bar_y2, bar_w, bar_h))
                sens_ratio = (sens_mult - SENS_MIN) / (SENS_MAX - SENS_MIN)
                pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y2, int(bar_w * sens_ratio), bar_h))
                sens_text = font.render(f"Threshold: {sens_mult:.2f}×", True, (255, 255, 255))
                screen.blit(sens_text, (bar_x, bar_y2 - 22))

            pygame.display.flip()
            clock.tick(FPS)

    finally:
        stream.stop()
        stream.close()
        pygame.quit()


if __name__ == "__main__":
    main()
