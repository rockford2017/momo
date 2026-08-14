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
                json_str = msg.text.split("```json\n")[1].split("\n
