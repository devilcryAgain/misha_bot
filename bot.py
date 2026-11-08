import logging
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, BotCommand, MenuButtonCommands,
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "9284766898:AAHydkJ4Fu74CBavAV7Qv1OLMtcKYjiy11M"

SUBJECTS = {
    "russian": "Русский язык",
    "math": "Математика",
    "geometry": "Геометрия",
    "physics": "Физика",
    "algebra": "Алгебра",
}

SUBJECT_BUTTONS = {
    "📚 Русский язык": "russian",
    "➗ Математика": "math",
    "📐 Геометрия": "geometry",
    "⚛ Физика": "physics",
    "🔢 Алгебра": "algebra",
}

GRADES = ["6", "7", "8", "9"]


# ---------- Клавиатуры ----------

def subjects_reply_keyboard() -> ReplyKeyboardMarkup:
    items = list(SUBJECT_BUTTONS)
    rows = [items[i:i + 2] for i in range(0, len(items), 2)]
    return ReplyKeyboardMarkup(
        [[KeyboardButton(t) for t in row] for row in rows],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Выбери предмет..."
    )


def grades_inline_keyboard(subject_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{g} класс", callback_data=f"grade:{subject_key}:{g}")
         for g in GRADES],
        [InlineKeyboardButton("⬅ Назад", callback_data="back:subjects")],
    ])


def actions_inline_keyboard(subject_key: str, grade: str) -> InlineKeyboardMarkup:
    """Кнопки после выбора класса: что делать дальше."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Решить задачу", callback_data=f"solve:{subject_key}:{grade}")],
        [InlineKeyboardButton("📖 Узнать теорию", callback_data=f"learn:{subject_key}:{grade}")],
        [InlineKeyboardButton("📝 Примеры заданий", callback_data=f"examples:{subject_key}:{grade}")],
        [InlineKeyboardButton("🔄 Сменить предмет/класс", callback_data="back:subjects")],
    ])


# ---------- Хэндлеры ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет! Выбери предмет:",
        reply_markup=subjects_reply_keyboard()
    )


async def handle_subject_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    key = SUBJECT_BUTTONS.get(text)
    if not key:
        return
    await update.message.reply_text(
        f"Предмет: *{SUBJECTS[key]}*\nВыбери класс:",
        parse_mode="Markdown",
        reply_markup=grades_inline_keyboard(key)
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    data = q.data

    # Возврат к предметам
    if data == "back:subjects":
        await q.edit_message_text("Выбери предмет заново (кнопки внизу).")
        return

    # Выбор класса -> приветствие Reshatel
    if data.startswith("grade:"):
        _, subject_key, grade = data.split(":", 2)
        subject_name = SUBJECTS[subject_key]

        # сохраняем выбор пользователя
        context.user_data["subject"] = subject_key
        context.user_data["grade"] = grade

        await q.edit_message_text(
            f"✅ *{subject_name}*, *{grade} класс*\n\n"
            f"Здравствуйте! Я чат-бот *Reshatel*.\n"
            f"Что нужно решить или узнать?",
            parse_mode="Markdown",
            reply_markup=actions_inline_keyboard(subject_key, grade)
        )
        return

    # Пользователь нажал "Решить задачу"
    if data.startswith("solve:"):
        _, subject_key, grade = data.split(":", 2)
        await q.edit_message_text(
            f"✏️ *{SUBJECTS[subject_key]}, {grade} класс*\n\n"
            f"Напишите условие задачи — я помогу с решением.\n"
            f"(Здесь подключите вашу логику / ИИ / базу задач.)",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅ Назад", callback_data=f"grade:{subject_key}:{grade}")]
            ])
        )
        # Включаем режим ожидания задачи
        context.user_data["awaiting_task"] = True
        return

    # "Узнать теорию"
    if data.startswith("learn:"):
        _, subject_key, grade = data.split(":", 2)
        await q.edit_message_text(
            f"📖 *{SUBJECTS[subject_key]}, {grade} класс — теория*\n\n"
            f"Здесь будет список тем и материалы.\n"
            f"(Подставьте свои темы.)",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅ Назад", callback_data=f"grade:{subject_key}:{grade}")]
            ])
        )
        return

    # "Примеры заданий"
    if data.startswith("examples:"):
        _, subject_key, grade = data.split(":", 2)
        await q.edit_message_text(
            f"📝 *{SUBJECTS[subject_key]}, {grade} класс — примеры*\n\n"
            f"Здесь будут примеры заданий.\n"
            f"(Подставьте свои примеры.)",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅ Назад", callback_data=f"grade:{subject_key}:{grade}")]
            ])
        )
        return


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "/start — открыть меню предметов\n"
        "/help — эта справка"
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Если пользователь нажал "Решить задачу" и теперь пишет условие
    if context.user_data.get("awaiting_task"):
        context.user_data["awaiting_task"] = False
        subject = SUBJECTS.get(context.user_data.get("subject", ""), "—")
        grade = context.user_data.get("grade", "—")
        await update.message.reply_text(
            f"📥 Принял задачу по предмету *{subject}*, *{grade} класс*.\n"
            f"Скоро здесь появится решение (подключите свою логику).",
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text(
        f"Вы написали: {update.message.text}\n"
        f"Чтобы открыть меню, введите /start"
    )


async def post_init(app: Application) -> None:
    await app.bot.set_my_commands([
        BotCommand("start", "📚 Открыть меню предметов"),
        BotCommand("help", "❓ Помощь"),
    ])
    await app.bot.set_chat_menu_button(menu_button=MenuButtonCommands())


def main() -> None:
    app = Application.builder().token(TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    # Нажатия на кнопки-предметы (ReplyKeyboard)
    pattern = "^(" + "|".join(s.replace("|", r"\|") for s in SUBJECT_BUTTONS) + ")$"
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex(pattern),
        handle_subject_text
    ))

    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    app.run_polling()


if __name__ == "__main__":
    main()