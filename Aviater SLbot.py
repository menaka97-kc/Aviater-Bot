import asyncio
import time
import logging
import os
import threading
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from playwright.async_api import async_playwright

# Load environment variables
BOT_TOKEN = os.getenv("7153351675:AAFyReyKoTIagAN_6TKjz2JWvK9CKMgQ7Hc")
CHAT_ID = os.getenv("1093690060")  # Your personal chat ID
ADMIN_ID = int(1093690060)         # For admin-only commands

# Initialize bot and logger
bot = Bot(token=BOT_TOKEN)

logging.basicConfig(
    filename='bot.log',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ✅ Fetch crash data from 1xBet
async def fetch_crash_data():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://1xbet.com/en/slots/game/52358/aviator")
        await page.wait_for_timeout(6000)

        values = []
        try:
            elements = await page.query_selector_all(".aviator-last-rounds__item")
            for el in elements[:10]:
                text = await el.inner_text()
                value = float(text.replace("x", "").strip())
                values.append(value)
        except:
            values = []

        await browser.close()
        return values

# 🔮 Make prediction based on crash data
def predict(crash_data):
    if not crash_data:
        return "⚠️ No data found"
    avg = sum(crash_data) / len(crash_data)
    if avg < 2:
        return f"🔥 HIGH CRASH LIKELY (avg: {avg:.2f})"
    else:
        return f"⚠️ LOW CRASH POSSIBLE (avg: {avg:.2f})"

# 📤 Send prediction to Telegram
async def send_prediction():
    data = await fetch_crash_data()
    message = predict(data)
    logging.info(f"Sent prediction: {message}")
    await bot.send_message(chat_id=CHAT_ID, text=message)

# ♻️ Main prediction loop
async def start_bot_loop():
    while True:
        try:
            await send_prediction()
        except Exception as e:
            logging.error(f"Prediction error: {e}")
        time.sleep(120)

# ✅ Check if user is admin
def is_admin(user_id):
    return int(user_id) == ADMIN_ID

# 🟢 /start command (admin-only)
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if is_admin(user_id):
        update.message.reply_text("✅ Aviator Predictor is running!")
        logging.info(f"/start used by admin {user_id}")
    else:
        update.message.reply_text("⛔ You are not authorized to use this bot.")
        logging.warning(f"Unauthorized /start attempt by {user_id}")

# 📈 /status command (admin-only)
def status(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if is_admin(user_id):
        update.message.reply_text("📊 Bot is active and sending signals every 2 minutes.")
    else:
        update.message.reply_text("⛔ You are not authorized.")
        logging.warning(f"Unauthorized /status attempt by {user_id}")

# 🔁 Run Telegram bot + prediction loop
def run_telegram_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("status", status))
    updater.start_polling()
    updater.idle()

def main():
    telegram_thread = threading.Thread(target=run_telegram_bot)
    telegram_thread.start()
    asyncio.run(start_bot_loop())

if __name__ == "__main__":
    main()
