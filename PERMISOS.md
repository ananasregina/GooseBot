# Discord Permissions Guide for GooseBot 🪿

## Overview

GooseBot requires specific Discord permissions and Gateway Intents to function properly. This guide explains each permission, why it's needed, and how to verify it's working.

---

## 📋 Quick Reference

### Minimum Required (Bot MUST HAVE)
- ✅ **Send Messages** (0x000008)
- ✅ **Read Messages** (0x000004)
- ✅ **Use Slash Commands** (0x000002)
- ✅ **Message Content Intent** (Privileged Gateway Intent)

### Recommended (For Full Functionality)
- ✅ All of the above
- ✅ **Embed Links** (0x000020)
- ✅ **Mention Everyone** (0x00000800)

### Optional (Not Required)
- ⚠️ **Server Members Intent** (Performance optimization)
- ⚠️ **Presence Intent** (Online status tracking)

---

## 🔍 Bot Permissions (OAuth2)

These permissions are set when inviting the bot to a server.

### 1. OAuth2 Scopes

| Scope | Required? | Purpose | Where to Configure |
|--------|------------|---------|-------------------|
| `bot` | ✅ **YES** | Adds bot as a user | OAuth2 URL Generator |
| `applications.commands` | ✅ **YES** | Allows slash commands | OAuth2 URL Generator |

**How to configure:**
1. Discord Developer Portal → Your Application → OAuth2 → URL Generator
2. Select scopes: Check `bot` and `applications.commands`
3. Generate invitation URL
4. Use URL to invite bot

### 2. Bot Permissions

#### Critical Permissions

**Send Messages** (0x000008)
- **Description**: Send messages in channels
- **Required for**: Bot responses, replies to @mentions
- **How to verify**: Bot can send messages
- **What breaks without this**: Bot reads @mentions but cannot reply

**Read Messages** (0x000004)
- **Description**: Read messages in channels
- **Required for**: Processing `@GooseBot` mentions
- **How to verify**: Check Discord server permissions
- **What breaks without this**: Bot cannot see message content at all

**Use Slash Commands** (0x000002)
- **Description**: Use application commands (slash commands)
- **Required for**: `/set_name`, `/clear_session`, `/status`, `/help`
- **How to verify**: Type `/` and see command list
- **What breaks without this**: Slash commands don't appear

#### Optional Permissions

**Embed Links** (0x000020)
- **Description**: Embed links in messages
- **Purpose**: Richer, better-formatted bot responses
- **Not required but**: Makes responses look better

**Attach Files** (0x000040)
- **Description**: Upload files to Discord
- **Purpose**: Attachment support (planned feature)
- **Status**: ⚠️ **FUTURE** - Not yet implemented

**Mention Everyone** (0x00000800)
- **Description**: Allow @everyone and @here mentions
- **Purpose**: Admin convenience
- **Risk**: Can be abused; only enable if needed
- **How to verify**: Bot can mention @everyone

**Add Reactions** (0x0000080)
- **Description**: Add emoji reactions
- **Status**: ❌ **NOT NEEDED** - GooseBot doesn't use reactions

**Read Message History** (0x0000200000)
- **Description**: Read old messages
- **Status**: ❌ **NOT NEEDED** - Only processes new messages

---

## 🔑 Gateway Intents (Privileged)

Gateway Intents control what events the bot receives via Discord's WebSocket connection.

### Required Intents

**Message Content Intent** ⚠️ **CRITICAL**

- **Description**: Allows bot to read message content, attachments, embeds
- **Required for**: Processing `@GooseBot` mentions
- **Code location**: `goosebot/bot.py` line 29: `intents.message_content = True`
- **Discord config**: Developer Portal → Your App → Bot → Privileged Gateway Intents
- **Verification needed**: ✅ **YES** (if bot in >100 servers or privileged intents)
- **Without this**: Bot cannot read message content at all!

**What this enables:**
- Reading `Message.content` (message text)
- Reading `Message.attachments` (file uploads)
- Reading `Message.embeds` (embedded content)
- Reading message text for @mentions

