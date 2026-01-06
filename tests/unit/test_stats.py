"""Tests for the statistics collection module."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.stats.collector import StatsCollector
from src.stats.models import AggregatedStats, BotStatsDTO, SystemStatsDTO


class TestAggregatedStats:
    """Tests for AggregatedStats dataclass."""

    def test_default_values(self):
        """Test default values are zeros."""
        stats = AggregatedStats()
        assert stats.message_count == 0
        assert stats.command_count == 0
        assert stats.callback_count == 0
        assert stats.error_count == 0
        assert stats.new_users == 0

    def test_custom_values(self):
        """Test custom values are set correctly."""
        stats = AggregatedStats(
            message_count=100,
            command_count=50,
            callback_count=25,
            error_count=5,
            new_users=10,
        )
        assert stats.message_count == 100
        assert stats.command_count == 50
        assert stats.callback_count == 25
        assert stats.error_count == 5
        assert stats.new_users == 10


class TestBotStatsDTO:
    """Tests for BotStatsDTO dataclass."""

    def test_required_field(self):
        """Test bot_id is required."""
        stats = BotStatsDTO(bot_id="test_bot")
        assert stats.bot_id == "test_bot"

    def test_default_values(self):
        """Test default values."""
        stats = BotStatsDTO(bot_id="test_bot")
        assert stats.bot_name == ""
        assert stats.total_users == 0
        assert stats.daily_active_users == 0
        assert stats.weekly_active_users == 0
        assert stats.uptime is None
        assert stats.today_messages == 0
        assert stats.today_commands == 0
        assert stats.today_callbacks == 0
        assert stats.week_messages == 0
        assert stats.week_commands == 0
        assert stats.error_rate == 0.0
        assert stats.hourly_pattern == [0] * 24
        assert stats.top_commands == []

    def test_with_uptime(self):
        """Test with uptime set."""
        uptime = timedelta(days=1, hours=5, minutes=30)
        stats = BotStatsDTO(bot_id="test_bot", uptime=uptime)
        assert stats.uptime == uptime
        assert stats.uptime.days == 1


class TestSystemStatsDTO:
    """Tests for SystemStatsDTO dataclass."""

    def test_default_values(self):
        """Test default values are zeros."""
        stats = SystemStatsDTO()
        assert stats.total_bots == 0
        assert stats.running_bots == 0
        assert stats.total_users == 0
        assert stats.today_messages == 0
        assert stats.today_commands == 0

    def test_custom_values(self):
        """Test custom values."""
        stats = SystemStatsDTO(
            total_bots=5,
            running_bots=3,
            total_users=1000,
            today_messages=500,
            today_commands=100,
        )
        assert stats.total_bots == 5
        assert stats.running_bots == 3
        assert stats.total_users == 1000


class TestStatsCollector:
    """Tests for StatsCollector class."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database manager."""
        db = MagicMock()
        db.session = MagicMock(return_value=AsyncMock())
        return db

    @pytest.fixture
    def collector(self, mock_db):
        """Create a stats collector for testing."""
        return StatsCollector(mock_db, flush_interval=60)

    def test_initialization(self, collector):
        """Test collector initialization."""
        assert collector.flush_interval == 60
        assert not collector._running
        assert collector._flush_task is None

    async def test_record_message(self, collector):
        """Test recording a message."""
        await collector.record_message("bot1", 12345)

        assert collector._message_counts["bot1"] == 1
        assert 12345 in collector._seen_users["bot1"]

    async def test_record_multiple_messages(self, collector):
        """Test recording multiple messages."""
        await collector.record_message("bot1", 12345)
        await collector.record_message("bot1", 12345)
        await collector.record_message("bot1", 67890)

        assert collector._message_counts["bot1"] == 3
        assert len(collector._seen_users["bot1"]) == 2

    async def test_record_command(self, collector):
        """Test recording a command."""
        await collector.record_command("bot1", "start", 12345)

        assert collector._command_counts["bot1"] == 1
        assert collector._command_usage["bot1"]["start"] == 1
        assert 12345 in collector._seen_users["bot1"]

    async def test_record_multiple_commands(self, collector):
        """Test recording multiple commands."""
        await collector.record_command("bot1", "start", 12345)
        await collector.record_command("bot1", "help", 12345)
        await collector.record_command("bot1", "start", 67890)

        assert collector._command_counts["bot1"] == 3
        assert collector._command_usage["bot1"]["start"] == 2
        assert collector._command_usage["bot1"]["help"] == 1

    async def test_record_callback(self, collector):
        """Test recording a callback."""
        await collector.record_callback("bot1", 12345)

        assert collector._callback_counts["bot1"] == 1
        assert 12345 in collector._seen_users["bot1"]

    async def test_record_error(self, collector):
        """Test recording an error."""
        await collector.record_error("bot1")

        assert collector._error_counts["bot1"] == 1

    async def test_record_new_user(self, collector):
        """Test recording a new user."""
        await collector.record_new_user("bot1")

        assert collector._new_user_counts["bot1"] == 1

    def test_get_current_counters_empty(self, collector):
        """Test getting counters when empty."""
        counters = collector.get_current_counters()
        assert counters == {}

    async def test_get_current_counters_with_data(self, collector):
        """Test getting counters with data."""
        await collector.record_message("bot1", 12345)
        await collector.record_command("bot1", "start", 12345)
        await collector.record_callback("bot1", 12345)
        await collector.record_error("bot1")

        counters = collector.get_current_counters()

        assert "bot1" in counters
        assert counters["bot1"]["messages"] == 1
        assert counters["bot1"]["commands"] == 1
        assert counters["bot1"]["callbacks"] == 1
        assert counters["bot1"]["errors"] == 1

    async def test_start_stop_lifecycle(self, collector):
        """Test start and stop lifecycle."""
        assert not collector._running

        await collector.start()
        assert collector._running
        assert collector._flush_task is not None

        # Start again should be no-op
        await collector.start()
        assert collector._running

        await collector.stop()
        assert not collector._running

    async def test_multiple_bots(self, collector):
        """Test tracking stats for multiple bots."""
        await collector.record_message("bot1", 100)
        await collector.record_message("bot2", 200)
        await collector.record_command("bot1", "start", 100)
        await collector.record_command("bot2", "help", 200)

        counters = collector.get_current_counters()

        assert "bot1" in counters
        assert "bot2" in counters
        assert counters["bot1"]["messages"] == 1
        assert counters["bot2"]["messages"] == 1
        assert counters["bot1"]["commands"] == 1
        assert counters["bot2"]["commands"] == 1


