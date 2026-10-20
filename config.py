import os

# 🔑 توکن از Environment Variable خونده می‌شه
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# 👑 مالک
OWNER_ID = 7023690411

# ⏳ کول‌داون‌ها (ثانیه)
RIP_COOLDOWN = 10
ABILITY_COOLDOWN = 30

# ⚽ پایان بازی
MAX_GOALS = 5

# 🏆 رنک‌ها
RANKS = [
    (0, "🥉 Bronze"),
    (100, "🥈 Silver"),
    (250, "🥇 Gold"),
    (500, "💎 Blue Lock"),
    (1000, "👑 Legend")
]