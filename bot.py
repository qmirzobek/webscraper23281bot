import os
import requests
import telebot
import yt_dlp
from bs4 import BeautifulSoup
from urllib.parse import urljoin

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

    return soup.get_text(separator="\n").strip()

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

# ✅ Function to download YouTube video using yt-dlp
def download_youtube_video(url):
    ydl_opts = {
        "format": "bestvideo+bestaudio/best",  # Get best video & audio
        "outtmpl": "video.%(ext)s",  # Save video file
        "postprocessors": [
            {"key": "FFmpegVideoConvertor", "preferedformat": "mp4"},
        ],
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_filename = ydl.prepare_filename(info)
        video_filename = video_filename.replace(info['ext'], 'mp4')
    
    # Download audio separately
    ydl_opts_audio = {
        "format": "bestaudio/best",
        "outtmpl": "audio.%(ext)s",
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3"},
        ],
    }
    
    with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
        ydl.extract_info(url, download=True)

    return video_filename, "audio.mp3"

# ✅ Function to download all videos from a YouTube playlist
def download_youtube_playlist(url):
    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": "playlist/%(title)s.%(ext)s",
        "postprocessors": [
            {"key": "FFmpegVideoConvertor", "preferedformat": "mp4"},
        ],
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    video_files = [f"playlist/{video['title']}.mp4" for video in info["entries"]]

    return video_files

# ✅ Telegram bot command: Handle /start
@bot.message_handler(commands=["start"])
def start_message(message):
    bot.reply_to(message, "Send me a website or YouTube link (video or playlist), and I'll process it!")

# ✅ Telegram bot command: Handle links
@bot.message_handler(func=lambda message: message.text.startswith("http"))
def handle_link(message):
    url = message.text.strip()
    bot.send_message(message.chat.id, f"🔍 Extracting content from: {url}")

    # Detect if the link is a YouTube **playlist**
    if "playlist" in url:
        bot.send_message(message.chat.id, "📥 Downloading entire YouTube playlist...")
        try:
            video_files = download_youtube_playlist(url)
            
            # Send all videos one by one
            for video_file in video_files:
                with open(video_file, "rb") as video:
                    bot.send_video(message.chat.id, video)
                os.remove(video_file)
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Failed to download playlist: {str(e)}")
        return

    # Detect if the link is a YouTube **video**
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
