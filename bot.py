from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
import os
from dotenv import load_dotenv
import json
import asyncio
import re

# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем токен из переменной окружения. В .env должно быть TOKEN=ваш_токен
TOKEN = os.getenv("TOKEN")
# Получаем путь к файлу JSON из переменной окружения. В .env должно быть BIBLE_JSON_PATH=data/bible.json
BIBLE_JSON_PATH = os.getenv("BIBLE_JSON_PATH")
# Получаем путь к файлу с алиасами книг. В .env должно быть BOOK_ALIASES_PATH=data/book_aliases.json
BOOK_ALIASES_PATH = os.getenv("BOOK_ALIASES_PATH")

# Проверяем, что токен и пути к файлам загружены
if not TOKEN:
    raise ValueError("BOT_TOKEN не найден. Убедитесь, что он установлен в .env файле.")
if not BIBLE_JSON_PATH:
    raise ValueError("BIBLE_JSON_PATH не найден. Убедитесь, что он установлен в .env файле или как переменная окружения.")
if not BOOK_ALIASES_PATH:
    raise ValueError("BOOK_ALIASES_PATH не найден. Убедитесь, что он установлен в .env файле или как переменная окружения.")

# Глобальные переменные для хранения данных Библии и алиасов
bible_data_processed = {}
canonical_book_names_by_id = {} # Ключ: BookId (int), Значение: Каноническое название книги (str)
canonical_book_ids_by_name = {} # Ключ: Каноническое название книги (str, нижний регистр), Значение: BookId (int)
BOOK_MAPPING = {} # Ключ: Пользовательский ввод (str, нижний регистр), Значение: Каноническое название книги (str)

# Для разделения на Ветхий и Новый Завет
OLD_TESTAMENT_IDS = set(range(1, 40)) # Бытие (1) до Малахия (39)
NEW_TESTAMENT_IDS = set(range(40, 67)) # Матфей (40) до Откровение (66)


# --- Функция для загрузки и обработки book_aliases.json ---
async def load_book_aliases():
    global canonical_book_names_by_id, canonical_book_ids_by_name, BOOK_MAPPING
    try:
        file_path = os.path.join(os.path.dirname(__file__), BOOK_ALIASES_PATH)
        with open(file_path, 'r', encoding='utf-8') as f:
            aliases_raw = json.load(f)

        for book_name_canonical, book_id in aliases_raw.items():
            canonical_book_names_by_id[book_id] = book_name_canonical
            canonical_book_ids_by_name[book_name_canonical.lower()] = book_id

            BOOK_MAPPING[book_name_canonical.lower()] = book_name_canonical

        # Вручную добавляем дополнительные распространенные сокращения
        BOOK_MAPPING.update({
            "быт": "Бытие", "книга бытия": "Бытие", "книга быт": "Бытие",
            "исх": "Исход", "книга исход": "Исход", "книга исх": "Исход",
            "лев": "Левит", "книга левит": "Левит", "книга лев": "Левит",
            "чис": "Числа", "книга числа": "Числа", "книга чис": "Числа",
            "вт": "Второзаконие", "второз": "Второзаконие",
            "нав": "Иисус Навин",
            "суд": "Судей",
            "руф": "Руфь",
            "1цар": "1 Царств", "2цар": "2 Царств", "3цар": "3 Царств", "4цар": "4 Царств",
            "1пар": "1 Паралипоменон", "2пар": "2 Паралипоменон",
            "ез": "Ездра",
            "нее": "Неемия",
            "есф": "Есфирь",
            "иов": "Иов",
            "пс": "Псалтирь", "псалом": "Псалтирь",
            "пр": "Притчи",
            "екк": "Екклесиаст",
            "пп": "Песнь Песней",
            "ис": "Исаия",
            "иер": "Иеремия",
            "плач": "Плач Иеремии",
            "иез": "Иезекииль",
            "дан": "Даниил",
            "ос": "Осия",
            "иоил": "Иоиль",
            "ам": "Амос",
            "авд": "Авдий",
            "ион": "Иона",
            "мих": "Михей",
            "наум": "Наум",
            "авв": "Аввакум",
            "соф": "Софония",
            "аг": "Аггей",
            "зах": "Захария",
            "мал": "Малахия",

            "матф": "Матфей", "от матфея": "Матфей", "евангелие от матфея": "Матфей",
            "мк": "Марк", "от марка": "Марк", "евангелие от марка": "Марк",
            "лкс": "Лука", "от луки": "Лука", "евангелие от луки": "Лука",
            "ин": "Иоанн", "от иоанна": "Иоанн", "евангелие от иоанна": "Иоанн",
            "деян": "Деяния", "деяния апостолов": "Деяния",
            "рим": "Римлянам",
            "1 кор": "1 Коринфянам", "2 кор": "2 Коринфянам",
            "гал": "Галатам",
            "еф": "Ефесянам",
            "фил": "Филиппийцам",
            "кол": "Колосянам",
            "1 фес": "1 Фессалоникийцам", "2 фес": "2 Фессалоникийцам",
            "1 тим": "1 Тимофею", "2 тим": "2 Тимофею",
            "тит": "Титу",
            "филим": "Филимону",
            "евр": "Евреям",
            "иак": "Иаков",
            "1 пет": "1 Петра", "2 пет": "2 Петра",
            "1 ин": "1 Иоанна", "2 ин": "2 Иоанна", "3 ин": "3 Иоанна",
            "иуд": "Иуда",
            "откр": "Откровение", "откровение иоанна": "Откровение"
        })

        print(f"Алиасы книг успешно загружены из {file_path}. Найдено канонических названий: {len(aliases_raw)}")
    except FileNotFoundError:
        print(f"Ошибка: Файл алиасов книг не найден по пути: {file_path}")
    except json.JSONDecodeError:
        print(f"Ошибка: Не удалось декодировать JSON из файла алиасов: {file_path}. Проверьте его формат.")
    except Exception as e:
        print(f"Произошла непредвиденная ошибка при загрузке алиасов книг: {e}")


