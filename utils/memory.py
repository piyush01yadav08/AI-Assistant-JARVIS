"""Private, local conversation memory and lightweight web answers for JARVIS."""
import json
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path


STOP_WORDS = {"the", "and", "for", "with", "that", "this", "what", "when", "where", "who", "why", "how", "are", "is", "was", "were", "you", "your", "jarvis", "about"}


class ConversationMemory:
    def __init__(self):
        self.path = Path(os.environ.get("APPDATA", Path.home())) / "JARVIS" / "memory.json"
        self.data = self._load()

    def _load(self):
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return {"history": data.get("history", []), "facts": data.get("facts", [])}
        except (OSError, ValueError, json.JSONDecodeError):
            return {"history": [], "facts": []}

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_message(self, role, text):
        self.data["history"].append({"role": role, "text": text, "time": int(time.time())})
        self.data["history"] = self.data["history"][-300:]
        self._save()

    def learn(self, fact):
        fact = fact.strip()
        if fact and fact.casefold() not in {item.casefold() for item in self.data["facts"]}:
            self.data["facts"].append(fact)
            self.data["facts"] = self.data["facts"][-100:]
            self._save()

    def related_fact(self, question):
        query_words = self._words(question)
        if not query_words:
            return None
        best, best_score = None, 0.0
        for fact in self.data["facts"]:
            fact_words = self._words(fact)
            overlap = len(query_words & fact_words)
            score = overlap / max(1, len(query_words))
            if score > best_score:
                best, best_score = fact, score
        return best if best_score >= 0.5 else None

    def related_message(self, question):
        """Retrieve a previous user message related to the current question."""
        query_words = self._words(question)
        best, best_score = None, 0.0
        # The final entry is the current question, so deliberately exclude it.
        for entry in self.data["history"][:-1]:
            if entry.get("role") != "you":
                continue
            words = self._words(entry.get("text", ""))
            score = len(query_words & words) / max(1, len(query_words))
            if score > best_score:
                best, best_score = entry.get("text"), score
        return best if best_score >= 0.5 else None

    def recent_user_messages(self):
        messages = [entry["text"] for entry in self.data["history"][:-1] if entry.get("role") == "you"]
        return messages[-3:]

    @staticmethod
    def _words(text):
        return {word for word in re.findall(r"[a-z0-9]+", text.casefold()) if len(word) > 2 and word not in STOP_WORDS}

    def clear(self):
        self.data = {"history": [], "facts": []}
        self._save()


def web_answer(question):
    """Return a short factual answer from DuckDuckGo's public instant-answer API."""
    url = "https://api.duckduckgo.com/?" + urllib.parse.urlencode({
        "q": question, "format": "json", "no_html": "1", "skip_disambig": "1",
    })
    request = urllib.request.Request(url, headers={"User-Agent": "JARVIS-Personal-Assistant/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=7) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    answer = data.get("Answer") or data.get("AbstractText")
    if not answer:
        topics = data.get("RelatedTopics", [])
        for topic in topics:
            if isinstance(topic, dict) and topic.get("Text"):
                answer = topic["Text"]
                break
    if not answer:
        return None
    answer = re.sub(r"\s+", " ", answer).strip()
    return answer[:500] + ("…" if len(answer) > 500 else "")
