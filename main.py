import telebot
from telebot import types
import os
import threading
from flask import Flask

# ===== بدّل هاي القيم =====
TOKEN = "8795207533:AAGgPAbOSzuWjydIaVmhVsP4pFopn0oa854 @BotFather"
CHANNEL_ID = -1003937781403 # ايدي القناة، لازم يبدي بـ -100
ADMIN_ID = 6149866829 # ايدي حسابك، تجيبه من @userinfobot
# ==========================

bot = telebot.TeleBot(TOKEN)
user_states = {}
temp_products = {}
products = {
    "drinks": [],
    "cake": [],
    "cosmetics": []
}

# سيرفر Flask حتى ما يطفي البوت على الاستضافة
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("🥤 المشروبات", callback_data="cat_drinks")
    btn2 = types.InlineKeyboardButton("🍰 الكيك", callback_data="cat_cake")
    btn3 = types.InlineKeyboardButton("💄 الكوزمتك", callback_data="cat_cosmetics")
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, "اهلاً بيك! اختار القسم:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('cat_'))
def show_category(call):
    category = call.data.split('_')[1]
    if not products[category]:
        bot.answer_callback_query(call.id, "ماكو منتجات بهذا القسم حالياً")
        return

    for product in products[category]:
        caption = f"📌 {product['name']}\n💰 السعر: {product['price']} دينار"
        bot.send_photo(call.message.chat.id, product['photo'], caption=caption)
    bot.answer_callback_query(call.id)

@bot.channel_post_handler(content_types=['photo'])
def handle_channel_photo(message):
    if str(message.chat.id)!= str(CHANNEL_ID):
        return

    file_id = message.photo[-1].file_id
    temp_products[ADMIN_ID] = {"photo": file_id}
    user_states[ADMIN_ID] = "choosing_category"

    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("🥤 المشروبات", callback_data="add_drinks")
    btn2 = types.InlineKeyboardButton("🍰 الكيك", callback_data="add_cake")
    btn3 = types.InlineKeyboardButton("💄 الكوزمتك", callback_data="add_cosmetics")
    btn4 = types.InlineKeyboardButton("🗑️ الغاء", callback_data="add_cancel")
    markup.add(btn1, btn2, btn3, btn4)

    bot.send_message(ADMIN_ID, "وصل منتج جديد من القناة 👆\nاختار القسم ماله:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('add_'))
def handle_add_category(call):
    if call.from_user.id!= ADMIN_ID:
        bot.answer_callback_query(call.id, "انت مو الادمن")
        return

    action = call.data.split('_')[1]
    if action == "cancel":
        user_states.pop(ADMIN_ID, None)
        temp_products.pop(ADMIN_ID, None)
        bot.edit_message_text("تم الغاء الاضافة", call.message.chat.id, call.message.message_id)
        return

    temp_products[ADMIN_ID]["category"] = action
    user_states[ADMIN_ID] = "waiting_name"
    bot.edit_message_text("تمام، هسه دزلي اسم المنتج:", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "waiting_name")
def get_product_name(message):
    if message.from_user.id!= ADMIN_ID:
        return
    temp_products[ADMIN_ID]["name"] = message.text
    user_states[ADMIN_ID] = "waiting_price"
    bot.send_message(message.chat.id, "زين، هسه دزلي السعر بالدينار، رقم بس:")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "waiting_price")
def get_product_price(message):
    if message.from_user.id!= ADMIN_ID:
        return

    if not message.text.isdigit():
        bot.send_message(message.chat.id, "السعر لازم يكون رقم فقط، عيد دز السعر:")
        return

    category = temp_products[ADMIN_ID]["category"]
    products[category].append({
        "photo": temp_products[ADMIN_ID]["photo"],
        "name": temp_products[ADMIN_ID]["name"],
        "price": message.text
    })

    user_states.pop(ADMIN_ID, None)
    temp_products.pop(ADMIN_ID, None)
    bot.send_message(message.chat.id, "تم اضافة المنتج بنجاح ✅")

threading.Thread(target=run_flask).start()
print("Bot is running...")
bot.polling(none_stop=True)
