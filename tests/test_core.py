import os
import tempfile
import unittest
from unittest.mock import Mock, patch


# Keep test credentials and conversation history out of the user's AppData.
TEST_APPDATA = tempfile.TemporaryDirectory()
os.environ["APPDATA"] = TEST_APPDATA.name

from commands import basic_commands as basic
from commands import system_automation as automation
from commands.natural_language import normalise
from gui import JarvisGUI
from utils.security import CredentialStore


class JarvisCoreTests(unittest.TestCase):
    def setUp(self):
        basic.speak = Mock()
        basic.memory.clear()

    def test_type_command_preserves_case(self):
        self.assertEqual(normalise("Type Hello, JARVIS!"), "type Hello, JARVIS!")

    def test_plain_words_do_not_trigger_keyboard_actions(self):
        with patch.object(automation.pyautogui, "press") as press:
            self.assertFalse(automation.system_control("open internet explorer"))
            press.assert_not_called()

    def test_exact_keyboard_action_runs(self):
        with patch.object(automation.pyautogui, "press") as press:
            self.assertEqual(automation.system_control("enter"), "Action completed.")
            press.assert_called_once_with("enter")

    def test_type_action_keeps_capital_letters(self):
        with patch.object(automation.pyautogui, "typewrite") as typewrite:
            self.assertEqual(automation.system_control(normalise("type Hello World")), "Action completed.")
            typewrite.assert_called_once_with("Hello World")

    def test_common_desktop_actions_route_without_errors(self):
        commands = [
            "volume up", "volume down", "mute", "play pause", "next track", "previous track",
            "copy", "paste", "right click", "double click", "click", "scroll up", "scroll down",
            "enter", "space", "backspace", "tab", "switch window", "show desktop", "task view",
            "minimize window", "maximize window", "close window", "snap left", "snap right",
            "new desktop", "close desktop", "select all", "cut", "undo", "redo", "save",
            "browser back", "browser forward", "refresh", "new tab", "close tab",
        ]
        with patch.object(automation.pyautogui, "press"), \
             patch.object(automation.pyautogui, "click"), \
             patch.object(automation.pyautogui, "rightClick"), \
             patch.object(automation.pyautogui, "doubleClick"), \
             patch.object(automation.pyautogui, "scroll"), \
             patch.object(automation.pyautogui, "hotkey"), \
             patch.object(automation.keyboard, "press_and_release"):
            for command in commands:
                self.assertTrue(automation.system_control(command), command)

    def test_brightness_routes_and_clamps(self):
        with patch.object(automation, "_current_brightness", return_value=95), \
             patch.object(automation, "_set_brightness", return_value=True) as set_brightness:
            self.assertIn("100 percent", automation.system_control("brightness up"))
            set_brightness.assert_called_once_with(105)
        with patch.object(automation, "_set_brightness", return_value=True) as set_brightness:
            self.assertIn("60 percent", automation.system_control("set brightness to 60"))
            set_brightness.assert_called_once_with(60)

    def test_memory_learn_and_recall(self):
        self.assertIn("remember", basic.handle_command("remember that my favorite color is blue").lower())
        self.assertIn("blue", basic.handle_command("what is my favorite color").lower())

    def test_web_answer_and_conversation_fallbacks(self):
        with patch.object(basic, "web_answer", return_value="Photosynthesis converts light into chemical energy."):
            self.assertIn("photosynthesis", basic.handle_command("what is photosynthesis").lower())
        self.assertIn("good to hear", basic.handle_command("hello").lower())

    def test_power_action_requires_confirmation(self):
        self.assertIn("say yes", basic.handle_command("shutdown").lower())
        basic.pending_power_action = None

    def test_wake_word_variants(self):
        self.assertEqual(JarvisGUI.wake_remainder("Hey, Jarvis open notepad"), "open notepad")
        self.assertEqual(JarvisGUI.wake_remainder("okay jarvis"), "")
        self.assertIsNone(JarvisGUI.wake_remainder("hello there"))

    def test_credentials_are_hashed_and_changeable(self):
        credentials = CredentialStore()
        credentials.configure("Lenovo", "old-password")
        raw = credentials.config_file.read_text(encoding="utf-8")
        self.assertNotIn("old-password", raw)
        self.assertTrue(credentials.verify("lenovo", "old-password"))
        self.assertTrue(credentials.change_password("Lenovo", "old-password", "new-password"))
        self.assertFalse(credentials.verify("Lenovo", "old-password"))
        self.assertTrue(credentials.verify("Lenovo", "new-password"))

    def test_installed_app_resolver_finds_core_apps(self):
        kind, path = basic._find_executable("notepad")
        self.assertEqual(kind, "executable")
        self.assertTrue(path.lower().endswith("notepad.exe"))


if __name__ == "__main__":
    unittest.main()
