import asyncio
import json
import os
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from dotenv import load_dotenv


# =========================
# НАСТРОЙКИ
# =========================

load_dotenv()

TOKEN = os.getenv("TELEGRAM_API_TOKEN")

if not TOKEN:
    raise ValueError("Не найден TELEGRAM_API_TOKEN в файле .env")


# Файл, где будут храниться данные
DATA_FILE = Path("data.json")

bot = Bot(token=TOKEN)
dp = Dispatcher()


# =========================
# РАБОТА С JSON
# =========================

def load_data():
    """Загружает данные из JSON."""

    if not DATA_FILE.exists():
        return {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):
        return {}


def save_data(data):
    """Сохраняет данные в JSON."""

    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4
        )


data = load_data()


# =========================
# INLINE-КЛАВИАТУРА
# =========================

def main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Добавить",
                    callback_data="add"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📚 Мои записи",
                    callback_data="list"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Удалить",
                    callback_data="delete"
                )
            ]
        ]
    )


# =========================
# ВРЕМЕННОЕ СОСТОЯНИЕ
# =========================

waiting_for_text = set()
waiting_for_delete = set()


# =========================
# /start
# =========================

@dp.message(CommandStart())
async def start(message: Message):

    user_id = str(message.from_user.id)

    # Если пользователя ещё нет
    if user_id not in data:
        data[user_id] = []

        save_data(data)

    await message.answer(
        "👋 Привет!\n\n"
        "Я бот для хранения твоих заметок.\n"
        "Выбери действие:",
        reply_markup=main_keyboard()
    )


# =========================
# КНОПКА "ДОБАВИТЬ"
# =========================

@dp.callback_query(F.data == "add")
async def add_button(callback: CallbackQuery):

    user_id = str(callback.from_user.id)

    waiting_for_text.add(user_id)

    await callback.message.answer(
        "📝 Напиши информацию, которую нужно запомнить.\n\n"
        "Например:\n"
        "Купить молоко\n"
        "Пароль от Wi-Fi: example123\n"
        "Идея для проекта: сделать сайт"
    )

    await callback.answer()


# =========================
# ПОЛУЧЕНИЕ ТЕКСТА
# =========================

@dp.message(F.text)
async def receive_text(message: Message):

    user_id = str(message.from_user.id)

    # Если пользователь добавляет запись
    if user_id in waiting_for_text:

        text = message.text.strip()

        if not text:
            await message.answer("❌ Запись не может быть пустой.")
            return

        if user_id not in data:
            data[user_id] = []

        data[user_id].append(text)

        save_data(data)

        waiting_for_text.remove(user_id)

        await message.answer(
            "✅ Запомнил!\n\n"
            f"📌 {text}",
            reply_markup=main_keyboard()
        )

        return

    # Если пользователь удаляет запись
    if user_id in waiting_for_delete:

        try:
            number = int(message.text)
        except ValueError:
            await message.answer(
                "❌ Напиши номер записи.\n"
                "Например: 2"
            )
            return

        notes = data.get(user_id, [])

        if number < 1 or number > len(notes):
            await message.answer(
                "❌ Записи с таким номером нет."
            )
            return

        deleted = notes.pop(number - 1)

        save_data(data)

        waiting_for_delete.remove(user_id)

        await message.answer(
            "🗑 Запись удалена:\n\n"
            f"📌 {deleted}",
            reply_markup=main_keyboard()
        )

        return


# =========================
# КНОПКА "МОИ ЗАПИСИ"
# =========================

@dp.callback_query(F.data == "list")
async def list_button(callback: CallbackQuery):

    user_id = str(callback.from_user.id)

    notes = data.get(user_id, [])

    if not notes:
        await callback.message.answer(
            "📭 У тебя пока нет сохранённых записей.",
            reply_markup=main_keyboard()
        )

        await callback.answer()
        return

    text = "📚 Твои записи:\n\n"

    for i, note in enumerate(notes, start=1):
        text += f"{i}. {note}\n\n"

    await callback.message.answer(
        text,
        reply_markup=main_keyboard()
    )

    await callback.answer()


# =========================
# КНОПКА "УДАЛИТЬ"
# =========================

@dp.callback_query(F.data == "delete")
async def delete_button(callback: CallbackQuery):

    user_id = str(callback.from_user.id)

    notes = data.get(user_id, [])

    if not notes:
        await callback.message.answer(
            "📭 У тебя нет записей для удаления.",
            reply_markup=main_keyboard()
        )

        await callback.answer()
        return

    text = "🗑 Какую запись удалить?\n\n"

    for i, note in enumerate(notes, start=1):
        text += f"{i}. {note}\n"

    text += "\nНапиши номер записи."

    waiting_for_delete.add(user_id)

    await callback.message.answer(text)

    await callback.answer()


# =========================
# ЗАПУСК
# =========================

async def main():

    print("Бот запущен!")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())


