# Использование GitHub Secrets для безопасного хранения токенов

## Проблема безопасности

⚠️ **ВАЖНО:** Токены ботов были случайно закоммичены в репозиторий. Нужно:

1. **Немедленно заменить токены** - создайте новых ботов через @BotFather
2. **Удалить старые токены из истории Git** (см. инструкцию ниже)
3. **Использовать GitHub Secrets** для хранения токенов

## Шаг 1: Создайте новых ботов

1. Откройте [@BotFather](https://t.me/BotFather)
2. Создайте нового бота: `/newbot`
3. Получите новый токен
4. **Повторите для админ-бота**

## Шаг 2: Добавьте токены в GitHub Secrets

1. Перейдите в ваш репозиторий на GitHub
2. Нажмите **Settings** → **Secrets and variables** → **Actions**
3. Нажмите **New repository secret**
4. Добавьте секреты:
   - `TELEGRAM_BOT_TOKEN` = ваш новый токен основного бота
   - `ADMIN_BOT_TOKEN` = ваш новый токен админ-бота
   - `ADMIN_IDS` = ваш Telegram ID

## Шаг 3: Удалите токены из истории Git

Выполните в терминале:

```bash
# Установите git-filter-repo (если еще не установлен)
pip install git-filter-repo

# Удалите токен из всей истории Git
git filter-repo --invert-paths --path DEPLOY.md --force

# Или используйте BFG Repo-Cleaner
# java -jar bfg.jar --replace-text passwords.txt
```

**Альтернативный способ (проще):**

```bash
# Создайте новый репозиторий без истории
git checkout --orphan new-main
git add -A
git commit -m "Clean repository without tokens"
git branch -D main
git branch -m main
git push -f origin main
```

⚠️ **Внимание:** Это перезапишет историю. Убедитесь, что у вас есть бэкап!

## Шаг 4: Используйте Secrets в GitHub Actions (если используете)

Создайте файл `.github/workflows/deploy.yml`:

```yaml
name: Deploy Bot

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Create .env file
        run: |
          echo "TELEGRAM_BOT_TOKEN=${{ secrets.TELEGRAM_BOT_TOKEN }}" >> .env
          echo "ADMIN_BOT_TOKEN=${{ secrets.ADMIN_BOT_TOKEN }}" >> .env
          echo "ADMIN_IDS=${{ secrets.ADMIN_IDS }}" >> .env
      - name: Deploy
        run: python3 bot.py
```

## Шаг 5: Для Railway/Render

На этих платформах используйте их встроенные секреты:

### Railway:
1. Settings → Variables
2. Добавьте переменные (они автоматически зашифрованы)

### Render:
1. Environment → Environment Variables
2. Добавьте переменные (они автоматически зашифрованы)

## Проверка безопасности

После удаления токенов проверьте:

```bash
# Проверьте, что токены не в истории
git log --all --full-history -p | grep -i "8508993803"

# Проверьте текущие файлы
grep -r "8508993803" .

# Если ничего не найдено - отлично!
```

## Рекомендации

✅ **Делайте:**
- Используйте GitHub Secrets
- Используйте переменные окружения на хостинге
- Регулярно ротируйте токены
- Используйте `.env.example` для документации

❌ **Не делайте:**
- Не коммитьте `.env` файлы
- Не публикуйте токены в документации
- Не отправляйте токены в сообщениях
- Не храните токены в открытом виде