class TestStatsMiddleware:
    """Tests for StatsMiddleware class."""

    @pytest.fixture
    def mock_collector(self):
        """Create a mock stats collector."""
        collector = AsyncMock()
        collector.record_message = AsyncMock()
        collector.record_command = AsyncMock()
        collector.record_callback = AsyncMock()
        collector.record_error = AsyncMock()
        return collector

    @pytest.fixture
    def middleware(self, mock_collector):
        """Create stats middleware for testing."""
        from src.middleware.stats import StatsMiddleware

        return StatsMiddleware(bot_id="test_bot", collector=mock_collector)

    async def test_record_regular_message(self, middleware, mock_collector):
        """Test recording a regular message (not a command)."""
        from aiogram.types import Message

        # Create mock message with proper spec
        message = MagicMock(spec=Message)
        message.text = "Hello, world!"
        message.caption = None
        message.from_user = MagicMock()
        message.from_user.id = 12345

        handler = AsyncMock(return_value="result")
        data = {}

        result = await middleware(handler, message, data)

        assert result == "result"
        mock_collector.record_message.assert_called_once_with("test_bot", 12345)
        mock_collector.record_command.assert_not_called()

    async def test_record_command(self, middleware, mock_collector):
        """Test recording a command message."""
        from aiogram.types import Message

        message = MagicMock(spec=Message)
        message.text = "/start"
        message.caption = None
        message.from_user = MagicMock()
        message.from_user.id = 12345

        handler = AsyncMock(return_value="result")
        data = {}

        result = await middleware(handler, message, data)

        assert result == "result"
        mock_collector.record_command.assert_called_once_with("test_bot", "start", 12345)
        mock_collector.record_message.assert_not_called()

    async def test_record_command_with_bot_mention(self, middleware, mock_collector):
        """Test recording a command with bot mention."""
        from aiogram.types import Message

        message = MagicMock(spec=Message)
        message.text = "/start@MyBot some args"
        message.caption = None
        message.from_user = MagicMock()
        message.from_user.id = 12345

        handler = AsyncMock(return_value="result")
        data = {}

        await middleware(handler, message, data)

        mock_collector.record_command.assert_called_once_with("test_bot", "start", 12345)

    async def test_record_callback(self, middleware, mock_collector):
        """Test recording a callback query."""
        from aiogram.types import CallbackQuery

        callback = MagicMock(spec=CallbackQuery)
        callback.from_user = MagicMock()
        callback.from_user.id = 12345

        handler = AsyncMock(return_value="result")
        data = {}

        result = await middleware(handler, callback, data)

        assert result == "result"
        mock_collector.record_callback.assert_called_once_with("test_bot", 12345)

    async def test_record_error(self, middleware, mock_collector):
        """Test recording an error when handler raises."""
        from aiogram.types import Message

        message = MagicMock(spec=Message)
        message.text = "Hello"
        message.caption = None
        message.from_user = MagicMock()
        message.from_user.id = 12345

        handler = AsyncMock(side_effect=ValueError("Test error"))
        data = {}

        with pytest.raises(ValueError):
            await middleware(handler, message, data)

        mock_collector.record_error.assert_called_once_with("test_bot")

    async def test_no_user(self, middleware, mock_collector):
        """Test handling event with no user."""
        from aiogram.types import Message

        message = MagicMock(spec=Message)
        message.text = "Hello"
        message.caption = None
        message.from_user = None

        handler = AsyncMock(return_value="result")
        data = {}

        result = await middleware(handler, message, data)

        assert result == "result"
        mock_collector.record_message.assert_called_once_with("test_bot", 0)

    async def test_caption_as_text(self, middleware, mock_collector):
        """Test recording a command from caption (photo with caption)."""
        from aiogram.types import Message

        message = MagicMock(spec=Message)
        message.text = None
        message.caption = "/help"
        message.from_user = MagicMock()
        message.from_user.id = 12345

        handler = AsyncMock(return_value="result")
        data = {}

        await middleware(handler, message, data)

        mock_collector.record_command.assert_called_once_with("test_bot", "help", 12345)


