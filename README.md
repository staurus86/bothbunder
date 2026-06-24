# Birthday bot для @undercrimea

Раз в сутки в **00:00 по МСК** бот пишет в чат, у кого сегодня день рождения.
Данные берёт из публичной Google-таблицы, поздравления шлёт через Telegram.
Работает бесплатно в облаке GitHub Actions — личный ПК держать включённым не нужно.

- Бот: **@UnderHBbot**
- Чат: **@undercrimea**
- Таблица: [Google Sheets](https://docs.google.com/spreadsheets/d/1ZINwZNhdn5YSxXJORaHuokBm6ITbHAD2PaWwQjm8A08/edit?gid=0)

Если именинников нет — бот пишет `Сегодня ДР нет`.

---

## Как это работает

1. GitHub Actions по расписанию (`cron: 0 21 * * *` UTC = 00:00 МСК) запускает `birthday_bot.py`.
2. Скрипт скачивает таблицу по CSV-ссылке (без ключей — таблица публичная).
3. Парсит колонку «Дата» (формат `01.авг.`), берёт сегодняшнюю дату по МСК, находит совпадения.
4. Отправляет сообщение в чат через Telegram Bot API.

Зависимостей нет — только стандартная библиотека Python 3.9+.

---

## Локальная проверка

```bash
# показать сообщение на сегодня, НЕ отправляя в чат
python birthday_bot.py --dry-run

# проверить конкретный день (ДД.ММ)
python birthday_bot.py --date 06.08 --dry-run

# реально отправить в чат (нужны переменные окружения, см. ниже)
python birthday_bot.py
```

Запуск тестов:

```bash
python -m unittest test_birthday_bot -v
```

### Переменные окружения для реальной отправки

| Переменная  | Значение                                   |
|-------------|--------------------------------------------|
| `BOT_TOKEN` | токен бота от @BotFather                    |
| `CHAT_ID`   | `@undercrimea` (или числовой id чата)       |

PowerShell:

```powershell
$env:BOT_TOKEN="<токен>"; $env:CHAT_ID="@undercrimea"; python birthday_bot.py
```

---

## Развёртывание в GitHub Actions (бесплатно, 24/7)

1. Создайте репозиторий на GitHub (приватный — нормально) и загрузите туда эти файлы:

   ```bash
   git init
   git add .
   git commit -m "Birthday bot"
   git branch -M main
   git remote add origin https://github.com/<ваш-логин>/<репозиторий>.git
   git push -u origin main
   ```

2. В репозитории откройте **Settings → Secrets and variables → Actions → New repository secret**
   и добавьте два секрета:
   - `BOT_TOKEN` — токен бота
   - `CHAT_ID` — `@undercrimea`

3. Готово. Расписание уже задано в `.github/workflows/birthday.yml`.
   Проверить вручную, не дожидаясь полуночи: вкладка **Actions → Birthday bot → Run workflow**.

---

## Важные нюансы

- **Точность времени.** GitHub может запустить cron не ровно в 00:00, а с задержкой 5–30 минут
  при высокой нагрузке. Для поздравлений это не критично.
- **Автоотключение.** Если в репозитории **60 дней нет коммитов**, GitHub отключает
  scheduled-workflow. Достаточно изредка делать любой коммит (или нажать Run workflow), чтобы держать его активным.
- **Бот должен оставаться в чате.** Если @UnderHBbot удалить из @undercrimea, отправка перестанет работать.
- **Безопасность токена.** Токен хранится только в GitHub Secrets и локальном окружении — в коде его нет.
  Если токен где-то засветился, перевыпустите его у @BotFather (`/revoke`) и обновите секрет.
