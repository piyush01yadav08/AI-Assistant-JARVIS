import tkinter as tk
from tkinter import messagebox, simpledialog
from threading import Thread
from datetime import datetime
import keyboard
import math
import time
import re
from utils.speak import is_speaking, speak
from utils.listen import get_listen_status, listen
from commands.basic_commands import handle_command
from utils.security import CredentialStore
from utils.startup import enable_startup
from utils.conversation import conversation

class JarvisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("JARVIS AI")
        self.root.geometry("700x700")
        self.root.configure(bg="#020617")

        self.is_running = True
        self.is_awake = False
        self.is_background = False
        self.security = CredentialStore()
        self.listener_started = False

        title = tk.Label(root, text="JARVIS", font=("Arial", 28, "bold"),
                         fg="#22d3ee", bg="#020617")
        title.pack(pady=10)

        self.orb = tk.Canvas(root, width=220, height=180, bg="#020617", highlightthickness=0)
        self.orb.pack(pady=(0, 2))
        self.animation_phase = 0
        self.draw_orb()

        self.clock = tk.Label(root, font=("Arial", 12), fg="white", bg="#020617")
        self.clock.pack()
        self.update_clock()

        self.chat_box = tk.Text(root, bg="#020617", fg="#e2e8f0",
                                font=("Consolas", 12), wrap=tk.WORD, bd=0)
        self.chat_box.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.chat_box.config(state=tk.DISABLED)

        self.command_entry = tk.Entry(root, font=("Arial", 12), bg="#0f172a", fg="white",
                                      insertbackground="white", relief=tk.FLAT)
        self.command_entry.pack(padx=12, pady=(0, 8), fill=tk.X)
        self.command_entry.bind("<Return>", self.submit_text)

        self.status = tk.Label(root, text="Locked", fg="#94a3b8", bg="#020617")
        self.status.pack(pady=5)

        btn_frame = tk.Frame(root, bg="#020617")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Send", command=self.submit_text, bg="#38bdf8", width=12).grid(row=0, column=0, padx=10)
        tk.Button(btn_frame, text="Test voice", command=lambda: speak("JARVIS voice is working."), bg="#a855f7", width=12).grid(row=0, column=1, padx=10)
        tk.Label(btn_frame, text="Say “Hey Jarvis” to activate • Ctrl+Alt+J shows this window", fg="#94a3b8", bg="#020617").grid(row=0, column=2, padx=10)

        self.root.protocol("WM_DELETE_WINDOW", self.close_app)
        keyboard.add_hotkey("ctrl+alt+j", lambda: self.root.after(0, self.show_window))
        self.root.after(100, self.initialize_security)
        self.root.after(150, lambda: self.log("Jarvis: " + enable_startup()))

    def update_clock(self):
        self.clock.config(text=datetime.now().strftime("%H:%M:%S"))
        self.root.after(1000, self.update_clock)

    def draw_orb(self):
        """Render the animated JARVIS core using only Tkinter canvas shapes."""
        self.orb.delete("all")
        self.animation_phase = (self.animation_phase + 4) % 360
        center_x, center_y = 110, 90
        awake = self.is_awake and self.security.is_unlocked()
        palette = {
            "calm": ("#22d3ee", "#164e63"), "focused": ("#22d3ee", "#164e63"),
            "happy": ("#facc15", "#713f12"), "warm": ("#fb7185", "#881337"),
            "supportive": ("#c084fc", "#581c87"), "curious": ("#34d399", "#065f46"),
            "playful": ("#fb923c", "#7c2d12"),
        }
        core_color, glow_color = palette.get(conversation.emotion, palette["calm"])
        if not awake:
            core_color, glow_color = "#0e7490", "#083344"
        pulse = 4 * math.sin(math.radians(self.animation_phase * 2))

        for radius, width in ((64 + pulse, 2), (51 - pulse / 2, 1)):
            self.orb.create_oval(center_x - radius, center_y - radius, center_x + radius, center_y + radius,
                                 outline=glow_color, width=width)

        # Two counter-rotating segmented rings give the orb a live HUD effect.
        for start, extent, radius in ((self.animation_phase, 110, 61),
                                      (180 - self.animation_phase, 82, 55),
                                      (self.animation_phase + 210, 48, 61)):
            self.orb.create_arc(center_x - radius, center_y - radius, center_x + radius, center_y + radius,
                                start=start, extent=extent, style=tk.ARC, outline=core_color, width=3)

        for angle in range(0, 360, 45):
            moving_angle = math.radians(angle + self.animation_phase)
            radius = 42 + 3 * math.sin(math.radians(self.animation_phase + angle * 2))
            x = center_x + radius * math.cos(moving_angle)
            y = center_y + radius * math.sin(moving_angle)
            self.orb.create_oval(x - 2, y - 2, x + 2, y + 2, fill=core_color, outline="")

        core_radius = 23 + pulse / 2
        self.orb.create_oval(center_x - core_radius, center_y - core_radius,
                             center_x + core_radius, center_y + core_radius,
                             fill=glow_color, outline=core_color, width=2)
        self.orb.create_text(center_x, center_y, text="J", font=("Arial", 20, "bold"), fill="#e0f2fe")
        state = conversation.emotion.upper() if awake else "STANDBY"
        self.orb.create_text(center_x, 164, text=state,
                             font=("Arial", 9, "bold"), fill=core_color)
        self.root.after(40, self.draw_orb)

    def log(self, msg):
        self.chat_box.config(state=tk.NORMAL)
        self.chat_box.insert(tk.END, msg + "\n")
        self.chat_box.see(tk.END)
        self.chat_box.config(state=tk.DISABLED)

    def submit_text(self, event=None):
        command = self.command_entry.get().strip()
        if not command:
            return
        self.command_entry.delete(0, tk.END)
        self.log("You: " + command)
        self.dispatch(command)

    def initialize_security(self):
        """Create credentials on first run, then begin the voice listener."""
        if not self.security.configured:
            messagebox.showinfo("Set up JARVIS security", "Create your identity and password. JARVIS will require them before it performs actions.")
            identity = simpledialog.askstring("JARVIS identity", "Your identity / name:", parent=self.root)
            password = simpledialog.askstring("JARVIS password", "Create a password:", parent=self.root, show="*")
            confirmation = simpledialog.askstring("Confirm password", "Enter the password again:", parent=self.root, show="*")
            if not identity or not password or password != confirmation:
                messagebox.showerror("Setup required", "JARVIS needs an identity and password before it can run.")
                self.close_app()
                return
            self.security.configure(identity, password)
            self.log("Jarvis: Security is configured. Say “Hey Jarvis”, then unlock me to continue.")
        self.start_listener()

    def start_listener(self):
        if not self.listener_started:
            self.listener_started = True
            Thread(target=self.run, daemon=True).start()

    def close_app(self):
        self.is_running = False
        keyboard.remove_hotkey("ctrl+alt+j")
        self.root.destroy()

    def run_in_background(self):
        """Hide the window without stopping the wake-word listener."""
        if not self.is_background:
            self.is_background = True
            self.root.withdraw()

    def show_window(self):
        self.is_background = False
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def unlock(self, pending_command=None):
        """Request typed credentials; never accept passwords through speech."""
        self.show_window()
        identity = simpledialog.askstring("JARVIS locked", "Identity:", parent=self.root)
        password = simpledialog.askstring("JARVIS locked", "Password:", parent=self.root, show="*")
        if not identity or password is None:
            self.log("Jarvis: Access remains locked.")
            speak("Access remains locked.")
            return
        if not self.security.verify(identity, password):
            messagebox.showerror("Access denied", "Identity or password is incorrect.")
            self.log("Jarvis: Access denied.")
            speak("Access denied.")
            return
        self.log("Jarvis: Access granted.")
        speak("Access granted.")
        if pending_command:
            self.dispatch(pending_command)

    def change_password(self):
        self.show_window()
        identity = simpledialog.askstring("Change JARVIS password", "Identity:", parent=self.root)
        current = simpledialog.askstring("Change JARVIS password", "Current password:", parent=self.root, show="*")
        new_password = simpledialog.askstring("Change JARVIS password", "New password:", parent=self.root, show="*")
        confirmation = simpledialog.askstring("Confirm new password", "Enter the new password again:", parent=self.root, show="*")
        if not identity or not current or not new_password or new_password != confirmation:
            messagebox.showerror("Password unchanged", "The identity, current password, and matching new password are required.")
            return
        if self.security.change_password(identity, current, new_password):
            self.log("Jarvis: Your password has been updated.")
        else:
            messagebox.showerror("Password unchanged", "Your identity or current password is incorrect.")
            self.log("Jarvis: Password update denied.")

    def dispatch(self, command):
        clean_command = command.strip().lower()
        if clean_command in {"lock jarvis", "lock yourself"}:
            self.security.lock()
            self.log("Jarvis: Locked.")
            return
        if clean_command in {"change jarvis password", "change password", "update jarvis password"}:
            if self.security.is_unlocked():
                self.change_password()
            else:
                self.unlock(command)
            return
        if self.security.is_unlocked():
            self.process_command(command)
        else:
            self.unlock(command)

    def process_command(self, command):
        if command.strip().lower() in {"bye jarvis", "goodbye jarvis", "close jarvis", "quit jarvis"}:
            speak("Goodbye")
            self.log("Jarvis: Goodbye")
            self.root.after(350, self.close_app)
            return
        try:
            response = handle_command(command)
            self.log("Jarvis: " + response)
            self.status.config(text="Command completed")
        except Exception as error:
            message = f"Command failed: {type(error).__name__}: {error}"
            self.log("Jarvis: " + message)
            self.status.config(text=message)
            speak("I could not complete that command. Please check the message on screen.")

    @staticmethod
    def wake_remainder(transcript):
        """Accept common wake-word variants produced by speech recognition."""
        cleaned = re.sub(r"[^a-z0-9\s]", " ", transcript.casefold())
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        for phrase in ("hey jarvis", "hi jarvis", "okay jarvis", "ok jarvis", "jarvis"):
            if cleaned.startswith(phrase):
                return cleaned[len(phrase):].strip()
        return None

    def run(self):
        self.root.after(0, lambda: self.log("Jarvis: Say “Hey Jarvis” when you need me."))

        while self.is_running:
            if is_speaking():
                self.root.after(0, lambda: self.status.config(text="Speaking..."))
                time.sleep(0.1)
                continue
            status = "Listening for a command..." if self.is_awake else "Waiting for “Hey Jarvis”"
            self.root.after(0, lambda value=status: self.status.config(text=value))
            cmd = listen()

            if cmd:
                self.root.after(0, lambda value=cmd: self.log("You: " + value))
                lowered = cmd.strip().lower()
                if lowered in {"bye jarvis", "goodbye jarvis", "close jarvis", "quit jarvis"}:
                    speak("Goodbye")
                    self.root.after(0, lambda: self.log("Jarvis: Goodbye"))
                    self.root.after(350, self.close_app)
                    break

                if not self.is_awake:
                    remainder = self.wake_remainder(lowered)
                    if remainder is not None:
                        self.is_awake = True
                        if self.security.is_unlocked():
                            greeting = "Hello again. Welcome back. What would you like to do?"
                        else:
                            greeting = "Hello. Welcome back. Please enter your identity and password."
                        speak(greeting)
                        self.root.after(0, lambda value=greeting: self.log("Jarvis: " + value))
                        if self.security.is_unlocked():
                            self.root.after(0, self.run_in_background)
                            if remainder:
                                self.root.after(0, lambda value=remainder: self.dispatch(value))
                        else:
                            self.root.after(0, lambda value=remainder or None: self.unlock(value))
                    continue

                self.root.after(0, lambda value=cmd: self.dispatch(value))
            else:
                error, _ = get_listen_status()
                if error:
                    self.root.after(0, lambda value=error: self.status.config(text=value))

def start_app():
    root = tk.Tk()
    app = JarvisGUI(root)
    root.mainloop()
