import threading
import tkinter as tk
from datetime import datetime

from agent import NovaAgent
from speech import SpeechRecognizer
from tts import NovaTTS
import tools as nova_tools

# -------------------------------------------------------------------
# NOVA — Friendly Agentic Desktop Assistant GUI
# -------------------------------------------------------------------

BG = "#0f172a"
CARD = "#172238"
INPUT = "#111c30"
TEXT = "#f1f5f9"
MUTED = "#94a3b8"
ACCENT = "#60a5fa"
ACCENT_HOVER = "#93c5fd"
GREEN = "#4ade80"
RED = "#fb7185"
PURPLE = "#a78bfa"
BORDER = "#263754"


class NovaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NOVA — Your AI Desktop Assistant")
        self.root.geometry("1180x760")
        self.root.minsize(900, 620)
        self.root.configure(bg=BG)

        self.busy = False
        self.camera_window = None
        self.camera_window_label = None
        self._camera_window_photo = None

        # Initialize NOVA services.
        self.agent = NovaAgent(self.set_status)
        self.speech = SpeechRecognizer()
        self.tts = NovaTTS(self.set_status)

        self._build()
        self._welcome()

        # Start the display polling only after all widgets exist.
        self._update_time_displays()

        # Close cleanly.
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ----------------------------------------------------------------
    # UI helpers
    # ----------------------------------------------------------------

    def _card(self, parent, **kwargs):
        return tk.Frame(
            parent,
            bg=CARD,
            bd=0,
            highlightbackground=BORDER,
            highlightthickness=1,
            **kwargs,
        )

    def _button(
        self,
        parent,
        text,
        command,
        bg="#1c2940",
        fg=TEXT,
        active="#29405f",
        font=("Segoe UI", 10, "bold"),
    ):
        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=active,
            activeforeground=TEXT,
            relief="flat",
            bd=0,
            cursor="hand2",
            font=font,
            padx=14,
            pady=9,
        )

        button.bind("<Enter>", lambda _: button.configure(bg=active))
        button.bind("<Leave>", lambda _: button.configure(bg=bg))

        return button

    # ----------------------------------------------------------------
    # Build GUI
    # ----------------------------------------------------------------

    def _build(self):
        # Header
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=28, pady=(22, 12))

        brand = tk.Frame(header, bg=BG)
        brand.pack(side="left")

        tk.Label(
            brand,
            text="NOVA",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 26, "bold"),
        ).pack(side="left")

        tk.Label(
            brand,
            text="  your personal desktop assistant",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 10),
        ).pack(side="left", pady=(9, 0))

        self.status_pill = tk.Label(
            header,
            text="  ● Ready  ",
            bg="#173524",
            fg=GREEN,
            font=("Segoe UI", 10, "bold"),
            padx=8,
            pady=5,
        )
        self.status_pill.pack(side="right", pady=5)

        # Main layout
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=28, pady=(4, 22))

        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=0)
        body.grid_rowconfigure(0, weight=1)

        # ------------------------------------------------------------
        # Conversation card
        # ------------------------------------------------------------

        conversation = self._card(body)
        conversation.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 14),
        )

        conversation.grid_rowconfigure(1, weight=1)
        conversation.grid_columnconfigure(0, weight=1)

        title_row = tk.Frame(conversation, bg=CARD)
        title_row.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=18,
            pady=(16, 8),
        )

        tk.Label(
            title_row,
            text="Conversation",
            bg=CARD,
            fg=TEXT,
            font=("Segoe UI", 13, "bold"),
        ).pack(side="left")

        tk.Label(
            title_row,
            text="  Ask me anything",
            bg=CARD,
            fg=MUTED,
            font=("Segoe UI", 9),
        ).pack(side="left", pady=(3, 0))

        self.chat = tk.Text(
            conversation,
            bg="#121d31",
            fg=TEXT,
            insertbackground=ACCENT,
            relief="flat",
            bd=0,
            wrap="word",
            font=("Segoe UI", 10),
            padx=18,
            pady=14,
            spacing1=3,
            spacing3=7,
            selectbackground="#31547e",
        )

        self.chat.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=10,
            pady=(0, 10),
        )

        self.chat.configure(state="disabled")

        # ------------------------------------------------------------
        # Message composer
        # ------------------------------------------------------------

        composer = tk.Frame(conversation, bg=CARD)
        composer.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=14,
            pady=(0, 14),
        )

        composer.grid_columnconfigure(0, weight=1)

        entry_wrap = tk.Frame(
            composer,
            bg=INPUT,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        entry_wrap.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 8),
        )

        self.entry = tk.Entry(
            entry_wrap,
            bg=INPUT,
            fg=TEXT,
            insertbackground=ACCENT,
            relief="flat",
            bd=0,
            font=("Segoe UI", 11),
        )

        self.entry.pack(
            fill="x",
            padx=14,
            pady=11,
        )

        self.entry.bind(
            "<Return>",
            lambda _: self.send(),
        )

        self.mic_btn = self._button(
            composer,
            "🎤",
            self.listen,
            bg="#233554",
            active="#2e466b",
        )

        self.mic_btn.grid(
            row=0,
            column=1,
            padx=(0, 7),
        )

        self.send_btn = self._button(
            composer,
            "Send  →",
            self.send,
            bg=ACCENT,
            fg="#07111f",
            active=ACCENT_HOVER,
        )

        self.send_btn.grid(
            row=0,
            column=2,
        )

        # ------------------------------------------------------------
        # Right information panel — scrollable
        # ------------------------------------------------------------

        side = self._card(body, width=270)
        side.grid(
            row=0,
            column=1,
            sticky="nsew",
        )
        side.grid_propagate(False)

        side.grid_rowconfigure(0, weight=1)
        side.grid_columnconfigure(0, weight=1)

        side_canvas = tk.Canvas(
            side,
            bg=CARD,
            highlightthickness=0,
            bd=0,
        )
        side_canvas.grid(row=0, column=0, sticky="nsew")

        side_scrollbar = tk.Scrollbar(
            side,
            orient="vertical",
            command=side_canvas.yview,
            width=10,
        )
        side_scrollbar.grid(row=0, column=1, sticky="ns")

        side_canvas.configure(yscrollcommand=side_scrollbar.set)

        side_content = tk.Frame(side_canvas, bg=CARD)
        side_window = side_canvas.create_window(
            (0, 0),
            window=side_content,
            anchor="nw",
        )

        def _update_side_scrollregion(event=None):
            side_canvas.configure(scrollregion=side_canvas.bbox("all"))

        def _resize_side_content(event):
            side_canvas.itemconfigure(side_window, width=event.width)

        side_content.bind(
            "<Configure>",
            _update_side_scrollregion,
        )
        side_canvas.bind(
            "<Configure>",
            _resize_side_content,
        )

        # Mouse-wheel scrolling over the right panel.
        def _side_mousewheel(event):
            side_canvas.yview_scroll(
                int(-1 * (event.delta / 120)),
                "units",
            )

        # Scroll only when the pointer is over the NOVA side panel.
        # This prevents the camera Toplevel window from being affected.
        side_canvas.bind("<Enter>", lambda _event: side_canvas.bind_all(
            "<MouseWheel>", _side_mousewheel
        ))
        side_canvas.bind("<Leave>", lambda _event: side_canvas.unbind_all(
            "<MouseWheel>"
        ))

        # NOVA header inside the scrollable area.
        tk.Label(
            side_content,
            text="NOVA",
            bg=CARD,
            fg=TEXT,
            font=("Segoe UI", 16, "bold"),
        ).pack(pady=(20, 0))

        tk.Label(
            side_content,
            text="Always here to help",
            bg=CARD,
            fg=MUTED,
            font=("Segoe UI", 9),
        ).pack(pady=(1, 8))

        # Keep the NOVA GUI clean: the live camera feed is shown only
        # in the separate, large camera window.
        self.nova_orb = tk.Label(
            side_content,
            text="◉\nNOVA\nONLINE",
            bg="#172238",
            fg=ACCENT,
            width=34,
            height=8,
            font=("Segoe UI", 13, "bold"),
            justify="center",
        )
        self.nova_orb.pack(padx=8, pady=(0, 2))

        status_box = tk.Frame(side_content, bg=CARD)
        status_box.pack(
            fill="x",
            padx=18,
            pady=(2, 8),
        )

        self._status_item(status_box, "●", "Listening", "Voice input")
        self._status_item(status_box, "✦", "Thinking", "AI reasoning")
        self._status_item(status_box, "✓", "Executing", "Desktop tools")
        self._status_item(status_box, "◖", "Speaking", "Voice output")

        # ------------------------------------------------------------
        # Camera controls
        # ------------------------------------------------------------

        camera_controls = tk.Frame(side_content, bg=CARD)
        camera_controls.pack(fill="x", padx=18, pady=(0, 7))

        self.camera_open_btn = self._button(
            camera_controls,
            "📷 Camera",
            self._camera_open,
            bg="#233554",
            active="#2e466b",
        )
        self.camera_open_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.camera_photo_btn = self._button(
            camera_controls,
            "📸 Photo",
            self._camera_photo,
            bg="#233554",
            active="#2e466b",
        )
        self.camera_photo_btn.pack(side="left", fill="x", expand=True, padx=4)

        self.camera_record_btn = self._button(
            camera_controls,
            "● Rec",
            self._camera_record,
            bg="#3a2430",
            fg="#fda4af",
            active="#512c3b",
        )
        self.camera_record_btn.pack(side="left", fill="x", expand=True, padx=(4, 0))

        self.camera_close_btn = self._button(
            side_content,
            "Close Camera",
            self._camera_close,
            bg="#2b2030",
            fg="#fda4af",
            active="#3a263b",
        )
        self.camera_close_btn.pack(fill="x", padx=18, pady=(0, 5))

        # ------------------------------------------------------------
        # Visible timer / stopwatch panel
        # ------------------------------------------------------------

        time_box = tk.Frame(
            side_content,
            bg=INPUT,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        time_box.pack(
            fill="x",
            padx=18,
            pady=(2, 10),
        )

        tk.Label(
            time_box,
            text="TIME TOOLS",
            bg=INPUT,
            fg=MUTED,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", padx=10, pady=(8, 2))

        timer_row = tk.Frame(time_box, bg=INPUT)
        timer_row.pack(fill="x", padx=10, pady=(0, 3))

        tk.Label(
            timer_row,
            text="⏱ TIMER",
            bg=INPUT,
            fg=TEXT,
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left")

        self.timer_display = tk.Label(
            timer_row,
            text="00:00",
            bg=INPUT,
            fg=ACCENT,
            font=("Consolas", 13, "bold"),
        )
        self.timer_display.pack(side="right")

        stopwatch_row = tk.Frame(time_box, bg=INPUT)
        stopwatch_row.pack(fill="x", padx=10, pady=(0, 3))

        tk.Label(
            stopwatch_row,
            text="⏱ STOPWATCH",
            bg=INPUT,
            fg=TEXT,
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left")

        self.stopwatch_display = tk.Label(
            stopwatch_row,
            text="00:00",
            bg=INPUT,
            fg=PURPLE,
            font=("Consolas", 15, "bold"),
        )
        self.stopwatch_display.pack(side="right")

        self.time_status_label = tk.Label(
            time_box,
            text="Ready",
            bg=INPUT,
            fg=MUTED,
            font=("Segoe UI", 8),
        )
        self.time_status_label.pack(anchor="w", padx=10, pady=(0, 7))

        tk.Label(
            side_content,
            text="Activity",
            bg=CARD,
            fg=TEXT,
            font=("Segoe UI", 11, "bold"),
        ).pack(
            anchor="w",
            padx=18,
            pady=(0, 5),
        )

        self.log = tk.Text(
            side,
            height=6,
            bg="#121d31",
            fg=MUTED,
            relief="flat",
            bd=0,
            font=("Segoe UI", 8),
            padx=10,
            pady=9,
        )

        self.log.pack(
            fill="both",
            padx=18,
            pady=(0, 14),
        )

        self.log.configure(state="disabled")

        self._button(
            side_content,
            "Stop Voice",
            self.tts.stop,
            bg="#2b2030",
            fg="#fda4af",
            active="#3a263b",
        ).pack(
            fill="x",
            padx=18,
            pady=(0, 18),
        )

    def _status_item(self, parent, icon, title, subtitle):
        row = tk.Frame(parent, bg=CARD)
        row.pack(fill="x", pady=4)

        tk.Label(
            row,
            text=icon,
            bg=CARD,
            fg=ACCENT,
            font=("Segoe UI", 12, "bold"),
            width=2,
        ).pack(side="left")

        texts = tk.Frame(row, bg=CARD)
        texts.pack(side="left")

        tk.Label(
            texts,
            text=title,
            bg=CARD,
            fg=TEXT,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w")

        tk.Label(
            texts,
            text=subtitle,
            bg=CARD,
            fg=MUTED,
            font=("Segoe UI", 8),
        ).pack(anchor="w")

    def _draw_orb(self):
        """Restore the static NOVA indicator in the main window."""
        try:
            if hasattr(self, "nova_orb"):
                self.nova_orb.configure(
                    text="◉\nNOVA\nONLINE",
                    image="",
                    fg=ACCENT,
                )
        except Exception:
            pass


    # ----------------------------------------------------------------
    # Camera controls / live preview
    # ----------------------------------------------------------------

    def _camera_open(self):
        """Open the camera and show a large live preview window."""
        def worker():
            result = nova_tools.open_camera()
            self.root.after(0, lambda r=result: self._camera_result(r))
            if "failed" not in result.lower() and "not available" not in result.lower():
                self.root.after(0, self._show_camera_window)
        threading.Thread(target=worker, daemon=True).start()

    def _show_camera_window(self):
        """Open a stable, large, resizable camera window with fixed controls."""
        try:
            if self.camera_window is not None and self.camera_window.winfo_exists():
                self.camera_window.deiconify()
                self.camera_window.lift()
                return
        except tk.TclError:
            self.camera_window = None

        win = tk.Toplevel(self.root)
        self.camera_window = win

        win.title("NOVA — Live Camera")
        win.configure(bg="#080f1d")
        win.resizable(True, True)
        win.minsize(700, 560)
        win.protocol("WM_DELETE_WINDOW", self._hide_camera_window)

        # Prevent the window manager from deciding a new cascade position.
        win.transient(self.root)

        # Grid: title fixed, preview expandable, controls fixed.
        win.grid_rowconfigure(1, weight=1)
        win.grid_columnconfigure(0, weight=1)

        title = tk.Label(
            win,
            text="NOVA LIVE CAMERA",
            bg="#080f1d",
            fg=TEXT,
            font=("Segoe UI", 15, "bold"),
        )
        title.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 6))

        preview_frame = tk.Frame(win, bg="#080f1d")
        preview_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=14,
            pady=(0, 10),
        )
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)

        self.camera_window_label = tk.Label(
            preview_frame,
            text="Starting camera...",
            bg="#080f1d",
            fg=MUTED,
            font=("Segoe UI", 11, "bold"),
            anchor="center",
            justify="center",
        )
        self.camera_window_label.grid(row=0, column=0, sticky="nsew")

        controls = tk.Frame(win, bg="#080f1d", height=58)
        controls.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=14,
            pady=(0, 14),
        )
        controls.grid_propagate(False)

        for col in range(3):
            controls.grid_columnconfigure(col, weight=1)
        controls.grid_rowconfigure(0, weight=1)

        photo_btn = self._button(
            controls,
            "📸 Take Photo",
            self._camera_photo,
            bg="#233554",
            active="#315078",
        )
        photo_btn.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        self.camera_window_record_btn = self._button(
            controls,
            "● Start Recording",
            self._camera_record,
            bg="#3a2430",
            fg="#fda4af",
            active="#512c3b",
        )
        self.camera_window_record_btn.grid(
            row=0, column=1, sticky="nsew", padx=5
        )

        close_btn = self._button(
            controls,
            "Close Camera",
            self._camera_close,
            bg="#2b2030",
            fg="#fda4af",
            active="#3a263b",
        )
        close_btn.grid(row=0, column=2, sticky="nsew", padx=(5, 0))

        # Do all geometry work after every widget exists, then position the
        # window once in the center of the current screen.
        win.geometry("900x700")
        win.update_idletasks()

        screen_w = win.winfo_screenwidth()
        screen_h = win.winfo_screenheight()
        win_w = 900
        win_h = 700
        pos_x = max(0, (screen_w - win_w) // 2)
        pos_y = max(0, (screen_h - win_h) // 2)

        win.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
        win.update_idletasks()

        # Store the final geometry so reopening the window uses the same
        # position instead of Windows choosing a new cascade location.
        self._camera_window_geometry = win.geometry()

        win.after(100, self._update_camera_window)

    def _hide_camera_window(self):
        """Close the camera window without moving the main NOVA window."""
        try:
            if self.camera_window is not None and self.camera_window.winfo_exists():
                self.camera_window.destroy()
        except tk.TclError:
            pass

        self.camera_window = None
        self.camera_window_label = None
        self._camera_window_photo = None

    def _camera_photo(self):
        def worker():
            result = nova_tools.take_photo()
            self.root.after(0, lambda r=result: self._camera_result(r))
        threading.Thread(target=worker, daemon=True).start()

    def _camera_record(self):
        def worker():
            status = nova_tools.camera_status()
            if "recording" in status.lower():
                result = nova_tools.stop_recording()
            else:
                result = nova_tools.start_recording()
            self.root.after(0, lambda r=result: self._camera_result(r))
        threading.Thread(target=worker, daemon=True).start()

    def _camera_close(self):
        def worker():
            result = nova_tools.close_camera()
            self.root.after(0, lambda r=result: self._camera_result(r))
            self.root.after(0, self._close_camera_window)
        threading.Thread(target=worker, daemon=True).start()

    def _close_camera_window(self):
        try:
            if self.camera_window is not None and self.camera_window.winfo_exists():
                self.camera_window.destroy()
        except tk.TclError:
            pass
        self.camera_window = None
        self.camera_window_label = None
        self._camera_window_photo = None

    def _camera_result(self, result):
        self.add_log(result)
        self.set_status("Ready")

    def _update_camera_window(self):
        """Update only the live preview; never change the window geometry."""
        try:
            win = self.camera_window
            label = self.camera_window_label

            if win is None or not win.winfo_exists() or label is None:
                return

            frame = nova_tools.get_camera_frame()

            if frame is not None:
                import cv2
                from PIL import Image, ImageTk, ImageOps

                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame)

                width = max(320, label.winfo_width())
                height = max(240, label.winfo_height())

                # Fill the preview area while maintaining the camera's aspect
                # ratio. This gives a much larger, easier-to-see live feed.
                image = ImageOps.fit(
                    image,
                    (width, height),
                    method=Image.Resampling.LANCZOS,
                    centering=(0.5, 0.5),
                )

                self._camera_window_photo = ImageTk.PhotoImage(image)
                label.configure(
                    image=self._camera_window_photo,
                    text="",
                )

            status = nova_tools.camera_status()

            if hasattr(self, "camera_window_record_btn"):
                if "recording" in status.lower():
                    self.camera_window_record_btn.configure(
                        text="■ Stop Recording"
                    )
                else:
                    self.camera_window_record_btn.configure(
                        text="● Start Recording"
                    )

            # Only schedule the next image refresh. No geometry/position calls.
            if win.winfo_exists():
                win.after(50, self._update_camera_window)

        except tk.TclError:
            return
        except Exception:
            try:
                if self.camera_window is not None and self.camera_window.winfo_exists():
                    self.camera_window.after(100, self._update_camera_window)
            except Exception:
                pass


    # ----------------------------------------------------------------
    # Timer / stopwatch display
    # ----------------------------------------------------------------

    @staticmethod
    def _format_clock(seconds, milliseconds=False):
        seconds = max(0.0, float(seconds))

        whole_seconds = int(seconds)
        millis = int((seconds - whole_seconds) * 1000)

        hours, remainder = divmod(whole_seconds, 3600)
        minutes, secs = divmod(remainder, 60)

        if hours:
            base = f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            base = f"{minutes:02d}:{secs:02d}"

        return f"{base}.{millis:03d}" if milliseconds else base

    def _update_time_displays(self):
        """Refresh timer/stopwatch labels without parsing tool response text."""
        try:
            state = nova_tools.get_time_state()

            timer_running = bool(state["timer_running"])
            timer_remaining = float(state["timer_remaining"])

            stopwatch_running = bool(state["stopwatch_running"])
            stopwatch_elapsed = float(state["stopwatch_elapsed"])

            self.timer_display.configure(
                text=self._format_clock(timer_remaining)
            )
            self.stopwatch_display.configure(
                text=self._format_clock(
                    stopwatch_elapsed,
                    milliseconds=True
                )
            )

            if timer_running and stopwatch_running:
                status = "Timer + stopwatch running"
            elif timer_running:
                status = "Timer running"
            elif stopwatch_running:
                status = "Stopwatch running"
            else:
                status = "Ready"

            self.time_status_label.configure(text=status)

        except Exception as error:
            # Show the real reason instead of hiding it behind a generic
            # "unavailable" message. Keep the label short for the GUI.
            self.timer_display.configure(text="00:00")
            self.stopwatch_display.configure(text="00:00")
            self.time_status_label.configure(
                text=f"Time error: {type(error).__name__}"
            )

        try:
            self.root.after(100, self._update_time_displays)
        except tk.TclError:
            pass

    # ----------------------------------------------------------------
    # Chat and status
    # ----------------------------------------------------------------

    def _welcome(self):
        self.add_chat(
            "NOVA",
            "Hi! I'm NOVA. I can help with your computer, answer questions, "
            "use my tools, and research current information.",
        )

        self.add_log("Ready for your next task.")

    def add_chat(self, speaker, text):
        def update():
            self.chat.configure(state="normal")

            now = datetime.now().strftime("%H:%M")

            self.chat.insert("end", f"{now}  {speaker}\n", "speaker")
            self.chat.insert("end", f"{text}\n\n", "message")

            self.chat.tag_configure(
                "speaker",
                foreground=ACCENT if speaker == "NOVA" else PURPLE,
                font=("Segoe UI", 9, "bold"),
            )

            self.chat.tag_configure(
                "message",
                foreground=TEXT,
                font=("Segoe UI", 10),
            )

            self.chat.see("end")
            self.chat.configure(state="disabled")

        self.root.after(0, update)

    def add_log(self, text):
        def update():
            self.log.configure(state="normal")
            self.log.insert("end", f"• {text}\n")
            self.log.see("end")
            self.log.configure(state="disabled")

        try:
            self.root.after(0, update)
        except tk.TclError:
            pass

    def set_status(self, status):
        def update():
            upper = str(status).upper()

            if "ERROR" in upper:
                color = RED
                background = "#3a1d27"
            elif any(
                item in upper
                for item in ("LISTEN", "THINK", "EXECUT", "SPEAK", "ONLINE")
            ):
                color = ACCENT
                background = "#1b3048"
            else:
                color = GREEN
                background = "#173524"

            self.status_pill.configure(
                text=f"  ● {upper.title()}  ",
                fg=color,
                bg=background,
            )

            self.add_log(status)

        try:
            self.root.after(0, update)
        except tk.TclError:
            pass

    # ----------------------------------------------------------------
    # Text interaction
    # ----------------------------------------------------------------

    def send(self):
        if self.busy:
            return

        text = self.entry.get().strip()

        if not text:
            return

        self.entry.delete(0, "end")
        self.add_chat("YOU", text)

        self.busy = True
        self.send_btn.configure(state="disabled")
        self.mic_btn.configure(state="disabled")

        self.set_status("Thinking")

        threading.Thread(
            target=self._run_agent,
            args=(text,),
            daemon=True,
        ).start()

    def _run_agent(self, text):
        try:
            answer = self.agent.run(text)
        except Exception as error:
            answer = f"I ran into a problem: {error}"

        self.root.after(
            0,
            lambda result=answer: self._finish(result),
        )

    def _finish(self, answer):
        self.add_chat("NOVA", answer)
        self.tts.speak(answer)

        self.busy = False
        self.camera_window = None
        self.camera_window_label = None
        self._camera_window_photo = None

        self.send_btn.configure(state="normal")
        self.mic_btn.configure(state="normal")

        self.set_status("Ready")
        self.entry.focus_set()

    # ----------------------------------------------------------------
    # Voice interaction
    # ----------------------------------------------------------------

    def listen(self):
        if self.busy:
            return

        self.busy = True

        self.send_btn.configure(state="disabled")
        self.mic_btn.configure(state="disabled")

        self.set_status("Listening")

        threading.Thread(
            target=self._listen_worker,
            daemon=True,
        ).start()

    def _listen_worker(self):
        try:
            text = self.speech.listen()

            if not text:
                message = "I didn't catch that. Please try again."

                self.root.after(
                    0,
                    lambda msg=message: self._finish_listen(msg),
                )
                return

            self.root.after(
                0,
                lambda recognized=text: self._process_voice(recognized),
            )

        except Exception as error:
            error_message = f"Microphone error: {error}"

            self.root.after(
                0,
                lambda msg=error_message: self._finish_listen(msg),
            )

    def _finish_listen(self, message):
        self.add_chat("NOVA", message)

        self.busy = False
        self.camera_window = None
        self.camera_window_label = None
        self._camera_window_photo = None

        self.send_btn.configure(state="normal")
        self.mic_btn.configure(state="normal")

        self.set_status("Ready")

    def _process_voice(self, text):
        self.add_chat("YOU", text)
        self.set_status("Thinking")

        threading.Thread(
            target=self._run_agent,
            args=(text,),
            daemon=True,
        ).start()

    # ----------------------------------------------------------------
    # Shutdown
    # ----------------------------------------------------------------

    def _on_close(self):
        try:
            nova_tools.close_camera()
        except Exception:
            pass
        self._close_camera_window()
        try:
            self.tts.stop()
        except Exception:
            pass

        try:
            nova_tools.close_camera()
        except Exception:
            pass

        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = NovaGUI(root)
    root.mainloop()
