import json
import os
import math
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
STORE_NAME = os.getenv("STORE_NAME", "Premium On Budget")
COMMUNITY_LINK = os.getenv("COMMUNITY_LINK", "https://t.me/+DICtE_XZN40wMTBl")
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER", "918920803981")
UPI_ID = os.getenv("UPI_ID", "Ask admin for UPI ID")
BANK_DETAILS = os.getenv("BANK_DETAILS", "Ask admin for bank details")
CRYPTO_DETAILS = os.getenv("CRYPTO_DETAILS", "Ask admin for crypto wallet")
GIFT_CARD_DETAILS = os.getenv("GIFT_CARD_DETAILS", "Ask admin for gift card details")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]
USD_RATE = float(os.getenv("USD_RATE", "96.01"))  # 1 USD = INR rate; update anytime in .env

BASE_DIR = Path(__file__).parent
PRODUCTS_FILE = BASE_DIR / "products.json"
ORDERS_FILE = BASE_DIR / "orders.json"

EMAIL, WHATSAPP, TELEGRAM_USERNAME, PAYMENT_METHOD, PAYMENT_PROOF = range(5)
SEARCH_QUERY = 20
PAGE_SIZE = 7


def load_products() -> List[Dict[str, Any]]:
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_orders(orders: List[Dict[str, Any]]) -> None:
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(orders, f, indent=2, ensure_ascii=False)


def load_orders() -> List[Dict[str, Any]]:
    if not ORDERS_FILE.exists():
        save_orders([])
    with open(ORDERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def money(product: Dict[str, Any]) -> str:
    if product.get("price_inr_max"):
        low = product["price_inr"]
        high = product["price_inr_max"]
        return f"₹{low}–₹{high} / ${low/USD_RATE:.2f}–${high/USD_RATE:.2f} approx"
    return f"₹{product['price_inr']} / ${product['price_inr']/USD_RATE:.2f} approx"


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍 Browse Categories", callback_data="categories")],
        [InlineKeyboardButton("🔎 Search Product", callback_data="search")],
        [InlineKeyboardButton("💬 Order on WhatsApp", url=f"https://wa.me/{WHATSAPP_NUMBER}")],
        [InlineKeyboardButton("👑 Join Premium Community", url=COMMUNITY_LINK)],
    ])


def back_home_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="home")]])


def get_categories() -> List[str]:
    return sorted({p["category"] for p in load_products()})


def product_by_id(product_id: str) -> Dict[str, Any] | None:
    return next((p for p in load_products() if p["id"] == product_id), None)


def product_text(product: Dict[str, Any]) -> str:
    return (
        f"✨ <b>{product['name']}</b>\n\n"
        f"💰 <b>Price:</b> {money(product)}\n"
        f"⏳ <b>Duration:</b> {product.get('duration','N/A')}\n"
        f"🔐 <b>Type:</b> {product.get('type','N/A')}\n"
        f"🛡 <b>Warranty:</b> {product.get('warranty','N/A')}\n\n"
        f"📌 <b>Description:</b> {product.get('description','')}\n\n"
        f"📧 Delivery via email after payment confirmation."
    )


