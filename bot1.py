import os
import requests
import telebot
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote_plus
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

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

    return images[:5]  # Limit to first 5 images

# ✅ Function to search Pinterest for images
def search_pinterest(query):
    # Configure Chrome for headless browsing
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    # Set up ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Open Pinterest search page
        search_url = f"https://www.pinterest.com/search/pins/?q={quote_plus(query)}"
        driver.get(search_url)

        # Wait for images to load
        time.sleep(5)  # Allow dynamic content to load

        # Extract image elements
        images = driver.find_elements(By.TAG_NAME, "img")

        image_urls = []
        for img in images[:10]:  # Get first 10 images
            img_url = img.get_attribute("src")
            if img_url and "https://" in img_url:
                image_urls.append(img_url)

        return image_urls

    finally:
        driver.quit()  # Close browser

# ✅ Telegram bot command: Handle /start
@bot.message_handler(commands=["start"])
def start_message(message):
    bot.reply_to(message, "Send me a website link, and I'll extract text, images, and videos!")

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

# ✅ Telegram bot command: Handle /pinterest search
@bot.message_handler(commands=["pinterest"])
def pinterest_search(message):
    query = message.text.replace("/pinterest", "").strip()
    if not query:
        bot.reply_to(message, "Please provide a search term. Example: `/pinterest cats`")
        return

    bot.send_message(message.chat.id, f"🔍 Searching Pinterest for: {query}")

    images = search_pinterest(query)
    if images:
        for img_url in images:
            bot.send_photo(message.chat.id, img_url)
    else:
        bot.send_message(message.chat.id, "❌ No images found.")

# ✅ Start the bot
print("🤖 Bot is running...")
bot.polling()
