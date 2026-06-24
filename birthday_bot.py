#!/usr/bin/env python3
"""Бот, который раз в сутки пишет в чат, у кого сегодня день рождения.

Данные берутся из публичной Google-таблицы (CSV-экспорт), сообщение шлётся
через Telegram Bot API. Запускается по расписанию (GitHub Actions) либо вручную
для проверки. Зависимостей нет — только стандартная библиотека.

Локальная проверка:
    python birthday_bot.py --dry-run          # показать сообщение, не отправлять
    python birthday_bot.py --date 06.08       # проверить конкретный день (ДД.ММ)
    python birthday_bot.py                     # реально отправить в чат (нужны env)

Переменные окружения для отправки:
    BOT_TOKEN  — токен бота от @BotFather
    CHAT_ID    — @username чата (напр. @undercrimea) или числовой id
"""

import argparse
import csv
import io
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from greetings import pick_greeting

# Публичная таблица с днями рождения (CSV-экспорт листа gid=0).
SHEET_ID = "1ZINwZNhdn5YSxXJORaHuokBm6ITbHAD2PaWwQjm8A08"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

# МСК — стабильный UTC+3 без перехода на летнее время (с 2014 года).
MSK = timezone(timedelta(hours=3), "MSK")

# Русские сокращения месяцев из колонки «Дата» (формат «01.авг.»).
RU_MONTHS = {
    "янв": 1, "фев": 2, "мар": 3, "апр": 4, "май": 5, "июн": 6,
    "июл": 7, "авг": 8, "сен": 9, "окт": 10, "ноя": 11, "дек": 12,
}


def fetch_csv(url=CSV_URL):
    """Скачать CSV-таблицу и вернуть её текст."""
    req = urllib.request.Request(url, headers={"User-Agent": "birthday-bot/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def parse_date(date_str):
    """«01.авг.» -> (1, 8). Возвращает None, если строку не разобрать."""
    if not date_str:
        return None
    parts = [p for p in date_str.strip().strip(".").lower().split(".") if p]
    if len(parts) < 2:
        return None
    try:
        day = int(parts[0])
    except ValueError:
        return None
    month = RU_MONTHS.get(parts[1][:3])
    if month is None or not 1 <= day <= 31:
        return None
    return day, month


def parse_rows(csv_text):
    """Разобрать CSV в список словарей {name, day, month}.

    Колонки по позиции: [0] индекс, [1] Имя, [2] Дата, [3] Месяц.
    Строки без имени или с неразборчивой датой пропускаются.
    """
    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)
    people = []
    for row in rows[1:]:  # пропускаем заголовок
        if len(row) < 3:
            continue
        name = row[1].strip()
        parsed = parse_date(row[2])
        if not name or parsed is None:
            continue
        day, month = parsed
        people.append({"name": name, "day": day, "month": month})
    return people


def birthdays_today(people, today):
    """Имена тех, у кого день рождения в дату `today` (день+месяц)."""
    return [p["name"] for p in people if p["day"] == today.day and p["month"] == today.month]


def build_message(names, greeting=""):
    """Текст сообщения для чата: список именинников + поздравление дня."""
    if not names:
        return "Сегодня ДР нет"
    lines = ["🎉 Сегодня день рождения у:"]
    lines += [f"• {name}" for name in names]
    if greeting:
        lines += ["", greeting]
    return "\n".join(lines)


def send_telegram(token, chat_id, text):
    """Отправить сообщение через Telegram Bot API. Бросает при ошибке."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    if not payload.get("ok"):
        raise RuntimeError(f"Telegram API error: {payload}")
    return payload


def resolve_today(date_arg):
    """Дата, на которую считаем именинников. По умолчанию — сегодня в МСК."""
    if date_arg:
        day_str, month_str = date_arg.split(".")
        # год не важен — сравниваем только день и месяц
        return datetime(2000, int(month_str), int(day_str))
    return datetime.now(MSK)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Бот дней рождения для Telegram")
    parser.add_argument("--dry-run", action="store_true",
                        help="показать сообщение в консоли, не отправлять в чат")
    parser.add_argument("--date", metavar="ДД.ММ",
                        help="проверить конкретный день вместо сегодняшнего")
    args = parser.parse_args(argv)

    today = resolve_today(args.date)
    people = parse_rows(fetch_csv())
    names = birthdays_today(people, today)
    text = build_message(names, pick_greeting(today))

    if args.dry_run:
        print(f"[dry-run] дата: {today.day:02d}.{today.month:02d}, записей в таблице: {len(people)}")
        print(text)
        return 0

    token = os.environ.get("BOT_TOKEN")
    chat_id = os.environ.get("CHAT_ID")
    if not token or not chat_id:
        print("Ошибка: не заданы BOT_TOKEN и/или CHAT_ID в переменных окружения.",
              file=sys.stderr)
        print("Для проверки без отправки запустите: python birthday_bot.py --dry-run",
              file=sys.stderr)
        return 1

    send_telegram(token, chat_id, text)
    print(f"Отправлено в {chat_id}: {text!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
