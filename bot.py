import asyncio
import logging
import os
import random
import string
import re
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, BotCommand
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from sqlalchemy import (
    Column, Integer, BigInteger, String, Float, Boolean, DateTime, ForeignKey,
    Text, select, func, update, delete
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship, joinedload
from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeExpiredError,
    FloodWaitError
)
from telethon.sessions import StringSession
import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== CONFIG ====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [7973988177]
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/bot_db")

# Telegram API credentials (default)
DEFAULT_API_ID = 32480523
DEFAULT_API_HASH = "147839735c9fa4e83451209e9b55cfc5"

CRYPTO_BOT_API_URL = "https://pay.crypt.bot/api"
USDT_TO_RUB_RATE = Decimal("90")

AVAILABLE_COUNTRIES = [
    "Россия", "США", "Германия", "Франция", "Великобритания",
    "Италия", "Испания", "Нидерланды", "Бельгия", "Португалия",
    "Швейцария", "Австрия", "Швеция", "Норвегия", "Дания",
    "Финляндия", "Греция", "Чехия", "Венгрия", "Румыния",
    "Болгария", "Хорватия", "Словакия", "Словения", "Эстония",
    "Латвия", "Литва", "Польша", "Ирландия", "Люксембург",
    "Канада", "Бразилия", "Мексика", "Аргентина", "Чили",
    "Япония", "Южная Корея", "Китай", "Индия", "Австралия",
    "Новая Зеландия", "ЮАР", "Египет", "Турция", "ОАЭ",
    "Саудовская Аравия", "Катар", "Израиль", "Сингапур", "Малайзия"
]

FLAGS = {
    "Россия": "🇷🇺", "США": "🇺🇸", "Германия": "🇩🇪", "Франция": "🇫🇷",
    "Великобритания": "🇬🇧", "Италия": "🇮🇹", "Испания": "🇪🇸",
    "Нидерланды": "🇳🇱", "Бельгия": "🇧🇪", "Португалия": "🇵🇹",
    "Швейцария": "🇨🇭", "Австрия": "🇦🇹", "Швеция": "🇸🇪",
    "Норвегия": "🇳🇴", "Дания": "🇩🇰", "Финляндия": "🇫🇮",
    "Греция": "🇬🇷", "Чехия": "🇨🇿", "Венгрия": "🇭🇺",
    "Румыния": "🇷🇴", "Болгария": "🇧🇬", "Хорватия": "🇭🇷",
    "Словакия": "🇸🇰", "Словения": "🇸🇮", "Эстония": "🇪🇪",
    "Латвия": "🇱🇻", "Литва": "🇱🇹", "Польша": "🇵🇱",
    "Ирландия": "🇮🇪", "Люксембург": "🇱🇺", "Канада": "🇨🇦",
    "Бразилия": "🇧🇷", "Мексика": "🇲🇽", "Аргентина": "🇦🇷",
    "Чили": "🇨🇱", "Япония": "🇯🇵", "Южная Корея": "🇰🇷",
    "Китай": "🇨🇳", "Индия": "🇮🇳", "Австралия": "🇦🇺",
    "Новая Зеландия": "🇳🇿", "ЮАР": "🇿🇦", "Египет": "🇪🇬",
    "Турция": "🇹🇷", "ОАЭ": "🇦🇪", "Саудовская Аравия": "🇸🇦",
    "Катар": "🇶🇦", "Израиль": "🇮🇱", "Сингапур": "🇸🇬",
    "Малайзия": "🇲🇾"
}

PREMIUM_EMOJI = {
    "settings": "5870982283724328568",
    "profile": "5870994129244131212",
    "people": "5870772616305839506",
    "user_check": "5891207662678317861",
    "user_cross": "5893192487324880883",
    "file": "5870528606328852614",
    "smile": "5870764288364252592",
    "growth_chart": "5870930636742595124",
    "stats_chart": "5870921681735781843",
    "home": "5873147866364514353",
    "lock_closed": "6037249452824072506",
    "lock_open": "6037496202990194718",
    "megaphone": "6039422865189638057",
    "check": "5870633910337015697",
    "cross": "5870657884844462243",
    "pencil": "5870676941614354370",
    "trash": "5870875489362513438",
    "down": "5893057118545646106",
    "clip": "6039451237743595514",
    "link": "5769289093221454192",
    "info": "6028435952299413210",
    "bot": "6030400221232501136",
    "eye": "6037397706505195857",
    "eye_hidden": "6037243349675544634",
    "send": "5963103826075456248",
    "download": "6039802767931481871",
    "bell": "6039486778597970865",
    "gift": "6032644646587338669",
    "clock": "5983150113483134607",
    "celebrate": "6041731551845159060",
    "font": "5870801517140775623",
    "write": "5870753782874246579",
    "media_photo": "6035128606563241721",
    "geo": "6042011682497106307",
    "wallet": "5769126056262898415",
    "box": "5884479287171485878",
    "cryptobot": "5260752406890711732",
    "calendar": "5890937706803894250",
    "tag": "5886285355279193209",
    "time_passed": "5775896410780079073",
    "apps": "5778672437122045013",
    "brush": "6050679691004612757",
    "add_text": "5771851822897566479",
    "format": "5778479949572738874",
    "coin": "5904462880941545555",
    "send_money": "5890848474563352982",
    "receive_money": "5879814368572478751",
    "code": "5940433880585605708",
    "loading": "5345906554510012647",
    "back": "5370309567146766474",
    "star": "5370599459661045441",
    "check_sub": "5774022692642492953",
    "subscribe": "6039450962865688331",
}

# ==================== DATABASE ====================
engine = create_async_engine(DATABASE_URL, pool_size=20, max_overflow=10)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class AdminSettings(Base):
    __tablename__ = "admin_settings"
    id = Column(Integer, primary_key=True)
    crypto_bot_token = Column(String(255), nullable=True, default=None)


