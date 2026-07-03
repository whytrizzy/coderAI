# Programming Assistant Telegram Bot

A Python-based Telegram bot that uses Google Gemini AI to answer coding and software development questions. The bot is strictly restricted to programming and development topics, and allows users to set their own API keys dynamically.

## Features

- **Programming & Development Only**: Configured with a system instruction that ensures the AI only replies to software development, coding, databases, DevOps, and computer science questions. It will politely decline any non-technical topics.
- **Dynamic API Key Management**:
  - Supports a global developer key specified in the environment (`.env`).
  - Supports individual user keys set using the `/setkey` command, stored in a local SQLite database.
  - Allows users to clear their keys via `/clearkey`.
- **Typing Indicator**: Displays "typing..." in Telegram while waiting for Gemini to generate the response.
- **Markdown Formatting Safety**: Graceful fallback to plain text if the AI response has formatting tags that break Telegram's parser.
- **Asynchronous Execution**: Leverages `asyncio` and `python-telegram-bot` v22+ without blocking the main event loop.

---

## Setup Instructions

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.14)
- A Telegram account to create a bot.
- A Google Gemini API key (optional if using the user-key method, but required to run the bot with a global key).

### 2. Create a Telegram Bot
1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Start a chat and send the `/newbot` command.
3. Follow the instructions to give your bot a name and a username.
4. Copy the API Token (e.g., `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`).

### 3. Get a Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Click on **Create API Key**.
3. Copy the generated key (starts with `AIzaSy`).

### 4. Installation & Configuration
Clone this workspace or navigate to the directory, then follow these steps:

1. **Create a virtual environment**:
   ```bash
   py -m venv .venv
   ```

2. **Activate the virtual environment**:
   - **Windows (Command Prompt)**:
     ```cmd
     .venv\Scripts\activate
     ```
   - **Windows (PowerShell)**:
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS**:
     ```bash
     source .venv/bin/activate
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file from the template:
   ```bash
   copy .env.example .env
   ```
   Edit `.env` and fill in your configuration:
   - `TELEGRAM_BOT_TOKEN`: The token you received from BotFather.
   - `GEMINI_API_KEY`: (Optional) A global Gemini API key to allow anyone to use the bot without setting their own.

### 5. Running the Bot
To run the bot locally:
```bash
python bot.py
```

---

## Bot Commands

- `/start` or `/help` - Displays the bot's welcome message and usage instructions.
- `/setkey <api_key>` - Saves a personal Gemini API key. This key will be used for all future queries by this user, overriding the global fallback key.
- `/clearkey` - Removes the personal API key from the local SQLite database.

---

## Database Architecture
The bot saves user API keys in a local SQLite file named `bot_data.db`. The schema is simple:
```sql
CREATE TABLE IF NOT EXISTS user_keys (
    user_id INTEGER PRIMARY KEY,
    gemini_api_key TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
No personal user data (username, chat messages) is stored, making it lightweight and secure.
