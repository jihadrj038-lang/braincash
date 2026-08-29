
import os
import json
import logging
import subprocess
import sys
from threading import Thread

# প্রয়োজনীয় প্যাকেজ অটো ইনস্টল
required_packages = ["python-telegram-bot", "requests", "flask"]
for package in required_packages:
    try:
        __import__(package.replace("-", "_"))
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ================= Keep-Alive Web Server (Flask) =================
web_app = Flask('')

@web_app.route('/')
def home():
    return "Bot is alive and running!", 200

def run_server():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_server)
    t.daemon = True
    t.start()

# ================= Configuration =================
BOT_TOKEN = "8136759671:AAEjaJW1bVFz2AUpchXxoPns7vpw_6PrgSE"
ADMIN_ID = 7469931517
BKASH_NUMBER = "01965291171"
REFERRAL_BONUS = 10
REQUIRED_CHANNEL = "@FreeIncomeBD1171"  # বাধ্যতামূলক চ্যানেল

DATA_FILE = "user_data.json"
tg_app = None

# সার্ভিস লিস্ট
SERVICES = {
    "wa_usa":   {"name": "🇺🇸 USA (ইউএসএ)", "price": 380, "badge": "🔥 Hot"},
    "wa_uk":    {"name": "🇬🇧 UK (ইউকে)", "price": 420, "badge": "⚡ Fast"},
    "wa_sa":    {"name": "🇸🇦 Saudi Arabia", "price": 450, "badge": "⭐ Top"},
    "wa_ae":    {"name": "🇦🇪 UAE (দুবাই)", "price": 450, "badge": "⭐ Top"},
    "wa_qa":    {"name": "🇶🇦 Qatar (কাতার)", "price": 420, "badge": ""},
    "wa_om":    {"name": "🇴🇲 Oman (ওমান)", "price": 390, "badge": ""},
    "wa_kw":    {"name": "🇰🇼 Kuwait (কুয়েত)", "price": 400, "badge": ""},
    "wa_bh":    {"name": "🇧🇭 Bahrain (বাহরাইন)", "price": 350, "badge": ""},
    "wa_my":    {"name": "🇲🇾 Malaysia", "price": 420, "badge": ""},
    "wa_sg":    {"name": "🇸🇬 Singapore", "price": 450, "badge": ""},
    "wa_eg":    {"name": "🇪🇬 Egypt (মিশর)", "price": 350, "badge": ""},
    "wa_ca":    {"name": "🇨🇦 Canada (কানাডা)", "price": 410, "badge": ""},
    "wa_de":    {"name": "🇩🇪 Germany", "price": 480, "badge": ""},
    "wa_fr":    {"name": "🇫🇷 France", "price": 490, "badge": ""},
    "wa_it":    {"name": "🇮🇹 Italy", "price": 460, "badge": ""},
    "wa_ru":    {"name": "🇷🇺 Russia", "price": 350, "badge": ""},
    "wa_br":    {"name": "🇧🇷 Brazil (ব্রাজিল)", "price": 360, "badge": "🔥 Cheap"},
    "wa_in":    {"name": "🇮🇳 India (ইন্ডিয়া)", "price": 340, "badge": "🔥 Cheap"},
    "wa_tr":    {"name": "🇹🇷 Turkey (তুরস্ক)", "price": 390, "badge": ""},
    "wa_id":    {"name": "🇮🇩 Indonesia", "price": 360, "badge": ""},
}

# ================= Data Helper Functions =================
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_data(data):
    try:
        temp_file = f"{DATA_FILE}.tmp"
        with open(temp_file, "w") as f:
            json.dump(data, f, indent=4)
        os.replace(temp_file, DATA_FILE)
    except Exception as e:
        print(f"Error saving data: {e}")

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

