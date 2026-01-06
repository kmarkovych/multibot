# Token Billing System

Complete guide to the token-based billing system with Telegram Stars payments.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Using Tokens in Handlers](#using-tokens-in-handlers)
- [Payment Flow](#payment-flow)
- [Database Schema](#database-schema)
- [API Reference](#api-reference)
- [Examples](#examples)

---

## Overview

The billing system provides a token/credits mechanism for premium bot features:

- **Free tokens on start**: New users automatically receive configurable free tokens
- **Token consumption**: Actions consume tokens based on configured costs
- **Telegram Stars purchases**: Users buy token packages using Telegram's native payment system
- **Per-bot balances**: Each bot maintains separate token balances for users

### How It Works

```
New User → /start → Receive 50 free tokens → Use premium features
                                                    ↓
                                            Balance depleted
                                                    ↓
                                            /buy → Select package → Pay with Stars
                                                    ↓
                                            Tokens credited → Continue using features
```

---

## Quick Start

### 1. Run the Migration

```bash
cd migrations && alembic upgrade head && cd ..
```

### 2. Enable the Billing Plugin

Add to your bot config (`config/bots/your_bot.yaml`):

```yaml
plugins:
  - name: "billing"
    enabled: true
    config:
      free_tokens: 50
      action_costs:
        generate_image: 10
        premium_feature: 5
      packages:
        - id: "small"
          stars: 50
          tokens: 100
          label: "100 Tokens"
        - id: "medium"
          stars: 200
          tokens: 500
          label: "500 Tokens"
          description: "Best value! +100 bonus tokens"
```

### 3. Gate Premium Handlers

```python
from src.billing import requires_tokens

@router.message(Command("generate"))
@requires_tokens(cost=10, action="generate_image")
async def cmd_generate(message: Message):
    # Tokens are automatically consumed before this runs
    await message.answer("Generating your image...")
```

---

## Configuration

### Plugin Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `free_tokens` | int | 50 | Tokens granted to new users |
| `action_costs` | dict | {} | Map of action names to token costs |
| `packages` | list | [] | Available purchase packages |

### Package Configuration

Each package in the `packages` list requires:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier for the package |
| `stars` | int | Yes | Price in Telegram Stars |
| `tokens` | int | Yes | Number of tokens granted |
| `label` | string | Yes | Display name shown to users |
| `description` | string | No | Additional description text |

### Full Configuration Example

```yaml
plugins:
  - name: "billing"
    enabled: true
    config:
      free_tokens: 100

      action_costs:
        generate_horoscope: 1
        generate_image: 10
        premium_analysis: 25

      packages:
        - id: "starter"
          stars: 25
          tokens: 50
          label: "50 Tokens"
          description: "Try it out"

        - id: "standard"
          stars: 100
          tokens: 250
          label: "250 Tokens"
          description: "Most popular"

        - id: "premium"
          stars: 350
          tokens: 1000
          label: "1000 Tokens"
          description: "Best value - save 30%"
```

---

## Using Tokens in Handlers

### The `@requires_tokens` Decorator

Automatically consumes tokens before executing a handler:

```python
from src.billing import requires_tokens

@router.message(Command("premium"))
@requires_tokens(cost=10, action="premium_feature")
async def cmd_premium(message: Message, token_manager: TokenManager):
    # This only runs if user had 10+ tokens (now consumed)
    await message.answer("Premium feature activated!")
```

**Parameters:**
- `cost` (int): Number of tokens to consume
- `action` (str): Action name for logging/analytics
- `on_insufficient` (callable, optional): Custom handler for insufficient tokens

### Custom Insufficient Tokens Handler

```python
async def prompt_purchase(event, required: int, available: int):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Buy Tokens", callback_data="billing:buy_menu")]
    ])
    await event.answer(
        f"You need {required} tokens but only have {available}.\n"
        "Purchase more to continue!",
        reply_markup=keyboard
    )

@router.message(Command("generate"))
@requires_tokens(cost=10, action="generate", on_insufficient=prompt_purchase)
async def cmd_generate(message: Message):
    await do_generation()
```

### The `@check_tokens` Decorator

Check balance without consuming (useful for showing menus):

```python
from src.billing import check_tokens

@router.message(Command("premium_menu"))
@check_tokens(cost=1)
async def cmd_premium_menu(message: Message, token_balance: int):
    # Only shown if user has at least 1 token
    await message.answer(f"Premium menu (Balance: {token_balance})")
```

### Manual Token Operations

Access `TokenManager` directly for complex scenarios:

```python
@router.message(Command("status"))
async def cmd_status(message: Message, token_manager: TokenManager):
    user_id = message.from_user.id

    # Get current balance
    balance = await token_manager.get_balance(user_id)

    # Check if can afford
    can_generate = await token_manager.can_afford(user_id, cost=10)

    # Get full stats
    stats = await token_manager.get_stats(user_id)

    await message.answer(
        f"Balance: {balance} tokens\n"
        f"Total purchased: {stats['total_purchased']}\n"
        f"Total used: {stats['total_consumed']}"
    )
```

### Granting Tokens (Admin/Promotional)

```python
@router.message(Command("grant"), AdminFilter())
async def cmd_grant(message: Message, token_manager: TokenManager):
    # Grant 100 tokens to a user
    target_user_id = 12345
    new_balance = await token_manager.grant(
        telegram_id=target_user_id,
        amount=100,
        reason="promotional_campaign",
    )
    await message.answer(f"Granted 100 tokens. New balance: {new_balance}")
```

---

## Payment Flow

### User Perspective

1. User runs `/tokens` to see balance
2. User clicks "Buy Tokens" or runs `/buy`
3. User selects a package from the menu
4. Telegram shows native payment UI with Stars
5. User confirms payment
6. Tokens are credited immediately
7. User receives confirmation message

### Technical Flow

```
1. User clicks package button
   → callback_data="billing:purchase:small"

2. Bot sends invoice
   → bot.send_invoice(currency="XTR", provider_token="")

3. Telegram sends PreCheckoutQuery
   → Bot validates package exists
   → Bot answers ok=True

4. Payment completes
   → Telegram sends Message with successful_payment

5. Bot processes payment
   → Credits tokens via TokenManager.purchase()
   → Logs transaction
   → Sends confirmation
```

### Telegram Stars Integration

Telegram Stars use:
- Currency code: `XTR`
- Provider token: `""` (empty string)
- No external payment provider needed

```python
await bot.send_invoice(
    chat_id=user_id,
    title="100 Tokens",
    description="Token pack for premium features",
    payload=json.dumps({"package_id": "small", "user_id": user_id}),
    provider_token="",  # Empty for Telegram Stars
    currency="XTR",     # Telegram Stars currency
    prices=[LabeledPrice(label="100 Tokens", amount=50)],
)
```

---

## Database Schema

### user_tokens Table

Stores token balances per user per bot:

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| telegram_id | BIGINT | User's Telegram ID |
| bot_id | VARCHAR(64) | Bot identifier |
| balance | INTEGER | Current token balance |
| total_purchased | INTEGER | Lifetime tokens purchased |
| total_consumed | INTEGER | Lifetime tokens consumed |
| created_at | TIMESTAMPTZ | First interaction |
| updated_at | TIMESTAMPTZ | Last update |

**Indexes:**
- `ix_user_tokens_telegram_bot` (telegram_id, bot_id) UNIQUE
- `ix_user_tokens_bot_id` (bot_id)

### token_transactions Table

Audit log of all token operations:

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| telegram_id | BIGINT | User's Telegram ID |
| bot_id | VARCHAR(64) | Bot identifier |
| transaction_type | VARCHAR(32) | purchase, consume, grant, refund |
| amount | INTEGER | Positive=credit, negative=debit |
| balance_after | INTEGER | Balance after transaction |
| reference_type | VARCHAR(64) | payment, action, welcome, admin |
| reference_id | VARCHAR(128) | Payment ID or action name |
| stars_paid | INTEGER | Stars spent (purchases only) |
| metadata_json | JSONB | Additional data |
| created_at | TIMESTAMPTZ | Transaction time |

**Indexes:**
- `ix_token_transactions_user_bot` (telegram_id, bot_id)
- `ix_token_transactions_created` (created_at)
- `ix_token_transactions_type` (transaction_type)

---

## API Reference

### TokenManager

The main service class for token operations.

#### Methods

```python
# Initialize user and get balance (called automatically by middleware)
balance, is_new = await token_manager.ensure_initialized(telegram_id)

# Get current balance
balance = await token_manager.get_balance(telegram_id)

# Check affordability
can_afford = await token_manager.can_afford(telegram_id, cost=10)

# Consume tokens (raises InsufficientTokensError if insufficient)
new_balance = await token_manager.consume(
    telegram_id=user_id,
    cost=10,
    action="generate_image",
    metadata={"prompt": "sunset"}  # optional
)

# Credit tokens from purchase
new_balance = await token_manager.purchase(
    telegram_id=user_id,
    package_id="small",
    stars_paid=50,
    payment_id="telegram_payment_id"
)

# Grant tokens (admin/promotional)
new_balance = await token_manager.grant(
    telegram_id=user_id,
    amount=100,
    reason="promo_code_XYZ"
)

# Get user statistics
stats = await token_manager.get_stats(telegram_id)
# Returns: {"balance": 50, "total_purchased": 100, "total_consumed": 50}

# Get transaction history
history = await token_manager.get_history(telegram_id, limit=20)

# Get action cost from config
cost = await token_manager.get_action_cost("generate_image")

# Get package by ID
package = token_manager.get_package("small")

# Get all packages
packages = token_manager.get_all_packages()
```

### InsufficientTokensError

Raised when user doesn't have enough tokens:

```python
from src.billing import InsufficientTokensError

try:
    await token_manager.consume(user_id, cost=100, action="expensive")
except InsufficientTokensError as e:
    print(f"Need {e.required}, have {e.available}")
    print(f"Action: {e.action}")
```

### Middleware Injected Data

The `TokenMiddleware` injects these into handler data:

| Key | Type | Description |
|-----|------|-------------|
| `token_manager` | TokenManager | Service instance |
| `token_balance` | int | User's current balance |
| `is_new_token_user` | bool | True if user was just initialized |

---

## Examples

### Premium Feature with Graceful Degradation

```python
@router.message(Command("analyze"))
async def cmd_analyze(message: Message, token_manager: TokenManager, token_balance: int):
    user_id = message.from_user.id

    if token_balance >= 10:
        # Premium analysis
        await token_manager.consume(user_id, 10, "premium_analysis")
        result = await do_premium_analysis(message.text)
        await message.answer(f"Premium Analysis:\n{result}")
    else:
        # Free basic analysis
        result = await do_basic_analysis(message.text)
        await message.answer(
            f"Basic Analysis:\n{result}\n\n"
            f"Upgrade to premium for detailed insights! /buy"
        )
```

### Welcome Message with Token Info

```python
@router.message(CommandStart())
async def cmd_start(message: Message, token_balance: int, is_new_token_user: bool):
    if is_new_token_user:
        await message.answer(
            f"Welcome! You've received {token_balance} free tokens.\n\n"
            "Use /tokens to check your balance.\n"
            "Use /buy to purchase more tokens."
        )
    else:
        await message.answer(
            f"Welcome back! Your balance: {token_balance} tokens."
        )
```

### Transaction History Display

```python
@router.callback_query(F.data == "show_history")
async def show_history(callback: CallbackQuery, token_manager: TokenManager):
    history = await token_manager.get_history(callback.from_user.id, limit=10)

    lines = ["Recent Transactions:\n"]
    for tx in history:
        emoji = "+" if tx["amount"] > 0 else ""
        lines.append(f"{emoji}{tx['amount']} - {tx['reference_id']}")

    await callback.message.edit_text("\n".join(lines))
```

### Admin Revenue Report

```python
@router.message(Command("revenue"), AdminFilter())
async def cmd_revenue(message: Message, db: DatabaseManager):
    async with db.session() as session:
        from sqlalchemy import func, select
        from src.billing.models import TokenTransaction

        query = select(
            func.sum(TokenTransaction.stars_paid).label("total_stars"),
            func.count().label("purchase_count")
        ).where(
            TokenTransaction.transaction_type == "purchase",
            TokenTransaction.bot_id == "your_bot_id"
        )

        result = await session.execute(query)
        row = result.one()

        await message.answer(
            f"Revenue Report:\n"
            f"Total Stars: {row.total_stars or 0}\n"
            f"Purchases: {row.purchase_count}"
        )
```
