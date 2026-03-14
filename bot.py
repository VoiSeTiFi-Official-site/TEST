import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto, WebAppInfo
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ════════════════════════════════════════════
#  ⚙️  НАСТРОЙКИ
# ════════════════════════════════════════════
BOT_TOKEN     = "8458402183:AAHQ225llgy2LKMMMSGM9lPW8XgfUB1l_Iw"
ADMIN_ID      = 7249758488
MANAGER_PHONE = "@Jannat_Abdullaeva_Admin"
DEV_USERNAME  = "@Mustafo_IT"

# 🔗 Ссылка на Mini App — вставь свою после деплоя на Vercel!
MINI_APP_URL  = "https://ravoni-platformm.vercel.app/?v=8"
# ════════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher(storage=MemoryStorage())

# ─── СЧЁТЧИК ПОЛЬЗОВАТЕЛЕЙ ───────────────────────────────────────────────────
user_counter: int = 0


# ─── FSM СОСТОЯНИЯ ───────────────────────────────────────────────────────────
class Quiz(StatesGroup):
    question = State()


# ─── ВОПРОСЫ ТЕСТА ───────────────────────────────────────────────────────────
QUESTIONS = [
    "Вақте касе туро танқид мекунад, ту зуд ранҷида мешавӣ?",
    "Баъзан бе сабаби равшан худро танҳо ҳис мекунӣ?",
    "Оё ту аз партофта шудан ё рад шудан метарсӣ?",
    "Вақте асабонӣ мешавӣ, ором шудан бароят душвор аст?",
    "Оё ту зуд худро гунаҳкор ҳис мекунӣ, ҳатто вақте айбдор нестӣ?",
    "Ба ту гуфтани «не» ба дигарон мушкил аст?",
    "Баъзан ҳис мекунӣ, ки муҳаббатро бояд «сазовор» шавӣ?",
    "Дар муносибатҳо аз ҳад вобаста ё баръакс сард мешавӣ?",
    "Оё дар дарунат ҳисси ғам ё холигии кӯҳна ҳаст?",
    "Вақте касе баланд гап мезанад, баданат танг мешавад?",
]

SCORES = {"A": 2, "B": 1, "C": 0}


# ─── ПРОГРЕСС БАР ────────────────────────────────────────────────────────────
def make_progress(current: int, total: int = 10) -> str:
    filled = "▰" * current
    empty  = "▱" * (total - current)
    return f"📊 Савол {current}/{total}  {filled}{empty}"


# ─── АВТО-НАПОМИНАНИЯ ─────────────────────────────────────────────────────────
async def remind_unfinished(user_id: int, state: FSMContext):
    await asyncio.sleep(300)
    data = await state.get_data()
    if data.get("in_quiz") and not data.get("reminded_unfinished"):
        await state.update_data(reminded_unfinished=True)
        kb = InlineKeyboardBuilder()
        kb.button(text="▶️ Тестро идома деҳ", callback_data="begin_quiz")
        kb.button(text="🏠 Меню",              callback_data="main_menu")
        kb.adjust(1)
        try:
            await bot.send_message(
                user_id,
                "⏰ *Эй, дӯст!*\n\n"
                "Ту тестро нимакора гузоштӣ... 🤔\n\n"
                "Шояд ҳамин натиҷа муҳимтарин чизест\n"
                "ки имрӯз барои худат кашф мекунӣ! 💡\n\n"
                "👇 Идома деҳ — танҳо чанд савол монда:",
                parse_mode="Markdown",
                reply_markup=kb.as_markup()
            )
        except Exception as e:
            logging.warning(f"Remind unfinished error: {e}")


async def remind_no_manager(user_id: int, state: FSMContext):
    await asyncio.sleep(300)
    data = await state.get_data()
    if data.get("test_done") and not data.get("went_to_manager") and not data.get("reminded_manager"):
        await state.update_data(reminded_manager=True)
        kb = InlineKeyboardBuilder()
        kb.button(text="🎁 КОНСУЛТАЦИЯИ РОЙГОН", callback_data="contact_manager")
        kb.button(text="🏠 Меню",                 callback_data="main_menu")
        kb.adjust(1)
        try:
            await bot.send_message(
                user_id,
                "💙 *Ёдат ҳаст?*\n\n"
                "Ту тестро гузаштӣ, аммо\n"
                "консултатсияи *РОЙГОН* ҳанӯз интизори туст! 🎁\n\n"
                "Менеҷер метавонад роҳи шифоро нишонат диҳад —\n"
                "ин фурсат *танҳо имрӯз* аст! ⏳\n\n"
                "👇 Як клик — ва тағйирот оғоз мешавад:",
                parse_mode="Markdown",
                reply_markup=kb.as_markup()
            )
        except Exception as e:
            logging.warning(f"Remind manager error: {e}")


