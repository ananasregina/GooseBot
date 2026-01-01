# TODO List

## High Priority ✅ (Completed)
- [x] `/set_name <name>` - Set the agent name for new sessions
- [x] `/clear_session` - Clear current channel's Goose session
- [x] `/restart_session` - Restart (delete and recreate) the session
- [x] **Persistent Session Storage**: Save channel→session mappings to file
- [x] **State Persistence**: Maintain conversation context across bot restarts
- [x] **Streaming**: Real-time response streaming to Discord
- [x] **Conversational Continuity**: Listening window for natural follow-ups

## Medium Priority ✅ (Completed)
- [x] `/status` - Show current session info and agent name
- [x] `/help` - Display command usage and help

## Core Features ✅ (Completed)
- [x] Discord bot with @mention support
- [x] Goose ACP (Agent Client Protocol) integration
- [x] Per-channel session management
- [x] Session continuity (resume sessions)
- [x] Configuration management
- [x] Error handling and logging
- [x] Type hints throughout codebase
- [x] Async/await patterns for Discord
- [x] Setup verification script
- [x] Full documentation (README, QUICKSTART)

## Low Priority (Future Enhancements)

### Planned Features
- [ ] **Attachment Support**: Handle file attachments and images
  - Add attachment download handler
  - Pass file paths to Goose CLI
  - Support multiple file types

- [ ] **Queue System**: Allow concurrent Goose CLI requests
  - Implement request queue
  - Better handle high-traffic servers
  - Add timeout/backoff logic

- [ ] **Session Export/Import**: Allow users to save and restore conversations
  - Export Discord conversations to files
  - Import conversations into sessions

- [ ] **Advanced Slash Commands**:
  - [ ] `/export_session` - Export conversation to file
  - [ ] `/import_session` - Import conversation from file
  - [ ] `/list_sessions` - List all bot sessions
  - [ ] `/config` - View/change bot settings
  - [ ] `/stats` - Show usage statistics

- [ ] **Infrastructure**:
  - [ ] Docker containerization
  - [ ] Deployment scripts
  - [ ] CI/CD pipeline

## Security
- [ ] Add rate limiting per user
- [ ] Token rotation support
- [ ] Audit logging

## Status Summary

**Completed**: 100% of initial core tasks.
**Current Version**: 1.1.0 (with Persistence and Streaming)

GooseBot is fully functional and ready for production use with session persistence and real-time streaming!
