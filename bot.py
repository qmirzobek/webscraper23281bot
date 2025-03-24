import os
import requests
import telebot
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import yt_dlp

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

    # Extract text
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

# ✅ Function to download a YouTube video in a single format (avoiding ffmpeg errors)
def download_video(url):
    output_dir = "downloads"
    os.makedirs(output_dir, exist_ok=True)  # Create downloads folder if not exists

    ydl_opts = {
        "format": "best",  # ✅ Avoids "bestvideo+bestaudio" merging issue
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)
        return file_path

# ✅ Function to download audio separately as MP3
def download_audio(url):
    output_dir = "downloads"
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        "format": "bestaudio",  # ✅ Downloads only the best audio format
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info).replace(info["ext"], "mp3")
        return file_path

# ✅ Function to download an entire YouTube playlist
def download_playlist(url):
    output_dir = "downloads"
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        "format": "best",
        "outtmpl": os.path.join(output_dir, "%(playlist)s/%(title)s.%(ext)s"),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        return output_dir

# ✅ Telegram bot command: Handle /start
@bot.message_handler(commands=["start"])
def start_message(message):
    bot.reply_to(message, "Send me a website link, YouTube video, or playlist, and I'll extract content!")

# ✅ Handle links
@bot.message_handler(func=lambda message: message.text.startswith("http"))
def handle_link(message):
    url = message.text.strip()

    if "youtube.com" in url or "youtu.be" in url:
        if "playlist" in url:
            bot.send_message(message.chat.id, f"📥 Downloading full playlist: {url}")
            playlist_path = download_playlist(url)
            bot.send_message(message.chat.id, "✅ Playlist downloaded! Check your files.")
        else:
            bot.send_message(message.chat.id, f"📥 Downloading video: {url}")
            video_path = download_video(url)

            if os.path.exists(video_path):
                with open(video_path, "rb") as video_file:
                    bot.send_video(message.chat.id, video_file)
                os.remove(video_path)
            else:
                bot.send_message(message.chat.id, "❌ Failed to download video.")

            bot.send_message(message.chat.id, "🎵 Extracting audio...")
            audio_path = download_audio(url)

            if os.path.exists(audio_path):
                with open(audio_path, "rb") as audio_file:
                    bot.send_audio(message.chat.id, audio_file)
                os.remove(audio_path)
            else:
                bot.send_message(message.chat.id, "❌ Failed to extract audio.")

    else:
        bot.send_message(message.chat.id, f"🔍 Extracting content from: {url}")

        # Extract text
        text = extract_text(url)
        if len(text) > 4096:
            bot.send_message(message.chat.id, text[:4096])
            for i in range(4096, len(text), 4096):
                bot.send_message(message.chat.id, text[i:i + 4096])
        else:
            bot.send_message(message.chat.id, text)

        # Extract images
        images = extract_images(url)
        if images:
            for img_url in images:
                bot.send_photo(message.chat.id, img_url)
        else:
            bot.send_message(message.chat.id, "❌ No images found.")

# ✅ Start the bot
print("🤖 Bot is running...")
bot.polling()
