import os
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from dotenv import load_dotenv
from database import Database

load_dotenv()

class AdminBot:
    def __init__(self):
        self.token = os.getenv('ADMIN_BOT_TOKEN')
        if not self.token:
            raise ValueError("ADMIN_BOT_TOKEN не найден в .env файле!")
        
        # Список ID администраторов (добавьте свой Telegram ID)
        self.admin_ids = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
        
        self.db = Database()
        self.load_events()
        self.pending_data = {}  # Для хранения данных в процессе добавления события
    
    def load_events(self):
        """Загружает события из JSON файла"""
        try:
            with open('data/events.json', 'r', encoding='utf-8') as f:
                self.events = json.load(f)
        except FileNotFoundError:
            self.events = {}
    
    def save_events(self):
        """Сохраняет события в JSON файл"""
        with open('data/events.json', 'w', encoding='utf-8') as f:
            json.dump(self.events, f, ensure_ascii=False, indent=2)
    
    def is_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь администратором"""
        return user_id in self.admin_ids
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ У вас нет доступа к админ-панели.")
            return
        
        keyboard = [
            [InlineKeyboardButton("👥 Подписчики", callback_data='subscribers')],
            [InlineKeyboardButton("📅 Все события", callback_data='events_list')],
            [InlineKeyboardButton("➕ Добавить событие", callback_data='add_event')],
            [InlineKeyboardButton("🗑️ Удалить событие", callback_data='delete_event')],
            [InlineKeyboardButton("📤 Тестовая рассылка", callback_data='test_send')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔐 Админ-панель\n\n"
            "Выберите действие:",
            reply_markup=reply_markup
        )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if not self.is_admin(user_id):
            await query.answer("❌ У вас нет доступа.", show_alert=True)
            return
        
        await query.answer()
        
        if query.data == 'subscribers':
            await self.show_subscribers(query)
        elif query.data == 'events_list':
            await self.show_events_list(query)
        elif query.data == 'add_event':
            await self.start_add_event(query)
        elif query.data == 'delete_event':
            await self.start_delete_event(query)
        elif query.data == 'test_send':
            await self.test_send(query)
        elif query.data.startswith('delete_'):
            date = query.data.replace('delete_', '')
            await self.confirm_delete(query, date)
        elif query.data.startswith('confirm_delete_'):
            date = query.data.replace('confirm_delete_', '')
            await self.delete_event(query, date)
        elif query.data == 'back':
            keyboard = [
                [InlineKeyboardButton("👥 Подписчики", callback_data='subscribers')],
                [InlineKeyboardButton("📅 Все события", callback_data='events_list')],
                [InlineKeyboardButton("➕ Добавить событие", callback_data='add_event')],
                [InlineKeyboardButton("🗑️ Удалить событие", callback_data='delete_event')],
                [InlineKeyboardButton("📤 Тестовая рассылка", callback_data='test_send')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                "🔐 Админ-панель\n\n"
                "Выберите действие:",
                reply_markup=reply_markup
            )
    
    async def show_subscribers(self, query):
        """Показывает список подписчиков"""
        subscribers = self.db.get_all_subscribers_info()
        
        if not subscribers:
            await query.message.reply_text("📭 Пока нет подписчиков.")
            return
        
        text = f"👥 Подписчики: {len(subscribers)}\n\n"
        for user_id, username, subscribed_at in subscribers[:50]:  # Показываем первых 50
            username_display = f"@{username}" if username else "Без username"
            text += f"• {username_display} (ID: {user_id})\n"
            text += f"  Подписался: {subscribed_at}\n\n"
        
        if len(subscribers) > 50:
            text += f"\n... и еще {len(subscribers) - 50} подписчиков"
        
        await query.message.reply_text(text)
    
    async def show_events_list(self, query):
        """Показывает список всех событий"""
        if not self.events:
            await query.message.reply_text("📅 Событий пока нет.")
            return
        
        text = "📅 Все события:\n\n"
        for date, event in sorted(self.events.items()):
            text += f"📆 {date}\n"
            text += f"   {event['title']}\n"
            if event.get('image'):
                text += f"   🖼️ Есть картинка\n"
            if event.get('map_url'):
                text += f"   🗺️ Есть карта\n"
            text += "\n"
        
        await query.message.reply_text(text)
    
    async def start_add_event(self, query):
        """Начинает процесс добавления события"""
        await query.message.reply_text(
            "➕ Добавление события\n\n"
            "Отправьте дату в формате: YYYY-MM-DD\n"
            "Например: 2024-12-19"
        )
        self.pending_data[query.from_user.id] = {'step': 'date'}
    
    async def start_delete_event(self, query):
        """Начинает процесс удаления события"""
        if not self.events:
            await query.message.reply_text("📅 Событий для удаления нет.")
            return
        
        keyboard = []
        for date in sorted(self.events.keys()):
            event = self.events[date]
            keyboard.append([InlineKeyboardButton(
                f"{date}: {event['title'][:30]}",
                callback_data=f"delete_{date}"
            )])
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='back')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            "🗑️ Выберите событие для удаления:",
            reply_markup=reply_markup
        )
    
    async def confirm_delete(self, query, date):
        """Подтверждение удаления события"""
        event = self.events.get(date)
        if not event:
            await query.answer("Событие не найдено", show_alert=True)
            return
        
        keyboard = [
            [InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_{date}")],
            [InlineKeyboardButton("❌ Отмена", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            f"🗑️ Удалить событие?\n\n"
            f"📆 {date}\n"
            f"📝 {event['title']}\n\n"
            f"Это действие нельзя отменить!",
            reply_markup=reply_markup
        )
    
    async def delete_event(self, query, date):
        """Удаляет событие"""
        if date in self.events:
            del self.events[date]
            self.save_events()
            await query.message.reply_text(f"✅ Событие {date} удалено.")
        else:
            await query.message.reply_text("❌ Событие не найдено.")
    
    async def test_send(self, query):
        """Отправляет тестовое сообщение"""
        await query.message.reply_text(
            "📤 Тестовая рассылка\n\n"
            "Эта функция отправит сообщение всем подписчикам.\n"
            "Введите текст сообщения:"
        )
        self.pending_data[query.from_user.id] = {'step': 'test_message'}
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            return
        
        if user_id not in self.pending_data:
            return
        
        step = self.pending_data[user_id]['step']
        text = update.message.text
        
        if step == 'date':
            # Проверяем формат даты
            try:
                datetime.strptime(text, '%Y-%m-%d')
                self.pending_data[user_id]['date'] = text
                self.pending_data[user_id]['step'] = 'title'
                await update.message.reply_text(
                    f"✅ Дата: {text}\n\n"
                    "Отправьте заголовок события:"
                )
            except ValueError:
                await update.message.reply_text(
                    "❌ Неверный формат даты!\n"
                    "Используйте формат: YYYY-MM-DD\n"
                    "Например: 2024-12-19"
                )
        
        elif step == 'title':
            self.pending_data[user_id]['title'] = text
            self.pending_data[user_id]['step'] = 'description'
            await update.message.reply_text(
                f"✅ Заголовок: {text}\n\n"
                "Отправьте описание события:"
            )
        
        elif step == 'description':
            self.pending_data[user_id]['description'] = text
            self.pending_data[user_id]['step'] = 'image'
            await update.message.reply_text(
                f"✅ Описание: {text}\n\n"
                "Отправьте ссылку на картинку (или отправьте /skip чтобы пропустить):"
            )
        
        elif step == 'image':
            if text.lower() == '/skip':
                self.pending_data[user_id]['image'] = None
            else:
                self.pending_data[user_id]['image'] = text
            self.pending_data[user_id]['step'] = 'map'
            await update.message.reply_text(
                "Отправьте ссылку на карту (или отправьте /skip чтобы пропустить):"
            )
        
        elif step == 'map':
            if text.lower() == '/skip':
                self.pending_data[user_id]['map_url'] = None
            else:
                self.pending_data[user_id]['map_url'] = text
            
            # Сохраняем событие
            data = self.pending_data[user_id]
            date = data['date']
            
            self.events[date] = {
                'title': data['title'],
                'description': data['description'],
                'image': data.get('image'),
                'map_url': data.get('map_url')
            }
            self.save_events()
            self.load_events()
            
            del self.pending_data[user_id]
            
            await update.message.reply_text(
                f"✅ Событие добавлено!\n\n"
                f"📆 Дата: {date}\n"
                f"📝 Заголовок: {data['title']}\n"
                f"📄 Описание: {data['description']}\n"
                f"🖼️ Картинка: {'Да' if data.get('image') else 'Нет'}\n"
                f"🗺️ Карта: {'Да' if data.get('map_url') else 'Нет'}"
            )
        
        elif step == 'test_message':
            # Отправляем тестовое сообщение всем подписчикам
            subscribers = self.db.get_all_subscribers()
            sent = 0
            failed = 0
            
            # Создаем бота один раз
            main_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            if not main_bot_token:
                await update.message.reply_text("❌ TELEGRAM_BOT_TOKEN не найден в .env")
                del self.pending_data[user_id]
                return
            
            bot = Bot(token=main_bot_token)
            
            await update.message.reply_text(f"📤 Начинаю рассылку {len(subscribers)} подписчикам...")
            
            for sub_id in subscribers:
                try:
                    await bot.send_message(chat_id=sub_id, text=text)
                    sent += 1
                except Exception as e:
                    failed += 1
                    print(f"Ошибка отправки {sub_id}: {e}")
            
            del self.pending_data[user_id]
            await update.message.reply_text(
                f"✅ Рассылка завершена!\n\n"
                f"📤 Отправлено: {sent}\n"
                f"❌ Ошибок: {failed}"
            )
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик фотографий"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            return
        
        if user_id in self.pending_data and self.pending_data[user_id]['step'] == 'image':
            # Получаем file_id фотографии
            photo = update.message.photo[-1]  # Берем фото наибольшего размера
            file_id = photo.file_id
            
            # Получаем прямую ссылку на файл
            bot = Bot(token=self.token)
            file = await bot.get_file(file_id)
            file_url = file.file_path
            
            self.pending_data[user_id]['image'] = f"https://api.telegram.org/file/bot{self.token}/{file_url}"
            self.pending_data[user_id]['step'] = 'map'
            
            await update.message.reply_text(
                "✅ Картинка сохранена!\n\n"
                "Отправьте ссылку на карту (или отправьте /skip чтобы пропустить):"
            )
    
    def run(self):
        """Запускает админ-бота"""
        application = Application.builder().token(self.token).build()
        
        # Регистрируем обработчики
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CallbackQueryHandler(self.button_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        
        print("Админ-бот запущен!")
        application.run_polling()

if __name__ == '__main__':
    bot = AdminBot()
    bot.run()

