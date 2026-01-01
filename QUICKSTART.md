# Quick Start Guide 🦆

## 1. Install Dependencies
```bash
source .venv/bin/activate
uv pip install -r requirements.txt
```

## 2. Set Up Discord Bot
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create "New Application" → "Bot"
3. Enable **Message Content Intent** (Gateway Intent section)
4. Copy **Bot Token**

## 3. Configure
```bash
cp config.env.example config.env
# Edit config.env:
# DISCORD_BOT_TOKEN=your_token_here
```

## 4. Launch
```bash
python run.py
```

## 5. Test
- Ping `@GooseBot hello` in any channel.
- Send another message immediately after, it will reply without a ping (listening window).
- Try `/help` for more commands.
