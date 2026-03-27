import asyncio
import logging
import os
import json
from datetime import datetime, timedelta
import re

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# ---------- Загрузка переменных окружения ----------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Поддержка нескольких администраторов
ADMIN_IDS = []
admin_ids_str = os.getenv("ADMIN_IDS")
if admin_ids_str:
    ADMIN_IDS = [int(x.strip()) for x in admin_ids_str.split(',') if x.strip()]
else:
    admin_id = os.getenv("ADMIN_ID")
    if admin_id:
        if ',' in admin_id:
            ADMIN_IDS = [int(x.strip()) for x in admin_id.split(',') if x.strip()]
        else:
            ADMIN_IDS = [int(admin_id)]

if not ADMIN_IDS:
    logging.warning("Не задан ни ADMIN_ID, ни ADMIN_IDS. Админ-панель будет недоступна.")

# ---------- Логирование ----------
logging.basicConfig(level=logging.INFO)

# ---------- Инициализация бота ----------
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

# ---------- Файл для хранения пользователей ----------
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(list(users), f)

users = load_users()

def add_user(user_id):
    if user_id not in users:
        users.add(user_id)
        save_users(users)

# ---------- Состояния FSM для админ-рассылки ----------
class BroadcastStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_photo = State()
    waiting_for_video_link = State()
    waiting_for_time = State()
    confirming = State()

# ---------- КЛАВИАТУРЫ ----------
admin_main_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📢 Новая рассылка", callback_data="admin_new_broadcast"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
        ],
        [
            InlineKeyboardButton(text="📋 Список пользователей", callback_data="admin_users_list"),
            InlineKeyboardButton(text="❌ Закрыть", callback_data="admin_close")
        ]
    ]
)

time_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🚀 Сейчас", callback_data="time_now"),
            InlineKeyboardButton(text="⏰ Через 1 час", callback_data="time_1h")
        ],
        [
            InlineKeyboardButton(text="⏰ Через 3 часа", callback_data="time_3h"),
            InlineKeyboardButton(text="⌨️ Свой вариант", callback_data="time_custom")
        ],
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")
        ]
    ]
)

confirm_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, отправить", callback_data="confirm_send"),
            InlineKeyboardButton(text="✏️ Изменить текст", callback_data="confirm_edit_text")
        ],
        [
            InlineKeyboardButton(text="🖼️ Изменить фото", callback_data="confirm_edit_photo"),
            InlineKeyboardButton(text="🎥 Изменить видео", callback_data="confirm_edit_video")
        ],
        [
            InlineKeyboardButton(text="⏰ Изменить время", callback_data="confirm_edit_time"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")
        ]
    ]
)

cancel_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить", callback_data="admin_cancel")]
    ]
)

# ---------- КЛИЕНТСКАЯ ЧАСТЬ ----------
whatsapp_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🗨️ Ватсап", url="https://wa.me/992200504437")]
    ]
)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    add_user(message.from_user.id)
    photo = FSInputFile("photo.jpg")
    user_name = message.from_user.first_name
    caption_text = (
        f"👋 Салом {user_name}!\n\n"
        "📚 Ба шумо дарси «5 қадам барои даромад дар Инстаграм» пешкаш карда мешавад!\n\n"
        "🎯 Дар ин дарс муҳокима мешавад:\n"
        "- Чӣ тавр стратегия тартиб додан?\n"
        "- Дар бозор чӣ хатоҳо вуҷуд дорад?\n"
        "- Ба чӣ чизҳо таваҷҷӯҳ кардан лозим?\n\n"
        "📘 Маълумот дар бораи курси Маркетинг, СММ ва Бренд\n\n"
        "🎥 https://www.youtube.com/watch?v=kTdFLbqT-2Y\n\n"
        "📞 Раками телефон: +992200504437"
    )
    await message.answer_photo(
        photo=photo,
        caption=caption_text,
        parse_mode="HTML",
        reply_markup=whatsapp_kb
    )

# ---------- АДМИН-ПАНЕЛЬ ----------
def is_admin(user_id):
    return user_id in ADMIN_IDS

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к админ-панели.")
        return
    await message.answer(
        f"🔧 <b>Админ-панель</b>\n\n"
        f"📊 Всего пользователей: <b>{len(users)}</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=admin_main_kb
    )