class TestStatsFormatting:
    """Tests for stats formatting helpers in admin handler."""

    def test_format_timedelta_with_days(self):
        """Test formatting timedelta with days."""
        from src.admin.handlers.stats import format_timedelta

        td = timedelta(days=3, hours=14, minutes=22)
        result = format_timedelta(td)
        assert result == "3d 14h 22m"

    def test_format_timedelta_without_days(self):
        """Test formatting timedelta without days."""
        from src.admin.handlers.stats import format_timedelta

        td = timedelta(hours=5, minutes=30)
        result = format_timedelta(td)
        assert result == "5h 30m"

    def test_format_timedelta_minutes_only(self):
        """Test formatting timedelta with minutes only."""
        from src.admin.handlers.stats import format_timedelta

        td = timedelta(minutes=45)
        result = format_timedelta(td)
        assert result == "45m"

    def test_format_timedelta_less_than_minute(self):
        """Test formatting timedelta less than a minute."""
        from src.admin.handlers.stats import format_timedelta

        td = timedelta(seconds=30)
        result = format_timedelta(td)
        assert result == "< 1m"

    def test_format_timedelta_none(self):
        """Test formatting None timedelta."""
        from src.admin.handlers.stats import format_timedelta

        result = format_timedelta(None)
        assert result == "N/A"

    def test_format_number(self):
        """Test formatting numbers with separators."""
        from src.admin.handlers.stats import format_number

        assert format_number(0) == "0"
        assert format_number(100) == "100"
        assert format_number(1000) == "1,000"
        assert format_number(1234567) == "1,234,567"

    def test_find_peak_hours(self):
        """Test finding peak hours."""
        from src.admin.handlers.stats import _find_peak_hours

        pattern = [0] * 24
        pattern[10] = 100
        pattern[14] = 80
        pattern[18] = 60

        result = _find_peak_hours(pattern)
        assert "10:00" in result
        assert "14:00" in result
        assert "18:00" in result

    def test_find_peak_hours_empty(self):
        """Test finding peak hours with no data."""
        from src.admin.handlers.stats import _find_peak_hours

        result = _find_peak_hours([])
        assert result == "No data"

        result = _find_peak_hours([0] * 24)
        assert result == "No data"
