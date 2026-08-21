"""Warm, local small-talk responses for JARVIS (without pretending to be human)."""
import random
import re


class ConversationEngine:
    def __init__(self):
        self.emotion = "calm"

    def _set(self, emotion, responses):
        self.emotion = emotion
        return random.choice(responses)

    def respond(self, text, memory):
        text = text.strip().casefold()
        name_match = re.fullmatch(r"(?:my name is|i am|i'm) ([a-z][a-z -]{1,40})", text)
        if name_match:
            name = name_match.group(1).strip().title()
            memory.learn(f"Your name is {name}")
            return self._set("happy", [f"Nice to meet you, {name}. I’ll remember that."])

        if text in {"hi", "hello", "hey", "good morning", "good afternoon", "good evening"}:
            return self._set("happy", ["Hello! It’s good to hear from you. How can I help today?", "Hi! I’m here and ready whenever you need me."])
        if text in {"how are you", "how are you doing", "how do you feel"}:
            return self._set("warm", ["I don’t have feelings like a person, but I’m working well and I’m glad to help you."])
        if any(phrase in text for phrase in ("thank you", "thanks", "thankyou")):
            return self._set("happy", ["You’re welcome!", "Anytime — I’m glad I could help."])
        if text in {"bye", "goodbye", "see you later"}:
            return self._set("warm", ["See you later. I’ll be here when you need me."])
        if any(phrase in text for phrase in ("i am sad", "i'm sad", "feeling sad", "feel sad", "upset", "stressed", "anxious")):
            return self._set("supportive", ["I’m sorry you’re feeling that way. Taking a short break, a drink of water, or talking with someone you trust may help. I’m here to listen too."])
        if any(phrase in text for phrase in ("i am happy", "i'm happy", "feeling great", "feel great", "excited")):
            return self._set("happy", ["That’s wonderful to hear! What’s making your day better?"])
        if any(phrase in text for phrase in ("i am bored", "i'm bored", "feeling bored")):
            return self._set("curious", ["Let’s fix that. We could play some music, search for a topic you like, or organize a small task. What sounds good?"])
        if text in {"tell me a joke", "say a joke"}:
            return self._set("playful", ["Why do programmers prefer dark mode? Because light attracts bugs."])
        if text in {"what can you do", "help", "what do you do"}:
            return self._set("focused", ["I can chat, remember things you explicitly teach me, answer basic questions from the web, and control many common PC tasks. Ask me naturally."])
        return None


conversation = ConversationEngine()
