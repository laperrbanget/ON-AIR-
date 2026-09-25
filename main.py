import pygame
import sys
import os
import json
import random

# ============================================================
# DEAD AIR - Step 6: Intro, Endings, Polish
# ============================================================

WIDTH, HEIGHT = 1280, 720
FPS = 60

BLACK = (10, 10, 10)
DARK = (20, 20, 25)
AMBER = (255, 176, 0)
GREEN = (80, 255, 120)
YELLOW = (255, 220, 80)
RED = (255, 70, 70)
GRAY = (90, 90, 90)
WHITE = (220, 220, 220)

def resource_path(relative_path):
    """Resolve path — works both in dev and PyInstaller .exe."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


FONT_PATH = resource_path(os.path.join("assets", "fonts", "VT323.ttf"))
SONGS_PATH = resource_path(os.path.join("data", "songs.json"))
REQUESTS_PATH = resource_path(os.path.join("data", "requests.json"))
FLAVOR_PATH = resource_path(os.path.join("data", "chatflavor.json"))
REPLIES_PATH = resource_path(os.path.join("data", "replies.json"))
EVENTS_PATH = resource_path(os.path.join("data", "events.json"))
INTRO_PATH = resource_path(os.path.join("data", "intro.json"))
ENDINGS_PATH = resource_path(os.path.join("data", "endings.json"))

SFX_CLICK = resource_path(os.path.join("assets", "sfx", "click.wav"))
SFX_STATIC = resource_path(os.path.join("assets", "sfx", "static_loop.wav"))
SFX_HUM = resource_path(os.path.join("assets", "sfx", "hum.wav"))
SFX_SCREAM = resource_path(os.path.join("assets", "sfx", "scream.wav"))
SFX_WHISPER = resource_path(os.path.join("assets", "sfx", "whisper.wav"))
SFX_PHONE = resource_path(os.path.join("assets", "sfx", "phone_ring.wav"))
SFX_POSITIVE = resource_path(os.path.join("assets", "sfx", "positive.wav"))
SFX_NEGATIVE = resource_path(os.path.join("assets", "sfx", "negative.wav"))
SFX_REQUEST_IN = resource_path(os.path.join("assets", "sfx", "request_in.wav"))
SFX_GHOST_TRACK = resource_path(os.path.join("assets", "sfx", "ghost_track.wav"))
SFX_TICK = resource_path(os.path.join("assets", "sfx", "tick.wav"))

COUNTDOWN_DURATION = 5.0

GLITCH_TEXTS = [
    "TRACK 10: [unknown]",
    "87:43",
    "operator_03_final.wav",
    "signal drift detected",
    "…",
    "reel 2 / reel 2",
]


class DeadAirGame:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("ON AIR")
        self.clock = pygame.time.Clock()
        self.running = True

        # Font
        if os.path.exists(FONT_PATH):
            self.font_tiny = pygame.font.Font(FONT_PATH, 16)
            self.font_small = pygame.font.Font(FONT_PATH, 20)
            self.font_mid = pygame.font.Font(FONT_PATH, 32)
            self.font_big = pygame.font.Font(FONT_PATH, 56)
            self.font_count = pygame.font.Font(FONT_PATH, 120)
        else:
            self.font_tiny = pygame.font.SysFont("consolas", 14)
            self.font_small = pygame.font.SysFont("consolas", 18)
            self.font_mid = pygame.font.SysFont("consolas", 28)
            self.font_big = pygame.font.SysFont("consolas", 48)
            self.font_count = pygame.font.SysFont("consolas", 100)

        # Load data
        self.songs = self.load_json(SONGS_PATH, "songs")
        self.requests = self.load_json(REQUESTS_PATH, "requests")
        self.flavor = self.load_json(FLAVOR_PATH, "flavor")
        self.replies = self.load_json(REPLIES_PATH, "replies")
        self.events = self.load_json(EVENTS_PATH, "events")
        self.intro_data = self.load_json(INTRO_PATH, "lines")
        self.endings_data = self.load_json(ENDINGS_PATH, None)
        self.song_by_id = {s["id"]: s for s in self.songs}

        # Game state: "intro", "playing", "ending"
        self.state = "intro"

        # Intro state
        self.intro_index = 0
        self.intro_timer = 0.0
        self.intro_typing_index = 0
        self.intro_typing_timer = 0.0
        self.intro_typing_speed = 0.04
        self.intro_lines_rendered = []  # list of (text, color, size)
        self.intro_wait_input = False

        # Ending state
        self.ending_index = 0
        self.ending_timer = 0.0
        self.ending_typing_index = 0
        self.ending_typing_timer = 0.0
        self.ending_lines_rendered = []
        self.ending_wait_restart = False

        # Reset untuk restart
        self.reset_game_state()

        self.debug = True

    # --------------------------------------------------------
    def reset_game_state(self):
        """Reset semua state gameplay (bukan intro/ending)."""
        self.game_hour = 0.0
        self.hour_duration = 90.0

        self.happiness = 80

        self.chat_log = []
        self.current_request = None
        self.request_index = 0
        self.waiting_response = False

        self.countdown_timer = 0.0
        self.countdown_active = False
        self.countdown_last_sec = 0

        self.locked_song = None
        self.now_playing = None

        self.response_feedback = None
        self.feedback_timer = 0.0
        self.feedback_color = GREEN

        self.flavor_index = 0
        self.flavor_timer = 3.0
        self.flavor_paused = False
        self.flavor_pause_timer = 0.0

        self.pending_reply_backs = []

        self.chat_scroll = 0
        self.max_scroll = 0

        self.silence_mode = False
        self.silence_triggered = False

        self.closing_triggered = False
        self.game_over = False
        self.game_over_reason = None

        self.scanline_surface = self.make_scanline_surface()
        self.vignette_surface = self.make_vignette_surface()

        self.shake_intensity = 0.0
        self.shake_timer = 0.0

        self.glitch_timer = 0.0
        self.glitch_active = False
        self.glitch_cooldown = 999.0
        self.glitch_text = ""

        self.jumpscare_active = False
        self.jumpscare_timer = 0.0
        self.jumpscare_duration = 1.2

        self.darkness = 0.0

        self.corrupt_delay_timer = 0.0
        self.corrupt_delay_active = False

        self.audio_swap_timer = 0.0
        self.audio_swap_state = 0
        self.base_static_volume = 0.05
        self.base_music_volume = 0.5

        self.event_index = 0
        self.event_active = False
        self.event_state = ""
        self.event_timer = 0.0
        self.event_data = None
        self.event_step = 0
        self.event_chat_step = 0
        self.event_pause_duration = 0.0

        self.reply_index = 0
        self.active_reply = None
        self.reply_options_visible = False

        self.call_pause_active = False
        self.call_pause_timer = 0.0

        self.fast_forward = False
        self.slow_down = False
        self.paused = False

        # Audio channels
        self.static_channel = None
        self.hum_channel = None
        self.static_sound = None

    def setup_ambient_audio(self):
        try:
            if os.path.exists(SFX_STATIC):
                self.static_channel = pygame.mixer.Channel(1)
                self.static_sound = pygame.mixer.Sound(SFX_STATIC)
                self.static_sound.set_volume(self.base_static_volume)
                self.static_channel.play(self.static_sound, loops=-1)
            if os.path.exists(SFX_HUM):
                self.hum_channel = pygame.mixer.Channel(2)
                h = pygame.mixer.Sound(SFX_HUM)
                h.set_volume(0.08)
                self.hum_channel.play(h, loops=-1)
        except pygame.error as e:
            print(f"[audio] ambient gagal: {e}")

    def load_json(self, path, key):
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if key is None:
            return data
        return data[key]

    def make_scanline_surface(self):
        surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for y in range(0, HEIGHT, 3):
            pygame.draw.line(surf, (0, 0, 0, 40), (0, y), (WIDTH, y))
        return surf

    def make_vignette_surface(self):
        small = pygame.Surface((80, 45), pygame.SRCALPHA)
        for x in range(80):
            for y in range(45):
                dx = (x - 40) / 40
                dy = (y - 22.5) / 22.5
                dist = (dx * dx + dy * dy) ** 0.5
                if dist > 0.9:
                    a = int(min(60, (dist - 0.9) * 400))
                    small.set_at((x, y), (0, 0, 0, a))
        return pygame.transform.smoothscale(small, (WIDTH, HEIGHT))

    def play_sfx(self, path, volume=0.5):
        if not os.path.exists(path):
            return
        try:
            s = pygame.mixer.Sound(path)
            s.set_volume(volume)
            s.play()
        except pygame.error:
            pass

    def play_music(self, song):
        if song is None:
            return
        if song["id"] == "silence":
            pygame.mixer.music.stop()
            self.now_playing = song
            return

        path = song.get("file")
        if not path or not os.path.exists(path):
            self.now_playing = song
            return

        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.base_music_volume)
            pygame.mixer.music.play(-1)
            self.now_playing = song
        except pygame.error as e:
            print(f"[music] gagal play {path}: {e}")
            self.now_playing = song

    # --------------------------------------------------------
    def corrupt_text(self, text, level):
        if level <= 0:
            return text
        chars = list(text)
        glitch_chars = "▓▒░█▄▀■□▪▫"
        if level == 1:
            for _ in range(random.randint(1, 2)):
                if chars:
                    i = random.randint(0, len(chars) - 1)
                    if chars[i] not in " \n":
                        chars[i] = random.choice(glitch_chars)
        elif level == 2:
            text = text.lower()
            chars = list(text)
            for _ in range(random.randint(3, 4)):
                if chars:
                    i = random.randint(0, len(chars) - 1)
                    if chars[i] not in " \n":
                        chars[i] = random.choice(glitch_chars)
        elif level >= 3:
            text = text.lower()
            chars = list(text)
            for _ in range(random.randint(5, 8)):
                if chars:
                    i = random.randint(0, len(chars) - 1)
                    if chars[i] not in " \n":
                        chars[i] = random.choice(glitch_chars)
            for _ in range(random.randint(2, 3)):
                i = random.randint(0, len(chars))
                chars.insert(i, random.choice(glitch_chars))
        return "".join(chars)

    # --------------------------------------------------------
    # INTRO
    # --------------------------------------------------------
    def update_intro(self, dt):
        if self.intro_wait_input:
            return
        if self.intro_index >= len(self.intro_data):
            return

        item = self.intro_data[self.intro_index]
        text = item["text"]

        # Typing effect
        if self.intro_typing_index < len(text):
            self.intro_typing_timer += dt
            if self.intro_typing_timer >= self.intro_typing_speed:
                self.intro_typing_timer = 0.0
                self.intro_typing_index += 1
                # Tick sound tiap 3 char
                if self.intro_typing_index % 3 == 0:
                    self.play_sfx(SFX_TICK, 0.15)
        else:
            # Selesai ngetik, tunggu delay
            self.intro_timer += dt
            if self.intro_timer >= item.get("delay", 0.5):
                # Commit line ke rendered
                self.intro_lines_rendered.append({
                    "text": text,
                    "color": item.get("color", WHITE),
                    "size": item.get("size", "small")
                })
                self.intro_index += 1
                self.intro_typing_index = 0
                self.intro_timer = 0.0

                # Kalau wait_input, stop
                if item.get("wait_input"):
                    self.intro_wait_input = True

    def draw_intro(self):
        self.screen.fill(BLACK)

        # Render lines yang udah selesai
        y = 80
        for line in self.intro_lines_rendered:
            font = self.get_intro_font_by_size(line["size"])
            txt = font.render(line["text"], True, tuple(line["color"]))
            self.screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, y))
            y += txt.get_height() + 10

        # Render line yang lagi diketik
        if not self.intro_wait_input and self.intro_index < len(self.intro_data):
            item = self.intro_data[self.intro_index]
            text = item["text"][:self.intro_typing_index]
            font = self.get_intro_font_by_size(item.get("size", "small"))
            txt = font.render(text, True, tuple(item.get("color", WHITE)))
            self.screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, y))

        # Scanline + vignette
        self.screen.blit(self.scanline_surface, (0, 0))
        self.screen.blit(self.vignette_surface, (0, 0))

    def get_intro_font_by_size(self, size):
        """Font khusus intro — sedikit lebih gede dari gameplay."""
        if not os.path.exists(FONT_PATH):
            # Fallback kalau font ga ada
            if size == "big":
                return pygame.font.SysFont("consolas", 72)
            elif size == "mid":
                return pygame.font.SysFont("consolas", 38)
            else:
                return pygame.font.SysFont("consolas", 26)
        if size == "big":
            return pygame.font.Font(FONT_PATH, 72)
        elif size == "mid":
            return pygame.font.Font(FONT_PATH, 38)
        else:
            return pygame.font.Font(FONT_PATH, 26)

    def get_font_by_size(self, size):
        if size == "big":
            return self.font_big
        elif size == "mid":
            return self.font_mid
        else:
            return self.font_small

    # --------------------------------------------------------
    # ENDING
    # --------------------------------------------------------
    def start_ending(self, reason):
        self.state = "ending"
        self.ending_reason = reason
        self.ending_index = 0
        self.ending_timer = 0.0
        self.ending_typing_index = 0
        self.ending_typing_timer = 0.0
        self.ending_lines_rendered = []
        self.ending_wait_restart = False

        # Stop musik & ambient
        pygame.mixer.music.stop()
        if self.static_channel:
            self.static_channel.stop()
        if self.hum_channel:
            self.hum_channel.stop()

    def update_ending(self, dt):
        if self.ending_wait_restart:
            return
        ending = self.endings_data.get(self.ending_reason, {})
        lines = ending.get("lines", [])
        if self.ending_index >= len(lines):
            self.ending_wait_restart = True
            return

        item = lines[self.ending_index]
        text = item["text"]

        if self.ending_typing_index < len(text):
            self.ending_typing_timer += dt
            if self.ending_typing_timer >= 0.04:
                self.ending_typing_timer = 0.0
                self.ending_typing_index += 1
        else:
            self.ending_timer += dt
            if self.ending_timer >= item.get("delay", 1.5):
                self.ending_lines_rendered.append({
                    "text": text,
                    "color": item.get("color", WHITE)
                })
                self.ending_index += 1
                self.ending_typing_index = 0
                self.ending_timer = 0.0

    def draw_ending(self):
        self.screen.fill(BLACK)

        ending = self.endings_data.get(self.ending_reason, {})
        title = ending.get("title", "END")
        title_color = tuple(ending.get("title_color", [220, 220, 220]))

        # Title di atas
        title_surf = self.font_big.render(title, True, title_color)
        self.screen.blit(
            title_surf,
            (WIDTH // 2 - title_surf.get_width() // 2, 80)
        )

        # Lines
        y = 220
        for line in self.ending_lines_rendered:
            txt = self.font_mid.render(line["text"], True, tuple(line["color"]))
            self.screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, y))
            y += txt.get_height() + 12

        # Line yang lagi diketik
        if not self.ending_wait_restart:
            lines = ending.get("lines", [])
            if self.ending_index < len(lines):
                item = lines[self.ending_index]
                text = item["text"][:self.ending_typing_index]
                txt = self.font_mid.render(text, True, tuple(item.get("color", WHITE)))
                self.screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, y))

        # Restart prompt
        if self.ending_wait_restart:
            prompt1 = self.font_small.render("[SPACE] play again", True, AMBER)
            prompt2 = self.font_small.render("[ESC] quit", True, GRAY)
            self.screen.blit(
                prompt1,
                (WIDTH // 2 - prompt1.get_width() // 2, HEIGHT - 120)
            )
            self.screen.blit(
                prompt2,
                (WIDTH // 2 - prompt2.get_width() // 2, HEIGHT - 90)
            )

        self.screen.blit(self.scanline_surface, (0, 0))
        self.screen.blit(self.vignette_surface, (0, 0))

    # --------------------------------------------------------
    # GAMEPLAY (sama kayak sebelumnya)
    # --------------------------------------------------------
    def update(self, dt):
        if self.game_over:
            if self.jumpscare_active:
                self.jumpscare_timer -= dt
                if self.jumpscare_timer <= 0:
                    self.jumpscare_active = False
                    self.start_ending(self.game_over_reason)
            return

        self.game_hour += dt / self.hour_duration
        if self.game_hour >= 6.0:
            self.game_hour = 6.0
            self.trigger_ending("survived")
            return

        self.darkness = min(0.4, self.game_hour / 6.0 * 0.4)

        if self.shake_timer > 0:
            self.shake_timer -= dt
            self.shake_intensity *= 0.92
        else:
            self.shake_intensity = 0.0

        if self.feedback_timer > 0:
            self.feedback_timer -= dt
            if self.feedback_timer <= 0:
                self.response_feedback = None

        if self.countdown_active:
            self.countdown_timer -= dt
            current_sec = max(0, int(self.countdown_timer) + 1)
            if current_sec != self.countdown_last_sec and current_sec > 0:
                self.countdown_last_sec = current_sec
                self.play_sfx(SFX_TICK, 0.4)
            if self.countdown_timer <= 0:
                self.countdown_timeout()

        if self.corrupt_delay_active:
            self.corrupt_delay_timer -= dt
            if self.corrupt_delay_timer <= 0:
                self.corrupt_delay_active = False

        if self.call_pause_active:
            self.call_pause_timer -= dt
            if self.call_pause_timer <= 0:
                self.call_pause_active = False
                self.add_chat("sorry. wrong number.", RED, username="unknown")
                self.happiness = max(0, self.happiness - 3)
            return

        if self.event_active:
            self.update_event(dt)
            return

        if 5.0 <= self.game_hour < 5.5:
            if not self.silence_triggered:
                self.silence_triggered = True
                self.silence_mode = True
                self.happiness = max(0, self.happiness - 5)
                self.add_chat("[SIGNAL LOST]", GRAY, username="system")
                pygame.mixer.music.stop()
        else:
            self.silence_mode = False

        if not self.silence_mode and self.game_hour >= 2.5:
            self.glitch_cooldown -= dt
            if self.glitch_cooldown <= 0 and not self.glitch_active:
                self.glitch_active = True
                self.glitch_timer = 0.3 if self.game_hour < 3.5 else 0.5
                base_cd = 120.0 - (self.game_hour - 2.5) * 22.0
                self.glitch_cooldown = max(20.0, base_cd + random.uniform(-5, 10))
                self.glitch_text = random.choice(GLITCH_TEXTS)
            if self.glitch_active:
                self.glitch_timer -= dt
                if self.glitch_timer <= 0:
                    self.glitch_active = False

        self.apply_audio_distortion(dt)

        if not self.game_over and not self.silence_mode and self.flavor:
            if self.flavor_paused:
                self.flavor_pause_timer -= dt
                if self.flavor_pause_timer <= 0:
                    self.flavor_paused = False
                    self.flavor_timer = 2.0
            else:
                self.flavor_timer -= dt
                if self.flavor_timer <= 0:
                    if self.flavor_index < len(self.flavor):
                        item = self.flavor[self.flavor_index]
                        self.flavor_index += 1
                        if item["type"] == "chat":
                            self.add_chat(item["text"], item["color"], username=item["username"])
                            self.flavor_timer = item.get("delay", 2.5)
                        elif item["type"] == "pause":
                            self.flavor_paused = True
                            self.flavor_pause_timer = item.get("duration", 5.0)

        if self.pending_reply_backs:
            for rb in self.pending_reply_backs[:]:
                rb["timer"] -= dt
                if rb["timer"] <= 0:
                    self.add_chat(rb["data"]["text"], rb["data"]["color"], username=rb["data"]["username"])
                    self.pending_reply_backs.remove(rb)

        if not self.waiting_response and not self.silence_mode:
            if self.reply_index < len(self.replies) and not self.active_reply:
                r = self.replies[self.reply_index]
                if self.game_hour >= r["hour"]:
                    self.spawn_reply(r)

        if not self.waiting_response and not self.silence_mode:
            if self.event_index < len(self.events) and not self.event_active:
                e = self.events[self.event_index]
                if self.game_hour >= e["hour"]:
                    self.start_event(e)

        if not self.waiting_response and not self.silence_mode and not self.game_over:
            if self.request_index < len(self.requests):
                req = self.requests[self.request_index]
                if self.game_hour >= req["hour"]:
                    self.spawn_request(req)

        if self.happiness <= 0 and not self.game_over:
            self.trigger_ending("off_air")

    def apply_audio_distortion(self, dt):
        if self.static_sound and self.static_channel:
            intensity = 1.0 - (self.happiness / 100)
            new_vol = self.base_static_volume + (intensity * 0.2)
            self.static_sound.set_volume(min(0.25, new_vol))

        if self.now_playing and self.now_playing["id"] != "silence":
            intensity = 1.0 - (self.happiness / 100)
            new_music_vol = self.base_music_volume * (1.0 - intensity * 0.7)
            try:
                pygame.mixer.music.set_volume(max(0.05, new_music_vol))
            except pygame.error:
                pass

        if self.game_hour >= 3.0 and self.static_sound:
            swap_interval = 5.0 if self.game_hour < 4.5 else 2.5
            self.audio_swap_timer += dt
            if self.audio_swap_timer >= swap_interval:
                self.audio_swap_timer = 0
                self.audio_swap_state = 1 - self.audio_swap_state
                if self.audio_swap_state == 1:
                    self.static_channel.set_volume(0.03, 0.25)
                else:
                    self.static_channel.set_volume(0.25, 0.03)

    def spawn_reply(self, r):
        self.active_reply = r
        self.reply_index += 1
        self.reply_options_visible = True
        color = tuple(r["color"])
        self.add_chat(r["text"], color, username=r["username"])

    def resolve_reply(self, key):
        if not self.active_reply:
            return
        r = self.active_reply
        for opt in r["options"]:
            if opt["key"] == key:
                self.add_chat(opt["text"], AMBER, username="you")
                self.happiness = max(0, min(100, self.happiness + opt["delta"]))
                if opt["delta"] > 0:
                    self.response_feedback = f"+{opt['delta']}"
                    self.feedback_color = GREEN
                    self.play_sfx(SFX_POSITIVE, 0.3)
                elif opt["delta"] < 0:
                    self.response_feedback = f"{opt['delta']}"
                    self.feedback_color = RED
                    self.play_sfx(SFX_NEGATIVE, 0.4)
                self.feedback_timer = 1.5
                self.play_sfx(SFX_CLICK, 0.3)
                rb = opt.get("reply_back")
                if rb:
                    self.pending_reply_backs.append({
                        "timer": rb.get("delay", 4.0),
                        "data": rb
                    })
                break
        self.active_reply = None
        self.reply_options_visible = False

    def start_event(self, e):
        self.event_data = e
        self.event_index += 1
        self.event_active = True
        self.event_state = "chat"
        self.event_chat_step = 0
        self.event_timer = 0.0
        self.event_pause_duration = e.get("pause_duration", 3.0)

    def update_event(self, dt):
        e = self.event_data
        if not e:
            self.event_active = False
            return

        if e["type"] == "erase":
            erase_count = e.get("erase_count", 10)
            if self.event_state == "chat":
                self.event_timer += dt
                if self.event_timer >= 0.4 and len(self.chat_log) > 0 and self.event_chat_step < erase_count:
                    self.chat_log.pop()
                    self.event_chat_step += 1
                    self.event_timer = 0.0
                if self.event_chat_step >= erase_count:
                    self.event_state = "pause"
                    self.event_timer = 0.0
            elif self.event_state == "pause":
                self.event_timer += dt
                if self.event_timer >= self.event_pause_duration:
                    self.event_state = "after"
                    self.event_chat_step = 0
                    self.event_timer = 0.0
            elif self.event_state == "after":
                self.event_timer += dt
                if self.event_timer >= 0.8:
                    if self.event_chat_step < len(e["after_chat"]):
                        c = e["after_chat"][self.event_chat_step]
                        self.add_chat(c["text"], c["color"], username=c["username"])
                        self.event_chat_step += 1
                        self.event_timer = 0.0
                    else:
                        self.happiness = max(0, self.happiness + e["happiness_delta"])
                        self.end_event()
            return

        if e["type"] == "ghost_track":
            if self.event_state == "chat":
                if self.event_chat_step == 0:
                    pygame.mixer.music.stop()
                    self.play_sfx(SFX_GHOST_TRACK, 0.7)
                    self.now_playing = {
                        "title": e["ghost_title"],
                        "color": [200, 60, 60],
                        "desc": "",
                        "id": "ghost",
                        "mood": "none"
                    }
                    self.event_timer = 0.0
                    self.event_chat_step = 1
                self.event_timer += dt
                if self.event_timer >= e.get("ghost_sfx_duration", 5.0):
                    self.event_state = "pause"
                    self.event_timer = 0.0
            elif self.event_state == "pause":
                self.event_timer += dt
                if self.event_timer >= self.event_pause_duration:
                    if self.locked_song:
                        self.play_music(self.locked_song)
                    self.event_state = "after"
                    self.event_chat_step = 0                   
                    self.event_timer = 0.0
            elif self.event_state == "after":
                self.event_timer += dt
                if self.event_timer >= 0.8:
                    if self.event_chat_step < len(e["chat_lines"]):
                        c = e["chat_lines"][self.event_chat_step]
                        self.add_chat(c["text"], c["color"], username=c["username"])
                        self.event_chat_step += 1
                        self.event_timer = 0.0
                    else:
                        self.happiness = max(0, self.happiness + e["happiness_delta"])
                        self.end_event()
            return

        if self.event_state == "chat":
            self.event_timer += dt
            if self.event_timer >= 0.5:
                if self.event_chat_step < len(e["chat_lines"]):
                    c = e["chat_lines"][self.event_chat_step]
                    self.add_chat(c["text"], c["color"], username=c["username"])
                    self.event_chat_step += 1
                    self.event_timer = 0.0
                else:
                    self.event_state = "pause"
                    self.event_timer = 0.0
        elif self.event_state == "pause":
            self.event_timer += dt
            if self.event_timer >= self.event_pause_duration:
                self.event_state = "after"
                self.event_chat_step = 0
                self.event_timer = 0.0
        elif self.event_state == "after":
            self.event_timer += dt
            if self.event_timer >= 0.8:
                if self.event_chat_step < len(e["after_chat"]):
                    c = e["after_chat"][self.event_chat_step]
                    self.add_chat(c["text"], c["color"], username=c["username"])
                    self.event_chat_step += 1
                    self.event_timer = 0.0
                else:
                    self.happiness = max(0, self.happiness + e["happiness_delta"])
                    self.end_event()

    def end_event(self):
        self.event_active = False
        self.event_data = None
        self.event_state = ""

    def spawn_request(self, req):
        self.current_request = req
        self.request_index += 1

        if req.get("event") == "phone_call":
            self.call_pause_active = True
            self.call_pause_timer = 4.0
            self.add_chat(req["pre_text"], RED, username="system")
            self.shake_intensity = 4.0
            self.shake_timer = 0.5
            self.play_sfx(SFX_PHONE, 0.7)
            return

        if req.get("closing"):
            self.add_chat(req["text"], WHITE, username=req.get("username", "unknown"))
            self.current_request = None
            self.closing_triggered = True
            self.add_chat("[END OF BROADCAST]", GRAY, username="system")
            return

        color = self.get_chat_color(req["corruption"])
        self.add_chat(req["text"], color, username=req.get("username", "anon"))

        self.play_sfx(SFX_REQUEST_IN, 0.5)

        self.shake_intensity = 2.0
        self.shake_timer = 0.3

        self.waiting_response = True
        self.countdown_active = True
        self.countdown_timer = COUNTDOWN_DURATION
        self.countdown_last_sec = COUNTDOWN_DURATION

        if req.get("corruption", 0) > 0:
            self.corrupt_delay_active = True
            self.corrupt_delay_timer = 0.5

    def add_chat(self, text, color=WHITE, username="anon"):
        jam = int(self.game_hour)
        menit = int((self.game_hour - jam) * 60)
        timestamp = f"{jam:02d}:{menit:02d}"
        self.chat_log.append({
            "time": timestamp,
            "username": username,
            "text": text,
            "color": color
        })
        if len(self.chat_log) > 50:
            self.chat_log = self.chat_log[-50:]

    def get_chat_color(self, corruption):
        if corruption == 0:
            return WHITE
        elif corruption == 1:
            return (200, 200, 180)
        elif corruption == 2:
            return (255, 200, 140)
        else:
            return (255, 140, 120)

    def countdown_timeout(self):
        if not self.waiting_response:
            return
        self.happiness = max(0, min(100, self.happiness - 10))
        self.response_feedback = "-10"
        self.feedback_color = RED
        self.feedback_timer = 1.5
        self.play_sfx(SFX_NEGATIVE, 0.6)
        self.add_chat("[no response]", GRAY, username="system")
        self.shake_intensity = 5.0
        self.shake_timer = 0.5
        self.waiting_response = False
        self.countdown_active = False
        self.current_request = None

    def select_song(self, song_index):
        if not self.waiting_response or not self.current_request:
            return
        if song_index >= len(self.songs):
            return
        song = self.songs[song_index]
        req = self.current_request
        delta = self.calculate_delta(req, song)
        self.happiness = max(0, min(100, self.happiness + delta))

        if delta > 0:
            self.response_feedback = f"+{delta}"
            self.feedback_color = GREEN
            self.play_sfx(SFX_POSITIVE, 0.4)
        elif delta < 0:
            self.response_feedback = f"{delta}"
            self.feedback_color = RED
            self.play_sfx(SFX_NEGATIVE, 0.5)
        else:
            self.response_feedback = "0"
            self.feedback_color = GRAY
        self.feedback_timer = 1.5

        self.play_sfx(SFX_CLICK, 0.3)
        self.play_music(song)
        self.locked_song = song

        self.waiting_response = False
        self.countdown_active = False
        self.current_request = None
        self.corrupt_delay_active = False

    def calculate_delta(self, req, song):
        if req.get("trap"):
            if song["id"] == "silence" and req.get("silence_neutral"):
                return 0
            return req["delta"]
        if req.get("correct") == ["__any__"]:
            if song["id"] == "silence":
                return req.get("silence_bonus", req["delta"])
            return req["delta"]
        if song["id"] in req.get("correct", []):
            if song["id"] == "silence" and req.get("silence_bonus"):
                return req["silence_bonus"]
            return req["delta"]
        return req.get("wrong_delta", -10)

    def trigger_ending(self, reason):
        self.game_over = True
        self.game_over_reason = reason
        if reason == "off_air":
            self.jumpscare_active = True
            self.jumpscare_timer = self.jumpscare_duration
            self.play_sfx(SFX_SCREAM, 0.8)
        else:
            self.start_ending(reason)

    # --------------------------------------------------------
    # DRAW
    # --------------------------------------------------------
    def draw(self):
        if self.state == "intro":
            self.draw_intro()
            pygame.display.flip()
            return

        if self.state == "ending":
            self.draw_ending()
            pygame.display.flip()
            return

        # Gameplay
        shake_x, shake_y = 0, 0
        if self.shake_intensity > 0.1:
            shake_x = random.randint(-int(self.shake_intensity), int(self.shake_intensity))
            shake_y = random.randint(-int(self.shake_intensity), int(self.shake_intensity))

        render_surf = pygame.Surface((WIDTH, HEIGHT))
        render_surf.fill(BLACK)

        old_screen = self.screen
        self.screen = render_surf

        header = pygame.Rect(0, 0, WIDTH, 60)
        pygame.draw.rect(self.screen, DARK, header)
        pygame.draw.line(self.screen, AMBER, (0, 60), (WIDTH, 60), 2)

        title = self.font_mid.render("ON AIR", True, AMBER)
        self.screen.blit(title, (30, 14))

        jam = int(self.game_hour)
        menit = int((self.game_hour - jam) * 60)
        clock_text = f"{jam:02d}:{menit:02d}"
        clock_surf = self.font_mid.render(clock_text, True, WHITE)
        self.screen.blit(clock_surf, (WIDTH - 220, 14))

        if self.paused:
            speed_text = "[ PAUSED ]"
            speed_color = RED
        elif self.fast_forward:
            speed_text = "[ >> 2x ]"
            speed_color = AMBER
        elif self.slow_down:
            speed_text = "[ > 0.5x ]"
            speed_color = GRAY
        else:
            speed_text = "[ > 1x ]"
            speed_color = (100, 100, 100)
        speed_surf = self.font_small.render(speed_text, True, speed_color)
        self.screen.blit(speed_surf, (WIDTH - 130, 22))

        self.draw_monitor()
        self.draw_chat()
        self.draw_happiness()
        self.draw_song_buttons()

        if self.countdown_active:
            self.draw_countdown()

        if self.response_feedback and self.feedback_timer > 0:
            fb = self.font_big.render(self.response_feedback, True, self.feedback_color)
            self.screen.blit(fb, (WIDTH // 2 - 30, 300))

        self.screen = old_screen

        self.screen.fill(BLACK)
        self.screen.blit(render_surf, (shake_x, shake_y))

        if self.darkness > 0:
            dark_surf = pygame.Surface((WIDTH, HEIGHT))
            dark_surf.set_alpha(int(self.darkness * 255))
            dark_surf.fill((0, 0, 0))
            self.screen.blit(dark_surf, (0, 0))

        self.draw_block_glitch()
        self.screen.blit(self.scanline_surface, (0, 0))
        self.screen.blit(self.vignette_surface, (0, 0))

        if self.glitch_active:
            self.draw_glitch()

        if self.jumpscare_active:
            self.draw_jumpscare()

        if self.paused:
            pause_surf = pygame.Surface((WIDTH, HEIGHT))
            pause_surf.set_alpha(180)
            pause_surf.fill(BLACK)
            self.screen.blit(pause_surf, (0, 0))
            pause_txt = self.font_big.render("PAUSED", True, WHITE)
            self.screen.blit(
                pause_txt,
                (WIDTH // 2 - pause_txt.get_width() // 2,
                 HEIGHT // 2 - pause_txt.get_height() // 2)
            )
            hint = self.font_small.render("press SPACE to resume", True, GRAY)
            self.screen.blit(
                hint,
                (WIDTH // 2 - hint.get_width() // 2,
                 HEIGHT // 2 + 60)
            )

        if self.debug and not self.game_over:
            speed_status = ""
            if self.fast_forward:
                speed_status = " [FF]"
            elif self.slow_down:
                speed_status = " [SLOW]"
            elif self.paused:
                speed_status = " [PAUSED]"
            dbg = self.font_tiny.render(
                f"DEBUG{speed_status}: [Shift+←/→] jam  [Shift+↑/↓] happy  [1-9] lagu  [Q/W/E] reply  [TAB] ff  [SHIFT] slow  [SPACE] pause  [ESC] keluar",
                True, GRAY
            )
            self.screen.blit(dbg, (20, HEIGHT - 18))

        pygame.display.flip()

    def draw_block_glitch(self):
        if self.game_hour < 2.5:
            return
        time_intensity = min(1.0, (self.game_hour - 2.5) / 3.5)
        happy_intensity = 1.0 - (self.happiness / 100)
        intensity = (time_intensity * 0.4) + (happy_intensity * 0.6)
        if intensity < 0.2:
            return
        snapshot = self.screen.copy()
        num_blocks = int(1 + intensity * 5)
        for _ in range(num_blocks):
            block_h = random.randint(6, 20)
            block_y = random.randint(0, HEIGHT - block_h)
            offset_x = random.randint(-12, 12)
            block = snapshot.subsurface(pygame.Rect(0, block_y, WIDTH, block_h)).copy()
            self.screen.blit(block, (offset_x, block_y))
        num_lines = int(1 + intensity * 3)
        for _ in range(num_lines):
            line_y = random.randint(0, HEIGHT - 1)
            offset_x = random.randint(-40, 40)
            color = (random.randint(150, 255), random.randint(150, 255), random.randint(150, 255))
            pygame.draw.line(self.screen, color, (offset_x, line_y), (offset_x + WIDTH, line_y), 1)

    def draw_glitch(self):
        snapshot = self.screen.copy()
        for _ in range(8):
            block_h = random.randint(20, 60)
            block_y = random.randint(80, 80 + 480 - block_h)
            offset_x = random.randint(-40, 40)
            block = snapshot.subsurface(pygame.Rect(0, block_y, WIDTH, block_h)).copy()
            self.screen.blit(block, (offset_x, block_y))
        small = pygame.Surface((80, 45))
        for _ in range(300):
            x = random.randint(0, 79)
            y = random.randint(0, 44)
            c = random.randint(0, 255)
            small.set_at((x, y), (c, c, c))
        scaled = pygame.transform.scale(small, (760, 480))
        scaled.set_alpha(100)
        self.screen.blit(scaled, (20, 80))
        monitor_center_x = 20 + 760 // 2
        monitor_center_y = 80 + 480 // 2
        txt = self.font_mid.render(self.glitch_text, True, RED)
        self.screen.blit(
            txt,
            (monitor_center_x - txt.get_width() // 2,
             monitor_center_y - txt.get_height() // 2)
        )

    def draw_jumpscare(self):
        flash = pygame.Surface((WIDTH, HEIGHT))
        flash.fill((255, 255, 255))
        flash.set_alpha(200)
        self.screen.blit(flash, (0, 0))
        small = pygame.Surface((160, 90))
        for _ in range(2000):
            x = random.randint(0, 159)
            y = random.randint(0, 89)
            c = random.randint(0, 255)
            small.set_at((x, y), (c, c, c))
        scaled = pygame.transform.scale(small, (WIDTH, HEIGHT))
        scaled.set_alpha(220)
        self.screen.blit(scaled, (0, 0))
        txt = self.font_big.render("OFF-AIR", True, RED)
        self.screen.blit(
            txt,
            (WIDTH // 2 - txt.get_width() // 2,
             HEIGHT // 2 - txt.get_height() // 2)
        )

    def draw_countdown(self):
        secs = max(0, int(self.countdown_timer) + 1)
        txt = self.font_count.render(str(secs), True, WHITE)
        monitor_center_x = 20 + 760 // 2
        monitor_center_y = 80 + 480 // 2
        self.screen.blit(
            txt,
            (monitor_center_x - txt.get_width() // 2,
             monitor_center_y - txt.get_height() // 2)
        )

    def draw_monitor(self):
        monitor_rect = pygame.Rect(20, 80, 760, 480)
        pygame.draw.rect(self.screen, DARK, monitor_rect)

        # Border tebal (3px) warna amber gelap
        pygame.draw.rect(self.screen, (120, 90, 20), monitor_rect, 3)
        # Inner border tipis (1px) lebih terang
        inner_rect = monitor_rect.inflate(-6, -6)
        pygame.draw.rect(self.screen, (60, 45, 10), inner_rect, 1)

        # Corner accents (4 sudut kecil)
        corner_len = 12
        corner_color = AMBER
        # Top-left
        pygame.draw.line(self.screen, corner_color, (monitor_rect.x, monitor_rect.y), (monitor_rect.x + corner_len, monitor_rect.y), 2)
        pygame.draw.line(self.screen, corner_color, (monitor_rect.x, monitor_rect.y), (monitor_rect.x, monitor_rect.y + corner_len), 2)
        # Top-right
        pygame.draw.line(self.screen, corner_color, (monitor_rect.right, monitor_rect.y), (monitor_rect.right - corner_len, monitor_rect.y), 2)
        pygame.draw.line(self.screen, corner_color, (monitor_rect.right, monitor_rect.y), (monitor_rect.right, monitor_rect.y + corner_len), 2)
        # Bottom-left
        pygame.draw.line(self.screen, corner_color, (monitor_rect.x, monitor_rect.bottom), (monitor_rect.x + corner_len, monitor_rect.bottom), 2)
        pygame.draw.line(self.screen, corner_color, (monitor_rect.x, monitor_rect.bottom), (monitor_rect.x, monitor_rect.bottom - corner_len), 2)
        # Bottom-right
        pygame.draw.line(self.screen, corner_color, (monitor_rect.right, monitor_rect.bottom), (monitor_rect.right - corner_len, monitor_rect.bottom), 2)
        pygame.draw.line(self.screen, corner_color, (monitor_rect.right, monitor_rect.bottom), (monitor_rect.right, monitor_rect.bottom - corner_len), 2)

        mon_label = self.font_small.render("MONITOR", True, GRAY)
        self.screen.blit(mon_label, (monitor_rect.x + 10, monitor_rect.y + 8))

        if self.call_pause_active:
            txt = self.font_big.render("[INCOMING CALL]", True, RED)
            self.screen.blit(
                txt,
                (monitor_rect.centerx - txt.get_width() // 2,
                 monitor_rect.centery - txt.get_height() // 2)
            )
            return

        if self.now_playing and not self.silence_mode:
            color = tuple(self.now_playing["color"])
            txt = self.font_big.render(self.now_playing["title"].upper(), True, color)
            self.screen.blit(
                txt,
                (monitor_rect.centerx - txt.get_width() // 2,
                 monitor_rect.centery - 60)
            )
            desc = self.font_small.render(self.now_playing.get("desc", ""), True, GRAY)
            self.screen.blit(
                desc,
                (monitor_rect.centerx - desc.get_width() // 2,
                 monitor_rect.centery + 20)
            )
            if not self.silence_mode and self.now_playing and self.now_playing["id"] != "silence":
                for i in range(20):
                    bh = random.randint(10, 60)
                    bx = monitor_rect.x + 60 + i * 32
                    by = monitor_rect.bottom - 80
                    pygame.draw.rect(self.screen, color, (bx, by - bh, 24, bh))
        else:
            if self.silence_mode:
                txt = self.font_big.render("[ SILENCE ]", True, GRAY)
            else:
                txt = self.font_big.render("[ NO SIGNAL ]", True, AMBER)
            self.screen.blit(
                txt,
                (monitor_rect.centerx - txt.get_width() // 2,
                 monitor_rect.centery - 30)
            )

    def draw_chat(self):
        chat_rect = pygame.Rect(800, 80, 460, 480)
        pygame.draw.rect(self.screen, DARK, chat_rect)
        pygame.draw.rect(self.screen, GRAY, chat_rect, 2)

        chat_label = self.font_small.render("CHAT", True, GRAY)
        self.screen.blit(chat_label, (chat_rect.x + 10, chat_rect.y + 8))

        inner_x = chat_rect.x + 12
        inner_y = chat_rect.y + 40
        inner_w = chat_rect.width - 24
        inner_h = chat_rect.height - 50 - (80 if self.reply_options_visible else 0)

        clip = self.screen.subsurface(pygame.Rect(inner_x, inner_y, inner_w, inner_h))

        line_h = 20
        entries_height = []
        total_h = 0
        for entry in self.chat_log:
            lines = entry["text"].split("\n")
            h = line_h * (len(lines) + 1) + 4
            entries_height.append(h)
            total_h += h

        self.max_scroll = max(0, total_h - inner_h)
        self.chat_scroll = max(0, min(self.chat_scroll, self.max_scroll))

        start_y = inner_h - total_h + self.chat_scroll
        y = start_y

        reply_username = None
        if self.active_reply:
            reply_username = self.active_reply["username"]

        for entry, h in zip(self.chat_log, entries_height):
            uname = self.font_small.render(entry["username"], True, tuple(entry.get("color", GRAY)))
            ts = self.font_small.render(entry["time"], True, (60, 60, 60))
            is_reply_target = reply_username and entry["username"] == reply_username
            if -line_h <= y <= inner_h:
                clip.blit(uname, (0, y))
                clip.blit(ts, (inner_w - ts.get_width(), y))
            corrupt_level = 0
            if self.current_request and entry["text"] == self.current_request["text"]:
                if not self.corrupt_delay_active:
                    corrupt_level = self.current_request.get("corruption", 0)
            lines = entry["text"].split("\n")
            for i, line in enumerate(lines):
                display_line = self.corrupt_text(line, corrupt_level) if corrupt_level > 0 else line
                txt = self.font_small.render(display_line, True, entry["color"])
                ty = y + line_h * (i + 1)
                if -line_h <= ty <= inner_h:
                    clip.blit(txt, (10, ty))
                    if is_reply_target and i == len(lines) - 1:
                        underline_y = ty + txt.get_height() - 2
                        pygame.draw.line(
                            clip, tuple(entry.get("color", GRAY)),
                            (10, underline_y), (10 + txt.get_width(), underline_y), 1
                        )
            y += h

        if self.reply_options_visible and self.active_reply:
            opts_y = chat_rect.bottom - 90
            label = self.font_small.render("─── REPLY ───", True, AMBER)
            self.screen.blit(label, (chat_rect.x + 15, opts_y))
            for i, opt in enumerate(self.active_reply["options"]):
                line = f"[{opt['key']}] {opt['text']}"
                txt = self.font_small.render(line, True, WHITE)
                self.screen.blit(txt, (chat_rect.x + 20, opts_y + 22 + i * 22))

    def draw_happiness(self):
        bar_x, bar_y = 20, 580
        bar_w, bar_h = WIDTH - 40, 30
        pygame.draw.rect(self.screen, DARK, (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(self.screen, GRAY, (bar_x, bar_y, bar_w, bar_h), 2)
        fill_w = int((self.happiness / 100) * (bar_w - 4))
        if self.happiness > 70:
            color = GREEN
        elif self.happiness > 40:
            color = YELLOW
        else:
            color = RED
        pygame.draw.rect(self.screen, color, (bar_x + 2, bar_y + 2, fill_w, bar_h - 4))
        label = self.font_small.render(f"HAPPINESS  {self.happiness}", True, BLACK)
        self.screen.blit(label, (bar_x + 10, bar_y + 4))

    def draw_song_buttons(self):
        cols = 3
        margin_x = 20
        margin_y = 622
        gap = 6
        btn_w = (WIDTH - margin_x * 2 - gap * (cols - 1)) // cols
        btn_h = 26
        for i, song in enumerate(self.songs):
            col = i % cols
            row = i // cols
            bx = margin_x + col * (btn_w + gap)
            by = margin_y + row * (btn_h + gap)
            rect = pygame.Rect(bx, by, btn_w, btn_h)
            border_color = tuple(song["color"])
            if self.locked_song and song["id"] == self.locked_song["id"]:
                border_color = WHITE
            if self.waiting_response:
                border_color = AMBER
            pygame.draw.rect(self.screen, DARK, rect)
            pygame.draw.rect(self.screen, border_color, rect, 2)
            mood_label = song["mood"] if song["mood"] != "silence" else "—"
            label = f"{i+1}. {song['title'].upper()} · {mood_label}"
            txt = self.font_tiny.render(label, True, tuple(song["color"]))
            self.screen.blit(
                txt,
                (rect.centerx - txt.get_width() // 2,
                 rect.centery - txt.get_height() // 2)
            )

    # --------------------------------------------------------
    def handle_input(self):
        if self.game_over or self.paused:
            return
        keys = pygame.key.get_pressed()
        mods = pygame.key.get_mods()
        shift = mods & pygame.KMOD_SHIFT

        self.fast_forward = keys[pygame.K_TAB]
        debug_shift = shift and (
            keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or
            keys[pygame.K_UP] or keys[pygame.K_DOWN]
        )
        self.slow_down = shift and not debug_shift and not self.fast_forward

        if self.debug and shift:
            if keys[pygame.K_LEFT]:
                self.game_hour = max(0.0, self.game_hour - 0.02)
            if keys[pygame.K_RIGHT]:
                self.game_hour = min(6.0, self.game_hour + 0.02)
            if keys[pygame.K_UP]:
                self.happiness = min(100, self.happiness + 1)
            if keys[pygame.K_DOWN]:
                self.happiness = max(0, self.happiness - 1)

    # --------------------------------------------------------
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            # Speed multiplier
            if self.state == "playing":
                if self.fast_forward:
                    dt *= 2.0
                elif self.slow_down:
                    dt *= 0.5
                if self.paused:
                    dt = 0.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False

                    if self.state == "intro":
                        if event.key == pygame.K_SPACE and self.intro_wait_input:
                            # Mulai game
                            self.state = "playing"
                            self.reset_game_state()
                            self.setup_ambient_audio()

                    elif self.state == "playing":
                        if event.key == pygame.K_SPACE:
                            self.paused = not self.paused
                            if self.paused:
                                pygame.mixer.music.pause()
                                if self.static_channel:
                                    self.static_channel.pause()
                                if self.hum_channel:
                                    self.hum_channel.pause()
                            else:
                                pygame.mixer.music.unpause()
                                if self.static_channel:
                                    self.static_channel.unpause()
                                if self.hum_channel:
                                    self.hum_channel.unpause()
                        elif pygame.K_1 <= event.key <= pygame.K_9:
                            idx = event.key - pygame.K_1
                            self.select_song(idx)
                        elif event.key == pygame.K_q and self.reply_options_visible:
                            self.resolve_reply("Q")
                        elif event.key == pygame.K_w and self.reply_options_visible:
                            self.resolve_reply("W")
                        elif event.key == pygame.K_e and self.reply_options_visible:
                            self.resolve_reply("E")
                        elif event.key == pygame.K_UP:
                            self.chat_scroll += 30
                        elif event.key == pygame.K_DOWN:
                            self.chat_scroll = max(0, self.chat_scroll - 30)

                    elif self.state == "ending":
                        if self.ending_wait_restart:
                            if event.key == pygame.K_SPACE:
                                # Restart
                                self.state = "intro"
                                self.intro_index = 0
                                self.intro_timer = 0.0
                                self.intro_typing_index = 0
                                self.intro_lines_rendered = []
                                self.intro_wait_input = False
                                self.reset_game_state()

                elif event.type == pygame.MOUSEWHEEL:
                    if self.state == "playing":
                        self.chat_scroll += event.y * 30
                        self.chat_scroll = max(0, self.chat_scroll)

            # Update
            if self.state == "intro":
                self.update_intro(dt)
            elif self.state == "playing":
                self.handle_input()
                if not self.paused:
                    self.update(dt)
            elif self.state == "ending":
                self.update_ending(dt)

            self.draw()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    DeadAirGame().run()