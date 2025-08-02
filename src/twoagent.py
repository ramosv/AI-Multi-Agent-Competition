import requests
import sys
import time
from datetime import datetime

# Agent 1 Configuration
AGENT1_NAME = "Agent 1"
AGENT1_LLM = "openai/gpt-4"
AGENT1_SYSTEM_PROMPT = "You are Agent 1, a creative and imaginative AI who loves storytelling, metaphors, and thinking outside the box. You're enthusiastic and often come up with unexpected ideas. Keep your responses concise but colorful."
AGENT1_TEMPERATURE = 1.2  # Higher temperature for more creativity
AGENT1_MAX_TOKENS = 150

# Agent 2 Configuration
AGENT2_NAME = "Agent 2"
AGENT2_LLM = "openai/gpt-4"
AGENT2_SYSTEM_PROMPT = "You are Agent 2, a logical and analytical AI who values precision, facts, and structured thinking. You like to break things down systematically and ask clarifying questions. Keep your responses concise but thorough."
AGENT2_TEMPERATURE = 0.7  # Lower temperature for more focused responses
AGENT2_MAX_TOKENS = 150

# Shared Configuration
OPENROUTER_API_KEY = "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"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_HISTORY = 20  # Number of messages to remember
DELAY_BETWEEN_MESSAGES = 0.5  # Seconds between messages for readability

# Store conversation history
conversation_history = []


def generate_response(prompt, agent_config, history):
    """Generate response for a specific agent"""
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        # Build messages with agent's personality and history
        messages = [{"role": "system", "content": agent_config["system_prompt"]}]

        # Add conversation history
        for msg in history[-MAX_HISTORY:]:
            messages.append(msg)

        # Add current message
        messages.append({"role": "user", "content": prompt})

        data = {
            "model": agent_config["model"],
            "messages": messages,
            "temperature": agent_config["temperature"],
            "max_tokens": agent_config["max_tokens"],
        }

        response = requests.post(OPENROUTER_API_URL, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()

        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return "I couldn't generate a response."

    except Exception as e:
        print(f"\n[Error] {agent_config['name']}: {type(e).__name__}: {e}")
        return "Sorry, I encountered an error."


def print_message(agent_name, message, color_code=""):
    """Print a formatted message from an agent"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{color_code}[{timestamp}] {agent_name}: {message}\033[0m")


def print_welcome():
    """Print welcome message"""
    print("\n" + "="*70)
    print("🤖 Two AI Agents Counting Game 🤖")
    print("="*70)
    print(f"\n\033[95m{AGENT1_NAME}\033[0m vs \033[96m{AGENT2_NAME}\033[0m")
    print("\nPress Ctrl+C to stop at any time")
    print("="*70)


def get_user_input():
    """Get conversation parameters from user"""
    print("\nPress Enter to start the counting game (or 'quit' to exit)")

    user_input = input().strip()
    if user_input.lower() == 'quit':
        return False

    return True


def run_conversation():
    """Run a conversation between two agents"""
    # Always start with counting game
    starting_topic = "Let's play a counting game! I'll start: 1"

    print(f"\n{'='*70}")
    print(f"Starting endless conversation (Press Ctrl+C to stop)")
    print(f"{'='*70}\n")

    # Agent configurations
    agent1 = {
        "name": AGENT1_NAME,
        "model": AGENT1_LLM,
        "system_prompt": AGENT1_SYSTEM_PROMPT,
        "temperature": AGENT1_TEMPERATURE,
        "max_tokens": AGENT1_MAX_TOKENS,
        "color": "\033[95m"  # Purple
    }

    agent2 = {
        "name": AGENT2_NAME,
        "model": AGENT2_LLM,
        "system_prompt": AGENT2_SYSTEM_PROMPT,
        "temperature": AGENT2_TEMPERATURE,
        "max_tokens": AGENT2_MAX_TOKENS,
        "color": "\033[96m"  # Cyan
    }

    # Clear conversation history for new conversation
    conversation_history.clear()

    # Start with the topic directed at Agent 1
    current_message = starting_topic
    current_speaker = None
    next_speaker = agent1

    # Run forever until interrupted
    turn = 0
    while True:
        try:
            # Show typing indicator
            print(f"{next_speaker['color']}[{next_speaker['name']} is thinking...]\033[0m", end="\r")

            # Generate response
            response = generate_response(
                current_message,
                next_speaker,
                conversation_history
            )

            # Clear typing indicator
            print(" " * 50, end="\r")

            # Print the response
            print_message(next_speaker['name'], response, next_speaker['color'])

            # Update conversation history
            if current_speaker:
                conversation_history.append({
                    "role": "assistant" if current_speaker == agent1 else "user",
                    "content": current_message
                })
            conversation_history.append({
                "role": "assistant" if next_speaker == agent1 else "user",
                "content": response
            })

            # Prepare for next turn
            current_message = response
            current_speaker = next_speaker
            next_speaker = agent2 if next_speaker == agent1 else agent1
            turn += 1

            # Delay for readability
            time.sleep(DELAY_BETWEEN_MESSAGES)

        except KeyboardInterrupt:
            print(f"\n\n{'='*70}")
            print(f"Conversation ended after {turn} exchanges")
            print(f"{'='*70}\n")
            break


def main():
    """Main function"""
    print_welcome()

    try:
        run_conversation()
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"\n[Error] {type(e).__name__}: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)