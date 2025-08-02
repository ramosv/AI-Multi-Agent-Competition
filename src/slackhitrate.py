import time
import requests
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest
from datetime import datetime

# Agent Configuration
AGENT_NAME = "Slack AI Agent"
AGENT_LLM = "openai/gpt-4"
AGENT_LLM_SYSTEM_PROMPT = "You are a helpful assistant agent in a Slack channel."
AGENT_LLM_TEMPERATURE = 1.0
AGENT_LLM_MAX_TOKENS = 1000
AGENT_MAX_HISTORY = 10  # Keep last 10 messages for context

# Slack Configuration
SLACK_BOT_TOKEN = "xoxb-9289779940197-9291934200246-TXt8f0bWAT8ZrcnOVzKGjelb"
SLACK_APP_TOKEN = "xapp-1-A09949YQKU1-9292075500406-35a135d487d157545748ad2a5bcf34119d5f2de699a3eb6c5afcaffb31c870e8"
# CHANNEL_ID = "C098KSPAD0E"
CHANNEL_ID = "C099ACK4P6U"

# OpenRouter Configuration
OPENROUTER_API_KEY = "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"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Initialize clients
web_client = WebClient(token=SLACK_BOT_TOKEN)

# Get bot user ID first
try:
    bot_info = web_client.auth_test()
    BOT_USER_ID = bot_info["user_id"]
    print(f"✓ Connected to Slack! Bot User ID: {BOT_USER_ID}")
except Exception as e:
    print(f"Failed to connect with bot token: {e}")
    exit(1)

# Initialize socket client after confirming bot token works
socket_client = SocketModeClient(
    app_token=SLACK_APP_TOKEN,
    web_client=web_client
)


# Store recent conversation history
conversation_history = []

# Track processed messages to avoid duplicates
processed_messages = set()
MESSAGE_DEDUP_WINDOW = 10  # seconds

def generate_response(prompt, history=None):
    """Generate response using OpenRouter API with optional history"""
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        messages = [{"role": "system", "content": AGENT_LLM_SYSTEM_PROMPT}]

        # Add conversation history if provided
        if history:
            for h in history[-8:]:  # Last 8 messages for context
                messages.append({"role": h["role"], "content": h["content"]})

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

    except Exception as e:
        print(f"Error generating response: {e}")
        return "Sorry, there was an error generating a response."


def send_message(channel, text):
    """Send a message to Slack"""
    try:
        response = web_client.chat_postMessage(
            channel=channel,
            text=text
        )
        return response
    except Exception as e:
        print(f"Error sending message: {e}")
        return None


def process_event(client: SocketModeClient, req: SocketModeRequest):
    """Process incoming events"""
    if req.type == "events_api":
        # Acknowledge the request
        response = SocketModeResponse(envelope_id=req.envelope_id)
        client.send_socket_mode_response(response)

        # Get the event
        event = req.payload.get("event", {})
        event_type = event.get("type")

        # Handle message events
        if event_type == "message":
            # Skip bot messages
            if event.get("bot_id") or event.get("user") == BOT_USER_ID:
                return

            # Skip subtypes (edits, deletes)
            if event.get("subtype"):
                return

            # Only respond in our channel
            if event.get("channel") != CHANNEL_ID:
                return

            text = event.get("text", "")
            user = event.get("user", "Unknown")
            ts = event.get("ts", "")

            # Create a unique message identifier
            message_id = f"{user}-{text}-{int(float(ts))}"

            # Skip if we've seen this message recently
            if message_id in processed_messages:
                return

            # Add to processed messages
            processed_messages.add(message_id)

            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] New message from {user}: {text}")

            # Add user message to history
            conversation_history.append({"role": "user", "content": text})

            # Generate and send response with history
            reply = generate_response(text, conversation_history)
            print(f"Responding: {reply[:100]}...")

            # Add bot response to history
            conversation_history.append({"role": "assistant", "content": reply})

            # Keep history size manageable
            if len(conversation_history) > AGENT_MAX_HISTORY * 2:
                conversation_history[:] = conversation_history[-AGENT_MAX_HISTORY:]

            send_message(CHANNEL_ID, reply)
    else:
        # Acknowledge other request types
        response = SocketModeResponse(envelope_id=req.envelope_id)
        client.send_socket_mode_response(response)


def main():
    print(f"{AGENT_NAME} is starting...")
    print(f"Using OpenRouter API with model: {AGENT_LLM}")
    print(f"Monitoring channel: {CHANNEL_ID}")

    # Set up event listener
    socket_client.socket_mode_request_listeners.append(process_event)

    # Connect with better error handling
    try:
        print("Connecting to Socket Mode...")
        socket_client.connect()
        print("✓ Socket Mode connected!")
    except Exception as e:
        print(f"Failed to connect to Socket Mode: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Socket Mode is enabled in your app settings")
        print("2. Make sure Event Subscriptions are enabled")
        print("3. Try regenerating the Socket Mode token")
        return

    print(f"\n{AGENT_NAME} is ready!")
    print("Real-time message processing enabled - NO DELAYS!")
    print("Press Ctrl+C to stop\n")

    try:
        # Keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        socket_client.close()


if __name__ == "__main__":
    main()