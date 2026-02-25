"""Telegram Bot for Personal Finance Tracker."""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

import httpx
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.core.config import settings

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# API base URL
API_BASE_URL = "http://localhost:8000"

# User data storage (in production, use database)
# Format: {telegram_user_id: {"jwt_token": "...", "user_id": 123}}
user_sessions = {}


async def call_api(
    method: str,
    endpoint: str,
    token: Optional[str] = None,
    data: Optional[dict] = None,
    params: Optional[dict] = None,
) -> dict:
    """Make API call to Finance Tracker backend."""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient() as client:
        try:
            if method.upper() == "GET":
                response = await client.get(
                    f"{API_BASE_URL}{endpoint}", headers=headers, params=params
                )
            elif method.upper() == "POST":
                response = await client.post(
                    f"{API_BASE_URL}{endpoint}", headers=headers, json=data
                )
            elif method.upper() == "PUT":
                response = await client.put(
                    f"{API_BASE_URL}{endpoint}", headers=headers, json=data
                )
            else:
                return {"error": "Unsupported HTTP method"}

            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"API error: {e.response.status_code} - {e.response.text}")
            return {
                "error": f"API error: {e.response.status_code}",
                "detail": e.response.text,
            }
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            return {"error": f"Request failed: {str(e)}"}


