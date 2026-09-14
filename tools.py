import os
import platform
import subprocess
import webbrowser
import threading
import time

from pathlib import Path
from datetime import datetime


# Optional Windows system-control libraries are loaded dynamically.
# This avoids Pylance "could not be resolved" warnings when the packages
# are installed in a different interpreter/environment.
_PYCAW_AVAILABLE = None


# ============================================================
# SAFE APPLICATIONS
# ============================================================

SAFE_APPS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
    "explorer": "explorer.exe",

    # Windows applications
    "tableau": r"C:/Program Files/Tableau/Tableau 2026.2/bin/tableau.exe",
    "vscode": r"C:/Users/harsh/AppData/Local/Programs/Microsoft VS Code/Code.exe",
    "vs code": r"C:/Users/harsh/AppData/Local/Programs/Microsoft VS Code/Code.exe",
    "visual studio code": r"C:/Users/harsh/AppData/Local/Programs/Microsoft VS Code/Code.exe",

    "notepad++": r"C:/Program Files/Notepad++/notepad++.exe",

    "powerbi": r"C:/Program Files/Microsoft Power BI Desktop/bin/PBIDesktop.exe",

    "power bi": r"C:/Program Files/Microsoft Power BI Desktop/bin/PBIDesktop.exe",

    "mysqlworkbench": r"C:/Program Files/MySQL/MySQL Workbench 8.0/MySQLWorkbench.exe",

    "JupyterNotebook": r"C:/ProgramData/anaconda3/Scripts/jupyter-notebook.exe",

    "jupyter": r"C:/ProgramData/anaconda3/Scripts/jupyter-notebook.exe",

    "jupyternotebook": r"C:/ProgramData/anaconda3/Scripts/jupyter-notebook.exe",

    "jupyter notebook": r"C:/ProgramData/anaconda3/Scripts/jupyter-notebook.exe",

    "gitbash": r"C:/Program Files/Git/git-bash.exe",
}


# ============================================================
# WEB / APPLICATION / FILE TOOLS
# ============================================================

def open_website(url):
    url = str(url).strip()

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        webbrowser.open(url)
        return f"Opened {url}"
    except Exception as e:
        return f"Could not open website: {e}"


def _find_vscode():
    """
    Find VS Code automatically so NOVA doesn't depend on one
    exact installation path.
    """
    candidates = [
        Path(os.environ.get("LOCALAPPDATA", ""))
        / "Programs"
        / "Microsoft VS Code"
        / "Code.exe",

        Path(r"C:\Program Files\Microsoft VS Code\Code.exe"),

        Path(r"C:\Program Files (x86)\Microsoft VS Code\Code.exe"),
    ]

    for path in candidates:
        if path.exists():
            return path

    return None


def open_app(name):
    key = str(name).lower().strip()

    # Special handling for VS Code.
    if key in (
        "vscode",
        "vs code",
        "visual studio code",
    ):
        vscode = _find_vscode()

        if vscode is None:
            return (
                "I couldn't find Visual Studio Code. "
                "Please check whether it is installed."
            )

        try:
            subprocess.Popen([str(vscode)], shell=False)
            return "Opened Visual Studio Code."
        except Exception as e:
            return f"Could not open Visual Studio Code: {e}"

    if key not in SAFE_APPS:
        return (
            f"Application '{name}' is not in NOVA's "
            "safe app list."
        )

    application = SAFE_APPS[key]

    # If the entry is an executable path, give a useful
    # error when the file is missing.
    if isinstance(application, str) and (
        "\\" in application or "/" in application
    ):
        if not Path(application).exists():
            return (
                f"NOVA found '{name}' in the safe list, "
                f"but the executable was not found at:\n"
                f"{application}"
            )

    try:
        subprocess.Popen(application, shell=False)
        return f"Opened {name}."

    except Exception as e:
        return f"Could not open {name}: {e}"


def open_folder(path):
    p = Path(path).expanduser()

    if not p.exists() or not p.is_dir():
        return f"Folder does not exist: {p}"

    try:
        if platform.system() == "Windows":
            os.startfile(str(p))

        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(p)])

        else:
            subprocess.Popen(["xdg-open", str(p)])

        return f"Opened folder {p}"

    except Exception as e:
        return f"Could not open folder: {e}"


