# Premium On Budget Telegram Store Bot

## Features
- Category menu
- Product list with pagination
- Product search
- Product details with INR + approximate USD price
- Order form inside bot
- Collects customer email, WhatsApp number, Telegram username and payment method
- Payment options: UPI, Bank Transfer, Crypto, Gift Card
- WhatsApp order button
- Telegram community join button
- Basic admin panel and recent orders

## Setup
1. Create bot from Telegram @BotFather and copy BOT TOKEN.
2. Copy `.env.example` to `.env`.
3. Fill BOT_TOKEN, ADMIN_IDS, payment details.
4. Install requirements:

```bash
pip install -r requirements.txt
```

5. Run:

```bash
python bot.py
```

## Find your Telegram Admin ID
Message @userinfobot on Telegram and copy your numeric ID.
Add it to `.env` like:

```env
ADMIN_IDS=123456789
```

## Commands
- `/start` - open store
- `/admin` - admin panel
- `/orders` - last 10 orders
- `/products_count` - total products
- `/cancel` - cancel current order/search

## Hosting
Works on Render, Railway, Replit, VPS or any Python host.
Keep `bot.py`, `products.json`, `requirements.txt`, and `.env` together.

## USD Rate
The bot uses `USD_RATE=96.01` by default. Update it in `.env` whenever needed.
