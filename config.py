import os

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
OWNER_ID = 7023690411

# کول‌داون‌ها و تنظیمات
RIP_COOLDOWN = 10
ABILITY_COOLDOWN = 20
ENERGY_COST = 20
EXHAUSTION_TIME = 120
MAX_GOALS = 3 # بازی با ۳ گل تموم میشه

RANKS = [
    (0, "🥉 Bronze", 100),
    (100, "🥈 Silver", 110),
    (250, "🥇 Gold", 120),
    (500, "💎 Blue Lock", 130),
    (1000, "👑 Legend", 150)
]