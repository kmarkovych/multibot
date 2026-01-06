# AI-Powered Daily Horoscope Telegram Bot

## Project Overview

A production-ready Telegram bot that delivers personalized AI-generated daily horoscopes with subscription-based delivery and integrated monetization through Telegram Stars.

## Key Features

### AI-Powered Horoscope Generation
- Unique, personalized horoscopes generated using OpenAI GPT-4.1-nano
- Fresh content generated daily for each zodiac sign
- Intelligent caching system to optimize API costs

### Subscription System
- Users can subscribe to receive daily horoscopes automatically
- Configurable delivery time with timezone support
- Flexible scheduling with user-preferred delivery hours

### Multi-Language Support
- Full localization in 4 languages:
  - English
  - Ukrainian
  - Portuguese
  - Kazakh
- Automatic language detection based on user's Telegram settings
- All UI elements, buttons, and messages translated

### Monetization with Telegram Stars
- Built-in token-based billing system
- New users receive free tokens to try the service
- Multiple purchase packages via Telegram's native payment system
- No external payment provider required

### User Experience
- Clean inline keyboard navigation
- All 12 zodiac signs supported
- Settings management (change sign, delivery time, timezone)
- Transaction history and balance tracking

## Technical Stack

| Component | Technology |
|-----------|------------|
| Framework | Python 3.11+ / aiogram 3.x |
| AI | OpenAI API (GPT-4.1-nano) |
| Database | PostgreSQL with SQLAlchemy async ORM |
| Payments | Telegram Stars (XTR currency) |
| Architecture | Plugin-based, modular design |

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Main menu with navigation |
| `/horoscope` | Get today's horoscope |
| `/subscribe` | Subscribe to daily delivery |
| `/unsubscribe` | Cancel subscription |
| `/settings` | Manage preferences |
| `/tokens` | View balance and purchase tokens |
| `/buy` | Purchase token packages |

## Pricing Packages

| Package | Stars | Tokens | Value |
|---------|-------|--------|-------|
| Starter | 25 | 30 | ~1 month daily |
| Standard | 75 | 100 | ~3+ months |
| Premium | 150 | 250 | Best value - 20% savings |

## Architecture Highlights

- **Scalable**: Plugin-based architecture allows easy feature additions
- **Reliable**: Rate limiting, error handling, and graceful degradation
- **Cost-efficient**: Daily horoscope caching minimizes API calls
- **Maintainable**: Clean separation of concerns with dedicated modules for scheduling, caching, subscriptions, and billing

## Deliverables

- Complete source code with documentation
- Database migration scripts
- Configuration templates
- Deployment instructions
- Test coverage

---

*Built with modern async Python patterns and production-ready infrastructure.*
