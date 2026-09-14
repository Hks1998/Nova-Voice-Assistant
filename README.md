# 🤖 NOVA — AI Desktop Assistant

Welcome to **NOVA**, your personal AI-powered Windows desktop assistant.

NOVA can understand text and voice commands, open applications and websites, control supported Windows settings, manage timers and stopwatches, and work with your camera.

---

## 🚀 Installation

### 1. Open the NOVA project folder

Open PowerShell and navigate to the folder where you downloaded or cloned NOVA.

```powershell
cd "path\to\NOVA_Agent_Beautified"
```

Replace `path\to\NOVA_Agent_Beautified` with your actual project location.

**Easier method:** Open the NOVA folder in File Explorer, click the address bar, type `powershell`, and press **Enter**. PowerShell will open directly in the correct folder.

### 2. Create a virtual environment

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\activate
```

### 3. Install the required packages

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Install the additional packages for the camera and Windows controls:

```powershell
pip install opencv-python pillow screen-brightness-control pycaw comtypes
```

### 4. Add your Groq API key

Create a file named:

```text
.env
```

inside the NOVA project folder.

Add:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Replace `your_groq_api_key_here` with your actual Groq API key.

> ⚠️ Keep your API key private. Never upload your `.env` file to GitHub.

### 5. Start NOVA

```powershell
python main.py
```

---

# 🎮 Using NOVA

## 💬 Text Commands

Type a command in the message box and click **Send**.

Examples:

```text
open calculator
open VS Code
open YouTube
set volume to 50 percent
increase volume
decrease brightness
set brightness to 70 percent
start timer for 5 minutes
start stopwatch
stop stopwatch
today's news
```

NOVA accepts normal conversational language.

---

## 🎤 Voice Commands

1. Click the **🎤 microphone** button.
2. Speak your command clearly.
3. NOVA will process and respond.

Examples:

```text
NOVA, increase volume
NOVA, set brightness to 60 percent
NOVA, start a stopwatch
NOVA, open VS Code
NOVA, take a picture
```

---

# 📷 Camera

Use the camera controls on the right side of the NOVA interface.

| Button | What it does |
|---|---|
| **📷 Camera** | Opens the live camera window |
| **📸 Photo** | Takes a photograph |
| **● Rec** | Starts or stops video recording |
| **Close Camera** | Closes the camera |

Make sure your webcam is connected and Windows allows Python to access it.

---

# ⏱️ Timer & Stopwatch

### Timer

```text
start timer for 10 minutes
cancel timer
how much time is left
```

### Stopwatch

```text
start stopwatch
stop stopwatch
reset stopwatch
```

The current values are shown in the **TIME TOOLS** section.

---

# 🔊 Volume & 💡 Brightness

### Volume

```text
increase volume
decrease volume
mute
unmute
set volume to 50 percent
```

### Brightness

```text
increase brightness
decrease brightness
set brightness to 70 percent
```

> Brightness control depends on Windows and your display hardware. Some external monitors do not support software brightness control.

---

# 🖥️ Applications & Websites

Examples:

```text
open calculator
open notepad
open paint
open VS Code
open Jupyter Notebook
open Tableau
open Power BI
open YouTube
```

---

# 🛑 Stopping NOVA

Close the main NOVA window to exit.

To stop voice output while NOVA is speaking, use:

```text
Stop Voice
```

---

# 🔁 Starting NOVA Again

Whenever you open a new PowerShell window, navigate to the project folder and activate the environment:

```powershell
cd "path\to\NOVA_Agent_Beautified"
.\.venv\Scripts\activate
python main.py
```

Replace `path\to\NOVA_Agent_Beautified` with the location of your project.

**Easy alternative:** Open the NOVA folder in File Explorer, type `powershell` in the address bar, press **Enter**, then run:

```powershell
.\.venv\Scripts\activate
python main.py
```

---

## ✅ Quick Start After Installation

```powershell
.\.venv\Scripts\activate
python main.py
```

**Enjoy using NOVA! 🚀**
