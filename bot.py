import asyncio
import random
import os
import re
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message

# ---------------- CONFIGURATIONS ----------------
API_ID = int(os.environ.get("API_ID", 123456))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING", "")

app = Client("selfbot_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# ---------------- STATE VARIABLES ----------------
IS_SELF_ON = True          # وضعیت کلی سلف‌بات (خاموش/روشن)
IS_LOOP_ON = False
IS_CLOCK_ON = True
IS_PMBOT_ON = False
IS_ANTIDEL_ON = True
IS_AFK_ON = False

AFK_REASON = ""
PMBOT_TEXT = "سلام عزیزم! در حال حاضر سیستم پاسخگویی خودکار فعال است. پیام بگذارید، بررسی می‌شود. 🌹"

CLOCK_STYLE = 1
TARGET_CHAT_LOOP = None
INTERVAL_LOOP = 300
TEXT_LOOP = ""

IS_TAGGING = False
TAG_LOGS = []

# ----------------- HELPER FUNCTIONS -----------------

def get_clock_string():
    now = datetime.now().strftime("%H:%M")
    styles = {
        1: f"⏰ {now}",
        2: f"⏱ [{now}]",
        3: f"✦ {now} ✦",
        4: f"• {now} •"
    }
    return styles.get(CLOCK_STYLE, f"⏰ {now}")

async def safe_type(chat_id, seconds=2):
    """شبیه‌سازی تایپینگ جهت حفظ امنیت اکانت"""
    try:
        await app.send_chat_action(chat_id, "typing")
        await asyncio.sleep(seconds)
    except Exception:
        pass

# ----------------- BACKGROUND TASKS -----------------

async def clock_task():
    """ساعت پویا روی بیوگرافی"""
    while True:
        if IS_SELF_ON and IS_CLOCK_ON:
            try:
                clock_text = get_clock_string()
                await app.update_profile(bio=f"{clock_text} | Selfbot Active")
            except Exception:
                pass
        await asyncio.sleep(60)

async def loop_sender_task():
    """ارسال تکراری هوشمند با ضد اسپم"""
    global IS_LOOP_ON
    while True:
        if IS_SELF_ON and IS_LOOP_ON and TARGET_CHAT_LOOP and TEXT_LOOP:
            try:
                await safe_type(TARGET_CHAT_LOOP, 2)
                sent_msg = await app.send_message(TARGET_CHAT_LOOP, TEXT_LOOP)
                asyncio.create_task(delete_trace(sent_msg, 120))
            except Exception as e:
                print(f"Error in Loop: {e}")

            delay = INTERVAL_LOOP + random.randint(3, 15)
            await asyncio.sleep(delay)
        else:
            await asyncio.sleep(5)

async def delete_trace(message, delay_seconds):
    await asyncio.sleep(delay_seconds)
    try:
        await message.delete()
    except Exception:
        pass

# ----------------- DASHBOARD & CONTROL -----------------

@app.on_message(filters.me & filters.command("self", prefixes="."))
async def toggle_selfbot(client, message):
    global IS_SELF_ON
    cmd = message.text.split()
    if len(cmd) > 1:
        if cmd[1].lower() == "off":
            IS_SELF_ON = False
            await message.reply_text("🔴 **سلف‌بات کاملاً غیرفعال شد.**")
        elif cmd[1].lower() == "on":
            IS_SELF_ON = True
            await message.reply_text("🟢 **سلف‌بات مجدداً فعال شد.**")
    else:
        status = "🟢 روشن" if IS_SELF_ON else "🔴 خاموش"
        await message.reply_text(f"⚙️ **وضعیت کلی سلف‌بات:** {status}")

@app.on_message(filters.me & filters.command(["help", "panel"], prefixes="."))
async def show_help(client, message):
    if not IS_SELF_ON: return

    st_self = "🟢 روشن" if IS_SELF_ON else "🔴 خاموش"
    st_loop = "🟢 روشن" if IS_LOOP_ON else "🔴 خاموش"
    st_clock = "🟢 روشن" if IS_CLOCK_ON else "🔴 خاموش"
    st_pm = "🟢 روشن" if IS_PMBOT_ON else "🔴 خاموش"
    st_antidel = "🟢 روشن" if IS_ANTIDEL_ON else "🔴 خاموش"
    st_afk = f"🟢 روشن ({AFK_REASON})" if IS_AFK_ON else "🔴 خاموش"

    help_text = (
        f"📋 **داشبورد و راهنمای کامل سلف‌بات**\n"
        f"💎 ───────────────────────── 💎\n\n"
        f"⚙️ **وضعیت فعلی سیستم:**\n"
        f"├ 🤖 **سلف‌بات:** {st_self}\n"
        f"├ 🔄 **ارسال تکراری:** {st_loop}\n"
        f"├ ⏰ **ساعت بیوگرافی:** {st_clock} (استایل: {CLOCK_STYLE})\n"
        f"├ 🛡 **منشی پی‌وی:** {st_pm}\n"
        f"├ 🗑 **ضد پاکسازی:** {st_antidel}\n"
        f"└ 🌙 **حالت غیبت (AFK):** {st_afk}\n\n"
        f"💎 ───────────────────────── 💎\n\n"
        f"🔑 **کنترل اصلی سلف‌بات:**\n"
        f"▫️ `.self on / off` ➔ خاموش/روشن کردن کل سلف‌بات\n\n"
        f"🏷 **تگ‌ها و گزارش‌ها:**\n"
        f"▫️ `.tags` ➔ مشاهده لاگ تگ‌ها\n"
        f"▫️ `.cleartags` ➔ پاکسازی تاریخچه تگ\n"
        f"▫️ `.tag [متن]` ➔ تگ تکی اعضا\n"
        f"▫️ `.all [متن]` ➔ تگ ۵ تایی اعضا\n"
        f"▫️ `.tagfast [متن]` ➔ تگ سریع اعضا\n"
        f"▫️ `.stoptag` ➔ توقف تگ‌زنی\n\n"
        f"⚡️ **تنظیمات حساب:**\n"
        f"▫️ `.clock` ➔ سوئیچ روشن/خاموش ساعت بیو\n"
        f"▫️ `.clockstyle [1-4]` ➔ تغییر استایل ساعت\n"
        f"▫️ `.afk [دلیل]` / `.unafk` ➔ حالت غیبت\n"
        f"▫️ `.pmbot on / off` ➔ منشی خودکار\n"
        f"▫️ `.setpm [متن]` ➔ تغییر متن منشی خودکار\n"
        f"▫️ `.antidel on / off` ➔ ضد پاکسازی\n\n"
        f"💣 **اسپم، ارسال و ابزارها:**\n"
        f"▫️ `.spam [تعداد] [متن]` ➔ اسپم سریع\n"
        f"▫️ `.delayspam [تاخیر] [تعداد] [متن]` ➔ اسپم با تاخیر\n"
        f"▫️ `.loop [here/آیدی] [ثانیه] [متن]` ➔ ارسال تکراری\n"
        f"▫️ `.stoploop` ➔ توقف ارسال تکراری\n"
        f"▫️ `.del [تعداد]` ➔ پاکسازی پیام‌های شما\n"
        f"▫️ `.purge` ➔ پاکسازی گروهی (با ریپلای)\n"
        f"▫️ `.calc [عبارت]` ➔ ماشین حساب\n"
        f"▫️ `.type [متن]` ➔ تایپ افکتی\n"
        f"▫️ `.font [متن]` ➔ فونت انگلیسی\n"
        f"▫️ `.info` ➔ دریافت اطلاعات کاربر\n"
        f"▫️ `.ping` ➔ بررسی سرعت سلف‌بات\n"
        f"💎 ───────────────────────── 💎"
    )
    await message.reply_text(help_text)

# ----------------- SYSTEM & UTILS -----------------

@app.on_message(filters.me & filters.command("ping", prefixes="."))
async def ping_cmd(client, message):
    if not IS_SELF_ON: return
    start = datetime.now()
    msg = await message.reply_text("🚀 **در حال بررسی...**")
    end = datetime.now()
    ms = (end - start).microseconds / 1000
    await msg.edit_text(f"⚡️ **سلف‌بات فعال است!**\n⏱ **پینگ:** `{ms:.2f}` میلی‌ثانیه")

@app.on_message(filters.me & filters.command("info", prefixes="."))
async def info_cmd(client, message):
    if not IS_SELF_ON: return
    user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    text = (
        f"👤 **اطلاعات کاربر:**\n\n"
        f"▫️ **نام:** {user.first_name}\n"
        f"▫️ **آیدی عددی:** `{user.id}`\n"
        f"▫️ **یوزرنام:** @{user.username if user.username else 'ندارد'}\n"
        f"▫️ **ربات:** {'بله' if user.is_bot else 'خیر'}"
    )
    await message.reply_text(text)

@app.on_message(filters.me & filters.command("calc", prefixes="."))
async def calc_cmd(client, message):
    if not IS_SELF_ON: return
    expr = message.text.replace(".calc", "").strip()
    try:
        res = eval(expr)
        await message.reply_text(f"🔢 **نتیجه:** `{res}`")
    except Exception as e:
        await message.reply_text(f"❌ **خطا در محاسبه:** `{e}`")

@app.on_message(filters.me & filters.command("type", prefixes="."))
async def type_cmd(client, message):
    if not IS_SELF_ON: return
    text = message.text.replace(".type", "").strip()
    typed = ""
    for char in text:
        typed += char
        await message.edit_text(typed + "▒")
        await asyncio.sleep(0.1)
    await message.edit_text(typed)

@app.on_message(filters.me & filters.command("font", prefixes="."))
async def font_cmd(client, message):
    if not IS_SELF_ON: return
    text = message.text.replace(".font", "").strip()
    fonts = {
        'a': '🅰', 'b': '🅱', 'c': '🅲', 'd': '🅳', 'e': '🅴', 'f': '🅵', 'g': '🅶',
        'h': '🅷', 'i': '🅸', 'j': '🅹', 'k': '🅺', 'l': '🅻', 'm': '🅼', 'n': '🅽',
        'o': '🅾', 'p': '🅿', 'q': '🆀', 'r': '🆁', 's': '🆂', 't': '🆃', 'u': '🆄',
        'v': '🆏', 'w': '🆆', 'x': '🆇', 'y': '🆈', 'z': '🆉'
    }
    converted = "".join([fonts.get(c.lower(), c) for c in text])
    await message.reply_text(f"🔤 **فونت جدید:**\n\n{converted}")

# ----------------- ACCOUNT SETTINGS -----------------

@app.on_message(filters.me & filters.command("clock", prefixes="."))
async def toggle_clock(client, message):
    if not IS_SELF_ON: return
    global IS_CLOCK_ON
    IS_CLOCK_ON = not IS_CLOCK_ON
    await message.reply_text(f"⏰ **ساعت بیوگرافی:** {'🟢 روشن' if IS_CLOCK_ON else '🔴 خاموش'}")

@app.on_message(filters.me & filters.command("clockstyle", prefixes="."))
async def change_clock_style(client, message):
    if not IS_SELF_ON: return
    global CLOCK_STYLE
    cmd = message.text.split()
    if len(cmd) > 1 and cmd[1].isdigit() and int(cmd[1]) in [1, 2, 3, 4]:
        CLOCK_STYLE = int(cmd[1])
        await message.reply_text(f"✅ **استایل ساعت روی حالت {CLOCK_STYLE} تنظیم شد.**")

@app.on_message(filters.me & filters.command("afk", prefixes="."))
async def set_afk(client, message):
    if not IS_SELF_ON: return
    global IS_AFK_ON, AFK_REASON
    AFK_REASON = message.text.replace(".afk", "").strip() or "در دسترس نیستم"
    IS_AFK_ON = True
    await message.reply_text(f"🌙 **حالت غیبت (AFK) فعال شد.**\n📝 **دلیل:** {AFK_REASON}")

@app.on_message(filters.me & filters.command("unafk", prefixes="."))
async def unset_afk(client, message):
    if not IS_SELF_ON: return
    global IS_AFK_ON
    IS_AFK_ON = False
    await message.reply_text("☀️ **حالت غیبت خاموش شد.**")

@app.on_message(filters.me & filters.command("pmbot", prefixes="."))
async def toggle_pmbot(client, message):
    if not IS_SELF_ON: return
    global IS_PMBOT_ON
    cmd = message.text.split()
    IS_PMBOT_ON = True if (len(cmd) > 1 and cmd[1].lower() == "on") else False
    await message.reply_text(f"🛡 **منشی خودکار پی‌وی:** {'🟢 روشن' if IS_PMBOT_ON else '🔴 خاموش'}")

@app.on_message(filters.me & filters.command("setpm", prefixes="."))
async def set_pmbot_text(client, message):
    if not IS_SELF_ON: return
    global PMBOT_TEXT
    new_text = message.text.replace(".setpm", "").strip()
    if new_text:
        PMBOT_TEXT = new_text
        await message.reply_text(f"✅ **متن جدید منشی ثبت شد:**\n\n{PMBOT_TEXT}")

@app.on_message(filters.me & filters.command("antidel", prefixes="."))
async def toggle_antidel(client, message):
    if not IS_SELF_ON: return
    global IS_ANTIDEL_ON
    cmd = message.text.split()
    IS_ANTIDEL_ON = True if (len(cmd) > 1 and cmd[1].lower() == "on") else False
    await message.reply_text(f"🗑 **ضد پاکسازی:** {'🟢 روشن' if IS_ANTIDEL_ON else '🔴 خاموش'}")

# ----------------- LOOP & SPAM -----------------

@app.on_message(filters.me & filters.command("loop", prefixes="."))
async def start_loop(client, message):
    if not IS_SELF_ON: return
    global IS_LOOP_ON, INTERVAL_LOOP, TARGET_CHAT_LOOP, TEXT_LOOP
    args = message.text.split(maxsplit=3)
    if len(args) < 4:
        await message.reply_text("❌ **فرمت صحیح:**\n`.loop [here/آیدی] [ثانیه] [متن]`")
        return
    
    target = message.chat.id if args[1] == "here" else (int(args[1]) if args[1].lstrip('-').isdigit() else args[1])
    INTERVAL_LOOP = int(args[2])
    TEXT_LOOP = args[3]
    TARGET_CHAT_LOOP = target
    IS_LOOP_ON = True
    await message.reply_text(f"🔄 **ارسال تکراری فعال شد!**\n🎯 **هدف:** `{TARGET_CHAT_LOOP}`\n⏱ **زمان:** `{INTERVAL_LOOP}` ثانیه")

@app.on_message(filters.me & filters.command("stoploop", prefixes="."))
async def stop_loop(client, message):
    if not IS_SELF_ON: return
    global IS_LOOP_ON
    IS_LOOP_ON = False
    await message.reply_text("🛑 **ارسال تکراری متوقف شد.**")

@app.on_message(filters.me & filters.command("spam", prefixes="."))
async def fast_spam(client, message):
    if not IS_SELF_ON: return
    args = message.text.split(maxsplit=2)
    if len(args) < 3 or not args[1].isdigit():
        await message.reply_text("❌ **فرمت صحیح:** `.spam [تعداد] [متن]`")
        return
    count = int(args[1])
    text = args[2]
    await message.delete()
    for _ in range(count):
        await app.send_message(message.chat.id, text)
        await asyncio.sleep(0.3)

@app.on_message(filters.me & filters.command("delayspam", prefixes="."))
async def delay_spam(client, message):
    if not IS_SELF_ON: return
    args = message.text.split(maxsplit=3)
    if len(args) < 4 or not args[1].isdigit() or not args[2].isdigit():
        await message.reply_text("❌ **فرمت صحیح:** `.delayspam [تاخیر] [تعداد] [متن]`")
        return
    delay = int(args[1])
    count = int(args[2])
    text = args[3]
    await message.delete()
    for _ in range(count):
        await app.send_message(message.chat.id, text)
        await asyncio.sleep(delay)

@app.on_message(filters.me & filters.command("del", prefixes="."))
async def delete_msgs(client, message):
    if not IS_SELF_ON: return
    cmd = message.text.split()
    count = int(cmd[1]) if len(cmd) > 1 and cmd[1].isdigit() else 1
    async for msg in app.get_chat_history(message.chat.id, limit=count + 1):
        if msg.from_user and msg.from_user.is_self:
            await msg.delete()

@app.on_message(filters.me & filters.command("purge", prefixes="."))
async def purge_msgs(client, message):
    if not IS_SELF_ON: return
    if not message.reply_to_message:
        await message.reply_text("❌ لطفاً روی یک پیام ریپلای کنید!")
        return
    start_id = message.reply_to_message.id
    end_id = message.id
    msg_ids = list(range(start_id, end_id + 1))
    await app.delete_messages(message.chat.id, msg_ids)

# ----------------- TAGGING SYSTEM -----------------

@app.on_message(filters.me & filters.command("tag", prefixes="."))
async def tag_single(client, message):
    if not IS_SELF_ON: return
    global IS_TAGGING
    IS_TAGGING = True
    tag_text = message.text.replace(".tag", "").strip() or "تگ"
    async for member in app.get_chat_members(message.chat.id):
        if not IS_TAGGING: break
        if not member.user.is_bot:
            await app.send_message(message.chat.id, f"[{member.user.first_name}](tg://user?id={member.user.id}) {tag_text}")
            TAG_LOGS.append(f"{datetime.now().strftime('%H:%M')} ➔ @{member.user.username or member.user.id}")
            await asyncio.sleep(2)

@app.on_message(filters.me & filters.command("all", prefixes="."))
async def tag_five(client, message):
    if not IS_SELF_ON: return
    global IS_TAGGING
    IS_TAGGING = True
    tag_text = message.text.replace(".all", "").strip() or "تگ عمومی"
    members_list = []
    async for member in app.get_chat_members(message.chat.id):
        if not IS_TAGGING: break
        if not member.user.is_bot:
            members_list.append(f"[{member.user.first_name}](tg://user?id={member.user.id})")
            if len(members_list) == 5:
                await app.send_message(message.chat.id, f"{' | '.join(members_list)}\n\n📣 {tag_text}")
                members_list = []
                await asyncio.sleep(3)

@app.on_message(filters.me & filters.command("tagfast", prefixes="."))
async def tag_fast_cmd(client, message):
    if not IS_SELF_ON: return
    global IS_TAGGING
    IS_TAGGING = True
    tag_text = message.text.replace(".tagfast", "").strip() or "تگ سریع"
    async for member in app.get_chat_members(message.chat.id):
        if not IS_TAGGING: break
        if not member.user.is_bot:
            await app.send_message(message.chat.id, f"[{member.user.first_name}](tg://user?id={member.user.id}) {tag_text}")
            await asyncio.sleep(0.8)

@app.on_message(filters.me & filters.command("stoptag", prefixes="."))
async def stop_tag(client, message):
    if not IS_SELF_ON: return
    global IS_TAGGING
    IS_TAGGING = False
    await message.reply_text("🛑 **عملیات تگ‌زنی متوقف شد.**")

@app.on_message(filters.me & filters.command("tags", prefixes="."))
async def show_tags_log(client, message):
    if not IS_SELF_ON: return
    text = "📌 **تاریخچه آخرین تگ‌ها:**\n\n" + "\n".join(TAG_LOGS[-10:]) if TAG_LOGS else "تاریخچه‌ای وجود ندارد."
    await message.reply_text(text)

@app.on_message(filters.me & filters.command("cleartags", prefixes="."))
async def clear_tags_log(client, message):
    if not IS_SELF_ON: return
    global TAG_LOGS
    TAG_LOGS = []
    await message.reply_text("🧹 **تاریخچه تگ‌ها پاک شد.**")

# ----------------- PASSIVE LISTENERS -----------------

@app.on_message(filters.private & ~filters.me & ~filters.bot)
async def pv_handlers(client, message):
    if not IS_SELF_ON: return

    if IS_AFK_ON:
        await message.reply_text(f"🌙 **در حال حاضر غایب هستم.**\n📝 **دلیل:** {AFK_REASON}")
    elif IS_PMBOT_ON:
        await message.reply_text(PMBOT_TEXT)

    # ذخیره‌ساز هوشمند رسانه‌های زمان‌دار و یک‌بارمصرف (TTL)
    if message.ttl_seconds:
        try:
            file_path = await message.download()
            await app.send_document("me", document=file_path, caption=f"📥 **رسانه زمان‌دار ذخیره شد از طرف:** {message.from_user.mention}")
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error TTL Save: {e}")

@app.on_deleted_messages()
async def anti_delete_handler(client, messages):
    if not IS_SELF_ON: return

    if IS_ANTIDEL_ON:
        for msg in messages:
            if msg.text:
                try:
                    await app.send_message("me", f"🗑 **پیام پاک شده شناسایی شد:**\n\n`{msg.text}`")
                except Exception:
                    pass

# ----------------- STARTUP -----------------
async def main():
    await app.start()
    print("Selfbot is Running Successfully!")
    asyncio.create_task(clock_task())
    asyncio.create_task(loop_sender_task())
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
