import os
import telebot
from telebot import types
from flask import Flask, request, jsonify

TOKEN = "8757264129:AAFX4VI8n4MQ9k7mBl9YmsbOF0Nq3eDbqgw"
SITE_URL = "https://glafira-ai.ru/nsfw/promo.html"
RENDER_URL = "https://velvet-bot-lewg.onrender.com"
ADMIN_ID = "8172285744"

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
    keyboard.add(types.InlineKeyboardButton("🔥 Open Website", url=SITE_URL))
    bot.send_message(
        message.chat.id,
        f"🎭 *Welcome to Velvet!*\n\n"
        f"Chat with AI companions who understand you.\n\n"
        f"🔥 *Try free:*\n"
        f"• 8 characters\n"
        f"• 30 messages/day\n\n"
        f"💎 *Premium:*\n"
        f"• Custom characters\n"
        f"• Unlimited access\n\n"
        f"👉 {SITE_URL}",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.send_message(message.chat.id, f"ℹ️ Visit: {SITE_URL}")

@bot.message_handler(commands=['premium'])
def premium(message):
    bot.send_message(
        message.chat.id,
        f"💎 *Premium:*\n"
        f"• Custom characters\n"
        f"• Unlimited messages\n"
        f"• Full access\n\n"
        f"💰 120⭐/month\n\n"
        f"👉 {SITE_URL}/pricing.html",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if str(message.from_user.id) == ADMIN_ID:
        bot.send_message(message.chat.id, "✅ Admin access granted")
    else:
        bot.send_message(message.chat.id, "❌ Access denied")

@app.route('/')
def index():
    return "Velvet Bot is running"

bot.remove_webhook()
bot.set_webhook(url=f"{RENDER_URL}/webhook/{TOKEN}")
print(f"✅ Webhook set")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))
