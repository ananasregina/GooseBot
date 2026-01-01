# Changelog

All notable changes to this project will be documented in this file.

## [1.3.0] - 2026-01-01

### Added
- **Attachment Support**: Support for image attachments in Discord. The bot now detects multimodal capabilities via ACP and processes images (Base64 encoding) to send to Goose.
- **Command: `/reset_session`**: New slash command as an alias for `/restart_session` to reset the current Goose session.

### Fixed
- **Session Management**: Resolved attribute errors in `clear_session` and `restart_session` by ensuring consistent method naming across `SessionManager`, `GooseClient`, and `CommandHandler`.
- **Session Clearing**: Fixed an issue where local session mappings were not actually being removed when clearing a session.
- **Message Finalization**: Resolved lag and truncation issues in Discord responses by ensuring strict synchronization between streamed chunks and final RPC results.

## [1.2.0] - 2026-01-01

## [1.1.0] - 2026-01-01

### Added
- **Command: `/capy`**: New slash command to get fresh, delicious Capybara facts and news via web search.
- **Model Selection**: Added support for `GOOSE_MODEL` environment variable to choose the AI model.
- **System Instructions**: Automatic injection of Discord context (Server, Channel, User) as system level instructions for Goose sessions.
- **Slash Command: `/compact`**: New command to manually trigger session compaction/summarization, helping manage context window and token usage.
- **Performance Optimizations**:
    - Reduced logging noise from Discord and Textual libraries to the TUI.
    - Implemented event filtering/limiting in TUI to prevent UI blocking the main bot logic.
- **Better Error Handling**: Improved logic for session restoration and error reporting in `GooseClient`.

### Changed
- Updated `README.md` and `config.env.example` with new settings and features.

## [1.0.0] - 2025-12-25
- Initial release of GooseBot.
- Basic chat integration with Goose via ACP.
- Session persistence and basic slash commands.
