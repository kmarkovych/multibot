"""Tests for the token billing system."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.billing.decorators import check_tokens, requires_tokens
from src.billing.exceptions import InsufficientTokensError
from src.billing.models import TokenTransaction, UserToken
from src.billing.token_manager import TokenManager, TokenPackage


class TestUserToken:
    """Tests for UserToken model."""

    def test_repr(self):
        """Test UserToken string representation."""
        token = UserToken(telegram_id=12345, bot_id="test_bot", balance=100)
        repr_str = repr(token)
        assert "12345" in repr_str
        assert "test_bot" in repr_str
        assert "100" in repr_str


class TestTokenTransaction:
    """Tests for TokenTransaction model."""

    def test_repr(self):
        """Test TokenTransaction string representation."""
        tx = TokenTransaction(
            id=1,
            telegram_id=12345,
            bot_id="test_bot",
            transaction_type="purchase",
            amount=100,
            balance_after=200,
        )
        repr_str = repr(tx)
        assert "purchase" in repr_str
        assert "100" in repr_str


class TestInsufficientTokensError:
    """Tests for InsufficientTokensError exception."""

    def test_error_message(self):
        """Test error message format."""
        error = InsufficientTokensError(required=10, available=5)
        assert "need 10" in str(error)
        assert "have 5" in str(error)

    def test_error_message_with_action(self):
        """Test error message with action name."""
        error = InsufficientTokensError(required=10, available=5, action="generate")
        assert "need 10" in str(error)
        assert "have 5" in str(error)
        assert "generate" in str(error)

    def test_error_attributes(self):
        """Test error attributes are set correctly."""
        error = InsufficientTokensError(required=10, available=5, action="test")
        assert error.required == 10
        assert error.available == 5
        assert error.action == "test"


class TestTokenPackage:
    """Tests for TokenPackage dataclass."""

    def test_basic_package(self):
        """Test basic package creation."""
        package = TokenPackage(
            id="small",
            stars=50,
            tokens=100,
            label="100 Tokens",
        )
        assert package.id == "small"
        assert package.stars == 50
        assert package.tokens == 100
        assert package.label == "100 Tokens"
        assert package.description == ""

    def test_package_with_description(self):
        """Test package with description."""
        package = TokenPackage(
            id="medium",
            stars=200,
            tokens=500,
            label="500 Tokens",
            description="Bonus 100 tokens included!",
        )
        assert package.description == "Bonus 100 tokens included!"


class TestTokenManager:
    """Tests for TokenManager class."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database manager."""
        db = MagicMock()
        db.session = MagicMock(return_value=AsyncMock())
        return db

    @pytest.fixture
    def packages(self):
        """Create test packages."""
        return [
            TokenPackage(id="small", stars=50, tokens=100, label="100 Tokens"),
            TokenPackage(id="medium", stars=200, tokens=500, label="500 Tokens"),
        ]

    @pytest.fixture
    def manager(self, mock_db, packages):
        """Create a token manager for testing."""
        return TokenManager(
            db=mock_db,
            bot_id="test_bot",
            free_tokens=50,
            action_costs={"generate": 5, "premium": 10},
            packages=packages,
        )

    def test_initialization(self, manager):
        """Test manager initialization."""
        assert manager.bot_id == "test_bot"
        assert manager.free_tokens == 50
        assert manager.action_costs == {"generate": 5, "premium": 10}
        assert len(manager.packages) == 2

    async def test_get_action_cost(self, manager):
        """Test getting action costs."""
        cost = await manager.get_action_cost("generate")
        assert cost == 5

        cost = await manager.get_action_cost("unknown")
        assert cost == 0

    def test_get_package(self, manager):
        """Test getting packages by ID."""
        package = manager.get_package("small")
        assert package is not None
        assert package.tokens == 100

        package = manager.get_package("nonexistent")
        assert package is None

    def test_get_all_packages(self, manager):
        """Test getting all packages."""
        packages = manager.get_all_packages()
        assert len(packages) == 2


