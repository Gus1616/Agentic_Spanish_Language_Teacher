import json
import os

STATE_FILE = "state.json"

DEFAULT_STATE = {
    "level": "beginner",          # beginner | intermediate | advanced
    "vocabulary_seen": [],        # list of Spanish words encountered
    "recent_mistakes": [],        # last few errors the user made
    "topics_covered": [],         # e.g. ["greetings", "present tense"]
    "session_history": [],        # last N user/assistant exchanges
}

def load() -> dict:
    if not os.path.exists(STATE_FILE):
        save(DEFAULT_STATE)
        return DEFAULT_STATE.copy()
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def add_to_history(state: dict, role: str, content: str, max_history: int = 10):
    """Append a message and trim to max_history pairs."""
    state["session_history"].append({"role": role, "content": content})
    if len(state["session_history"]) > max_history * 2:
        state["session_history"] = state["session_history"][-max_history * 2:]