import asyncio
import random
import os
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ---------------- CONFIGURATIONS ----------------
API_ID = int(os.environ.get("API_ID", 123456))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING", "")

app = Client("selfbot_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# ---------------- STATE VARIABLES ----------------
IS_SELF_ON = True
IS_CLOCK_ON = True
IS_PV_GUARD_ON = True
IS_AUTO_CLEAN_ON = True

TARGET_CHAT_ID = None  # آیدی یا یوزرنام گروه هدف
MESSAGE_TEXT = "پیام پیش‌فرض بازی سلف‌بات"
INTERVAL_SECONDS = 300  # زمان‌بندی دستی (به ثانیه)
USE_RANDOM_DELAY = True  # حالت تصادفی ضد اسپم

# حالت منتظر دریافت ورودی از کاربر (برای تنظیمات)
WAITING_FOR = None  # 'text', 'time', 'chat'

TAGS_DB = {
    "game": "دستورات و آمار مربوط به بازی",
    "notes": "یادداشت‌ها و متون مهم شخصی"
}

# ----------------- BACKGROUND TASKS -----------------

async def clock_task():
    """ساعت پویا روی بیوگرافی (قابل خاموش/روشن)"""
    while True:
        if IS_CLOCK_ON:
            now = datetime.now().strftime("%H:%M")
            try:
                await app.update_profile(bio=f"⏰ {now} | Selfbot Active")
            except Exception:
                pass
        await asyncio.sleep(60)

async def auto_sender_task():
    """ارسال هوشمند زمان‌بندی‌شده با شبیه‌سازی رفتار انسان"""
    while True:
        if IS_SELF_ON and TARGET_CHAT_ID:
            try:
                # شبیه‌سازی تایپینگ قبل از ارسال
                await app.send_chat_action(TARGET_CHAT_ID, "typing")
                await asyncio.sleep(3)
                
                # ارسال پیام اصلی
                sent_msg = await app.send_message(TARGET_CHAT_ID, MESSAGE_TEXT)
                
                # پاک‌سازی خودکار ردپای پیام از گروه
                if IS_AUTO_CLEAN_ON:
                    asyncio.create_task(delete_trace(sent_msg, 120))
            except Exception as e:
                print(f"Error in auto sender: {e}")

            # محاسبه زمان انتظار (دقیق با ثانیه یا تصادفی)
            delay = INTERVAL_SECONDS
            if USE_RANDOM_DELAY:
                delay += random.randint(10, 90)  # افزودن تایم تصادفی ضد اسپم
            await asyncio.sleep(delay)
        else:
            await asyncio.sleep(10)

async def delete_trace(message, delay_seconds):
    """حذف پیام پس از مدت مشخص"""
    await asyncio.sleep(delay_seconds)
    try:
        await message.delete()
    except Exception:
        pass

# ----------------- INLINE MENU & CONTROL PANEL -----------------

def build_menu():
    status_self = "✅ روشن" if IS_SELF_ON else "❌ خاموش"
    status_clock = "✅ روشن" if IS_CLOCK_ON else "❌ خاموش"
    status_guard = "✅ روشن" if IS_PV_GUARD_ON else "❌ خاموش"
    status_clean = "✅ روشن" if IS_AUTO_CLEAN_ON else "❌ خاموش"
    status_mode = "🎲 تصادفی" if USE_RANDOM_DELAY else "⏱ دقیق (ثانیه‌ای)"
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"سلف‌بات: {status_self}", callback_data="toggle_self"), InlineKeyboardButton(f"ساعت بیو: {status_clock}", callback_data="toggle_clock")],
        [InlineKeyboardButton(f"دزدگیر پی‌وی: {status_guard}", callback_data="toggle_guard"), InlineKeyboardButton(f"حذف ردپا: {status_clean}", callback_data="toggle_clean")],
        [InlineKeyboardButton(f"حالت ارسال: {status_mode}", callback_data="toggle_mode")],
        [InlineKeyboardButton("✏️ تنظیم متن پیام", callback_data="set_text"), InlineKeyboardButton("⏱ تنظیم زمان (ثانیه)", callback_data="set_time")],
        [InlineKeyboardButton("🎯 تنظیم گروه هدف", callback_data="set_chat")],
        [InlineKeyboardButton("🏷 تگ‌ها و یادداشت‌ها", callback_data="show_tags")],
        [InlineKeyboardButton("❌ بستن منو", callback_data="close_menu")]
    ])

@app.on_message(filters.me & filters.command("panel", prefixes="."))
async def open_panel(client, message):
    """باز کردن منوی تنظیمات گرافیکی"""
    chat_info = TARGET_CHAT_ID if TARGET_CHAT_ID else "تنظیم نشده"
    info_text = (
        f"⚙️ **پنل مدیریت سلف‌بات مشتی**\n\n"
        f"📝 **متن فعلی:** `{MESSAGE_TEXT}`\n"
        f"⏱ **زمان ارسال:** `{INTERVAL_SECONDS}` ثانیه\n"
        f"🎯 **گروه هدف:** `{chat_info}`"
    )
    await message.reply_text(info_text, reply_markup=build_menu())

