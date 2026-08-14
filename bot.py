import asyncio
import random
import os
from datetime import datetime
from pyrogram import Client, filters

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

# ----------------- FULL CONTROL PANEL -----------------

@app.on_message(filters.me & filters.command("panel", prefixes="."))
async def open_panel(client, message):
    """پنل مدیریت کامل و شیک سلف‌بات"""
    st_self = "🟢 روشن" if IS_SELF_ON else "🔴 خاموش"
    st_clock = "🟢 روشن" if IS_CLOCK_ON else "🔴 خاموش"
    st_guard = "🟢 روشن" if IS_PV_GUARD_ON else "🔴 خاموش"
    st_clean = "🟢 روشن" if IS_AUTO_CLEAN_ON else "🔴 خاموش"
    st_mode = "🎲 تصادفی (ضد اسپم)" if USE_RANDOM_DELAY else "⏱ دقیق (ثانیه‌ای)"
    target_info = TARGET_CHAT_ID if TARGET_CHAT_ID else "تنظیم نشده"

    panel_text = (
        f"👑 **پنل مدیریت سلف‌بات مشتی** 👑\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 **وضعیت سیستم:**\n"
        f"├ 🤖 **سلف‌بات:** {st_self}\n"
        f"├ ⏰ **ساعت بیو:** {st_clock}\n"
        f"├ 🛡 **دزدگیر پی‌وی:** {st_guard}\n"
        f"├ 🧹 **حذف ردپا:** {st_clean}\n"
        f"├ 🔀 **حالت ارسال:** {st_mode}\n"
        f"├ ⏱ **زمان ارسال:** `{INTERVAL_SECONDS}` ثانیه\n"
        f"├ 🎯 **گروه هدف:** `{target_info}`\n"
        f"└ 📝 **متن ارسال:** `{MESSAGE_TEXT}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🛠 **دستورات سریع تغییر تنظیمات:**\n\n"
        f"▫️ `.self on` / `.self off` ➔ روشن/خاموش سلف‌بات\n"
        f"▫️ `.clock on` / `.clock off` ➔ روشن/خاموش ساعت بیو\n"
        f"▫️ `.guard on` / `.guard off` ➔ روشن/خاموش دزدگیر پی‌وی\n"
        f"▫️ `.clean on` / `.clean off` ➔ روشن/خاموش حذف ردپا\n"
        f"▫️ `.mode random` / `.mode exact` ➔ تغییر حالت زمان ارسال\n"
        f"▫️ `.settext متن جدید` ➔ تغییر متن پیام ارسال\n"
        f"▫️ `.settime 300` ➔ تغییر زمان ارسال (به ثانیه)\n"
        f"▫️ `.setchat id` ➔ تنظیم گروه هدف\n"
        f"▫️ `.tags` ➔ مشاهده لیست تگ‌ها\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    await message.reply_text(panel_text)

# ----------------- COMMAND HANDLERS -----------------

@app.on_message(filters.me & filters.command("self", prefixes="."))
async def toggle_self(client, message):
    global IS_SELF_ON
    cmd = message.text.split()
    if len(cmd) > 1 and cmd[1] == "off":
        IS_SELF_ON = False
        await message.reply_text("🔴 **سلف‌بات خاموش شد.**")
    else:
        IS_SELF_ON = True
        await message.reply_text("🟢 **سلف‌بات روشن شد.**")

@app.on_message(filters.me & filters.command("clock", prefixes="."))
async def toggle_clock(client, message):
    global IS_CLOCK_ON
    cmd = message.text.split()
    if len(cmd) > 1 and cmd[1] == "off":
        IS_CLOCK_ON = False
        await message.reply_text("🔴 **ساعت بیو خاموش شد.**")
    else:
        IS_CLOCK_ON = True
        await message.reply_text("🟢 **ساعت بیو روشن شد.**")

@app.on_message(filters.me & filters.command("guard", prefixes="."))
async def toggle_guard(client, message):
    global IS_PV_GUARD_ON
    cmd = message.text.split()
    if len(cmd) > 1 and cmd[1] == "off":
        IS_PV_GUARD_ON = False
        await message.reply_text("🔴 **دزدگیر پی‌وی خاموش شد.**")
    else:
        IS_PV_GUARD_ON = True
        await message.reply_text("🟢 **دزدگیر پی‌وی روشن شد.**")

@app.on_message(filters.me & filters.command("clean", prefixes="."))
async def toggle_clean(client, message):
    global IS_AUTO_CLEAN_ON
    cmd = message.text.split()
    if len(cmd) > 1 and cmd[1] == "off":
        IS_AUTO_CLEAN_ON = False
        await message.reply_text("🔴 **حذف ردپا خاموش شد.**")
    else:
        IS_AUTO_CLEAN_ON = True
        await message.reply_text("🟢 **حذف ردپا روشن شد.**")

@app.on_message(filters.me & filters.command("mode", prefixes="."))
async def toggle_mode(client, message):
    global USE_RANDOM_DELAY
    cmd = message.text.split()
    if len(cmd) > 1 and cmd[1] == "exact":
        USE_RANDOM_DELAY = False
        await message.reply_text("⏱ **حالت ارسال روی زمان دقیق تنظیم شد.**")
    else:
        USE_RANDOM_DELAY = True
        await message.reply_text("🎲 **حالت ارسال روی زمان تصادفی (ضد اسپم) تنظیم شد.**")

@app.on_message(filters.me & filters.command("settext", prefixes="."))
async def set_text_cmd(client, message):
    global MESSAGE_TEXT
    new_text = message.text.replace(".settext", "").strip()
    if new_text:
        MESSAGE_TEXT = new_text
        await message.reply_text(f"✅ **متن جدید تنظیم شد:**\n`{MESSAGE_TEXT}`")
    else:
        await message.reply_text("❌ لطفاً متن جدید را بعد از دستور بنویس.\nمثال: `.settext سلام بازی` ")

@app.on_message(filters.me & filters.command("settime", prefixes="."))
async def set_time_cmd(client, message):
    global INTERVAL_SECONDS
    cmd = message.text.split()
    if len(cmd) > 1 and cmd[1].isdigit():
        INTERVAL_SECONDS = int(cmd[1])
        await message.reply_text(f"✅ **زمان ارسال روی {INTERVAL_SECONDS} ثانیه تنظیم شد.**")
    else:
        await message.reply_text("❌ لطفاً عدد ثانیه را وارد کن.\nمثال: `.settime 300` ")

@app.on_message(filters.me & filters.command("setchat", prefixes="."))
async def set_chat_cmd(client, message):
    global TARGET_CHAT_ID
    cmd = message.text.split()
    if len(cmd) > 1:
        chat_val = cmd[1]
        TARGET_CHAT_ID = int(chat_val) if chat_val.lstrip('-').isdigit() else chat_val
        await message.reply_text(f"✅ **گروه هدف تنظیم شد روی:** `{TARGET_CHAT_ID}`")
    else:
        await message.reply_text("❌ لطفاً آیدی یا یوزرنام گروه را وارد کن.\nمثال: `.setchat -1001234567` ")

# ----------------- ADVANCED FEATURES -----------------

@app.on_message(filters.me & filters.command("tags", prefixes="."))
async def get_tags(client, message):
    """مشاهده تگ‌ها"""
    text = "📌 **لیست تگ‌ها و یادداشت‌ها:**\n\n"
    for tag, val in TAGS_DB.items():
        text += f"• `#{tag}` ➔ {val}\n"
    await message.reply_text(text)

@app.on_message(filters.private & ~filters.me & ~filters.bot)
async def pv_guard_handler(client, message):
    """دزدگیر پی‌وی"""
    if IS_PV_GUARD_ON:
        await message.reply_text("⚠️ **پیام شما دریافت شد.** لطفاً از ارسال پیام‌های متوالی خودداری کنید.")

@app.on_message(filters.private & ~filters.me)
async def self_destruct_saver(client, message):
    """ذخیره‌ساز عکس/ویس یک‌بارمصرف در Saved Messages"""
    if message.ttl_seconds:
        try:
            file_path = await message.download()
            await app.send_document("me", document=file_path, caption=f"📥 **رسانه یک‌بارمصرف ذخیره شد از طرف:** {message.from_user.mention}")
            if os.path.exists(file_path):
                os.remove(file_path)
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
