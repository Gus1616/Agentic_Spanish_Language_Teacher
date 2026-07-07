import re
import sys
import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv(override=True)


sys.path.insert(0, os.path.dirname(__file__))
import state as learning_state
import orchestrator
import agents


def update_state_from_response(state: dict, agent_name: str, response: str):
    if agent_name == "assessment":
        match = re.search(r"LEVEL:\s*(beginner|intermediate|advanced)", response, re.IGNORECASE)
        if match:
            state["level"] = match.group(1).lower()

    if agent_name == "lesson":
        match = re.search(r"VOCAB:\s*(.+)", response)
        if match:
            new_words = [w.strip() for w in match.group(1).split(",")]
            state["vocabulary_seen"].extend(new_words)
            state["vocabulary_seen"] = list(dict.fromkeys(state["vocabulary_seen"]))[-100:]

    if agent_name == "feedback":
        match = re.search(r"MISTAKES:\s*(.+)", response)
        if match and match.group(1).strip().lower() != "none":
            state["recent_mistakes"].append(match.group(1).strip())
            state["recent_mistakes"] = state["recent_mistakes"][-10:]


def clean_response(response: str) -> str:
    """Strip internal metadata tags from agent replies before display."""
    response = re.sub(r"\nLEVEL:\s*(beginner|intermediate|advanced)\s*$", "", response, flags=re.IGNORECASE | re.MULTILINE)
    response = re.sub(r"\nVOCAB:\s*.+$", "", response, flags=re.MULTILINE)
    response = re.sub(r"\nMISTAKES:\s*.+$", "", response, flags=re.MULTILINE)
    return response.strip()


# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Spanish Tutor",
    page_icon="🇪🇸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state init ─────────────────────────────────────────────────────────
if "learning_state" not in st.session_state:
    st.session_state.learning_state = learning_state.load()

if "messages" not in st.session_state:
    # Seed from persisted session_history so the chat survives page refreshes
    history = st.session_state.learning_state.get("session_history", [])
    st.session_state.messages = [
        {"role": m["role"], "content": m["content"]} for m in history
    ]

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🇪🇸 Your Progress")

    s = st.session_state.learning_state
    level = s.get("level", "beginner")
    level_icon = {"beginner": "🟢", "intermediate": "🟡", "advanced": "🔴"}.get(level, "🟢")
    st.metric("Level", f"{level_icon} {level.capitalize()}")

    st.divider()

    vocab = s.get("vocabulary_seen", [])
    st.metric("Words Learned", len(vocab))
    if vocab:
        with st.expander("Vocabulary"):
            st.write(", ".join(vocab))

    st.divider()

    topics = s.get("topics_covered", [])
    st.metric("Topics Covered", len(topics))
    if topics:
        with st.expander("Topics"):
            for t in topics:
                st.write(f"• {t}")

    st.divider()

    mistakes = s.get("recent_mistakes", [])
    if mistakes:
        with st.expander(f"Recent mistakes ({len(mistakes)})"):
            for m in mistakes:
                st.write(f"• {m}")

    st.divider()
    if st.button("Reset Progress", type="secondary", use_container_width=True):
        fresh = learning_state.DEFAULT_STATE.copy()
        fresh["vocabulary_seen"] = []
        fresh["recent_mistakes"] = []
        fresh["topics_covered"] = []
        fresh["session_history"] = []
        learning_state.save(fresh)
        st.session_state.learning_state = fresh
        st.session_state.messages = []
        st.rerun()

# ── Main chat area ─────────────────────────────────────────────────────────────
st.title("Spanish Learning Tutor")
st.caption("Chat with your AI tutor — ask to learn vocabulary, do exercises, or get feedback on your answers.")

AGENT_LABELS = {
    "assessment": "Assessment",
    "lesson": "Lesson",
    "practice": "Practice",
    "feedback": "Feedback",
}

for msg in st.session_state.messages:
    avatar = "🧑" if msg["role"] == "user" else "🎓"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if msg.get("agent"):
            st.caption(f"{AGENT_LABELS.get(msg['agent'], msg['agent'])} agent")

if prompt := st.chat_input("Say something in Spanish or ask your tutor anything…"):
    state = st.session_state.learning_state

    # Show user message immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    # Route and respond
    with st.chat_message("assistant", avatar="🎓"):
        with st.spinner(""):
            decision = orchestrator.decide(state, prompt)
            agent_name = decision.get("agent", "lesson")
            topic = decision.get("topic", "")

            if agent_name == "assessment":
                raw_response = agents.assessment_agent(state, prompt)
            elif agent_name == "lesson":
                raw_response = agents.lesson_agent(state, prompt, topic)
            elif agent_name == "practice":
                raw_response = agents.practice_agent(state, prompt, topic)
            elif agent_name == "feedback":
                raw_response = agents.feedback_agent(state, prompt)
            else:
                raw_response = agents.lesson_agent(state, prompt, topic)

        display_response = clean_response(raw_response)
        st.markdown(display_response)
        st.caption(f"{AGENT_LABELS.get(agent_name, agent_name)} agent")

    # Persist to session state
    st.session_state.messages.append({
        "role": "assistant",
        "content": display_response,
        "agent": agent_name,
    })

    # Update and save learning state
    learning_state.add_to_history(state, "user", prompt)
    learning_state.add_to_history(state, "assistant", raw_response)
    if topic and topic not in state["topics_covered"]:
        state["topics_covered"].append(topic)
    update_state_from_response(state, agent_name, raw_response)
    learning_state.save(state)
    st.session_state.learning_state = state

    st.rerun()