def list_files(path="."):
    p = Path(path).expanduser()

    if not p.exists() or not p.is_dir():
        return f"Folder does not exist: {p}"

    try:
        items = sorted(
            p.iterdir(),
            key=lambda x: (
                not x.is_dir(),
                x.name.lower()
            )
        )[:100]

        if not items:
            return "The folder is empty."

        return "\n".join(
            (
                "[DIR] "
                if item.is_dir()
                else "[FILE] "
            ) + item.name
            for item in items
        )

    except Exception as e:
        return f"Could not list files: {e}"


def current_time():
    return datetime.now().strftime(
        "%A, %d %B %Y, %I:%M:%S %p"
    )


def calculate(expression):
    # Restricted calculator. No builtins, variables or imports.
    allowed = set(
        "0123456789+-*/().% "
    )

    if not expression:
        return "Please provide an arithmetic expression."

    if any(char not in allowed for char in expression):
        return "Only basic arithmetic is allowed."

    try:
        return str(
            eval(
                expression,
                {"__builtins__": {}},
                {}
            )
        )

    except Exception as e:
        return f"Calculation error: {e}"


def take_screenshot(path="nova_screenshot.png"):
    try:
        import pyautogui

        screenshot = pyautogui.screenshot()
        screenshot.save(path)

        return (
            "Screenshot saved to "
            f"{Path(path).resolve()}"
        )

    except Exception as e:
        return f"Screenshot failed: {e}"


# ============================================================
# STOPWATCH
# ============================================================

_stopwatch_lock = threading.Lock()
_stopwatch_start = None
_stopwatch_elapsed = 0.0