# ─── КЛАВИАТУРЫ ──────────────────────────────────────────────────────────────
def kb_start():
    b = InlineKeyboardBuilder()
    # 🌐 Кнопка открытия Mini App (WebApp)
    b.button(
        text="🌐 Ворид шудан дар Барнома",
        web_app=WebAppInfo(url=MINI_APP_URL)
    )
    b.button(text="🧪 ТЕСТ",  callback_data="start_test")
    b.button(text="🆘 ЁРДАМ", callback_data="help")
    b.adjust(1, 2)   # Mini App — отдельная строка, Тест+Ёрдам — рядом
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
    # После результата — тоже можно открыть Mini App
    b.button(
        text="🌐 Барномаро кушоед",
        web_app=WebAppInfo(url=MINI_APP_URL)
    )
    b.button(text="🎁 КОНСУЛТАЦИЯИ БЕ ПУЛ — РОЙГОН!", callback_data="contact_manager")
    b.button(text="🏠 Меню",                            callback_data="main_menu")
    b.adjust(1)
    return b.as_markup()

def kb_menu_only():
    b = InlineKeyboardBuilder()
    b.button(text="🏠 Меню", callback_data="main_menu")
    return b.as_markup()

def kb_help():
    b = InlineKeyboardBuilder()
    b.button(text="🛠 Техподдержка",  url=f"https://t.me/{DEV_USERNAME.lstrip('@')}")
    b.button(text="💬 Менеҷер",       url=f"https://t.me/{MANAGER_PHONE.lstrip('@')}")
    b.button(text="🏠 Меню",           callback_data="main_menu")
    b.adjust(2, 1)
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
        f"👥 *Аллакай {user_counter:,} нафар тестро гузаштанд!*\n\n"
        "👇 Яке аз тугмаҳоро пахш кунед:"
    )
    await message.answer_photo(
        photo=photo,
        caption=text,
        parse_mode="Markdown",
        reply_markup=kb_start()
    )


