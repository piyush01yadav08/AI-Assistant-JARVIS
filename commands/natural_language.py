"""Natural-language helpers for the local JARVIS command router.

This module deliberately uses transparent, offline rules instead of sending voice
commands to a cloud service.  It makes common conversational requests map to the
same actions as their short command equivalents.
"""
import re


def normalise(text: str) -> str:
    """Return a compact command phrase while preserving text after 'type'."""
    raw_text = (text or "").strip()
    # Preserve capitalization and punctuation for literal text that JARVIS will type.
    type_match = re.match(r"^\s*(?:(?:hey\s+)?jarvis\s+)?(?:please\s+)?(?:could you\s+)?type\s+(.+)$", raw_text, re.I)
    if type_match:
        return "type " + type_match.group(1).strip()

    text = raw_text.lower()
    # Keep periods so file names such as "report.pdf" and "photo.png" work.
    text = re.sub(r"[?!,]", " ", text)
    text = re.sub(r"\b(jarvis|please|could you|would you|can you|for me)\b", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    replacements = {
        "take a screenshot": "screenshot",
        "take screenshot": "screenshot",
        "capture my screen": "screenshot",
        "turn the volume up": "volume up",
        "turn volume up": "volume up",
        "make it louder": "volume up",
        "turn the volume down": "volume down",
        "turn volume down": "volume down",
        "make it quieter": "volume down",
        "increase the brightness": "brightness up",
        "increase brightness": "brightness up",
        "make the screen brighter": "brightness up",
        "decrease the brightness": "brightness down",
        "decrease brightness": "brightness down",
        "make the screen dimmer": "brightness down",
        "play music": "play pause",
        "pause music": "play pause",
        "play pause": "play pause",
        "next song": "next track",
        "previous song": "previous track",
        "show task view": "task view",
        "snap window left": "snap left",
        "snap window right": "snap right",
        "go to sleep": "sleep computer",
        "lock my computer": "lock computer",
        "lock the computer": "lock computer",
        "show desktop": "show desktop",
        "minimize all windows": "show desktop",
        "switch window": "switch window",
        "next window": "switch window",
        "go back": "browser back",
        "go forward": "browser forward",
        "refresh page": "refresh",
        "select everything": "select all",
        "cut that": "cut",
        "copy that": "copy",
        "paste that": "paste",
        "undo that": "undo",
        "redo that": "redo",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return re.sub(r"\s+", " ", text).strip()


def extract_after(command: str, prefixes: tuple[str, ...]) -> str:
    for prefix in prefixes:
        if command.startswith(prefix):
            return command[len(prefix):].strip(" :")
    return ""


def search_terms(command: str) -> str:
    terms = extract_after(command, ("search for ", "search ", "look up ", "google ", "find "))
    return terms.replace(" on google", "").strip()
