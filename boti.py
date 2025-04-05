import asyncio
import os
import subprocess
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telethon import TelegramClient
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import InputAudioStream, InputStream
from pytgcalls.exceptions import GroupCallNotFoundError
import logging

# إعدادات البوت الرسمي
BOT_TOKEN = "7520474372:AAHKww9Ua1Vol7Ib1lyKTDiXacTfpMFwS2Q"
DEVELOPER_USERNAME = "@eee_98"
ADMIN_USER_ID = 1388984721  # غيّر إلى معرف المستخدم (ID) الخاص بك فقط

# إعدادات الحساب المساعد (Userbot)
API_ID = 21713649  # غيّر إلى api_id الخاص بك
API_HASH = "6185e0990184774e94306290fdaa589a"  # غيّر إلى api_hash الخاص بك
SESSION_NAME = "userbot_session"

# إعدادات السجل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# تهيئة البوت
bot = Bot(token=BOT_TOKEN)

# تهيئة الحساب المساعد
userbot = TelegramClient(SESSION_NAME, API_ID, API_HASH)
pytgcalls = PyTgCalls(userbot)
queue = {}

# ======= وظائف البوت =======

def start_handler(update, context):
    buttons = [
        ["تشغيل أغنية", "إيقاف", "تخطي"],
        ["عرض احصائيات البوت", "المطور", "لتنصيب بوت"],
        ["تحديث السورس"]  # زر لتحديث السورس للمطور
    ]
    update.message.reply_text("أهلاً بك في بوت تشغيل الموسيقى!", reply_markup=buttons)

def play_command(update, context):
    query = update.message.text.split(" ", 1)[1]
    chat_id = update.message.chat.id
    filename = f"{query}.mp3"

    update.message.reply_text(f"جاري تحميل: {query}")
    try:
        subprocess.run(["yt-dlp", "-x", "--audio-format", "mp3", "-o", filename, f"ytsearch1:{query}"], check=True)
    except Exception as e:
        update.message.reply_text(f"خطأ في تحميل الأغنية: {e}")
        logging.error(f"خطأ في تحميل الأغنية: {e}")
        return

    if os.path.exists(filename):
        if chat_id not in queue:
            queue[chat_id] = []
        queue[chat_id].append(filename)
        update.message.reply_text("تمت إضافة الأغنية، وسيتم التشغيل.")

        try:
            # دعوة الحساب المساعد إلى المكالمة الجماعية وتشغيل الأغنية
            pytgcalls.join_group_call(
                chat_id,
                InputStream(InputAudioStream(file_path=filename))
            )
        except GroupCallNotFoundError:
            update.message.reply_text("يرجى بدء محادثة صوتية في المجموعة أولاً.")
        except Exception as e:
            update.message.reply_text(f"خطأ في التشغيل: {e}")
            logging.error(f"خطأ في تشغيل الأغنية في المجموعة {chat_id}: {e}")
    else:
        update.message.reply_text("فشل العثور على الملف.")
        logging.error("فشل العثور على الملف.")

def stop_command(update, context):
    chat_id = update.message.chat.id
    try:
        pytgcalls.leave_group_call(chat_id)
        queue.pop(chat_id, None)
        update.message.reply_text("تم إيقاف التشغيل.")
    except Exception as e:
        update.message.reply_text(f"خطأ: {e}")
        logging.error(f"خطأ في إيقاف التشغيل: {e}")

def skip_command(update, context):
    chat_id = update.message.chat.id
    if chat_id in queue and queue[chat_id]:
        queue[chat_id].pop(0)
        if queue[chat_id]:
            next_song = queue[chat_id][0]
            pytgcalls.change_stream(
                chat_id,
                InputStream(InputAudioStream(file_path=next_song))
            )
            update.message.reply_text("تم تشغيل الأغنية التالية.")
        else:
            pytgcalls.leave_group_call(chat_id)
            update.message.reply_text("لا توجد أغانٍ أخرى.")
    else:
        update.message.reply_text("قائمة التشغيل فارغة.")

def stats_command(update, context):
    if update.message.from_user.id != ADMIN_USER_ID:
        update.message.reply_text("أنت لست المسؤول، لا يمكنك الوصول إلى الإحصائيات.")
        return

    members = bot.get_chat_members_count(update.message.chat.id)
    update.message.reply_text(f"عدد المشتركين: {members}")

def dev_command(update, context):
    if update.message.from_user.id != ADMIN_USER_ID:
        update.message.reply_text("أنت لست المسؤول، لا يمكنك الوصول إلى معلومات المطور.")
        return
    
    update.message.reply_text(f"المطور: {DEVELOPER_USERNAME}")

def install_command(update, context):
    update.message.reply_text("للتنصيب والتواصل مع المطور: @eee_98")

# ======= دالة لتحديث السورس (للمطور فقط) =======
def update_source(update, context):
    if update.message.from_user.id != ADMIN_USER_ID:
        update.message.reply_text("أنت لست المسؤول، لا يمكنك تحديث السورس.")
        return

    update.message.reply_text("جاري تحديث السورس...")
    try:
        subprocess.run(["git", "pull"], check=True)
        update.message.reply_text("تم تحديث السورس بنجاح!")
    except Exception as e:
        update.message.reply_text(f"حدث خطأ أثناء تحديث السورس: {e}")
        logging.error(f"خطأ أثناء تحديث السورس: {e}")

# ======= دالة للدعوة التلقائية عند إعطاء الإشراف =======
async def invite_userbot_to_call(chat_id):
    try:
        await pytgcalls.join_group_call(
            chat_id,
            InputStream(InputAudioStream(file_path="default.mp3"))  # في حالة كانت الأغنية غير موجودة، يقوم بتشغيل أغنية افتراضية.
        )
        print(f"تم دعوة الحساب المساعد إلى المكالمة في المجموعة {chat_id}")
    except Exception as e:
        print(f"خطأ في دعوة الحساب المساعد: {e}")
        logging.error(f"خطأ في دعوة الحساب المساعد: {e}")

# ======= إعداد المساعد =======
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start_handler))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r"^تشغيل .*"), play_command))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r"^إيقاف$"), stop_command))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r"^تخطي$"), skip_command))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r"^عرض احصائيات البوت$"), stats_command))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r"^المطور$"), dev_command))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r"^لتنصيب بوت$"), install_command))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r"^تحديث السورس$"), update_source))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()