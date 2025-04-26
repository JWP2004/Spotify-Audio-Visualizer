import pygame
import sounddevice as sd
import numpy as np

# Sound Config
SAMPLE_RATE = 44100
CHUNK_SIZE = 1024

class AudioInput:
    # ran into issues on testing, have to use 3rd party software to capture sound for spotify, create README file on how to setup
    def __init__(self):
        self.audio_buffer = np.zeros(CHUNK_SIZE)
        self.device_index = self.find_vb_audio_device()
        self.stream = sd.InputStream(callback=self.audio_callback,
                                     channels=1,
                                     samplerate=SAMPLE_RATE,
                                     blocksize=CHUNK_SIZE,
                                     device=(self.device_index, None))
        self.stream.start()

    def find_vb_audio_device(self):
        devices = sd.query_devices()
        for idx, dev in enumerate(devices):
            if "cable output" in dev['name'].lower() and dev['max_input_channels'] > 0:
                return idx
        raise RuntimeError("VB-Audio device not found.")

    def audio_callback(self, indata, frames, time, status):
        self.audio_buffer = np.copy(indata[:, 0])

class Visualizer:
    def __init__(self, audio_input):
        self.audio_input = audio_input

    def draw(self, screen):
        WIDTH, HEIGHT = screen.get_size()
        screen.fill((0, 0, 0))

        # Sound Bars (FFT), do not exceed 80 otherwise it wont render for some reason
        fft = np.abs(np.fft.rfft(self.audio_input.audio_buffer * np.hanning(len(self.audio_input.audio_buffer))))
        fft = fft / np.max(fft + 1e-6)
        num_bars = 80
        bar_width = WIDTH // num_bars
        max_height = HEIGHT // 2

        for i in range(num_bars):
            index = int(i * len(fft) / num_bars)
            bar_height = int(fft[index] * max_height)
            x = i * bar_width
            y = HEIGHT - bar_height
            pygame.draw.rect(screen, (255, 255, 255), (x, y, bar_width - 2, bar_height))

        # Grey wave form for reference of sound or no sound (also cool looking)
        resampled_indices = np.linspace(0, len(self.audio_input.audio_buffer) - 1, WIDTH).astype(int)
        resampled = self.audio_input.audio_buffer[resampled_indices]
        waveform = (resampled * 100) + (HEIGHT - 100)
        points = [(x, waveform[x]) for x in range(WIDTH)]
        pygame.draw.aalines(screen, (200, 200, 200), False, points)

pygame.init()
screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
pygame.display.set_caption("Spotify Audio Visualizer")
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((0, 0, 0))
    pygame.display.flip()

pygame.quit()
