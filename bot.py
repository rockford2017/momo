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
IS_LOOP_ON = False
IS_CLOCK_ON = True
IS_PV_GUARD_ON = True

TARGET_CHAT = None
INTERVAL_SECONDS = 300
MESSAGE_TEXT = ""

# ----------------- BACKGROUND TASKS -----------------

async def clock_task():
    """ساعت پویا روی بیوگرافی"""
    while True:
        if IS_CLOCK_ON:
            now = datetime.now().strftime("%H:%M")
            try:
                await app.update_profile(bio=f"⏰ {now} | Selfbot Active")
            except Exception:
                pass
        await asyncio.sleep(60)

async def auto_loop_task():
    """ارسال لوپ هوشمند پیام تکراری"""
    global IS_LOOP_ON
    while True:
        if IS_LOOP_ON and TARGET_CHAT and MESSAGE_TEXT:
            try:
                # ۱. شبیه‌سازی تایپینگ انسان
                await app.send_chat_action(TARGET_CHAT, "typing")
                await asyncio.sleep(3)
                
                # ۲. ارسال پیام اصلی
                sent_msg = await app.send_message(TARGET_CHAT, MESSAGE_TEXT)
                
                # ۳. پاک‌سازی خودکار ردپا پس از ۲ دقیقه
                asyncio.create_task(delete_trace(sent_msg, 120))
            except Exception as e:
                print(f"Error in loop: {e}")

            # ۴. محاسبه زمان انتظار (تایم اصلی + تاخیر تصادفی ضد اسپم)
            random_delay = random.randint(10, 60)
            total_delay = INTERVAL_SECONDS + random_delay
            await asyncio.sleep(total_delay)
        else:
            await asyncio.sleep(5)

async def delete_trace(message, delay_seconds):
    await asyncio.sleep(delay_seconds)
    try:
        await message.delete()
    except Exception:
        pass

# ----------------- COMMAND HANDLERS -----------------

@app.on_message(filters.me & filters.command("loop", prefixes="."))
async def start_loop(client, message):
    """
    فرمت دستور:
    .loop [زمان به ثانیه] [آیدی یا یوزرنام گروه] [متن پیام]
    مثال:
    .loop 300 @mygroup سلام این پیام تکراری بازی است
    """
    global IS_LOOP_ON, INTERVAL_SECONDS, TARGET_CHAT, MESSAGE_TEXT
    
    args = message.text.split(maxsplit=3)
    
    if len(args) < 4:
        await message.reply_text(
            "❌ **فرمت دستور اشتباه است!**\n\n"
            "👈 **شکل صحیح:**\n"
            "`.loop [زمان به ثانیه] [آیدی/یوزرنام گروه] [متن پیام]`\n\n"
            "مثال:\n"
            "`.loop 300 @mygroup سلام بازی`"
        )
        return

    try:
        time_sec = int(args[1])
        chat_id = int(args[2]) if args[2].lstrip('-').isdigit() else args[2]
        text_to_send = args[3]

        INTERVAL_SECONDS = time_sec
        TARGET_CHAT = chat_id
        MESSAGE_TEXT = text_to_send
        IS_LOOP_ON = True

        await message.reply_text(
            f"✅ **ارسال لوپ با موفقیت فعال شد!**\n\n"
            f"⏱ **زمان‌بندی پایه:** `{INTERVAL_SECONDS}` ثانیه (+تایم تصادفی)\n"
            f"🎯 **گروه هدف:** `{TARGET_CHAT}`\n"
            f"📝 **متن پیام:** `{MESSAGE_TEXT}`"
        )
    except Exception as e:
        await message.reply_text(f"❌ خطا در پردازش دستور: {e}")

@app.on_message(filters.me & filters.command("stoploop", prefixes="."))
async def stop_loop(client, message):
    global IS_LOOP_ON
    IS_LOOP_ON = False
    await message.reply_text("🛑 **ارسال لوپ تکراری خاموش شد.**")

@app.on_message(filters.me & filters.command("panel", prefixes="."))
async def show_status(client, message):
    st_loop = "🟢 روشن" if IS_LOOP_ON else "🔴 خاموش"
    st_clock = "🟢 روشن" if IS_CLOCK_ON else "🔴 خاموش"
    st_guard = "🟢 روشن" if IS_PV_GUARD_ON else "🔴 خاموش"

    await message.reply_text(
        f"👑 **وضعیت سلف‌بات مشتی** 👑\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔄 **وضعیت لوپ ارسال:** {st_loop}\n"
        f"⏱ **زمان پایه:** `{INTERVAL_SECONDS}` ثانیه\n"
        f"🎯 **گروه هدف:** `{TARGET_CHAT if TARGET_CHAT else 'تنظیم نشده'}`\n"
        f"📝 **متن لوپ:** `{MESSAGE_TEXT if MESSAGE_TEXT else 'تنظیم نشده'}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏰ **ساعت بیو:** {st_clock}\n"
        f"🛡 **دزدگیر پی‌وی:** {st_guard}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 **راهنمای سریع:**\n"
        f"▫️ `.loop 300 @chat text` ➔ شروع لوپ\n"
        f"▫️ `.stoploop` ➔ توقف لوپ\n"
        f"▫️ `.clock on/off` ➔ ساعت بیو\n"
        f"▫️ `.guard on/off` ➔ دزدگیر پی‌وی"
    )

@app.on_message(filters.me & filters.command("clock", prefixes="."))
async def toggle_clock(client, message):
    global IS_CLOCK_ON
    cmd = message.text.split()
    IS_CLOCK_ON = True if (len(cmd) > 1 and cmd[1] == "on") else False
    await message.reply_text(f"⏰ ساعت بیو: {'🟢 روشن' if IS_CLOCK_ON else '🔴 خاموش'}")

@app.on_message(filters.me & filters.command("guard", prefixes="."))
async def toggle_guard(client, message):
    global IS_PV_GUARD_ON
    cmd = message.text.split()
    IS_PV_GUARD_ON = True if (len(cmd) > 1 and cmd[1] == "on") else False
    await message.reply_text(f"🛡 دزدگیر پی‌وی: {'🟢 روشن' if IS_PV_GUARD_ON else '🔴 خاموش'}")

# ----------------- OTHER FEATURES -----------------

@app.on_message(filters.private & ~filters.me & ~filters.bot)
async def pv_guard_handler(client, message):
    if IS_PV_GUARD_ON:
        await message.reply_text("⚠️ **پیام شما دریافت شد.** لطفاً از ارسال پیام‌های متوالی خودداری کنید.")

@app.on_message(filters.private & ~filters.me)
async def self_destruct_saver(client, message):
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
    asyncio.create_task(auto_loop_task())
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