class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True)
    username = Column(String(255), nullable=True)
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now)
    purchases = relationship("Purchase", back_populates="user")


class Country(Base):
    __tablename__ = "countries"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    code = Column(String(10), nullable=False)
    price = Column(Float, default=100.0)
    accounts = relationship("Account", back_populates="country")


class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True)
    phone = Column(String(20), nullable=False, unique=True)
    api_id = Column(Integer, nullable=True, default=DEFAULT_API_ID)
    api_hash = Column(String(255), nullable=True, default=DEFAULT_API_HASH)
    session_string = Column(Text, nullable=True)
    password_2fa = Column(String(255), nullable=True)
    country_id = Column(Integer, ForeignKey("countries.id"))
    country = relationship("Country", back_populates="accounts")
    sold = Column(Boolean, default=False)
    buyer_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    buyer = relationship("User", back_populates="purchases")
    purchase = relationship("Purchase", back_populates="account", uselist=False)
    code_delivered = Column(Boolean, default=False)


class Purchase(Base):
    __tablename__ = "purchases"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    user = relationship("User", back_populates="purchases")
    account_id = Column(Integer, ForeignKey("accounts.id"))
    account = relationship("Account", back_populates="purchase")
    purchase_date = Column(DateTime, default=datetime.now)
    code = Column(String(10), nullable=True)
    code_used = Column(Boolean, default=False)
    invoice_id = Column(BigInteger, nullable=True)
    payment_method = Column(String(20), nullable=True)


# ==================== STATES ====================
class BroadcastStates(StatesGroup):
    waiting_for_message = State()


class AddAccountStates(StatesGroup):
    waiting_for_country = State()
    waiting_for_phone = State()
    waiting_for_api_id = State()
    waiting_for_api_hash = State()
    waiting_for_2fa = State()
    waiting_for_session = State()


class ChangePriceStates(StatesGroup):
    waiting_for_country = State()
    waiting_for_price = State()


class GiveBalanceStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_amount = State()


class CryptobotTokenStates(StatesGroup):
    waiting_for_token = State()


class BuyAccountStates(StatesGroup):
    waiting_for_country_selection = State()
    waiting_for_payment = State()


# ==================== INIT DATABASE ====================
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        result = await session.execute(select(AdminSettings).limit(1))
        if not result.scalar_one_or_none():
            session.add(AdminSettings(crypto_bot_token=None))

        for country_name in AVAILABLE_COUNTRIES:
            result = await session.execute(
                select(Country).where(Country.name == country_name)
            )
            if not result.scalar_one_or_none():
                session.add(Country(
                    name=country_name,
                    code=country_name[:2].upper(),
                    price=100.0
                ))

        await session.commit()


# ==================== CRYPTO BOT API ====================
async def get_crypto_bot_token():
    async with async_session() as session:
        result = await session.execute(select(AdminSettings).limit(1))
        settings = result.scalar_one_or_none()
        return settings.crypto_bot_token if settings else None


async def create_crypto_invoice(amount_rub):
    token = await get_crypto_bot_token()
    if not token:
        return None

    amount_usdt = round(float(Decimal(str(amount_rub)) / USDT_TO_RUB_RATE), 2)

    headers = {"Crypto-Pay-API-Token": token}
    payload = {
        "asset": "USDT",
        "amount": str(amount_usdt),
        "description": "Покупка Telegram аккаунта",
        "paid_btn_name": "callback",
        "paid_btn_url": "https://t.me/your_bot",
        "expires_in": 1800,
        "allow_comments": False,
        "allow_anonymous": False,
    }

    async with aiohttp.ClientSession() as http_session:
        try:
            async with http_session.post(
                f"{CRYPTO_BOT_API_URL}/createInvoice",
                headers=headers,
                json=payload,
                timeout=15
            ) as resp:
                data = await resp.json()
                if data.get("ok"):
                    return data["result"]
                logger.error(f"CryptoBot error: {data}")
                return None
        except Exception as e:
            logger.error(f"CryptoBot exception: {e}")
            return None


async def check_crypto_invoice(invoice_id):
    token = await get_crypto_bot_token()
    if not token:
        return None

    headers = {"Crypto-Pay-API-Token": token}

    async with aiohttp.ClientSession() as http_session:
        try:
            async with http_session.get(
                f"{CRYPTO_BOT_API_URL}/getInvoices",
                headers=headers,
                params={"invoice_ids": str(invoice_id)},
                timeout=15
            ) as resp:
                data = await resp.json()
                if data.get("ok") and data["result"]["items"]:
                    return data["result"]["items"][0]
                return None
        except Exception as e:
            logger.error(f"CryptoBot exception: {e}")
            return None


# ==================== TELETHON SERVICE ====================
async def get_code_from_account(account_id):
    async with async_session() as session:
        result = await session.execute(
            select(Account).where(Account.id == account_id)
        )
        account = result.scalar_one_or_none()
        if not account or not account.session_string:
            return None, None

    api_id = account.api_id if account.api_id else DEFAULT_API_ID
    api_hash = account.api_hash if account.api_hash else DEFAULT_API_HASH

    client = TelegramClient(
        StringSession(account.session_string),
        api_id,
        api_hash
    )
    try:
        await client.connect()
        if not await client.is_user_authorized():
            await client.disconnect()
            return None, None

        async for dialog in client.iter_dialogs(limit=50):
            if hasattr(dialog.message, 'message') and dialog.message.message:
                msg_text = dialog.message.message
                if any(word in msg_text.lower() for word in ['code', 'код', 'login', 'вход', 'verify']):
                    code_match = re.search(r'\b\d{5}\b', msg_text)
                    if code_match:
                        code = code_match.group()

                        has_2fa = False
                        fa_code = None
                        if account.password_2fa:
                            has_2fa = True
                            fa_code = account.password_2fa

                        await client.disconnect()
                        return code, fa_code

        await client.disconnect()
        return None, None
    except Exception as e:
        logger.error(f"Telethon error: {e}")
        try:
            await client.disconnect()
        except:
            pass
        return None, None


