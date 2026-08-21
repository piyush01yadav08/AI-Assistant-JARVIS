import ctypes
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

import pyautogui
import keyboard
from utils.speak import speak

SCREENSHOTS = Path.home() / "Pictures" / "Jarvis Screenshots"


def _hotkey(*keys):
    pyautogui.hotkey(*keys)


def _current_brightness():
    command = "(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness | Select-Object -First 1 -ExpandProperty CurrentBrightness)"
    try:
        result = subprocess.run(["powershell.exe", "-NoProfile", "-Command", command], capture_output=True,
                                text=True, timeout=5, check=False)
        return int(result.stdout.strip())
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None


def _set_brightness(value):
    value = max(0, min(100, value))
    command = (
        "$m=Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods; "
        f"$m | ForEach-Object {{ Invoke-CimMethod -InputObject $_ -MethodName WmiSetBrightness -Arguments @{{Timeout=1;Brightness={value}}} }}"
    )
    try:
        result = subprocess.run(["powershell.exe", "-NoProfile", "-Command", command], capture_output=True,
                                text=True, timeout=5, check=False)
        return result.returncode == 0 and not result.stderr.strip()
    except (OSError, subprocess.TimeoutExpired):
        return False


def system_control(command):

    if command == "shutdown":
        os.system("shutdown /s /t 1")
        return "Shutting down the computer."

    elif command == "restart":
        os.system("shutdown /r /t 1")
        return "Restarting the computer."

    elif command in ("sleep", "sleep computer"):
        ctypes.windll.powrprof.SetSuspendState(False, True, False)
        return "Putting the computer to sleep."

    elif command in ("lock", "lock computer"):
        ctypes.windll.user32.LockWorkStation()
        return "Locking the computer."

    elif "screenshot" in command:
        SCREENSHOTS.mkdir(parents=True, exist_ok=True)
        filename = SCREENSHOTS / f"screenshot-{datetime.now():%Y%m%d-%H%M%S}.png"
        pyautogui.screenshot().save(filename)
        return f"Screenshot saved to {filename}"

    elif command == "volume up":
        pyautogui.press("volumeup")

    elif command == "volume down":
        pyautogui.press("volumedown")

    elif command in {"mute", "mute volume", "unmute", "unmute volume"}:
        pyautogui.press("volumemute")
        return "Toggled mute."

    elif command == "play pause":
        pyautogui.press("playpause")

    elif command == "next track":
        pyautogui.press("nexttrack")

    elif command == "previous track":
        pyautogui.press("prevtrack")

    elif command in {"brightness up", "brightness down"}:
        current = _current_brightness()
        if current is None:
            return "Brightness control is not available for this display."
        target = current + (10 if command == "brightness up" else -10)
        if _set_brightness(target):
            return f"Brightness set to {max(0, min(100, target))} percent."
        return "Brightness control is not available for this display."

    elif match := re.fullmatch(r"(?:set )?brightness(?: to)? (\d{1,3})(?: percent)?", command):
        target = int(match.group(1))
        if target > 100:
            return "Brightness must be between 0 and 100 percent."
        if _set_brightness(target):
            return f"Brightness set to {target} percent."
        return "Brightness control is not available for this display."

    elif command == "copy":
        keyboard.press_and_release("ctrl+c")

    elif command == "paste":
        keyboard.press_and_release("ctrl+v")

    elif command == "right click":
        pyautogui.rightClick()

    elif command == "double click":
        pyautogui.doubleClick()

    elif command == "click":
        pyautogui.click()

    elif command == "scroll up":
        pyautogui.scroll(10)

    elif command == "scroll down":
        pyautogui.scroll(-10)

    elif command.startswith("type "):
        text = command[5:]
        pyautogui.typewrite(text)

    elif command == "enter":
        pyautogui.press("enter")

    elif command == "space":
        pyautogui.press("space")

    elif command == "backspace":
        pyautogui.press("backspace")

    elif command == "tab":
        pyautogui.press("tab")
    elif command in ("switch window", "switch application"):
        _hotkey("alt", "tab")
    elif command == "show desktop":
        _hotkey("win", "d")
    elif command == "task view":
        _hotkey("win", "tab")
    elif command == "minimize window":
        _hotkey("win", "down")
    elif command == "maximize window":
        _hotkey("win", "up")
    elif command == "close window":
        _hotkey("alt", "f4")
    elif command == "snap left":
        _hotkey("win", "left")
    elif command == "snap right":
        _hotkey("win", "right")
    elif command == "new desktop":
        _hotkey("win", "ctrl", "d")
    elif command == "close desktop":
        _hotkey("win", "ctrl", "f4")
    elif command == "select all":
        _hotkey("ctrl", "a")
    elif command == "cut":
        _hotkey("ctrl", "x")
    elif command == "undo":
        _hotkey("ctrl", "z")
    elif command == "redo":
        _hotkey("ctrl", "y")
    elif command == "save":
        _hotkey("ctrl", "s")
    elif command == "browser back":
        _hotkey("alt", "left")
    elif command == "browser forward":
        _hotkey("alt", "right")
    elif command == "refresh":
        pyautogui.press("f5")
    elif command == "new tab":
        _hotkey("ctrl", "t")
    elif command == "close tab":
        _hotkey("ctrl", "w")

    else:
        return False

    return "Action completed."
