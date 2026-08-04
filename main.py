
import os, json, requests, logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- আপনার তথ্যসমূহ ---
BOT_TOKEN = "8136759671:AAHuCTZnvot7VY9r6t1JXM99uqHA9VX1Iig"
ADMIN_ID = 7469931517
BKASH_NUMBER = "01965291171"
REFERRAL_BONUS = 10  # প্রতি রেফারে বোনাস (টাকা)

# UddoktaPay Credentials
UDDOKTAPAY_API_KEY = "1zwIwlrCfbHk1YVgZIs7ESdhOIK9jDPl3KRcEmTh"
UDDOKTAPAY_API_URL = "https://globalnumbd.paymently.io/api/checkout-v2/request"

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

DATA_FILE = "user_data.json"
tg_app = None

# --- ডেটাবেজ ফাংশনসমূহ ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
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

# --- Webhook Server (অটো ব্যালেন্স এড করার জন্য) ---
class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            payload = json.loads(body.decode('utf-8'))
            api_key = self.headers.get('RT-UDDOKTAPAY-API-KEY') or self.headers.get('rt-uddoktapay-api-key')
            
            if api_key == UDDOKTAPAY_API_KEY and payload.get('status') == 'COMPLETED':
                metadata = payload.get('metadata', {})
                user_id = metadata.get('user_id')
                amount = float(payload.get('amount', 0))
                
                if user_id and amount > 0:
                    update_user_balance(user_id, amount)
                    
                    if tg_app and tg_app.bot:
                        msg = f"🎉 **অটো ডিপোজিট সফল হয়েছে!**\n\n💰 যোগ করা হয়েছে: ৳{amount}\n💳 নতুন ব্যালেন্স: ৳{get_user_balance(user_id)}"
                        tg_app.loop.create_task(tg_app.bot.send_message(chat_id=int(user_id), text=msg, parse_mode='Markdown'))
                        
                        admin_msg = f"🔔 **নতুন অটো পেমেন্ট সফল!**\n\n👤 User ID: `{user_id}`\n💵 পরিমাণ: ৳{amount}\n💳 TrxID: `{payload.get('transaction_id')}`"
                        tg_app.loop.create_task(tg_app.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode='Markdown'))

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        except Exception as e:
            print(f"Webhook Exception: {e}")
            self.send_response(500)
            self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Server Running!")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("", port), WebhookHandler)
    server.serve_forever()

# --- UddoktaPay লিংক তৈরি ---
def create_payment_link(user_id, full_name, amount):
    headers = {
        "RT-UDDOKTAPAY-API-KEY": UDDOKTAPAY_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "full_name": str(full_name),
        "email": f"user_{user_id}@globalnumbd.com",
        "amount": str(amount),
        "metadata": {
            "user_id": str(user_id)
        },
        "redirect_url": "https://t.me/GlobalNumBD_official_bot",
        "cancel_url": "https://t.me/GlobalNumBD_official_bot"
    }
    try:
        response = requests.post(UDDOKTAPAY_API_URL, json=payload, headers=headers, timeout=10)
        res_data = response.json()
        if res_data.get("status"):
            return res_data.get("payment_url")
    except Exception as e:
        print(f"Payment Link API Error: {e}")
    return None

