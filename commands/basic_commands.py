"""Intent router for JARVIS desktop actions."""
import datetime
import os
import re
import shutil
import subprocess
import webbrowser
import winreg
from pathlib import Path
from urllib.parse import quote_plus

import psutil

from commands.natural_language import extract_after, normalise, search_terms
from commands.system_automation import system_control
from utils.memory import ConversationMemory, web_answer
from utils.conversation import conversation
from utils.ai_chat import chat_reply
from utils.listen import reset_calibration
from utils.speak import speak

apps = {
    "notepad": "notepad.exe", "calculator": "calc.exe", "paint": "mspaint.exe",
    "file explorer": "explorer.exe", "explorer": "explorer.exe", "command prompt": "cmd.exe",
    "powershell": "powershell.exe", "chrome": "chrome.exe", "firefox": "firefox.exe",
    "edge": "msedge.exe", "word": "winword.exe", "excel": "excel.exe",
    "powerpoint": "powerpnt.exe", "outlook": "outlook.exe", "teams": "teams.exe",
    "zoom": "zoom.exe", "vlc": "vlc.exe", "spotify": "spotify.exe", "discord": "discord.exe",
    "vscode": "code.exe", "visual studio code": "code.exe", "notion": "notion.exe",
    "slack": "slack.exe", "whatsapp": "whatsapp.exe", "telegram": "telegram.exe",
    "task manager": "taskmgr.exe", "control panel": "control.exe", "settings": "ms-settings:",
}

WEBSITES = {
    "google": "https://google.com", "youtube": "https://youtube.com", "gmail": "https://mail.google.com",
    "github": "https://github.com", "wikipedia": "https://wikipedia.org", "facebook": "https://facebook.com",
    "instagram": "https://instagram.com", "linkedin": "https://linkedin.com", "netflix": "https://netflix.com",
}
POWER_ACTIONS = {"shutdown", "restart", "sleep", "sleep computer"}
pending_power_action = None
memory = ConversationMemory()


def _say(message):
    speak(message)
    memory.add_message("jarvis", message)
    return message


def _is_question(command):
    prefixes = ("what ", "who ", "when ", "where ", "why ", "how ", "tell me about ", "define ", "explain ")
    return command.startswith(prefixes) or command in {"what is this", "help me"}


def _should_remember(command):
    """Avoid retaining text that is likely to contain credentials or typed secrets."""
    return not command.startswith("type ") and "password" not in command


def _app_name(text):
    """Remove conversational suffixes before looking up an installed app."""
    return re.sub(r"\s+(app|application|program)$", "", text.strip().casefold())


def _name_matches(wanted, candidate):
    wanted = re.sub(r"[^a-z0-9]", "", _app_name(wanted))
    candidate = re.sub(r"[^a-z0-9]", "", candidate.casefold())
    return wanted == candidate or (len(wanted) >= 4 and wanted in candidate)


def _find_registered_app(name):
    """Look up executables registered by Windows installers (App Paths)."""
    registry_roots = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\App Paths"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths"),
    ]
    matches = []
    for hive, root_path in registry_roots:
        try:
            with winreg.OpenKey(hive, root_path) as root:
                index = 0
                while True:
                    try:
                        key_name = winreg.EnumKey(root, index)
                        index += 1
                    except OSError:
                        break
                    if not _name_matches(name, Path(key_name).stem):
                        continue
                    try:
                        with winreg.OpenKey(root, key_name) as key:
                            value, _ = winreg.QueryValueEx(key, None)
                        executable = re.search(r'"([^"]+\.exe)"|([^\s]+\.exe)', value, re.I)
                        path = executable.group(1) or executable.group(2) if executable else ""
                        if path and Path(path).exists():
                            matches.append(path)
                    except OSError:
                        continue
        except OSError:
            continue
    return min(matches, key=len) if matches else None


def _find_start_app(name):
    """Find Microsoft Store/UWP and Start-menu-only apps via Windows' app catalog."""
    safe_name = name.replace("'", "''")
    script = (
        "$items = Get-StartApps | Where-Object { $_.Name -like '*" + safe_name + "*' }; "
        "$items | ForEach-Object { $_.Name + [char]31 + $_.AppID }"
    )
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", script], capture_output=True,
            text=True, encoding="utf-8", errors="ignore", timeout=8, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    matches = []
    for line in result.stdout.splitlines():
        if "\x1f" not in line:
            continue
        display_name, app_id = line.split("\x1f", 1)
        if _name_matches(name, display_name):
            matches.append((display_name, app_id))
    if not matches:
        return None
    return min(matches, key=lambda item: (item[0].casefold() != _app_name(name), len(item[0])))[1]


