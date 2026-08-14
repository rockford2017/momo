import asyncio
import random
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ---------------- CONFIGS ----------------
API_ID = 123456  # Replace with your API_ID
API_HASH = "YOUR_API_HASH"  # Replace with your API_HASH

app = Client("my_selfbot", api_id=API_ID, api_hash=API_HASH)

# State Variables
IS_SELF_ON = True
IS_CLOCK_ON = True
TARGET_CHAT_ID = None
MESSAGE_TEXT = "پیام پیش‌فرض بازی"
INTERVAL_SECONDS = 300  # 5 minutes
USE_RANDOM_DELAY = True

TAGS_DB = {
    "game": "لیست دستورات مربوط به بازی",
    "info": "اطلاعات مهم اکانت و یادداشت‌ها"
}

# ----------------- HELPERS -----------------
async def clock_task():
    """Clock Task for Bio"""
    while True:
        if IS_CLOCK_ON:
            now = datetime.now().strftime("%H:%M")
            try:
                await app.update_profile(bio=f"⏰ Time: {now} | Online")
            except Exception:
                pass
        await asyncio.sleep(60)

async def auto_sender_task():
    """Auto Message Sender with Anti-Spam Strategy"""
    while True:
        if IS_SELF_ON and TARGET_CHAT_ID:
            try:
                # Simulate Typing
                await app.send_chat_action(TARGET_CHAT_ID, "typing")
                await asyncio.sleep(3)
                
                # Send Message
                sent_msg = await app.send_message(TARGET_CHAT_ID, MESSAGE_TEXT)
                
                # Auto Clean-Up Trace (Optional)
                # await asyncio.sleep(60)
                # await sent_msg.delete()
            except Exception as e:
                print(f"Error in sending message: {e}")

            # Interval Logic (Exact vs Random Delay)
            delay = INTERVAL_SECONDS
            if USE_RANDOM_DELAY:
                delay += random.randint(10, 60)
            await asyncio.sleep(delay)
        else:
            await asyncio.sleep(10)

# ----------------- COMMANDS & HANDLERS -----------------

@app.on_message(filters.me & filters.command("panel", prefixes="."))
async def open_panel(client, message):
    """Control Panel Menu"""
    status_self = "✅ روشن" if IS_SELF_ON else "❌ خاموش"
    status_clock = "✅ روشن" if IS_CLOCK_ON else "❌ خاموش"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"سلف‌بات: {status_self}", callback_data="toggle_self")],
        [InlineKeyboardButton(f"ساعت بیو: {status_clock}", callback_data="toggle_clock")],
        [InlineKeyboardButton("🏷 تگ‌ها و یادداشت‌ها", callback_data="show_tags")],
        [InlineKeyboardButton("❌ بستن منو", callback_data="close_menu")]
    ])
    await message.reply_text("⚙️ **پنل مدیریت سلف‌بات مشتی**", reply_markup=keyboard)

@app.on_callback_query()
async def menu_callback(client, callback_query):
    global IS_SELF_ON, IS_CLOCK_ON
    data = callback_query.data
    
    if data == "toggle_self":
        IS_SELF_ON = not IS_SELF_ON
        await callback_query.answer(f"وضعیت سلف: {IS_SELF_ON}")
    elif data == "toggle_clock":
        IS_CLOCK_ON = not IS_CLOCK_ON
        await callback_query.answer(f"وضعیت ساعت: {IS_CLOCK_ON}")
    elif data == "show_tags":
        text = "📌 **فهرست تگ‌های ثبت شده:**\n\n"
        for tag, content in TAGS_DB.items():
            text += f"#️⃣ `#{tag}` : {content}\n"
        await callback_query.message.edit_text(text)
        return
    elif data == "close_menu":
        await callback_query.message.delete()
        return

    # Refresh Menu State
    status_self = "✅ روشن" if IS_SELF_ON else "❌ خاموش"
    status_clock = "✅ روشن" if IS_CLOCK_ON else "❌ خاموش"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"سلف‌بات: {status_self}", callback_data="toggle_self")],
        [InlineKeyboardButton(f"ساعت بیو: {status_clock}", callback_data="toggle_clock")],
        [InlineKeyboardButton("🏷 تگ‌ها و یادداشت‌ها", callback_data="show_tags")],
        [InlineKeyboardButton("❌ بستن منو", callback_data="close_menu")]
    ])
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)

@app.on_message(filters.me & filters.command("tags", prefixes="."))
async def get_tags(client, message):
    """Get Tags List in Saved Messages"""
    text = "📌 **تگ‌های شما:**\n\n"
    for tag, val in TAGS_DB.items():
        text += f"• `#{tag}` ➔ {val}\n"
    await message.reply_text(text)

@app.on_message(filters.private & ~filters.me)
async def pv_guard(client, message):
    """Simple Anti-Spam / PV Guard"""
    # Auto-reply if offline or spam detected
    pass

# ----------------- STARTUP -----------------
async def main():
    await app.start()
    print("Selfbot Started Successfully!")
    asyncio.create_task(clock_task())
    asyncio.create_task(auto_sender_task())
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