# ==================== UTILS ====================
def em(key: str) -> str:
    return PREMIUM_EMOJI.get(key, "")


def format_price(price: float) -> str:
    return f"{price:.2f}"


def build_account_data_text(account, purchase, country, flag):
    """Собирает сообщение с данными аккаунта."""
    lines = [
        f'<b><tg-emoji emoji-id="{em("code")}">🔨</tg-emoji> Данные аккаунта</b>',
        '',
        f'{flag} <b>Страна:</b> {country.name if country else "Неизвестно"}',
        f'<tg-emoji emoji-id="{em("file")}">📁</tg-emoji> <b>Номер:</b> <code>{account.phone}</code>',
        f'<tg-emoji emoji-id="{em("code")}">🔨</tg-emoji> <b>Код:</b> <code>{purchase.code}</code>',
    ]
    if account.password_2fa:
        lock_emoji_id = em("lock_closed")
        lines.append(
            f'<tg-emoji emoji-id="{lock_emoji_id}">🔒</tg-emoji> <b>2FA пароль:</b> <code>{account.password_2fa}</code>'
        )
    return "\n".join(lines)


# ==================== KEYBOARDS ====================
def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="Купить аккаунт",
                    icon_custom_emoji_id=em("box")
                ),
                KeyboardButton(
                    text="Профиль",
                    icon_custom_emoji_id=em("profile")
                )
            ],
            [
                KeyboardButton(
                    text="Пополнить баланс",
                    icon_custom_emoji_id=em("wallet")
                ),
                KeyboardButton(
                    text="Поддержка",
                    icon_custom_emoji_id=em("info")
                )
            ]
        ],
        resize_keyboard=True
    )


def get_admin_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="Статистика",
                    icon_custom_emoji_id=em("stats_chart")
                ),
                KeyboardButton(
                    text="Добавить аккаунт",
                    icon_custom_emoji_id=em("file")
                )
            ],
            [
                KeyboardButton(
                    text="Изменить цены",
                    icon_custom_emoji_id=em("pencil")
                ),
                KeyboardButton(
                    text="Выдать баланс",
                    icon_custom_emoji_id=em("send_money")
                )
            ],
            [
                KeyboardButton(
                    text="Рассылка",
                    icon_custom_emoji_id=em("megaphone")
                ),
                KeyboardButton(
                    text="CryptoBot Token",
                    icon_custom_emoji_id=em("cryptobot")
                )
            ],
            [
                KeyboardButton(
                    text="Главное меню",
                    icon_custom_emoji_id=em("home")
                )
            ]
        ],
        resize_keyboard=True
    )


def get_countries_inline_keyboard(page: int = 0, per_page: int = 10, prefix: str = "buy_country") -> InlineKeyboardMarkup:
    start = page * per_page
    end = start + per_page
    page_countries = AVAILABLE_COUNTRIES[start:end]

    buttons = []
    for i in range(0, len(page_countries), 2):
        row = []
        for j in range(2):
            if i + j < len(page_countries):
                country = page_countries[i + j]
                flag = FLAGS.get(country, "")
                row.append(InlineKeyboardButton(
                    text=f"{flag} {country}",
                    callback_data=f"{prefix}_{country}"
                ))
        buttons.append(row)

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(
            text="Назад",
            callback_data=f"countries_page_{page - 1}_{prefix}",
            icon_custom_emoji_id=em("back")
        ))
    if end < len(AVAILABLE_COUNTRIES):
        nav_row.append(InlineKeyboardButton(
            text="Далее",
            callback_data=f"countries_page_{page + 1}_{prefix}",
            icon_custom_emoji_id=em("down")
        ))
    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton(
        text="Отмена",
        callback_data="cancel_action",
        icon_custom_emoji_id=em("cross")
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_account_purchase_keyboard(purchase_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Получить код",
                callback_data=f"get_code_{purchase_id}",
                icon_custom_emoji_id=em("code")
            )],
            [InlineKeyboardButton(
                text="В главное меню",
                callback_data="main_menu",
                icon_custom_emoji_id=em("home")
            )]
        ]
    )


def get_payment_method_keyboard(amount: float, country_name: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Оплатить с баланса",
                callback_data=f"pay_balance_{amount}_{country_name}",
                icon_custom_emoji_id=em("wallet")
            )],
            [InlineKeyboardButton(
                text="Оплатить через CryptoBot",
                callback_data=f"pay_crypto_{amount}_{country_name}",
                icon_custom_emoji_id=em("cryptobot")
            )],
            [InlineKeyboardButton(
                text="Отмена",
                callback_data="cancel_payment",
                icon_custom_emoji_id=em("cross")
            )]
        ]
    )


def get_check_payment_keyboard(invoice_id: int, purchase_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Проверить оплату",
                callback_data=f"check_payment_{invoice_id}_{purchase_id}",
                icon_custom_emoji_id=em("loading")
            )],
            [InlineKeyboardButton(
                text="Отмена",
                callback_data="cancel_payment",
                icon_custom_emoji_id=em("cross")
            )]
        ]
    )


def get_admin_broadcast_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Отмена",
                callback_data="cancel_broadcast",
                icon_custom_emoji_id=em("cross")
            )]
        ]
    )


def get_admin_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Отмена",
                callback_data="cancel_action",
                icon_custom_emoji_id=em("cross")
            )]
        ]
    )


# ==================== HANDLERS ====================
router = Router()
dp = Dispatcher(storage=MemoryStorage())


