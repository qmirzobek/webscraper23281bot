import os
import requests
import telebot
import yt_dlp
from bs4 import BeautifulSoup
from urllib.parse import urljoin

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

# ✅ Function to download video using yt-dlp
def download_video(url):
    output_file = "video.mp4"
    ydl_opts = {
        'outtmpl': output_file,  # Save as "video.mp4"
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'quiet': True,  # No unnecessary logs
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return output_file

# ✅ Telegram bot command: Handle /start
@bot.message_handler(commands=["start"])
def start_message(message):
    bot.reply_to(message, "Send me a website link or video link, and I'll extract content or download the video!")

# ✅ Telegram bot command: Handle links
@bot.message_handler(func=lambda message: message.text.startswith("http"))
def handle_link(message):
    url = message.text.strip()
    bot.send_message(message.chat.id, f"🔍 Extracting content from: {url}")

    # Detect if the link is a video site
    if "youtube.com" in url or "youtu.be" in url or "twitter.com" in url or "instagram.com" in url:
        bot.send_message(message.chat.id, "📥 Downloading video...")
        try:
            video_path = download_video(url)
            with open(video_path, "rb") as video:
                bot.send_video(message.chat.id, video)
            os.remove(video_path)  # Delete file after sending
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Video download failed: {str(e)}")
        return

    # Extract and send text
    text = extract_text(url)
    if len(text) > 4096:
        for i in range(0, len(text), 4096):
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

# ✅ Start the bot
print("🤖 Bot is running...")
bot.polling()
