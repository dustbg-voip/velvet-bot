import os
import telebot
from telebot import types
from flask import Flask, request, jsonify
import time
import requests
import secrets

TOKEN = "8757264129:AAFX4VI8n4MQ9k7mBl9YmsbOF0Nq3eDbqgw"
SITE_URL = "https://glafira-ai.ru/nsfw/promo.html"
AUTH_URL = "https://glafira-ai.ru/nsfw/auth.html"
RENDER_URL = "https://velvet-bot-lewg.onrender.com"
ADMIN_ID = "8172285744"
API_URL = "https://glafira-ai.ru/living-api"

PLANS = {
    "1month": {"label": "Premium - 1 month", "price": 100, "days": 30},
    "3months": {"label": "Premium - 3 months", "price": 250, "days": 90},
    "1year": {"label": "Premium - 1 year", "price": 800, "days": 365},
}

bot = telebot.TeleBot(TOKEN)
def notify_admin(message):
    """Отправляет уведомление админу"""
    try:
        bot.send_message(
            ADMIN_ID,
            message,
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Notify error: {e}")

app = Flask(__name__)

@app.route(f'/webhook/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return jsonify({'ok': True})
    return jsonify({'ok': False}), 403

def activate_premium_on_server(user_id, days):
    try:
        response = requests.post(
            f"{API_URL}/activate-premium",
            json={"user_id": f"tg_{user_id}", "days": days},
            timeout=10
        )
        if response.status_code != 200:
            return None
        
        token_response = requests.post(
            f"{API_URL}/generate-token",
            json={"user_id": f"tg_{user_id}", "days": days},
            timeout=10
        )
        if token_response.status_code == 200:
            token_data = token_response.json()
            return token_data.get("access_token")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def show_premium_plans(chat_id):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("1 month - 100 Stars", callback_data="buy_1month"),
        types.InlineKeyboardButton("3 months - 250 Stars", callback_data="buy_3months"),
        types.InlineKeyboardButton("1 year - 800 Stars", callback_data="buy_1year")
    )
    bot.send_message(
        chat_id,
        f"*Premium Plans*\n\n"
        f"1 month: 100 Stars\n"
        f"3 months: 250 Stars (save 17%)\n"
        f"1 year: 800 Stars (save 33%)\n\n"
        f"All plans include:\n"
        f"- Custom characters\n"
        f"- Unlimited messages\n"
        f"- Full access",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

def send_invoice_premium(chat_id, plan_key):
    plan = PLANS[plan_key]
    prices = [types.LabeledPrice(label=plan["label"], amount=plan["price"])]
    try:
        bot.send_invoice(
            chat_id=chat_id,
            title="Velvet Premium",
            description=f"Access for {plan['days']} days",
            invoice_payload=f"premium_{plan_key}_{chat_id}_{int(time.time())}",
            provider_token="",
            currency="XTR",
            prices=prices,
            start_parameter="premium_subscription"
        )
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False

@bot.message_handler(commands=['start'])
def start(message):
    # Уведомляем админа о новом пользователе
    user_info = f"*New user!*\n"
    user_info += f"ID: {message.from_user.id}\n"
    user_info += f"Name: {message.from_user.first_name or 'Unknown'}\n"
    user_info += f"Username: @{message.from_user.username or 'none'}"
    notify_admin(user_info)
    
    args = message.text.split()
    if len(args) > 1 and args[1] == "premium":
        show_premium_plans(message.chat.id)
        return
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("Open Website", url=SITE_URL))
    keyboard.add(types.InlineKeyboardButton("Get Premium", callback_data="show_plans"))
    
    bot.send_message(
        message.chat.id,
        f"*Welcome to Velvet!*\n\n"
        f"Chat with AI companions who understand you.\n\n"
        f"*Free:* 8 characters, 30 msg/day\n"
        f"*Premium:* Custom characters, unlimited\n\n"
        f"Visit: {SITE_URL}",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "show_plans":
        show_premium_plans(call.message.chat.id)
        bot.answer_callback_query(call.id)
    elif call.data.startswith("buy_"):
        plan_key = call.data.replace("buy_", "")
        if plan_key in PLANS:
            send_invoice_premium(call.message.chat.id, plan_key)
        bot.answer_callback_query(call.id)

@bot.pre_checkout_query_handler(func=lambda query: True)
def pre_checkout(query):
    try:
        bot.answer_pre_checkout_query(query.id, ok=True)
    except Exception as e:
        bot.answer_pre_checkout_query(query.id, ok=False, error_message=str(e))

@bot.message_handler(content_types=['successful_payment'])
def successful_payment(message):
    user_id = message.from_user.id
    payload = message.successful_payment.invoice_payload
    
    plan_key = "1month"
    for key in PLANS:
        if key in payload:
            plan_key = key
            break
    
    days = PLANS[plan_key]["days"]
    access_token = activate_premium_on_server(user_id, days)
    
    if access_token:
        bot.send_message(
            user_id,
            f"*Payment received!*\n\n"
            f"Premium activated for {days} days!\n\n"
            f"*Your credentials:*\n"
            f"Premium ID: `tg_{user_id}`\n"
            f"Access Token: `{access_token}`\n\n"
            f"*Login:*\n"
            f"1. Visit: {AUTH_URL}\n"
            f"2. Enter Premium ID and Token\n"
            f"3. Enjoy full access!\n\n"
            f"*Keep your token safe!*",
            parse_mode="Markdown"
        )
    else:
        bot.send_message(
            user_id,
            f"Payment received! Activation in progress...\n"
            f"Your ID: tg_{user_id}"
        )
    
    try:
        bot.send_message(
            ADMIN_ID,
            f"*New payment!*\n"
            f"User: {user_id}\n"
            f"Plan: {PLANS[plan_key]['label']}\n"
            f"Amount: {message.successful_payment.total_amount} Stars"
        )
    except:
        pass

@bot.message_handler(commands=['simulate_1month'])
def simulate_1month(message):
    if str(message.from_user.id) != ADMIN_ID:
        bot.send_message(message.chat.id, "Access denied")
        return
    notify_admin(f"*Simulation command*\nFrom: {message.from_user.id}\nCommand: {message.text}")
    args = message.text.split()
    user_id = args[1] if len(args) > 1 else str(message.from_user.id)
    access_token = activate_premium_on_server(user_id, 30)
    if access_token:
        bot.send_message(
            message.chat.id,
            f"*SIMULATION: 1 Month*\n"
            f"User: tg_{user_id}\n"
            f"Token: `{access_token}`\n"
            f"Status: Activated",
            parse_mode="Markdown"
        )
    else:
        bot.send_message(message.chat.id, "Failed")

@bot.message_handler(commands=['simulate_3months'])
def simulate_3months(message):
    if str(message.from_user.id) != ADMIN_ID:
        bot.send_message(message.chat.id, "Access denied")
        return
    notify_admin(f"*Simulation command*\nFrom: {message.from_user.id}\nCommand: {message.text}")
    args = message.text.split()
    user_id = args[1] if len(args) > 1 else str(message.from_user.id)
    access_token = activate_premium_on_server(user_id, 90)
    if access_token:
        bot.send_message(
            message.chat.id,
            f"*SIMULATION: 3 Months*\n"
            f"User: tg_{user_id}\n"
            f"Token: `{access_token}`\n"
            f"Status: Activated",
            parse_mode="Markdown"
        )
    else:
        bot.send_message(message.chat.id, "Failed")

@bot.message_handler(commands=['simulate_1year'])
def simulate_1year(message):
    if str(message.from_user.id) != ADMIN_ID:
        bot.send_message(message.chat.id, "Access denied")
        return
    notify_admin(f"*Simulation command*\nFrom: {message.from_user.id}\nCommand: {message.text}")
    args = message.text.split()
    user_id = args[1] if len(args) > 1 else str(message.from_user.id)
    access_token = activate_premium_on_server(user_id, 365)
    if access_token:
        bot.send_message(
            message.chat.id,
            f"*SIMULATION: 1 Year*\n"
            f"User: tg_{user_id}\n"
            f"Token: `{access_token}`\n"
            f"Status: Activated",
            parse_mode="Markdown"
        )
    else:
        bot.send_message(message.chat.id, "Failed")

@bot.message_handler(commands=['premium'])
def premium_cmd(message):
    show_premium_plans(message.chat.id)

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if str(message.from_user.id) == ADMIN_ID:
        bot.send_message(
            message.chat.id,
            f"*Admin Commands:*\n"
            f"/simulate_1month [user_id]\n"
            f"/simulate_3months [user_id]\n"
            f"/simulate_1year [user_id]",
            parse_mode="Markdown"
        )
    else:
        bot.send_message(message.chat.id, "Access denied")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.send_message(message.chat.id, f"Visit: {SITE_URL}")

@app.route('/')
def index():
    return "Velvet Bot is running"

bot.remove_webhook()
bot.set_webhook(url=f"{RENDER_URL}/webhook/{TOKEN}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))