async def check_auto_auth(telegram_user_id: str) -> Optional[str]:
    """Check if user is already linked and get their token."""
    # Try to fetch user by telegram_user_id
    result = await call_api("GET", f"/auth/telegram/{telegram_user_id}")

    if "error" not in result and result.get("access_token"):
        return result["access_token"]
    return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    telegram_user_id = str(user.id)

    # Check if user is already authenticated
    auto_token = await check_auto_auth(telegram_user_id)
    auth_status = ""

    if auto_token:
        user_sessions[telegram_user_id] = {"jwt_token": auto_token}
        auth_status = "✅ <b>Already authenticated!</b> You can use all features.\n\n"
    else:
        auth_status = "⚠️ You need to authenticate first using /auth [JWT_TOKEN]\n\n"

    keyboard = [
        [KeyboardButton("💰 Add Expense"), KeyboardButton("💵 Add Income")],
        [KeyboardButton("📊 Summary"), KeyboardButton("📈 This Month")],
        [KeyboardButton("📋 Recent Transactions"), KeyboardButton("⚙️ Settings")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_html(
        f"👋 Hi {user.mention_html()}!\n\n"
        f"Welcome to <b>Personal Finance Tracker</b> bot!\n\n"
        f"{auth_status}"
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
    """Authenticate user with JWT token and link Telegram account."""
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide your JWT token:\n"
            "/auth YOUR_JWT_TOKEN\n\n"
            "Get your token from the web app at /auth/login"
        )
        return

    token = context.args[0]
    telegram_user_id = str(update.effective_user.id)

    # Validate token and link Telegram account
    result = await call_api("GET", "/auth/me", token=token)

    if "error" in result:
        await update.message.reply_text(
            "❌ Invalid token. Please login to the web app and get a new token."
        )
        return

    # Link Telegram account to user profile
    link_data = {"telegram_user_id": telegram_user_id}
    link_result = await call_api("PUT", "/auth/me", token=token, data=link_data)

    if "error" in link_result:
        logger.error(f"Failed to link Telegram account: {link_result}")

    # Store session
    user_sessions[telegram_user_id] = {"jwt_token": token, "user_id": result.get("id")}

    await update.message.reply_text(
        "✅ Authentication successful!\n"
        "Your Telegram account is now linked.\n"
        "You'll stay logged in even after bot restarts!"
    )


async def expense_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add an expense transaction."""
    telegram_user_id = str(update.effective_user.id)

    # Check authentication
    if telegram_user_id not in user_sessions:
        await update.message.reply_text("❌ Please authenticate first using /auth [YOUR_JWT_TOKEN]")
        return

    # Parse arguments
    if len(context.args) < 1:
        await update.message.reply_text(
            "❌ Usage: /expense [amount] [description]\n" "Example: /expense 50 Groceries"
        )
        return

    try:
        amount = float(context.args[0])
        description = " ".join(context.args[1:]) if len(context.args) > 1 else "Expense"

        # Call API to create transaction
        token = user_sessions[telegram_user_id]["jwt_token"]
        transaction_data = {
            "amount": amount,
            "description": description,
            "is_expense": True,
            "date": date.today().isoformat(),
        }

        result = await call_api("POST", "/transactions", token=token, data=transaction_data)

        if "error" in result:
            await update.message.reply_text(
                f"❌ Failed to add expense:\n{result.get('detail', result['error'])}"
            )
        else:
            await update.message.reply_text(
                f"✅ Expense added!\n\n"
                f"💸 Amount: ${amount:.2f}\n"
                f"📝 Description: {description}\n"
                f"📅 Date: {date.today().strftime('%Y-%m-%d')}\n"
                f"🆔 ID: {result.get('id', 'N/A')}",
                parse_mode="HTML",
            )

    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ Invalid amount. Please use a number.\n" "Example: /expense 50 Groceries"
        )


async def income_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add an income transaction."""
    telegram_user_id = str(update.effective_user.id)

    # Check authentication
    if telegram_user_id not in user_sessions:
        await update.message.reply_text("❌ Please authenticate first using /auth [YOUR_JWT_TOKEN]")
        return

    # Parse arguments
    if len(context.args) < 1:
        await update.message.reply_text(
            "❌ Usage: /income [amount] [description]\n" "Example: /income 1000 Salary"
        )
        return

    try:
        amount = float(context.args[0])
        description = " ".join(context.args[1:]) if len(context.args) > 1 else "Income"

        # Call API to create transaction
        token = user_sessions[telegram_user_id]["jwt_token"]
        transaction_data = {
            "amount": amount,
            "description": description,
            "is_expense": False,
            "date": date.today().isoformat(),
        }

        result = await call_api("POST", "/transactions", token=token, data=transaction_data)

        if "error" in result:
            await update.message.reply_text(
                f"❌ Failed to add income:\n{result.get('detail', result['error'])}"
            )
        else:
            await update.message.reply_text(
                f"✅ Income added!\n\n"
                f"💵 Amount: ${amount:.2f}\n"
                f"📝 Description: {description}\n"
                f"📅 Date: {date.today().strftime('%Y-%m-%d')}\n"
                f"🆔 ID: {result.get('id', 'N/A')}",
                parse_mode="HTML",
            )

    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ Invalid amount. Please use a number.\n" "Example: /income 1000 Salary"
        )


async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show financial summary."""
    telegram_user_id = str(update.effective_user.id)

    if telegram_user_id not in user_sessions:
        await update.message.reply_text("❌ Please authenticate first using /auth [YOUR_JWT_TOKEN]")
        return

    # Fetch from API
    token = user_sessions[telegram_user_id]["jwt_token"]
    result = await call_api("GET", "/analytics/summary", token=token)

    if "error" in result:
        error_detail = result.get('detail', result['error'])
        logger.error(f"Summary API error: {error_detail}")
        await update.message.reply_text(
            f"❌ Failed to fetch summary:\n{error_detail}"
        )
        return

    # Format summary (defaults to current month)
    total_income = float(result.get("total_income", 0))
    total_expenses = float(result.get("total_expenses", 0))
    balance = float(result.get("balance", 0))
    period_start = result.get("period_start", "")
    period_end = result.get("period_end", "")
    transaction_count = result.get("transactions_count", 0)

    balance_sign = "+" if balance >= 0 else ""
    summary_text = f"""
📊 <b>Financial Summary</b>
📅 Period: {period_start} to {period_end}

💵 <b>Income:</b> ${total_income:.2f}
💸 <b>Expenses:</b> ${total_expenses:.2f}
💰 <b>Balance:</b> {balance_sign}${balance:.2f}
📋 <b>Transactions:</b> {transaction_count}
"""

    # Add top categories if available
    categories = result.get("top_categories", [])
    if categories:
        summary_text += "\n<b>Top Categories:</b>\n"
        for cat in categories[:5]:
            summary_text += f"• {cat.get('name', 'Unknown')}: ${cat.get('total', 0):.2f}\n"

    await update.message.reply_html(summary_text)


async def month_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current month statistics."""
    telegram_user_id = str(update.effective_user.id)

    if telegram_user_id not in user_sessions:
        await update.message.reply_text("❌ Please authenticate first using /auth [YOUR_JWT_TOKEN]")
        return

    # Fetch from API
    token = user_sessions[telegram_user_id]["jwt_token"]
    result = await call_api("GET", "/analytics/summary", token=token)

    if "error" in result:
        await update.message.reply_text(
            f"❌ Failed to fetch month statistics:\n{result.get('detail', result['error'])}"
        )
        return

    # Extract data (summary returns this month by default)
    income = float(result.get("total_income", 0))
    expenses = float(result.get("total_expenses", 0))
    net = income - expenses

    # Get category breakdown
    categories_result = await call_api("GET", "/analytics/categories", token=token, params={"is_expense": True})
    categories = categories_result if isinstance(categories_result, list) else []

    net_sign = "+" if net >= 0 else ""
    month_text = f"""
📅 <b>Statistics for {datetime.now().strftime('%B %Y')}</b>

💵 Income: ${income:.2f}
💸 Expenses: ${expenses:.2f}
💰 Net: {net_sign}${net:.2f}
"""

    # Add expense breakdown if available
    if categories and expenses > 0:
        month_text += "\n📊 <b>Expense Breakdown:</b>\n"
        for cat in categories[:6]:
            cat_total = float(cat.get("total", 0))
            cat_name = cat.get("category_name", "Unknown")
            percentage = (cat_total / expenses * 100) if expenses > 0 else 0
            month_text += f"• {cat_name}: ${cat_total:.2f} ({percentage:.0f}%)\n"

    await update.message.reply_html(month_text)


async def recent_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show recent transactions."""
    telegram_user_id = str(update.effective_user.id)

    if telegram_user_id not in user_sessions:
        await update.message.reply_text("❌ Please authenticate first using /auth [YOUR_JWT_TOKEN]")
        return

    # Fetch from API
    token = user_sessions[telegram_user_id]["jwt_token"]
    result = await call_api("GET", "/transactions", token=token, params={"limit": 10})

    if "error" in result:
        await update.message.reply_text(
            f"❌ Failed to fetch transactions:\n{result.get('detail', result['error'])}"
        )
        return

    transactions = result.get("items", []) if isinstance(result, dict) else result

    if not transactions:
        await update.message.reply_text("📋 No transactions found.\n\nUse /expense or /income to add some!")
        return

    recent_text = "📋 <b>Recent Transactions</b>\n\n"

    # Group by date
    from collections import defaultdict

    by_date = defaultdict(list)
    for tx in transactions[:10]:
        tx_date = tx.get("date", "Unknown")
        by_date[tx_date].append(tx)

    for tx_date in sorted(by_date.keys(), reverse=True):
        recent_text += f"📅 {tx_date}\n"
        for tx in by_date[tx_date]:
            is_expense = tx.get("is_expense", True)
            amount = float(tx.get("amount", 0))
            description = tx.get("description", "No description")
            icon = "💸" if is_expense else "💵"
            recent_text += f"  {icon} ${amount:.2f} - {description}\n"
        recent_text += "\n"

    recent_text += "Use /export to get full transaction history."
    await update.message.reply_html(recent_text)


async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Export transactions."""
    telegram_user_id = str(update.effective_user.id)

    if telegram_user_id not in user_sessions:
        await update.message.reply_text("❌ Please authenticate first using /auth [YOUR_JWT_TOKEN]")
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
            "To add income, use:\n/income [amount] [description]\n\n" "Example: /income 1000 Salary"
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
            parse_mode="HTML",
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
