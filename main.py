
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes

# লগইন সেটআপ
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# আপনার বটের টোকেন এবং অ্যাডমিন লিংক
BOT_TOKEN = "8136759671:AAEjaJW1bVFz2AUpchXxoPns7vpw_6PrgSE"
SUPPORT_URL = "https://t.me/jihad1171"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🤖 **GlobalNumBD অফিশিয়াল বটে আপনাকে স্বাগতম!** 🛡️\n\n"
        "👤 **অ্যাকাউন্ট স্ট্যাটাস:** একটিভ (Verified)\n"
        "💰 **আপনার বর্তমান ব্যালেন্স:** ৳০.০০\n\n"
        "*আপনার আস্থাই আমাদের মূল শক্তি। নিরাপদ ও দ্রুত সেবা পেতে নিচের অপশনগুলো ব্যবহার করুন.*"
    )
    
    keyboard = [
        [InlineKeyboardButton("📱 নম্বর কিনুন (Buy Number)", callback_data="buy_number")],
        [
            InlineKeyboardButton("💳 রিচার্জ / ডিপোজিট", callback_data="deposit"),
            InlineKeyboardButton("📊 আমার প্রোফাইল", callback_data="profile"),
        ],
        [InlineKeyboardButton("📜 নিয়মাবলী ও নির্দেশিকা", callback_data="terms")],
        [InlineKeyboardButton("🛡️ হেল্প ও লাইভ সাপোর্ট", url=SUPPORT_URL)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text=welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == "buy_number":
        text = "🌍 **সবচেয়ে জনপ্রিয় দেশগুলোর লিস্ট:**\nনিচের যেকোনো একটি দেশে ক্লিক করে অর্ডার করুন:"
        keyboard = [
            [InlineKeyboardButton("🇺🇸 USA - ৳৩৮০", callback_data="buy_usa"), InlineKeyboardButton("🇬🇧 UK - ৳৪২০", callback_data="buy_uk")],
            [InlineKeyboardButton("🇸🇦 Saudi Arabia - ৳৪৫০", callback_data="buy_saudi"), InlineKeyboardButton("🇦🇪 UAE - ৳৪৫০", callback_data="buy_uae")],
            [InlineKeyboardButton("🇶🇦 Qatar - ৳৪২০", callback_data="buy_qatar"), InlineKeyboardButton("🇴🇲 Oman - ৳৩৯০", callback_data="buy_oman")],
            [InlineKeyboardButton("🇰🇼 Kuwait - ৳৪০০", callback_data="buy_kuwait"), InlineKeyboardButton("🇧🇭 Bahrain - ৳৪১০", callback_data="buy_bahrain")],
            [InlineKeyboardButton("🇲🇾 Malaysia - ৳৪২০", callback_data="buy_malaysia"), InlineKeyboardButton("🇸🇬 Singapore - ৳৪৫০", callback_data="buy_singapore")],
            [InlineKeyboardButton("🇪🇬 Egypt - ৳৩৫০", callback_data="buy_egypt"), InlineKeyboardButton("🇨🇦 Canada - ৳৪৪০", callback_data="buy_canada")],
            [InlineKeyboardButton("🇩🇪 Germany - ৳৪৮০", callback_data="buy_germany"), InlineKeyboardButton("🇫🇷 France - ৳৪৯০", callback_data="buy_france")],
            [InlineKeyboardButton("🇮🇹 Italy - ৳৪৬০", callback_data="buy_italy"), InlineKeyboardButton("🇷🇺 Russia - ৳৩৫০", callback_data="buy_russia")],
            [InlineKeyboardButton("🇧🇷 Brazil - ৳৩৬০", callback_data="buy_brazil"), InlineKeyboardButton("🇮🇳 India - ৳৩৪০", callback_data="buy_india")],
            [InlineKeyboardButton("🇹🇷 Turkey - ৳৩৯০", callback_data="buy_turkey"), InlineKeyboardButton("🇮🇩 Indonesia - ৳৩৬০", callback_data="buy_indonesia")],
            [InlineKeyboardButton("🔙 প্রধান মেনু", callback_data="main_menu")]
        ]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "deposit":
        await query.edit_message_text(
            text="💳 **রিচার্জ / ডিপোজিট:**\n\nঅটোমেটিক পেমেন্ট সিস্টেম খুব শীঘ্রই যুক্ত হচ্ছে। ব্যালেন্স এড করতে সরাসরি সাপোর্টে যোগাযোগ করুন।",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛡️ লাইভ সাপোর্ট", url=SUPPORT_URL)],
                [InlineKeyboardButton("🔙 প্রধান মেনু", callback_data="main_menu")]
            ]),
            parse_mode="Markdown"
        )

    elif data == "profile":
        await query.edit_message_text(
            text=f"📊 **আপনার প্রোফাইল তথ্য:**\n\n- টেলিগ্রাম আইডি: `{query.from_user.id}`\n- নাম: {query.from_user.first_name}\n- ব্যালেন্স: ৳০.০০\n- স্ট্যাটাস: Verified",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 প্রধান মেনু", callback_data="main_menu")]]),
            parse_mode="Markdown"
        )

    elif data == "terms":
        await query.edit_message_text(
            text="📜 **নিয়মাবলী ও নির্দেশিকা:**\n\n১. সেবা গ্রহণের পূর্বে পর্যাপ্ত ব্যালেন্স রিচার্জ করুন।\n২. যেকোনো সমস্যায় ২৪ ঘণ্টার মধ্যে সাপোর্টে যোগাযোগ করুন।\n৩. অপব্যবহার করলে অ্যাকাউন্ট ব্লক করা হতে পারে।",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 প্রধান মেনু", callback_data="main_menu")]]),
            parse_mode="Markdown"
        )

    elif data == "main_menu":
        await start(update, context)

    elif data.startswith("buy_"):
        country_name = data.replace("buy_", "").upper()
        await query.edit_message_text(
            text=f"🛒 আপনি **{country_name}** এর নম্বর সিলেক্ট করেছেন।\n\nঅর্ডার কনফার্ম করতে অথবা ব্যালেন্স অ্যাড করতে সাপোর্টে যোগাযোগ করুন।",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛡️ সাপোর্টে কথা বলুন", url=SUPPORT_URL)],
                [InlineKeyboardButton("🔙 দেশের লিস্টে ফিরুন", callback_data="buy_number")]
            ]),
            parse_mode="Markdown"
        )

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
