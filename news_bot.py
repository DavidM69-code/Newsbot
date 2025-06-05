import os
import logging
import threading
import socket
from contextlib import closing
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests

# --- Configuration --- #
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
NEWS_API_URL = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"
PORT = 10000  # Must match Render port setting

# --- Setup --- #
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Dummy HTTP server for Render
app = Flask(__name__)

@app.route('/')
def health_check():
    return "🤖 NewsBot is running", 200

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

# --- Bot Functions --- #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome to NewsBot! Send /news for headlines")

async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get(NEWS_API_URL, timeout=10)
        response.raise_for_status()
        
        articles = response.json().get("articles", [])
        if not articles:
            await update.message.reply_text("❌ No news found")
            return

        for article in articles[:5]:  # Limit to 5 articles
            title = article.get('title', 'No title')
            url = article.get('url', '')
            message = f"📰 {title}" + (f"\n🔗 {url}" if url else "")
            await update.message.reply_text(message)

    except Exception as e:
        logger.error(f"News fetch error: {e}")
        await update.message.reply_text("⚠️ Error fetching news. Try again later.")

# --- Instance Control --- #
def port_in_use(port):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        return sock.connect_ex(('localhost', port)) == 0

# --- Main --- #
if __name__ == "__main__":
    # Validate config
    if not BOT_TOKEN or not NEWS_API_KEY:
        logger.error("Missing environment variables!")
        exit(1)

    # Prevent multiple instances
    if port_in_use(PORT):
        logger.error(f"Port {PORT} already in use - another instance running?")
        exit(1)

    # Start health check server
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Configure bot
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("news", get_news))

    # Clean start
    await application.bot.delete_webhook(drop_pending_updates=True)
    logger.info("Starting bot...")
    
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            close_loop=False
        )
    except Exception as e:
        logger.critical(f"Bot crashed: {e}")
    finally:
        logger.info("Bot stopped")