def products_keyboard(products: List[Dict[str, Any]], prefix: str, page: int) -> InlineKeyboardMarkup:
    total_pages = max(1, math.ceil(len(products) / PAGE_SIZE))
    start = page * PAGE_SIZE
    page_items = products[start:start + PAGE_SIZE]
    rows = [[InlineKeyboardButton(p["name"], callback_data=f"product:{p['id']}")] for p in page_items]
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"{prefix}:{page-1}"))
    nav.append(InlineKeyboardButton(f"Page {page+1}/{total_pages}", callback_data="noop"))
    if page + 1 < total_pages:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"{prefix}:{page+1}"))
    rows.append(nav)
    rows.append([InlineKeyboardButton("🏠 Home", callback_data="home")])
    return InlineKeyboardMarkup(rows)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"👑 <b>Welcome to {STORE_NAME}</b>\n\n"
        "Premium subscriptions. Budget-friendly prices. Smooth delivery.\n\n"
        "✨ Browse premium products\n"
        "🔎 Search by product name\n"
        "📧 Delivery via email\n"
        "🛡 Warranty mentioned on every product\n\n"
        "Choose an option below."
    )
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu(), parse_mode=ParseMode.HTML)
    else:
        await update.callback_query.edit_message_text(text, reply_markup=main_menu(), parse_mode=ParseMode.HTML)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "noop":
        return
    if data == "home":
        await start(update, context)
        return
    if data == "categories":
        rows = [[InlineKeyboardButton(cat, callback_data=f"cat:{cat}:0")] for cat in get_categories()]
        rows.append([InlineKeyboardButton("🏠 Home", callback_data="home")])
        await query.edit_message_text("🛍 <b>Select a category</b>", reply_markup=InlineKeyboardMarkup(rows), parse_mode=ParseMode.HTML)
        return
    if data.startswith("cat:"):
        _, category, page = data.split(":", 2)
        page = int(page)
        items = [p for p in load_products() if p["category"] == category]
        await query.edit_message_text(
            f"🛍 <b>{category}</b> products:",
            reply_markup=products_keyboard(items, f"cat:{category}", page),
            parse_mode=ParseMode.HTML,
        )
        return
    if data.startswith("product:"):
        product_id = data.split(":", 1)[1]
        product = product_by_id(product_id)
        if not product:
            await query.edit_message_text("Product not found.", reply_markup=back_home_keyboard())
            return
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Order in Bot", callback_data=f"order:{product_id}")],
            [InlineKeyboardButton("💬 Order on WhatsApp", url=f"https://wa.me/{WHATSAPP_NUMBER}?text=Hi%20I%20want%20{product['name'].replace(' ', '%20')}")],
            [InlineKeyboardButton("👑 Join Community", url=COMMUNITY_LINK)],
            [InlineKeyboardButton("🏠 Home", callback_data="home")],
        ])
        await query.edit_message_text(product_text(product), reply_markup=kb, parse_mode=ParseMode.HTML)
        return
    if data == "search":
        await query.edit_message_text("🔎 Send me the product name you want to search.", reply_markup=back_home_keyboard())
        return SEARCH_QUERY


async def order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_id = query.data.split(":", 1)[1]
    product = product_by_id(product_id)
    if not product:
        await query.edit_message_text("Product not found.")
        return ConversationHandler.END
    context.user_data["order"] = {"product_id": product_id, "product_name": product["name"], "price": money(product)}
    await query.edit_message_text(
        f"✅ <b>Order Started</b>\n\nProduct: <b>{product['name']}</b>\nPrice: <b>{money(product)}</b>\n\n📧 Please send your email address for delivery.",
        parse_mode=ParseMode.HTML,
    )
    return EMAIL


async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order"]["email"] = update.message.text.strip()
    await update.message.reply_text("📱 Send your WhatsApp number.")
    return WHATSAPP


async def get_whatsapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order"]["whatsapp"] = update.message.text.strip()
    await update.message.reply_text("👤 Send your Telegram username. Example: @username")
    return TELEGRAM_USERNAME


async def get_telegram_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order"]["telegram_username"] = update.message.text.strip()
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("UPI", callback_data="pay:UPI"), InlineKeyboardButton("Bank Transfer", callback_data="pay:Bank Transfer")],
        [InlineKeyboardButton("Crypto", callback_data="pay:Crypto"), InlineKeyboardButton("Gift Card", callback_data="pay:Gift Card")],
    ])
    await update.message.reply_text("💳 Choose your payment method:", reply_markup=kb)
    return PAYMENT_METHOD


async def payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    method = query.data.split(":", 1)[1]
    context.user_data["order"]["payment_method"] = method
    details = {
        "UPI": f"UPI ID: {UPI_ID}",
        "Bank Transfer": BANK_DETAILS,
        "Crypto": CRYPTO_DETAILS,
        "Gift Card": GIFT_CARD_DETAILS,
    }.get(method, "Contact admin for payment details")
    await query.edit_message_text(
        f"💳 <b>{method}</b> selected.\n\n{details}\n\nAfter payment, send transaction ID or screenshot note here.",
        parse_mode=ParseMode.HTML,
    )
    return PAYMENT_PROOF


