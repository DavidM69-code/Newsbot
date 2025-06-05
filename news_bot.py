import os
import signal
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests

# Load environment variables securely
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
NEWS_API_URL = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"

# Validate configuration
if not BOT_TOKEN or not NEWS_API_KEY:
    raise ValueError("Missing required environment variables!")

# Graceful shutdown handler for Render.com
def shutdown_handler(signum, frame):
    print("🛑 Received shutdown signal. Stopping bot gracefully...")
    if 'app' in globals():
        app.stop()
    exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, shutdown_handler)  # For Render
signal.signal(signal.SIGINT, shutdown_handler)   # For Ctrl+C

# Bot commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome to NewsBot!\nSend /news to get the latest headlines.")

async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get(NEWS_API_URL, timeout=10)
        response.raise_for_status()
        
        articles = response.json().get("articles", [])
        if not articles:
            await update.message.reply_text("❌ No news found.")
            return

        for article in articles[:5]:
            message = f"📰 {article.get('title', 'No title')}"
            if url := article.get('url'):
                message += f"\n🔗 {url}"
            await update.message.reply_text(message)

    except Exception as e:
        print(f"⚠️ Error: {str(e)}")
        await update.message.reply_text("⚠️ Error fetching news. Please try again later.")

# Main application
if __name__ == "__main__":
    print("🚀 Starting NewsBot...")
    
    try:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("news", get_news))
        
        print("🤖 Bot is running. Press Ctrl+C to stop.")
        app.run_polling()
        
    except Exception as e:
        print(f"💥 Critical error: {str(e)}")
        exit(1)
