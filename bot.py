import json
import os
import asyncio
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ===== Загрузка токена из .env =====
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError(
        "❌ BOT_TOKEN не найден!\n"
        "Создай файл .env в корне проекта и добавь строку:\n"
        "BOT_TOKEN=твой_токен_от_BotFather"
    )

# ===== Файл для хранения данных =====
DATA_FILE = "user_data.json"

# ===== Инициализация бота =====
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ===== Работа с JSON =====
def load_data():
    """Загружает данные из JSON-файла"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_data(data):
    """Сохраняет данные в JSON-файл"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_user_data(user_id):
    """Получает данные пользователя"""
    data = load_data()
    return data.get(str(user_id), {"files": [], "counter": 0})


def update_user_data(user_id, user_data):
    """Обновляет данные пользователя"""
    data = load_data()
    data[str(user_id)] = user_data
    save_data(data)


# ===== Клавиатура =====
def get_main_keyboard():
    """Создаёт инлайн-клавиатуру с двумя кнопками"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📁 Сохранить файл", callback_data="save_file")
    builder.button(text="📊 Мои файлы", callback_data="my_files")
    builder.adjust(2)
    return builder.as_markup()


# ===== Обработчики =====
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    user_data = get_user_data(user_id)

    await message.answer(
        f"Привет, {message.from_user.first_name}!\n\n"
        f"Я бот для сохранения файлов.\n"
        f"Твоих сохранённых файлов: {len(user_data['files'])}\n\n"
        f"Используй кнопки ниже:",
        reply_markup=get_main_keyboard(),
    )


@dp.callback_query(lambda c: c.data == "save_file")
async def process_save_file(callback: types.CallbackQuery):
    """Обработчик кнопки сохранения файла"""
    user_id = callback.from_user.id
    user_data = get_user_data(user_id)

    user_data["counter"] += 1
    user_data["files"].append(f"Файл #{user_data['counter']}")
    update_user_data(user_id, user_data)

    await callback.message.answer(
        f"✅ Файл сохранён!\n"
        f"Всего файлов: {len(user_data['files'])}"
    )
    await callback.answer("Файл сохранён!")


@dp.callback_query(lambda c: c.data == "my_files")
async def process_my_files(callback: types.CallbackQuery):
    """Обработчик кнопки просмотра файлов"""
    user_id = callback.from_user.id
    user_data = get_user_data(user_id)

    if not user_data["files"]:
        await callback.message.answer("У тебя пока нет сохранённых файлов.")
    else:
        files_list = "\n".join(f"• {f}" for f in user_data["files"])
        await callback.message.answer(f"📁 Твои файлы:\n\n{files_list}")
    await callback.answer()


# ===== Запуск =====
async def main():
    print("✅ Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())