import os
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv
from database import Database
from scheduler import Scheduler

load_dotenv()

class AdventBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN не найден в .env файле!")
        self.db = Database()
        self.scheduler = Scheduler(self)
        self.bot_instance = None
        self.load_events()
        
    def load_events(self):
        """Загружает события из JSON файла"""
        try:
            with open('data/events.json', 'r', encoding='utf-8') as f:
                self.events = json.load(f)
        except FileNotFoundError:
            print("Внимание: файл data/events.json не найден!")
            self.events = {}
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name
        
        # Добавляем пользователя в базу подписчиков
        self.db.add_subscriber(user_id, username)
        
        keyboard = [
            [InlineKeyboardButton("📅 Сегодняшние события", callback_data='today')],
            [InlineKeyboardButton("📋 Открыть все события", callback_data='all')],
            [InlineKeyboardButton("ℹ️ О краеведении", callback_data='info')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"Привет, {username}! 👋\n\n"
            "Я бот-адвент календарь! Каждый день я буду отправлять тебе "
            "новые события и задания.\n\n"
            "Выбери действие:",
            reply_markup=reply_markup
        )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'today':
            await self.send_today_event(query.message.chat_id, context)
        elif query.data == 'all':
            await self.send_all_events(query.message.chat_id, context)
        elif query.data == 'info':
            await query.message.reply_text(
                "ℹ️ О краеведении:\n\n"
                "kraygid.ru/ — готовые планы путешествий по России: интересные места, локальные открытия, кафе, рестораны, актуальные афиши городов, аутдор и трекинг. Маршруты по Петербургу, Кавказу, Дальнему Востоку, Средней полосе и другим регионам. Купить гайд со скидкой 50% по промокоду ADVENT можно на сайте kraygid.ru/"
            )
    
    async def send_today_event(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE = None):
        """Отправляет сегодняшнее событие"""
        message_text = "Привет! Спасибо, что подписался, бот заработает 19-го декабря, мы уже тоже ждем!!"
        
        # Определяем бота для отправки
        if context:
            bot = context.bot
        else:
            bot = Bot(token=self.token)
        
        await bot.send_message(chat_id=chat_id, text=message_text)
    
    async def send_all_events(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        """Отправляет список всех событий"""
        message_text = "Спасибо, что подписался, бот заработает 19-го декабря, мы уже тоже ждем!!"
        await context.bot.send_message(chat_id=chat_id, text=message_text)
    
    async def send_daily_event(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE = None):
        """Отправляет ежедневное событие подписчику"""
        await self.send_today_event(chat_id, context)
    
    def run(self):
        """Запускает бота"""
        application = Application.builder().token(self.token).build()
        
        # Регистрируем обработчики
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Запускаем планировщик
        self.scheduler.start()
        
        # Запускаем бота
        print("Бот запущен!")
        application.run_polling()

if __name__ == '__main__':
    bot = AdventBot()
    bot.run()

