import os
import telebot
from telebot import types
from flask import Flask, request, jsonify

TOKEN = "8757264129:AAFX4VI8n4MQ9k7mBl9YmsbOF0Nq3eDbqgw"
SITE_URL = "https://glafira-ai.ru/nsfw/promo.html"
RENDER_URL = "https://velvet-bot-lewg.onrender.com"
ADMIN_ID = "8172285744"  # Ваш Telegram ID

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route(f'/webhook/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return jsonify({'ok': True})
    return jsonify({'ok': False}), 403

@bot.message_handler(commands=['start'])
def start(message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔥 Открыть сайт", url=SITE_URL))
    bot.send_message(message.chat.id, f"🎭 *Добро пожаловать в Velvet!*\n\n👉 {SITE_URL}", parse_mode="Markdown", reply_markup=keyboard)

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.send_message(message.chat.id, f"ℹ️ Перейди на сайт: {SITE_URL}")

@bot.message_handler(commands=['premium'])
def premium(message):
    bot.send_message(message.chat.id, f"💎 *Premium:* 120⭐/мес\n👉 {SITE_URL}/pricing.html", parse_mode="Markdown")

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if str(message.from_user.id) == ADMIN_ID:
        bot.send_message(message.chat.id, "✅ Вы администратор\n\nКоманды:\n/status — статистика\n/users — пользователи")
    else:
        bot.send_message(message.chat.id, "❌ Доступ запрещен")

@bot.message_handler(commands=['status'])
def status_cmd(message):
    if str(message.from_user.id) == ADMIN_ID:
        bot.send_message(message.chat.id, "✅ Бот работает\nВерсия: 1.0\nСтатус: OK")
    else:
        bot.send_message(message.chat.id, "❌ Доступ запрещен")

@app.route('/')
def index():
    return "Velvet Bot is running"

# Настройка webhook
bot.remove_webhook()
bot.set_webhook(url=f"{RENDER_URL}/webhook/{TOKEN}")
print(f"✅ Webhook set to: {RENDER_URL}/webhook/{TOKEN}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))
