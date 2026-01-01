# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2026-01-01

### Added
- **Command: `/noticias`**: New slash command to search for news on a specific topic with a personalized analysis.
- **Typing Indicators**: Added Discord "typing" indicators for slash commands (`/capy` and `/noticias`) to provide better visual feedback during long-running tasks.

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