def _find_file(name):
    """Locate a user file by file name, including its extension, in common folders."""
    requested = re.sub(r"^(my|the)\s+", "", name.strip().strip('"'))
    direct_path = Path(requested).expanduser()
    if direct_path.is_absolute() and direct_path.is_file():
        return direct_path

    roots = [
        Path.home() / "Desktop", Path.home() / "Downloads", Path.home() / "Documents",
        Path.home() / "Pictures", Path.home() / "Videos", Path.home() / "Music",
    ]
    if os.environ.get("OneDrive"):
        roots.append(Path(os.environ["OneDrive"]))
    wanted = requested.casefold()
    wanted_stem = Path(requested).stem.casefold()
    partial_matches = []
    for root in roots:
        if not root.is_dir():
            continue
        try:
            for folder, _, filenames in os.walk(root):
                for filename in filenames:
                    path = Path(folder) / filename
                    if filename.casefold() == wanted or path.stem.casefold() == wanted_stem:
                        return path
                    if len(wanted_stem) >= 4 and wanted_stem in path.stem.casefold():
                        partial_matches.append(path)
        except OSError:
            continue
    return min(partial_matches, key=lambda item: len(item.name)) if partial_matches else None


def _find_executable(name):
    """Resolve an app only when Windows can verify that it is available."""
    mapped = apps.get(_app_name(name))
    if mapped == "ms-settings:":
        return "uri", mapped
    candidates = [mapped] if mapped else []
    candidates.extend([name, f"{name}.exe"])
    for candidate in candidates:
        if not candidate:
            continue
        found = shutil.which(candidate)
        if found:
            return "executable", found
        if Path(candidate).is_file():
            return "executable", str(Path(candidate))
    shortcut = _find_shortcut(name)
    if shortcut:
        return "shortcut", str(shortcut)
    registered = _find_registered_app(name)
    if registered:
        return "executable", registered
    start_app = _find_start_app(name)
    if start_app:
        return "windows_app", start_app
    return None, None


def _launch(target):
    kind, path = _find_executable(target)
    if not path:
        return False
    if kind in {"uri", "shortcut"}:
        os.startfile(path)
    elif kind == "windows_app":
        subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{path}"], shell=False)
    else:
        subprocess.Popen([path], shell=False)
    return True


def _find_shortcut(name):
    """Find a matching user-visible Start Menu or Desktop shortcut on demand."""
    roots = [
        Path.home() / "Desktop",
        Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
    ]
    wanted = _app_name(name)
    possible = []
    for root in roots:
        if not root.exists():
            continue
        for shortcut in root.rglob("*.lnk"):
            if _name_matches(wanted, shortcut.stem):
                possible.append(shortcut)
    return min(possible, key=lambda item: len(item.stem)) if possible else None


def _close(name):
    executable = apps.get(name, name)
    executable = Path(executable).name
    if not executable.endswith(".exe"):
        executable += ".exe"
    matches = [p for p in psutil.process_iter(["name"]) if (p.info["name"] or "").lower() == executable.lower()]
    if not matches:
        return f"I couldn't find {name} running."
    for process in matches:
        process.terminate()
    return f"Closing {name}."


def _open_folder(name):
    folders = {"downloads": Path.home() / "Downloads", "documents": Path.home() / "Documents",
               "pictures": Path.home() / "Pictures", "desktop": Path.home() / "Desktop", "music": Path.home() / "Music"}
    location = folders.get(name, Path(name).expanduser())
    if location.exists():
        os.startfile(str(location))
        return f"Opening {location.name}."
    return f"I couldn't find the folder {name}."


def _create_folder(command):
    """Create a plainly named folder in a safe personal location."""
    match = re.fullmatch(r"create (?:a )?folder (?:named |called )?(.+?)(?: in (desktop|documents|downloads))?", command)
    if not match:
        return None
    folder_name, location_name = match.groups()
    folder_name = folder_name.strip(" .")
    if not folder_name or any(char in folder_name for char in '<>:"/\\|?*') or ".." in folder_name:
        return "Please use a simple folder name without special path characters."
    roots = {"desktop": Path.home() / "Desktop", "downloads": Path.home() / "Downloads", "documents": Path.home() / "Documents"}
    root = roots.get(location_name or "documents")
    destination = root / folder_name
    if destination.exists():
        return f"The folder {folder_name} already exists in {root.name}."
    try:
        destination.mkdir(parents=True)
        return f"Created folder {folder_name} in {root.name}."
    except OSError:
        return f"I couldn't create the folder {folder_name}."