async def payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order = context.user_data.get("order", {})
    order["payment_proof"] = update.message.text or "Attachment/payment proof sent"
    order["customer_name"] = update.effective_user.full_name
    order["customer_id"] = update.effective_user.id
    order["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    order["status"] = "Pending"

    orders = load_orders()
    order["order_id"] = len(orders) + 1
    orders.append(order)
    save_orders(orders)

    await update.message.reply_text(
        f"✅ Order received!\n\nOrder ID: #{order['order_id']}\nProduct: {order['product_name']}\n\nJoin our Telegram community for updates:\n{COMMUNITY_LINK}\n\nOur team will verify payment and deliver via email.",
    )

    admin_text = (
        f"🆕 New Order #{order['order_id']}\n"
        f"Product: {order['product_name']}\n"
        f"Price: {order['price']}\n"
        f"Email: {order['email']}\n"
        f"WhatsApp: {order['whatsapp']}\n"
        f"Telegram: {order['telegram_username']}\n"
        f"Payment: {order['payment_method']}\n"
        f"Proof: {order['payment_proof']}\n"
        f"Customer: {order['customer_name']} ({order['customer_id']})"
    )
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(admin_id, admin_text)
        except Exception as e:
            logging.warning("Could not notify admin %s: %s", admin_id, e)
    context.user_data.pop("order", None)
    return ConversationHandler.END


async def search_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.message.text.strip().lower()
    results = [p for p in load_products() if q in p["name"].lower() or q in p["category"].lower()]
    if not results:
        await update.message.reply_text("No product found. Try another name.", reply_markup=back_home_keyboard())
        return ConversationHandler.END
    await update.message.reply_text(
        f"🔎 Found {len(results)} product(s):",
        reply_markup=products_keyboard(results, "searchpage", 0),
    )
    context.user_data["search_results"] = results
    return ConversationHandler.END


async def search_page_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    page = int(query.data.split(":", 1)[1])
    results = context.user_data.get("search_results", [])
    await query.edit_message_reply_markup(reply_markup=products_keyboard(results, "searchpage", page))


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Cancelled. Use /start to open the store again.")
    return ConversationHandler.END


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("Admin access only.")
        return
    orders = load_orders()
    pending = sum(1 for o in orders if o.get("status") == "Pending")
    await update.message.reply_text(
        f"👑 Admin Panel\n\nTotal orders: {len(orders)}\nPending orders: {pending}\n\nCommands:\n/orders - recent orders\n/products_count - total products",
    )


async def orders_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("Admin access only.")
        return
    orders = load_orders()[-10:]
    if not orders:
        await update.message.reply_text("No orders yet.")
        return
    text = "📦 Recent Orders\n\n"
    for o in orders:
        text += f"#{o['order_id']} | {o['product_name']} | {o['status']} | {o['email']}\n"
    await update.message.reply_text(text)


async def products_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("Admin access only.")
        return
    await update.message.reply_text(f"Total products: {len(load_products())}")


  def main():

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN missing. Add it in .env")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    app.run_polling()
    order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(order_start, pattern=r"^order:")],
        states={
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            WHATSAPP: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_whatsapp)],
            TELEGRAM_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_telegram_username)],
            PAYMENT_METHOD: [CallbackQueryHandler(payment_method, pattern=r"^pay:")],
            PAYMENT_PROOF: [MessageHandler(filters.TEXT & ~filters.COMMAND, payment_proof)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    search_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern=r"^search$")],
        states={SEARCH_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_text)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("orders", orders_cmd))
    app.add_handler(CommandHandler("products_count", products_count))
    app.add_handler(order_conv)
    app.add_handler(search_conv)
    app.add_handler(CallbackQueryHandler(search_page_handler, pattern=r"^searchpage:"))
    app.add_handler(CallbackQueryHandler(button_handler))

    print(f"{STORE_NAME} bot is running...")
    from telegram.ext import MessageHandler, filters

async def handle_message(update, context):
    await start(update, context)


app.run_polling()


if __name__ == "__main__":
    main()
