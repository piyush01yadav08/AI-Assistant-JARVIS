"""Local authentication for JARVIS.

Only a salted password hash is stored; the password itself is never written to
disk.  This is an application lock, not a replacement for a Windows account
password or full-disk encryption.
"""
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path


class CredentialStore:
    ITERATIONS = 310_000
    def __init__(self):
        app_data = Path(os.environ.get("APPDATA", Path.home())) / "JARVIS"
        self.config_file = app_data / "security.json"
        self._unlocked = False

    @property
    def configured(self):
        return self.config_file.is_file()

    def configure(self, identity, password):
        salt = os.urandom(16)
        password_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, self.ITERATIONS)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.config_file.write_text(json.dumps({
            "identity": identity.strip(),
            "salt": base64.b64encode(salt).decode("ascii"),
            "password_hash": base64.b64encode(password_hash).decode("ascii"),
        }), encoding="utf-8")

    def change_password(self, identity, current_password, new_password):
        """Replace credentials only after validating the existing password."""
        if not self.verify(identity, current_password):
            return False
        self.configure(identity, new_password)
        self.touch()
        return True

    def verify(self, identity, password):
        try:
            data = json.loads(self.config_file.read_text(encoding="utf-8"))
            salt = base64.b64decode(data["salt"])
            expected = base64.b64decode(data["password_hash"])
        except (OSError, KeyError, ValueError, json.JSONDecodeError):
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, self.ITERATIONS)
        valid_identity = hmac.compare_digest(data["identity"].casefold(), identity.strip().casefold())
        valid_password = hmac.compare_digest(actual, expected)
        if valid_identity and valid_password:
            self.touch()
            return True
        return False

    def touch(self):
        self._unlocked = True

    def is_unlocked(self):
        return self._unlocked

    def lock(self):
        self._unlocked = False
