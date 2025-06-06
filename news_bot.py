import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import threading

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get configuration from environment
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NEWSAPI_KEY = os.getenv('NEWSAPI_KEY')
PING_CHAT_ID = os.getenv('PING_CHAT_ID')  # Your private chat ID (get from @userinfobot)

# News categories
CATEGORIES = {
    'general': 'General',
    'business': 'Business',
    'entertainment': 'Entertainment',
    'health': 'Health',
    'science': 'Science',
    'sports': 'Sports',
    'technology': 'Technology'
}

# ================== Self-Ping System ================== #
def self_ping(context: CallbackContext):
    """Automatically pings to keep the bot online"""
    try:
        context.bot.send_message(
            chat_id=PING_CHAT_ID,
            text="🤖 Bot heartbeat - Keeping connection alive",
            disable_notification=True
        )
        logger.info("Keep-alive ping sent")
    except Exception as e:
        logger.error(f"Ping failed: {e}")

# ================== News Functions ================== #
def get_news(category=None, query=None):
    """Fetch news from NewsAPI"""
    base_url = "https://newsapi.org/v2/"
    
    if query:
        url = f"{base_url}everything?q={query}&sortBy=publishedAt&apiKey={NEWSAPI_KEY}"
    elif category:
        url = f"{base_url}top-headlines?category={category}&apiKey={NEWSAPI_KEY}"
    else:
        url = f"{base_url}top-headlines?apiKey={NEWSAPI_KEY}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data['articles'] if data['status'] == 'ok' else None
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return None

def format_news(articles, limit=5):
    """Format news articles for Telegram"""
    if not articles:
        return "No news articles found."
    
    messages = []
    for article in articles[:limit]:
        title = article.get('title', 'No title')
        source = article.get('source', {}).get('name', 'Unknown source')
        url = article.get('url', '#')
        published_at = article.get('publishedAt', '')
        
        if published_at:
            try:
                pub_date = datetime.strptime(published_at, '%Y-%m-%dT%H:%M:%SZ')
                published_at = pub_date.strftime('%B %d, %Y %H:%M UTC')
            except ValueError:
                pass
        
        message = f"<b>{title}</b>\n<i>Source: {source}</i>"
        if published_at:
            message += f"\n<i>Published: {published_at}</i>"
        message += f"\n<a href='{url}'>Read more</a>"
        messages.append(message)
    
    return "\n\n".join(messages)

# ================== Command Handlers ================== #
def start(update: Update, context: CallbackContext) -> None:
    """Send welcome message"""
    user = update.effective_user
    update.message.reply_text(
        f"Hi {user.first_name}!\n\n"
        "I'm your News Bot. Use /news for latest headlines or /help for commands."
    )

def news(update: Update, context: CallbackContext) -> None:
    """Send general news"""
    articles = get_news()
    message = format_news(articles)
    update.message.reply_text(message, parse_mode='HTML', disable_web_page_preview=True)

def categories(update: Update, context: CallbackContext) -> None:
    """Show news categories"""
    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"category_{cat}")]
        for cat, name in CATEGORIES.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Choose a category:', reply_markup=reply_markup)

def category_handler(update: Update, context: CallbackContext) -> None:
    """Handle category selection"""
    query = update.callback_query
    query.answer()
    category = query.data.split('_')[1]
    articles = get_news(category=category)
    message = f"<b>{CATEGORIES[category]} News</b>\n\n{format_news(articles)}"
    query.edit_message_text(text=message, parse_mode='HTML', disable_web_page_preview=True)

# ================== Main Bot Setup ================== #
def main():
    """Start the bot with keep-alive pings"""
    updater = Updater(TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher
    job_queue = updater.job_queue

    # Add command handlers
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('news', news))
    dispatcher.add_handler(CommandHandler('categories', categories))
    dispatcher.add_handler(CallbackQueryHandler(category_handler, pattern='^category_'))

    # Set up keep-alive pings (every 10 minutes)
    job_queue.run_repeating(
        self_ping,
        interval=600,  # 10 minutes between pings
        first=10       # Initial delay (seconds)
    )

    # Start the bot
    updater.start_polling()
    logger.info("Bot started with keep-alive system")
    updater.idle()

if __name__ == '__main__':
    main()