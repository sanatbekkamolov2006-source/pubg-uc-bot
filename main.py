import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# .env faylidan tokenni yuklash
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)

# Bot va Dispatcher obyektlari
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Narxlar (Yakuniy narxlar)
UC_PRICES = {
    "30_uc": {"name": "30 UC", "price": 6100},
    "60_uc": {"name": "60 UC", "price": 12100},
    "325_uc": {"name": "300 + 25 UC", "price": 60500},
    "660_uc": {"name": "600 + 60 UC", "price": 121000},
    "1800_uc": {"name": "1500 + 300 UC", "price": 302000},
    "3850_uc": {"name": "3000 + 850 UC", "price": 604000},
    "8100_uc": {"name": "6000 + 2100 UC", "price": 1208000},
    "16200_uc": {"name": "12000 + 4200 UC", "price": 2415000},
    "24300_uc": {"name": "18000 + 6300 UC", "price": 3622500},
    "32400_uc": {"name": "24000 + 8400 UC", "price": 4830000},
    "40500_uc": {"name": "30000 + 10500 UC", "price": 6037500},
    "48600_uc": {"name": "36000 + 12600 UC", "price": 7245000},
    "81000_uc": {"name": "60000 + 21000 UC", "price": 12075000},
}

# FSM holatlari
class OrderUC(StatesGroup):
    waiting_for_id = State()
    waiting_for_payment = State()

# Asosiy menyu tugmalari
def main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 UC Sotib Olish")],
            [KeyboardButton(text="👤 Mening Profilim"), KeyboardButton(text="📞 Admin bilan bog'lanish")],
            [KeyboardButton(text="ℹ️ Ma'lumot")]
        ],
        resize_keyboard=True
    )
    return keyboard

# UC paketlari tugmalari
def uc_packages_keyboard():
    buttons = []
    for key, item in UC_PRICES.items():
        buttons.append([InlineKeyboardButton(text=f"{item['name']} - {item['price']:,} UZS", callback_data=f"buy_{key}")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

# /start komandasi
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        f"Assalomu alaykum, {message.from_user.full_name}!\n"
        f"PUBG Mobile UC sotib olish botiga xush kelibsiz.\n"
        f"Kerakli UC paketini tanlang va buyurtma bering.",
        reply_markup=main_menu()
    )

# UC sotib olish tugmasi bosilganda
@dp.message(F.text == "🛒 UC Sotib Olish")
async def show_packages(message: types.Message):
    await message.answer("Kerakli UC paketini tanlang:", reply_markup=uc_packages_keyboard())

# UC paketi tanlanganda
@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery, state: FSMContext):
    package_key = callback.data.replace("buy_", "")
    package = UC_PRICES.get(package_key)
    if not package:
        await callback.answer("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")
        return
    
    await state.update_data(package=package)
    await callback.message.answer(
        f"Siz {package['name']} tanladingiz.\n"
        f"Narxi: {package['price']:,} UZS.\n\n"
        f"Iltimos, PUBG Mobile Player ID raqamingizni kiriting:"
    )
    await state.set_state(OrderUC.waiting_for_id)
    await callback.answer()

# Player ID kiritilganda
@dp.message(OrderUC.waiting_for_id)
async def process_id(message: types.Message, state: FSMContext):
    player_id = message.text
    if not player_id.isdigit():
        await message.answer("Iltimos, faqat raqamlardan iborat Player ID kiriting.")
        return
    
    data = await state.get_data()
    package = data['package']
    
    await state.update_data(player_id=player_id)
    
    payment_text = (
        f"✅ Buyurtma tasdiqlandi!\n\n"
        f"📦 Paket: {package['name']}\n"
        f"🆔 Player ID: {player_id}\n"
        f"💰 To'lov summasi: {package['price']:,} UZS\n\n"
        f"💳 To'lov qilish uchun karta raqami:\n"
        f"`8600 0000 0000 0000` (Namuna)\n"
        f"Ega: Bot Egasi\n\n"
        f"To'lovni amalga oshirgach, chekni (skrinshot) shu yerga yuboring."
    )
    
    await message.answer(payment_text, parse_mode="Markdown")
    await state.set_state(OrderUC.waiting_for_payment)

# To'lov cheki yuborilganda
@dp.message(OrderUC.waiting_for_payment, F.photo)
async def process_payment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    package = data['package']
    player_id = data['player_id']
    
    await message.answer(
        "Rahmat! To'lov cheki qabul qilindi.\n"
        "Adminlarimiz tekshirib, UC ni 5-15 daqiqa ichida hisobingizga o'tkazib berishadi.",
        reply_markup=main_menu()
    )
    await state.clear()

# Admin bilan bog'lanish
@dp.message(F.text == "📞 Admin bilan bog'lanish")
async def contact_admin(message: types.Message):
    await message.answer("Savollar bo'yicha admin bilan bog'laning: @admin_username")

# Ma'lumot
@dp.message(F.text == "ℹ️ Ma'lumot")
async def info_cmd(message: types.Message):
    await message.answer(
        "Ushbu bot orqali PUBG Mobile o'yini uchun UC sotib olishingiz mumkin.\n"
        "Barcha to'lovlar xavfsiz va UC yetkazib berish kafolatlangan.\n"
        "Buyurtmalar 5-15 daqiqa ichida bajariladi."
    )

# Profil
@dp.message(F.text == "👤 Mening Profilim")
async def profile_cmd(message: types.Message):
    await message.answer(
        f"👤 Ism: {message.from_user.full_name}\n"
        f"🆔 Telegram ID: {message.from_user.id}\n"
        f"📊 Buyurtmalar soni: 0"
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
