import asyncio
import os
import subprocess
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
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
dp = Dispatcher(bot)

# تهيئة الحساب المساعد
userbot = TelegramClient(SESSION_NAME, API_ID, API_HASH)
pytgcalls = PyTgCalls(userbot)
queue = {}

# ======= وظائف البوت =======

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    buttons = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons.add("تشغيل أغنية", "إيقاف", "تخطي")
    buttons.add("عرض احصائيات البوت", "المطور", "لتنصيب بوت")
    buttons.add("تحديث السورس")  # زر لتحديث السورس للمطور
    await message.reply("أهلاً بك في بوت تشغيل الموسيقى!", reply_markup=buttons)

@dp.message_handler(lambda m: m.text.startswith("تشغيل ") or m.text.startswith("شغل "))
async def play_command(message: types.Message):
    query = message.text.split(" ", 1)[1]
    chat_id = message.chat.id
    filename = f"{query}.mp3"

    await message.reply(f"جاري تحميل: {query}")
    try:
        subprocess.run(["yt-dlp", "-x", "--audio-format", "mp3", "-o", filename, f"ytsearch1:{query}"], check=True)
    except Exception as e:
        await message.reply(f"خطأ في تحميل الأغنية: {e}")
        logging.error(f"خطأ في تحميل الأغنية: {e}")
        return

    if os.path.exists(filename):
        if chat_id not in queue:
            queue[chat_id] = []
        queue[chat_id].append(filename)
        await message.reply("تمت إضافة الأغنية، وسيتم التشغيل.")

        try:
            # دعوة الحساب المساعد إلى المكالمة الجماعية وتشغيل الأغنية
            await pytgcalls.join_group_call(
                chat_id,
                InputStream(InputAudioStream(file_path=filename))
            )
        except GroupCallNotFoundError:
            await message.reply("يرجى بدء محادثة صوتية في المجموعة أولاً.")
        except Exception as e:
            await message.reply(f"خطأ في التشغيل: {e}")
            logging.error(f"خطأ في تشغيل الأغنية في المجموعة {chat_id}: {e}")
    else:
        await message.reply("فشل العثور على الملف.")
        logging.error("فشل العثور على الملف.")

@dp.message_handler(lambda m: m.text.lower() == "إيقاف")
async def stop_command(message: types.Message):
    chat_id = message.chat.id
    try:
        await pytgcalls.leave_group_call(chat_id)
        queue.pop(chat_id, None)
        await message.reply("تم إيقاف التشغيل.")
    except Exception as e:
        await message.reply(f"خطأ: {e}")
        logging.error(f"خطأ في إيقاف التشغيل: {e}")

@dp.message_handler(lambda m: m.text.lower() == "تخطي")
async def skip_command(message: types.Message):
    chat_id = message.chat.id
    if chat_id in queue and queue[chat_id]:
        queue[chat_id].pop(0)
        if queue[chat_id]:
            next_song = queue[chat_id][0]
            await pytgcalls.change_stream(
                chat_id,
                InputStream(InputAudioStream(file_path=next_song))
            )
            await message.reply("تم تشغيل الأغنية التالية.")
        else:
            await pytgcalls.leave_group_call(chat_id)
            await message.reply("لا توجد أغانٍ أخرى.")
    else:
        await message.reply("قائمة التشغيل فارغة.")

@dp.message_handler(lambda m: m.text == "عرض احصائيات البوت")
async def stats_command(message: types.Message):
    if message.from_user.id != ADMIN_USER_ID:
        await message.reply("أنت لست المسؤول، لا يمكنك الوصول إلى الإحصائيات.")
        return

    members = await bot.get_chat_members_count(message.chat.id)
    await message.reply(f"عدد المشتركين: {members}")

@dp.message_handler(lambda m: m.text == "المطور")
async def dev_command(message: types.Message):
    if message.from_user.id != ADMIN_USER_ID:
        await message.reply("أنت لست المسؤول، لا يمكنك الوصول إلى معلومات المطور.")
        return
    
    await message.reply(f"المطور: {DEVELOPER_USERNAME}")

@dp.message_handler(lambda m: m.text == "لتنصيب بوت")
async def install_command(message: types.Message):
    await message.reply("للتنصيب والتواصل مع المطور: @eee_98")

# ======= دالة لتحديث السورس (للمطور فقط) =======
@dp.message_handler(lambda m: m.text == "تحديث السورس" and m.from_user.id == ADMIN_USER_ID)
async def update_source(message: types.Message):
    await message.reply("جاري تحديث السورس...")
    try:
        subprocess.run(["git", "pull"], check=True)
        await message.reply("تم تحديث السورس بنجاح!")
    except Exception as e:
        await message.reply(f"حدث خطأ أثناء تحديث السورس: {e}")
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

# ======= إدارة الأخطاء =======
async def handle_error(exception):
    logging.error(f"خطأ في البوت: {exception}")
    # يمكن إضافة آلية لتنبيه المطور عبر البريد الإلكتروني أو من خلال Telegram إذا حدث خطأ

# ======= التشغيل =======
async def start_all():
    await userbot.start()
    await pytgcalls.start()
    print("الحساب المساعد متصل")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_all())
    executor.start_polling(dp, skip_updates=True)