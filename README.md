# GooseBot 🪿

A Discord bot that bridges Discord and the Goose.ai CLI, allowing users to interact with Goose's AI capabilities directly from Discord with real-time streaming and session persistence.

## Features

- **Conversational Continuity**: Responds to @mentions, Direct Messages, and replies.
- **Listening Window**: Stays attentive for 5 minutes (configurable) after its last response, allowing natural conversation without constant pinging.
- **Real-time Streaming**: Response chunks are streamed to Discord as they arrive, providing a smooth experience.
- **Session Persistence**: Remembers conversation context across bot restarts by saving state to `~/.config/goosebot/`.
- **Slash Commands**: Control sessions with `/clear_session`, `/restart_session`, `/set_name`, `/status`, and `/help`.
- **Agent Naming**: Customize the agent name per server.
- **Goose ACP Integration**: Uses the Agent Client Protocol (ACP) for high-performance communication.

## Prerequisites

1. **Python 3.11+**
2. **uv** (Python package manager)
3. **Goose CLI 1.18.0+** installed and configured

## Setup

### 1. Install Dependencies

```bash
# Activate virtual environment
source .venv/bin/activate

# Install Python dependencies
uv pip install -r requirements.txt
```

### 2. Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" tab and create a bot
4. Enable **Message Content Intent** (CRITICAL) and **Server Members Intent**
5. Copy the bot token

### 3. Configure Bot

1. Copy example config:
    ```bash
    cp config.env.example config.env
    ```

2. Edit `config.env` and add your Discord token:
    ```env
    DISCORD_BOT_TOKEN=your_actual_bot_token_here
    LISTEN_WINDOW_SECONDS=300
    ```

### 4. Invite Bot to Server

1. In Discord Developer Portal → OAuth2 → URL Generator
2. Select **Scopes**: `bot`, `applications.commands`
3. Select **Bot Permissions**:
   - Send Messages
   - Use Slash Commands
   - Read Messages/View Channels
   - Embed Links (Optional)
4. Copy the generated URL and open it in a browser to authorize.

### 5. Start the Bot

```bash
python run.py
```

## Usage

### Basic Chat

- **@Mention**: Mention the bot in any channel.
- **Follow-up**: After the bot replies, it will "listen" to the channel for 5 minutes (default). Any message you send in that channel during this time will be processed without needing a mention.
- **Reply**: Reply to any of the bot's previous messages.
- **Direct Message**: Message the bot directly for a private conversation.

### Slash Commands

- `/set_name <name>` - Set the agent name for new sessions in this server
- `/clear_session` - Clear the current Goose session for this channel
- `/restart_session` - Restart (delete and recreate) the session
- `/status` - Show the current session status and information
- `/help` - Display help information and available commands

## Architecture

GooseBot uses **Discord Gateway WebSocket** for communication and communicates with Goose CLI via **ACP (Agent Client Protocol)** over stdio.

```
┌─────────────────────────────────────────┐
│  Discord User Message / Mention        │
│              ↓                          │
│  Discord Gateway (WebSocket)            │
│              ↓                          │
│    GooseBot (discord.py)                │
│              ↓                          │
│  Goose ACP Process (JSON-RPC)           │
│              ↓                          │
│  Streaming Response Chunks              │
│              ↓                          │
│  Discord Message Edit (Throttled)       │
└─────────────────────────────────────────┘
```

## Troubleshooting

### Bot doesn't respond to mentions
- ✅ Verify **Message Content Intent** is enabled in Discord Developer Portal (CRITICAL)
- ✅ Ensure bot has "Read Messages" and "Send Messages" permissions
- ✅ Check `config.env` for the correct token
- Check logs for "Unknown update type" or connection errors.

### Sessions lost?
- Check `~/.config/goosebot/` for `sessions.json` and `client_sessions.json`. These files store the state.

## License

MIT License - feel free to use and modify!
