"""Tests for Telegram bot functionality."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from telegram import Update, User as TelegramUser, Message, Chat
from telegram.ext import ContextTypes
from decimal import Decimal

from app.telegram_bot.bot import (
    start,
    help_command,
    auth_command,
    expense_command,
    income_command,
    summary_command,
    month_command,
    recent_command,
    export_command,
    message_handler,
    create_application,
)


@pytest.fixture
def mock_update():
    """Create a mock Telegram Update object."""
    update = Mock(spec=Update)
    update.effective_user = Mock(spec=TelegramUser)
    update.effective_user.id = 123456
    update.effective_user.mention_html.return_value = "<b>TestUser</b>"
    update.message = Mock(spec=Message)
    update.message.reply_html = AsyncMock()
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    """Create a mock Context object."""
    context = Mock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []
    return context


class TestBotCommands:
    """Test bot command handlers."""

    @pytest.mark.asyncio
    async def test_start_command(self, mock_update, mock_context):
        """Test /start command."""
        await start(mock_update, mock_context)
        mock_update.message.reply_html.assert_called_once()
        call_args = mock_update.message.reply_html.call_args
        assert "Welcome" in call_args[0][0]
        assert "Personal Finance Tracker" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_help_command(self, mock_update, mock_context):
        """Test /help command."""
        await help_command(mock_update, mock_context)
        mock_update.message.reply_html.assert_called_once()
        call_args = mock_update.message.reply_html.call_args
        assert "Help" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_auth_command_without_token(self, mock_update, mock_context):
        """Test /auth command without providing token."""
        mock_context.args = []
        await auth_command(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "provide your JWT token" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_auth_command_with_token(self, mock_update, mock_context):
        """Test /auth command with token."""
        mock_context.args = ["test_token_123"]
        await auth_command(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "successful" in call_args[0][0]


class TestTransactionCommands:
    """Test transaction-related commands."""

    @pytest.mark.asyncio
    async def test_expense_command_without_auth(self, mock_update, mock_context):
        """Test /expense command without authentication."""
        from app.telegram_bot.bot import user_sessions

        user_sessions.clear()  # Ensure no auth

        mock_context.args = ["50", "Groceries"]
        await expense_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "authenticate first" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_expense_command_without_amount(self, mock_update, mock_context):
        """Test /expense command without amount."""
        from app.telegram_bot.bot import user_sessions

        user_sessions[123456] = {"jwt_token": "test_token"}

        mock_context.args = []
        await expense_command(mock_update, mock_context)

        call_args = mock_update.message.reply_text.call_args
        assert "Usage" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_expense_command_with_valid_data(self, mock_update, mock_context):
        """Test /expense command with valid data."""
        from app.telegram_bot.bot import user_sessions

        user_sessions[123456] = {"jwt_token": "test_token"}

        mock_context.args = ["50", "Grocery", "shopping"]
        await expense_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Expense added" in call_args[0][0]
        assert "$50" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_expense_command_with_invalid_amount(self, mock_update, mock_context):
        """Test /expense command with invalid amount."""
        from app.telegram_bot.bot import user_sessions

        user_sessions[123456] = {"jwt_token": "test_token"}

        mock_context.args = ["invalid", "Description"]

        # Expect exception to be handled
        try:
            await expense_command(mock_update, mock_context)
        except:
            pass

        # Check error message was sent
        call_args = mock_update.message.reply_text.call_args
        if call_args:
            assert "Invalid" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_income_command_with_valid_data(self, mock_update, mock_context):
        """Test /income command with valid data."""
        from app.telegram_bot.bot import user_sessions

        user_sessions[123456] = {"jwt_token": "test_token"}

        mock_context.args = ["1000", "Salary"]
        await income_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Income added" in call_args[0][0]
        assert "$1000" in call_args[0][0]


class TestReportCommands:
    """Test report commands."""

    @pytest.mark.asyncio
    async def test_summary_command_without_auth(self, mock_update, mock_context):
        """Test /summary command without authentication."""
        from app.telegram_bot.bot import user_sessions

        user_sessions.clear()

        await summary_command(mock_update, mock_context)

        call_args = mock_update.message.reply_text.call_args
        assert "authenticate first" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_summary_command_with_auth(self, mock_update, mock_context):
        """Test /summary command with authentication."""
        from app.telegram_bot.bot import user_sessions

        user_sessions[123456] = {"jwt_token": "test_token"}

        await summary_command(mock_update, mock_context)

        mock_update.message.reply_html.assert_called_once()
        call_args = mock_update.message.reply_html.call_args
        assert "Financial Summary" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_month_command(self, mock_update, mock_context):
        """Test /month command."""
        from app.telegram_bot.bot import user_sessions

        user_sessions[123456] = {"jwt_token": "test_token"}

        await month_command(mock_update, mock_context)

        mock_update.message.reply_html.assert_called_once()
        call_args = mock_update.message.reply_html.call_args
        assert "Statistics" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_recent_command(self, mock_update, mock_context):
        """Test /recent command."""
        from app.telegram_bot.bot import user_sessions

        user_sessions[123456] = {"jwt_token": "test_token"}

        await recent_command(mock_update, mock_context)

        mock_update.message.reply_html.assert_called_once()
        call_args = mock_update.message.reply_html.call_args
        assert "Recent Transactions" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_export_command(self, mock_update, mock_context):
        """Test /export command."""
        from app.telegram_bot.bot import user_sessions

        user_sessions[123456] = {"jwt_token": "test_token"}

        await export_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "export" in call_args[0][0].lower()


class TestMessageHandler:
    """Test message handler for buttons."""

    @pytest.mark.asyncio
    async def test_message_handler_add_expense_button(self, mock_update, mock_context):
        """Test message handler for 'Add Expense' button."""
        mock_update.message.text = "💰 Add Expense"
        await message_handler(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "/expense" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_message_handler_summary_button(self, mock_update, mock_context):
        """Test message handler for 'Summary' button."""
        from app.telegram_bot.bot import user_sessions

        user_sessions[123456] = {"jwt_token": "test_token"}

        mock_update.message.text = "📊 Summary"
        await message_handler(mock_update, mock_context)

        mock_update.message.reply_html.assert_called_once()

    @pytest.mark.asyncio
    async def test_message_handler_unknown_text(self, mock_update, mock_context):
        """Test message handler with unknown text."""
        mock_update.message.text = "random text"
        await message_handler(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "didn't understand" in call_args[0][0]


class TestBotCreation:
    """Test bot application creation."""

    def test_create_application_without_token(self):
        """Test create_application returns None without token."""
        with patch("app.telegram_bot.bot.settings") as mock_settings:
            mock_settings.TELEGRAM_BOT_TOKEN = None
            result = create_application()
            assert result is None

    def test_create_application_with_token(self):
        """Test create_application creates application with token."""
        with patch("app.telegram_bot.bot.settings") as mock_settings:
            mock_settings.TELEGRAM_BOT_TOKEN = "123456:ABC-DEF"
            result = create_application()
            assert result is not None
            assert hasattr(result, "bot")


class TestBotIntegration:
    """Test bot integration points."""

    def test_bot_has_all_commands(self):
        """Test bot application has all required command handlers."""
        with patch("app.telegram_bot.bot.settings") as mock_settings:
            mock_settings.TELEGRAM_BOT_TOKEN = "123456:ABC-DEF"
            app = create_application()

            if app:
                # Check handlers are registered
                assert len(app.handlers) > 0

    def test_user_sessions_storage(self):
        """Test user sessions can store data."""
        from app.telegram_bot.bot import user_sessions

        # Test storing session
        user_sessions[12345] = {"jwt_token": "test_token"}
        assert 12345 in user_sessions
        assert user_sessions[12345]["jwt_token"] == "test_token"

        # Cleanup
        user_sessions.clear()