**Guilds Intent**

- **Description**: Receive events about servers
- **Required for**: Getting guild IDs, channel IDs
- **Code location**: `goosebot/bot.py` line 31: `intents.guilds = True`
- **Verification needed**: ❌ **NO**
- **Without this**: Bot cannot get server information

**Messages Intent**

- **Description**: Receive message events
- **Required for**: `on_message()` event handler
- **Code location**: `goosebot/bot.py` line 30: `intents.messages = True`
- **Verification needed**: ❌ **NO**
- **Without this**: Bot never receives messages!

### Optional Intents

**Server Members Intent**

- **Description**: Receive events about member joins/leaves/updates
- **Purpose**: Member list caching, improved performance
- **Code location**: `goosebot/bot.py` line 32: `intents.members = True`
- **Verification needed**: ✅ **YES** (if enabled)
- **Without this**: Works, but member list may be incomplete

**Presence Intent**

- **Description**: Receive user status (online, idle, etc.)
- **Purpose**: Track user activity
- **Status**: ❌ **NOT USED**
- **Verification needed**: ✅ **YES** (if enabled)

---

## ✅ Setup Checklist

Before running GooseBot, ensure:

### Discord Developer Portal Configuration

- [ ] Application created and named
- [ ] Bot created under application
- [ ] **Message Content Intent** enabled (CRITICAL)
- [ ] Server Members Intent enabled (optional)
- [ ] Bot token copied safely (only shown once!)
- [ ] Bot token added to `config.env`

### OAuth2 URL Generation

- [ ] Scope `bot` selected
- [ ] Scope `applications.commands` selected
- [ ] Permission **Send Messages** checked
- [ ] Permission **Read Messages** checked
- [ ] Permission **Use Slash Commands** checked
- [ ] (Optional) **Embed Links** checked
- [ ] (Optional) **Mention Everyone** checked
- [ ] Invitation URL generated
- [ ] Bot invited to test server

### Bot Verification

- [ ] Bot appears in server member list
- [ ] Bot has correct permissions in server settings
- [ ] `/help` command works
- [ ] `@GooseBot` mention triggers response

---

## 🧪 Troubleshooting

### Problem: "Bot doesn't respond to mentions"

**Possible Causes:**

1. **Missing Permissions**
   - Check server settings → Integrations → GooseBot
   - Verify "Send Messages" and "Read Messages" are enabled
   - Re-invite bot if permissions look incorrect

2. **Message Content Intent Disabled**
   - Discord Developer Portal → Your App → Bot → Privileged Gateway Intents
   - Ensure "Message Content Intent" is toggled ON
   - Restart bot after enabling

3. **Wrong Code Configuration**
   - Check `goosebot/bot.py` line 29: `intents.message_content = True`
   - The intent must be enabled in BOTH code AND Discord Portal

4. **Bot Token Issues**
   - Verify `DISCORD_BOT_TOKEN` in `config.env`
   - Token must be valid and not expired
   - Regenerate token if needed (shows only once!)

5. **Rate Limiting**
   - Discord may limit requests
   - Wait a few seconds and try again

### Problem: "Slash commands don't appear"

**Possible Causes:**

1. **Missing "Use Slash Commands" permission**
   - OAuth2 URL must include this permission
   - Check invitation permissions were correct
   - Re-invite bot with correct permissions

2. **Commands not synced**
   - Bot syncs commands automatically on startup
   - Wait 10-30 seconds after bot starts
   - Check logs for "Synced X command(s)" message

3. **Permission Conflict**
   - Server admin may have restricted bot's permissions
   - Check server's role/permission settings for bot role

### Problem: "Message Content Intent verification required"

**Context:**
- Discord requires verification for bots in >100 servers
- Also required for all bots using privileged intents (regardless of server count)

**Solution:**