class TestRequiresTokensDecorator:
    """Tests for @requires_tokens decorator."""

    @pytest.fixture
    def mock_token_manager(self):
        """Create a mock token manager."""
        manager = AsyncMock()
        manager.consume = AsyncMock()
        return manager

    async def test_successful_consumption(self, mock_token_manager):
        """Test decorator when tokens are successfully consumed."""
        from aiogram.types import Message

        mock_token_manager.consume.return_value = 45  # New balance

        @requires_tokens(cost=5, action="test")
        async def handler(message, token_manager):
            return "success"

        message = MagicMock(spec=Message)
        message.from_user = MagicMock()
        message.from_user.id = 12345

        result = await handler(message, token_manager=mock_token_manager)

        assert result == "success"
        mock_token_manager.consume.assert_called_once_with(
            telegram_id=12345,
            cost=5,
            action="test",
        )

    async def test_insufficient_tokens(self, mock_token_manager):
        """Test decorator when user has insufficient tokens."""
        from aiogram.types import Message

        mock_token_manager.consume.side_effect = InsufficientTokensError(
            required=5, available=2, action="test"
        )

        @requires_tokens(cost=5, action="test")
        async def handler(message, token_manager):
            return "success"

        message = MagicMock(spec=Message)
        message.from_user = MagicMock()
        message.from_user.id = 12345
        message.answer = AsyncMock()

        result = await handler(message, token_manager=mock_token_manager)

        assert result is None
        message.answer.assert_called_once()
        # Check the message contains insufficient tokens info
        call_args = message.answer.call_args[0][0]
        assert "Insufficient tokens" in call_args

    async def test_custom_insufficient_handler(self, mock_token_manager):
        """Test decorator with custom insufficient handler."""
        from aiogram.types import Message

        mock_token_manager.consume.side_effect = InsufficientTokensError(
            required=5, available=2, action="test"
        )

        custom_called = False

        async def custom_handler(event, required, available):
            nonlocal custom_called
            custom_called = True
            await event.answer(f"Custom: need {required}")

        @requires_tokens(cost=5, action="test", on_insufficient=custom_handler)
        async def handler(message, token_manager):
            return "success"

        message = MagicMock(spec=Message)
        message.from_user = MagicMock()
        message.from_user.id = 12345
        message.answer = AsyncMock()

        result = await handler(message, token_manager=mock_token_manager)

        assert result is None
        assert custom_called
        message.answer.assert_called_once()

    async def test_no_token_manager(self):
        """Test decorator when token_manager is not in context."""
        from aiogram.types import Message

        @requires_tokens(cost=5, action="test")
        async def handler(message):
            return "success"

        message = MagicMock(spec=Message)
        message.from_user = MagicMock()
        message.from_user.id = 12345

        # Should still execute handler without consuming
        result = await handler(message)
        assert result == "success"


class TestCheckTokensDecorator:
    """Tests for @check_tokens decorator."""

    async def test_sufficient_balance(self):
        """Test decorator when user has sufficient balance."""
        from aiogram.types import Message

        @check_tokens(cost=5)
        async def handler(message, token_balance):
            return "success"

        message = MagicMock(spec=Message)
        result = await handler(message, token_balance=10)
        assert result == "success"

    async def test_insufficient_balance(self):
        """Test decorator when user has insufficient balance."""
        from aiogram.types import Message

        @check_tokens(cost=5)
        async def handler(message, token_balance):
            return "success"

        message = MagicMock(spec=Message)
        message.answer = AsyncMock()

        result = await handler(message, token_balance=2)
        assert result is None
        message.answer.assert_called_once()


class TestTokenMiddleware:
    """Tests for TokenMiddleware class."""

    @pytest.fixture
    def mock_token_manager(self):
        """Create a mock token manager."""
        manager = AsyncMock()
        manager.ensure_initialized = AsyncMock(return_value=(50, True))
        return manager

    @pytest.fixture
    def middleware(self, mock_token_manager):
        """Create middleware for testing."""
        from src.middleware.tokens import TokenMiddleware

        return TokenMiddleware(token_manager=mock_token_manager)

    async def test_injects_token_data(self, middleware, mock_token_manager):
        """Test middleware injects token data into context."""
        message = MagicMock()
        message.from_user = MagicMock()
        message.from_user.id = 12345

        handler = AsyncMock(return_value="result")
        data = {}

        result = await middleware(handler, message, data)

        assert result == "result"
        assert "token_manager" in data
        assert "token_balance" in data
        assert "is_new_token_user" in data
        assert data["token_balance"] == 50
        assert data["is_new_token_user"] is True

    async def test_initializes_new_user(self, middleware, mock_token_manager):
        """Test middleware initializes new users."""
        message = MagicMock()
        message.from_user = MagicMock()
        message.from_user.id = 12345

        handler = AsyncMock()
        data = {}

        await middleware(handler, message, data)

        mock_token_manager.ensure_initialized.assert_called_once_with(
            telegram_id=12345
        )

    async def test_handles_no_user(self, middleware, mock_token_manager):
        """Test middleware handles messages without user."""
        message = MagicMock()
        message.from_user = None

        handler = AsyncMock(return_value="result")
        data = {}

        result = await middleware(handler, message, data)

        assert result == "result"
        assert data["token_balance"] == 0
        mock_token_manager.ensure_initialized.assert_not_called()

    async def test_handles_initialization_error(self, middleware, mock_token_manager):
        """Test middleware handles initialization errors gracefully."""
        mock_token_manager.ensure_initialized.side_effect = Exception("DB error")

        message = MagicMock()
        message.from_user = MagicMock()
        message.from_user.id = 12345

        handler = AsyncMock(return_value="result")
        data = {}

        # Should not raise, should continue with 0 balance
        result = await middleware(handler, message, data)

        assert result == "result"
        assert data["token_balance"] == 0
