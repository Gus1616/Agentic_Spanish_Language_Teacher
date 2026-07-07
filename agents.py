from openai import OpenAI

client = OpenAI()
MODEL = "gpt-4o"

def _call_claude(system: str, user: str) -> str:
    """Thin wrapper around the OpenAI API."""
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
    )
    return response.choices[0].message.content


def assessment_agent(state: dict, user_message: str) -> str:
    system = f"""You are a Spanish language assessor.
The learner's current recorded level is: {state['level']}.
Topics they have covered so far: {state['topics_covered']}.

Ask 2-3 short diagnostic questions to check their real level.
After they answer, end your reply with one line in this exact format:
LEVEL: beginner | intermediate | advanced

Keep it encouraging and conversational."""

    return _call_claude(system, user_message)


def lesson_agent(state: dict, user_message: str, topic: str = "") -> str:
    vocab_seen = ", ".join(state["vocabulary_seen"][-20:]) or "none yet"
    system = f"""You are a friendly Spanish tutor.
The learner is at {state['level']} level.
Vocabulary they already know: {vocab_seen}.
Topic to teach today: {topic or 'choose something appropriate for their level'}.

Teach a short, clear lesson (5-8 sentences max).
Introduce 3-5 new Spanish words or phrases.
End with: VOCAB: word1, word2, word3 (comma-separated list of new words introduced)"""

    return _call_claude(system, user_message)


def practice_agent(state: dict, user_message: str, topic: str = "") -> str:
    mistakes = ", ".join(state["recent_mistakes"][-5:]) or "none recorded"
    system = f"""You are a Spanish practice coach.
The learner is at {state['level']} level.
Topic to practise: {topic or 'mix of recent topics'}.
Their recent mistakes: {mistakes}.

Give them 2-3 exercises. Choose from:
  - Fill in the blank
  - Translate this sentence
  - Pick the correct word

Present the exercises clearly and wait for their answers.
Do NOT give the answers yet."""

    return _call_claude(system, user_message)


def feedback_agent(state: dict, user_message: str) -> str:
    history_text = "\n".join(
        f"{m['role'].capitalize()}: {m['content']}"
        for m in state["session_history"][-6:]
    )
    system = f"""You are a Spanish language feedback coach.
The learner is at {state['level']} level.

Recent conversation:
{history_text}

The learner just submitted an answer. Grade it and:
1. Say clearly whether it was correct or incorrect.
2. If wrong, explain the rule simply.
3. Give the correct answer.
4. Be encouraging.

End your reply with:
MISTAKES: <brief description of any error, or 'none'>"""

    return _call_claude(system, user_message)