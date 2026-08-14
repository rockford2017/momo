import asyncio
import random
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ---------------- CONFIGURATIONS ----------------
# تمام تنظیمات از طریق Secrets گیت‌هاب خوانده می‌شوند تا سشن نسوزد
import os

API_ID = int(os.environ.get("API_ID", 123456))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING", "")

app = Client("selfbot_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# Global State Variables (قابلیت تغییر از داخل تلگرام)
IS_SELF_ON = True
IS_CLOCK_ON = True
IS_PV_GUARD_ON = True
IS_AUTO_CLEAN_ON = True

TARGET_CHAT_ID = None  # آیدی گروه بازی
MESSAGE_TEXT = "پیام پیش‌فرض بازی"
INTERVAL_SECONDS = 300  # زمان‌بندی دستی (مثلاً ۳۰۰ ثانیه)
USE_RANDOM_DELAY = True  # حالت تصادفی ضد اسپم (۴ تا ۷ دقیقه)

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
                
                # پاک‌سازی خودکار ردپای پیام از گروه در صورت فعال بودن
                if IS_AUTO_CLEAN_ON:
                    asyncio.create_task(delete_trace(sent_msg, 120))
            except Exception as e:
                print(f"Error in auto sender: {e}")

            # محاسبه زمان انتظار (دقیق یا تصادفی)
            delay = INTERVAL_SECONDS
            if USE_RANDOM_DELAY:
                delay += random.randint(10, 90)  # تأخیر تصادفی بین ۱۰ تا ۹۰ ثانیه
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

@app.on_message(filters.me & filters.command("panel", prefixes="."))
async def open_panel(client, message):
    """باز کردن منوی تنظیمات گرافیکی با دستور .panel"""
    await message.reply_text("⚙️ **پنل مدیریت سلف‌بات مشتی**", reply_markup=build_menu())

def build_menu():
    status_self = "✅ روشن" if IS_SELF_ON else "❌ خاموش"
    status_clock = "✅ روشن" if IS_CLOCK_ON else "❌ خاموش"
    status_guard = "✅ روشن" if IS_PV_GUARD_ON else "❌ خاموش"
    status_clean = "✅ روشن" if IS_AUTO_CLEAN_ON else "❌ خاموش"
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"سلف‌بات: {status_self}", callback_data="toggle_self")],
        [InlineKeyboardButton(f"ساعت بیو: {status_clock}", callback_data="toggle_clock")],
        [InlineKeyboardButton(f"دزدگیر پی‌وی: {status_guard}", callback_data="toggle_guard")],
        [InlineKeyboardButton(f"پاک‌سازی ردپا: {status_clean}", callback_data="toggle_clean")],
        [InlineKeyboardButton("🏷 تگ‌ها و یادداشت‌ها", callback_data="show_tags")],
        [InlineKeyboardButton("❌ بستن منو", callback_data="close_menu")]
    ])

@app.on_callback_query()
async def menu_callback(client, callback_query):
    global IS_SELF_ON, IS_CLOCK_ON, IS_PV_GUARD_ON, IS_AUTO_CLEAN_ON
    data = callback_query.data
    
    if data == "toggle_self":
        IS_SELF_ON = not IS_SELF_ON
    elif data == "toggle_clock":
        IS_CLOCK_ON = not IS_CLOCK_ON
    elif data == "toggle_guard":
        IS_PV_GUARD_ON = not IS_PV_GUARD_ON
    elif data == "toggle_clean":
        IS_AUTO_CLEAN_ON = not IS_AUTO_CLEAN_ON
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

    await callback_query.message.edit_text("⚙️ **پنل مدیریت سلف‌بات مشتی**", reply_markup=build_menu())

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
        # ارسال هشدار هوشمند به فرستنده
        await message.reply_text("⚠️ **پیام شما دریافت شد.** لطفا از ارسال پیام‌های متوالی و اسپم خودداری کنید.")

@app.on_message(filters.private & (filters.photo | filters.video | filters.voice))
async def self_destruct_saver(client, message):
    """ذخیره‌ساز عکس/ویس/ویدیوی یک‌بارمصرف (تایمردار) در Saved Messages"""
    if message.ttl_seconds:  # اگر رسانه یک‌بارمصرف باشد
        await message.download(file_name="ttl_media/")
        await app.send_message("me", f"📥 **رسانه یک‌بارمصرف ذخیره شد از طرف:** {message.from_user.mention}")

# ----------------- STARTUP -----------------
async def main():
    await app.start()
    print("Selfbot is Running...")
    asyncio.create_task(clock_task())
    asyncio.create_task(auto_sender_task())
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
