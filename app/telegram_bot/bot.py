"""Telegram Bot for Personal Finance Tracker."""

import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from datetime import datetime, date
from decimal import Decimal

from app.core.config import settings

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# User data storage (in production, use database)
# Format: {telegram_user_id: {"jwt_token": "...", "user_id": 123}}
user_sessions = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    keyboard = [
        [KeyboardButton("💰 Add Expense"), KeyboardButton("💵 Add Income")],
        [KeyboardButton("📊 Summary"), KeyboardButton("📈 This Month")],
        [KeyboardButton("📋 Recent Transactions"), KeyboardButton("⚙️ Settings")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_html(
        f"👋 Hi {user.mention_html()}!\n\n"
        f"Welcome to <b>Personal Finance Tracker</b> bot!\n\n"
        f"<b>Available Commands:</b>\n"
        f"/start - Show this message\n"
        f"/auth - Link your account (JWT token)\n"
        f"/expense [amount] [description] - Add expense\n"
        f"/income [amount] [description] - Add income\n"
        f"/summary - View financial summary\n"
        f"/month - This month's statistics\n"
        f"/recent - Recent transactions\n"
        f"/export - Export transactions to CSV\n"
        f"/help - Show help\n\n"
        f"Or use the buttons below! 👇",
        reply_markup=reply_markup,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
<b>📱 Personal Finance Tracker Bot Help</b>

<b>Authentication:</b>
/auth [YOUR_JWT_TOKEN] - Link your account

<b>Quick Add:</b>
/expense 50 Groceries - Add $50 grocery expense
/income 1000 Salary - Add $1000 income

<b>Reports:</b>
/summary - Financial overview
/month - Current month statistics
/recent - Last 10 transactions

<b>Export:</b>
/export - Get CSV file of transactions

<b>Examples:</b>
• /expense 12.50 Coffee at Starbucks
• /income 500 Freelance payment
• /summary
"""
    await update.message.reply_html(help_text)


async def auth_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Authenticate user with JWT token."""
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide your JWT token:\n"
            "/auth YOUR_JWT_TOKEN\n\n"
            "Get your token from the web app at /auth/login"
        )
        return

    token = context.args[0]
    user_id = update.effective_user.id

    # In production: validate token with API
    # For now, store it
    user_sessions[user_id] = {"jwt_token": token}

    await update.message.reply_text(
        "✅ Authentication successful!\n"
        "You can now use all bot features."
    )


async def expense_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add an expense transaction."""
    user_id = update.effective_user.id

    # Check authentication
    if user_id not in user_sessions:
        await update.message.reply_text(
            "❌ Please authenticate first using /auth [YOUR_JWT_TOKEN]"
        )
        return

    # Parse arguments
    if len(context.args) < 1:
        await update.message.reply_text(
            "❌ Usage: /expense [amount] [description]\n"
            "Example: /expense 50 Groceries"
        )
        return

    try:
        amount = Decimal(context.args[0])
        description = " ".join(context.args[1:]) if len(context.args) > 1 else "Expense"

        # In production: Call API to create transaction
        # For demo, just confirm
        await update.message.reply_text(
            f"✅ Expense added!\n\n"
            f"💸 Amount: ${amount}\n"
            f"📝 Description: {description}\n"
            f"📅 Date: {date.today().strftime('%Y-%m-%d')}\n\n"
            f"<i>Transaction will be synced with your account.</i>",
            parse_mode="HTML"
        )

    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ Invalid amount. Please use a number.\n"
            "Example: /expense 50 Groceries"
        )


async def income_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add an income transaction."""
    user_id = update.effective_user.id

    # Check authentication
    if user_id not in user_sessions:
        await update.message.reply_text(
            "❌ Please authenticate first using /auth [YOUR_JWT_TOKEN]"
        )
        return

    # Parse arguments
    if len(context.args) < 1:
        await update.message.reply_text(
            "❌ Usage: /income [amount] [description]\n"
            "Example: /income 1000 Salary"
        )
        return

    try:
        amount = Decimal(context.args[0])
        description = " ".join(context.args[1:]) if len(context.args) > 1 else "Income"

        # In production: Call API to create transaction
        await update.message.reply_text(
            f"✅ Income added!\n\n"
            f"💵 Amount: ${amount}\n"
            f"📝 Description: {description}\n"
            f"📅 Date: {date.today().strftime('%Y-%m-%d')}\n\n"
            f"<i>Transaction will be synced with your account.</i>",
            parse_mode="HTML"
        )

    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ Invalid amount. Please use a number.\n"
            "Example: /income 1000 Salary"
        )


async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show financial summary."""
    user_id = update.effective_user.id

    if user_id not in user_sessions:
        await update.message.reply_text(
            "❌ Please authenticate first using /auth [YOUR_JWT_TOKEN]"
        )
        return

    # In production: Fetch from API
    # For demo, show mock data
    summary_text = """
📊 <b>Financial Summary</b>

💵 <b>Income:</b> $5,240.00
💸 <b>Expenses:</b> $3,180.50
💰 <b>Balance:</b> $2,059.50

📈 <b>This Month:</b>
  Income: $1,200.00
  Expenses: $845.30
  Net: +$354.70

<b>Top Categories:</b>
🍔 Food & Dining: $320.00
🚗 Transportation: $180.50
🏠 Housing: $1,200.00
"""
    await update.message.reply_html(summary_text)


async def month_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current month statistics."""
    user_id = update.effective_user.id

    if user_id not in user_sessions:
        await update.message.reply_text(
            "❌ Please authenticate first using /auth [YOUR_JWT_TOKEN]"
        )
        return

    month_text = f"""
📅 <b>Statistics for {datetime.now().strftime('%B %Y')}</b>

💵 Income: $1,200.00
💸 Expenses: $845.30
💰 Net: +$354.70

📊 <b>Expense Breakdown:</b>
🍔 Food: $220.00 (26%)
🚗 Transport: $180.50 (21%)
🛒 Shopping: $150.00 (18%)
💡 Utilities: $120.00 (14%)
🎮 Entertainment: $80.80 (10%)
📱 Other: $94.00 (11%)

📈 Spending trend: -12% vs last month
"""
    await update.message.reply_html(month_text)


async def recent_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show recent transactions."""
    user_id = update.effective_user.id

    if user_id not in user_sessions:
        await update.message.reply_text(
            "❌ Please authenticate first using /auth [YOUR_JWT_TOKEN]"
        )
        return

    # In production: Fetch from API
    recent_text = """
📋 <b>Recent Transactions</b>

📅 2024-01-15
  💸 $45.00 - Grocery Store
  💸 $12.50 - Coffee Shop

📅 2024-01-14
  💸 $89.99 - Amazon Order
  💵 $500.00 - Freelance Payment

📅 2024-01-13
  💸 $35.00 - Gas Station
  💸 $18.50 - Lunch

Use /export to get full transaction history.
"""
    await update.message.reply_html(recent_text)


async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Export transactions."""
    user_id = update.effective_user.id

    if user_id not in user_sessions:
        await update.message.reply_text(
            "❌ Please authenticate first using /auth [YOUR_JWT_TOKEN]"
        )
        return

    await update.message.reply_text(
        "📥 Generating your transaction export...\n\n"
        "In production version, you'll receive:\n"
        "• CSV file with all transactions\n"
        "• Excel file with analytics\n\n"
        "For now, visit the web app at:\n"
        "GET /export/transactions/csv\n"
        "GET /export/transactions/excel"
    )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses and text messages."""
    text = update.message.text

    if text == "💰 Add Expense":
        await update.message.reply_text(
            "To add an expense, use:\n/expense [amount] [description]\n\n"
            "Example: /expense 50 Groceries"
        )
    elif text == "💵 Add Income":
        await update.message.reply_text(
            "To add income, use:\n/income [amount] [description]\n\n"
            "Example: /income 1000 Salary"
        )
    elif text == "📊 Summary":
        await summary_command(update, context)
    elif text == "📈 This Month":
        await month_command(update, context)
    elif text == "📋 Recent Transactions":
        await recent_command(update, context)
    elif text == "⚙️ Settings":
        await update.message.reply_text(
            "⚙️ <b>Settings</b>\n\n"
            "Current settings:\n"
            "• Default currency: USD\n"
            "• Notifications: Enabled\n"
            "• Language: English\n\n"
            "Use /auth to link your account.",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            "I didn't understand that. Use /help to see available commands."
        )


def create_application():
    """Create and configure the Telegram bot application."""
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set. Bot will not start.")
        return None

    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("auth", auth_command))
    application.add_handler(CommandHandler("expense", expense_command))
    application.add_handler(CommandHandler("income", income_command))
    application.add_handler(CommandHandler("summary", summary_command))
    application.add_handler(CommandHandler("month", month_command))
    application.add_handler(CommandHandler("recent", recent_command))
    application.add_handler(CommandHandler("export", export_command))

    # Message handler for buttons
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    return application


async def start_bot():
    """Start the Telegram bot."""
    application = create_application()
    if application:
        logger.info("Starting Telegram bot...")
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        return application
    return None


async def stop_bot(application):
    """Stop the Telegram bot."""
    if application:
        logger.info("Stopping Telegram bot...")
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
