"""Tests for configuration module."""



from src.core.config import (
    AppConfig,
    BotConfig,
    ConfigManager,
    resolve_env_vars,
)


class TestResolveEnvVars:
    """Tests for environment variable resolution."""

    def test_resolve_simple_var(self, monkeypatch):
        """Test resolving a simple environment variable."""
        monkeypatch.setenv("TEST_VAR", "test_value")
        result = resolve_env_vars("${TEST_VAR}")
        assert result == "test_value"

    def test_resolve_var_in_string(self, monkeypatch):
        """Test resolving a variable embedded in a string."""
        monkeypatch.setenv("TOKEN", "abc123")
        result = resolve_env_vars("Bearer ${TOKEN}")
        assert result == "Bearer abc123"

    def test_resolve_multiple_vars(self, monkeypatch):
        """Test resolving multiple variables."""
        monkeypatch.setenv("USER", "admin")
        monkeypatch.setenv("HOST", "localhost")
        result = resolve_env_vars("${USER}@${HOST}")
        assert result == "admin@localhost"

    def test_resolve_missing_var(self):
        """Test resolving a missing variable returns empty string."""
        result = resolve_env_vars("${MISSING_VAR}")
        assert result == ""

    def test_resolve_in_dict(self, monkeypatch):
        """Test resolving variables in a dictionary."""
        monkeypatch.setenv("TOKEN", "secret")
        data = {"key": "${TOKEN}", "nested": {"value": "${TOKEN}"}}
        result = resolve_env_vars(data)
        assert result == {"key": "secret", "nested": {"value": "secret"}}

    def test_resolve_in_list(self, monkeypatch):
        """Test resolving variables in a list."""
        monkeypatch.setenv("ITEM", "value")
        data = ["${ITEM}", "static"]
        result = resolve_env_vars(data)
        assert result == ["value", "static"]


class TestBotConfig:
    """Tests for BotConfig model."""

    def test_valid_config(self):
        """Test creating a valid bot config."""
        config = BotConfig(
            id="test_bot",
            name="Test Bot",
            token="123:ABC",
        )
        assert config.id == "test_bot"
        assert config.name == "Test Bot"
        assert config.enabled is True
        assert config.mode == "polling"

    def test_token_env_resolution(self, monkeypatch):
        """Test that tokens are resolved from environment."""
        monkeypatch.setenv("MY_TOKEN", "secret_token")
        config = BotConfig(
            id="test",
            name="Test",
            token="${MY_TOKEN}",
        )
        assert config.token == "secret_token"

    def test_default_values(self):
        """Test default values are applied."""
        config = BotConfig(id="test", name="Test", token="123:ABC")
        assert config.description == ""
        assert config.enabled is True
        assert config.mode == "polling"
        assert config.plugins == []


class TestConfigManager:
    """Tests for ConfigManager."""

    def test_load_from_env(self, monkeypatch):
        """Test loading config from environment."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/db")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")

        manager = ConfigManager.load_from_env()
        assert manager.app_config.database_url == "postgresql://test:test@localhost/db"
        assert manager.app_config.log_level == "DEBUG"

    def test_load_bot_config_from_yaml(self, tmp_path):
        """Test loading bot config from YAML file."""
        config_file = tmp_path / "bot.yaml"
        config_file.write_text("""
id: test_bot
name: Test Bot
token: "123:ABC"
mode: polling
plugins:
  - name: start
    enabled: true
""")

        manager = ConfigManager(AppConfig())
        config = manager.load_bot_config(config_file)

        assert config.id == "test_bot"
        assert config.name == "Test Bot"
        assert len(config.plugins) == 1
        assert config.plugins[0].name == "start"