# ================= Channel Membership Check =================
async def is_user_joined(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception:
        return True

async def send_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"⚠️ **বট ব্যবহার করতে আপনাকে আমাদের চ্যানেলে জয়েন হতে হবে!**\n\n"
        f"নিচের **'📢 চ্যানেলে জয়েন করুন'** বাটনে ক্লিক করে জয়েন হোন, তারপর **'✅ চেক করুন'** বাটনে চাপ দিন।"
    )
    keyboard = [
        [InlineKeyboardButton("📢 চ্যানেলে জয়েন করুন", url="https://t.me/FreeIncomeBD1171")],
        [InlineKeyboardButton("✅ চেক করুন", callback_data="check_joined")]
    ]
    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# ================= Telegram Bot Handlers =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if not await is_user_joined(context.bot, user.id):
        await send_join_request(update, context)
        return

    data = load_data()
    uid = str(user.id)
    
    if uid not in data:
        data[uid] = {"balance": 0, "referred_by": None}
        if context.args:
            referrer_id = str(context.args[0])
            if referrer_id != uid and referrer_id in data:
                data[uid]["referred_by"] = referrer_id
                data[referrer_id]["balance"] += REFERRAL_BONUS
                try:
                    await context.bot.send_message(
                        chat_id=int(referrer_id),
                        text=f"🎉 **রেফারেল পুরস্কার!**\nএকজন নতুন ইউজার আপনার লিংকে জয়েন করেছে! আপনি পেয়েছেন **৳{REFERRAL_BONUS}** বোনাস।"
                    )
                except Exception:
                    pass
        save_data(data)

    balance = data[uid]["balance"]
    bot_username = (await context.bot.get_me()).username
    refer_link = f"https://t.me/{bot_username}?start={user.id}"

    text = (
        f"👑 **GlobalNumBD - Premium Virtual Number Bot**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👋 **স্বাগতম, {user.first_name}!**\n\n"
        f"⚡ **কেন আমাদের সার্ভিস সেরা?**\n"
        f"✅ ১-৩ মিনিটে দ্রুত OTP ডেলিভারি\n"
        f"✅ ১০০% আসল ও ফ্রেশ নাম্বার\n"
        f"✅ যেকোনো সমস্যায় ইনস্ট্যান্ট সাপোর্ট\n\n"
        f"💰 **আপনার একাউন্ট ব্যালেন্স:** ৳{balance}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎁 **রেফার করে ফ্রি টাকা আয় করুন:**\n"
        f"আপনার রেফার লিংক শেয়ার করুন, প্রতি রেফারে পান **৳{REFERRAL_BONUS}** ইনস্ট্যান্ট!\n"
        f"🔗 `{refer_link}`"
    )

    keyboard = [
        [InlineKeyboardButton("📱 নম্বর কিনুন (Buy Number)", callback_data='buy_number')],
        [InlineKeyboardButton("💳 রিচার্জ / ডিপোজিট", callback_data='deposit'), InlineKeyboardButton("📊 আমার তথ্য", callback_data='my_info')],
        [InlineKeyboardButton("🎁 রেফার ও আয়", callback_data='refer_info'), InlineKeyboardButton("🧑‍💻 হেল্প ও সাপোর্ট", callback_data='support')]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == 'check_joined':
        if await is_user_joined(context.bot, user_id):
            await query.message.delete()
            await start(update, context)
        else:
            await query.answer("❌ আপনি এখনো চ্যানেলে জয়েন করেননি! দয়া করে চ্যানেলে জয়েন হয়ে আবার ট্রাই করুন।", show_alert=True)
        return

    if not await is_user_joined(context.bot, user_id):
        await send_join_request(update, context)
        return

    if query.data == 'buy_number':
        keyboard = []
        items = list(SERVICES.items())
        for i in range(0, len(items), 2):
            row = []
            key1, item1 = items[i]
            badge1 = f" [{item1['badge']}]" if item1['badge'] else ""
            row.append(InlineKeyboardButton(f"{item1['name']} - ৳{item1['price']}{badge1}", callback_data=f"select_{key1}"))
            
            if i + 1 < len(items):
                key2, item2 = items[i+1]
                badge2 = f" [{item2['badge']}]" if item2['badge'] else ""
                row.append(InlineKeyboardButton(f"{item2['name']} - ৳{item2['price']}{badge2}", callback_data=f"select_{key2}"))
            keyboard.append(row)
            
        keyboard.append([InlineKeyboardButton("🔙 প্রধান মেনু", callback_data='main_menu')])
        await query.edit_message_text(
            "🌍 **সবচেয়ে জনপ্রিয় দেশগুলোর লিস্ট:**\n"
            "নিচের যেকোনো একটি দেশে ক্লিক করে অর্ডার করুন:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    elif query.data.startswith('select_'):
        service_key = query.data.replace('select_', '')
        service = SERVICES[service_key]
        user_balance = get_user_balance(user_id)

        if user_balance < service['price']:
            text = (
                f"❌ **অপর্যাপ্ত ব্যালেন্স!**\n\n"
                f"📦 **প্যাকেজ:** {service['name']}\n"
                f"💵 **প্যাকেজ মূল্য:** ৳{service['price']}\n"
                f"💳 **আপনার বর্তমান ব্যালেন্স:** ৳{user_balance}\n\n"
                f"👉 নম্বর কিনতে আগে একাউন্ট রিচার্জ করুন।"
            )
            keyboard = [
                [InlineKeyboardButton("💳 এখনই রিচার্জ করুন", callback_data='deposit')],
                [InlineKeyboardButton("🔙 ব্যাকে যান", callback_data='buy_number')]
            ]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            update_user_balance(user_id, -service['price'])
            admin_text = (
                f"🛍️ **নতুন নম্বর অর্ডার এসেছে!**\n\n"
                f"👤 ইউজার: {query.from_user.full_name} (@{query.from_user.username})\n"
                f"🆔 User ID: `{user_id}`\n"
                f"📦 দেশ: {service['name']}\n"
                f"💰 কেটে নেওয়া হয়েছে: ৳{service['price']}\n\n"
                f"📌 **কাস্টমারকে নম্বর দিতে টাইপ করুন:**\n`/sendnum {user_id} আপনার_নম্বর`"
            )
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode='Markdown')
            await query.edit_message_text(
                f"✅ **অর্ডার কনফার্ম হয়েছে!**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📦 দেশ: {service['name']}\n"
                f"💰 খরচের পরিমাণ: ৳{service['price']}\n\n"
                f"⏳ **এডমিন আপনার নম্বর প্রসেস করছে...**\n"
                f"খুব দ্রুতই আপনাকে এই চ্যাটে নম্বর পাঠানো হবে।",
                parse_mode='Markdown'
            )

    elif query.data == 'deposit':
        text = (
            f"💳 **ইনস্ট্যান্ট ম্যানুয়াল বিকাশ ডিপোজিট**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📱 **বিকাশ পার্সোনাল নম্বর:** `{BKASH_NUMBER}`\n"
            f"📌 **অপশন:** Send Money (সেন্ড মানি)\n\n"
            f"📝 **টাকা পাঠানোর পর কি করবেন?**\n"
            f"টাকা পাঠানোর পর আপনি যে নম্বর থেকে টাকা পাঠিয়েছেন (**বিকাশ নম্বর**) এবং **TrxID (ট্রানজেকশন আইডি)** সরাসরি এই চ্যাটে লিখে পাঠান।\n\n"
            f"⚡ এডমিন ভেরিফাই করে ১-২ মিনিটে আপনার ব্যালেন্স যুক্ত করে দেবে!"
        )
        keyboard = [[InlineKeyboardButton("🔙 প্রধান মেনু", callback_data='main_menu')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif query.data == 'my_info':
        balance = get_user_balance(user_id)
        bot_username = (await context.bot.get_me()).username
        text = (
            f"👤 **আপনার প্রোফাইল তথ্য:**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 **User ID:** `{user_id}`\n"
            f"🏷️ **নাম:** {query.from_user.full_name}\n"
            f"💰 **বর্তমান ব্যালেন্স:** ৳{balance}\n\n"
            f"🔗 **রেফারেল লিংক:**\n`https://t.me/{bot_username}?start={user_id}`"
        )
        keyboard = [[InlineKeyboardButton("🔙 প্রধান মেনু", callback_data='main_menu')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif query.data == 'refer_info':
        bot_username = (await context.bot.get_me()).username
        refer_link = f"https://t.me/{bot_username}?start={user_id}"
        text = (
            f"🎁 **রেফার করে আনলিমিটেড ইনকাম করুন!**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"আপনার ইনভাইট লিংক ব্যবহার করে যে কেউ বটে জয়েন করলেই আপনি পাবেন **৳{REFERRAL_BONUS}** বোনাস!\n\n"
            f"🔗 **আপনার বিশেষ রেফার লিংক:**\n`{refer_link}`\n\n"
            f"📌 লিংকটি কপি করে বন্ধুদের বা মেসেঞ্জার গ্রুপে শেয়ার করুন।"
        )
        keyboard = [[InlineKeyboardButton("🔙 প্রধান মেনু", callback_data='main_menu')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif query.data == 'support':
        await query.edit_message_text(
            "🧑‍💻 **হেল্প ও কাস্টমার সাপোর্ট**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "যেকোনো প্রয়োজনে বা সমস্যার জন্য সরাসরি এডমিনের সাথে কথা বলুন:\n\n"
            "👨‍💻 **এডমিন আইডি:** @jihad1171\n"
            "⏰ **সার্ভিস টাইম:** ২৪ ঘন্টা সার্ভিস চালু!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 প্রধান মেনু", callback_data='main_menu')]]),
            parse_mode='Markdown'
        )

    elif query.data == 'request_otp':
        await query.answer("⏳ ওটিপি কোড চেক করা হচ্ছে, এডমিন কোড পাঠানোর সাথে সাথে আপনার কাছে চলে আসবে...", show_alert=True)

    elif query.data == 'main_menu':
        balance = get_user_balance(user_id)
        text = (
            f"🤖 **GlobalNumBD মেনু**\n\n"
            f"💰 **আপনার বর্তমান ব্যালেন্স:** ৳{balance}"
        )
        keyboard = [
            [InlineKeyboardButton("📱 নম্বর কিনুন (Buy Number)", callback_data='buy_number')],
            [InlineKeyboardButton("💳 রিচার্জ / ডিপোজিট", callback_data='deposit'), InlineKeyboardButton("📊 আমার তথ্য", callback_data='my_info')],
            [InlineKeyboardButton("🎁 রেফার ও আয়", callback_data='refer_info'), InlineKeyboardButton("🧑‍💻 হেল্প ও সাপোর্ট", callback_data='support')]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ================= Smart Admin & User Message Handler =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message

    if msg.text and msg.text.startswith("/"):
        return

    if user.id != ADMIN_ID and not await is_user_joined(context.bot, user.id):
        await send_join_request(update, context)
        return

    if user.id == ADMIN_ID:
        data = load_data()
        success, fail = 0, 0
        
        status_msg = await update.message.reply_text("⏳ **ব্রডকাস্ট শুরু হয়েছে, সবার কাছে পাঠানো হচ্ছে...**", parse_mode='Markdown')

        for uid in list(data.keys()):
            try:
                await context.bot.copy_message(
                    chat_id=int(uid),
                    from_chat_id=update.effective_chat.id,
                    message_id=msg.message_id
                )
                success += 1
            except Exception:
                fail += 1

        await status_msg.edit_text(
            f"✅ **ব্রডকাস্ট সম্পূর্ণ সফল!**\n━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 সফলভাবে গেছে: `{success}` জনের কাছে\n"
            f"❌ ব্যর্থ (ব্লক করেছে): `{fail}` জন",
            parse_mode='Markdown'
        )

    else:
        user_msg_text = msg.text if msg.text else "[ছবি বা অন্য কোনো মিডিয়া ফাইল]"
        admin_text = (
            f"🚨 **নতুন কাস্টমার মেসেজ / ডিপোজিট রিকোয়েস্ট!**\n\n"
            f"👤 ইউজার: {user.full_name} (@{user.username})\n"
            f"🆔 User ID: `{user.id}`\n"
            f"💬 মেসেজ:\n`{user_msg_text}`\n\n"
            f"📌 **ব্যালেন্স দিতে টাইপ করুন:**\n`/addbalance {user.id} পরিমাণ`"
        )
        
        if msg.photo:
            await context.bot.send_photo(chat_id=ADMIN_ID, photo=msg.photo[-1].file_id, caption=admin_text, parse_mode='Markdown')
        else:
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode='Markdown')

        await update.message.reply_text("✅ আপনার মেসেজ এডমিনের কাছে পাঠানো হয়েছে! এডমিন খুব দ্রুত রিপ্লাই বা অ্যাকশন নেবেন।")

# ================= Admin Commands =================
async def add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        target_user_id = context.args[0]
        amount = float(context.args[1])
        update_user_balance(target_user_id, amount)
        await update.message.reply_text(f"✅ User ID {target_user_id}-এ ৳{amount} যোগ করা হয়েছে!")
        await context.bot.send_message(chat_id=int(target_user_id), text=f"🎉 আপনার একাউন্টে ৳{amount} ব্যালেন্স যোগ করা হয়েছে!")
    except Exception:
        await update.message.reply_text("❌ ভুল ফরম্যাট! লিখুন:\n`/addbalance <USER_ID> <পরিমাণ>`")

async def send_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        target_user_id = context.args[0]
        number_to_send = " ".join(context.args[1:])
        msg = f"🎉 **আপনার নম্বর প্রস্তুত:**\n`{number_to_send}`\n\n📌 *(নাম্বারের ওপর চাপ দিলে কপি হয়ে যাবে)*"
        keyboard = [[InlineKeyboardButton("📩 Get OTP / কোড পান", callback_data='request_otp')]]
        await context.bot.send_message(chat_id=int(target_user_id), text=msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        await update.message.reply_text(f"✅ User ID {target_user_id}-এ নম্বর পাঠানো হয়েছে!")
    except Exception:
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
    except Exception:
        await update.message.reply_text("❌ ভুল ফরম্যাট! লিখুন:\n`/sendotp <USER_ID> <OTP>`")

async def users_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text(f"📊 মোট ইউজারের সংখ্যা: {len(load_data())} জন")

# ================= Main Execution =================
if __name__ == '__main__':
    # ১. প্রথমে ব্যাকগ্রাউন্ডে Flask Server চালু হবে
    keep_alive()
    
    # ২. এরপর টেলিগ্রাম বট চালু হবে
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    tg_app = app

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sendnum", send_number))
    app.add_handler(CommandHandler("sendotp", send_otp))
    app.add_handler(CommandHandler("addbalance", add_balance))
    app.add_handler(CommandHandler("users", users_count))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    print("Bot is starting cleanly with Flask web server...")
    app.run_polling(drop_pending_updates=True)
