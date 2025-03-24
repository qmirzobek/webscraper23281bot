import os
import requests
import telebot
from bs4 import BeautifulSoup
from urllib.parse import urljoin
# from requests_html import HTMLSession
import subprocess
import json
import scrapy

from scrapy_splash import SplashRequest

class PinterestSpider(scrapy.Spider):
    name = "pinterest"
    allowed_domains = ["pinterest.com"]

    def start_requests(self):
        query = getattr(self, "query", None)  # Get search term from command
        if not query:
            return

        search_url = f"https://www.pinterest.com/search/pins/?q={query}"
        yield SplashRequest(url=search_url, callback=self.parse, args={"wait": 2})

    def parse(self, response):
        images = response.css("img::attr(src)").getall()
        yield {"images": images[:10]}  # Return first 10 images

# 🔹 Replace with your Telegram bot token from @BotFather
BOT_TOKEN = os.getenv("YOUR_BOT_TOKEN")
PINTEREST_ACCESS_TOKEN = os.getenv("PINTEREST_ACCESS_TOKEN")  # Store API Token in Env Vars

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

# ✅ Function to fetch images from Pinterest API
def fetch_pinterest_images(query):
    url = f"https://api.pinterest.com/v5/search/pins?query={query}&page_size=10"
    headers = {"Authorization": f"Bearer {PINTEREST_ACCESS_TOKEN}"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        images = [pin["images"]["original"]["url"] for pin in data.get("items", []) if "images" in pin]
        return images
    else:
        print(f"Error: {response.json()}")
        return []

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


# ✅ Telegram bot command: Handle links
@bot.message_handler(func=lambda message: message.text.startswith("http"))
def handle_link(message):
    url = message.text.strip()
    bot.send_message(message.chat.id, f"🔍 Extracting content from: {url}")

    # Extract and send text
    text = extract_text(url)
    if len(text) > 4096:
        bot.send_message(message.chat.id, f"📄 Website Text:\n{text[:4096]}")
        for i in range(4096, len(text), 4096):
            bot.send_message(message.chat.id, f"{text[i:i+4096]}")
    else:
        bot.send_message(message.chat.id, f"📄 Website Text:\n{text}")

    # Extract and send images
    images = extract_images(url)
    if images:
        for img_url in images:
            bot.send_photo(message.chat.id, img_url)
    else:
        bot.send_message(message.chat.id, "❌ No images found.")


@bot.message_handler(commands=["start"])
def start_message(message):
    bot.reply_to(message, "Send me a website link, or use /pinterest <query> to search images!")

# ✅ Start the bot
print("🤖 Bot is running...")
bot.polling()
