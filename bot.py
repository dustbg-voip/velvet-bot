import os
import telebot
from telebot import types
from flask import Flask, request, jsonify
import time
import requests

TOKEN = "8757264129:AAFX4VI8n4MQ9k7mBl9YmsbOF0Nq3eDbqgw"
SITE_URL = "https://glafira-ai.ru/nsfw/promo.html"
AUTH_URL = "https://glafira-ai.ru/nsfw/auth.html"
RENDER_URL = "https://velvet-bot-lewg.onrender.com"
ADMIN_ID = "8172285744"
API_URL = "https://glafira-ai.ru/living-api"

# Пакеты корон
CROWN_PACKS = {
    "10": {"crowns": 10, "stars": 29, "label": "Starter"},
    "50": {"crowns": 50, "stars": 99, "label": "Standard"},
    "200": {"crowns": 200, "stars": 299, "label": "Premium"},
    "500": {"crowns": 500, "stars": 599, "label": "Ultimate"},
}

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

def notify_admin(message):
    try:
        bot.send_message(ADMIN_ID, message, parse_mode="Markdown")
    except:
        pass

def add_crowns_to_user(user_id, crowns):
    try:
        response = requests.post(
            f"{API_URL}/add-crowns",
            json={"user_id": f"tg_{user_id}", "amount": crowns},
            timeout=10
        )
        return response.status_code == 200
    except:
        return False

@bot.message_handler(commands=['start'])
def start(message):
    args = message.text.split()
    
    if len(args) > 1 and args[1].startswith("buy_"):
        pack_key = args[1].replace("buy_", "")
        if pack_key in CROWN_PACKS:
            show_crown_pack(message.chat.id, pack_key)
            return
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("Open Website", url=SITE_URL))
    keyboard.add(types.InlineKeyboardButton("Buy Crowns", callback_data="show_packs"))
    
    notify_admin(f"*New user!*\nID: {message.from_user.id}\nName: {message.from_user.first_name or 'Unknown'}\nUsername: @{message.from_user.username or 'none'}")
    
    bot.send_message(
        message.chat.id,
        f"*Welcome to Velvet!*\n\n"
        f"Chat with AI companions who understand you.\n\n"
        f"*Free:* 3 messages/day\n"
        f"*Crowns:* 1 Crown = 1 message\n\n"
        f"Visit: {SITE_URL}",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

def show_crown_packs(chat_id):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for key, pack in CROWN_PACKS.items():
        keyboard.add(types.InlineKeyboardButton(
            f"👑 {pack['crowns']} Crowns — {pack['stars']} Stars ({pack['label']})",
            callback_data=f"buy_{key}"
        ))
    
    bot.send_message(
        chat_id,
        f"👑 *Buy Crowns*\n\n"
        f"1 Crown = 1 message\n\n"
        f"Choose a pack:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

def show_crown_pack(chat_id, pack_key):
    pack = CROWN_PACKS[pack_key]
    prices = [types.LabeledPrice(label=f"{pack['crowns']} Crowns", amount=pack['stars'])]
    
    bot.send_invoice(
        chat_id=chat_id,
        title=f"👑 {pack['crowns']} Crowns",
        description=f"{pack['label']} pack: {pack['crowns']} messages",
        invoice_payload=f"crowns_{pack_key}_{chat_id}_{int(time.time())}",
        provider_token="",
        currency="XTR",
        prices=prices,
        start_parameter="buy_crowns"
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "show_packs":
        show_crown_packs(call.message.chat.id)
        bot.answer_callback_query(call.id)
    
    elif call.data.startswith("buy_"):
        pack_key = call.data.replace("buy_", "")
        if pack_key in CROWN_PACKS:
            show_crown_pack(call.message.chat.id, pack_key)
        bot.answer_callback_query(call.id)

@bot.pre_checkout_query_handler(func=lambda query: True)
def pre_checkout(query):
    bot.answer_pre_checkout_query(query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def successful_payment(message):
    user_id = message.from_user.id
    payload = message.successful_payment.invoice_payload
    
    # Извлекаем pack_key из payload
    pack_key = "10"
    for key in CROWN_PACKS:
        if f"crowns_{key}_" in payload:
            pack_key = key
            break
    
    pack = CROWN_PACKS[pack_key]
    crowns = pack["crowns"]
    
    # Начисляем короны
    success = add_crowns_to_user(user_id, crowns)
    
    if success:
        bot.send_message(
            user_id,
            f"✅ *Payment received!*\n\n"
            f"👑 {crowns} Crowns added!\n\n"
            f"Your Crowns ID: tg_{user_id}\n"
            f"Login: {AUTH_URL}",
            parse_mode="Markdown"
        )
    else:
        bot.send_message(
            user_id,
            f"Payment received! Adding Crowns...\n"
            f"Your ID: tg_{user_id}",
            parse_mode="Markdown"
        )
    
    notify_admin(
        f"💰 *New payment!*\n"
        f"User: {user_id}\n"
        f"Pack: {pack['label']} ({crowns} Crowns)\n"
        f"Amount: {message.successful_payment.total_amount} Stars"
    )

@bot.message_handler(commands=['buy'])
def buy_cmd(message):
    show_crown_packs(message.chat.id)

@bot.message_handler(commands=['balance'])
def balance_cmd(message):
    try:
        response = requests.get(f"{API_URL}/crowns-balance/tg_{message.from_user.id}", timeout=5)
        data = response.json()
        if data.get('ok'):
            bot.send_message(message.chat.id, f"👑 Your Crowns: {data['crowns']}")
        else:
            bot.send_message(message.chat.id, "Error checking balance")
    except:
        bot.send_message(message.chat.id, "Server unavailable")

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if str(message.from_user.id) == ADMIN_ID:
        bot.send_message(message.chat.id, "✅ Admin access")
    else:
        bot.send_message(message.chat.id, "Access denied")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.send_message(
        message.chat.id,
        f"*Commands:*\n"
        f"/buy — Buy Crowns\n"
        f"/balance — Check Crowns balance\n"
        f"/help — Help\n\n"
        f"Visit: {SITE_URL}",
        parse_mode="Markdown"
    )

@app.route('/')
def index():
    return "Velvet Bot is running"

bot.remove_webhook()
bot.set_webhook(url=f"{RENDER_URL}/webhook/{TOKEN}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))
