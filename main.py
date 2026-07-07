import re
import state as st
import orchestrator
import agents

from dotenv import load_dotenv
load_dotenv()

def update_state_from_response(state: dict, agent_name: str, response: str):
    """Parse any structured tags the agents embed in their replies."""

    # Assessment agent signals a new level
    if agent_name == "assessment":
        match = re.search(r"LEVEL:\s*(beginner|intermediate|advanced)", response, re.IGNORECASE)
        if match:
            state["level"] = match.group(1).lower()

    # Lesson agent signals new vocabulary
    if agent_name == "lesson":
        match = re.search(r"VOCAB:\s*(.+)", response)
        if match:
            new_words = [w.strip() for w in match.group(1).split(",")]
            state["vocabulary_seen"].extend(new_words)
            # Keep the list from growing forever
            state["vocabulary_seen"] = list(dict.fromkeys(state["vocabulary_seen"]))[-100:]

    # Feedback agent signals a mistake
    if agent_name == "feedback":
        match = re.search(r"MISTAKES:\s*(.+)", response)
        if match and match.group(1).strip().lower() != "none":
            state["recent_mistakes"].append(match.group(1).strip())
            state["recent_mistakes"] = state["recent_mistakes"][-10:]


def main():
    print("🇪🇸  Spanish Learning Agent  —  type 'quit' to exit\n")

    while True:
        user_input = input("You: ").strip()
        if not user_input or user_input.lower() in ("quit", "exit"):
            print("¡Hasta luego!")
            break

        # 1. Load current state from disk
        state = st.load()

        # 2. Orchestrator decides which agent to call
        decision = orchestrator.decide(state, user_input)
        agent_name = decision.get("agent", "lesson")
        topic = decision.get("topic", "")

        print(f"\n[Routing → {agent_name} agent]\n")

        # 3. Call the chosen specialist agent
        if agent_name == "assessment":
            response = agents.assessment_agent(state, user_input)
        elif agent_name == "lesson":
            response = agents.lesson_agent(state, user_input, topic)
        elif agent_name == "practice":
            response = agents.practice_agent(state, user_input, topic)
        elif agent_name == "feedback":
            response = agents.feedback_agent(state, user_input)
        else:
            response = agents.lesson_agent(state, user_input, topic)

        print(f"Tutor: {response}\n")

        # 4. Update shared state
        st.add_to_history(state, "user", user_input)
        st.add_to_history(state, "assistant", response)
        if topic and topic not in state["topics_covered"]:
            state["topics_covered"].append(topic)
        update_state_from_response(state, agent_name, response)

        # 5. Save state back to disk
        st.save(state)


if __name__ == "__main__":
    main()