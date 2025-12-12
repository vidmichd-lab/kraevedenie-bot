FROM python:3.9-slim

WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаем папку data если её нет
RUN mkdir -p data

# Запускаем бота
CMD ["python3", "bot.py"]

