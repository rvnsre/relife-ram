"""Offline learning data and calculations shared by the desktop and MCP."""
import json
import math
from pathlib import Path
import statistics
import time

LESSONS_FILE = Path(__file__).resolve().parents[3] / "share/relife/lessons.json"
DAY_MS = 86400000


def lessons():
    return json.loads(LESSONS_FILE.read_text(encoding="utf-8"))


def parse_cards(text):
    cards = json.loads(text)
    if not isinstance(cards, list) or len(cards) > 10000:
        raise ValueError("Etibarsız kart siyahısı.")
    for card in cards:
        if (
            not isinstance(card, dict)
            or not all(isinstance(card.get(key), str) and 0 < len(card[key]) <= 4000
                       for key in ("q", "a"))
            or not all(type(card.get(key)) in (int, float) and 0 <= card[key] <= limit
                       for key, limit in (("due", 10**15), ("interval", 90)))
        ):
            raise ValueError("Etibarsız kart məlumatı.")
    return [{key: card[key] for key in ("q", "a", "due", "interval")} for card in cards]


def now_ms():
    return time.time_ns() // 1000000


def schedule(card, recalled, now):
    interval = min(90, max(1, card["interval"] * 2)) if recalled else 0
    card.update(interval=interval, due=now + (interval * DAY_MS if recalled else 60000))


UNITS = {
    "m": ("length", 1), "cm": ("length", .01), "km": ("length", 1000),
    "g": ("mass", .001), "kg": ("mass", 1), "mg": ("mass", .000001),
    "s": ("time", 1), "min": ("time", 60), "h": ("time", 3600),
}


def convert(value, source, target):
    if type(value) not in (int, float) or not -1e100 <= value <= 1e100:
        raise ValueError("Sonlu ədəd daxil edin.")
    dimension, factor = UNITS[source]
    target_dimension, target_factor = UNITS[target]
    if dimension != target_dimension:
        raise ValueError("Eyni ölçü növünün vahidlərini seçin.")
    return value * factor / target_factor


LABS = {
    "Gərginlik (V)": ("Cərəyan (A), müqavimət (Ω)", 2, lambda i, r: i * max_nonnegative(r)),
    "Düzbucaqlının sahəsi": ("Uzunluq, en", 2, lambda a, b: max_nonnegative(a) * max_nonnegative(b)),
    "Üçbucağın sahəsi": ("Oturacaq, hündürlük", 2, lambda a, b: max_nonnegative(a) * max_nonnegative(b) / 2),
    "Dairənin sahəsi": ("Radius", 1, lambda r: math.pi * max_nonnegative(r) ** 2),
    "Sürət (m/s)": ("Məsafə (m), vaxt (s)", 2, lambda d, t: max_nonnegative(d) / positive(t)),
    "Qüvvə (N)": ("Kütlə (kg), təcil (m/s²)", 2, lambda m, a: max_nonnegative(m) * a),
    "Sıxlıq (kg/m³)": ("Kütlə (kg), həcm (m³)", 2, lambda m, v: max_nonnegative(m) / positive(v)),
    "Torpağın nəmliyi (%)": ("Nəm kütlə (q), quru kütlə (q)", 2,
                            lambda wet, dry: max_nonnegative(wet - dry) / positive(dry) * 100),
    "Ədədi orta": ("Ədədləri boşluqla ayırın", None, statistics.mean),
    "Median": ("Ədədləri boşluqla ayırın", None, statistics.median),
    "Ehtimal": ("Uğurlu nəticə sayı, bütün nəticələrin sayı", 2,
                lambda good, total: count_probability(good, total)),
}


def max_nonnegative(value):
    if value < 0:
        raise ValueError("Mənfi qiymət daxil etməyin.")
    return value


def positive(value):
    if value <= 0:
        raise ValueError("Məxrəcdə müsbət qiymət daxil edin.")
    return value


def count_probability(good, total):
    if not good.is_integer() or not total.is_integer() or not 0 <= good <= total:
        raise ValueError("Sıfırdan kiçik olmayan uyğun tam saylar daxil edin.")
    return good / positive(total)


def calculate(name, text):
    if not text or len(text) > 12000:
        raise ValueError("Ədədləri boşluqla ayırın.")
    values = [float(value.replace(",", ".")) for value in text.split()]
    if not values or not all(-1e100 <= value <= 1e100 for value in values):
        raise ValueError("Sonlu ədədlər daxil edin.")
    _, count, operation = LABS[name]
    if count is None:
        return operation(values)
    if len(values) != count:
        raise ValueError(f"{count} ədəd daxil edin.")
    return operation(*values)


def lesson_plan(subject, grade, topic, objective, minutes):
    if not topic.strip() or not objective.strip() or not 20 <= minutes <= 180:
        raise ValueError("Mövzu, məqsəd və 20–180 dəqiqə arası müddət daxil edin.")
    intro, example, guided, close = (minutes * share // 100 for share in (10, 25, 20, 10))
    independent = minutes - intro - example - guided - close
    return "\n".join((
        f"{subject} | {grade}",
        f"Mövzu: {topic}",
        f"Təlim nəticəsi: {objective}",
        f"{intro} dəq — Mövzuya aid əvvəlki bilikləri sualla yoxla.",
        f"{example} dəq — Bir işlənmiş nümunəni addım-addım izah et.",
        f"{guided} dəq — Bir tapşırığı siniflə birlikdə həll et.",
        f"{independent} dəq — Yeni tapşırığı müstəqil həll etdir.",
        f"{close} dəq — Nəticəni yoxla və növbəti təkrar vaxtını seç.",
    ))
