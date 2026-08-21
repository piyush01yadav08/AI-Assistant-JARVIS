"""Reliable speech recognition for JARVIS."""
import os

import speech_recognition as sr


recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = True
recognizer.energy_threshold = 300
recognizer.pause_threshold = 0.8
recognizer.non_speaking_duration = 0.5
_calibrated = False
last_error = ""
last_device_name = ""


def _microphone_index():
    """Use Windows' chosen default unless the user explicitly selects an input."""
    forced_index = os.environ.get("JARVIS_MICROPHONE_INDEX")
    if forced_index and forced_index.isdigit():
        return int(forced_index)
    # None tells PyAudio to use the microphone selected in Windows Settings.
    return None


def get_listen_status():
    return last_error, last_device_name


def reset_calibration():
    """Recalibrate before the next spoken command after the room noise changes."""
    global _calibrated
    _calibrated = True


def listen(timeout=None, phrase_time_limit=12):
    """Wait for speech and return a complete, naturally paced command."""
    global _calibrated, last_error, last_device_name
    try:
        index = _microphone_index()
        names = sr.Microphone.list_microphone_names()
        last_device_name = names[index] if index is not None and index < len(names) else "Windows default microphone"
        with sr.Microphone(device_index=index) as source:
            if _calibrated:
                # Calibration is intentionally manual: automatic calibration can set the
                # threshold too high and miss quieter voices.
                recognizer.adjust_for_ambient_noise(source, duration=0.7)
                _calibrated = False
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        language = os.environ.get("JARVIS_LANGUAGE", "en-IN")
        heard = recognizer.recognize_google(audio, language=language).lower().strip()
        last_error = ""
        return heard
    except sr.UnknownValueError:
        last_error = "I couldn't understand that. Please speak a little closer to the microphone."
        return ""
    except sr.RequestError:
        last_error = "Speech recognition needs an internet connection."
        return ""
    except (sr.WaitTimeoutError, OSError, ValueError):
        last_error = "I couldn't access the selected microphone."
        return ""
