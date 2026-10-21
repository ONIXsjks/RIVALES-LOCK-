import os

# 🔑 توکن از Environment Variable خونده می‌شه
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# 👑 مالک
OWNER_ID = 7023690411

# ⏳ کول‌داون‌ها (ثانیه)
RIP_COOLDOWN = 10       # کول‌داون بین هر ریپ
ABILITY_COOLDOWN = 20   # کول‌داون هر Ability (۲۰ ثانیه)

# ⚡ سیستم انرژی
ENERGY_COST = 20        # هر ریپ چقدر انرژی کم می‌کنه
EXHAUSTION_TIME = 120   # اگر انرژی صفر بشه، ۱۲۰ ثانیه (۲ دقیقه) قفل می‌شه

# ⚽ پایان بازی
MAX_GOALS = 5           # بعد از ۵ گل بازی تموم می‌شه

# 🏆 رنک‌ها
RANKS = [
    (0, "🥉 Bronze"),
    (100, "🥈 Silver"),
    (250, "🥇 Gold"),
    (500, "💎 Blue Lock"),
    (1000, "👑 Legend")
]