def _format_duration(seconds, include_milliseconds=False):
    seconds = max(0.0, float(seconds))

    whole_seconds = int(seconds)
    milliseconds = int((seconds - whole_seconds) * 1000)

    hours, remainder = divmod(whole_seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    if hours:
        base = f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        base = f"{minutes:02d}:{secs:02d}"

    if include_milliseconds:
        return f"{base}.{milliseconds:03d}"

    return base


def get_time_state():
    """
    Return the live timer and stopwatch state for the NOVA GUI.

    The GUI uses this public function to read the current values directly
    instead of parsing timer_status()/stopwatch_status() response text.
    """
    with _timer_lock:
        timer_running = (
            _timer_cancel is not None
            and _timer_end is not None
        )

        if timer_running:
            timer_remaining = max(
                0.0,
                _timer_end - time.monotonic()
            )
        else:
            timer_remaining = 0.0

    with _stopwatch_lock:
        stopwatch_running = _stopwatch_start is not None
        stopwatch_elapsed = _stopwatch_elapsed

        if stopwatch_running:
            stopwatch_elapsed += (
                time.monotonic() - _stopwatch_start
            )

    return {
        "timer_running": timer_running,
        "timer_remaining": timer_remaining,
        "stopwatch_running": stopwatch_running,
        "stopwatch_elapsed": max(0.0, stopwatch_elapsed),
    }


def start_stopwatch():
    global _stopwatch_start

    with _stopwatch_lock:

        if _stopwatch_start is not None:
            return "The stopwatch is already running."

        _stopwatch_start = time.monotonic()

    return "Stopwatch started."


def stop_stopwatch():
    global _stopwatch_start
    global _stopwatch_elapsed

    with _stopwatch_lock:

        if _stopwatch_start is None:
            return (
                "Stopwatch is already stopped at "
                f"{_format_duration(_stopwatch_elapsed)}."
            )

        _stopwatch_elapsed += (
            time.monotonic() - _stopwatch_start
        )

        _stopwatch_start = None

        elapsed = _stopwatch_elapsed

    return (
        "Stopwatch stopped at "
        f"{_format_duration(elapsed)}."
    )


def reset_stopwatch():
    global _stopwatch_start
    global _stopwatch_elapsed

    with _stopwatch_lock:
        _stopwatch_start = None
        _stopwatch_elapsed = 0.0

    return "Stopwatch reset to 00:00."


def stopwatch_status():
    with _stopwatch_lock:

        elapsed = _stopwatch_elapsed
        running = _stopwatch_start is not None

        if running:
            elapsed += (
                time.monotonic() - _stopwatch_start
            )

    state = "running" if running else "stopped"

    return (
        f"Stopwatch: {_format_duration(elapsed)} "
        f"({state})."
    )


# ============================================================
# COUNTDOWN TIMER
# ============================================================

_timer_lock = threading.Lock()
_timer_cancel = None
_timer_end = None

def _timer_alert():
    """Trigger a reliable Windows alert when the timer finishes."""
    try:
        if platform.system() == "Windows":
            import winsound
            import ctypes

            # Audible alert
            for _ in range(3):
                winsound.MessageBeep(
                    winsound.MB_ICONEXCLAMATION
                )
                time.sleep(0.35)

            # Visible Windows popup
            ctypes.windll.user32.MessageBoxW(
                0,
                "Your NOVA timer has finished.",
                "NOVA Timer",
                0x00000040
            )

        else:
            print("\a")
            print("NOVA TIMER FINISHED")

    except Exception as e:
        print(f"Timer alert error: {e}")


def start_timer(seconds):
    global _timer_cancel
    global _timer_end

    try:
        seconds = float(seconds)
    except (TypeError, ValueError):
        return "Timer duration must be a number of seconds."

    if seconds <= 0:
        return "Timer duration must be greater than zero."

    with _timer_lock:
        if _timer_cancel is not None:
            return "A timer is already running."

        _timer_cancel = threading.Event()
        cancel_event = _timer_cancel

        _timer_end = time.monotonic() + seconds

    threading.Thread(
        target=_timer_worker,
        args=(cancel_event,),
        daemon=True,
        name="NOVA-Timer"
    ).start()

    return (
        f"Timer started for "
        f"{_format_duration(seconds)}."
    )


def _timer_worker(cancel_event):
    global _timer_cancel
    global _timer_end

    while not cancel_event.is_set():

        with _timer_lock:
            end = _timer_end

        if end is None:
            return

        remaining = end - time.monotonic()

        if remaining <= 0:
            break

        # Check frequently so cancellation is responsive.
        cancel_event.wait(min(remaining, 0.2))

    finished = not cancel_event.is_set()

    with _timer_lock:
        # Only this timer is allowed to clear its own state.
        if _timer_cancel is cancel_event:
            _timer_cancel = None
            _timer_end = None

    if finished:
        print("⏰ NOVA TIMER FINISHED")
        _timer_alert()


def cancel_timer():
    global _timer_cancel
    global _timer_end

    with _timer_lock:
        if _timer_cancel is None:
            return "There is no active timer."

        _timer_cancel.set()
        _timer_cancel = None
        _timer_end = None

    return "Timer cancelled."


def timer_status():
    with _timer_lock:
        if _timer_cancel is None or _timer_end is None:
            return "No timer is currently running."

        remaining = max(
            0,
            _timer_end - time.monotonic()
        )

    return (
        "Timer remaining: "
        f"{_format_duration(remaining)}."
    )


# ============================================================
# CAMERA / PHOTO / VIDEO TOOLS
# ============================================================

_camera_lock = threading.Lock()
_camera_capture = None
_camera_thread = None
_camera_stop_event = None
_camera_frame = None
_camera_recording = False
_camera_writer = None
_camera_video_path = None


def _camera_worker(stop_event):
    global _camera_capture
    global _camera_frame
    global _camera_recording
    global _camera_writer

    while not stop_event.is_set():
        with _camera_lock:
            capture = _camera_capture

        if capture is None:
            break

        ok, frame = capture.read()
        if not ok:
            time.sleep(0.03)
            continue

        with _camera_lock:
            _camera_frame = frame.copy()

            if _camera_recording and _camera_writer is not None:
                try:
                    _camera_writer.write(frame)
                except Exception:
                    pass

        time.sleep(0.01)

    with _camera_lock:
        writer = _camera_writer
        _camera_writer = None
        _camera_recording = False

    if writer is not None:
        try:
            writer.release()
        except Exception:
            pass


def open_camera(camera_index=0):
    """Start NOVA's webcam and make its live frame available to the GUI."""
    global _camera_capture
    global _camera_thread
    global _camera_stop_event
    global _camera_frame

    try:
        camera_index = int(camera_index)
    except (TypeError, ValueError):
        camera_index = 0

    with _camera_lock:
        if _camera_capture is not None:
            return "Camera is already running."

    try:
        import cv2
    except ImportError:
        return "OpenCV is not installed. Run: pip install opencv-python"

    capture = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)

    if not capture.isOpened():
        capture.release()
        # Try the default backend as a fallback.
        capture = cv2.VideoCapture(camera_index)

    if not capture.isOpened():
        capture.release()
        return "I couldn't open the camera. Check that your webcam is connected and not being used by another application."

    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    stop_event = threading.Event()

    with _camera_lock:
        _camera_capture = capture
        _camera_stop_event = stop_event
        _camera_frame = None

    thread = threading.Thread(
        target=_camera_worker,
        args=(stop_event,),
        daemon=True,
        name="NOVA-Camera",
    )

    with _camera_lock:
        _camera_thread = thread

    thread.start()
    return "Camera started."


