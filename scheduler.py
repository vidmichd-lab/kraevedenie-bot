from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

class Scheduler:
    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
    
    def start(self):
        """Запускает планировщик ежедневных рассылок в 9:00"""
        self.scheduler.add_job(
            self.send_daily_to_all,
            trigger=CronTrigger(hour=9, minute=0),
            id='daily_event',
            replace_existing=True
        )
        self.scheduler.start()
    
    async def send_daily_to_all(self):
        """Отправляет ежедневное событие всем подписчикам"""
        subscribers = self.bot.db.get_all_subscribers()
        
        if not subscribers:
            print("Нет подписчиков для рассылки")
            return
        
        for user_id in subscribers:
            try:
                await self.bot.send_daily_event(user_id, None)
            except Exception as e:
                print(f"Ошибка отправки пользователю {user_id}: {e}")

