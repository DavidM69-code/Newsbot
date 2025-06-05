import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests

# Dummy HTTP server for Render
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 NewsBot is running!", 200

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# Load config
BOT_TOKEN = os.getenv('BOT_TOKEN')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
NEWS_API_URL = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"

# Bot commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome to NewsBot!")

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

if __name__ == "__main__":
    # Start Flask server in background
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Start Telegram bot
    bot = ApplicationBuilder().token(BOT_TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("news", get_news))
    print("🤖 Bot is starting...")
    bot.run_polling()