1. **Prepare Verification Information**
   - Bot description: Explain what your bot does
   - Example: "AI assistant that responds to @mentions with helpful information"
   - Website repository: Link to your GitHub
   - Privacy policy: How you handle user data

2. **Submit Verification Request**
   - Discord Developer Portal → Your App → Bot
   - Look for "Verification Required" banner
   - Click "Verification" button
   - Fill out verification form

3. **Verification Process**
   - Takes 1-3 business days typically
   - Email notification when approved
   - No code changes needed after approval

4. **If Rejected**
   - Discord will explain why
   - Common reasons:
     - Unclear purpose
     - Missing information
     - Violates ToS
   - Improve application and re-submit

---

## 🎯 Permission Best Practices

### Minimum Viable Configuration

For GooseBot to work:

```
OAuth2 Scopes:
- bot
- applications.commands

Bot Permissions:
- Send Messages (0x000008)
- Read Messages (0x000004)
- Use Slash Commands (0x000002)

Gateway Intents:
- Message Content ✅ REQUIRED
- Guilds ✅ REQUIRED
- Messages ✅ REQUIRED
```

### Recommended Configuration

For best experience:

```
OAuth2 Scopes:
- bot
- applications.commands

Bot Permissions:
- Send Messages (0x000008)
- Read Messages (0x000004)
- Use Slash Commands (0x000002)
- Embed Links (0x000020)
- Mention Everyone (0x00000800)

Gateway Intents:
- Message Content ✅ REQUIRED
- Guilds ✅ REQUIRED
- Messages ✅ REQUIRED
- Server Members ⚠️ OPTIONAL
```

### Security Considerations

- ❌ **Don't** enable "Administrator" permission unless necessary
- ❌ **Don't** enable "Manage Messages" (0x000010) unless needed
- ✅ **Do** follow principle of least privilege
- ✅ **Do** document why each permission is needed
- ✅ **Do** use environment variables for tokens (never hardcode!)

---

## 📚 Additional Resources

- [Discord Documentation - Permissions](https://discord.com/developers/docs/topics/permissions)
- [Discord Documentation - Intents](https://discord.com/developers/docs/topics/gateway#privileged-intents)
- [Discord Developer Portal](https://discord.com/developers/applications)
- [discord.py Documentation - Intents](https://discordpy.readthedocs.io/en/stable/intents.html)

---

## ❓ Frequently Asked Questions

### Do I need to verify my bot?

**A**: It depends on:
- ✅ **Yes, if**: Bot in >100 servers OR using Message Content Intent
- ❌ **No, if**: Bot in <100 servers AND only using non-privileged intents

### Can I run GooseBot without Message Content Intent?

**A**: ❌ **No!** Message Content Intent is **CRITICAL** for GooseBot because:
- Bot needs to read `@GooseBot` mentions
- Bot needs to extract message text after mention
- Without it, bot cannot function at all

### Why does my bot show "Missing Access" error?

**A**: Common reasons:
- Bot invited to server but permissions not granted
- OAuth2 URL didn't include required scopes/permissions
- Server admin disabled specific permissions
- Message Content Intent not enabled in Discord Portal

### Is a web server / port forwarding required?

**A**: ❌ **No**, for GooseBot's current architecture:
- GooseBot uses Discord Gateway WebSocket (direct connection)
- No HTTP endpoint needed
- It connects *out* to Discord and Goose ACP, so no inbound ports need to be opened.
### What if my verification is denied?

**A**: Discord typically explains why. Common solutions:
1. Improve bot description with more details
2. Add GitHub repository link
3. Explain legitimate use case clearly
4. Add privacy policy documentation
5. Re-apply after making improvements

---

## 🚀 Quick Setup Command

```bash
#1. Complete Discord Developer Portal setup
# (Follow checklist above)

#2. Generate OAuth2 URL with correct permissions
# (Use Quick Reference tables)

#3. Invite bot to test server

#4. Start GooseBot
source .venv/bin/activate
python run.py

#5. Test with:
@GooseBot hello!
```

---

**Last Updated**: December 31, 2025