# ==================== START / MENU ====================
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            session.add(User(
                id=message.from_user.id,
                username=message.from_user.username
            ))
            await session.commit()

    if message.from_user.id in ADMIN_IDS:
        await message.answer(
            f'<b><tg-emoji emoji-id="{em("bot")}">🤖</tg-emoji> Добро пожаловать в админ-панель!</b>\n'
            f'<i>Выберите действие:</i>',
            parse_mode=ParseMode.HTML,
            reply_markup=get_admin_reply_keyboard()
        )
    else:
        await message.answer(
            f'<b><tg-emoji emoji-id="{em("bot")}">🤖</tg-emoji> Добро пожаловать в магазин Telegram аккаунтов!</b>\n\n'
            f'<tg-emoji emoji-id="{em("info")}">ℹ</tg-emoji> Здесь вы можете купить аккаунты Telegram разных стран.\n'
            f'<tg-emoji emoji-id="{em("wallet")}">👛</tg-emoji> Оплата через баланс бота или CryptoBot.',
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_reply_keyboard()
        )


@router.message(F.text == "Главное меню")
async def main_menu(message: Message, state: FSMContext):
    await state.clear()
    await cmd_start(message, state)


# ==================== BUY ACCOUNT ====================
@router.message(F.text == "Купить аккаунт")
async def buy_account_start(message: Message, state: FSMContext):
    if message.from_user.id in ADMIN_IDS:
        await message.answer(
            f'<b><tg-emoji emoji-id="{em("box")}">📦</tg-emoji> Выберите страну:</b>',
            parse_mode=ParseMode.HTML,
            reply_markup=get_countries_inline_keyboard(prefix="buy_country")
        )
    else:
        await message.answer(
            f'<b><tg-emoji emoji-id="{em("box")}">📦</tg-emoji> Выберите страну аккаунта:</b>',
            parse_mode=ParseMode.HTML,
            reply_markup=get_countries_inline_keyboard(prefix="buy_country")
        )
    await state.set_state(BuyAccountStates.waiting_for_country_selection)


@router.callback_query(F.data.startswith("buy_country_"), StateFilter(BuyAccountStates.waiting_for_country_selection))
async def buy_country_selected(callback: CallbackQuery, state: FSMContext):
    country_name = callback.data.split("_", 1)[1]

    async with async_session() as session:
        result = await session.execute(
            select(Country).where(Country.name == country_name)
        )
        country = result.scalar_one_or_none()

        if not country:
            await callback.answer("Страна не найдена", show_alert=True)
            return

        accounts_count_result = await session.execute(
            select(func.count()).select_from(Account).where(
                Account.country_id == country.id,
                Account.sold == False,
                Account.session_string.isnot(None)
            )
        )
        accounts_count = accounts_count_result.scalar() or 0

        flag = FLAGS.get(country_name, "")

        await callback.message.edit_text(
            f'<b><tg-emoji emoji-id="{em("box")}">📦</tg-emoji> Покупка аккаунта</b>\n\n'
            f'{flag} <b>Страна:</b> {country_name}\n'
            f'<tg-emoji emoji-id="{em("coin")}">🪙</tg-emoji> <b>Цена:</b> {format_price(country.price)} ₽\n'
            f'<tg-emoji emoji-id="{em("box")}">📦</tg-emoji> <b>В наличии:</b> {accounts_count} шт.\n',
            parse_mode=ParseMode.HTML,
            reply_markup=get_payment_method_keyboard(country.price, country_name)
        )

    await state.update_data(country_name=country_name, country_id=country.id, price=country.price)
    await state.set_state(BuyAccountStates.waiting_for_payment)
    await callback.answer()


