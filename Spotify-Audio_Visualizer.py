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

# Sound Config (DONT CHANGE THESE APART FROM FPS)
SAMPLE_RATE = 44100
CHUNK_SIZE = 1024
FPS = 60

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
        # there would be a stutter effects when it checks for updates, this fixed the issue
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

# Searches for VB-Audio cable (YOU MUST HAVE DRIVERS INSTALLED OTHERWISE IT WONT LAUNCH)
    def find_vb_audio_device(self):
        devices = sd.query_devices()
        for idx, dev in enumerate(devices):
            if "cable output" in dev['name'].lower() and dev['max_input_channels'] > 0:
                return idx
        raise RuntimeError("VB-Audio device not found.")

    def audio_callback(self, indata, frames, time, status):
        self.audio_buffer = np.copy(indata[:, 0])

class Visualizer:
    def __init__(self, audio_input, spotify_manager):
        self.audio_input = audio_input
        self.spotify = spotify_manager
        self.background_color = [0, 0, 0]
        self.bar_color = [255, 255, 255]
        self.visualizer_shape = "rectangle"
        self.visualizer_offset = 150
        self.logo = pygame.image.load("spovis.png").convert_alpha()
        self.logo = pygame.transform.smoothscale(self.logo, (200, 200))
        self.logo_angle = 0

    def draw(self, screen, font):
        WIDTH, HEIGHT = screen.get_size()
        screen.fill(self.background_color)
        mouse_pos = pygame.mouse.get_pos()

        fft = np.abs(np.fft.rfft(self.audio_input.audio_buffer * np.hanning(len(self.audio_input.audio_buffer))))
        fft = fft / np.max(fft + 1e-6)

        num_bars = 80
        bar_width = WIDTH // num_bars
        max_height = HEIGHT // 2
        for i in range(num_bars):
            index = int(i * len(fft) / num_bars)
            magnitude = fft[index]
            bar_height = int(magnitude * max_height)
            x = i * bar_width
            y = HEIGHT - self.visualizer_offset - bar_height

            color = tuple(self.bar_color)
            if self.visualizer_shape == "rectangle":
                pygame.draw.rect(screen, color, pygame.Rect(x, y, bar_width - 2, bar_height), border_radius=6)
            elif self.visualizer_shape == "circle":
                pygame.draw.circle(screen, color, (x + bar_width // 2, y + bar_height // 2), bar_width // 4)
            elif self.visualizer_shape == "triangle":
                points = [(x + bar_width // 2, y), (x, y + bar_height), (x + bar_width, y + bar_height)]
                pygame.draw.polygon(screen, color, points)

        resampled_indices = np.linspace(0, len(self.audio_input.audio_buffer) - 1, WIDTH).astype(int)
        resampled_waveform = self.audio_input.audio_buffer[resampled_indices]
        resampled_waveform = (resampled_waveform * 100) + (HEIGHT - self.visualizer_offset - 50)
        waveform_points = [(x, resampled_waveform[x]) for x in range(WIDTH)]
        if len(waveform_points) > 1:
            pygame.draw.aalines(screen, (200, 200, 200), False, waveform_points)

        with self.spotify.art_lock:
            if self.spotify.album_art:
                art_size = min(WIDTH // 4, 200)
                album_art_scaled = pygame.transform.smoothscale(self.spotify.album_art, (art_size, art_size))
                screen.blit(album_art_scaled, (WIDTH - art_size - 20, 20))

            title_surface = font.render(self.spotify.track_title, True, (255, 255, 255))
            screen.blit(title_surface, (20, 20))

            bar_x = 20
            bar_y = HEIGHT - self.visualizer_offset + 20
            bar_width = WIDTH - 40
            bar_height = 10
            pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height), border_radius=5)
            progress_ratio = self.spotify.progress_ms / self.spotify.duration_ms if self.spotify.duration_ms else 0
            pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, int(bar_width * progress_ratio), bar_height), border_radius=5)

        self.logo_angle += 0.2
        bass = np.mean(fft[:5])
        scale_factor = 1.0 + bass * 0.5
        scaled_logo = pygame.transform.rotozoom(self.logo, self.logo_angle, scale_factor)
        scaled_logo.set_alpha(30)
        logo_rect = scaled_logo.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(scaled_logo, logo_rect)

        # Button for UI, shape, color, and fulscreen mode
        buttons = [
            (pygame.Rect(20, HEIGHT - 105, 150, 40), "Color"),
            (pygame.Rect(20, HEIGHT - 60, 150, 40), "Shape"),
            (pygame.Rect(WIDTH - 170, HEIGHT - 60, 150, 40), "Fullscreen")
        ]
        for rect, label in buttons:
            color = (180, 180, 180) if rect.collidepoint(mouse_pos) else (120, 120, 120)
            pygame.draw.rect(screen, color, rect, border_radius=10)
            label_surface = font.render(label, True, (255, 255, 255))
            screen.blit(label_surface, (rect.x + 10, rect.y + 8))

        media_controls = [("|<<", "previous"), ("||", "play_pause"), (">>|", "next")]
        media_button_width = 80
        media_button_height = 40
        media_spacing = 20
        media_start_x = (WIDTH - (len(media_controls) * media_button_width + (len(media_controls) - 1) * media_spacing)) // 2
        media_button_y = HEIGHT - 90
        for i, (label, _) in enumerate(media_controls):
            x = media_start_x + i * (media_button_width + media_spacing)
            rect = pygame.Rect(x, media_button_y, media_button_width, media_button_height)
            color = (180, 180, 180) if rect.collidepoint(mouse_pos) else (120, 120, 120)
            pygame.draw.rect(screen, color, rect, border_radius=10)
            label_surface = font.render(label, True, (255, 255, 255))
            label_rect = label_surface.get_rect(center=(x + media_button_width // 2, media_button_y + media_button_height // 2))
            screen.blit(label_surface, label_rect)

# HOLY SHIT THIS WAS HORRIBLE TO WRITE, works well though :)

class FullProgram:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
        pygame.display.set_caption("Spotify Audio Visualizer")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Bahnschrift', 24, bold=True)
        self.running = True
        self.is_fullscreen = False

        self.spotify = SpotifyManager()
        self.audio_input = AudioInput()
        self.visualizer = Visualizer(self.audio_input, self.spotify)

    def run(self):
        while self.running:
            self.handle_events()
            self.visualizer.draw(self.screen, self.font)
            pygame.display.flip()
            self.clock.tick(FPS)

        self.audio_input.stream.stop()
        self.audio_input.stream.close()
        pygame.quit()

    def handle_events(self):
        WIDTH, HEIGHT = self.screen.get_size()
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if pygame.Rect(20, HEIGHT - 60, 150, 40).collidepoint(mouse_pos):
                    shape_order = ["rectangle", "circle", "triangle"]
                    idx = shape_order.index(self.visualizer.visualizer_shape)
                    self.visualizer.visualizer_shape = shape_order[(idx + 1) % len(shape_order)]
                elif pygame.Rect(20, HEIGHT - 105, 150, 40).collidepoint(mouse_pos):
                    self.visualizer.background_color = [np.random.randint(0, 256) for _ in range(3)]
                    self.visualizer.bar_color = [np.random.randint(0, 256) for _ in range(3)]
                elif pygame.Rect(WIDTH - 170, HEIGHT - 60, 150, 40).collidepoint(mouse_pos):
                    self.is_fullscreen = not self.is_fullscreen
                    if self.is_fullscreen:
                        self.screen = pygame.display.set_mode((1280, 720), pygame.FULLSCREEN)
                    else:
                        self.screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
                media_controls = [("|<<", "previous"), ("||", "play_pause"), (">>|", "next")]
                media_button_width = 80
                media_button_height = 40
                media_spacing = 20
                media_start_x = (WIDTH - (len(media_controls) * media_button_width + (len(media_controls) - 1) * media_spacing)) // 2
                media_button_y = HEIGHT - 90
                for i, (_, action) in enumerate(media_controls):
                    rect = pygame.Rect(media_start_x + i * (media_button_width + media_spacing), media_button_y,
                                       media_button_width, media_button_height)
                    if rect.collidepoint(mouse_pos):
                        self.spotify.control_playback(action)

# My brain hurts :(
    

if __name__ == '__main__':
    app = FullProgram()
    app.run()
