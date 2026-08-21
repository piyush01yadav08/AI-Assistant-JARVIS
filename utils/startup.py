"""Windows sign-in startup registration for this local JARVIS installation."""
import os
import sys
from pathlib import Path


def enable_startup():
    """Create a hidden Startup-folder launcher and return a status message."""
    startup_folder = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    if not startup_folder.exists():
        return "Windows Startup folder was not found."

    project_root = Path(__file__).resolve().parents[1]
    main_file = project_root / "main.py"
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    interpreter = pythonw if pythonw.is_file() else Path(sys.executable)
    launcher = startup_folder / "JARVIS AI.vbs"

    # WScript hides the console window while retaining the same Python environment.
    command = f'"{interpreter}" "{main_file}"'
    content = (
        'Set shell = CreateObject("WScript.Shell")\n'
        f'shell.Run "{command.replace("\"", "\"\"")}", 0, False\n'
    )
    try:
        launcher.write_text(content, encoding="utf-8")
        return "JARVIS will start automatically when you sign in to Windows."
    except OSError:
        return "I could not enable Windows startup automatically."
