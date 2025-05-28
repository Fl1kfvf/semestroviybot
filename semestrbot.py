import json
from pathlib import Path
import logging
import random
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка конфигурации
CONFIG_FILE = Path('config.json')

def load_config():
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки конфига: {e}")
        return {}

config = load_config()
TMDB_API = config.get('TMDB_API')
BOT_TOKEN = config.get('BOT_TOKEN')

if not TMDB_API or not BOT_TOKEN:
    logger.error("Не найдены необходимые ключи в config.json")
    print("Пример содержимого config.json:")
    print('''{
    "TMDB_API": "ваш_ключ_tmdb",
    "BOT_TOKEN": "ваш_токен_бота"}''')
    exit(1)

# Логгирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    "Первое сообщение"
    await update.message.reply_text(
        "Кино-бот\n\n"
        "Доступные команды:\n"
        "/search <название> - Поиск фильма\n"
        "/top - Топ-10 TMDB\n"
        "/random - Случайный фильм\n"
        "/help - Помощь"
    )

async def search_movie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    "Поиск фильма на TMDB"
    if not context.args:
        await update.message.reply_text("Укажите название фильма после команды /search")
        return

    query = ' '.join(context.args)
    try:
        response = requests.get(
            f'https://api.themoviedb.org/3/search/movie?api_key={TMDB_API}&query={query}&language=ru-RU'
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['results']:
                film = data['results'][0]
                msg = (
                    f"{film.get('title', 'Без названия')}\n"
                    f"Год: {film.get('release_date', 'неизвестен')[:4] if film.get('release_date') else 'неизвестен'}\n"
                    f"Рейтинг: {film.get('vote_average', 'нет данных')}"
                )
            else:
                msg = "Фильм не найден на TMDB"
        else:
            msg = f"Ошибка API: {response.status_code}"
            
        await update.message.reply_text(msg)
    except Exception as e:
        logger.error(f"Ошибка поиска: {e}")
        await update.message.reply_text("Ошибка при поиске фильма")

async def get_tmdb_top(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    "Топ-10 фильмов по версии TMDB"
    try:
        response = requests.get(
            f'https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API}&language=ru-RU&page=1'
        )
        
        if response.status_code == 200:
            data = response.json()
            movies = []
            for i, film in enumerate(data['results'][:10], 1):
                title = film.get('title', 'Без названия')
                year = film.get('release_date', '')[:4] if film.get('release_date') else 'N/A'
                rating = film.get('vote_average', 'N/A')
                movies.append(f"{i}. {title} ({year}) ★ {rating}")
            
            if movies:
                await update.message.reply_text("Топ-10 популярных фильмов (TMDB):\n\n" + "\n".join(movies))
            else:
                await update.message.reply_text("Не удалось получить топ фильмов")
        else:
            await update.message.reply_text(f"Ошибка API: {response.status_code}")
    except Exception as e:
        logger.error(f"Ошибка TMDB: {e}")
        await update.message.reply_text("Ошибка при получении топ-10")

async def get_random_movie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    "Случайный фильм из популярных на TMDB"
    try:
        page = random.randint(1, 5)  # Случайная страница 1-5
        response = requests.get(
            f'https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API}&language=ru-RU&page={page}'
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['results']:
                film = random.choice(data['results'])
                msg = (
                    f"Случайный фильм:\n\n"
                    f"{film.get('title', 'Без названия')}\n"
                    f"Год: {film.get('release_date', '')[:4] if film.get('release_date') else 'неизвестен'}\n"
                    f"Рейтинг: {film.get('vote_average', 'нет данных')}"
                )
            else:
                msg = "Не найдены фильмы"
        else:
            msg = f"Ошибка API: {response.status_code}"
            
        await update.message.reply_text(msg)
    except Exception as e:
        logger.error(f"Ошибка случайного фильма: {e}")
        await update.message.reply_text("Ошибка при выборе фильма")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    "Команды"
    await update.message.reply_text(
        "Доступные команды:\n\n"
        "/search <название> - Поиск фильма\n"
        "/top - Топ-10 TMDB\n"
        "/random - Случайный фильм из популярных\n"
        "/help - Эта справка"
    )

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("search", search_movie))
    application.add_handler(CommandHandler("top", get_tmdb_top))
    application.add_handler(CommandHandler("random", get_random_movie))
    
    logger.info("Бот запущен")
    application.run_polling()

if __name__ == '__main__':
    main()