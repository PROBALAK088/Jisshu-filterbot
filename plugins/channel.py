
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from info import CHANNELS, MOVIE_UPDATE_CHANNEL, ADMINS , LOG_CHANNEL
from database.ia_filterdb import save_file, unpack_new_file_id
from utils import get_poster, temp
import re
from database.users_chats_db import db
import ffmpeg

async def extract_thumbnail(video_path, output_image="thumbnail.jpg"):
    try:
        (
            ffmpeg
            .input(video_path, ss=5)  # 5 সেকেন্ড পরের ফ্রেম নেবে
            .output(output_image, vframes=1)
            .run(overwrite_output=True)
        )
        return output_image
    except Exception as e:
        print(f"Thumbnail extraction failed: {e}")
        return None

async def send_movie_updates(bot, file_name, caption, file_id, video_path=None):
    try:
        year_match = re.search(r"\b(19|20)\d{2}\b", caption)
        year = year_match.group(0) if year_match else None      
        pattern = r"(?i)(?:s|season)0*(\d{1,2})"
        season = re.search(pattern, caption)
        if not season:
            season = re.search(pattern, file_name) 
        if year:
            file_name = file_name[:file_name.find(year) + 4]      
        if not year:
            if season:
                season = season.group(1) if season else None       
                file_name = file_name[:file_name.find(season) + 1]

        qualities = ["ORG", "org", "hdcam", "HDCAM", "HQ", "hq", "HDRip", "hdrip", 
                     "camrip", "WEB-DL", "CAMRip", "hdtc", "predvd", "DVDscr", "dvdscr", 
                     "dvdrip", "dvdscr", "HDTC", "dvdscreen", "HDTS", "hdts"]
        quality = await check_qualities(caption.lower(), qualities) or "HDRip"

        language = ""
        nb_languages = ["Hindi", "Bengali", "Bangla", "Hin", "Ban", "বাংলা", "हिन्दी", "Eng", "Tam", "English", 
                        "Marathi", "Tamil", "Telugu", "Malayalam", "Kannada", "Punjabi", "Gujrati", "Korean", 
                        "Japanese", "Bhojpuri", "Dual", "Multi"]
        for lang in nb_languages:
            if lang.lower() in caption.lower():
                language += f"{lang}, "
        language = language.strip(", ") or "Not Sure"

        movie_name = await movie_name_format(file_name)    
        if movie_name in processed_movies:
            return 
        processed_movies.add(movie_name)

        poster_url, title, genres, release_date, rating = await get_imdb(movie_name)
        @Client.on_message(filters.chat(CHANNELS) & media_filter)
async def media(bot, message):
    print("Received a new media message!")  # Debugging Message


        # যদি পোস্টার না থাকে, তাহলে ভিডিও থেকে থাম্বনেইল এক্সট্রাক্ট করো
        if not poster_url and video_path:
            poster_url = await extract_thumbnail(video_path)

        caption_message = (
            f"🎬 <b>Title:</b> <code>{title or movie_name}</code>\n"
            f"🗂 <b>Genres:</b> {genres or 'Unknown'}\n"
            f"📆 <b>Year:</b> {release_date or 'Unknown'}\n"
            f"⭐ <b>IMDb Rating:</b> {rating or 'N/A'} / 10\n\n"
            f"🔊 <b>Language:</b> {language}\n"
            f"💿 <b>Quality:</b> {quality}\n\n"
            f"📌 <b>𝗡𝗼𝘁𝗲:</b> 𝙄𝙛 𝙮𝙤𝙪 𝙣𝙚𝙚𝙙 𝙩𝙤 𝙜𝙚𝙩 𝙖𝙡𝙡 𝙦𝙪𝙖𝙡𝙞𝙩𝙮 𝙛𝙞𝙡𝙚𝙨, 𝙥𝙡𝙚𝙖𝙨𝙚 𝙘𝙤𝙥𝙮 𝙩𝙝𝙚 𝙖𝙗𝙤𝙫𝙚 𝙛𝙞𝙡𝙚 𝙣𝙖𝙢𝙚 𝙖𝙣𝙙 𝙥𝙖𝙨𝙩𝙚 𝙞𝙩 𝙞𝙣𝙩𝙤 𝙩𝙝𝙚 𝙗𝙚𝙡𝙤𝙬 𝙢𝙤𝙫𝙞𝙚 𝙨𝙚𝙖𝙧𝙘𝙝 𝙜𝙧𝙤𝙪𝙥 🔰.\n\n"
            f"🎥 <b>𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱 𝗟𝗶𝗻𝗸:</b> 𝘾𝙡𝙞𝙘𝙠 𝙩𝙝𝙚 𝙗𝙪𝙩𝙩𝙤𝙣 𝙗𝙚𝙡𝙤𝙬 𝙩𝙤 𝙜𝙚𝙩 𝙩𝙝𝙚 𝙛𝙞𝙡𝙚 🎥!"
        )

        movie_update_channel = await db.movies_update_channel_id()    

        btn = [
            [InlineKeyboardButton('🎥 𝗚𝗲𝘁 𝗙𝗶𝗹𝗲 🎥', url=f'https://telegram.me/{temp.U_NAME}?start=getfile-{file_id}')],
            [InlineKeyboardButton('💫Mᴏᴠɪᴇ Sᴇᴀʀᴄʜ Gʀᴏᴜᴘ💝', url='https://t.me/movierequestgroupHQ')]
        ]
        reply_markup = InlineKeyboardMarkup(btn)

        if poster_url:
            await bot.send_photo(movie_update_channel if movie_update_channel else MOVIE_UPDATE_CHANNEL, 
                                 photo=poster_url, caption=caption_message, reply_markup=reply_markup)
        else:
            no_poster = "https://telegra.ph/file/88d845b4f8a024a71465d.jpg"
            await bot.send_photo(movie_update_channel if movie_update_channel else MOVIE_UPDATE_CHANNEL, 
                                 photo=no_poster, caption=caption_message, reply_markup=reply_markup)  

    except Exception as e:
        print('Failed to send movie update. Error - ', e)
        await bot.send_message(LOG_CHANNEL, f'Failed to send movie update. Error - {e}')
