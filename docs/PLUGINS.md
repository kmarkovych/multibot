# Plugin Development Guide

Complete guide to creating plugins for the Telegram Multibot System.

## Table of Contents

- [Plugin Basics](#plugin-basics)
- [Handler Types](#handler-types)
- [Filters](#filters)
- [Keyboards](#keyboards)
- [Finite State Machine](#finite-state-machine)
- [Database Access](#database-access)
- [Configuration](#configuration)
- [Best Practices](#best-practices)
- [Examples](#examples)

---

## Plugin Basics

### Minimal Plugin

```python
# src/plugins/custom/hello.py

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.plugins.base import BasePlugin


class HelloPlugin(BasePlugin):
    name = "hello"
    description = "Says hello"
    version = "1.0.0"

    def setup_handlers(self, router: Router) -> None:
        @router.message(Command("hello"))
        async def hello(message: Message) -> None:
            await message.answer("Hello, World!")


plugin = HelloPlugin
```

### Plugin with Configuration

```python
class GreetPlugin(BasePlugin):
    name = "greet"
    description = "Customizable greeting"
    version = "1.0.0"

    def setup_handlers(self, router: Router) -> None:
        @router.message(Command("greet"))
        async def greet(message: Message) -> None:
            greeting = self.get_config("greeting", "Hello")
            name = message.from_user.first_name
            await message.answer(f"{greeting}, {name}!")
```

Config in YAML:
```yaml
plugins:
  - name: "greet"
    config:
      greeting: "Welcome"
```

---

## Handler Types

### Message Handlers

```python
from aiogram.filters import Command
from aiogram import F

def setup_handlers(self, router: Router) -> None:
    # Command handler
    @router.message(Command("start"))
    async def cmd_start(message: Message) -> None:
        await message.answer("Welcome!")

    # Text message handler
    @router.message(F.text)
    async def on_text(message: Message) -> None:
        await message.answer(f"You said: {message.text}")

    # Photo handler
    @router.message(F.photo)
    async def on_photo(message: Message) -> None:
        await message.answer("Nice photo!")

    # Document handler
    @router.message(F.document)
    async def on_document(message: Message) -> None:
        await message.answer(f"Received: {message.document.file_name}")
```

### Callback Query Handlers

```python
from aiogram.types import CallbackQuery

@router.callback_query(F.data == "button_clicked")
async def on_button(callback: CallbackQuery) -> None:
    await callback.answer("Button clicked!")
    await callback.message.edit_text("You clicked the button")

@router.callback_query(F.data.startswith("action_"))
async def on_action(callback: CallbackQuery) -> None:
    action = callback.data.split("_")[1]
    await callback.answer(f"Action: {action}")
```

### Inline Query Handlers

```python
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

@router.inline_query()
async def on_inline(query: InlineQuery) -> None:
    results = [
        InlineQueryResultArticle(
            id="1",
            title="Result 1",
            input_message_content=InputTextMessageContent(
                message_text=f"You searched: {query.query}"
            )
        )
    ]
    await query.answer(results, cache_time=1)
```

---

## Filters

### Built-in Filters

```python
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram import F

# Command with arguments
@router.message(Command("echo"))
async def echo(message: Message) -> None:
    text = message.text.split(maxsplit=1)
    if len(text) > 1:
        await message.answer(text[1])

# StartCommand with deep link
@router.message(CommandStart(deep_link=True))
async def start_with_payload(message: Message) -> None:
    payload = message.text.split()[1] if len(message.text.split()) > 1 else None
    await message.answer(f"Deep link payload: {payload}")

# Filter by content type
@router.message(F.content_type.in_({"photo", "video"}))
async def on_media(message: Message) -> None:
    await message.answer("Media received!")

# Filter by chat type
@router.message(F.chat.type == "private")
async def private_only(message: Message) -> None:
    await message.answer("Private message")

# Filter by user
@router.message(F.from_user.id == 123456789)
async def admin_only(message: Message) -> None:
    await message.answer("Hello, admin!")
```

### Custom Filters

```python
from aiogram.filters import Filter
from aiogram.types import Message


class IsAdmin(Filter):
    def __init__(self, admin_ids: list[int]):
        self.admin_ids = admin_ids

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in self.admin_ids


# Usage
@router.message(Command("admin"), IsAdmin([123456789]))
async def admin_command(message: Message) -> None:
    await message.answer("Admin command executed")
```

---

## Keyboards

### Reply Keyboard

```python
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

@router.message(Command("menu"))
async def show_menu(message: Message) -> None:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Option 1"), KeyboardButton(text="Option 2")],
            [KeyboardButton(text="Cancel")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.answer("Choose:", reply_markup=keyboard)

@router.message(F.text == "Cancel")
async def cancel(message: Message) -> None:
    await message.answer("Cancelled", reply_markup=ReplyKeyboardRemove())
```

### Inline Keyboard

```python
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Using InlineKeyboardMarkup
@router.message(Command("buttons"))
async def show_buttons(message: Message) -> None:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Yes", callback_data="confirm_yes"),
            InlineKeyboardButton(text="No", callback_data="confirm_no"),
        ],
        [InlineKeyboardButton(text="Visit Website", url="https://example.com")],
    ])
    await message.answer("Choose:", reply_markup=keyboard)

# Using Builder
@router.message(Command("dynamic"))
async def dynamic_buttons(message: Message) -> None:
    builder = InlineKeyboardBuilder()

    for i in range(1, 6):
        builder.button(text=f"Item {i}", callback_data=f"item_{i}")

    builder.adjust(2)  # 2 buttons per row

    await message.answer("Items:", reply_markup=builder.as_markup())
```

---

## Finite State Machine

### Define States

```python
from aiogram.fsm.state import State, StatesGroup


class OrderForm(StatesGroup):
    waiting_for_product = State()
    waiting_for_quantity = State()
    waiting_for_address = State()
    confirming = State()
```

### Use States in Handlers

```python
from aiogram.fsm.context import FSMContext

def setup_handlers(self, router: Router) -> None:

    @router.message(Command("order"))
    async def start_order(message: Message, state: FSMContext) -> None:
        await state.set_state(OrderForm.waiting_for_product)
        await message.answer("What product do you want to order?")

    @router.message(OrderForm.waiting_for_product)
    async def process_product(message: Message, state: FSMContext) -> None:
        await state.update_data(product=message.text)
        await state.set_state(OrderForm.waiting_for_quantity)
        await message.answer("How many?")

    @router.message(OrderForm.waiting_for_quantity)
    async def process_quantity(message: Message, state: FSMContext) -> None:
        try:
            quantity = int(message.text)
            await state.update_data(quantity=quantity)
            await state.set_state(OrderForm.waiting_for_address)
            await message.answer("Delivery address?")
        except ValueError:
            await message.answer("Please enter a number")

    @router.message(OrderForm.waiting_for_address)
    async def process_address(message: Message, state: FSMContext) -> None:
        await state.update_data(address=message.text)
        data = await state.get_data()

        await state.set_state(OrderForm.confirming)

        text = (
            f"Order Summary:\n"
            f"Product: {data['product']}\n"
            f"Quantity: {data['quantity']}\n"
            f"Address: {data['address']}\n\n"
            f"Confirm?"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Confirm", callback_data="order_confirm"),
                InlineKeyboardButton(text="Cancel", callback_data="order_cancel"),
            ]
        ])

        await message.answer(text, reply_markup=keyboard)

    @router.callback_query(OrderForm.confirming, F.data == "order_confirm")
    async def confirm_order(callback: CallbackQuery, state: FSMContext) -> None:
        data = await state.get_data()
        # Save order to database...
        await state.clear()
        await callback.message.edit_text("Order placed!")

    @router.callback_query(OrderForm.confirming, F.data == "order_cancel")
    async def cancel_order(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await callback.message.edit_text("Order cancelled")
```

---

## Database Access

### Using Repositories

```python
from src.database.repositories.bot_repository import (
    BotRepository,
    UserRepository,
    PluginStateRepository,
)

def setup_handlers(self, router: Router) -> None:

    @router.message(Command("stats"))
    async def show_stats(message: Message, session) -> None:
        # Session is injected by DatabaseMiddleware
        user_repo = UserRepository(session)

        # Get or create user
        user, created = await user_repo.get_or_create(
            telegram_id=message.from_user.id,
            bot_id=self._bot_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )

        if created:
            await message.answer("Welcome, new user!")
        else:
            await message.answer(f"Welcome back! First seen: {user.first_seen_at}")

        # Get user count
        count = await user_repo.get_user_count(self._bot_id)
        await message.answer(f"Total users: {count}")
```

### Saving Plugin State

```python
@router.message(Command("save"))
async def save_state(message: Message, session) -> None:
    repo = PluginStateRepository(session)

    await repo.set_state(
        bot_id=self._bot_id,
        plugin_name=self.name,
        state_key="user_preferences",
        state_value={"theme": "dark", "notifications": True},
    )

    await message.answer("Preferences saved!")

@router.message(Command("load"))
async def load_state(message: Message, session) -> None:
    repo = PluginStateRepository(session)

    prefs = await repo.get_state(
        bot_id=self._bot_id,
        plugin_name=self.name,
        state_key="user_preferences",
    )

    if prefs:
        await message.answer(f"Theme: {prefs['theme']}")
    else:
        await message.answer("No preferences saved")
```

---

## Configuration

### Reading Configuration

```python
class MyPlugin(BasePlugin):
    name = "my_plugin"

    def setup_handlers(self, router: Router) -> None:
        # Access full config
        config = self.config

        # Get specific values with defaults
        api_key = self.get_config("api_key", "")
        max_items = self.get_config("max_items", 10)
        features = self.get_config("features", [])

        @router.message(Command("config"))
        async def show_config(message: Message) -> None:
            await message.answer(f"Max items: {max_items}")
```

Config in YAML:
```yaml
plugins:
  - name: "my_plugin"
    config:
      api_key: "secret123"
      max_items: 25
      features:
        - feature1
        - feature2
```

---

## Best Practices

### 1. Use Type Hints

```python
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

async def handler(
    message: Message,
    state: FSMContext,
    session,  # Database session
) -> None:
    pass
```

### 2. Handle Errors Gracefully

```python
@router.message(Command("risky"))
async def risky_command(message: Message) -> None:
    try:
        result = await some_risky_operation()
        await message.answer(f"Success: {result}")
    except SomeError as e:
        await message.answer(f"Error: {e}")
```

### 3. Use Logging

```python
import logging

logger = logging.getLogger(__name__)

class MyPlugin(BasePlugin):
    async def on_load(self, bot) -> None:
        logger.info(f"Plugin {self.name} loaded for bot {self._bot_id}")
```

### 4. Document Your Handlers

```python
@router.message(Command("command"))
async def my_command(message: Message) -> None:
    """
    Handle /command.

    Usage: /command <arg1> <arg2>

    This command does X, Y, Z.
    """
    pass
```

### 5. Keep Handlers Small

```python
# Good
@router.message(Command("process"))
async def process_command(message: Message) -> None:
    data = await fetch_data(message.text)
    result = process_data(data)
    await send_result(message, result)

# Avoid large handler functions
```

---

## Examples

### Weather Bot Plugin

```python
import aiohttp
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.plugins.base import BasePlugin


class WeatherPlugin(BasePlugin):
    name = "weather"
    description = "Get weather information"
    version = "1.0.0"

    def setup_handlers(self, router: Router) -> None:

        @router.message(Command("weather"))
        async def get_weather(message: Message) -> None:
            args = message.text.split(maxsplit=1)
            if len(args) < 2:
                await message.answer("Usage: /weather <city>")
                return

            city = args[1]
            api_key = self.get_config("api_key")

            if not api_key:
                await message.answer("Weather API not configured")
                return

            async with aiohttp.ClientSession() as session:
                url = f"https://api.openweathermap.org/data/2.5/weather"
                params = {"q": city, "appid": api_key, "units": "metric"}

                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        temp = data["main"]["temp"]
                        desc = data["weather"][0]["description"]
                        await message.answer(
                            f"Weather in {city}:\n"
                            f"Temperature: {temp}°C\n"
                            f"Conditions: {desc}"
                        )
                    else:
                        await message.answer(f"City not found: {city}")


plugin = WeatherPlugin
```

### Poll Plugin

```python
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, PollAnswer

from src.plugins.base import BasePlugin


class PollPlugin(BasePlugin):
    name = "poll"
    description = "Create and manage polls"
    version = "1.0.0"

    def setup_handlers(self, router: Router) -> None:

        @router.message(Command("poll"))
        async def create_poll(message: Message) -> None:
            await message.answer_poll(
                question="What's your favorite color?",
                options=["Red", "Green", "Blue", "Yellow"],
                is_anonymous=False,
            )

        @router.poll_answer()
        async def handle_poll_answer(poll_answer: PollAnswer) -> None:
            user_id = poll_answer.user.id
            option = poll_answer.option_ids[0]
            # Save poll answer...


plugin = PollPlugin
```

---

## Testing Plugins

```python
# tests/unit/test_my_plugin.py

import pytest
from src.plugins.custom.my_plugin import MyPlugin


class TestMyPlugin:
    def test_plugin_metadata(self):
        plugin = MyPlugin()
        assert plugin.name == "my_plugin"
        assert plugin.version == "1.0.0"

    def test_config_defaults(self):
        plugin = MyPlugin()
        assert plugin.get_config("missing", "default") == "default"

    def test_config_values(self):
        plugin = MyPlugin(config={"key": "value"})
        assert plugin.get_config("key") == "value"
```
