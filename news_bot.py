from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests

BOT_TOKEN = "TelegramTOKEN"
NEWS_API_KEY = "NewsAPIKEY"
NEWS_API_URL = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome to NewsBot!\nSend /news to get the latest headlines.")

async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get(NEWS_API_URL)
        data = response.json()
        articles = data.get("articles", [])

        if not articles:
            await update.message.reply_text("❌ No news found.")
            return

        for article in articles[:5]:
            title = article.get("title", "No title")
            url = article.get("url", "")
            message = f"📰 {title}\n🔗 {url}"
            await update.message.reply_text(message)

    except Exception:
        await update.message.reply_text("⚠️ Error fetching news.")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("news", get_news))

print("🚀 NewsBot is running...")
app.run_polling()
