import asyncio
import os
import subprocess
from telethon import TelegramClient
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import InputAudioStream
from pytgcalls.exceptions import GroupCallNotFoundError
import logging

# إعدادات الحساب المساعد (Userbot)
API_ID = 21713649  # غيّر إلى api_id الخاص بك
API_HASH = "6185e0990184774e94306290fdaa589a"  # غيّر إلى api_hash الخاص بك
SESSION_NAME = "userbot_session"

# إعدادات السجل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# تهيئة الحساب المساعد
userbot = TelegramClient(SESSION_NAME, API_ID, API_HASH)
pytgcalls = PyTgCalls(userbot)
queue = {}

# ======= وظائف البوت =======

async def start_handler(update):
    buttons = [
        ["تشغيل أغنية", "إيقاف", "تخطي"],
        ["عرض احصائيات البوت", "المطور", "لتنصيب بوت"],
        ["تحديث السورس"]  # زر لتحديث السورس للمطور
    ]
    await update.reply("أهلاً بك في بوت تشغيل الموسيقى!", buttons)

async def play_command(update):
    query = update.text.split(" ", 1)[1]
    chat_id = update.chat.id
    filename = f"{query}.mp3"

    await update.reply(f"جاري تحميل: {query}")
    try:
        subprocess.run(["yt-dlp", "-x", "--audio-format", "mp3", "-o", filename, f"ytsearch1:{query}"], check=True)
    except Exception as e:
        await update.reply(f"خطأ في تحميل الأغنية: {e}")
        logging.error(f"خطأ في تحميل الأغنية: {e}")
        return

    if os.path.exists(filename):
        if chat_id not in queue:
            queue[chat_id] = []
        queue[chat_id].append(filename)
        await update.reply("تمت إضافة الأغنية، وسيتم التشغيل.")

        try:
            # دعوة الحساب المساعد إلى المكالمة الجماعية وتشغيل الأغنية
            await pytgcalls.join_group_call(
                chat_id,
                InputAudioStream(file_path=filename)
            )
        except GroupCallNotFoundError:
            await update.reply("يرجى بدء محادثة صوتية في المجموعة أولاً.")
        except Exception as e:
            await update.reply(f"خطأ في التشغيل: {e}")
            logging.error(f"خطأ في تشغيل الأغنية في المجموعة {chat_id}: {e}")
    else:
        await update.reply("فشل العثور على الملف.")
        logging.error("فشل العثور على الملف.")

async def stop_command(update):
    chat_id = update.chat.id
    try:
        await pytgcalls.leave_group_call(chat_id)
        queue.pop(chat_id, None)
        await update.reply("تم إيقاف التشغيل.")
    except Exception as e:
        await update.reply(f"خطأ: {e}")
        logging.error(f"خطأ في إيقاف التشغيل: {e}")

async def skip_command(update):
    chat_id = update.chat.id
    if chat_id in queue and queue[chat_id]:
        queue[chat_id].pop(0)
        if queue[chat_id]:
            next_song = queue[chat_id][0]
            await pytgcalls.change_stream(
                chat_id,
                InputAudioStream(file_path=next_song)
            )
            await update.reply("تم تشغيل الأغنية التالية.")
        else:
            await pytgcalls.leave_group_call(chat_id)
            await update.reply("لا توجد أغانٍ أخرى.")
    else:
        await update.reply("قائمة التشغيل فارغة.")

async def update_source(update):
    await update.reply("جاري تحديث السورس...")
    try:
        subprocess.run(["git", "pull"], check=True)
        await update.reply("تم تحديث السورس بنجاح!")
    except Exception as e:
        await update.reply(f"حدث خطأ أثناء تحديث السورس: {e}")
        logging.error(f"خطأ أثناء تحديث السورس: {e}")

# ======= إعداد المساعد =======
async def main():
    # اتصال الحساب المساعد
    await userbot.start()

    # استخدام Python asyncio أو أي مكتبة للدردشة مع المستخدمين

    print("تم الاتصال بنجاح.")

if __name__ == "__main__":
    asyncio.run(main())