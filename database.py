import sqlite3

class Database:
    def __init__(self):
        self.db_path = 'subscribers.db'
        self.init_db()
    
    def init_db(self):
        """Создает таблицу подписчиков"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscribers (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def add_subscriber(self, user_id: int, username: str):
        """Добавляет подписчика"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO subscribers (user_id, username)
            VALUES (?, ?)
        ''', (user_id, username))
        conn.commit()
        conn.close()
    
    def get_all_subscribers(self):
        """Возвращает список всех подписчиков"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM subscribers')
        subscribers = [row[0] for row in cursor.fetchall()]
        conn.close()
        return subscribers

