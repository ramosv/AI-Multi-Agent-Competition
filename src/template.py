import requests
import sys
from datetime import datetime

# Agent Configuration
AGENT_NAME = "Terminal AI Agent"
AGENT_LLM = "openai/gpt-4"  # Can use any OpenRouter model
AGENT_LLM_SYSTEM_PROMPT = "You are a helpful assistant in a terminal conversation."
AGENT_LLM_TEMPERATURE = 1.0
AGENT_LLM_MAX_TOKENS = 1000
AGENT_MAX_HISTORY = 10  # Number of conversation turns to remember

# OpenRouter Configuration
OPENROUTER_API_KEY = "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"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Store conversation history for context
conversation_history = []


def generate_response(prompt):
    """Generate response using OpenRouter API with conversation context"""
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        # Build messages array with system prompt and conversation history
        messages = [{"role": "system", "content": AGENT_LLM_SYSTEM_PROMPT}]

        # Add conversation history
        for msg in conversation_history[-AGENT_MAX_HISTORY:]:
            messages.append(msg)

        # Add current user message
        messages.append({"role": "user", "content": prompt})

        data = {
            "model": AGENT_LLM,
            "messages": messages,
            "temperature": AGENT_LLM_TEMPERATURE,
            "max_tokens": AGENT_LLM_MAX_TOKENS,
        }

        response = requests.post(OPENROUTER_API_URL, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()

        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return "Sorry, I couldn't generate a response."

    except requests.exceptions.HTTPError as e:
        print(f"\n[Error] HTTP Error from OpenRouter: {e}")
        if e.response is not None:
            try:
                error_data = e.response.json()
                if "error" in error_data:
                    error_msg = error_data["error"].get("message", "Unknown error")
                    print(f"[Error] {error_msg}")
            except:
                pass
        return "Sorry, there was an error generating a response."
    except requests.exceptions.RequestException as e:
        print(f"\n[Error] Network error: {e}")
        return "Sorry, there was a network error."
    except Exception as e:
        print(f"\n[Error] Unexpected error: {type(e).__name__}: {e}")
        return "Sorry, an unexpected error occurred."


def print_welcome():
    """Print welcome message and instructions"""
    print("\n" + "="*50)
    print(f"Welcome to {AGENT_NAME}!")
    print(f"Model: {AGENT_LLM}")
    print("="*50)
    print("\nCommands:")
    print("  /quit, /exit, /q - Exit the program")
    print("  /clear - Clear conversation history")
    print("  /history - Show conversation history")
    print("\nJust type your message and press Enter to chat!")
    print("="*50 + "\n")


def print_history():
    """Print conversation history"""
    print("\n" + "-"*30 + " History " + "-"*30)
    if not conversation_history:
        print("No conversation history yet.")
    else:
        for i, msg in enumerate(conversation_history):
            role = "You" if msg["role"] == "user" else "AI"
            print(f"{role}: {msg['content'][:100]}{'...' if len(msg['content']) > 100 else ''}")
    print("-"*69 + "\n")


def run_agent():
    """Main function to run the terminal agent"""
    print_welcome()

    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()

            # Check for commands
            if user_input.lower() in ['/quit', '/exit', '/q']:
                print("\nGoodbye! Thanks for chatting!")
                break
            elif user_input.lower() == '/clear':
                conversation_history.clear()
                print("\n[Conversation history cleared]\n")
                continue
            elif user_input.lower() == '/history':
                print_history()
                continue
            elif not user_input:
                continue

            # Show thinking indicator
            print("AI: ", end="", flush=True)
            print("Thinking...", end="\r", flush=True)

            # Generate response
            response = generate_response(user_input)

            # Clear thinking indicator and print response
            print(" " * 20, end="\r")  # Clear the "Thinking..." message
            print(f"AI: {response}")
            print()  # Empty line for readability

            # Add to conversation history
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": response})

            # Keep conversation history size manageable
            if len(conversation_history) > AGENT_MAX_HISTORY * 2:
                conversation_history[:] = conversation_history[-AGENT_MAX_HISTORY:]

        except KeyboardInterrupt:
            print("\n\n[Interrupted by user]")
            print("Type /quit to exit or press Enter to continue chatting.")
            continue
        except Exception as e:
            print(f"\n[Error] {type(e).__name__}: {e}")
            continue


if __name__ == "__main__":
    try:
        run_agent()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)