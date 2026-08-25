import os
import telebot
from telebot import types
from flask import Flask, request, jsonify
import time

TOKEN = "8757264129:AAFX4VI8n4MQ9k7mBl9YmsbOF0Nq3eDbqgw"
SITE_URL = "https://glafira-ai.ru/nsfw/promo.html"
RENDER_URL = "https://velvet-bot-lewg.onrender.com"
ADMIN_ID = "8172285744"

# Тарифы
PLANS = {
    "1month": {"label": "Premium — 1 месяц", "price": 100, "days": 30},
    "3months": {"label": "Premium — 3 месяца", "price": 250, "days": 90},
    "1year": {"label": "Premium — 1 год", "price": 800, "days": 365},
}

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
premium_users = {}  # user_id -> expiry_timestamp

@app.route(f'/webhook/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return jsonify({'ok': True})
    return jsonify({'ok': False}), 403

def send_invoice_premium(chat_id, plan_key="1month"):
    """Отправляет инвойс для оплаты Premium"""
    plan = PLANS[plan_key]
    prices = [types.LabeledPrice(label=plan["label"], amount=plan["price"])]
    
    try:
        bot.send_invoice(
            chat_id=chat_id,
            title="💎 Velvet Premium",
            description=f"Доступ к Premium на {plan['days']} дней:\n"
                        f"• Свои персонажи\n"
                        f"• Безлимитные сообщения\n"
                        f"• Полный доступ",
            payload=f"premium_{plan_key}_{chat_id}_{int(time.time())}",
            provider_token="",
            currency="XTR",
            prices=prices,
            start_parameter="premium_subscription"
        )
        return True
    except Exception as e:
        print(f"Error sending invoice: {e}")
        return False

@bot.message_handler(commands=['start'])
def start(message):
    # Проверяем, если пользователь пришел за Premium
    if message.text and "premium" in message.text:
        show_premium_plans(message.chat.id)
        return
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("🔥 Open Website", url=SITE_URL))
    keyboard.add(types.InlineKeyboardButton("💎 Get Premium", callback_data="show_plans"))
    
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

def show_premium_plans(chat_id):
    """Показывает тарифы"""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("💎 1 месяц — 100⭐", callback_data="buy_1month"),
        types.InlineKeyboardButton("🔥 3 месяца — 250⭐ (скидка 17%)", callback_data="buy_3months"),
        types.InlineKeyboardButton("👑 1 год — 800⭐ (скидка 33%)", callback_data="buy_1year")
    )
    
    bot.send_message(
        chat_id,
        f"💎 *Premium Тарифы*\n\n"
        f"Выберите план:\n\n"
        f"⭐ *1 месяц:* 100 Stars\n"
        f"⭐ *3 месяца:* 250 Stars (экономия 17%)\n"
        f"⭐ *1 год:* 800 Stars (экономия 33%)\n\n"
        f"Все тарифы включают:\n"
        f"✅ Свои персонажи\n"
        f"✅ Безлимит\n"
        f"✅ Полный доступ",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data == "show_plans")
def show_plans_callback(call):
    show_premium_plans(call.message.chat.id)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_callback(call):
    plan_key = call.data.replace("buy_", "")
    if plan_key in PLANS:
        send_invoice_premium(call.message.chat.id, plan_key)
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
    
    # Определяем тариф из payload
    payload = message.successful_payment.invoice_payload
    plan_key = "1month"  # по умолчанию
    for key in PLANS:
        if key in payload:
            plan_key = key
            break
    
    days = PLANS[plan_key]["days"]
    expiry = int(time.time()) + days * 86400
    premium_users[user_id] = expiry
    
    bot.send_message(
        user_id,
        f"✅ *Платеж успешно получен!*\n\n"
        f"💎 *Premium активирован на {days} дней!*\n\n"
        f"🎉 Спасибо за покупку!\n"
        f"🔥 Наслаждайтесь полным доступом к Velvet!\n\n"
        f"👉 Перейти к чату: {SITE_URL}",
        parse_mode="Markdown"
    )
    
    try:
        bot.send_message(
            ADMIN_ID,
            f"💰 *Новый платеж!*\n"
            f"Пользователь: {user_id}\n"
            f"Тариф: {PLANS[plan_key]['label']}\n"
            f"Сумма: {message.successful_payment.total_amount} Stars\n"
            f"ID: {message.successful_payment.telegram_payment_charge_id}"
        )
    except:
        pass

@bot.message_handler(commands=['premium'])
def premium_cmd(message):
    show_premium_plans(message.chat.id)

@bot.message_handler(commands=['status'])
def status_cmd(message):
    user_id = message.chat.id
    if user_id in premium_users:
        expiry = premium_users[user_id]
        remaining = (expiry - int(time.time())) / 86400
        bot.send_message(user_id, f"✅ Premium активен!\nОсталось: {int(remaining)} дней")
    else:
        bot.send_message(user_id, "⛔ У вас нет Premium.\n/premium для покупки")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.send_message(message.chat.id, f"ℹ️ Посетите сайт: {SITE_URL}")

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if str(message.from_user.id) == ADMIN_ID:
        active = len([u for u, exp in premium_users.items() if exp > time.time()])
        bot.send_message(message.chat.id, f"✅ Админ-панель:\nАктивных Premium: {active}")
    else:
        bot.send_message(message.chat.id, "❌ Доступ запрещен")

@app.route('/')
def index():
    return "Velvet Bot is running (Stars payments)"

bot.remove_webhook()
bot.set_webhook(url=f"{RENDER_URL}/webhook/{TOKEN}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))
