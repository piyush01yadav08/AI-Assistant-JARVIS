"""Thread-safe Windows text-to-speech for JARVIS."""
from queue import Queue
from threading import Event, Thread

_speech_queue = Queue()
_speaking = Event()
_voice_failed = Event()
last_error = ""


def _speech_worker():
    """Keep native Windows SAPI and all voice calls on one thread."""
    global last_error
    try:
        import pythoncom
        import win32com.client
        pythoncom.CoInitialize()
        voice = win32com.client.Dispatch("SAPI.SpVoice")
        voice.Volume = 100
        voice.Rate = 0
    except Exception as error:
        last_error = f"Speech output is unavailable: {error}"
        _voice_failed.set()
        return

    while True:
        text = _speech_queue.get()
        if text is None:
            return
        try:
            _speaking.set()
            voice.Speak(str(text))
        except Exception as error:
            last_error = f"Speech output failed: {error}"
        finally:
            _speaking.clear()
            _speech_queue.task_done()


Thread(target=_speech_worker, daemon=True, name="JarvisSpeech").start()


def speak(text):
    """Queue a spoken reply without blocking the interface."""
    if text and not _voice_failed.is_set():
        _speech_queue.put(str(text))


def is_speaking():
    return not _voice_failed.is_set() and (_speaking.is_set() or not _speech_queue.empty())