def get_camera_frame():
    """Return a copy of the latest webcam frame, or None if inactive."""
    with _camera_lock:
        if _camera_frame is None:
            return None
        return _camera_frame.copy()


def take_photo(filename=None):
    """Capture the latest webcam frame and save it as a JPEG."""
    global _camera_frame

    try:
        import cv2
    except ImportError:
        return "OpenCV is not installed. Run: pip install opencv-python"

    with _camera_lock:
        frame = None if _camera_frame is None else _camera_frame.copy()
        camera_active = _camera_capture is not None

    if not camera_active:
        started = open_camera()
        if "started" not in started.lower() and "already" not in started.lower():
            return started

        # Give the camera worker a moment to provide the first frame.
        deadline = time.monotonic() + 3
        while frame is None and time.monotonic() < deadline:
            time.sleep(0.05)
            with _camera_lock:
                frame = None if _camera_frame is None else _camera_frame.copy()

    if frame is None:
        return "The camera is running, but no video frame is available yet."

    camera_dir = Path.home() / "Pictures" / "NOVA_Camera"
    camera_dir.mkdir(parents=True, exist_ok=True)

    if filename:
        path = Path(str(filename)).expanduser()
        if not path.is_absolute():
            path = camera_dir / path
        if path.suffix.lower() not in (".jpg", ".jpeg", ".png"):
            path = path.with_suffix(".jpg")
    else:
        path = camera_dir / f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]}.jpg"

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if cv2.imwrite(str(path), frame):
            return f"Photo saved to {path}"
        return "I couldn't save the photo."
    except Exception as e:
        return f"Photo capture failed: {e}"


def start_recording(filename=None):
    """Start recording the live webcam stream to an MP4 file."""
    global _camera_recording
    global _camera_writer
    global _camera_video_path

    try:
        import cv2
    except ImportError:
        return "OpenCV is not installed. Run: pip install opencv-python"

    with _camera_lock:
        camera_active = _camera_capture is not None
        already_recording = _camera_recording

    if already_recording:
        return f"Recording is already running: {_camera_video_path}"

    if not camera_active:
        result = open_camera()
        if "started" not in result.lower() and "already" not in result.lower():
            return result

        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            with _camera_lock:
                if _camera_frame is not None:
                    break
            time.sleep(0.05)

    with _camera_lock:
        frame = None if _camera_frame is None else _camera_frame.copy()

    if frame is None:
        return "The camera is running, but no video frame is available yet."

    camera_dir = Path.home() / "Videos" / "NOVA_Camera"
    camera_dir.mkdir(parents=True, exist_ok=True)

    if filename:
        path = Path(str(filename)).expanduser()
        if not path.is_absolute():
            path = camera_dir / path
        if path.suffix.lower() != ".mp4":
            path = path.with_suffix(".mp4")
    else:
        path = camera_dir / f"video_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]}.mp4"

    height, width = frame.shape[:2]
    fps = 20.0

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, fps, (width, height))

    if not writer.isOpened():
        writer.release()
        return "I couldn't create the video file."

    with _camera_lock:
        _camera_writer = writer
        _camera_video_path = path
        _camera_recording = True

    return f"Recording started: {path}"


def stop_recording():
    """Stop the active webcam recording."""
    global _camera_recording
    global _camera_writer
    global _camera_video_path

    with _camera_lock:
        if not _camera_recording:
            return "No video recording is currently running."

        writer = _camera_writer
        path = _camera_video_path
        _camera_writer = None
        _camera_recording = False
        _camera_video_path = None

    if writer is not None:
        try:
            writer.release()
        except Exception:
            pass

    return f"Recording stopped. Video saved to {path}"


def camera_status():
    """Return the current camera/recording state."""
    with _camera_lock:
        camera_running = _camera_capture is not None
        recording = _camera_recording
        path = _camera_video_path

    if recording:
        return f"Camera is running and recording to {path}."
    if camera_running:
        return "Camera is running."
    return "Camera is closed."


