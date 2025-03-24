import os
import requests
import telebot
from pytube import YouTube
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

# ✅ Function to download YouTube video using pytube
def download_youtube_video(url):
    yt = YouTube(url)
    
    # Download video
    video_stream = yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc().first()
    video_path = video_stream.download(filename="video.mp4")

    # Download audio separately
    audio_stream = yt.streams.filter(only_audio=True).first()
    audio_path = audio_stream.download(filename="audio.mp4")

    # Convert audio to MP3
    mp3_audio_path = "audio.mp3"
    os.rename(audio_path, mp3_audio_path)

    return video_path, mp3_audio_path

# ✅ Telegram bot command: Handle /start
@bot.message_handler(commands=["start"])
def start_message(message):
    bot.reply_to(message, "Send me a website link or YouTube link, and I'll extract content or download videos!")

# ✅ Telegram bot command: Handle links
@bot.message_handler(func=lambda message: message.text.startswith("http"))
def handle_link(message):
    url = message.text.strip()
    bot.send_message(message.chat.id, f"🔍 Extracting content from: {url}")

    # Detect if the link is a YouTube video
    if "youtube.com" in url or "youtu.be" in url:
        bot.send_message(message.chat.id, "📥 Downloading YouTube video...")
        try:
            video_path, audio_path = download_youtube_video(url)
            
            # Send video
            with open(video_path, "rb") as video:
                bot.send_video(message.chat.id, video)

            # Send audio
            with open(audio_path, "rb") as audio:
                bot.send_audio(message.chat.id, audio)

            # Delete files after sending
            os.remove(video_path)
            os.remove(audio_path)
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Failed to download video: {str(e)}")
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