@app.on_callback_query()
async def menu_callback(client, callback_query):
    global IS_SELF_ON, IS_CLOCK_ON, IS_PV_GUARD_ON, IS_AUTO_CLEAN_ON, USE_RANDOM_DELAY, WAITING_FOR
    data = callback_query.data
    
    if data == "toggle_self":
        IS_SELF_ON = not IS_SELF_ON
    elif data == "toggle_clock":
        IS_CLOCK_ON = not IS_CLOCK_ON
    elif data == "toggle_guard":
        IS_PV_GUARD_ON = not IS_PV_GUARD_ON
    elif data == "toggle_clean":
        IS_AUTO_CLEAN_ON = not IS_AUTO_CLEAN_ON
    elif data == "toggle_mode":
        USE_RANDOM_DELAY = not USE_RANDOM_DELAY
    elif data == "set_text":
        WAITING_FOR = "text"
        await callback_query.message.edit_text("✏️ **لطفاً متن جدیدی که می‌خواهی ارسال شود را بفرست:**")
        return
    elif data == "set_time":
        WAITING_FOR = "time"
        await callback_query.message.edit_text("⏱ **لطفاً زمان ارسال را به ثانیه فرست (مثلاً 300):**")
        return
    elif data == "set_chat":
        WAITING_FOR = "chat"
        await callback_query.message.edit_text("🎯 **آیدی یا یوزرنام گروه هدف را بفرست (مثلاً 12345678- یا mygroup@):**")
        return
    elif data == "show_tags":
        text = "📌 **فهرست تگ‌های ثبت‌شده:**\n\n"
        for tag, content in TAGS_DB.items():
            text += f"#️⃣ `#{tag}` ➔ {content}\n"
        await callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="refresh_menu")]]))
        return
    elif data == "refresh_menu":
        pass
    elif data == "close_menu":
        await callback_query.message.delete()
        return

    chat_info = TARGET_CHAT_ID if TARGET_CHAT_ID else "تنظیم نشده"
    info_text = (
        f"⚙️ **پنل مدیریت سلف‌بات مشتی**\n\n"
        f"📝 **متن فعلی:** `{MESSAGE_TEXT}`\n"
        f"⏱ **زمان ارسال:** `{INTERVAL_SECONDS}` ثانیه\n"
        f"🎯 **گروه هدف:** `{chat_info}`"
    )
    await callback_query.message.edit_text(info_text, reply_markup=build_menu())

# ----------------- INPUT HANDLER FOR MENU -----------------

@app.on_message(filters.me & ~filters.command(["panel", "tags"]))
async def input_listener(client, message):
    global WAITING_FOR, MESSAGE_TEXT, INTERVAL_SECONDS, TARGET_CHAT_ID
    
    if WAITING_FOR == "text":
        MESSAGE_TEXT = message.text
        WAITING_FOR = None
        await message.reply_text(f"✅ **متن جدید ذخیره شد:**\n`{MESSAGE_TEXT}`")
    elif WAITING_FOR == "time":
        if message.text.isdigit():
            INTERVAL_SECONDS = int(message.text)
            WAITING_FOR = None
            await message.reply_text(f"✅ **زمان ارسال روی {INTERVAL_SECONDS} ثانیه تنظیم شد.**")
        else:
            await message.reply_text("❌ لطفاً فقط عدد وارد کن!")
    elif WAITING_FOR == "chat":
        try:
            chat_input = int(message.text) if message.text.lstrip('-').isdigit() else message.text
            TARGET_CHAT_ID = chat_input
            WAITING_FOR = None
            await message.reply_text(f"✅ **گروه هدف تنظیم شد روی:** `{TARGET_CHAT_ID}`")
        except Exception as e:
            await message.reply_text(f"❌ خطا در تشخیص گروه: {e}")

# ----------------- ADVANCED FEATURES -----------------

@app.on_message(filters.me & filters.command("tags", prefixes="."))
async def get_tags(client, message):
    """مشاهده تگ‌ها در Saved Messages"""
    text = "📌 **لیست تگ‌ها و یادداشت‌ها:**\n\n"
    for tag, val in TAGS_DB.items():
        text += f"• `#{tag}` ➔ {val}\n"
    await message.reply_text(text)

@app.on_message(filters.private & ~filters.me & ~filters.bot)
async def pv_guard_handler(client, message):
    """دزدگیر پی‌وی برای اخطار به پیام‌های اسپم"""
    if IS_PV_GUARD_ON:
        await message.reply_text("⚠️ **پیام شما دریافت شد.** لطفاً از ارسال پیام‌های متوالی خودداری کنید.")

@app.on_message(filters.private & ~filters.me)
async def self_destruct_saver(client, message):
    """ذخیره‌ساز عکس/ویس/ویدیوی یک‌بارمصرف (تایمردار) مستقیم در Saved Messages"""
    if message.ttl_seconds:  # اگر رسانه یک‌بارمصرف باشد
        try:
            file_path = await message.download()
            await app.send_document("me", document=file_path, caption=f"📥 **رسانه یک‌بارمصرف ذخیره شد از طرف:** {message.from_user.mention}")
            if os.path.exists(file_path):
                os.remove(file_path)  # پاک کردن فایل دانلود شده روی سرور
        except Exception as e:
            print(f"Error saving TTL media: {e}")

# ----------------- STARTUP -----------------
async def main():
    await app.start()
    print("Selfbot is Running Successfully!")
    asyncio.create_task(clock_task())
    asyncio.create_task(auto_sender_task())
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
