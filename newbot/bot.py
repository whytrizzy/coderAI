import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode, ChatAction
from google import genai
from google.genai import types
import db

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GLOBAL_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = (
    "You are an expert programming and software development assistant.\n"
    "Your absolute rule is to ONLY answer questions related to programming, coding, "
    "software engineering, databases, computer science, DevOps, system architecture, "
    "and development-related tools (like Git, Docker, package managers, etc.).\n"
    "If the user's query is not about programming, coding, or software development, "
    "you MUST politely decline to answer.\n"
    "Your response for non-programming queries should be: "
    "\"I am programmed to assist only with programming and development-related queries. "
    "Please ask a development-related question!\" or a polite variation of it.\n"
    "Be precise, helpful, and write high-quality code.\n"
    "If code is requested, provide well-commented, clean, and modern code."
)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start or /help is issued."""
    welcome_text = (
        "👋 **Welcome to the Programming Assistant Bot!**\n\n"
        "I am an AI assistant designed **exclusively** to help you with programming, "
        "software engineering, system design, database management, DevOps, and developer tools.\n\n"
        "🛠️ **Commands:**\n"
        "• `/start` or `/help` - Show this welcome message.\n"
        "• `/setkey <api_key>` - Set your own personal Google Gemini API key.\n"
        "• `/clearkey` - Delete your saved API key from my database.\n\n"
        "🔑 **API Key Configuration:**\n"
    )
    
    if GLOBAL_GEMINI_API_KEY:
        welcome_text += (
            "✅ A global Gemini API key is configured. You can start asking programming questions "
            "immediately! However, you can still set your own key using `/setkey` to override the global key."
        )
    else:
        welcome_text += (
            "⚠️ No global API key is configured. **You must set your own Gemini API key** to use the bot.\n"
            "1. Get a free key from [Google AI Studio](https://aistudio.google.com/).\n"
            "2. Send me `/setkey <your_api_key>` to get started."
        )
        
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

async def set_key_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Store the user's Gemini API key in SQLite."""
    user_id = update.effective_user.id
    
    # Extract API key from command arguments
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Please provide your Gemini API key.\n"
            "Example: `/setkey AIzaSyYourKeyHere`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
        
    api_key = context.args[0].strip()
    
    # Basic validation: Gemini keys typically start with AIzaSy
    if not api_key.startswith("AIzaSy"):
        await update.message.reply_text(
            "⚠️ Warning: This doesn't look like a standard Gemini API key (typically starts with 'AIzaSy'). "
            "Please verify your key and try again if it doesn't work."
        )
        
    db.set_user_key(user_id, api_key)
    
    # Mask the key for display confirmation
    masked_key = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else "Saved Key"
    
    await update.message.reply_text(
        f"✅ **API Key saved successfully!**\n"
        f"Configured key: `{masked_key}`\n\n"
        f"You can now send me any programming questions.",
        parse_mode=ParseMode.MARKDOWN
    )

async def clear_key_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete the user's Gemini API key from SQLite."""
    user_id = update.effective_user.id
    deleted = db.delete_user_key(user_id)
    
    if deleted:
        await update.message.reply_text("✅ Your personal Gemini API key has been removed from the database.")
    else:
        await update.message.reply_text("ℹ️ You don't have a personal API key saved in the database.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the user's message and query Gemini."""
    if not update.message or not update.message.text:
        return
        
    user_id = update.effective_user.id
    user_prompt = update.message.text
    
    # Determine API key: User key overrides global key
    user_key = db.get_user_key(user_id)
    api_key = user_key or GLOBAL_GEMINI_API_KEY
    
    if not api_key:
        await update.message.reply_text(
            "⚠️ **API Key Required**\n"
            "I don't have access to an API key to process your request.\n\n"
            "Please get a free key from [Google AI Studio](https://aistudio.google.com/) "
            "and configure it using:\n"
            "`/setkey <your_api_key>`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
        
    # Send typing action to Telegram user interface
    await update.message.chat.send_action(action=ChatAction.TYPING)
    
    try:
        # Initialize Gemini Client
        client = genai.Client(api_key=api_key)
        
        # Define the configuration with system instruction
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION
        )
        
        # Call Gemini API in a separate thread to prevent blocking the async loop
        response = await asyncio.to_thread(
            client.models.generate_content,
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=config
        )
        
        bot_response = response.text
        if not bot_response:
            bot_response = "Error: Gemini returned an empty response."
            
    except Exception as e:
        logger.error(f"Error querying Gemini API: {e}")
        error_msg = str(e)
        if "API_KEY_INVALID" in error_msg or "API key not valid" in error_msg:
            await update.message.reply_text(
                "❌ **Invalid API Key**\n"
                "The API key provided was rejected. Please double-check your key or "
                "set a new one with `/setkey <key>`.",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                f"❌ **An error occurred while connecting to the AI:**\n"
                f"`{error_msg}`",
                parse_mode=ParseMode.MARKDOWN
            )
        return
        
    # Send the response back to the user, handling Markdown parsing errors gracefully
    try:
        await update.message.reply_text(bot_response, parse_mode=ParseMode.MARKDOWN)
    except Exception as parse_error:
        logger.warning(f"Failed to parse markdown response, falling back to plain text. Error: {parse_error}")
        try:
            # Fall back to plain text
            await update.message.reply_text(bot_response)
        except Exception as send_error:
            logger.error(f"Failed to send message: {send_error}")

def main() -> None:
    """Start the bot."""
    # Check if Telegram Bot Token is set
    if not TELEGRAM_BOT_TOKEN:
        logger.critical("TELEGRAM_BOT_TOKEN environment variable not set. Exiting.")
        print("CRITICAL: TELEGRAM_BOT_TOKEN environment variable not set. Please configure it in .env")
        return
        
    # Initialize SQLite database
    logger.info("Initializing database...")
    db.init_db()
    
    # Create the Telegram Application
    logger.info("Starting Telegram bot...")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", start_command))
    application.add_handler(CommandHandler("setkey", set_key_command))
    application.add_handler(CommandHandler("clearkey", clear_key_command))
    
    # Register text message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    print("Bot is starting... Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
