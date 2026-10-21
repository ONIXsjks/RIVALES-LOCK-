import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "/app/data/blue_lock.db")

def migrate():
    print("🔄 در حال آپدیت دیتابیس...")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # اضافه کردن ستون انرژی و خستگی به جدول کاربران (اگر وجود نداشته باشه)
    try:
        c.execute("ALTER TABLE users ADD COLUMN energy INTEGER DEFAULT 100")
        print("✅ ستون energy اضافه شد.")
    except sqlite3.OperationalError:
        print("ℹ️ ستون energy از قبل وجود داشت.")

    try:
        c.execute("ALTER TABLE users ADD COLUMN exhausted_until INTEGER DEFAULT 0")
        print("✅ ستون exhausted_until اضافه شد.")
    except sqlite3.OperationalError:
        print("ℹ️ ستون exhausted_until از قبل وجود داشت.")

    conn.commit()
    conn.close()
    print("🎉 دیتابیس با موفقیت آپدیت شد!")

if __name__ == "__main__":
    migrate()