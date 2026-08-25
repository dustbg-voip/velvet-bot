import os
import telebot
from telebot import types
import logging
from flask import Flask, request, jsonify

TOKEN = "8777890530:AAGpBEQAxhmYfSshDlk670cWEpWOrY8x1rY"
SITE_URL = "https://glafira-ai.ru/nsfw/v6.html"

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
    bot.send_message(message.chat.id, f"🎭 *Добро пожаловать в Velvet AI!*\n\n👉 {SITE_URL}", parse_mode="Markdown", reply_markup=keyboard)

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.send_message(message.chat.id, f"ℹ️ Перейди на сайт: {SITE_URL}")

@bot.message_handler(commands=['premium'])
def premium(message):
    bot.send_message(message.chat.id, f"💎 *Premium:* 120⭐/мес\n👉 {SITE_URL}/pricing.html", parse_mode="Markdown")

@app.route('/')
def index():
    return "Velvet AI Bot is running"

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=f"https://velvet-bot.onrender.com/webhook/{TOKEN}")
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))