def close_camera():
    """Stop the webcam and release all camera resources."""
    global _camera_capture
    global _camera_thread
    global _camera_stop_event
    global _camera_frame
    global _camera_recording
    global _camera_writer
    global _camera_video_path

    with _camera_lock:
        capture = _camera_capture
        stop_event = _camera_stop_event
        writer = _camera_writer

        _camera_capture = None
        _camera_thread = None
        _camera_stop_event = None
        _camera_frame = None
        _camera_recording = False
        _camera_writer = None
        _camera_video_path = None

    if stop_event is not None:
        stop_event.set()

    if writer is not None:
        try:
            writer.release()
        except Exception:
            pass

    if capture is not None:
        try:
            capture.release()
        except Exception:
            pass

    return "Camera closed."


# ============================================================
# WINDOWS SYSTEM CONTROLS — VOLUME / BRIGHTNESS
# ============================================================

def _native_volume_key(vk_code, presses=1):
    """Send a Windows hardware-volume key without requiring pycaw."""
    if platform.system() != "Windows":
        return "Native Windows volume controls are only available on Windows."

    try:
        import ctypes

        user32 = ctypes.windll.user32
        KEYEVENTF_KEYUP = 0x0002

        presses = max(1, int(presses))
        for _ in range(presses):
            user32.keybd_event(vk_code, 0, 0, 0)
            user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)
            time.sleep(0.03)

        return None
    except Exception as e:
        return f"Windows volume control failed: {e}"


# Windows multimedia virtual-key codes.
_VK_VOLUME_MUTE = 0xAD
_VK_VOLUME_DOWN = 0xAE
_VK_VOLUME_UP = 0xAF


def _send_volume_key(vk_code, presses=1):
    """Send native Windows multimedia volume keys."""
    if platform.system() != "Windows":
        return "Native Windows volume controls are only available on Windows."

    try:
        import ctypes

        user32 = ctypes.windll.user32
        key_up = 0x0002
        for _ in range(max(1, int(presses))):
            user32.keybd_event(vk_code, 0, 0, 0)
            user32.keybd_event(vk_code, 0, key_up, 0)
            time.sleep(0.025)
        return None
    except Exception as e:
        return f"Windows volume control failed: {e}"


_VK_VOLUME_MUTE = 0xAD
_VK_VOLUME_DOWN = 0xAE
_VK_VOLUME_UP = 0xAF


def _try_exact_volume_with_pycaw(target):
    """
    Try exact Windows endpoint-volume control through pycaw.
    Returns True on success and False when pycaw/COM is unavailable.
    """
    try:
        from importlib import import_module

        pycaw_module = import_module("pycaw.pycaw")
        comtypes_module = import_module("comtypes")

        AudioUtilities = getattr(pycaw_module, "AudioUtilities")
        IAudioEndpointVolume = getattr(
            pycaw_module, "IAudioEndpointVolume"
        )

        comtypes_module.CoInitialize()
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_,
                comtypes_module.CLSCTX_ALL,
                None,
            )
            endpoint = interface.QueryInterface(IAudioEndpointVolume)
            endpoint.SetMasterVolumeLevelScalar(float(target) / 100.0, None)

            if target > 0 and endpoint.GetMute():
                endpoint.SetMute(0, None)

            return True
        finally:
            comtypes_module.CoUninitialize()

    except Exception:
        return False


def set_volume(percent):
    """
    Set Windows master volume to a requested percentage.

    NOVA treats phrases such as 'set volume to 50%', 'reduce volume to
    50%', and 'lower volume to 50%' as an absolute target, not a relative
    decrease.
    """
    try:
        target = max(0.0, min(100.0, float(percent)))
    except (TypeError, ValueError):
        return "Volume must be a number from 0 to 100 percent."

    # Preferred path: exact endpoint volume.
    if _try_exact_volume_with_pycaw(target):
        return f"System volume set to {round(target)}%."

    # Fallback: native Windows volume keys. Windows volume steps are normally
    # about 2 percentage points. Saturate downward first, then step upward to
    # the requested target so the result does not depend on the previous level.
    down_error = _send_volume_key(
        _VK_VOLUME_DOWN,
        55
    )
    if down_error:
        return down_error

    up_presses = round(target / 2.0)

    if up_presses:
        up_error = _send_volume_key(_VK_VOLUME_UP, up_presses)
        if up_error:
            return up_error

    return (
        f"System volume set to approximately {round(target)}% "
        f"using Windows native controls."
    )