@dp.callback_query(lambda c: c.data == "admin_stats")
async def show_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback.answer()
    await callback.message.answer(
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего пользователей: <b>{len(users)}</b>\n"
        f"📅 Активных: <b>{len(users)}</b>\n\n"
        f"💡 <i>Каждый пользователь, который запустил /start, добавлен в список</i>",
        parse_mode="HTML",
        reply_markup=admin_main_kb
    )

@dp.callback_query(lambda c: c.data == "admin_users_list")
async def show_users_list(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback.answer()
    if not users:
        await callback.message.answer("📋 Список пользователей пуст.")
        return
    users_list_text = f"📋 <b>Список пользователей</b>\n\nВсего: <b>{len(users)}</b> пользователей\n\n"
    sample = list(users)[:10]
    if sample:
        users_list_text += "Примеры ID:\n"
        for uid in sample:
            users_list_text += f"• <code>{uid}</code>\n"
        if len(users) > 10:
            users_list_text += f"\n... и ещё {len(users) - 10} пользователей"
    await callback.message.answer(users_list_text, parse_mode="HTML", reply_markup=admin_main_kb)

@dp.callback_query(lambda c: c.data == "admin_close")
async def close_admin(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback.answer()
    await state.clear()
    await callback.message.delete()

@dp.callback_query(lambda c: c.data == "admin_cancel")
async def cancel_action(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback.answer()
    await state.clear()
    await callback.message.answer(
        "❌ Действие отменено.\n\nВернуться в админ-панель: /admin",
        reply_markup=None
    )

# ---------- СОЗДАНИЕ РАССЫЛКИ ----------
@dp.callback_query(lambda c: c.data == "admin_new_broadcast")
async def new_broadcast(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback.answer()
    await state.set_state(BroadcastStates.waiting_for_text)
    await callback.message.answer(
        "📝 <b>Шаг 1 из 4: Введите текст</b>\n\n"
        "Введите текст сообщения для рассылки.\n"
        "Можно использовать <b>HTML-разметку</b>:\n"
        "• <b>жирный</b> — <code>&lt;b&gt;текст&lt;/b&gt;</code>\n"
        "• <i>курсив</i> — <code>&lt;i&gt;текст&lt;/i&gt;</code>\n\n"
        "❌ Чтобы отменить, нажмите кнопку:",
        parse_mode="HTML",
        reply_markup=cancel_kb
    )

@dp.message(BroadcastStates.waiting_for_text)
async def process_text(message: types.Message, state: FSMContext):
    await state.update_data(text=message.text)
    await state.set_state(BroadcastStates.waiting_for_photo)
    await message.answer(
        "📸 <b>Шаг 2 из 4: Добавьте фото</b>\n\n"
        "Отправьте фото (можно просто как изображение).\n"
        "Или отправьте <b>«пропустить»</b>, если фото не нужно.\n\n"
        "❌ Чтобы отменить, нажмите кнопку:",
        parse_mode="HTML",
        reply_markup=cancel_kb
    )

@dp.message(BroadcastStates.waiting_for_photo)
async def process_photo(message: types.Message, state: FSMContext):
    photo = None
    if message.photo:
        photo = message.photo[-1].file_id
        await message.answer("✅ Фото получено!")
    elif message.text and message.text.strip().lower() == "пропустить":
        photo = None
        await message.answer("✅ Фото пропущено, рассылка будет без фото.")
    else:
        await message.answer(
            "❌ Пожалуйста, отправьте фото или напишите «пропустить».\n\n"
            "Или нажмите кнопку отмены:",
            reply_markup=cancel_kb
        )
        return
    await state.update_data(photo=photo)
    await state.set_state(BroadcastStates.waiting_for_video_link)
    await message.answer(
        "🎥 <b>Шаг 3 из 4: Добавьте ссылку на видео</b>\n\n"
        "Введите ссылку на видео (YouTube и т.п.).\n"
        "Ссылка будет добавлена в текст сообщения как обычная ссылка.\n"
        "Или отправьте <b>«пропустить»</b>, если ссылка не нужна.\n\n"
        "❌ Чтобы отменить, нажмите кнопку:",
        parse_mode="HTML",
        reply_markup=cancel_kb
    )

@dp.message(BroadcastStates.waiting_for_video_link)
async def process_video_link(message: types.Message, state: FSMContext):
    video_link = None
    if message.text and message.text.strip().lower() == "пропустить":
        video_link = None
        await message.answer("✅ Видео пропущено, ссылки не будет.")
    elif message.text and (message.text.startswith("http://") or message.text.startswith("https://")):
        video_link = message.text.strip()
        await message.answer("✅ Ссылка получена! Она будет добавлена в текст.")
    else:
        await message.answer(
            "❌ Это не похоже на ссылку.\n"
            "Введите корректную ссылку (начинается с http:// или https://)\n"
            "или напишите «пропустить».\n\n"
            "Или нажмите кнопку отмены:",
            reply_markup=cancel_kb
        )
        return
    await state.update_data(video_link=video_link)
    await state.set_state(BroadcastStates.waiting_for_time)
    await message.answer(
        f"⏰ <b>Шаг 4 из 4: Выберите время отправки</b>\n\n"
        f"📊 <b>Важно:</b> Рассылку получат <b>{len(users)} пользователей</b>\n\n"
        "Выберите когда отправить:",
        parse_mode="HTML",
        reply_markup=time_kb
    )

@dp.callback_query(lambda c: c.data.startswith("time_") and c.data != "time_custom")
async def process_time_choice(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback.answer()
    data = callback.data
    delay_seconds = 0
    if data == "time_now":
        delay_seconds = 0
    elif data == "time_1h":
        delay_seconds = 3600
    elif data == "time_3h":
        delay_seconds = 10800
    else:
        await callback.message.answer("❌ Неизвестный выбор.")
        return
    await state.update_data(delay_seconds=delay_seconds)
    await show_preview(callback.message, state)

@dp.callback_query(lambda c: c.data == "time_custom")
async def custom_time_request(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback.answer()
    await state.set_state(BroadcastStates.waiting_for_time)
    await callback.message.answer(
        "⌨️ <b>Введите время вручную</b>\n\n"
        "Варианты:\n"
        "• <code>+2</code> — через 2 часа\n"
        "• <code>+1.5</code> — через 1.5 часа\n"
        "• <code>14:30</code> — сегодня в 14:30\n"
        "• <code>14:30 25.12</code> — 25 декабря в 14:30\n\n"
        "❌ Чтобы отменить, нажмите кнопку:",
        parse_mode="HTML",
        reply_markup=cancel_kb
    )

@dp.message(BroadcastStates.waiting_for_time)
async def process_custom_time(message: types.Message, state: FSMContext):
    user_input = message.text.strip()
    delay_seconds = parse_time(user_input)
    if delay_seconds is None:
        await message.answer(
            "❌ Неверный формат.\n"
            "Используйте: <code>+2</code>, <code>14:30</code> или <code>14:30 25.12</code>\n\n"
            "Или нажмите кнопку отмены:",
            parse_mode="HTML",
            reply_markup=cancel_kb
        )
        return
    if delay_seconds <= 0:
        await message.answer(
            "❌ Время должно быть в будущем.\n\n"
            "Попробуйте ещё раз:",
            reply_markup=cancel_kb
        )
        return
    await state.update_data(delay_seconds=delay_seconds)
    await show_preview(message, state)

def parse_time(user_input):
    now = datetime.now()
    if user_input.startswith('+'):
        try:
            hours = float(user_input[1:])
            return int(hours * 3600)
        except:
            return None
    if re.match(r'^\d{1,2}:\d{2}$', user_input):
        try:
            target_time = datetime.strptime(user_input, "%H:%M").time()
            target = datetime.combine(now.date(), target_time)
            if target < now:
                target += timedelta(days=1)
            return (target - now).total_seconds()
        except:
            return None
    if re.match(r'^\d{1,2}:\d{2}\s+\d{1,2}\.\d{2}$', user_input):
        try:
            time_part, date_part = user_input.split()
            target_time = datetime.strptime(time_part, "%H:%M").time()
            target_date = datetime.strptime(date_part, "%d.%m").date()
            year = now.year
            target = datetime.combine(target_date.replace(year=year), target_time)
            if target < now:
                target = datetime.combine(target_date.replace(year=year+1), target_time)
            return (target - now).total_seconds()
        except:
            return None
    return None

# ---------- ПРЕДПРОСМОТР ----------
async def show_preview(message: types.Message, state: FSMContext):
    data = await state.get_data()
    text = data.get("text", "")
    photo = data.get("photo")
    video_link = data.get("video_link")
    delay = data.get("delay_seconds", 0)
    users_count = len(users)

    if video_link:
        text += f"\n\n🎥 Смотреть видео: {video_link}"

    if delay == 0:
        time_text = "🚀 Сейчас"
    else:
        hours = int(delay // 3600)
        minutes = int((delay % 3600) // 60)
        if hours > 0 and minutes > 0:
            time_text = f"⏰ Через {hours} ч. {minutes} мин."
        elif hours > 0:
            time_text = f"⏰ Через {hours} ч."
        else:
            time_text = f"⏰ Через {minutes} мин."

    preview_header = (
        f"📬 ПРЕДПРОСМОТР РАССЫЛКИ\n\n"
        f"👥 Получателей: {users_count}\n"
        f"⏱️ Отправка: {time_text}\n"
        f"{'📸 Есть фото' if photo else '📸 Без фото'}\n"
        f"{'🎥 Есть видео-ссылка' if video_link else '🎥 Без видео'}\n"
        f"{'─' * 30}\n\n"
    )
    full_text = preview_header + text

    if photo:
        await message.answer_photo(photo=photo, caption=full_text, parse_mode=None)
    else:
        await message.answer(full_text, parse_mode=None)

    await state.set_state(BroadcastStates.confirming)
    await message.answer(
        "✅ Подтвердите отправку\n\n"
        "Всё верно? Если нужно что-то изменить, выберите нужный пункт:",
        reply_markup=confirm_kb
    )

# ---------- ПОДТВЕРЖДЕНИЕ ----------
@dp.callback_query(lambda c: c.data.startswith("confirm_"))
async def confirm_broadcast(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback.answer()
    action = callback.data
    if action == "confirm_send":
        data = await state.get_data()
        delay = data.get("delay_seconds", 0)
        users_count = len(users)
        if users_count == 0:
            await callback.message.answer("❌ Нет пользователей для рассылки!")
            await state.clear()
            return
        if delay == 0:
            status_msg = await callback.message.answer(
                f"🚀 <b>Начинаю рассылку...</b>\n\n"
                f"👥 Получателей: {users_count}\n"
                f"⏱️ Отправка: сейчас\n\n"
                f"<i>Отправка может занять некоторое время...</i>",
                parse_mode="HTML"
            )
            await send_broadcast(data, status_msg)
        else:
            hours = int(delay // 3600)
            minutes = int((delay % 3600) // 60)
            time_str = f"{hours} ч. {minutes} мин." if hours > 0 else f"{minutes} мин."
            await callback.message.answer(
                f"⏳ <b>Рассылка запланирована!</b>\n\n"
                f"👥 Получателей: {users_count}\n"
                f"⏱️ Отправка через: {time_str}\n\n"
                f"<i>Я уведомлю вас, когда рассылка начнётся и завершится.</i>",
                parse_mode="HTML"
            )
            asyncio.create_task(schedule_broadcast(data, delay, callback.message.chat.id))
        await state.clear()
    elif action == "confirm_edit_text":
        await state.set_state(BroadcastStates.waiting_for_text)
        await callback.message.answer(
            "✏️ <b>Измените текст</b>\n\nВведите новый текст:",
            parse_mode="HTML",
            reply_markup=cancel_kb
        )
    elif action == "confirm_edit_photo":
        await state.set_state(BroadcastStates.waiting_for_photo)
        await callback.message.answer(
            "🖼️ <b>Измените фото</b>\n\nОтправьте новое фото или «пропустить»:",
            parse_mode="HTML",
            reply_markup=cancel_kb
        )
    elif action == "confirm_edit_video":
        await state.set_state(BroadcastStates.waiting_for_video_link)
        await callback.message.answer(
            "🎥 <b>Измените видео-ссылку</b>\n\nВведите новую ссылку или «пропустить»:",
            parse_mode="HTML",
            reply_markup=cancel_kb
        )
    elif action == "confirm_edit_time":
        await state.set_state(BroadcastStates.waiting_for_time)
        await callback.message.answer(
            "⏰ <b>Измените время</b>\n\nВыберите новый вариант:",
            parse_mode="HTML",
            reply_markup=time_kb
        )

# ---------- ФУНКЦИИ ОТПРАВКИ ----------
async def send_broadcast(data: dict, status_msg: types.Message = None):
    text = data.get("text", "")
    photo = data.get("photo")
    video_link = data.get("video_link")
    if video_link:
        text += f"\n\n🎥 Смотреть видео: {video_link}"
    users_list = list(users)
    total = len(users_list)
    success = 0
    fail = 0
    last_update = 0
    for i, user_id in enumerate(users_list):
        try:
            if photo:
                await bot.send_photo(user_id, photo=photo, caption=text, parse_mode="HTML")
            else:
                await bot.send_message(user_id, text, parse_mode="HTML")
            success += 1
        except Exception as e:
            logging.error(f"Ошибка отправки {user_id}: {e}")
            fail += 1
        await asyncio.sleep(0.05)
        progress = int((i + 1) / total * 100)
        if status_msg and progress >= last_update + 10:
            last_update = progress
            try:
                await status_msg.edit_text(
                    f"🚀 <b>Идёт рассылка...</b>\n\n"
                    f"📊 Прогресс: {progress}%\n"
                    f"✅ Успешно: {success}\n"
                    f"❌ Ошибок: {fail}\n"
                    f"👥 Осталось: {total - (i + 1)}\n\n"
                    f"<i>Пожалуйста, подождите...</i>",
                    parse_mode="HTML"
                )
            except:
                pass
    if status_msg:
        await status_msg.edit_text(
            f"✅ <b>Рассылка завершена!</b>\n\n"
            f"📊 Итог:\n"
            f"👥 Всего: {total}\n"
            f"✅ Успешно: {success}\n"
            f"❌ Ошибок: {fail}\n\n"
            f"<i>Сообщение получили {success} из {total} пользователей</i>",
            parse_mode="HTML"
        )

async def schedule_broadcast(data, delay, admin_chat_id):
    await asyncio.sleep(delay)
    await bot.send_message(
        admin_chat_id,
        f"🔔 <b>Начинаю запланированную рассылку...</b>\n\n"
        f"👥 Получателей: {len(users)}\n"
        f"⏱️ Время отправки: сейчас",
        parse_mode="HTML"
    )
    status_msg = await bot.send_message(
        admin_chat_id,
        "🚀 <b>Идёт рассылка...</b>\n<i>Пожалуйста, подождите...</i>",
        parse_mode="HTML"
    )
    await send_broadcast(data, status_msg)
    await bot.send_message(
        admin_chat_id,
        "✅ <b>Запланированная рассылка завершена!</b>",
        parse_mode="HTML"
    )

# ---------- КОМАНДА ОТМЕНЫ ----------
@dp.message(Command("cancel"))
async def cancel_cmd(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активного действия.")
        return
    await state.clear()
    await message.answer("❌ Действие отменено.")

# ---------- ЗАПУСК ----------
async def main():
    # Удаляем вебхук с повторными попытками
    for attempt in range(5):
        try:
            info = await bot.get_webhook_info()
            if info.url:
                logging.info(f"Текущий вебхук: {info.url}. Удаляем...")
                await bot.delete_webhook(drop_pending_updates=True)
                logging.info("Вебхук удалён")
            else:
                logging.info("Вебхук не установлен")
            break
        except Exception as e:
            logging.error(f"Ошибка при удалении вебхука (попытка {attempt+1}): {e}")
            await asyncio.sleep(2)
    else:
        logging.warning("Не удалось удалить вебхук. Продолжаем...")

    await asyncio.sleep(3)
    await bot.delete_webhook(drop_pending_updates=True)
    await asyncio.sleep(1)

    logging.info("Запускаем polling...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
