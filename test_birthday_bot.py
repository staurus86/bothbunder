"""Тесты парсинга дат, выбора именинников и поздравлений."""

import re
import unittest
from datetime import datetime

import birthday_bot as bb
from greetings import GREETINGS, pick_greeting

# Фрагмент реальной таблицы (включая имя с кавычками и эмодзи).
SAMPLE_CSV = (
    ",Имя,Дата,Месяц\n"
    "6,Максим Альбертович,01.авг.,Август\n"
    "21,Юна,05.авг.,Август\n"
    "26,Аня 🦉,06.авг.,Август\n"
    '83,"Антон ""Ваш Партнер""",23.авг.,Август\n'
    "1,Январский Друг,15.янв.,Январь\n"
    "99,,10.май.,Май\n"            # пустое имя — должно отсеяться
    "100,Битая Строка,непонятно,Май\n"  # неразборчивая дата — отсеять
)


class ParseDateTest(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(bb.parse_date("01.авг."), (1, 8))

    def test_january(self):
        self.assertEqual(bb.parse_date("15.янв."), (15, 1))

    def test_may_three_letters(self):
        self.assertEqual(bb.parse_date("10.май."), (10, 5))

    def test_garbage(self):
        self.assertIsNone(bb.parse_date("непонятно"))

    def test_empty(self):
        self.assertIsNone(bb.parse_date(""))


class ParseRowsTest(unittest.TestCase):
    def setUp(self):
        self.people = bb.parse_rows(SAMPLE_CSV)

    def test_skips_empty_name_and_bad_date(self):
        names = [p["name"] for p in self.people]
        self.assertNotIn("", names)
        self.assertNotIn("Битая Строка", names)

    def test_quoted_name_preserved(self):
        names = [p["name"] for p in self.people]
        self.assertIn('Антон "Ваш Партнер"', names)

    def test_count(self):
        # 5 валидных строк из 7
        self.assertEqual(len(self.people), 5)


class BirthdaysTodayTest(unittest.TestCase):
    def setUp(self):
        self.people = bb.parse_rows(SAMPLE_CSV)

    def test_match(self):
        today = datetime(2026, 8, 6)  # год не важен
        self.assertEqual(bb.birthdays_today(self.people, today), ["Аня 🦉"])

    def test_no_match(self):
        today = datetime(2026, 3, 3)
        self.assertEqual(bb.birthdays_today(self.people, today), [])


class BuildMessageTest(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(bb.build_message([], "Счастья!"), "Сегодня ДР нет")

    def test_one_with_greeting(self):
        msg = bb.build_message(["Юна"], "Счастья и здоровья!")
        self.assertIn("Юна", msg)
        self.assertIn("🎉", msg)
        self.assertIn("Счастья и здоровья!", msg)

    def test_many(self):
        msg = bb.build_message(["Юна", "Аня 🦉"], "Тепла!")
        self.assertIn("Юна", msg)
        self.assertIn("Аня 🦉", msg)
        self.assertIn("Тепла!", msg)


class GreetingsTest(unittest.TestCase):
    def test_exactly_100(self):
        self.assertEqual(len(GREETINGS), 100)

    def test_all_unique(self):
        self.assertEqual(len(set(GREETINGS)), 100)

    def test_no_blanks(self):
        self.assertTrue(all(g.strip() for g in GREETINGS))

    def test_gender_neutral(self):
        # Слова, выдающие род адресата, недопустимы.
        forbidden = re.compile(
            r"\b(его|её|ее|был|была|счастлив|счастлива|рад|рада|горд|горда|сам|сама)\b",
            re.IGNORECASE,
        )
        offenders = [g for g in GREETINGS if forbidden.search(g)]
        self.assertEqual(offenders, [], f"Найдены гендерные маркеры: {offenders}")


class PickGreetingTest(unittest.TestCase):
    def test_deterministic(self):
        d = datetime(2026, 8, 6)
        self.assertEqual(pick_greeting(d), pick_greeting(d))

    def test_varies_across_days(self):
        # За 100 разных дней подряд поздравления не повторяются.
        picks = [pick_greeting(datetime(2026, 1, 1) + __import__("datetime").timedelta(days=i))
                 for i in range(100)]
        self.assertEqual(len(set(picks)), 100)


if __name__ == "__main__":
    unittest.main()