@router.callback_query(F.data.startswith("countries_page_"))
async def countries_page(callback: CallbackQuery):
    parts = callback.data.split("_")
    page = int(parts[2])
    prefix = parts[3] if len(parts) > 3 else "buy_country"

    await callback.message.edit_text(
        f'<b><tg-emoji emoji-id="{em("box")}">📦</tg-emoji> Выберите страну:</b>',
        parse_mode=ParseMode.HTML,
        reply_markup=get_countries_inline_keyboard(page=page, prefix=prefix)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pay_balance_"), StateFilter(BuyAccountStates.waiting_for_payment))
async def pay_with_balance(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    amount = float(parts[2])
    country_name = parts[3]

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()

        if not user or user.balance < amount:
            await callback.answer("Недостаточно средств на балансе!", show_alert=True)
            return

        result = await session.execute(
            select(Country).where(Country.name == country_name)
        )
        country = result.scalar_one_or_none()

        if not country:
            await callback.answer("Страна не найдена", show_alert=True)
            return

        result = await session.execute(
            select(Account).where(
                Account.country_id == country.id,
                Account.sold == False,
                Account.session_string.isnot(None)
            ).limit(1)
        )
        account = result.scalar_one_or_none()

        if not account:
            await callback.answer("Аккаунты закончились!", show_alert=True)
            return

        user.balance -= amount
        account.sold = True
        account.buyer_id = user.id

        purchase = Purchase(
            user_id=user.id,
            account_id=account.id,
            payment_method="balance"
        )
        session.add(purchase)
        await session.commit()
        await session.refresh(purchase)

        flag = FLAGS.get(country_name, "")

        await callback.message.edit_text(
            f'<b><tg-emoji emoji-id="{em("check")}">✅</tg-emoji> Аккаунт успешно куплен!</b>\n\n'
            f'{flag} <b>Страна:</b> {country_name}\n'
            f'<tg-emoji emoji-id="{em("file")}">📁</tg-emoji> <b>Номер:</b> <code>{account.phone}</code>\n\n'
            f'<i>Нажмите кнопку ниже, чтобы получить код из Telegram:</i>',
            parse_mode=ParseMode.HTML,
            reply_markup=get_account_purchase_keyboard(purchase.id)
        )

    await state.clear()
    await callback.answer("Покупка успешна!", show_alert=True)


@router.callback_query(F.data.startswith("pay_crypto_"), StateFilter(BuyAccountStates.waiting_for_payment))
async def pay_with_crypto(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    amount = float(parts[2])
    country_name = parts[3]

    invoice = await create_crypto_invoice(amount)
    if not invoice:
        await callback.answer("Ошибка создания платежа. Проверьте токен CryptoBot.", show_alert=True)
        return

    invoice_id = invoice["invoice_id"]
    pay_url = invoice["pay_url"]

    async with async_session() as session:
        result = await session.execute(
            select(Country).where(Country.name == country_name)
        )
        country = result.scalar_one_or_none()

        result = await session.execute(
            select(Account).where(
                Account.country_id == country.id,
                Account.sold == False,
                Account.session_string.isnot(None)
            ).limit(1)
        )
        account = result.scalar_one_or_none()

        if not account:
            await callback.answer("Аккаунты закончились!", show_alert=True)
            return

        account.sold = True
        account.buyer_id = callback.from_user.id

        purchase = Purchase(
            user_id=callback.from_user.id,
            account_id=account.id,
            payment_method="crypto",
            invoice_id=invoice_id
        )
        session.add(purchase)
        await session.commit()
        await session.refresh(purchase)

        flag = FLAGS.get(country_name, "")

        await callback.message.edit_text(
            f'<b><tg-emoji emoji-id="{em("cryptobot")}">👾</tg-emoji> Оплата через CryptoBot</b>\n\n'
            f'{flag} <b>Страна:</b> {country_name}\n'
            f'<tg-emoji emoji-id="{em("coin")}">🪙</tg-emoji> <b>Сумма:</b> {format_price(amount)} ₽\n\n'
            f'<tg-emoji emoji-id="{em("link")}">🔗</tg-emoji> <a href="{pay_url}">Нажмите для оплаты</a>\n\n'
            f'<i>После оплаты нажмите "Проверить оплату"</i>',
            parse_mode=ParseMode.HTML,
            reply_markup=get_check_payment_keyboard(invoice_id, purchase.id),
            disable_web_page_preview=True
        )

    await state.update_data(country_name=country_name, purchase_id=purchase.id)
    await callback.answer()


@router.callback_query(F.data.startswith("check_payment_"))
async def check_payment(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    invoice_id = int(parts[2])
    purchase_id = int(parts[3])

    invoice = await check_crypto_invoice(invoice_id)

    if invoice and invoice["status"] == "paid":
        async with async_session() as session:
            result = await session.execute(
                select(Purchase).where(Purchase.id == purchase_id)
            )
            purchase = result.scalar_one_or_none()

            if purchase:
                result = await session.execute(
                    select(Account).where(Account.id == purchase.account_id)
                )
                account = result.scalar_one_or_none()

                result = await session.execute(
                    select(Country).where(Country.id == account.country_id)
                )
                country = result.scalar_one_or_none()

                flag = FLAGS.get(country.name, "") if country else ""

                await callback.message.edit_text(
                    f'<b><tg-emoji emoji-id="{em("check")}">✅</tg-emoji> Оплата подтверждена!</b>\n\n'
                    f'{flag} <b>Страна:</b> {country.name if country else "Неизвестно"}\n'
                    f'<tg-emoji emoji-id="{em("file")}">📁</tg-emoji> <b>Номер:</b> <code>{account.phone}</code>\n\n'
                    f'<i>Нажмите кнопку ниже, чтобы получить код:</i>',
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_account_purchase_keyboard(purchase_id)
                )

                await state.clear()
                await callback.answer("Оплата подтверждена!", show_alert=True)
            else:
                await callback.answer("Покупка не найдена", show_alert=True)
    elif invoice and invoice["status"] == "active":
        await callback.answer("Платёж ещё не получен. Попробуйте позже.", show_alert=True)
    else:
        await callback.answer("Платёж не найден или отменён.", show_alert=True)


# ==================== GET CODE ====================
@router.callback_query(F.data.startswith("get_code_"))
async def get_code_handler(callback: CallbackQuery):
    purchase_id = int(callback.data.split("_")[2])

    await callback.answer("Ищу код, подождите...", show_alert=False)

    async with async_session() as session:
        result = await session.execute(
            select(Purchase)
            .options(joinedload(Purchase.account))
            .where(Purchase.id == purchase_id)
        )
        purchase = result.unique().scalar_one_or_none()

        if not purchase or purchase.user_id != callback.from_user.id:
            await callback.answer("Покупка не найдена", show_alert=True)
            return

        if purchase.code and purchase.code_used:
            await callback.answer("Код уже был получен ранее", show_alert=True)
            return

        if purchase.code:
            account = purchase.account
            result = await session.execute(
                select(Country).where(Country.id == account.country_id)
            )
            country = result.scalar_one_or_none()
            flag = FLAGS.get(country.name, "") if country else ""

            text = build_account_data_text(account, purchase, country, flag)
            await callback.message.edit_text(text, parse_mode=ParseMode.HTML)
            await callback.answer()
            return

        status_msg = await callback.message.answer(
            f'<tg-emoji emoji-id="{em("loading")}">🔄</tg-emoji> <i>Получаю код из аккаунта...</i>',
            parse_mode=ParseMode.HTML
        )

        code, fa_code = await get_code_from_account(purchase.account_id)

        await status_msg.delete()

        if code:
            purchase.code = code
            purchase.code_used = True
            account = purchase.account
            if fa_code:
                account.password_2fa = fa_code

            await session.commit()
            await session.refresh(purchase)

            result = await session.execute(
                select(Country).where(Country.id == account.country_id)
            )
            country = result.scalar_one_or_none()
            flag = FLAGS.get(country.name, "") if country else ""

            text = build_account_data_text(account, purchase, country, flag)
            await callback.message.edit_text(text, parse_mode=ParseMode.HTML)
        else:
            await callback.message.edit_text(
                f'<b><tg-emoji emoji-id="{em("cross")}">❌</tg-emoji> Код не найден</b>\n\n'
                f'<i>Попробуйте позже или обратитесь в поддержку.</i>',
                parse_mode=ParseMode.HTML
            )

    await callback.answer()


# ==================== PROFILE ====================
@router.message(F.text == "Профиль")
async def profile(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

        result = await session.execute(
            select(func.count()).select_from(Purchase).where(Purchase.user_id == message.from_user.id)
        )
        purchases_count = result.scalar() or 0

        balance = user.balance if user else 0.0

        await message.answer(
            f'<b><tg-emoji emoji-id="{em("profile")}">👤</tg-emoji> Ваш профиль</b>\n\n'
            f'<tg-emoji emoji-id="{em("tag")}">🏷</tg-emoji> <b>ID:</b> <code>{message.from_user.id}</code>\n'
            f'<tg-emoji emoji-id="{em("wallet")}">👛</tg-emoji> <b>Баланс:</b> {format_price(balance)} ₽\n'
            f'<tg-emoji emoji-id="{em("box")}">📦</tg-emoji> <b>Куплено аккаунтов:</b> {purchases_count}',
            parse_mode=ParseMode.HTML
        )


@router.message(F.text == "Поддержка")
async def support(message: Message):
    await message.answer(
        f'<b><tg-emoji emoji-id="{em("info")}">ℹ</tg-emoji> Поддержка</b>\n\n'
        f'<i>По всем вопросам обращайтесь к администратору.</i>',
        parse_mode=ParseMode.HTML
    )


# ==================== ADMIN HANDLERS ====================
@router.message(F.text == "Статистика")
async def admin_stats(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    async with async_session() as session:
        users_count_result = await session.execute(
            select(func.count()).select_from(User)
        )
        users_count = users_count_result.scalar() or 0

        accounts_count_result = await session.execute(
            select(func.count()).select_from(Account).where(Account.sold == False)
        )
        accounts_count = accounts_count_result.scalar() or 0

        sold_count_result = await session.execute(
            select(func.count()).select_from(Account).where(Account.sold == True)
        )
        sold_count = sold_count_result.scalar() or 0

        purchases_count_result = await session.execute(
            select(func.count()).select_from(Purchase)
        )
        purchases_count = purchases_count_result.scalar() or 0

        await message.answer(
            f'<b><tg-emoji emoji-id="{em("stats_chart")}">📊</tg-emoji> Статистика бота</b>\n\n'
            f'<tg-emoji emoji-id="{em("people")}">👥</tg-emoji> <b>Пользователей:</b> {users_count}\n'
            f'<tg-emoji emoji-id="{em("box")}">📦</tg-emoji> <b>Аккаунтов в наличии:</b> {accounts_count}\n'
            f'<tg-emoji emoji-id="{em("check")}">✅</tg-emoji> <b>Продано аккаунтов:</b> {sold_count}\n'
            f'<tg-emoji emoji-id="{em("send_money")}">🪙</tg-emoji> <b>Всего покупок:</b> {purchases_count}',
            parse_mode=ParseMode.HTML
        )


@router.message(F.text == "Добавить аккаунт")
async def admin_add_account(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    await message.answer(
        f'<b><tg-emoji emoji-id="{em("file")}">📁</tg-emoji> Выберите страну аккаунта:</b>',
        parse_mode=ParseMode.HTML,
        reply_markup=get_countries_inline_keyboard(prefix="add_country")
    )
    await state.set_state(AddAccountStates.waiting_for_country)


@router.callback_query(F.data.startswith("add_country_"), StateFilter(AddAccountStates.waiting_for_country))
async def add_account_country_selected(callback: CallbackQuery, state: FSMContext):
    country_name = callback.data.split("_", 1)[1]

    await state.update_data(country_name=country_name)
    await callback.message.edit_text(
        f'<b><tg-emoji emoji-id="{em("file")}">📁</tg-emoji> Введите номер телефона аккаунта:</b>\n'
        f'<i>Формат: +79991234567</i>',
        parse_mode=ParseMode.HTML,
        reply_markup=get_admin_cancel_keyboard()
    )
    await state.set_state(AddAccountStates.waiting_for_phone)
    await callback.answer()


@router.message(StateFilter(AddAccountStates.waiting_for_phone))
async def add_account_phone(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    phone = message.text.strip()
    await state.update_data(phone=phone)

    await message.answer(
        f'<b><tg-emoji emoji-id="{em("file")}">📁</tg-emoji> Введите API ID:</b>\n'
        f'<i>По умолчанию: {DEFAULT_API_ID}</i>',
        parse_mode=ParseMode.HTML,
        reply_markup=get_admin_cancel_keyboard()
    )
    await state.set_state(AddAccountStates.waiting_for_api_id)


@router.message(StateFilter(AddAccountStates.waiting_for_api_id))
async def add_account_api_id(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    try:
        api_id = int(message.text.strip()) if message.text.strip() else DEFAULT_API_ID
    except ValueError:
        api_id = DEFAULT_API_ID

    await state.update_data(api_id=api_id)

    await message.answer(
        f'<b><tg-emoji emoji-id="{em("file")}">📁</tg-emoji> Введите API Hash:</b>\n'
        f'<i>По умолчанию: {DEFAULT_API_HASH}</i>',
        parse_mode=ParseMode.HTML,
        reply_markup=get_admin_cancel_keyboard()
    )
    await state.set_state(AddAccountStates.waiting_for_api_hash)


@router.message(StateFilter(AddAccountStates.waiting_for_api_hash))
async def add_account_api_hash(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    api_hash = message.text.strip() or DEFAULT_API_HASH
    await state.update_data(api_hash=api_hash)

    await message.answer(
        f'<b><tg-emoji emoji-id="{em("file")}">📁</tg-emoji> Введите сессию (session string):</b>\n'
        f'<i>Можно получить через Telethon</i>',
        parse_mode=ParseMode.HTML,
        reply_markup=get_admin_cancel_keyboard()
    )
    await state.set_state(AddAccountStates.waiting_for_session)


@router.message(StateFilter(AddAccountStates.waiting_for_session))
async def add_account_session(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    session_string = message.text.strip()
    await state.update_data(session_string=session_string)

    await message.answer(
        f'<b><tg-emoji emoji-id="{em("file")}">📁</tg-emoji> Введите 2FA пароль (если есть):</b>\n'
        f'<i>Напишите 0 если нет</i>',
        parse_mode=ParseMode.HTML,
        reply_markup=get_admin_cancel_keyboard()
    )
    await state.set_state(AddAccountStates.waiting_for_2fa)


@router.message(StateFilter(AddAccountStates.waiting_for_2fa))
async def add_account_2fa(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    password_2fa = message.text.strip()
    if password_2fa == "0":
        password_2fa = None

    data = await state.get_data()
    country_name = data["country_name"]
    phone = data["phone"]
    api_id = data.get("api_id", DEFAULT_API_ID)
    api_hash = data.get("api_hash", DEFAULT_API_HASH)
    session_string = data["session_string"]

    async with async_session() as session:
        result = await session.execute(
            select(Country).where(Country.name == country_name)
        )
        country = result.scalar_one_or_none()

        if not country:
            country = Country(name=country_name, code=country_name[:2].upper(), price=100.0)
            session.add(country)
            await session.flush()

        account = Account(
            phone=phone,
            api_id=api_id,
            api_hash=api_hash,
            session_string=session_string,
            password_2fa=password_2fa,
            country_id=country.id
        )
        session.add(account)
        await session.commit()

        flag = FLAGS.get(country_name, "")

        await message.answer(
            f'<b><tg-emoji emoji-id="{em("check")}">✅</tg-emoji> Аккаунт успешно добавлен!</b>\n\n'
            f'{flag} <b>Страна:</b> {country_name}\n'
            f'<tg-emoji emoji-id="{em("file")}">📁</tg-emoji> <b>Номер:</b> <code>{phone}</code>',
            parse_mode=ParseMode.HTML,
            reply_markup=get_admin_reply_keyboard()
        )

    await state.clear()


@router.message(F.text == "Изменить цены")
async def admin_change_prices(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    await message.answer(
        f'<b><tg-emoji emoji-id="{em("pencil")}">🖋</tg-emoji> Выберите страну для изменения цены:</b>',
        parse_mode=ParseMode.HTML,
        reply_markup=get_countries_inline_keyboard(prefix="change_price")
    )
    await state.set_state(ChangePriceStates.waiting_for_country)


@router.callback_query(F.data.startswith("change_price_"), StateFilter(ChangePriceStates.waiting_for_country))
async def change_price_country_selected(callback: CallbackQuery, state: FSMContext):
    country_name = callback.data.split("_", 1)[1]

    async with async_session() as session:
        result = await session.execute(
            select(Country).where(Country.name == country_name)
        )
        country = result.scalar_one_or_none()
        current_price = country.price if country else 100.0

    await state.update_data(country_name=country_name)
    await callback.message.edit_text(
        f'<b><tg-emoji emoji-id="{em("pencil")}">🖋</tg-emoji> Введите новую цену для {country_name}:</b>\n'
        f'<i>Текущая цена: {format_price(current_price)} ₽</i>',
        parse_mode=ParseMode.HTML,
        reply_markup=get_admin_cancel_keyboard()
    )
    await state.set_state(ChangePriceStates.waiting_for_price)
    await callback.answer()


@router.message(StateFilter(ChangePriceStates.waiting_for_price))
async def change_price_set(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    try:
        new_price = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer(
            f'<tg-emoji emoji-id="{em("cross")}">❌</tg-emoji> Неверный формат цены',
            parse_mode=ParseMode.HTML
        )
        return

    data = await state.get_data()
    country_name = data["country_name"]

    async with async_session() as session:
        result = await session.execute(
            select(Country).where(Country.name == country_name)
        )
        country = result.scalar_one_or_none()
        if country:
            country.price = new_price
        else:
            session.add(Country(name=country_name, code=country_name[:2].upper(), price=new_price))
        await session.commit()

    await message.answer(
        f'<b><tg-emoji emoji-id="{em("check")}">✅</tg-emoji> Цена обновлена!</b>\n\n'
        f'<b>{country_name}:</b> {format_price(new_price)} ₽',
        parse_mode=ParseMode.HTML,
        reply_markup=get_admin_reply_keyboard()
    )
    await state.clear()


@router.message(F.text == "Выдать баланс")
async def admin_give_balance(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    await message.answer(
        f'<b><tg-emoji emoji-id="{em("send_money")}">🪙</tg-emoji> Введите ID пользователя:</b>',
        parse_mode=ParseMode.HTML,
        reply_markup=get_admin_cancel_keyboard()
    )
    await state.set_state(GiveBalanceStates.waiting_for_user_id)


@router.message(StateFilter(GiveBalanceStates.waiting_for_user_id))
async def give_balance_user_id(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer(
            f'<tg-emoji emoji-id="{em("cross")}">❌</tg-emoji> Неверный ID',
            parse_mode=ParseMode.HTML
        )
        return

    await state.update_data(target_user_id=user_id)
    await message.answer(
        f'<b><tg-emoji emoji-id="{em("send_money")}">🪙</tg-emoji> Введите сумму для выдачи:</b>',
        parse_mode=ParseMode.HTML,
        reply_markup=get_admin_cancel_keyboard()
    )
    await state.set_state(GiveBalanceStates.waiting_for_amount)


@router.message(StateFilter(GiveBalanceStates.waiting_for_amount))
async def give_balance_amount(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    try:
        amount = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer(
            f'<tg-emoji emoji-id="{em("cross")}">❌</tg-emoji> Неверная сумма',
            parse_mode=ParseMode.HTML
        )
        return

    data = await state.get_data()
    target_user_id = data["target_user_id"]

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.id == target_user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(id=target_user_id)
            session.add(user)

        user.balance += amount
        await session.commit()

    await message.answer(
        f'<b><tg-emoji emoji-id="{em("check")}">✅</tg-emoji> Баланс выдан!</b>\n\n'
        f'<tg-emoji emoji-id="{em("profile")}">👤</tg-emoji> <b>ID:</b> <code>{target_user_id}</code>\n'
        f'<tg-emoji emoji-id="{em("coin")}">🪙</tg-emoji> <b>Сумма:</b> {format_price(amount)} ₽',
        parse_mode=ParseMode.HTML,
        reply_markup=get_admin_reply_keyboard()
    )
    await state.clear()


@router.message(F.text == "Рассылка")
async def admin_broadcast(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    await message.answer(
        f'<b><tg-emoji emoji-id="{em("megaphone")}">📣</tg-emoji> Отправьте сообщение для рассылки всем пользователям:</b>',
        parse_mode=ParseMode.HTML,
        reply_markup=get_admin_broadcast_keyboard()
    )
    await state.set_state(BroadcastStates.waiting_for_message)


@router.message(StateFilter(BroadcastStates.waiting_for_message))
async def broadcast_send(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

        sent_count = 0
        for user in users:
            try:
                await message.copy_to(chat_id=user.id)
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send to {user.id}: {e}")

        await message.answer(
            f'<b><tg-emoji emoji-id="{em("check")}">✅</tg-emoji> Рассылка завершена!</b>\n\n'
            f'<tg-emoji emoji-id="{em("send")}">⬆</tg-emoji> <b>Отправлено:</b> {sent_count} пользователям',
            parse_mode=ParseMode.HTML,
            reply_markup=get_admin_reply_keyboard()
        )

    await state.clear()


@router.message(F.text == "CryptoBot Token")
async def admin_cryptobot_token(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    current_token = await get_crypto_bot_token()
    masked = current_token[:10] + "..." if current_token else "Не указан"

    await message.answer(
        f'<b><tg-emoji emoji-id="{em("cryptobot")}">👾</tg-emoji> Настройка CryptoBot Token</b>\n\n'
        f'<tg-emoji emoji-id="{em("tag")}">🏷</tg-emoji> <b>Текущий токен:</b> <code>{masked}</code>\n\n'
        f'<i>Введите новый токен:</i>',
        parse_mode=ParseMode.HTML,
        reply_markup=get_admin_cancel_keyboard()
    )
    await state.set_state(CryptobotTokenStates.waiting_for_token)


@router.message(StateFilter(CryptobotTokenStates.waiting_for_token))
async def cryptobot_token_set(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    new_token = message.text.strip()

    async with async_session() as session:
        result = await session.execute(select(AdminSettings).limit(1))
        settings = result.scalar_one_or_none()

        if not settings:
            settings = AdminSettings(crypto_bot_token=new_token)
            session.add(settings)
        else:
            settings.crypto_bot_token = new_token

        await session.commit()

    await message.answer(
        f'<b><tg-emoji emoji-id="{em("check")}">✅</tg-emoji> CryptoBot токен обновлён!</b>',
        parse_mode=ParseMode.HTML,
        reply_markup=get_admin_reply_keyboard()
    )
    await state.clear()


# ==================== CANCEL HANDLERS ====================
@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        f'<b><tg-emoji emoji-id="{em("cross")}">❌</tg-emoji> Действие отменено</b>',
        parse_mode=ParseMode.HTML
    )
    if callback.from_user.id in ADMIN_IDS:
        await callback.message.answer(
            f'<tg-emoji emoji-id="{em("home")}">🏘</tg-emoji> <b>Админ-панель:</b>',
            parse_mode=ParseMode.HTML,
            reply_markup=get_admin_reply_keyboard()
        )
    await callback.answer()


@router.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        f'<b><tg-emoji emoji-id="{em("cross")}">❌</tg-emoji> Платёж отменён</b>',
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.callback_query(F.data == "cancel_broadcast")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        f'<b><tg-emoji emoji-id="{em("cross")}">❌</tg-emoji> Рассылка отменена</b>',
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        f'<b><tg-emoji emoji-id="{em("home")}">🏘</tg-emoji> Главное меню</b>',
        parse_mode=ParseMode.HTML
    )
    if callback.from_user.id in ADMIN_IDS:
        await callback.message.answer(
            f'<tg-emoji emoji-id="{em("home")}">🏘</tg-emoji> <b>Админ-панель:</b>',
            parse_mode=ParseMode.HTML,
            reply_markup=get_admin_reply_keyboard()
        )
    else:
        await callback.message.answer(
            f'<tg-emoji emoji-id="{em("home")}">🏘</tg-emoji> <b>Главное меню:</b>',
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_reply_keyboard()
        )
    await callback.answer()


# ==================== GET COUNTRIES PRICES ====================
@router.callback_query(F.data.startswith("admin_countries_"))
async def admin_countries_page(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа", show_alert=True)
        return

    page = int(callback.data.split("_")[2])

    await callback.message.edit_text(
        f'<b><tg-emoji emoji-id="{em("box")}">📦</tg-emoji> Выберите страну:</b>',
        parse_mode=ParseMode.HTML,
        reply_markup=get_countries_inline_keyboard(page=page, prefix="add_country")
    )
    await callback.answer()


# ==================== MAIN ====================
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="profile", description="Профиль"),
        BotCommand(command="buy", description="Купить аккаунт"),
    ]
    await bot.set_my_commands(commands)


async def main():
    await init_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp.include_router(router)

    await set_commands(bot)

    logger.info("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
