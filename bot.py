import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, FSInputFile, BufferedInputFile, InputMediaPhoto
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from fpdf import FPDF

# ════════════════════════════════════════════
#  ⚙️  НАСТРОЙКИ — ЗАМЕНИ НА СВОИ
# ════════════════════════════════════════════
BOT_TOKEN     = "8458402183:AAHQ225llgy2LKMMMSGM9lPW8XgfUB1l_Iw"
ADMIN_ID      = 7249758488
MANAGER_PHONE = "@Jannat_Abdullaeva_Admin"
# ════════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher(storage=MemoryStorage())


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


# ─── PDF ОТЧЁТ ───────────────────────────────────────────────────────────────
def generate_pdf(user_name: str, score: int, answers: list) -> bytes:
    if score <= 6:
        level = "Kudaki darun - nisbatan orom"
        color = (0, 180, 0)
    elif score <= 13:
        level = "Kudaki darun - zahm dorad"
        color = (220, 160, 0)
    else:
        level = "Kudaki darun - baland faryed mezanad"
        color = (200, 0, 0)

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 15, "NATIJA / REZULTAT", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 8, datetime.now().strftime("%d.%m.%Y  %H:%M"), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 10, f"Foydalanuvchi: {user_name}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 36)
    pdf.set_text_color(*color)
    pdf.cell(0, 20, f"{score} / 20", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*color)
    pdf.cell(0, 10, level, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    bar_x = 20
    bar_y = pdf.get_y()
    bar_w = 170
    bar_h = 10
    fill_w = int(bar_w * score / 20)
    pdf.set_fill_color(220, 220, 220)
    pdf.rect(bar_x, bar_y, bar_w, bar_h, "F")
    pdf.set_fill_color(*color)
    pdf.rect(bar_x, bar_y, fill_w, bar_h, "F")
    pdf.ln(18)

    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 8, "Javoblar / Otvetlar:", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    answer_labels = {"A": "Bisyor vaqt (A)", "B": "Bazzan (B)", "C": "Qarib ne (C)"}

    for i, (q, a) in enumerate(zip(QUESTIONS, answers), 1):
        if i % 2 == 0:
            pdf.set_fill_color(245, 245, 245)
        else:
            pdf.set_fill_color(255, 255, 255)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(80, 80, 80)
        short_q = f"{i}. " + (q[:55] + "..." if len(q) > 55 else q)
        pdf.cell(130, 8, short_q, fill=True)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*color)
        pdf.cell(50, 8, answer_labels.get(a, a), align="C", fill=True, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 8, f"Menejer: {MANAGER_PHONE}", align="C", new_x="LMARGIN", new_y="NEXT")

    return pdf.output()


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
    b.button(text="🎁 КОНСУЛТАЦИЯИ БЕ ПУЛ — РОЙГОН!", callback_data="contact_manager")
    b.button(text="🏠 Меню",                            callback_data="main_menu")
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
    await state.update_data(q_index=0, answers=[])
    progress = make_progress(1)
    text = f"{progress}\n\n❓ *Савол 1 аз 10*\n\n{QUESTIONS[0]}"
    await call.message.edit_caption(caption=text, parse_mode="Markdown",
                                    reply_markup=kb_answer(0))


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
        progress = make_progress(next_q + 1)
        text = f"{progress}\n\n❓ *Савол {next_q + 1} аз 10*\n\n{QUESTIONS[next_q]}"
        await call.message.edit_caption(caption=text, parse_mode="Markdown",
                                        reply_markup=kb_answer(next_q))
    else:
        total_score = sum(SCORES[a] for a in answers)
        await state.clear()
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
    await call.message.edit_caption(caption=text, parse_mode="Markdown",
                                    reply_markup=kb_answer(prev_index))


# ─── Кнопка МЕНЮ ─────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "main_menu")
async def cb_main_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
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
    await call.message.edit_caption(caption=text, parse_mode="Markdown",
                                    reply_markup=kb_result())

    # Голосовое
    try:
        voice = FSInputFile("AUDOI.oga")
        await call.message.answer_voice(voice)
    except FileNotFoundError:
        logging.warning("AUDOI.oga не найден.")

    # PDF отчёт
    try:
        user = call.from_user
        user_name = user.full_name or user.username or "Foydalanuvchi"
        pdf_bytes = generate_pdf(user_name, score, answers)
        pdf_file = BufferedInputFile(bytes(pdf_bytes), filename="natija.pdf")
        await call.message.answer_document(
            pdf_file,
            caption="📄 *Натиҷаи шумо дар PDF* — нигоҳ доред! 🗂",
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"PDF error: {e}")


# ─── Кнопка ЁРДАМ ────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "help")
async def cb_help(call: CallbackQuery):
    await call.answer()
    await call.message.edit_media(
        media=InputMediaPhoto(
            media=FSInputFile("photo_help.png"),
            caption=(
                "🆘 *ЁРДАМ*\n\n"
                "Агар саволе дошта бошед ё кӯмак лозим бошад —\n"
                "администратори мо омода аст! 😊\n\n"
                f"👤 *Администратор:* [{MANAGER_PHONE}](https://t.me/{MANAGER_PHONE.lstrip('@')})\n\n"
                "Ҳамеша дар хидмати шумо ҳастем! 💙"
            ),
            parse_mode="Markdown"
        ),
        reply_markup=kb_menu_only()
    )


# ─── Кнопка МЕНЕДЖЕР ─────────────────────────────────────────────────────────
@dp.callback_query(F.data == "contact_manager")
async def cb_manager(call: CallbackQuery):
    await call.answer()
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
    await call.message.answer(text, parse_mode="Markdown", reply_markup=kb_menu_only())


# ─── ЗАПУСК ──────────────────────────────────────────────────────────────────
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