def increase_volume(amount=10):
    """Increase Windows master volume by the requested number of percentage points."""
    try:
        amount = abs(float(amount))
    except (TypeError, ValueError):
        amount = 10.0

    # Try exact current-level adjustment with pycaw first.
    try:
        from importlib import import_module

        pycaw_module = import_module("pycaw.pycaw")
        comtypes_module = import_module("comtypes")
        AudioUtilities = getattr(pycaw_module, "AudioUtilities")
        IAudioEndpointVolume = getattr(
            pycaw_module, "IAudioEndpointVolume"
        )

        comtypes_module.CoInitialize()
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_,
                comtypes_module.CLSCTX_ALL,
                None,
            )
            endpoint = interface.QueryInterface(IAudioEndpointVolume)
            current = float(endpoint.GetMasterVolumeLevelScalar()) * 100.0
            target = min(100.0, current + amount)
            endpoint.SetMasterVolumeLevelScalar(target / 100.0, None)
            if target > 0 and endpoint.GetMute():
                endpoint.SetMute(0, None)
            return f"System volume increased to {round(target)}%."
        finally:
            comtypes_module.CoUninitialize()
    except Exception:
        pass

    presses = max(1, round(amount / 2.0))
    error = _send_volume_key(_VK_VOLUME_UP, presses)
    return error if error else f"System volume increased by approximately {presses * 2}%."


def decrease_volume(amount=10):
    """Decrease Windows master volume by the requested number of percentage points."""
    try:
        amount = abs(float(amount))
    except (TypeError, ValueError):
        amount = 10.0

    try:
        from importlib import import_module

        pycaw_module = import_module("pycaw.pycaw")
        comtypes_module = import_module("comtypes")
        AudioUtilities = getattr(pycaw_module, "AudioUtilities")
        IAudioEndpointVolume = getattr(
            pycaw_module, "IAudioEndpointVolume"
        )

        comtypes_module.CoInitialize()
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_,
                comtypes_module.CLSCTX_ALL,
                None,
            )
            endpoint = interface.QueryInterface(IAudioEndpointVolume)
            current = float(endpoint.GetMasterVolumeLevelScalar()) * 100.0
            target = max(0.0, current - amount)
            endpoint.SetMasterVolumeLevelScalar(target / 100.0, None)
            return f"System volume decreased to {round(target)}%."
        finally:
            comtypes_module.CoUninitialize()
    except Exception:
        pass

    presses = max(1, round(amount / 2.0))
    error = _send_volume_key(_VK_VOLUME_DOWN, presses)
    return error if error else f"System volume decreased by approximately {presses * 2}%."


def mute_volume():
    """Mute Windows master volume using the native Windows volume control."""
    error = _send_volume_key(_VK_VOLUME_MUTE)
    return error if error else "System volume muted."


def unmute_volume():
    """Unmute Windows master volume using the native Windows volume control."""
    error = _send_volume_key(_VK_VOLUME_MUTE)
    return error if error else "System volume unmuted."


def get_volume():
    """Return Windows volume-control availability."""
    try:
        from importlib import import_module
        import_module("pycaw.pycaw")
        return "Windows system volume control is available, including exact percentage control."
    except Exception:
        return "Windows native volume control is available. Exact percentage uses a native key fallback."


def _load_brightness_control():
    """Load screen-brightness-control only when brightness is requested."""
    try:
        from importlib import import_module
        return import_module("screen_brightness_control")
    except Exception:
        return None


def _powershell_brightness_get():
    """Read primary-display brightness through Windows WMI."""
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-Command",
                "(Get-CimInstance -Namespace root/WMI "
                "-ClassName WmiMonitorBrightness | "
                "Select-Object -First 1 -ExpandProperty CurrentBrightness)"
            ],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except Exception:
        pass
    return None


def _powershell_brightness_set(value):
    """Set primary-display brightness through Windows WMI."""
    try:
        command = (
            "$m = Get-CimInstance -Namespace root/WMI "
            "-ClassName WmiMonitorBrightnessMethods; "
            "$m | ForEach-Object { $_.WmiSetBrightness(1, "
            f"{int(value)}) }}"
        )
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-Command", command
            ],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return result.returncode == 0
    except Exception:
        return False


def _read_brightness_value():
    """Read brightness using screen-brightness-control, then WMI."""
    sbc = _load_brightness_control()

    if sbc is not None:
        try:
            values = sbc.get_brightness()
            if isinstance(values, (list, tuple)):
                values = values[0] if values else None
            if values is not None:
                return float(values)
        except Exception:
            pass

    return _powershell_brightness_get()


