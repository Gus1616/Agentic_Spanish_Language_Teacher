from openai import OpenAI
import json

client = OpenAI()
MODEL = "gpt-4o"

def decide(state: dict, user_message: str) -> dict:
    """
    Returns a routing decision, e.g.:
      {"agent": "lesson", "topic": "present tense verbs"}
      {"agent": "practice", "topic": "greetings"}
      {"agent": "feedback", "topic": ""}
      {"agent": "assessment", "topic": ""}
    """
    system = """You are the orchestrator for a Spanish learning app.
You decide which specialist agent to call next based on the learner's state and message.

The agents available are:
  - assessment  → use when the learner is new OR asks to be tested on their level
  - lesson      → use when the learner wants to learn something new
  - practice    → use when the learner wants exercises or drills
  - feedback    → use when the learner has just answered an exercise

Respond ONLY with valid JSON in this exact format (no explanation, no markdown):
{"agent": "<assessment|lesson|practice|feedback>", "topic": "<short topic string or empty>"}"""

    user_prompt = f"""Learner state:
- Level: {state['level']}
- Topics covered: {state['topics_covered']}
- Recent mistakes: {state['recent_mistakes'][-3:]}
- Last message: "{user_message}"

What should happen next?"""

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=128,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user_prompt},
        ],
    )

    raw = response.choices[0].message.content.strip()

    try:
        decision = json.loads(raw)
    except json.JSONDecodeError:
        # Graceful fallback if the model didn't return clean JSON
        decision = {"agent": "lesson", "topic": ""}

    return decision