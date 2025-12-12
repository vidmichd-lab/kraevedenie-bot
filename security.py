import os
import logging
from datetime import datetime
from typing import Tuple
from telegram import Update

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('security.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SecurityManager:
    def __init__(self):
        self.admin_ids = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
        self.blocked_users = set()
        self.suspicious_activity = []
    
    def is_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь администратором"""
        if not self.admin_ids:
            logger.warning("ADMIN_IDS не настроен! Админ-доступ отключен.")
            return False
        return user_id in self.admin_ids
    
    def is_blocked(self, user_id: int) -> bool:
        """Проверяет, заблокирован ли пользователь"""
        return user_id in self.blocked_users
    
    def log_suspicious_activity(self, user_id: int, username: str, action: str, details: str = ""):
        """Логирует подозрительную активность"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'username': username,
            'action': action,
            'details': details
        }
        self.suspicious_activity.append(log_entry)
        logger.warning(f"Suspicious activity: User {user_id} (@{username}) tried to {action}. Details: {details}")
    
    def validate_date(self, date_str: str) -> bool:
        """Валидация формата даты"""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            # Проверяем, что дата не слишком далеко в прошлом или будущем
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            now = datetime.now()
            # Разрешаем даты от 2020 года до 2030 года
            if date_obj.year < 2020 or date_obj.year > 2030:
                return False
            return True
        except (ValueError, TypeError):
            return False
    
    def validate_url(self, url: str) -> bool:
        """Валидация URL"""
        if not url or not isinstance(url, str):
            return False
        # Простая проверка на наличие http/https
        return url.startswith(('http://', 'https://'))
    
    def sanitize_text(self, text: str, max_length: int = 5000) -> str:
        """Очистка и ограничение длины текста"""
        if not text:
            return ""
        # Удаляем потенциально опасные символы
        text = text.replace('\x00', '').replace('\r', '')
        # Ограничиваем длину
        if len(text) > max_length:
            text = text[:max_length]
        return text.strip()
    
    def check_admin_access(self, update: Update) -> Tuple[bool, str]:
        """Проверяет доступ администратора с логированием"""
        if not update.effective_user:
            return False, "Не удалось определить пользователя"
        
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name
        
        if self.is_blocked(user_id):
            self.log_suspicious_activity(user_id, username, "access_attempt", "Blocked user tried to access")
            return False, "Доступ заблокирован"
        
        if not self.is_admin(user_id):
            self.log_suspicious_activity(user_id, username, "unauthorized_access", "Non-admin tried to access admin functions")
            return False, "У вас нет доступа к админ-панели"
        
        return True, ""

