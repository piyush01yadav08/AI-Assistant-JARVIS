# Advanced JARVIS AI with Automation 🤖

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
