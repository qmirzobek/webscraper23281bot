import os
import requests
import telebot
from bs4 import BeautifulSoup
import yt_dlp
from urllib.parse import quote_plus, urljoin

# 🔹 Replace with your Telegram bot token
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

    text = soup.get_text(separator="\n").strip()
    return text

# ✅ Function to extract images from a website
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

# ✅ Function to download YouTube video as MP4
def download_youtube_video(url):
    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": "video.mp4",
        "merge_output_format": "mp4",
        "quiet": True
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    return "video.mp4"

# ✅ Function to download YouTube audio as MP3
def download_youtube_audio(url):
    ydl_opts = {
        "format": "bestaudio",
        "outtmpl": "audio.mp3",
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
        "quiet": True
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    return "audio.mp3"

# ✅ Function to search Pinterest images
def search_pinterest(query):
    headers = {"User-Agent": "Mozilla/5.0"}
    search_url = f"https://www.pinterest.com/search/pins/?q={quote_plus(query)}"
    response = requests.get(search_url, headers=headers)

    soup = BeautifulSoup(response.text, "html.parser")
    image_urls = []

    for img_tag in soup.find_all("img", limit=10):  # Get first 10 images
        img_url = img_tag.get("src")
        if img_url and "https://" in img_url:
            image_urls.append(img_url)

    return image_urls

# ✅ Telegram bot command: Handle /start
@bot.message_handler(commands=["start"])
def start_message(message):
    bot.reply_to(
        message, "Send me a website link, YouTube video, or Pinterest search query!\n"
        "👉 `/pinterest cats` to search Pinterest images\n"
        "👉 Send a **YouTube link** to download video/audio\n"
        "👉 Send any **website link** to extract text & images."
    )

# ✅ Handle website links
@bot.message_handler(func=lambda message: message.text.startswith("http"))
def handle_link(message):
    url = message.text.strip()
    bot.send_message(message.chat.id, f"🔍 Extracting content from: {url}")

    if "youtube.com" in url or "youtu.be" in url:
        bot.send_message(message.chat.id, "📥 Downloading YouTube video...")
        video_path = download_youtube_video(url)
        audio_path = download_youtube_audio(url)

        # Send video
        with open(video_path, "rb") as video:
            bot.send_video(message.chat.id, video)
        
        # Send audio
        with open(audio_path, "rb") as audio:
            bot.send_audio(message.chat.id, audio)

    else:
        text = extract_text(url)
        bot.send_message(message.chat.id, f"📄 Website Text:\n{text[:4096]}")

        images = extract_images(url)
        if images:
            for img_url in images:
                bot.send_photo(message.chat.id, img_url)
        else:
            bot.send_message(message.chat.id, "❌ No images found.")

# ✅ Handle Pinterest search queries
@bot.message_handler(commands=["pinterest"])
def handle_pinterest(message):
    query = message.text.replace("/pinterest", "").strip()
    
    if not query:
        bot.reply_to(message, "❌ Please provide a search term. Example: `/pinterest cats`")
        return

    bot.send_message(message.chat.id, f"🔎 Searching Pinterest for '{query}'...")
    
    image_urls = search_pinterest(query)
    
    if not image_urls:
        bot.send_message(message.chat.id, "❌ No images found!")
    else:
        for img_url in image_urls:
            bot.send_photo(message.chat.id, img_url)

# ✅ Start the bot
print("🤖 Bot is running...")
bot.polling()
