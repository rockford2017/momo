import asyncio
import random
import os
import re
import json
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message

# ---------------- CONFIGURATIONS ----------------
API_ID = int(os.environ.get("API_ID", 123456))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING", "")

app = Client("selfbot_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# ---------------- STATE MANAGEMENT & PERSISTENCE ----------------
CONFIG = {
    "IS_SELF_ON": True,
    "IS_CLOCK_NAME": False,
    "IS_CLOCK_BIO": False,
    "CLOCK_STYLE": 1,
    "IS_AFK_ON": False,
    "AFK_REASON": "",
    "IS_ANTIDEL_ON": True,
    "IS_ANTIEDIT_ON": True,
    "IS_TTL_SAVE": True,
    "ORIGINAL_NAME": "",
    "ORIGINAL_BIO": ""
}

IS_LOOP_ON = False
TARGET_CHAT_LOOP = None
INTERVAL_LOOP = 300
TEXT_LOOP = ""

IS_TAGGING = False
TAG_LOGS = []

SETTINGS_MSG_CAPTION = "#SELFBOT_CONFIG_DATA"

async def save_config_to_telegram():
    """ذخیره‌سازی دائمی تنظیمات در پیام‌های ذخیره‌شده (Saved Messages)"""
    try:
        config_json = json.dumps(CONFIG, ensure_ascii=False, indent=2)
        text = f"{SETTINGS_MSG_CAPTION}\n```json\n{config_json}\n```"
        
        async for msg in app.get_chat_history("me", limit=20):
            if msg.text and SETTINGS_MSG_CAPTION in msg.text:
                await msg.edit_text(text)
                return
        await app.send_message("me", text)
    except Exception as e:
        print(f"Error saving config: {e}")

async def load_config_from_telegram():
    """بازیابی تنظیمات پس از ری‌استارت"""
    global CONFIG
    try:
        async for msg in app.get_chat_history("me", limit=20):
            if msg.text and SETTINGS_MSG_CAPTION in msg.text:
                json_str = msg.text.split("```json\n")[1].split("\n```")[0]
                loaded_data = json.loads(json_str)
                CONFIG.update(loaded_data)
                print("Config loaded successfully!")
                return
    except Exception as e:
        print(f"Error loading config: {e}")

# ----------------- HELPER FUNCTIONS -----------------

def get_clock_string():
    now = datetime.now().strftime("%H:%M")
    styles = {
        1: f"⏰ {now}",
        2: f"[{now}]",
        3: f"✦ {now} ✦",
        4: f"• {now} •"
    }
    return styles.get(CONFIG["CLOCK_STYLE"], f"⏰ {now}")

async def safe_type(chat_id, seconds=1):
    try:
        await app.send_chat_action(chat_id, "typing")
        await asyncio.sleep(seconds)
    except Exception:
        pass

# ----------------- BACKGROUND TASKS -----------------

async def clock_task():
    """وظیفه به‌روزرسانی هوشمند ساعت روی اسم و بیوگرافی"""
    while True:
        if CONFIG["IS_SELF_ON"]:
            clock_text = get_clock_string()
            
            # به‌روزرسانی ساعت اسم
            if CONFIG["IS_CLOCK_NAME"]:
                try:
                    base_name = CONFIG["ORIGINAL_NAME"] or "User"
                    new_first_name = f"{base_name} {clock_text}"
                    await app.update_profile(first_name=new_first_name)
                except Exception as e:
                    print(f"Clock Name Error: {e}")
            
            # به‌روزرسانی ساعت بیوگرافی
            if CONFIG["IS_CLOCK_BIO"]:
                try:
                    base_bio = CONFIG["ORIGINAL_BIO"] or ""
                    new_bio = f"{base_bio} | {clock_text}".strip(" |")
                    await app.update_profile(bio=new_bio[:70])
                except Exception as e:
                    print(f"Clock Bio Error: {e}")

        await asyncio.sleep(60)

async def loop_sender_task():
    """ارسال تکراری هوشمند با تمهیدات ضد اسپم"""
    global IS_LOOP_ON
    while True:
        if CONFIG["IS_SELF_ON"] and IS_LOOP_ON and TARGET_CHAT_LOOP and TEXT_LOOP:
            try:
                await safe_type(TARGET_CHAT_LOOP, 1)
                sent_msg = await app.send_message(TARGET_CHAT_LOOP, TEXT_LOOP)
                asyncio.create_task(delete_trace(sent_msg, 120))
            except Exception as e:
                print(f"Error in Loop: {e}")

            delay = INTERVAL_LOOP + random.randint(2, 10)
            await asyncio.sleep(delay)
        else:
            await asyncio.sleep(5)

async def delete_trace(message, delay_seconds):
    await asyncio.sleep(delay_seconds)
    try:
        await message.delete()
    except Exception:
        pass

# ----------------- DASHBOARD & PANEL -----------------

@app.on_message(filters.me & filters.command("self", prefixes="."))
async def toggle_selfbot(client, message):
    cmd = message.text.split()
    if len(cmd) > 1:
        if cmd[1].lower() == "off":
            CONFIG["IS_SELF_ON"] = False
            await message.edit_text("🔴 **سلف‌بات غیرفعال شد.**")
        elif cmd[1].lower() == "on":
            CONFIG["IS_SELF_ON"] = True
            await message.edit_text("🟢 **سلف‌بات فعال شد.**")
        await save_config_to_telegram()
    else:
        status = "🟢 روشن" if CONFIG["IS_SELF_ON"] else "🔴 خاموش"
        await message.edit_text(f"⚙️ **وضعیت کلی سلف‌بات:** {status}")

@app.on_message(filters.me & filters.command(["help", "panel"], prefixes="."))
async def show_help(client, message):
    if not CONFIG["IS_SELF_ON"]: return

    st_self = "🟢 فعال" if CONFIG["IS_SELF_ON"] else "🔴 غیرفعال"
    st_cname = f"🟢 روشن (استایل {CONFIG['CLOCK_STYLE']})" if CONFIG["IS_CLOCK_NAME"] else "🔴 خاموش"
    st_cbio = "🟢 روشن" if CONFIG["IS_CLOCK_BIO"] else "🔴 خاموش"
    st_loop = "🟢 روشن" if IS_LOOP_ON else "🔴 خاموش"
    st_afk = f"🟢 روشن ({CONFIG['AFK_REASON']})" if CONFIG["IS_AFK_ON"] else "🔴 خاموش"
    st_antidel = "🟢 فعال" if CONFIG["IS_ANTIDEL_ON"] else "🔴 غیرفعال"
    st_antiedit = "🟢 فعال" if CONFIG["IS_ANTIEDIT_ON"] else "🔴 غیرفعال"

    panel_text = (
        f"╭───𖤓 **𝗦𝗧𝗘𝗔𝗟𝗧𝗛 𝗦𝗘𝗟𝗙𝗕𝗢𝗧** 𖤓───╮\n"
        f"│\n"
        f"├ ⚙️ **[ وضعیت سیستم ]**\n"
        f"│ ├ 🤖 سلف‌بات: {st_self}\n"
        f"│ ├ 👤 ساعت روی اسم: {st_cname}\n"
        f"│ ├ 📝 ساعت روی بیو: {st_cbio}\n"
        f"│ ├ 🔄 ارسال تکراری: {st_loop}\n"
        f"│ ├ 🌙 حالت AFK: {st_afk}\n"
        f"│ └ 💾 ذخیره‌سازی: 🟢 متصل\n"
        f"│\n"
        f"├ 🛡 **[ امنیت و حفاظت ]**\n"
        f"│ ├ 🗑 ضد پاکسازی (Anti-Delete): {st_antidel}\n"
        f"│ ├ ✏️ ضد ویرایش (Anti-Edit): {st_antiedit}\n"
        f"│ └ 📥 ذخیره زمان‌دارها (TTL): 🟢 فعال\n"
        f"│\n"
        f"├ 🕹 **[ دستورات مدیریت ]**\n"
        f"│ ├ `.self on/off` ➔ خاموش/روشن کلی\n"
        f"│ ├ `.clockname` ➔ سوئیچ ساعت روی اسم\n"
        f"│ ├ `.clockbio` ➔ سوئیچ ساعت روی بیو\n"
        f"│ ├ `.clockstyle [1-4]` ➔ استایل ساعت\n"
        f"│ ├ `.afk [دلیل]` / `.unafk` ➔ حالت غیبت\n"
        f"│ ├ `.antidel on/off` ➔ ضد پاکسازی\n"
        f"│ └ `.antiedit on/off` ➔ ضد ویرایش\n"
        f"│\n"
        f"├ 💣 **[ ابزارها & تگ ]**\n"
        f"│ ├ `.loop [here/آیدی] [ثانیه] [متن]`\n"
        f"│ ├ `.stoploop` ➔ توقف ارسال تکراری\n"
        f"│ ├ `.spam [تعداد] [متن]` ➔ اسپم سریع\n"
        f"│ ├ `.del [تعداد]` / `.purge` ➔ پاکسازی\n"
        f"│ ├ `.tag` / `.all` / `.tagfast` / `.stoptag`\n"
        f"│ ├ `.calc [عبارت]` ➔ ماشین حساب\n"
        f"│ └ `.ping` ➔ بررسی سرعت\n"
        f"│\n"
        f"╰──────────────────────────╯"
    )
    await message.edit_text(panel_text)

# ----------------- SYSTEM & UTILS -----------------

@app.on_message(filters.me & filters.command("ping", prefixes="."))
async def ping_cmd(client, message):
    if not CONFIG["IS_SELF_ON"]: return
    start = datetime.now()
    await message.edit_text("🚀")
    end = datetime.now()
    ms = (end - start).microseconds / 1000
    await message.edit_text(f"⚡️ `{ms:.2f} ms`")

@app.on_message(filters.me & filters.command("calc", prefixes="."))
async def calc_cmd(client, message):
    if not CONFIG["IS_SELF_ON"]: return
    expr = message.text.replace(".calc", "").strip()
    try:
        res = eval(expr)
        await message.edit_text(f"🔢 `{res}`")
    except Exception as e:
        await message.edit_text(f"❌ Error: `{e}`")

# ----------------- PROFILE & CLOCKS -----------------

@app.on_message(filters.me & filters.command("clockname", prefixes="."))
async def toggle_clock_name(client, message):
    if not CONFIG["IS_SELF_ON"]: return
    CONFIG["IS_CLOCK_NAME"] = not CONFIG["IS_CLOCK_NAME"]
    
    if not CONFIG["IS_CLOCK_NAME"]:
        # بازگرداندن اسم اصلی
        try:
            await app.update_profile(first_name=CONFIG["ORIGINAL_NAME"])
        except Exception:
            pass
            
    await save_config_to_telegram()
    status = "🟢 روشن" if CONFIG["IS_CLOCK_NAME"] else "🔴 خاموش"
    await message.edit_text(f"👤 **ساعت روی اسم:** {status}")

@app.on_message(filters.me & filters.command("clockbio", prefixes="."))
async def toggle_clock_bio(client, message):
    if not CONFIG["IS_SELF_ON"]: return
    CONFIG["IS_CLOCK_BIO"] = not CONFIG["IS_CLOCK_BIO"]
    
    if not CONFIG["IS_CLOCK_BIO"]:
        # بازگرداندن بیوگرافی اصلی
        try:
            await app.update_profile(bio=CONFIG["ORIGINAL_BIO"])
        except Exception:
            pass

    await save_config_to_telegram()
    status = "🟢 روشن" if CONFIG["IS_CLOCK_BIO"] else "🔴 خاموش"
    await message.edit_text(f"📝 **ساعت روی بیو:** {status}")

@app.on_message(filters.me & filters.command("clockstyle", prefixes="."))
async def change_clock_style(client, message):
    if not CONFIG["IS_SELF_ON"]: return
    cmd = message.text.split()
    if len(cmd) > 1 and cmd[1].isdigit() and int(cmd[1]) in [1, 2, 3, 4]:
        CONFIG["CLOCK_STYLE"] = int(cmd[1])
        await save_config_to_telegram()
        await message.edit_text(f"✅ **استایل ساعت روی {CONFIG['CLOCK_STYLE']} تنظیم شد.**")

@app.on_message(filters.me & filters.command("afk", prefixes="."))
async def set_afk(client, message):
    if not CONFIG["IS_SELF_ON"]: return
    CONFIG["AFK_REASON"] = message.text.replace(".afk", "").strip() or "در دسترس نیستم"
    CONFIG["IS_AFK_ON"] = True
    await save_config_to_telegram()
    await message.edit_text(f"🌙 **حالت غیبت فعال شد.**\n📝 **دلیل:** {CONFIG['AFK_REASON']}")

@app.on_message(filters.me & filters.command("unafk", prefixes="."))
async def unset_afk(client, message):
    if not CONFIG["IS_SELF_ON"]: return
    CONFIG["IS_AFK_ON"] = False
    await save_config_to_telegram()
    await message.edit_text("☀️ **حالت غیبت غیرفعال شد.**")

@app.on_message(filters.me & filters.command("antidel", prefixes="."))
async def toggle_antidel(client, message):
    if not CONFIG["IS_SELF_ON"]: return
    cmd = message.text.split()
    CONFIG["IS_ANTIDEL_ON"] = True if (len(cmd) > 1 and cmd[1].lower() == "on") else False
    await save_config_to_telegram()
    await message.edit_text(f"🗑 **ضد پاکسازی:** {'🟢 روشن' if CONFIG['IS_ANTIDEL_ON'] else '🔴 خاموش'}")

@app.on_message(filters.me & filters.command("antiedit", prefixes="."))
async def toggle_antiedit(client, message):
    if not CONFIG["IS_SELF_ON"]: return
    cmd = message.text.split()
    CONFIG["IS_ANTIEDIT_ON"] = True if (len(cmd) > 1 and cmd[1].lower() == "on") else False
    await save_config_to_telegram()
    await message.edit_text(f"✏️ **ضد ویرایش:** {'🟢 روشن' if CONFIG['IS_ANTIEDIT_ON'] else '🔴 خاموش'}")

# ----------------- LOOP & SPAM -----------------

@app.on_message(filters.me & filters.command("loop", prefixes="."))
async def start_loop(client, message):
    if not CONFIG["IS_SELF_ON"]: return
    global IS_LOOP_ON, INTERVAL_LOOP, TARGET_CHAT_LOOP, TEXT_LOOP
    args = message.text.split(maxsplit=3)
    if len(args) < 4:
        await message.edit_text("❌ `.loop [here/آیدی] [ثانیه] [متن]`")
        return
    
    target = message.chat.id if args[1] == "here" else (int(args[1]) if args[1].lstrip('-').isdigit() else args[1])
    INTERVAL_LOOP = int(args[2])
    TEXT_LOOP = args[3]
    TARGET_CHAT_LOOP = target
    IS_LOOP_ON = True
    await message.edit_text(f"🔄 **ارسال تکراری فعال شد!**\n🎯 **هدف:** `{TARGET_CHAT_LOOP}`")

@app.on_message(filters.me & filters.command("stoploop", prefixes="."))
async def stop_loop(client, message):
    if not CONFIG["IS_SELF_ON"]: return
    global IS_LOOP_ON
    IS_LOOP_ON = False
    await message.edit_text("🛑 **ارسال تکراری متوقف شد.**")

@app.on_message(filters.me & filters.command("spam", prefixes="."))
async def fast_spam(client, message):
    if not CONFIG["IS_SELF_ON"]: return
    args = message.text.split(maxsplit=2)
    if len(args) < 3 or not args[1].isdigit():
        await message.edit_text("❌ `.spam [تعداد] [متن]`")
        return
    count = int(args[1])
    text = args[2]
    await message.delete()
    for _ in range(count):
        await app.send_message(message.chat.id, text)
        await asyncio.sleep(0.3)

@app.on_message(filters.me & filters.command("del", prefixes="."))
async def delete_msgs(client, message):
    if not CONFIG["IS_SELF_ON"]: return
    cmd = message.text.split()
    count = int(cmd[1]) if len(cmd) > 1 and cmd[1].isdigit() else 1
    async for msg in app.get_chat_history(message.chat.id, limit=count + 1):
        if msg.from_user and msg.from_user.is_self:
            await msg.delete()

@app.on_message(filters.me & filters.command("purge", prefixes="."))
async def purge_msgs(client, message):
    if not CONFIG["IS_SELF_ON"]: return
    if not message.reply_to_message:
        await message.edit_text("❌ روی یک پیام ریپلای کنید.")
        return
    start_id = message.reply_to_message.id
    end_id = message.id
    msg_ids = list(range(start_id, end_id + 1))
    await app.delete_messages(message.chat.id, msg_ids)

# ----------------- TAGGING SYSTEM -----------------

@app.on_message(filters.me & filters.command("tag", prefixes="."))
async def tag_single(client, message):
    if not CONFIG["IS_SELF_ON"]: return
    global IS_TAGGING
    IS_TAGGING = True
    tag_text = message.text.replace(".tag", "").strip() or "تگ"
    await message.delete()
    async for member in app.get_chat_members(message.chat.id):
        if not IS_TAGGING: break
        if not member.user.is_bot:
            await app.send_message(message.chat.id, f"[{member.user.first_name}](tg://user?id={member.user.id}) {tag_text}")
            await asyncio.sleep(2)

@app.on_message(filters.me & filters.command("all", prefixes="."))
async def tag_five(client, message):
    if not CONFIG["IS_SELF_ON"]: return
    global IS_TAGGING
    IS_TAGGING = True
    tag_text = message.text.replace(".all", "").strip() or "تگ"
    await message.delete()
    members_list = []
    async for member in app.get_chat_members(message.chat.id):
        if not IS_TAGGING: break
        if not member.user.is_bot:
            members_list.append(f"[{member.user.first_name}](tg://user?id={member.user.id})")
            if len(members_list) == 5:
                await app.send_message(message.chat.id, f"{' | '.join(members_list)}\n\n📣 {tag_text}")
                members_list = []
                await asyncio.sleep(3)

@app.on_message(filters.me & filters.command("stoptag", prefixes="."))
async def stop_tag(client, message):
    if not CONFIG["IS_SELF_ON"]: return
    global IS_TAGGING
    IS_TAGGING = False
    await message.edit_text("🛑 **عملیات تگ متوقف شد.**")

# ----------------- PASSIVE LISTENERS & SECURITY -----------------

@app.on_message(filters.private & ~filters.me & ~filters.bot)
async def pv_handlers(client, message):
    if not CONFIG["IS_SELF_ON"]: return

    # حالت غیبت (AFK)
    if CONFIG["IS_AFK_ON"]:
        await message.reply_text(f"🌙 **در حال حاضر غایب هستم.**\n📝 **دلیل:** {CONFIG['AFK_REASON']}")

    # دانلود و ذخیره خودکار رسانه‌های زمان‌دار و یک‌بارمصرف (TTL)
    if message.ttl_seconds and CONFIG["IS_TTL_SAVE"]:
        try:
            file_path = await message.download()
            sender_info = f"@{message.from_user.username}" if message.from_user.username else f"`{message.from_user.id}`"
            await app.send_document(
                "me", 
                document=file_path, 
                caption=f"📥 **رسانه یک‌بارمصرف ذخیره شد**\n👤 **فرستنده:** {sender_info}"
            )
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error TTL Save: {e}")

@app.on_message_edited()
async def anti_edit_handler(client, message):
    """گزارش ادیت شدن پیام‌ها به پیام‌های ذخیره‌شده"""
    if CONFIG["IS_SELF_ON"] and CONFIG["IS_ANTIEDIT_ON"]:
        if not message.from_user or message.from_user.is_self: return
        try:
            chat_title = message.chat.title if message.chat.title else "پی‌وی"
            user_info = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
            log_text = (
                f"✏️ **ویرایش پیام شناسایی شد!**\n\n"
                f"👤 **کاربر:** {user_info}\n"
                f"📍 **مکان:** {chat_title}\n"
                f"📝 **متن جدید:**\n`{message.text}`"
            )
            await app.send_message("me", log_text)
        except Exception:
            pass

@app.on_deleted_messages()
async def anti_delete_handler(client, messages):
    """گزارش پاک شدن پیام‌ها به پیام‌های ذخیره‌شده"""
    if CONFIG["IS_SELF_ON"] and CONFIG["IS_ANTIDEL_ON"]:
        for msg in messages:
            if msg.text:
                try:
                    log_text = f"🗑 **پیام پاک‌شده شناسایی شد:**\n\n`{msg.text}`"
                    await app.send_message("me", log_text)
                except Exception:
                    pass

# ----------------- STARTUP & INITIALIZATION -----------------
async def main():
    await app.start()
    print("Selfbot started!")
    
    # ذخیره اسم و بیوگرافی اولیه اکانت
    me = await app.get_me()
    CONFIG["ORIGINAL_NAME"] = me.first_name or ""
    
    try:
        full_user = await app.get_chat("me")
        CONFIG["ORIGINAL_BIO"] = full_user.bio or ""
    except Exception:
        CONFIG["ORIGINAL_BIO"] = ""

    # بازیابی تنظیمات قبلی از پیام‌های ذخیره‌شده
    await load_config_from_telegram()

    # فعال‌سازی وظایف پس‌زمینه
    asyncio.create_task(clock_task())
    asyncio.create_task(loop_sender_task())
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
