import os
import telebot
from telebot import types
from flask import Flask, request, jsonify
import time

TOKEN = "8757264129:AAFX4VI8n4MQ9k7mBl9YmsbOF0Nq3eDbqgw"
SITE_URL = "https://glafira-ai.ru/nsfw/promo.html"
RENDER_URL = "https://velvet-bot-lewg.onrender.com"
ADMIN_ID = "8172285744"

PREMIUM_PRICE_STARS = 100

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

premium_users = set()

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
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("🔥 Open Website", url=SITE_URL))
    keyboard.add(types.InlineKeyboardButton("💎 Get Premium", callback_data="premium"))
    
    bot.send_message(
        message.chat.id,
        f"🎭 *Welcome to Velvet!*\n\n"
        f"Chat with AI companions who understand your deepest desires.\n\n"
        f"🔥 *Free:*\n"
        f"• 8 characters\n"
        f"• 30 messages/day\n"
        f"• Flirt and erotic\n\n"
        f"💎 *Premium:*\n"
        f"• Custom characters\n"
        f"• Unlimited messages\n"
        f"• Full access\n\n"
        f"👉 {SITE_URL}",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data == "premium")
def premium_callback(call):
    user_id = call.message.chat.id
    
    prices = [types.LabeledPrice(label="Premium месяц", amount=PREMIUM_PRICE_STARS)]
    
    try:
        bot.send_invoice(
            chat_id=user_id,
            title="💎 Velvet Premium",
            description=f"Доступ к Premium на 30 дней:\n"
                        f"• Свои персонажи\n"
                        f"• Безлимитные сообщения\n"
                        f"• Полный доступ",
            payload=f"premium_{user_id}_{int(time.time())}",
            provider_token="",
            currency="XTR",
            prices=prices,
            start_parameter="premium_subscription"
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"Ошибка: {str(e)}")
    
    bot.answer_callback_query(call.id)

@bot.pre_checkout_query_handler(func=lambda query: True)
def pre_checkout(pre_checkout_query):
    try:
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    except Exception as e:
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=False, error_message=str(e))

@bot.message_handler(content_types=['successful_payment'])
def successful_payment(message):
    user_id = message.from_user.id
    
    premium_users.add(user_id)
    
    bot.send_message(
        user_id,
        f"✅ *Платеж успешно получен!*\n\n"
        f"💎 *Premium активирован на 30 дней!*\n\n"
        f"🎉 Спасибо за покупку!\n"
        f"🔥 Наслаждайтесь полным доступом к Velvet!",
        parse_mode="Markdown"
    )
    
    try:
        bot.send_message(
            ADMIN_ID,
            f"💰 *Новый платеж!*\n"
            f"Пользователь: {user_id}\n"
            f"Сумма: {message.successful_payment.total_amount} Stars\n"
            f"ID платежа: {message.successful_payment.telegram_payment_charge_id}"
        )
    except:
        pass

@bot.message_handler(commands=['premium'])
def premium_cmd(message):
    prices = [types.LabeledPrice(label="Premium месяц", amount=PREMIUM_PRICE_STARS)]
    
    bot.send_invoice(
        chat_id=message.chat.id,
        title="💎 Velvet Premium",
        description=f"Доступ к Premium на 30 дней",
        payload=f"premium_{message.chat.id}_{int(time.time())}",
        provider_token="",
        currency="XTR",
        prices=prices,
        start_parameter="premium_subscription"
    )

@bot.message_handler(commands=['status'])
def status_cmd(message):
    user_id = message.chat.id
    if user_id in premium_users:
        bot.send_message(user_id, "✅ У вас активен Premium!")
    else:
        bot.send_message(user_id, "⛔ У вас нет Premium. Используйте /premium для покупки.")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.send_message(message.chat.id, f"ℹ️ Посетите сайт: {SITE_URL}")

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if str(message.from_user.id) == ADMIN_ID:
        bot.send_message(message.chat.id, "✅ Админ-панель:\n" + f"Активных Premium: {len(premium_users)}")
    else:
        bot.send_message(message.chat.id, "❌ Доступ запрещен")

@app.route('/')
def index():
    return "Velvet Bot is running (Stars payments)"

bot.remove_webhook()
bot.set_webhook(url=f"{RENDER_URL}/webhook/{TOKEN}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))
