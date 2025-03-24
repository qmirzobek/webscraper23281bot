import os
import requests
import telebot
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from requests_html import HTMLSession

# 🔹 Replace with your Telegram bot token from @BotFather
BOT_TOKEN = os.getenv("YOUR_BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# ✅ Function to extract text from a website
def extract_text(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # Remove unnecessary elements like scripts & styles
    for tag in soup(["script", "meta", "noscript"]):
        tag.extract()

    # Extract text
    text = soup.get_text(separator="\n").strip()
    return text

# ✅ Function to extract image URLs
def extract_images(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    images = []
    for img_tag in soup.find_all("img"):
        img_url = img_tag.get("src")
        if img_url:
            img_url = urljoin(url, img_url)  # Convert relative to absolute URL
            images.append(img_url)

    return images[:10]  # Limit to first 5 images

# ✅ Function to fetch Pinterest images using requests-html
def fetch_pinterest_images(query):
    session = HTMLSession()
    url = f"https://www.pinterest.com/search/pins/?q={query}"
    response = session.get(url)
    response.html.render()  # Execute JavaScript

    # Extract image URLs
    images = response.html.xpath('//img/@src')
    return images[:10]  # Return first 10 images

# ✅ Telegram bot command: Handle /pinterest
@bot.message_handler(commands=["pinterest"])
def pinterest_search(message):
    query = message.text.replace("/pinterest ", "").strip()

    if not query:
        bot.reply_to(message, "❌ Please provide a search term. Example: `/pinterest cats`")
        return

    bot.send_message(message.chat.id, f"🔍 Searching Pinterest for: {query}")
    images = fetch_pinterest_images(query)

    if images:
        for img_url in images:
            bot.send_photo(message.chat.id, img_url)
    else:
        bot.send_message(message.chat.id, "❌ No images found.")

# ✅ Telegram bot command: Handle /start
@bot.message_handler(commands=["start"])
def start_message(message):
    bot.reply_to(message, "Send me a website link, or use /pinterest <query> to search images!")

# ✅ Start the bot
print("🤖 Bot is running...")
bot.polling()
