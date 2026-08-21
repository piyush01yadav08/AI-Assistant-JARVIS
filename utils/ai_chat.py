"""Optional private conversational-model backend using a local Ollama server."""
import json
import os
import urllib.error
import urllib.request


def chat_reply(message, memory):
    """Ask a locally running model for a short, conversational response.

    Ollama keeps prompts and responses on the PC.  If it is not installed or a
    model is unavailable, this returns None so JARVIS can use its local fallback.
    """
    model = os.environ.get("JARVIS_OLLAMA_MODEL", "llama3.2:3b")
    context = memory.data.get("history", [])[-12:]
    messages = [{
        "role": "system",
        "content": (
            "You are JARVIS, a warm, concise personal desktop assistant. "
            "Talk naturally, be helpful, and do not claim to have human feelings. "
            "Do not ask for or repeat passwords. Keep answers under 120 words."
        ),
    }]
    for entry in context:
        role = "assistant" if entry.get("role") == "jarvis" else "user"
        messages.append({"role": role, "content": entry.get("text", "")})
    # The current message may already be in the history; append only if needed.
    if not context or context[-1].get("text") != message:
        messages.append({"role": "user", "content": message})

    payload = json.dumps({"model": model, "messages": messages, "stream": False}).encode("utf-8")
    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/chat", data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
        reply = data.get("message", {}).get("content", "").strip()
        return reply[:900] if reply else None
    except (urllib.error.URLError, OSError, ValueError, json.JSONDecodeError):
        return None