# --- Функция для загрузки и обработки Библии ---
async def load_bible():
    global bible_data_processed
    raw_bible_data = {}
    try:
        file_path = os.path.join(os.path.dirname(__file__), BIBLE_JSON_PATH)
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_bible_data = json.load(f)

        if "Books" in raw_bible_data:
            for book_raw in raw_bible_data["Books"]:
                book_id = book_raw.get("BookId")
                book_name_canonical = canonical_book_names_by_id.get(book_id)

                if book_name_canonical:
                    bible_data_processed[book_name_canonical] = {}
                    for chapter in book_raw.get("Chapters", []):
                        chapter_id = str(chapter.get("ChapterId"))
                        bible_data_processed[book_name_canonical][chapter_id] = {}
                        for verse in chapter.get("Verses", []):
                            verse_id = str(verse.get("VerseId"))
                            verse_text = verse.get("Text")
                            if verse_text:
                                bible_data_processed[book_name_canonical][chapter_id][verse_id] = verse_text
                else:
                    print(f"Предупреждение: Не удалось найти каноническое название для BookId: {book_id} в book_aliases.json. Эта книга будет проигнорирована.")
            print(f"Библия успешно загружена и обработана из {file_path}. Найдено книг: {len(bible_data_processed)}")
        else:
            print(f"Ошибка: Не найдена секция 'Books' в файле Библии: {file_path}. Проверьте его формат.")

    except FileNotFoundError:
        print(f"Ошибка: Файл Библии не найден по пути: {file_path}")
    except json.JSONDecodeError:
        print(f"Ошибка: Не удалось декодировать JSON из файла: {file_path}. Проверьте его формат.")
    except Exception as e:
        print(f"Произошла непредвиденная ошибка при загрузке Библии: {e}")

# --- Функция, которая будет вызвана после инициализации Application ---
async def post_init(application: Application):
    """Вызывается после инициализации Application, чтобы загрузить данные."""
    print("Выполняется post_init: Загрузка алиасов книг...")
    await load_book_aliases()
    print("Выполняется post_init: Загрузка данных Библии...")
    await load_bible()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает команду /start."""
    await update.message.reply_text("Привет! Я бот ✝️.\nИспользуйте команду /bible [Книга] [Глава]:[Стих] для чтения Библии или /bible_menu для интерактивной навигации.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает все текстовые сообщения, которые не являются командами."""
    user_message = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    first_name = update.message.from_user.first_name

    print(f"Получено сообщение от {first_name} (@{username} / ID: {user_id}): {user_message}")

    await update.message.reply_text(f"Я получил ваше сообщение: '{user_message}'. Для чтения Библии используйте /bible [Книга] [Глава]:[Стих] или /bible_menu для интерактивной навигации.")

