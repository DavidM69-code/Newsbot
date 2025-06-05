import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests

# Load environment variables
load_dotenv()

# Secure token/key access
BOT_TOKEN = os.getenv("BOT_TOKEN")  # From .env or Render environment
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_API_URL = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome to NewsBot!\nSend /news to get the latest headlines.")

async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get(NEWS_API_URL)
        
        # Better error handling
        if response.status_code != 200:
            await update.message.reply_text(f"❌ News API Error: {response.status_code}")
            return
            
        data = response.json()
        articles = data.get("articles", [])

        if not articles:
            await update.message.reply_text("❌ No news found.")
            return

        for article in articles[:5]:  # Limit to 5 articles
            title = article.get("title", "No title")
            url = article.get("url", "")
            message = f"📰 {title}\n🔗 {url}" if url else f"📰 {title}"
            await update.message.reply_text(message)

    except Exception as e:
        print(f"Error: {e}")  # Logging for debugging
        await update.message.reply_text("⚠️ Error fetching news. Please try again later.")

if __name__ == "__main__":
    # Validate token before starting
    if not BOT_TOKEN:
        raise ValueError("No BOT_TOKEN found! Check your .env or environment variables")
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("news", get_news))
    app.run_polling()
