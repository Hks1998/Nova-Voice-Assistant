🤖 NOVA — AI Desktop Assistant

Welcome to NOVA, your personal AI-powered Windows desktop assistant.

NOVA can understand text and voice commands, open applications and websites, control supported Windows settings, manage timers and stopwatches, and work with your camera.

🚀 Installation

1. Open the NOVA project folder

Open PowerShell and run:

cd "C:\Users\harsh\OneDrive\Desktop\NOVA_Agentic_Desktop_Assistant_Beautified\NOVA_Agent_Beautified"

If your NOVA folder is somewhere else, change the path accordingly.

2. Create a virtual environment

python -m venv .venv

Activate it:

.\.venv\Scripts\activate

When it is active, you should see something similar to:

(.venv) PS C:\...>

3. Install the required packages

First install the project's packages:

python -m pip install --upgrade pip
pip install -r requirements.txt

Then install the packages used for the camera and Windows controls:

pip install opencv-python pillow screen-brightness-control pycaw comtypes

4. Add your Groq API key

Create a file named:

.env

inside the NOVA project folder.

Add:

GROQ_API_KEY=your_groq_api_key_here

Replace your_groq_api_key_here with your actual Groq API key.

⚠️ Keep your API key private. Never upload your .env file to GitHub or share it publicly.

5. Start NOVA

With the virtual environment activated:

python main.py

NOVA should now open.

🎮 Using NOVA

💬 Text Commands

Type your command in the message box and click Send.

Try:

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

You can use normal conversational language. You do not need to follow a special command format.

🎤 Voice Commands

Click the 🎤 microphone button.

Speak your command clearly.

NOVA will process it and respond.

Examples:

NOVA, increase volume
NOVA, set brightness to 60 percent
NOVA, start a stopwatch
NOVA, open VS Code
NOVA, take a picture

📷 Camera

Use the camera controls on the right side of the NOVA interface.

Button

What it does

📷 Camera

Opens the live camera window

📸 Photo

Takes a photograph

● Rec

Starts or stops video recording

Close Camera

Closes the camera

Photos and videos are saved in the NOVA camera folders created by the application.

Make sure your webcam is connected and that Windows has given Python permission to access it.

⏱️ Timer & Stopwatch

NOVA supports both timers and a stopwatch.

Timer

start timer for 10 minutes
cancel timer
how much time is left

Stopwatch

start stopwatch
stop stopwatch
reset stopwatch

The current timer and stopwatch values are displayed in the TIME TOOLS section of the NOVA interface.

🔊 Volume & 💡 Brightness

NOVA can control supported Windows system settings.

Volume

increase volume
decrease volume
mute
unmute
set volume to 50 percent

Brightness

increase brightness
decrease brightness
set brightness to 70 percent

Brightness control depends on Windows and your display hardware. Some external monitors do not allow software brightness control.

🖥️ Applications & Websites

NOVA can launch supported applications and websites.

Examples:

open calculator
open notepad
open paint
open VS Code
open Jupyter Notebook
open Tableau
open Power BI
open YouTube

🛑 Stopping NOVA

To close NOVA, simply close the main NOVA window.

To stop voice output while NOVA is speaking, use:

Stop Voice

🔁 Starting NOVA Again

Whenever you open a new PowerShell window, activate the virtual environment first:

cd "C:\Users\harsh\OneDrive\Desktop\NOVA_Agentic_Desktop_Assistant_Beautified\NOVA_Agent_Beautified"
.\.venv\Scripts\activate
python main.py

✅ Quick Start

For normal day-to-day use, these are the only commands you usually need:

cd "C:\Users\harsh\OneDrive\Desktop\NOVA_Agentic_Desktop_Assistant_Beautified\NOVA_Agent_Beautified"
.\.venv\Scripts\activate
python main.py

Enjoy using NOVA! 🚀