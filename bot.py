import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ════════════════════════════════════════════
#  ⚙️  НАСТРОЙКИ — ЗАМЕНИ НА СВОИ
# ════════════════════════════════════════════
BOT_TOKEN     = "8458402183:AAHQ225llgy2LKMMMSGM9lPW8XgfUB1l_Iw"
ADMIN_ID      = 7249758488
MANAGER_PHONE = "@Jannat_Abdullaeva_Admin"   # ← ВСТАВЬ НОМЕР МЕНЕДЖЕРА СЮДА
# ════════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher(storage=MemoryStorage())


# ─── FSM СОСТОЯНИЯ ───────────────────────────────────────────────────────────
class Quiz(StatesGroup):
    question = State()


# ─── ВОПРОСЫ ТЕСТА ───────────────────────────────────────────────────────────
QUESTIONS = [
    "❓ *Савол 1 аз 10*\n\nВақте касе туро танқид мекунад, ту зуд ранҷида мешавӣ?",
    "❓ *Савол 2 аз 10*\n\nБаъзан бе сабаби равшан худро танҳо ҳис мекунӣ?",
    "❓ *Савол 3 аз 10*\n\nОё ту аз партофта шудан ё рад шудан метарсӣ?",
    "❓ *Савол 4 аз 10*\n\nВақте асабонӣ мешавӣ, ором шудан бароят душвор аст?",
    "❓ *Савол 5 аз 10*\n\nОё ту зуд худро гунаҳкор ҳис мекунӣ, ҳатто вақте айбдор нестӣ?",
    "❓ *Савол 6 аз 10*\n\nБа ту гуфтани «не» ба дигарон мушкил аст?",
    "❓ *Савол 7 аз 10*\n\nБаъзан ҳис мекунӣ, ки муҳаббатро бояд «сазовор» шавӣ?",
    "❓ *Савол 8 аз 10*\n\nДар муносибатҳо аз ҳад вобаста ё баръакс сард мешавӣ?",
    "❓ *Савол 9 аз 10*\n\nОё дар дарунат ҳисси ғам ё холигии кӯҳна ҳаст?",
    "❓ *Савол 10 аз 10*\n\nВақте касе баланд гап мезанад, баданат танг мешавад?",
]

# А=2, Б=1, В=0
SCORES = {"A": 2, "B": 1, "C": 0}


# ─── КЛАВИАТУРЫ ──────────────────────────────────────────────────────────────
def kb_start():
    b = InlineKeyboardBuilder()
    b.button(text="🧪 ТЕСТ", callback_data="start_test")
    b.button(text="🆘 ЁРДАМ", callback_data="help")
    b.adjust(2)
    return b.as_markup()

def kb_begin_test():
    b = InlineKeyboardBuilder()
    b.button(text="▶️ ТЕСТРО ОҒОЗ КУН", callback_data="begin_quiz")
    return b.as_markup()

def kb_answer(q_index: int):
    b = InlineKeyboardBuilder()
    b.button(text="А — Бисёр вақт",  callback_data=f"ans_A_{q_index}")
    b.button(text="Б — Баъзан",       callback_data=f"ans_B_{q_index}")
    b.button(text="В — Қариб не",     callback_data=f"ans_C_{q_index}")
    if q_index > 0:
        b.button(text="🔙 Назад", callback_data="back")
    b.button(text="🏠 Меню", callback_data="main_menu")
    b.adjust(1)
    return b.as_markup()

def kb_result():
    b = InlineKeyboardBuilder()
    b.button(text="🔄 Такроран гузаштан", callback_data="start_test")
    b.button(text="📞 Менеҷер",           callback_data="contact_manager")
    b.button(text="🏠 Меню",               callback_data="main_menu")
    b.adjust(1)
    return b.as_markup()

def kb_menu_only():
    b = InlineKeyboardBuilder()
    b.button(text="🏠 Меню", callback_data="main_menu")
    return b.as_markup()


# ─── /start ──────────────────────────────────────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    photo = FSInputFile("photo_start.png")
    text = (
        "✨ *Хуш омадед!*\n\n"
        "Салом, дӯсти азиз! 👋\n\n"
        "Ин бот ба шумо кӯмак мекунад, ки ҳолати *кӯдаки дарунатонро* бифаҳмед.\n\n"
        "🌱 Тест хеле содда аст — танҳо 10 савол.\n"
        "Ҷавоб деҳ ва натиҷаро бубинед!\n\n"
        "👇 Яке аз тугмаҳоро пахш кунед:"
    )
    await message.answer_photo(photo=photo, caption=text,
                               parse_mode="Markdown", reply_markup=kb_start())


