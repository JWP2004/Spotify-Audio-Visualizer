import pygame
import sounddevice as sd
import numpy as np
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import threading
import time
from PIL import Image
import requests
from io import BytesIO

# Sound Config
SAMPLE_RATE = 44100
CHUNK_SIZE = 1024

# Spotipy Dev Data (cant show key on public repo)
SPOTIFY_CLIENT_ID = 'KEY WILL BE ADDED FOR FINAL FOR SECURITY REASONS'
CLIENT_SECRET = 'KEY WILL BE ADDED FOR FINAL FOR SECURITY REASONS'
REDIRECT_URI = 'http://127.0.0.1:9090/callback'

class SpotifyManager:
    def __init__(self):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope='user-read-playback-state,user-modify-playback-state'
        ))
        self.track_title = "Loading..."
        self.album_art = None
        self.progress_ms = 0
        self.duration_ms = 1
        self.art_lock = threading.Lock()
        self.thread = threading.Thread(target=self.update_loop, daemon=True)
        self.thread.start()

    def update_loop(self):
        while True:
            try:
                current = self.sp.current_playback()
                if current and current.get("item"):
                    track = current["item"]
                    artist = ", ".join([a["name"] for a in track["artists"]])
                    title = track["name"]
                    image_url = track["album"]["images"][0]["url"]
                    progress = current["progress_ms"]
                    duration = track["duration_ms"]
                    art = self.load_album_art(image_url) if image_url else None
                    with self.art_lock:
                        self.track_title = f"{title} - {artist}"
                        self.album_art = art
                        self.progress_ms = progress
                        self.duration_ms = duration
            except Exception:
                pass
            time.sleep(1)

    def load_album_art(self, url):
        try:
            response = requests.get(url)
            image = Image.open(BytesIO(response.content)).convert("RGBA")
            return pygame.image.fromstring(image.tobytes(), image.size, image.mode)
        except:
            return None

    def control_playback(self, action):
        try:
            if action == "previous":
                self.sp.previous_track()
            elif action == "play_pause":
                if self.sp.current_playback()["is_playing"]:
                    self.sp.pause_playback()
                else:
                    self.sp.start_playback()
            elif action == "next":
                self.sp.next_track()
        except Exception as e:
            print(f"Spotify API error: {e}")
            
            
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


        with self.spotify.art_lock:
             if self.spotify.album_art:
                art_size = 200
                art = pygame.transform.smoothscale(self.spotify.album_art, (art_size, art_size))
                screen.blit(art, (screen.get_width() - art_size - 20, 20))

        title = font.render(self.spotify.track_title, True, (255, 255, 255))
        screen.blit(title, (20, 20))

        # Time stamp bar
        bar_x, bar_y = 20, screen.get_height() - 50
        bar_width = screen.get_width() - 40
        bar_height = 10
        pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
        progress_ratio = self.spotify.progress_ms / self.spotify.duration_ms
        pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, int(bar_width * progress_ratio), bar_height))


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
