import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "/app/data/blue_lock.db")

def migrate():
    print("🔄 در حال آپدیت دیتابیس...")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 🆕 اضافه کردن ستون‌های جدید به users
    try: c.execute("ALTER TABLE users ADD COLUMN energy INTEGER DEFAULT 100")
    except: pass
    try: c.execute("ALTER TABLE users ADD COLUMN exhausted_until INTEGER DEFAULT 0")
    except: pass
    try: c.execute("ALTER TABLE users ADD COLUMN coins INTEGER DEFAULT 0")
    except: pass

    # 🆕 اضافه کردن ستون role (پست) به کاراکترها
    try: c.execute("ALTER TABLE characters ADD COLUMN role TEXT DEFAULT 'MF'")
    except: pass

    # 🆕 ساخت جدول matches
    c.execute('''CREATE TABLE IF NOT EXISTS matches (
        chat_id INTEGER PRIMARY KEY, p1_id INTEGER, p2_id INTEGER, 
        p1_goals INTEGER DEFAULT 0, p2_goals INTEGER DEFAULT 0, 
        turn_id INTEGER)''')

    # 🆕 ساخت جدول user_abilities
    c.execute('''CREATE TABLE IF NOT EXISTS user_abilities (
        user_id INTEGER, ability_id INTEGER, PRIMARY KEY (user_id, ability_id))''')

    # 🆕 ساخت جدول history
    c.execute('''CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT, attacker_id INTEGER, target_id INTEGER, 
        ability_name TEXT, result TEXT, points INTEGER, timestamp INTEGER)''')

    # 🆕 ساخت جدول events
    c.execute('''CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, event_type TEXT, target_id INTEGER, 
        multiplier REAL, ends_at INTEGER, is_active INTEGER DEFAULT 1)''')

    conn.commit()
    conn.close()
    print("🎉 دیتابیس با موفقیت آپدیت شد!")

if __name__ == "__main__":
    migrate()