def _set_brightness_value(value):
    """Set brightness with verification and a Windows WMI fallback."""
    value = int(max(0, min(100, round(float(value)))))

    sbc = _load_brightness_control()
    if sbc is not None:
        try:
            sbc.set_brightness(value)
            time.sleep(0.15)
            current = _read_brightness_value()
            if current is not None and abs(current - value) <= 2:
                return True
        except Exception:
            pass

    return _powershell_brightness_set(value)



def get_brightness():
    """Get the current primary-display brightness."""
    value = _read_brightness_value()
    if value is None:
        return (
            "I couldn't read the display brightness. "
            "Your display may not expose software brightness control."
        )
    return f"Screen brightness is {round(value)}%."


def set_brightness(percent):
    """Set primary-display brightness to 0–100 percent."""
    try:
        value = max(0.0, min(100.0, float(percent)))
    except (TypeError, ValueError):
        return "Brightness must be a number from 0 to 100 percent."

    if _set_brightness_value(value):
        return f"Screen brightness set to {round(value)}%."

    return (
        "I couldn't change the screen brightness. "
        "This can happen with external monitors or displays whose "
        "driver does not expose software brightness control."
    )


def increase_brightness(amount=10):
    """Increase primary-display brightness."""
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        amount = 10.0

    current = _read_brightness_value()
    if current is None:
        return "I couldn't read the current screen brightness."

    target = min(100.0, current + amount)
    return set_brightness(target)


def decrease_brightness(amount=10):
    """Decrease primary-display brightness."""
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        amount = 10.0

    current = _read_brightness_value()
    if current is None:
        return "I couldn't read the current screen brightness."

    target = max(0.0, current - amount)
    return set_brightness(target)




# ============================================================
# GROQ TOOL SCHEMA HELPER
# ============================================================

def _schema(properties=None, required=None):
    return {
        "type": "object",
        "properties": properties or {},
        "required": required or [],
    }


# ============================================================
# LOCAL TOOL REGISTRY
# ============================================================

