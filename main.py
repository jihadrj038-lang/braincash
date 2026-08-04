
import os, http.server, socketserver, threading
threading.Thread(target=lambda: socketserver.TCPServer(("", int(os.environ.get("PORT", 8080))), http.server.SimpleHTTPRequestHandler).serve_forever(), daemon=True).start()

import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- আপনার তথ্যসমূহ ---
BOT_TOKEN = "8136759671:AAHuCTZnvot7VY9r6t1JXM99uqHA9VX1Iig"
ADMIN_ID = 7469931517
BKASH_NUMBER = "01965291171"
REFERRAL_BONUS = 10  # প্রতি রেফারে কত টাকা পাবে

# --- দেশ ও দামের তালিকা ---
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

# --- ডেটাবেজ (JSON ফাইল) ---
DATA_FILE = "user_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_user_balance(user_id):
    data = load_data()
    return data.get(str(user_id), {}).get("balance", 0)

def update_user_balance(user_id, amount):
    data = load_data()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {"balance": 0, "referred_by": None}
    data[uid]["balance"] += amount
    save_data(data)

# --- /start কমান্ড (রেফারেল লজিকসহ) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = load_data()
    uid = str(user.id)
    
    # নতুন ইউজার হলে ডাটাবেজে যুক্ত করা
    if uid not in data:
        data[uid] = {"balance": 0, "referred_by": None}
        
        # রেফারেল চেক
        if context.args:
            referrer_id = context.args[0]
            if referrer_id != uid and referrer_id in data:
                data[uid]["referred_by"] = referrer_id
                data[referrer_id]["balance"] += REFERRAL_BONUS
                try:
                    await context.bot.send_message(
                        chat_id=int(referrer_id),
                        text=f"🎉 **রেফারেল বোনাস!**\nএকজন নতুন ইউজার আপনার লিংকে জয়েন করেছেন। আপনি ৳{REFERRAL_BONUS} বোনাস পেয়েছেন!"
                    )
                except:
                    pass
        save_data(data)

    balance = data[uid]["balance"]
    bot_username = (await context.bot.get_me()).username
    refer_link = f"https://t.me/{bot_username}?start={user.id}"

    text = (
        f"হ্যালো {user.first_name}! 👋\n\n"
        f"🤖 **GlobalNumBD** বটে আপনাকে স্বাগতম।\n"
        f"💰 **আপনার বর্তমান ব্যালেন্স:** ৳{balance}\n\n"
        f"🔗 **আপনার রেফারেল লিংক:**\n`{refer_link}`\n"
        f"*(বন্ধুদের ইনভাইট করে প্রতি রেফারে ৳{REFERRAL_BONUS} বোনাস পান!)*"
    )

    keyboard = [
        [InlineKeyboardButton("📱 নম্বর কিনুন (Buy Number)", callback_data='buy_number')],
        [InlineKeyboardButton("💳 ডিপোজিট / ব্যালেন্স অ্যাড", callback_data='deposit')],
        [InlineKeyboardButton("🧑‍💻 সাপোর্ট (Support)", callback_data='support')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# --- বাটন হ্যান্ডলার ---
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

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
        await query.edit_message_text("একটি দেশ নির্বাচন করুন:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith('select_'):
        service_key = query.data.replace('select_', '')
        service = SERVICES[service_key]
        user_balance = get_user_balance(user_id)

        if user_balance < service['price']:
            text = (
                f"❌ **প্যাকেজের মূল্য:** ৳{service['price']}\n"
                f"💳 **আপনার ব্যালেন্স:** ৳{user_balance}\n\n"
                f"আপনার পর্যাপ্ত ব্যালেন্স নেই! নম্বর কিনতে আগে একাউন্টে টাকা রিচার্জ করুন।"
            )
            keyboard = [[InlineKeyboardButton("💳 ডিপোজিট করুন", callback_data='deposit')], [InlineKeyboardButton("🔙 মেনু", callback_data='main_menu')]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            # ব্যালেন্স কেটে নেওয়া
            update_user_balance(user_id, -service['price'])
            
            # এডমিনকে জানানো
            admin_text = (
                f"🛍️ **নতুন নাম্বার অর্ডার এসেছে!**\n\n"
                f"👤 ইউজার: {query.from_user.full_name} (@{query.from_user.username})\n"
                f"🆔 User ID: `{user_id}`\n"
                f"📦 দেশ: {service['name']}\n"
                f"💰 কেটে নেওয়া হয়েছে: ৳{service['price']}\n\n"
                f"📌 **কাস্টমারকে নম্বর দিতে টাইপ করুন:**\n`/sendnum {user_id} আপনার_নম্বর`"
            )
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode='Markdown')

            await query.edit_message_text(
                f"✅ **অর্ডার সফল হয়েছে!**\n"
                f"আপনার একাউন্ট থেকে ৳{service['price']} কেটে নেওয়া হয়েছে।\n\n"
                f"⏳ এডমিন দ্রুত আপনাকে নম্বর ডেলিভারি দিচ্ছে, দয়া করে অপেক্ষা করুন...",
                parse_mode='Markdown'
            )

    elif query.data == 'deposit':
        text = (
            f"💳 **টাকা রিচার্জ পদ্ধতি:**\n\n"
            f"বিকাশ পার্সোনাল: `{BKASH_NUMBER}` (Send Money)\n\n"
            f"⚠️ টাকা পাঠানোর পর সেন্ডার নম্বর ও Transaction ID লিখে সরাসরি এই চ্যাটে মেসেজ পাঠান।"
        )
        keyboard = [[InlineKeyboardButton("🔙 প্রধান মেনু", callback_data='main_menu')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif query.data == 'support':
        await query.edit_message_text(
            "🧑‍💻 যেকোনো প্রয়োজনে এডমিনের সাথে যোগাযোগ করুন:\nএডমিন আইডি: @jihad1171",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 প্রধান মেনু", callback_data='main_menu')]])
        )

    elif query.data == 'request_otp':
        await query.answer("⏳ ওটিপি কোড চেক করা হচ্ছে, কোড আসা মাত্রই এখানে মেসেজ আসবে...", show_alert=True)

    elif query.data == 'main_menu':
        balance = get_user_balance(user_id)
        keyboard = [
            [InlineKeyboardButton("📱 নম্বর কিনুন", callback_data='buy_number')],
            [InlineKeyboardButton("💳 ডিপোজিট / ব্যালেন্স অ্যাড", callback_data='deposit')],
            [InlineKeyboardButton("🧑‍💻 সাপোর্ট", callback_data='support')]
        ]
        await query.edit_message_text(f"প্রধান মেনু:\n💰 বর্তমান ব্যালেন্স: ৳{balance}", reply_markup=InlineKeyboardMarkup(keyboard))

# --- ডিপোজিট মেসেজ প্রসেস ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_msg = update.message.text

    admin_text = (
        f"🚨 **নতুন ডিপোজিট মেসেজ!**\n\n"
        f"👤 ইউজার: {user.full_name} (@{user.username})\n"
        f"🆔 User ID: `{user.id}`\n"
        f"💬 মেসেজ:\n`{user_msg}`\n\n"
        f"📌 **ব্যালেন্স দিতে কমান্ড ব্যবহার করুন:**\n`/addbalance {user.id} পরিমাণ`"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode='Markdown')
    await update.message.reply_text("✅ আপনার মেসেজটি এডমিনের কাছে পাঠানো হয়েছে! ভেরিফাই করে ব্যালেন্স যোগ করে দেওয়া হবে।")

# --- এডমিন কমান্ডস ---
async def add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        target_user_id = context.args[0]
        amount = float(context.args[1])
        update_user_balance(target_user_id, amount)

        await update.message.reply_text(f"✅ User ID {target_user_id}-এ ৳{amount} সফলভাবে যোগ করা হয়েছে!")
        await context.bot.send_message(chat_id=int(target_user_id), text=f"🎉 আপনার একাউন্টে ৳{amount} ব্যালেন্স যোগ করা হয়েছে!")
    except:
        await update.message.reply_text("❌ ভুল ফরম্যাট! লিখুন:\n`/addbalance <USER_ID> <পরিমাণ>`")

async def send_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        target_user_id = context.args[0]
        number_to_send = " ".join(context.args[1:])

        msg = (
            f"🎉 **আপনার অর্ডারকৃত নম্বর:**\n"
            f"`{number_to_send}`\n\n"
            f"📌 *(নাম্বারের ওপর চাপ দিলেই অটো কপি হয়ে যাবে)*"
        )
        keyboard = [[InlineKeyboardButton("📩 Get OTP / কোড পান", callback_data='request_otp')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(chat_id=int(target_user_id), text=msg, reply_markup=reply_markup, parse_mode='Markdown')
        await update.message.reply_text(f"✅ User ID {target_user_id}-এ সফলভাবে নম্বর পাঠানো হয়েছে!")
    except:
        await update.message.reply_text("❌ ভুল ফরম্যাট! লিখুন:\n`/sendnum <USER_ID> <নম্বর>`")

async def send_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        target_user_id = context.args[0]
        otp_code = context.args[1]

        msg = f"🔑 **আপনার OTP কোড:** `{otp_code}`\n\n*(কোডের ওপর চাপ দিলে কপি হয়ে যাবে)*"
        await context.bot.send_message(chat_id=int(target_user_id), text=msg, parse_mode='Markdown')
        await update.message.reply_text(f"✅ User ID {target_user_id}-এ OTP পাঠানো হয়েছে!")
    except:
        await update.message.reply_text("❌ ভুল ফরম্যাট! লিখুন:\n`/sendotp <USER_ID> <OTP>`")

async def users_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        data = load_data()
        await update.message.reply_text(f"📊 আপনার বটে মোট ইউজার সংখ্যা: {len(data)} জন")

# --- মূল রানার ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sendnum", send_number))
    app.add_handler(CommandHandler("sendotp", send_otp))
    app.add_handler(CommandHandler("addbalance", add_balance))
    app.add_handler(CommandHandler("users", users_count))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running successfully...")
    app.run_polling()