# ─── Кнопка ТЕСТ ─────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "start_test")
async def cb_test(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    photo = FSInputFile("photo_test.png")
    text = (
        "🧪 *ТЕСТ: «Оё кӯдаки даруни ту ҳанӯз захм дорад?»*\n\n"
        "📌 *Дастур:*\n"
        "Ба ҳар савол ростқавлона ҷавоб деҳ:\n\n"
        "• А — бисёр вақт\n"
        "• Б — баъзан\n"
        "• В — қариб не\n\n"
        "💡 Тест 10 савол дорад. Ҳозир тайёр?"
    )
    await call.message.answer_photo(photo=photo, caption=text,
                                    parse_mode="Markdown",
                                    reply_markup=kb_begin_test())


# ─── Начало теста ─────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "begin_quiz")
async def cb_begin(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.set_state(Quiz.question)
    await state.update_data(q_index=0, answers=[])
    await call.message.answer(
        QUESTIONS[0],
        parse_mode="Markdown",
        reply_markup=kb_answer(0)
    )


# ─── Ответы на вопросы ────────────────────────────────────────────────────────
@dp.callback_query(Quiz.question, F.data.startswith("ans_"))
async def cb_answer(call: CallbackQuery, state: FSMContext):
    await call.answer()
    parts   = call.data.split("_")
    letter  = parts[1]
    q_index = int(parts[2])

    data    = await state.get_data()
    current = data.get("q_index", 0)

    if q_index != current:
        return

    answers = data.get("answers", [])
    if len(answers) <= q_index:
        answers.append(letter)
    else:
        answers[q_index] = letter

    next_q = current + 1

    if next_q < len(QUESTIONS):
        await state.update_data(q_index=next_q, answers=answers)
        await call.message.answer(
            QUESTIONS[next_q],
            parse_mode="Markdown",
            reply_markup=kb_answer(next_q)
        )
    else:
        total_score = sum(SCORES[a] for a in answers)
        await state.clear()
        await send_result(call.message, total_score)


# ─── Кнопка НАЗАД ─────────────────────────────────────────────────────────────
@dp.callback_query(Quiz.question, F.data == "back")
async def cb_back(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    current = data.get("q_index", 0)

    if current <= 0:
        return

    prev_index = current - 1
    await state.update_data(q_index=prev_index)
    await call.message.answer(
        QUESTIONS[prev_index],
        parse_mode="Markdown",
        reply_markup=kb_answer(prev_index)
    )


# ─── Кнопка МЕНЮ ─────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "main_menu")
async def cb_main_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    photo = FSInputFile("photo_start.png")
    text = (
        "✨ *Хуш омадед!*\n\n"
        "Салом, дӯсти азиз! 👋\n\n"
        "Ин бот ба шумо кӯмак мекунад, ки ҳолати *кӯдаки дарунатонро* бифаҳмед.\n\n"
        "🌱 Тест хеле содда аст — танҳо 10 савол.\n"
        "Ҷавоб деҳ ва натиҷаро бубинед!\n\n"
        "👇 Яке аз тугмаҳоро пахш кунед:"
    )
    await call.message.answer_photo(photo=photo, caption=text,
                                    parse_mode="Markdown", reply_markup=kb_start())


# ─── Результат ────────────────────────────────────────────────────────────────
async def send_result(message: Message, score: int):
    if score <= 6:
        icon  = "🟢"
        title = "Кӯдаки дарун — нисбатан ором"
        body  = (
            "Ту аллакай бисёр чизро гузаштаӣ. 💪\n"
            "Аммо қабатҳои амиқ ҳанӯз метавонанд кушода шаванд.\n\n"
            "👉 *Қадами аввал:* худогоҳиро идома деҳ."
        )
    elif score <= 13:
        icon  = "🟡"
        title = "Кӯдаки дарун — захм дорад"
        body  = (
            "Баъзе реаксияҳои имрӯзат аз гузашта меоянд. 🌧\n\n"
            "📌 *Нишонаҳо:*\n"
            "• ҳассосият\n"
            "• тарси рад шудан\n"
            "• душвории ором шудан\n\n"
            "👉 Ба ту кор бо кӯдаки дарун хеле кӯмак мекунад."
        )
    else:
        icon  = "🔴"
        title = "Кӯдаки дарун — баланд фарёд мезанад"
        body  = (
            "Системаи асаб ҳанӯз дар ҳолати муҳофизат аст. 🛡\n\n"
            "📍 *Ин метавонад сабаб бошад:*\n"
            "• хастагии равонӣ\n"
            "• мушкили муносибат\n"
            "• худқадркунии паст\n"
            "• изтироби дохилӣ\n\n"
            "👉 Ба ту шифои амиқ лозим аст."
        )

    text = (
        f"📊 *Натиҷаи тест*\n\n"
        f"{icon} *{title}*\n\n"
        f"🔢 Хол: *{score} аз 20*\n\n"
        f"{body}\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "Такроран тест гузаред ё бо менеҷер тамос гиред 👇"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=kb_result())

    try:
        voice = FSInputFile("AUDOI.oga")
        await message.answer_voice(voice)
    except FileNotFoundError:
        logging.warning("Файл AUDOI.oga не найден, голосовое сообщение не отправлено.")


# ─── Кнопка ЁРДАМ ────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "help")
async def cb_help(call: CallbackQuery):
    await call.answer()
    photo = FSInputFile("photo_help.png")
    text = (
        "🆘 *ЁРДАМ*\n\n"
        "Агар саволе дошта бошед ё кӯмак лозим бошад —\n"
        "администратори мо омода аст! 😊\n\n"
        f"👤 *Администратор:* {MANAGER_PHONE}\n\n"   # ✅ ИСПРАВЛЕНО: было ADMIN_USERNAME
        "Ҳамеша дар хидмати шумо ҳастем! 💙"
    )
    await call.message.answer_photo(photo=photo, caption=text,
                                    parse_mode="Markdown",
                                    reply_markup=kb_menu_only())


# ─── Кнопка МЕНЕДЖЕР ─────────────────────────────────────────────────────────
@dp.callback_query(F.data == "contact_manager")              # ✅ ОДИН обработчик
async def cb_manager(call: CallbackQuery):
    await call.answer()
    # В cb_manager замени текст на:
text = (
    "📞 *Тамос бо менеҷер*\n\n"
    f"👤 [{MANAGER_PHONE}](https://t.me/{MANAGER_PHONE.lstrip('@')})\n\n"
    "Нависед — мо ёрдам мекунем! 💙"
)
    await call.message.answer(text, parse_mode="Markdown", reply_markup=kb_menu_only())


# ─── ЗАПУСК ──────────────────────────────────────────────────────────────────
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