# ─── Кнопка ТЕСТ ─────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "start_test")
async def cb_test(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    await call.message.edit_media(
        media=InputMediaPhoto(
            media=FSInputFile("photo_test.png"),
            caption=(
                "🧪 *ТЕСТ: «Оё кӯдаки даруни ту ҳанӯз захм дорад?»*\n\n"
                "📌 *Дастур:*\n"
                "Ба ҳар савол ростқавлона ҷавоб деҳ:\n\n"
                "• А — бисёр вақт\n"
                "• Б — баъзан\n"
                "• В — қариб не\n\n"
                "💡 Тест 10 савол дорад. Ҳозир тайёр?"
            ),
            parse_mode="Markdown"
        ),
        reply_markup=kb_begin_test()
    )


# ─── Начало теста ─────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "begin_quiz")
async def cb_begin(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.set_state(Quiz.question)
    await state.update_data(
        q_index=0, answers=[], in_quiz=True, test_done=False,
        went_to_manager=False, reminded_unfinished=False, reminded_manager=False
    )
    asyncio.create_task(remind_unfinished(call.from_user.id, state))
    progress = make_progress(1)
    text = f"{progress}\n\n❓ *Савол 1 аз 10*\n\n{QUESTIONS[0]}"
    await call.message.edit_caption(
        caption=text, parse_mode="Markdown", reply_markup=kb_answer(0)
    )


# ─── Ответы на вопросы ────────────────────────────────────────────────────────
@dp.callback_query(Quiz.question, F.data.startswith("ans_"))
async def cb_answer(call: CallbackQuery, state: FSMContext):
    global user_counter
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
        progress = make_progress(next_q + 1)
        text = f"{progress}\n\n❓ *Савол {next_q + 1} аз 10*\n\n{QUESTIONS[next_q]}"
        await call.message.edit_caption(
            caption=text, parse_mode="Markdown", reply_markup=kb_answer(next_q)
        )
    else:
        total_score = sum(SCORES[a] for a in answers)
        user_counter += 1
        await state.update_data(in_quiz=False, test_done=True, answers=answers)
        await state.set_state(None)
        asyncio.create_task(remind_no_manager(call.from_user.id, state))
        await send_result(call, total_score, answers)


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
    progress = make_progress(prev_index + 1)
    text = f"{progress}\n\n❓ *Савол {prev_index + 1} аз 10*\n\n{QUESTIONS[prev_index]}"
    await call.message.edit_caption(
        caption=text, parse_mode="Markdown", reply_markup=kb_answer(prev_index)
    )


# ─── Кнопка МЕНЮ ─────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "main_menu")
async def cb_main_menu(call: CallbackQuery, state: FSMContext):
    await state.update_data(in_quiz=False)
    await call.answer()
    await call.message.edit_media(
        media=InputMediaPhoto(
            media=FSInputFile("photo_start.png"),
            caption=(
                "✨ *Хуш омадед!*\n\n"
                "Салом, дӯсти азиз! 👋\n\n"
                "Ин бот ба шумо кӯмак мекунад, ки ҳолати *кӯдаки дарунатонро* бифаҳмед.\n\n"
                "🌱 Тест хеле содда аст — танҳо 10 савол.\n"
                "Ҷавоб деҳ ва натиҷаро бубинед!\n\n"
                f"👥 *Аллакай {user_counter:,} нафар тестро гузаштанд!*\n\n"
                "👇 Яке аз тугмаҳоро пахш кунед:"
            ),
            parse_mode="Markdown"
        ),
        reply_markup=kb_start()
    )


# ─── Результат ────────────────────────────────────────────────────────────────
async def send_result(call: CallbackQuery, score: int, answers: list):
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
        "━━━━━━━━━━━━━━━━\n\n"
        "🎁 *КОНСУЛТАЦИЯИ БЕ ПУЛ — РОЙГОН!*\n\n"
        "Мехоҳӣ бидонӣ, ки чӣ тавр метавонӣ\n"
        "кӯдаки дарунатро шифо диҳӣ?\n\n"
        "👇 Менеҷери мо омода аст, ки *РОЙГОН* ба ту кӯмак кунад!\n"
        "Ин танҳо барои имрӯз аст — фурсатро аз даст надеҳ! ⏳"
    )
    await call.message.edit_caption(
        caption=text, parse_mode="Markdown", reply_markup=kb_result()
    )

    # Голосовое
    try:
        voice = FSInputFile("AUDOI.oga")
        await call.message.answer_voice(voice)
    except FileNotFoundError:
        logging.warning("AUDOI.oga не найден.")


# ─── Кнопка ЁРДАМ ────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "help")
async def cb_help(call: CallbackQuery):
    await call.answer()
    await call.message.edit_media(
        media=InputMediaPhoto(
            media=FSInputFile("photo_help.png"),
            caption=(
                "🆘 *ЁРДАМ*\n\n"
                "━━━━━━━━━━━━━━━━\n"
                "🛠 *Техподдержка:*\n"
                "Агар бот кор намекунад, тугма фишор намешавад\n"
                "ё хатогие дидед — нависед:\n"
                f"👤 [{DEV_USERNAME}](https://t.me/{DEV_USERNAME.lstrip('@')})\n\n"
                "━━━━━━━━━━━━━━━━\n"
                "💬 *Саволҳо оид ба курс:*\n"
                "Консултатсия, нарх, пардохт ва дигар саволҳо —\n"
                "менеҷери мо омода аст:\n"
                f"👤 [{MANAGER_PHONE}](https://t.me/{MANAGER_PHONE.lstrip('@')})\n\n"
                "Ҳамеша дар хидмати шумо ҳастем! 💙"
            ),
            parse_mode="Markdown"
        ),
        reply_markup=kb_help()
    )


# ─── Кнопка МЕНЕДЖЕР ─────────────────────────────────────────────────────────
@dp.callback_query(F.data == "contact_manager")
async def cb_manager(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.update_data(went_to_manager=True)
    text = (
        "🎁 *КОНСУЛТАЦИЯИ БЕ ПУЛ — РОЙГОН!*\n\n"
        "Шумо қадами дурусте гузоштед! 🌟\n\n"
        "Менеҷери мо бо шумо шахсан сӯҳбат мекунад ва\n"
        "роҳи шифои кӯдаки дарунатонро нишон медиҳад.\n\n"
        "💬 Ба менеҷер нависед — вай ҳозир онлайн аст:\n\n"
        f"👤 [{MANAGER_PHONE}](https://t.me/{MANAGER_PHONE.lstrip('@')})\n\n"
        "⏳ *Ин консултатсия комилан РОЙГОН аст!*\n"
        "Нависед ва тағйирот оғоз мешавад! 💙"
    )
    await call.message.answer(
        text, parse_mode="Markdown", reply_markup=kb_menu_only()
    )


# ─── ЗАПУСК ──────────────────────────────────────────────────────────────────
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
