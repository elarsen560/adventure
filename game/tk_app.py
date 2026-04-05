from __future__ import annotations

import math
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import font as tkfont
from tkinter import scrolledtext

from game.audio import AudioConfig, AudioManager
from game.content import ITEMS, ROOMS, intro_text, parse_args
from game.engine import Command, Game
from game.map import render_map
from game.parser import parse_command


POST_WIN_PROMPT = "Enter 'quit' to exit the observatory or 'restart' to begin a new run."
STARTUP_COVER = Path("assets/images/startup/cover_v1.png")
ROOM_IMAGE_DIR = Path("assets/images/rooms")
MAP_WIDTH_RATIO = 0.75


def centered_geometry(screen_width: int, screen_height: int, width: int, height: int) -> str:
    x = max(0, (screen_width - width) // 2)
    y = max(0, (screen_height - height) // 2)
    return f"{width}x{height}+{x}+{y}"


def startup_cover_path() -> Path | None:
    return STARTUP_COVER if STARTUP_COVER.exists() else None


def room_image_path(room_id: str) -> Path | None:
    path = ROOM_IMAGE_DIR / f"{room_id}.png"
    return path if path.exists() else None


def subsample_factor(width: int, height: int, max_width: int, max_height: int) -> int:
    if max_width <= 0 or max_height <= 0:
        return 1
    width_ratio = width / max_width
    height_ratio = height / max_height
    return max(1, math.ceil(max(width_ratio, height_ratio)))


class DesktopAudioManager(AudioManager):
    def play_victory_jingle(self) -> None:
        return


@dataclass
class DesktopCommandResult:
    lines: list[str]
    should_close: bool = False
    reset_transcript: bool = False


class DesktopGameSession:
    def __init__(self, args, audio_manager: AudioManager | None = None):
        self.args = args
        self.audio = audio_manager or DesktopAudioManager(
            AudioConfig.from_runtime(mute=args.mute, preset=args.audio_preset)
        )
        self._gameplay_ambient_enabled = self.audio.config.ambient_enabled
        self._gameplay_sfx_enabled = self.audio.config.sfx_enabled
        self.audio.config.ambient_enabled = False
        self.audio.config.sfx_enabled = False
        self.audio.initialize()
        self.game: Game | None = None
        self.gameplay_started = False
        self.new_game(args.seed, gameplay_started=False)
        self.start_title_audio()

    def shutdown(self) -> None:
        self.audio.shutdown()

    def new_game(self, seed: int | None, *, gameplay_started: bool) -> list[str]:
        self.game = Game(seed=seed, debug=self.args.debug, audio_manager=self.audio)
        self.gameplay_started = gameplay_started
        if gameplay_started:
            self.enable_gameplay_audio()
            return self.gameplay_opening_lines()
        return self.title_screen_lines()

    def title_screen_lines(self) -> list[str]:
        assert self.game is not None
        return [self.title_screen_text()]

    def title_screen_text(self) -> str:
        assert self.game is not None
        return intro_text(self.game.state).split("\n\nRun seed:", 1)[0]

    def gameplay_opening_lines(self) -> list[str]:
        assert self.game is not None
        return [
            f"Run seed: {self.game.state.seed}\n{self.game.state.variation['intro_line']}",
            self.game.describe_room(),
            "Type 'help' for commands or 'instructions' for play guidance.",
            self.audio.status_line(),
        ]

    def start_title_audio(self) -> None:
        if not self.audio.available:
            return
        self.audio.reset_session_audio()
        self.audio.play_music("main_theme")

    def enable_gameplay_audio(self) -> None:
        self.audio.config.ambient_enabled = self._gameplay_ambient_enabled
        self.audio.config.sfx_enabled = self._gameplay_sfx_enabled
        if self.audio.available:
            self.audio._apply_volumes()
            self.audio.play_music("main_theme")
            if self.game is not None:
                self.audio.update_for_state(self.game.state)

    def begin_gameplay(self) -> list[str]:
        if self.gameplay_started:
            return []
        assert self.game is not None
        self.gameplay_started = True
        self.enable_gameplay_audio()
        return self.gameplay_opening_lines()

    def handle_command(self, raw: str) -> DesktopCommandResult:
        assert self.game is not None
        text = raw.rstrip("\n")
        if not text.strip():
            return DesktopCommandResult([])
        parsed = parse_command(text)

        if self.game.state.won:
            normalized = " ".join(text.lower().split())
            if normalized == "quit":
                return DesktopCommandResult(
                    [f"> {text}", self.game.do_quit(Command("quit", raw=text))],
                    should_close=True,
                )
            if normalized == "restart":
                lines = [f"> {text}", *self.new_game(None, gameplay_started=True)]
                return DesktopCommandResult(lines, reset_transcript=True)
            return DesktopCommandResult([f"> {text}", POST_WIN_PROMPT])

        victory = self.game.try_victory(text)
        if victory:
            return DesktopCommandResult([f"> {text}", victory, POST_WIN_PROMPT])

        response = self.game.process(text)
        return DesktopCommandResult(
            [f"> {text}", response],
            should_close=(parsed.action == "quit" and not self.game.state.running),
        )

    def map_text(self) -> str:
        assert self.game is not None
        return render_map(self.game.state)

    def inventory_text(self) -> str:
        assert self.game is not None
        if not self.game.state.inventory:
            return "You are carrying nothing."
        return "\n".join(f"- {ITEMS[item_id].name}" for item_id in self.game.state.inventory)

    def visual_text(self) -> str:
        assert self.game is not None
        room = ROOMS[self.game.state.current_room]
        return f"{room.name}\n\nVisual plate reserved for a future room image."


class AsterfallDesktopApp:
    def __init__(self, root: tk.Tk, args):
        self.root = root
        self.session = DesktopGameSession(args)
        self.history: list[str] = []
        self.history_index: int | None = None

        self.root.title("Asterfall Observatory")
        self.root.geometry(
            centered_geometry(
                self.root.winfo_screenwidth(),
                self.root.winfo_screenheight(),
                1200,
                760,
            )
        )
        self.root.minsize(980, 620)
        self.root.configure(bg="#111317")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.game_frame: tk.Frame | None = None
        self.startup_frame: tk.Frame | None = None
        self.startup_visual_frame = None
        self.startup_visual_label = None
        self.startup_cover_image = None
        self.transcript = None
        self.entry = None
        self.visual_frame = None
        self.visual_label = None
        self.room_visual_image = None
        self.visual_panel = None
        self.map_panel = None
        self.inventory_panel = None

        self._build_startup_layout()

    def _build_startup_layout(self) -> None:
        self.startup_frame = tk.Frame(self.root, bg="#111317", padx=18, pady=18)
        self.startup_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.startup_frame.grid_columnconfigure(0, weight=1)
        self.startup_frame.grid_rowconfigure(0, weight=1)
        self.startup_frame.grid_rowconfigure(1, weight=1)

        mono = tkfont.nametofont("TkFixedFont").copy()
        mono.configure(size=12)
        title_font = tkfont.nametofont("TkFixedFont").copy()
        title_font.configure(size=14)

        self.startup_visual_frame = tk.Frame(self.startup_frame, bg="#1a1f26", bd=1, relief="flat")
        self.startup_visual_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 12))
        self.startup_visual_frame.grid_rowconfigure(0, weight=1)
        self.startup_visual_frame.grid_columnconfigure(0, weight=1)

        self.startup_visual_label = tk.Label(
            self.startup_visual_frame,
            text="Asterfall Observatory\n\nCover plate reserved for a future title image.",
            bg="#141920",
            fg="#dcd5c4",
            font=title_font,
            justify="center",
        )
        self.startup_visual_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        text_frame = tk.Frame(self.startup_frame, bg="#1a1f26", bd=1, relief="flat")
        text_frame.grid(row=1, column=0, sticky="nsew")
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        intro_pane = tk.Text(
            text_frame,
            wrap="word",
            font=mono,
            bg="#171b21",
            fg="#e2dccf",
            relief="flat",
            padx=18,
            pady=18,
            height=12,
        )
        intro_pane.grid(row=0, column=0, sticky="nsew")
        intro_pane.insert("1.0", self.session.title_screen_text())
        intro_pane.configure(state="disabled")

        start_button = tk.Button(
            text_frame,
            text="Start Game",
            command=self.start_game,
            font=mono,
            bg="#2b3340",
            fg="#f0eadc",
            activebackground="#394454",
            activeforeground="#f0eadc",
            relief="flat",
            padx=18,
            pady=8,
        )
        start_button.grid(row=1, column=0, sticky="e", padx=12, pady=(0, 12))
        self.root.after(10, self.update_startup_visual)
        self.root.bind("<Configure>", self.on_root_configure)
        self.root.bind("<Return>", self.start_game)

    def update_startup_visual(self) -> None:
        if self.startup_visual_label is None or self.startup_visual_frame is None:
            return
        path = startup_cover_path()
        if path is None:
            self.startup_visual_label.configure(
                image="",
                text="Asterfall Observatory\n\nCover plate reserved for a future title image.",
            )
            self.startup_cover_image = None
            return
        try:
            image = tk.PhotoImage(file=str(path))
            max_width = max(720, self.startup_visual_frame.winfo_width() - 24)
            max_height = max(360, self.startup_visual_frame.winfo_height() - 24)
            factor = subsample_factor(image.width(), image.height(), max_width, max_height)
            if factor > 1:
                image = image.subsample(factor, factor)
            self.startup_cover_image = image
            self.startup_visual_label.configure(image=image, text="")
        except tk.TclError:
            self.startup_visual_label.configure(
                image="",
                text="Asterfall Observatory\n\nCover image could not be loaded.",
            )
            self.startup_cover_image = None

    def on_root_configure(self, _event=None) -> None:
        if self.startup_frame is not None:
            self.update_startup_visual()
        if self.game_frame is not None:
            self.update_room_visual()

    def _build_layout(self) -> None:
        self.root.grid_columnconfigure(0, weight=1, uniform="desktop")
        self.root.grid_columnconfigure(1, weight=1, uniform="desktop")
        self.root.grid_rowconfigure(0, weight=1)

        mono = tkfont.nametofont("TkFixedFont").copy()
        mono.configure(size=13)
        small_mono = tkfont.nametofont("TkFixedFont").copy()
        small_mono.configure(size=11)

        self.game_frame = tk.Frame(self.root, bg="#111317")
        self.game_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.game_frame.grid_columnconfigure(0, weight=1, uniform="gameplay")
        self.game_frame.grid_columnconfigure(1, weight=1, uniform="gameplay")
        self.game_frame.grid_rowconfigure(0, weight=1)

        left = tk.Frame(self.game_frame, bg="#111317", padx=12, pady=12)
        left.grid(row=0, column=0, sticky="nsew")
        left.grid_rowconfigure(0, weight=1)
        left.grid_columnconfigure(0, weight=1)

        right = tk.Frame(self.game_frame, bg="#111317", padx=12, pady=12)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(0, weight=3)
        right.grid_rowconfigure(1, weight=3)
        right.grid_columnconfigure(0, weight=1)

        self.transcript = scrolledtext.ScrolledText(
            left,
            wrap="word",
            font=mono,
            bg="#171b21",
            fg="#e2dccf",
            insertbackground="#e2dccf",
            relief="flat",
            padx=14,
            pady=14,
        )
        self.transcript.grid(row=0, column=0, sticky="nsew")
        self.transcript.configure(state="disabled")

        entry_frame = tk.Frame(left, bg="#111317", pady=10)
        entry_frame.grid(row=1, column=0, sticky="ew")
        entry_frame.grid_columnconfigure(1, weight=1)

        prompt = tk.Label(entry_frame, text=">", font=mono, bg="#111317", fg="#d6ceb8")
        prompt.grid(row=0, column=0, sticky="w", padx=(0, 8))

        self.entry = tk.Entry(
            entry_frame,
            font=mono,
            bg="#0f1217",
            fg="#f0eadc",
            insertbackground="#f0eadc",
            relief="flat",
        )
        self.entry.grid(row=0, column=1, sticky="ew")
        self.entry.bind("<Return>", self.on_submit)
        self.entry.bind("<Up>", self.on_history_up)
        self.entry.bind("<Down>", self.on_history_down)

        self.visual_frame, self.visual_label = self._make_visual_panel(right, "Visual Plate", row=0, font=small_mono)
        lower = tk.Frame(right, bg="#111317")
        lower.grid(row=1, column=0, sticky="nsew")
        lower.grid_rowconfigure(0, weight=1)
        map_weight = max(1, int(MAP_WIDTH_RATIO * 100))
        inventory_weight = max(1, int((1.0 - MAP_WIDTH_RATIO) * 100))
        lower.grid_columnconfigure(0, weight=map_weight, uniform="lower")
        lower.grid_columnconfigure(1, weight=inventory_weight, uniform="lower")

        self.map_panel = self._make_panel(lower, "Observatory Map", row=0, column=0, font=small_mono, height=8, padx=(0, 10))
        self.inventory_panel = self._make_panel(lower, "Inventory", row=0, column=1, font=small_mono, height=8)

    def start_game(self, _event=None):
        self.root.unbind("<Return>")
        if self.startup_frame is not None:
            self.startup_frame.destroy()
            self.startup_frame = None
        self._build_layout()
        self.append_lines(self.session.begin_gameplay())
        self.refresh_side_panels()
        self.entry.focus_set()
        return "break"

    def _make_panel(
        self,
        parent: tk.Frame,
        title: str,
        row: int,
        *,
        column: int = 0,
        font,
        height: int = 8,
        padx: tuple[int, int] | int = 0,
    ) -> tk.Text:
        frame = tk.Frame(parent, bg="#1a1f26", bd=1, relief="flat")
        frame.grid(row=row, column=column, sticky="nsew", pady=(0, 10 if row < 2 else 0), padx=padx)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        label = tk.Label(frame, text=title, anchor="w", bg="#232a34", fg="#d7cfba", padx=10, pady=6, font=font)
        label.grid(row=0, column=0, sticky="ew")

        text = tk.Text(
            frame,
            wrap="word" if title == "Inventory" else "none",
            font=font,
            bg="#141920",
            fg="#dcd5c4",
            insertbackground="#dcd5c4",
            relief="flat",
            padx=10,
            pady=10,
            height=height,
        )
        text.grid(row=1, column=0, sticky="nsew")
        text.configure(state="disabled")
        return text

    def _make_visual_panel(self, parent: tk.Frame, title: str, row: int, *, font) -> tuple[tk.Frame, tk.Label]:
        frame = tk.Frame(parent, bg="#1a1f26", bd=1, relief="flat")
        frame.grid(row=row, column=0, sticky="nsew", pady=(0, 10 if row < 2 else 0))
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        label = tk.Label(frame, text=title, anchor="w", bg="#232a34", fg="#d7cfba", padx=10, pady=6, font=font)
        label.grid(row=0, column=0, sticky="ew")

        visual = tk.Label(
            frame,
            text="Visual plate reserved for a future room image.",
            justify="center",
            bg="#141920",
            fg="#dcd5c4",
            font=font,
            padx=10,
            pady=10,
        )
        visual.grid(row=1, column=0, sticky="nsew")
        return frame, visual

    def append_lines(self, lines: list[str]) -> None:
        if not lines:
            return
        assert self.transcript is not None
        self.transcript.configure(state="normal")
        for line in lines:
            if self.transcript.index("end-1c") != "1.0":
                self.transcript.insert("end", "\n\n")
            self.transcript.insert("end", line.rstrip())
        self.transcript.configure(state="disabled")
        self.transcript.see("end")

    def clear_transcript(self) -> None:
        assert self.transcript is not None
        self.transcript.configure(state="normal")
        self.transcript.delete("1.0", "end")
        self.transcript.configure(state="disabled")

    def set_panel_text(self, widget: tk.Text, text: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def refresh_side_panels(self) -> None:
        assert self.map_panel is not None
        assert self.inventory_panel is not None
        self.set_panel_text(self.map_panel, self.session.map_text())
        self.set_panel_text(self.inventory_panel, self.session.inventory_text())
        self.update_room_visual()

    def update_room_visual(self) -> None:
        if self.visual_label is None or self.visual_frame is None:
            return
        assert self.session.game is not None
        room_id = self.session.game.state.current_room
        path = room_image_path(room_id)
        if path is None:
            self.visual_label.configure(
                image="",
                text=self.session.visual_text(),
            )
            self.room_visual_image = None
            return
        try:
            image = tk.PhotoImage(file=str(path))
            max_width = max(360*1.4, self.visual_frame.winfo_width() - 8)
            max_height = max(260*1.4, self.visual_frame.winfo_height() - 34)
            factor = subsample_factor(image.width(), image.height(), max_width, max_height)
            if factor > 1:
                image = image.subsample(factor, factor)
            self.room_visual_image = image
            self.visual_label.configure(image=image, text="")
        except tk.TclError:
            self.visual_label.configure(
                image="",
                text=self.session.visual_text(),
            )
            self.room_visual_image = None

    def on_submit(self, _event=None):
        assert self.entry is not None
        raw = self.entry.get()
        self.entry.delete(0, "end")
        self.history_index = None
        if raw.strip():
            self.history.append(raw)
        result = self.session.handle_command(raw)
        if result.reset_transcript:
            self.clear_transcript()
        self.append_lines(result.lines)
        self.refresh_side_panels()
        if result.should_close:
            self.root.after(50, self.on_close)
        return "break"

    def on_history_up(self, _event=None):
        if not self.history:
            return "break"
        if self.history_index is None:
            self.history_index = len(self.history) - 1
        elif self.history_index > 0:
            self.history_index -= 1
        self._show_history_value()
        return "break"

    def on_history_down(self, _event=None):
        if self.history_index is None:
            return "break"
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self._show_history_value()
        else:
            self.history_index = None
            self.entry.delete(0, "end")
        return "break"

    def _show_history_value(self) -> None:
        if self.history_index is None:
            return
        self.entry.delete(0, "end")
        self.entry.insert(0, self.history[self.history_index])

    def on_close(self) -> None:
        self.session.shutdown()
        self.root.destroy()


def run_desktop_app(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    root = tk.Tk()
    AsterfallDesktopApp(root, args)
    root.mainloop()
