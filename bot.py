import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

DATA_FILE = "users_data.json"

programs = {
    "day_1": ["Отжимания", "Приседания", "Планка"],
    "day_2": ["Бег на месте", "Подтягивания", "Пресс"],
    "day_3": ["Йога", "Растяжка", "Медитация"]
}

def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def init_user_data(data, user_id, user):
    if user_id not in data:
        data[user_id] = {
            "username": user.username or user.full_name,
            "current_day": None,
            "workouts_done": {},
            "stats": {}
        }
    # Обеспечиваем наличие всех ключей
    data[user_id].setdefault("current_day", None)
    data[user_id].setdefault("workouts_done", {})
    data[user_id].setdefault("stats", {})

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = load_data()
    user_id = str(user.id)

    init_user_data(data, user_id, user)
    save_data(data)

    keyboard = [
        [InlineKeyboardButton("День 1", callback_data="day_day_1")],
        [InlineKeyboardButton("День 2", callback_data="day_day_2")],
        [InlineKeyboardButton("День 3", callback_data="day_day_3")]
    ]
    await update.message.reply_text(
        f"Привет, {user.first_name}! Выбери тренировочный день:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = load_data()
    user_id = str(query.from_user.id)
    user = query.from_user
    init_user_data(data, user_id, user)

    # Обработка выбора дня
    if query.data.startswith("day_"):
        day = query.data[4:]
        data[user_id]["current_day"] = day
        save_data(data)

        keyboard = []
        for ex in programs.get(day, []):
            done = data[user_id]["workouts_done"].get(day, {}).get(ex, {}).get("done", False)
            mark = "✅" if done else "❌"
            keyboard.append([InlineKeyboardButton(f"{mark} {ex}", callback_data=f"ex_{ex}")])
        keyboard.append([InlineKeyboardButton("Завершить тренировку", callback_data="finish")])

        await query.edit_message_text(
            f"День: {day}\nВыбери упражнения, которые выполнил:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Отметка упражнения выполненным/не выполненным
    if query.data.startswith("ex_"):
        ex = query.data[3:]
        day = data[user_id].get("current_day")
        if not day:
            await query.answer("Сначала выбери день", show_alert=True)
            return

        if day not in data[user_id]["workouts_done"]:
            data[user_id]["workouts_done"][day] = {}

        done = data[user_id]["workouts_done"][day].get(ex, {}).get("done", False)
        done = not done  # переключаем статус

        data[user_id]["workouts_done"][day][ex] = {
            "done": done,
            "reps": data[user_id]["workouts_done"][day].get(ex, {}).get("reps", 0),
            "weight": data[user_id]["workouts_done"][day].get(ex, {}).get("weight", 0)
        }
        save_data(data)

        keyboard = []
        for exercise in programs[day]:
            done_mark = "✅" if data[user_id]["workouts_done"][day].get(exercise, {}).get("done") else "❌"
            keyboard.append([InlineKeyboardButton(f"{done_mark} {exercise}", callback_data=f"ex_{exercise}")])
        keyboard.append([InlineKeyboardButton("Завершить тренировку", callback_data="finish")])

        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # Завершение тренировки
    if query.data == "finish":
        day = data[user_id].get("current_day")
        if not day:
            await query.answer("Нет выбранной тренировки", show_alert=True)
            return

        done_exercises = [ex for ex, v in data[user_id]["workouts_done"].get(day, {}).items() if v.get("done")]
        text = f"Тренировка за {day} завершена!\nВыполнено упражнений: {len(done_exercises)} из {len(programs.get(day, []))}"

        data[user_id]["current_day"] = None
        save_data(data)

        await query.edit_message_text(text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Используй команду /start чтобы начать тренировку.")

if __name__ == "__main__":
    from telegram.ext import Application

    TOKEN = "7296754209:AAFF4YY0I5aBBqRzlU7goe105ZM8lk4dzvI"

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Бот запущен...")
    app.run_polling()
