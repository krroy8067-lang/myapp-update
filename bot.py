import logging
import random
import string
import time
from datetime import datetime, timedelta

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

import firebase_admin
from firebase_admin import credentials, db

# ------------------ CONFIG ------------------
BOT_TOKEN = "AAHtUSPXlL2_FiGZuqxz-ICz-TO3S_sKXtE"
FIREBASE_CRED = "serviceAccountKey.json"
DB_URL = "YOUR_FIREBASE_DB_URL"

UPI_ID = "yourupi@upi"

plans = {
    "1 Day": {"price": 80, "days": 1},
    "7 Days": {"price": 310, "days": 7},
    "15 Days": {"price": 550, "days": 15},
    "1 Month": {"price": 900, "days": 30}
}

# ------------------ FIREBASE INIT ------------------
cred = credentials.Certificate(FIREBASE_CRED)
firebase_admin.initialize_app(cred, {
    'databaseURL': DB_URL
})

# ------------------ FUNCTIONS ------------------

def generate_key():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

def create_key(user_id, plan_name):
    plan = plans[plan_name]
    key = generate_key()
    expiry = int(time.time()) + plan["days"] * 86400

    data = {
        "user_id": user_id,
        "plan": plan_name,
        "expiry": expiry,
        "status": "active"
    }

    db.reference("keys").child(key).set(data)
    return key

# ------------------ BOT HANDLERS ------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[p] for p in plans.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Welcome!\nChoose a plan:",
        reply_markup=reply_markup
    )

async def plan_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    plan = update.message.text

    if plan not in plans:
        return

    context.user_data["selected_plan"] = plan
    price = plans[plan]["price"]

    await update.message.reply_text(
        f"You selected {plan}\n\n"
        f"Price: ₹{price}\n\n"
        f"Pay to UPI: {UPI_ID}\n\n"
        f"After payment, send 'PAID'"
    )

async def payment_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() == "paid":
        plan = context.user_data.get("selected_plan")

        if not plan:
            await update.message.reply_text("Please select a plan first.")
            return

        user_id = str(update.message.from_user.id)

        key = create_key(user_id, plan)

        await update.message.reply_text(
            f"✅ Payment received!\n\n"
            f"Your Key: {key}\n\n"
            f"Plan: {plan}"
        )

# ------------------ MAIN ------------------

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, plan_selected))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^paid$"), payment_done))

    app.run_polling()

if __name__ == "__main__":
    main()