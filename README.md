# Advanced JARVIS AI with Automation 🤖
# 🤖 JARVIS AI Assistant (Basic UI + Full PC Automation)

An advanced **voice-controlled AI assistant** built using Python with a modern GUI and full system automation capabilities.

---

## 🚀 Features

### 🧠 AI Assistant

* Voice recognition (Speech-to-Text)
* Text-to-Speech response
* Smart command handling

### 🖥️ Modern GUI

* Dark futuristic interface
* Real-time chat display
* Live digital clock
* Start / Stop controls
* Status indicator (Listening / Idle)

### 💻 Full PC Automation

* Shutdown / Restart system
* Volume control (up/down/mute)
* Screenshot capture
* Copy / Paste automation
* Open applications (Chrome, VS Code)
* Web search automation

---

## 🛠️ Tech Stack

* **Python**
* **Tkinter** (GUI)
* **SpeechRecognition** (Voice Input)
* **pyttsx3** (Voice Output)
* **PyAutoGUI** (Automation)
* **Keyboard** (Hotkeys)
* **OS / Webbrowser modules**

---

## 📁 Project Structure

```
jarvis-ai/
│── main.py
│── gui.py
│── requirements.txt
│── README.md
│
├── utils/
│   ├── listen.py
│   ├── speak.py
│
├── commands/
│   ├── basic_commands.py
│   ├── system_automation.py
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/jarvis-ai.git
cd jarvis-ai
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Run Application

```bash
python main.py
```

---

## 🎤 Example Voice Commands

* “Open Google”
* “Search Python tutorials”
* “What is the time”
* “Take screenshot”
* “Volume up”
* “Shutdown system”
* “Copy / Paste”

---

## ⚠️ Important Notes

* Run terminal as **Administrator** (required for automation features)
* Ensure microphone access is enabled
* First-time voice recognition may take a few seconds

---



## 🔮 Future Enhancements

* ChatGPT integration (real AI conversation)
* Wake word detection ("Hey Jarvis")
* Face recognition login
* Mobile app integration
* Advanced animations 

---

## 💼 Use Case

This project demonstrates:

* AI integration
* GUI development
* System automation
* Real-world application design



---

## 👨‍💻 Author

**Piyush Yadav**

* LinkedIn: https://www.linkedin.com/in/piyush-yadav-48ba81324
* Email: [piyushyadav24680@gmail.com](mailto:piyushyadav24680@gmail.com)

---

## ⭐ Show Your Support

If you like this project:

* ⭐ Star the repo
* 🍴 Fork it
* 🧠 Improve it

---

## ⚡ Tagline

> "Your Personal AI Assistant — Inspired by JARVIS, Built with Python"

## Features
- Voice and typed natural-language requests
- Reliable noise-aware voice recognition with forgiving speech timing
- Say `recalibrate microphone` after moving to a noisier or quieter room
- Uses the microphone selected in Windows Settings; set `JARVIS_MICROPHONE_INDEX` only if you need to override it
- App, website, search, folder, window, browser, typing and clipboard controls
- Opens installed apps by checking Windows app registrations, Start Menu shortcuts, Windows Start apps, and app aliases
- Opens files (including `.pdf`, `.docx`, `.png`, and other extensions) from common personal folders
- Screenshots saved under `Pictures/Jarvis Screenshots`
- Brightness controls (`brightness up`, `brightness down`, `set brightness to 60`) on supported laptop displays
- Media, volume, browser tab, task-view, virtual-desktop, and window snap controls
- Creates folders safely in Documents, Desktop, or Downloads
- Safe confirmation before shutdown, restart, or sleep
- Hands-free wake word: say `Hey Jarvis`; say `Bye Jarvis` to close the app
- Automatically registers itself to start when you sign in to Windows
- After waking, JARVIS keeps listening in the background; press `Ctrl+Alt+J` to show its window again
- Password-protected access; say `lock Jarvis` to lock immediately
- Local persistent conversation memory: say `remember that ...`; clear it with `forget our conversations`
- Answers basic factual questions using a web lookup when no saved memory applies
- Spoken interactive conversation with friendly, emotionally expressive tones and matching orb moods
- Optional private local AI chat via Ollama; set `JARVIS_OLLAMA_MODEL` to choose a downloaded model
- Change credentials securely with `change Jarvis password` after unlocking

## Examples
`Could you open Chrome`, `search for weather in Delhi`, `show desktop`,
`switch window`, `take a screenshot`, `type hello there`, `close Notepad`.
You can also say `Hey Jarvis, open Chrome` in one phrase.

## Run
pip install -r requirements.txt
python main.py
