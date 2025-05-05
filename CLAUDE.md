# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Run the application: `python main.py` (console) or `python main.py --web` (web interface)
- Run a specific test: `python test_claude.py` or `python minimal_test.py` or `python test_http.py`
- Setup environment: `bash setup.sh`

## Code Style Guidelines
- **Imports**: Standard library first, then third-party packages, then local modules; sort alphabetically
- **Formatting**: Use 4-space indentation; line length under 100 characters
- **Types**: Use type hints when defining functions (Python 3.11+ compatible)
- **Naming**: snake_case for variables/functions, UPPER_CASE for constants
- **Error Handling**: Use try/except blocks with specific exceptions; log errors with descriptive messages
- **Logging**: Use the standard logging module with appropriate log levels
- **API Calls**: Handle timeouts and HTTP status codes; provide informative error messages
- **Environment Variables**: Access via os.environ.get() with appropriate defaults
- **Documentation**: Include docstrings for functions and modules; use concise descriptive comments