async def read_bible_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает команду /bible для чтения стихов (как раньше)."""
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите книгу, главу и стих (например, `/bible Иоанн 3:16` или `/bible Бытие 1`).")
        return

    query_str = " ".join(context.args).strip()
    match = re.match(r"(.+?)\s+(\d+)(?::(\d+)(?:-(\d+))?)?$", query_str, re.IGNORECASE)

    if not match:
        await update.message.reply_text("Неверный формат запроса. Используйте: `/bible Книга Глава:Стих` или `/bible Книга Глава` (например, `/bible Иоанн 3:16`).")
        return

    book_raw, chapter_str, verse_start_str, verse_end_str = match.groups()

    book_name_canonical = BOOK_MAPPING.get(book_raw.lower())
    chapter_num_str = chapter_str
    
    verse_start = int(verse_start_str) if verse_start_str else None
    verse_end = int(verse_end_str) if verse_end_str else verse_start

    response_text = ""

    if not book_name_canonical:
        response_text = f"Неизвестная книга '{book_raw}'. Проверьте название или используйте сокращение."
    elif not bible_data_processed:
        response_text = "Данные Библии не загружены или не обработаны. Пожалуйста, сообщите администратору."
    elif book_name_canonical not in bible_data_processed:
        response_text = f"Книга '{book_name_canonical}' найдена в списке алиасов, но не найдена в файле Библии. Проверьте ваш файл bible.json."
    elif chapter_num_str not in bible_data_processed[book_name_canonical]:
        response_text = f"Глава {chapter_num_str} не найдена в книге '{book_name_canonical}'."
    else:
        chapter_data = bible_data_processed[book_name_canonical][chapter_num_str]
        
        if verse_start is None:
            verses = []
            for v_num_str in sorted(chapter_data.keys(), key=int):
                verses.append(f"{v_num_str}. {chapter_data[v_num_str]}")
            
            if verses:
                response_text = f"*{book_name_canonical} {chapter_num_str} глава:*\n" + "\n".join(verses)
            else:
                response_text = f"В главе {chapter_num_str} книги '{book_name_canonical}' не найдено стихов."

        else:
            requested_verses = []
            current_verse = verse_start
            
            while current_verse <= (verse_end or verse_start):
                v_str = str(current_verse)
                if v_str in chapter_data:
                    requested_verses.append(f"{v_str}. {chapter_data[v_str]}")
                else:
                    if verse_start == verse_end:
                        response_text = f"Стих {v_str} не найден в {book_name_canonical} {chapter_num_str} главе."
                        break
                current_verse += 1
            
            if not response_text:
                 if requested_verses:
                    verse_range_str = f":{verse_start}"
                    if verse_end is not None and verse_end != verse_start:
                        verse_range_str += f"-{verse_end}"
                    
                    response_text = f"*{book_name_canonical} {chapter_num_str}{verse_range_str}:*\n" + "\n".join(requested_verses)
                 else:
                    response_text = f"Стихи в диапазоне {verse_start}{'-'+str(verse_end) if verse_end != verse_start else ''} не найдены в {book_name_canonical} {chapter_num_str} главе."

    await update.message.reply_text(response_text, parse_mode='Markdown')

# --- Новая команда для вызова меню Библии ---
async def bible_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Ветхий Завет", callback_data="show_books:old_testament")], # Изменено callback_data
        [InlineKeyboardButton("Новый Завет", callback_data="show_books:new_testament")]  # Изменено callback_data
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await (update.message or update.callback_query.message).reply_text("Выберите раздел Библии:", reply_markup=reply_markup)


# --- Обработчик нажатий на Inline кнопки ---
async def handle_button_press(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # Обязательно ответить на CallbackQuery, чтобы убрать "часики"

    data = query.data
    chat_id = query.message.chat_id
    message_id = query.message.message_id

    # Вспомогательная функция для отображения списка книг
    async def display_books(category_type):
        book_buttons = []
        if category_type == "old_testament":
            title = "Ветхий Завет"
            book_ids_to_show = OLD_TESTAMENT_IDS
        elif category_type == "new_testament":
            title = "Новый Завет"
            book_ids_to_show = NEW_TESTAMENT_IDS
        else:
            await query.edit_message_text("Неизвестная категория.")
            return

        current_row = []
        # Сортируем книги по BookId
        sorted_book_ids = sorted(book_ids_to_show)
        
        for book_id in sorted_book_ids:
            book_name = canonical_book_names_by_id.get(book_id)
            if book_name and book_name in bible_data_processed: # Проверяем, что книга есть в загруженной Библии
                current_row.append(InlineKeyboardButton(book_name, callback_data=f"book:{book_id}"))
                if len(current_row) == 2: # По 2 кнопки в ряд для книг
                    book_buttons.append(current_row)
                    current_row = []
        if current_row: # Добавляем оставшиеся кнопки, если есть
            book_buttons.append(current_row)
        
        # Добавляем кнопку "Назад" к главному меню
        book_buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main_menu")])

        reply_markup = InlineKeyboardMarkup(book_buttons)
        await query.edit_message_text(f"Выберите книгу из {title}:", reply_markup=reply_markup)


    if data.startswith("show_books:"): # Теперь обрабатываем show_books
        category = data.split(":")[1]
        await display_books(category)

    elif data.startswith("book:"):
        book_id = int(data.split(":")[1])
        book_name_canonical = canonical_book_names_by_id.get(book_id)

        if not book_name_canonical or book_name_canonical not in bible_data_processed:
            await query.edit_message_text("Книга не найдена или не загружена.")
            return

        chapter_buttons = []
        chapters = bible_data_processed[book_name_canonical]
        
        current_row = []
        for chapter_id_str in sorted(chapters.keys(), key=int):
            current_row.append(InlineKeyboardButton(chapter_id_str, callback_data=f"chapter:{book_id}:{chapter_id_str}"))
            if len(current_row) == 5: # По 5 кнопок в ряд для глав
                chapter_buttons.append(current_row)
                current_row = []
        if current_row: # Добавляем оставшиеся кнопки
            chapter_buttons.append(current_row)
        
        # Добавляем кнопку "Назад к книгам"
        # Передаем категорию, чтобы display_books знал, какой список книг показывать
        category_for_back = 'old_testament' if book_id in OLD_TESTAMENT_IDS else 'new_testament'
        chapter_buttons.append([InlineKeyboardButton("⬅️ Назад к книгам", callback_data=f"show_books:{category_for_back}")]) # Изменено здесь

        reply_markup = InlineKeyboardMarkup(chapter_buttons)
        await query.edit_message_text(f"Выберите главу для книги *{book_name_canonical}*:", reply_markup=reply_markup, parse_mode='Markdown')

    elif data.startswith("chapter:"):
        _, book_id_str, chapter_id_str = data.split(":")
        book_id = int(book_id_str)
        book_name_canonical = canonical_book_names_by_id.get(book_id)

        if not book_name_canonical or book_name_canonical not in bible_data_processed or chapter_id_str not in bible_data_processed[book_name_canonical]:
            await query.edit_message_text("Глава не найдена или не загружена.")
            return

        chapter_data = bible_data_processed[book_name_canonical][chapter_id_str]
        
        verses = []
        for v_num_str in sorted(chapter_data.keys(), key=int):
            verses.append(f"{v_num_str}. {chapter_data[v_num_str]}")
        
        response_text = ""
        if verses:
            response_text = f"*{book_name_canonical} {chapter_id_str} глава:*\n" + "\n".join(verses)
        else:
            response_text = f"В главе {chapter_id_str} книги '{book_name_canonical}' не найдено стихов."
        
        # Добавляем кнопку "Назад к книгам"
        # Передаем категорию, чтобы display_books знал, какой список книг показывать
        category_for_back = 'old_testament' if book_id in OLD_TESTAMENT_IDS else 'new_testament'
        keyboard = [[InlineKeyboardButton("⬅️ Назад к главам", callback_data=f"book:{book_id}")]] # Возвращаемся к списку глав этой книги
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Telegram имеет ограничение на длину сообщения (4096 символов).
        # Если глава очень длинная, нужно разбить её на несколько сообщений.
        if len(response_text) > 4000:
            await query.edit_message_text(f"Глава *{book_name_canonical} {chapter_id_str}* слишком длинная для одного сообщения. Отправляю только начало.", parse_mode='Markdown')
            await query.message.reply_text(response_text[:4000] + "...", parse_mode='Markdown', reply_markup=reply_markup)
        else:
            await query.edit_message_text(response_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif data == "back_to_main_menu":
        # Если нажали "Назад" из меню книг, возвращаемся к выбору Завета
        keyboard = [
            [InlineKeyboardButton("Ветхий Завет", callback_data="show_books:old_testament")],
            [InlineKeyboardButton("Новый Завет", callback_data="show_books:new_testament")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выберите раздел Библии:", reply_markup=reply_markup)
    
    # OLD: elif data.startswith("back_to_category:"):
    #    category = data.split(":")[1]
    #    await handle_button_press(update.callback_query, context) # Повторно вызываем обработчик для категории

    # OLD: elif data.startswith("back_to_books:"):
    #    category = data.split(":")[1]
    #    await handle_button_press(update.callback_query, context)


if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()

    app.post_init = post_init

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("bible", read_bible_command))
    app.add_handler(CommandHandler("bible_menu", bible_menu))

    app.add_handler(CallbackQueryHandler(handle_button_press))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot Started...")
    app.run_polling()