def handle_command(command):
    """Understand a short command or a conversational request and perform it."""
    global pending_power_action
    command = normalise(command)
    if not command:
        return "I didn't catch that."
    if _should_remember(command):
        memory.add_message("you", command)

    if pending_power_action:
        if command in {"yes", "confirm", "do it", "go ahead"}:
            action, pending_power_action = pending_power_action, None
            return _say(system_control(action))
        if command in {"no", "cancel", "never mind"}:
            pending_power_action = None
            return _say("Cancelled.")
        return "Please say yes to confirm, or no to cancel the power action."

    if command in POWER_ACTIONS:
        pending_power_action = command
        return _say(f"This will {command.replace(' computer', '')} your computer. Say yes to confirm or no to cancel.")

    if command in {"forget our conversations", "clear conversation memory", "forget everything"}:
        memory.clear()
        return _say("I cleared the saved conversation memory.")

    if command in {"recalibrate microphone", "calibrate microphone", "improve microphone"}:
        reset_calibration()
        return _say("I’ll recalibrate the microphone before the next command. Please keep the room quiet for a moment.")

    learned = extract_after(command, ("remember that ", "remember ", "learn that "))
    if learned:
        memory.learn(learned)
        return _say("I will remember that.")

    conversational_reply = conversation.respond(command, memory)
    if conversational_reply:
        return _say(conversational_reply)

    conversation.emotion = "focused"

    result = system_control(command)
    if result:
        return _say(result)

    created = _create_folder(command)
    if created:
        return _say(created)

    if command in {"time", "what time is it", "tell me the time"}:
        return _say(datetime.datetime.now().strftime("It is %I:%M %p"))
    if command in {"date", "what is the date", "todays date", "today date"}:
        return _say(datetime.datetime.now().strftime("Today is %A, %d %B %Y"))

    if _is_question(command):
        remembered = memory.related_fact(command)
        if remembered:
            return _say(f"From what you told me: {remembered}")
        if any(word in command for word in ("previous", "before", "earlier", "remember", "talked")):
            recent = memory.recent_user_messages()
            if recent:
                return _say("Recently, you asked about: " + "; ".join(recent))
        related = memory.related_message(command)
        if related:
            return _say(f"Earlier, you said: {related}")
        answer = web_answer(command)
        if answer:
            return _say(answer)
        ai_reply = chat_reply(command, memory)
        if ai_reply:
            return _say(ai_reply)
        return _say("I’m not certain about that yet, but I’d be happy to help you explore it. You can also say 'search for' followed by the topic for full results.")

    if command.startswith(("search ", "search for ", "look up ", "google ", "find ")):
        terms = search_terms(command)
        if terms:
            webbrowser.open(f"https://www.google.com/search?q={quote_plus(terms)}")
            return _say(f"Searching for {terms}.")

    folder = extract_after(command, ("open my ", "open the "))
    if folder in {"downloads", "documents", "pictures", "desktop", "music"}:
        return _say(_open_folder(folder))

    target = extract_after(command, ("open ", "launch ", "start "))
    if target:
        if target in WEBSITES:
            webbrowser.open(WEBSITES[target])
            return _say(f"Opening {target}.")
        try:
            if _launch(target):
                return _say(f"Opening {target}.")
        except OSError:
            return _say(f"I found {target.title()}, but Windows could not start it.")
        file_path = _find_file(target)
        if file_path:
            try:
                os.startfile(str(file_path))
                return _say(f"Opening {file_path.name}.")
            except OSError:
                return _say(f"I found {file_path.name}, but Windows could not open it.")
        if Path(target).suffix:
            return _say(f"I couldn't find the file {target} in your common folders.")
        return _say(f"{target.title()} is not installed on this PC.")

    target = extract_after(command, ("close ", "quit ", "exit "))
    if target:
        return _say(_close(target))

    ai_reply = chat_reply(command, memory)
    if ai_reply:
        return _say(ai_reply)
    return _say("I’m here with you. I may not know that yet, but you can tell me more, teach me with 'remember that …', or ask me to help with a PC task.")
