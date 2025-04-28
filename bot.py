import logging
import requests
import time
import threading
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === НАСТРОЙКИ ===
TELEGRAM_BOT_TOKEN = '7972664040:AAFKSXUgjUGKM6nzBFSf_o0bjnahdU6_86E'  # <-- Сюда вставить токен от @BotFather
CHAT_ID = 6492320144  # сюда запишем chat_id пользователя

BYBIT_PRICE_URL = 'https://api.bybit.com/v2/public/tickers?symbol=USDTUSDT'  # Можно будет заменить на реальный маркет USDT/USDT если понадобится
CHECK_INTERVAL = 600  # 600 секунд = 10 минут
VOLATILITY_THRESHOLD = 0.2  # 0.2% изменения

last_price = None
bot_running = False

# === НАСТРОЙКА ЛОГИРОВАНИЯ ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_usdt_price():
    try:
        response = requests.get('https://api.bybit.com/v5/market/tickers?category=spot&symbol=USDTUSDT')
        data = response.json()
        price = float(data['result']['list'][0]['lastPrice'])
        return price
    except Exception as e:
        logger.error(f"Ошибка при получении цены: {e}")
        return None


def price_monitor(bot: Bot):
    global last_price, bot_running

    while bot_running:
        current_price = get_usdt_price()

        if current_price and last_price:
            change = abs((current_price - last_price) / last_price) * 100

            if change >= VOLATILITY_THRESHOLD:
                direction = "выросла" if current_price > last_price else "упала"
                message = f"\u2B06\uFE0F Цена {direction} на {change:.2f}%!\nТекущая цена USDT: {current_price:.4f} USD"
                bot.send_message(chat_id=CHAT_ID, text=message)

        last_price = current_price
        time.sleep(CHECK_INTERVAL)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_running, CHAT_ID, last_price

    CHAT_ID = update.effective_chat.id
    if not bot_running:
        bot_running = True
        last_price = get_usdt_price()
        threading.Thread(target=price_monitor, args=(context.bot,), daemon=True).start()
        await update.message.reply_text("\u2705 Бот запущен. Отслеживаю курс USDT на Bybit!")
    else:
        await update.message.reply_text("\u26A0\uFE0F Бот уже работает.")


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_running

    bot_running = False
    await update.message.reply_text("\u274C Бот остановлен.")


async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_price = get_usdt_price()
    if current_price:
        await update.message.reply_text(f"\u2139\uFE0F Текущая цена USDT: {current_price:.4f} USD")
    else:
        await update.message.reply_text("\u26A0\uFE0F Не удалось получить цену. Попробуйте позже.")


if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("price", price))

    print("Бот запущен...")
    app.run_polling()
