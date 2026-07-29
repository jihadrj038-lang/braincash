
import os, http.server, socketserver, threading
threading.Thread(target=lambda: socketserver.TCPServer(("", int(os.environ.get("PORT", 8080))), http.server.SimpleHTTPRequestHandler).serve_forever(), daemon=True).start()

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- আপনার তথ্যাসমূহ ---
BOT_TOKEN = "8136759671:AAHuCTZnvot7VY9r6t1JXM99uqHA9VX1Iig" # আপনার পুরো বট টোকেনটি এখানে নিশ্চিত করুন
ADMIN_ID = 7469931517
BKASH_NUMBER = "01965291171"

# --- দেশ ও দামের তালিকা (২০টি দেশ) ---
SERVICES = {
    "wa_uk":    {"name": "🇬🇧 UK", "price": 420},
    "wa_qa":    {"name": "🇶🇦 Qatar", "price": 420},
    "wa_eg":    {"name": "🇪🇬 Egypt", "price": 350},
    "wa_om":    {"name": "🇴🇲 Oman", "price": 390},
    "wa_kw":    {"name": "🇰🇼 Kuwait", "price": 400},
    "wa_bh":    {"name": "🇧🇭 Bahrain", "price": 350},
    "wa_my":    {"name": "🇲🇾 Malaysia", "price": 420},
    "wa_sg":    {"name": "🇸🇬 Singapore", "price": 450},
    "wa_sa":    {"name": "🇸🇦 Saudi Arabia", "price": 450},
    "wa_ae":    {"name": "🇦🇪 UAE", "price": 450},
    "wa_usa":   {"name": "🇺🇸 USA", "price": 380},
    "wa_ca":    {"name": "🇨🇦 Canada", "price": 410},
    "wa_de":    {"name": "🇩🇪 Germany", "price": 480},
    "wa_fr":    {"name": "🇫🇷 France", "price": 490},
    "wa_it":    {"name": "🇮🇹 Italy", "price": 460},
    "wa_ru":    {"name": "🇷🇺 Russia", "price": 350},
    "wa_au":    {"name": "🇦🇺 Australia", "price": 520},
    "wa_tr":    {"name": "🇹🇷 Turkey", "price": 390},
    "wa_id":    {"name": "🇮🇩 Indonesia", "price": 360},
    "wa_jp":    {"name": "🇯🇵 Japan", "price": 580},
}

# --- ইউজার সংখ্যা সেভ করার জন্য সিস্টেমে যুক্ত কোড ---
USER_FILE = "users.txt"

def save_user(user_id):
    users = set()
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            users = set(f.read().splitlines())
    if str(user_id) not in users:
        with open(USER_FILE, "a") as f:
            f.write(f"{user_id}\n")

def get_user_count():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            return len(set(f.read().splitlines()))
    return 0

async def users_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        count = get_user_count()
        await update.message.reply_text(f"📊 আপনার বটে মোট ইউজার সংখ্যা: {count} জন")