# --- টেলিগ্রাম বট কমান্ডস ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
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
                        text=f"🎉 **রেফারেল বোনাস!**\nএকজন নতুন ইউজার আপনার লিংকে জয়েন করেছেন। আপনি ৳{REFERRAL_BONUS} বোনাস পেয়েছেন!"
                    )
                except Exception:
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
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

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
            update_user_balance(user_id, -service['price'])
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
            f"💳 **টাকা রিচার্জের মাধ্যম বেছে নিন:**\n\n"
            f"⚡ **অটো ডিপোজিট (UddoktaPay):** বিকাশ/নগদ/রকেট পেমেন্ট লিংকের মাধ্যমে ইন্সট্যান্ট রিচার্জ।\n\n"
            f"📱 **ম্যানুয়াল বিকাশ পার্সোনাল:**\nনম্বর: `{BKASH_NUMBER}` (Send Money)\n"
            f"টাকা পাঠানোর পর সেন্ডার নম্বর ও TrxID লিখে মেসেজ দিন।"
        )
        keyboard = [
            [InlineKeyboardButton("⚡ অটো পেমেন্ট (বিকাশ/নগদ)", callback_data='auto_deposit')],
            [InlineKeyboardButton("🔙 প্রধান মেনু", callback_data='main_menu')]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif query.data == 'auto_deposit':
        context.user_data['awaiting_deposit_amount'] = True
        await query.edit_message_text(
            "💰 **কত টাকা রিচার্জ করতে চান?**\nনিচে টাকার পরিমাণটি লিখে পাঠান (যেমন: `100` বা `500`):",
            parse_mode='Markdown'
        )

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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_msg = update.message.text.strip()

    if context.user_data.get('awaiting_deposit_amount'):
        if user_msg.isdigit() and int(user_msg) >= 10:
            amount = int(user_msg)
            context.user_data['awaiting_deposit_amount'] = False
            payment_url = create_payment_link(user.id, user.full_name, amount)
            
            if payment_url:
                keyboard = [[InlineKeyboardButton("🔗 পেমেন্ট করুন (Pay Now)", url=payment_url)]]
                await update.message.reply_text(
                    f"✅ **৳{amount} পেমেন্ট লিংক তৈরি হয়েছে!**\n\n"
                    f"নিচের বাটনে চাপ দিয়ে পেমেন্ট সম্পূর্ণ করলেই অটো ব্যালেন্স এড হয়ে যাবে।",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text("❌ পেমেন্ট লিংক তৈরি করতে সমস্যা হয়েছে! কিছুক্ষণ পর চেষ্টা করুন।")
            return
        else:
            await update.message.reply_text("⚠️ অনুগ্রহ করে সঠিক অংক লিখুন (সর্বনিম্ন ১০ টাকা)।")
            return

    admin_text = (
        f"🚨 **নতুন ম্যানুয়াল ডিপোজিট মেসেজ!**\n\n"
        f"👤 ইউজার: {user.full_name} (@{user.username})\n"
        f"🆔 User ID: `{user.id}`\n"
        f"💬 মেসেজ:\n`{user_msg}`\n\n"
        f"📌 **ব্যালেন্স দিতে টাইপ করুন:**\n`/addbalance {user.id} পরিমাণ`"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode='Markdown')
    await update.message.reply_text("✅ আপনার মেসেজটি এডমিনের কাছে পাঠানো হয়েছে! ভেরিফাই করে ব্যালেন্স যোগ করে দেওয়া হবে।")

# --- এডমিন কমান্ডসমুহ ---
async def add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        target_user_id = context.args[0]
        amount = float(context.args[1])
        update_user_balance(target_user_id, amount)
        await update.message.reply_text(f"✅ User ID {target_user_id}-এ ৳{amount} সফলভাবে যোগ করা হয়েছে!")
        await context.bot.send_message(chat_id=int(target_user_id), text=f"🎉 আপনার একাউন্টে ৳{amount} ব্যালেন্স যোগ করা হয়েছে!")
    except Exception:
        await update.message.reply_text("❌ ভুল ফরম্যাট! লিখুন:\n`/addbalance <USER_ID> <পরিমাণ>`")

async def send_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        target_user_id = context.args[0]
        number_to_send = " ".join(context.args[1:])
        msg = f"🎉 **আপনার অর্ডারকৃত নম্বর:**\n`{number_to_send}`\n\n📌 *(নাম্বারের ওপর চাপ দিলেই অটো কপি হয়ে যাবে)*"
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

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not context.args:
        return
    message_to_send = " ".join(context.args)
    data = load_data()
    success, fail = 0, 0
    for uid in data.keys():
        try:
            await context.bot.send_message(chat_id=int(uid), text=f"📢 **নোটিফিকেশন:**\n\n{message_to_send}", parse_mode='Markdown')
            success += 1
        except Exception:
            fail += 1
    await update.message.reply_text(f"✅ **ব্রডকাস্ট সম্পন্ন!**\n🎯 সফল: {success} জন | ❌ ব্যর্থ: {fail} জন")

async def users_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text(f"📊 মোট ইউজার সংখ্যা: {len(load_data())} জন")

# --- প্রধান অ্যাপ রান ---
if __name__ == '__main__':
    Thread(target=run_server, daemon=True).start()
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    tg_app = app

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sendnum", send_number))
    app.add_handler(CommandHandler("sendotp", send_otp))
    app.add_handler(CommandHandler("addbalance", add_balance))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("users", users_count))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot and Webhook HTTP server running successfully...")
    app.run_polling()