LOCAL_TOOLS = {

    "open_website": {
        "description": (
            "Open a website in the default browser."
        ),
        "function": open_website,
        "schema": _schema(
            {
                "url": {
                    "type": "string"
                }
            },
            ["url"]
        ),
    },

    "open_app": {
        "description": (
            "Open a safe desktop application. "
            "Available applications include: "
            "Git Bash, Jupyter Notebook, MySQL Workbench, "
            "Power BI, VS Code, Notepad++, Tableau, "
            "Notepad, Calculator, Paint and Explorer."
        ),
        "function": open_app,
        "schema": _schema(
            {
                "name": {
                    "type": "string"
                }
            },
            ["name"]
        ),
    },

    "open_folder": {
        "description": (
            "Open an existing local folder."
        ),
        "function": open_folder,
        "schema": _schema(
            {
                "path": {
                    "type": "string"
                }
            },
            ["path"]
        ),
    },

    "list_files": {
        "description": (
            "List files in an existing local directory."
        ),
        "function": list_files,
        "schema": _schema(
            {
                "path": {
                    "type": "string"
                }
            }
        ),
    },

    "current_time": {
        "description": (
            "Get the local computer date and time."
        ),
        "function": current_time,
        "schema": _schema(),
    },

    "calculate": {
        "description": (
            "Perform basic arithmetic."
        ),
        "function": calculate,
        "schema": _schema(
            {
                "expression": {
                    "type": "string"
                }
            },
            ["expression"]
        ),
    },

    "take_screenshot": {
        "description": (
            "Take a screenshot and save it locally."
        ),
        "function": take_screenshot,
        "schema": _schema(
            {
                "path": {
                    "type": "string"
                }
            }
        ),
    },

    # --------------------------------------------------------
    # Stopwatch
    # --------------------------------------------------------

    "start_stopwatch": {
        "description": (
            "Start the NOVA stopwatch."
        ),
        "function": start_stopwatch,
        "schema": _schema(),
    },

    "stop_stopwatch": {
        "description": (
            "Stop the NOVA stopwatch and report "
            "the elapsed time."
        ),
        "function": stop_stopwatch,
        "schema": _schema(),
    },

    "reset_stopwatch": {
        "description": (
            "Reset the NOVA stopwatch to zero."
        ),
        "function": reset_stopwatch,
        "schema": _schema(),
    },

    "stopwatch_status": {
        "description": (
            "Report the current NOVA stopwatch time."
        ),
        "function": stopwatch_status,
        "schema": _schema(),
    },

    # --------------------------------------------------------
    # Countdown timer
    # --------------------------------------------------------

    "start_timer": {
        "description": (
            "Start a countdown timer. Convert the "
            "requested minutes or hours into seconds."
        ),
        "function": start_timer,
        "schema": _schema(
            {
                "seconds": {
                    "type": "number",
                    "description": (
                        "Timer duration in seconds."
                    ),
                }
            },
            ["seconds"]
        ),
    },

    "cancel_timer": {
        "description": (
            "Cancel the currently active countdown timer."
        ),
        "function": cancel_timer,
        "schema": _schema(),
    },

    "timer_status": {
        "description": (
            "Report the remaining time on the active "
            "countdown timer."
        ),
        "function": timer_status,
        "schema": _schema(),
    },
    # --------------------------------------------------------
    # Windows volume
    # --------------------------------------------------------

    "get_volume": {
        "description": (
            "Read the current Windows system master volume. "
            "Use for commands like 'what is the volume'."
        ),
        "function": get_volume,
        "schema": _schema(),
    },

    "set_volume": {
        "description": (
            "Set Windows system master volume to an ABSOLUTE percentage from "
            "0 to 100. Use this tool for phrases such as 'set volume to "
            "50 percent', 'reduce volume to 50 percent', 'lower volume to "
            "50%', or 'make the volume 50%'. Do NOT use decrease_volume "
            "when the user specifies a target percentage."
        ),
        "function": set_volume,
        "schema": _schema(
            {"percent": {"type": "number"}},
            ["percent"]
        ),
    },

    "increase_volume": {
        "description": (
            "Increase Windows system master volume. "
            "Default amount is 10 percentage points."
        ),
        "function": increase_volume,
        "schema": _schema(
            {"amount": {"type": "number"}}
        ),
    },

    "decrease_volume": {
        "description": (
            "Decrease Windows system master volume. "
            "Default amount is 10 percentage points."
        ),
        "function": decrease_volume,
        "schema": _schema(
            {"amount": {"type": "number"}}
        ),
    },

    "mute_volume": {
        "description": "Mute the Windows system master volume.",
        "function": mute_volume,
        "schema": _schema(),
    },

    "unmute_volume": {
        "description": "Unmute the Windows system master volume.",
        "function": unmute_volume,
        "schema": _schema(),
    },

    # --------------------------------------------------------
    # Windows brightness
    # --------------------------------------------------------

    "get_brightness": {
        "description": (
            "Read the current primary-display brightness. "
            "Use for commands like 'what is the brightness'."
        ),
        "function": get_brightness,
        "schema": _schema(),
    },

    "set_brightness": {
        "description": (
            "Set primary display brightness from 0 to 100 percent. "
            "Use for commands like 'set brightness to 70 percent'."
        ),
        "function": set_brightness,
        "schema": _schema(
            {"percent": {"type": "number"}},
            ["percent"]
        ),
    },

    "increase_brightness": {
        "description": (
            "Increase primary display brightness. "
            "Default amount is 10 percentage points."
        ),
        "function": increase_brightness,
        "schema": _schema(
            {"amount": {"type": "number"}}
        ),
    },

    "decrease_brightness": {
        "description": (
            "Decrease primary display brightness. "
            "Default amount is 10 percentage points."
        ),
        "function": decrease_brightness,
        "schema": _schema(
            {"amount": {"type": "number"}}
        ),
    },

    # --------------------------------------------------------
    # Camera / photo / video
    # --------------------------------------------------------

    "open_camera": {
        "description": (
            "Start NOVA's webcam and show its live preview in the GUI."
        ),
        "function": open_camera,
        "schema": _schema(
            {"camera_index": {"type": "integer"}},
        ),
    },

    "take_photo": {
        "description": (
            "Take a picture with NOVA's webcam and save it locally."
        ),
        "function": take_photo,
        "schema": _schema(
            {"filename": {"type": "string"}},
        ),
    },

    "start_recording": {
        "description": (
            "Start recording video from NOVA's webcam and save it as MP4."
        ),
        "function": start_recording,
        "schema": _schema(
            {"filename": {"type": "string"}},
        ),
    },

    "stop_recording": {
        "description": (
            "Stop the active NOVA webcam video recording."
        ),
        "function": stop_recording,
        "schema": _schema(),
    },

    "camera_status": {
        "description": (
            "Report whether NOVA's camera is running and whether it is recording."
        ),
        "function": camera_status,
        "schema": _schema(),
    },

    "close_camera": {
        "description": (
            "Close NOVA's webcam and release the camera."
        ),
        "function": close_camera,
        "schema": _schema(),
    },
    

    
}