# --- /start কমান্ড ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user.id)
    
    keyboard = [
        [InlineKeyboardButton("📱 নম্বর কিনুন (Buy Number)", callback_data='buy_number')],
        [InlineKeyboardButton("🧑‍💻 সাপোর্ট (Support)", callback_data='support')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"হ্যালো {user.first_name}! 👋\n\n**GlobalNumBD** বটে আপনাকে স্বাগতম। নিচে থেকে সার্ভিস বেছে নিন:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# --- বাটন ক্লিক হ্যান্ডলার ---
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'buy_number':
        keyboard = []
        items = list(SERVICES.items())

        for i in range(0, len(items), 2):
            row = []
            key1, item1 = items[i]
            row.append(InlineKeyboardButton(f"{item1['name']} - ৳{item1['price']}", callback_data=f"select_{key1}"))

            if i + 1 < len(items):
                key2, item2 = items[i+1]
                row.append(InlineKeyboardButton(f"{item2['name']} - ৳{item2['price']}", callback_data=f"select_{key2}"))

            keyboard.append(row)

        keyboard.append([InlineKeyboardButton("🔙 প্রধান মেনু", callback_data='main_menu')])
        await query.edit_message_text("একটি দেশ/সার্ভিস নির্বাচন করুন:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith('select_'):
        service_key = query.data.replace('select_', '')
        service = SERVICES[service_key]
        context.user_data['pending_order'] = service

        text = (
            f"🎯 **অর্ডার বিবরণ:**\n"
            f"সার্ভিস: {service['name']}\n"
            f"মূল্য: ৳{service['price']}\n\n"
            f"💳 **পেমেন্ট নির্দেশিকা:**\n"
            f"বিকাশ পার্সোনাল: `{BKASH_NUMBER}` (Send Money)\n\n"
            f"⚠️ **টাকা পাঠানোর পর সেন্ডার নম্বর ও Transaction ID লিখে সরাসরি এই চ্যাটে মেসেজ পাঠান।**"
        )
        await query.edit_message_text(text, parse_mode='Markdown')

    elif query.data == 'support':
        await query.edit_message_text(
            "🧑‍💻 যেকোনো প্রয়োজনে এডমিনের সাথে যোগাযোগ করুন:\nএডমিন আইডি: @jihad1171",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 প্রধান মেনু", callback_data='main_menu')]])
        )

    elif query.data == 'main_menu':
        keyboard = [
            [InlineKeyboardButton("📱 নম্বর কিনুন", callback_data='buy_number')],
            [InlineKeyboardButton("🧑‍💻 সাপোর্ট", callback_data='support')]
        ]
        await query.edit_message_text("প্রধান মেনু:", reply_markup=InlineKeyboardMarkup(keyboard))

# --- ইউজার মেসেজ রিসিভ ও এডমিনকে নোটিফিকেশন ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    pending_order = context.user_data.get('pending_order')

    if pending_order:
        user_msg = update.message.text
        admin_text = (
            f"🚨 **নতুন পেমেন্ট রিকোয়েস্ট এসেছে!**\n\n"
            f"👤 ইউজার: {user.full_name} (@{user.username})\n"
            f"🆔 User ID: `{user.id}`\n"
            f"📦 প্রোডাক্ট: {pending_order['name']}\n"
            f"💰 দাম: ৳{pending_order['price']}\n"
            f"💬 কাস্টমারের পেমেন্ট ডিটেইলস:\n`{user_msg}`\n\n"
            f"📌 **কাস্টমারকে নম্বর দিতে নিচে পাঠান:**\n`/sendnum {user.id} আপনার_নম্বর`"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode='Markdown')
        await update.message.reply_text("✅ আপনার পেমেন্ট তথ্য জমা নেওয়া হয়েছে! এডমিন ভেরিফাই করে দ্রুত আপনাকে নম্বর পাঠাবে।")
        context.user_data['pending_order'] = None
    else:
        await update.message.reply_text("অর্ডার শুরু করতে /start লিখে প্রেস করুন।")

# --- এডমিন কমান্ড: কাস্টমারকে নম্বর পাঠানো ---
async def send_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        target_user_id = context.args[0]
        number_to_send = " ".join(context.args[1:])

        msg = f"🎉 **আপনার অর্ডারকৃত নম্বর:**\n`{number_to_send}`\n\nOTP কোডের জন্য অপেক্ষা করুন, আসা মাত্রই পাঠানো হবে।"
        await context.bot.send_message(chat_id=target_user_id, text=msg, parse_mode='Markdown')
        await update.message.reply_text(f"✅ User ID {target_user_id}-এ সফলভাবে নম্বর পাঠানো হয়েছে!")
    except Exception as e:
        await update.message.reply_text("❌ ভুল ফরম্যাট! সঠিকভাবে লিখুন:\n`/sendnum <USER_ID> <নম্বর>`")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sendnum", send_number))
    app.add_handler(CommandHandler("users", users_count))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running successfully...")
    app.run_polling()
