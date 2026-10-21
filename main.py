import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "/app/data/blue_lock.db")

def db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = db(); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, name TEXT, rank_points INTEGER DEFAULT 0,
        goals INTEGER DEFAULT 0, saves INTEGER DEFAULT 0, last_rip INTEGER DEFAULT 0,
        game_goals INTEGER DEFAULT 0, game_active INTEGER DEFAULT 0,
        energy INTEGER DEFAULT 100, exhausted_until INTEGER DEFAULT 0, photo_path TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_slots (
        user_id INTEGER, slot_number INTEGER, character_id INTEGER, PRIMARY KEY (user_id, slot_number))''')
    c.execute('''CREATE TABLE IF NOT EXISTS characters (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, tier TEXT,
        defense INTEGER, dribble_defense INTEGER, attack INTEGER, photo_file_id TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS abilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name_en TEXT UNIQUE, name_fa TEXT,
        aliases TEXT, power INTEGER, cooldown INTEGER DEFAULT 20, category TEXT, owner TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS character_abilities (
        character_id INTEGER, ability_id INTEGER, PRIMARY KEY (character_id, ability_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS ability_cooldowns (
        user_id INTEGER, ability_id INTEGER, last_used INTEGER, PRIMARY KEY (user_id, ability_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS character_messages (
        message_id INTEGER PRIMARY KEY, chat_id INTEGER, character_id INTEGER, expires_at INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bot_images (
        key TEXT PRIMARY KEY, file_id TEXT, updated_at INTEGER, updated_by INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, reward_multiplier REAL DEFAULT 1.0,
        starts_at INTEGER, ends_at INTEGER, is_active INTEGER DEFAULT 1, photo_file_id TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bans (
        user_id INTEGER PRIMARY KEY, reason TEXT, banned_at INTEGER, banned_by INTEGER)''')
    conn.commit(); conn.close()

CHARACTERS = [
    ("Noel Noa","master",95,90,95),("Lavinho","master",85,95,90),("Leonardo Luna","master",80,85,90),
    ("Chris Prince","master",90,80,85),("Mark Snuffy","master",85,75,80),("Pablo Cavascoz","master",80,85,85),
    ("Julian Loki","master",75,95,85),("Dada Silva","master",85,80,75),("Blake","master",80,75,80),
    ("Bunny Iglesias","world_class",75,70,75),("Lockhart","world_class",70,65,70),("Itoshi Sae","world_class",85,90,85),
    ("Vivian Hugo","world_class",70,75,70),("Don Lorenzo","world_class",85,80,75),("Michael Kaiser","world_class",80,85,90),
    ("Teddy Knight","world_class",70,70,75),("Charles Chevalier","world_class",75,80,75),("Itoshi Rin","world_class",90,85,90),
    ("Meguru Bachira","world_class",65,95,80),("Tabito Karasu","world_class",80,75,75),("Ikki Niko","world_class",75,70,65),
    ("Reo Mikage","world_class",80,85,75),("Kenyu Yukimiya","world_class",70,85,75),("Ryusei Shido","world_class",75,80,90),
    ("Barou Shoei","world_class",70,75,95),("Alexis Ness","world_class",75,75,70),("Jin Kiyora","world_class",80,75,70),
    ("Onazi","world_class",70,65,75),("Seishiro Nagi","world_class",65,85,90),("Oliver Aiku","world_class",90,80,70),
    ("Agi","world_class",65,70,75),("Ranze Kurona","world_class",70,80,65),("Eita Otoya","world_class",65,85,75),
    ("Kusu","world_class",70,70,70),("Jyubei Aryu","world_class",85,65,70),("Yo Hiori","world_class",65,75,70),
    ("Sendo","world_class",75,65,80),("Isagi Yoichi","world_class",75,70,85),("Chigiri","world_class",65,90,80),
    ("Igaguri","world_class",60,55,50),("Gin Gagamaru","world_class",85,70,65),("Zantetsu","world_class",75,65,70),
    ("Nanase","world_class",70,70,65),
]

ABILITIES = [
    ("Direct Shot","شوت مستقیم","directshot,دایرکت,شوت مستقیم",80,20,"shot","Isagi Yoichi"),
    ("Gyro Shot","شوت چرخشی","gyro,ژایرو",85,20,"shot","Itoshi Rin"),
    ("Knuckle Shot","شوت بی‌جهت","knuckle,ناکل",85,20,"shot","Michael Kaiser"),
    ("Bicycle Kick","قیچی برگردون","bicycle,قیچی",85,20,"shot","Ryusei Shido"),
    ("Predator Shot","شوت شکارچی","predator,پردیتور",90,20,"shot","Itoshi Rin"),
    ("Kaiser Impact","ضربه کایزر","kaiser,کایزر",95,20,"shot","Michael Kaiser"),
    ("Barou Charge","حمله بارو","barou,بارو",90,20,"shot","Barou Shoei"),
    ("Sniper Shot","شوت تک‌تیرانداز","sniper,اسنایپر",85,20,"shot","Kenyu Yukimiya"),
    ("Trap","تله","trap,ترپ,تله",75,20,"dribble","Isagi Yoichi"),
    ("Elastic Dribble","دریبل الاستیک","elastic,الاستیک",85,20,"dribble","Meguru Bachira"),
    ("Flow Dribble","دریبل جریان","flowdribble,فلو دریبل",85,20,"dribble","Meguru Bachira"),
    ("Speed Dribble","دریبل سرعتی","speed,اسپید",90,20,"dribble","Chigiri"),
    ("God Speed","سرعت خدا","godspeed,گاد اسپید",95,20,"dribble","Julian Loki"),
    ("Magician Dribble","دریبل جادوگر","magician,ماجیشن",90,20,"dribble","Itoshi Sae"),
    ("Block","بلاک","block,بلاک",75,20,"defend","Ikki Niko"),
    ("Slide Tackle","تکل سرشی","slide,اسلاید",85,20,"defend","Oliver Aiku"),
    ("Metavision","دید فراگیر","metavision,متاویژن",85,20,"defend","Isagi Yoichi"),
    ("Aura Defense","دفاع هاله‌ای","aura,آورا",90,20,"defend","Don Lorenzo"),
    ("Iron Wall","دیوار آهنی","ironwall,آیرون وال",90,20,"defend","Jyubei Aryu"),
    ("Predator Eye","چشم شکارچی","predatoreye,پردیتور آی",90,20,"defend","Itoshi Rin"),
    ("Flow","جریان","flow,فلو",90,20,"special","Meguru Bachira"),
    ("Protagonist Aura","هاله قهرمان","protagonist,پروتاگونیست",95,20,"special","Isagi Yoichi"),
    ("Emperor Aura","هاله امپراتور","emperor,امپراتور",95,20,"special","Michael Kaiser"),
    ("God Mode","حالت خدا","godmode,گاد مود",100,20,"special","Noel Noa"),
    ("Berserker Mode","حالت دیوانه","berserker,برزرکر",95,20,"special","Ryusei Shido"),
]

def seed():
    conn = db(); c = conn.cursor()
    for ch in CHARACTERS:
        try: c.execute("INSERT INTO characters (name,tier,defense,dribble_defense,attack) VALUES (?,?,?,?,?)", ch)
        except: pass
    for ab in ABILITIES:
        try: c.execute("INSERT INTO abilities (name_en,name_fa,aliases,power,cooldown,category,owner) VALUES (?,?,?,?,?,?,?)", ab)
        except: pass
    
    # 🔧 رفع باگ Abilityها
    c.execute("INSERT OR IGNORE INTO character_abilities (character_id,ability_id) SELECT c.id,a.id FROM characters c, abilities a WHERE c.name=a.owner")
    c.execute('''INSERT OR IGNORE INTO character_abilities (character_id, ability_id)
                 SELECT c.id, a.id FROM characters c, abilities a 
                 WHERE c.id NOT IN (SELECT character_id FROM character_abilities) 
                 AND a.category IN ('shot', 'dribble', 'defend') 
                 GROUP BY c.id HAVING COUNT(a.id) <= 3''')
    conn.commit(); conn.close()
import time
import random
from config import RANKS, ABILITY_COOLDOWN, ENERGY_COST, EXHAUSTION_TIME
from database import db

def get_rank(p):
    for t,n in reversed(RANKS):
        if p >= t: return n
    return RANKS[0][1]

def is_banned(uid):
    conn = db(); c = conn.cursor()
    c.execute("SELECT 1 FROM bans WHERE user_id=?", (uid,))
    r = c.fetchone(); conn.close(); return r is not None

def get_user(uid):
    conn = db(); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    r = c.fetchone(); conn.close(); return r

def get_slots(uid):
    conn = db(); c = conn.cursor()
    c.execute("""SELECT us.slot_number,c.id,c.name FROM user_slots us
                 JOIN characters c ON us.character_id=c.id
                 WHERE us.user_id=? ORDER BY us.slot_number""", (uid,))
    r = c.fetchall(); conn.close(); return r

def get_abilities(uid):
    conn = db(); c = conn.cursor()
    c.execute("""SELECT DISTINCT a.* FROM user_slots us
                 JOIN character_abilities ca ON us.character_id=ca.character_id
                 JOIN abilities a ON ca.ability_id=a.id
                 WHERE us.user_id=?""", (uid,))
    r = c.fetchall(); conn.close(); return r

def check_rip_status(uid):
    conn = db(); c = conn.cursor()
    c.execute("SELECT last_rip, energy, exhausted_until FROM users WHERE user_id=?", (uid,))
    r = c.fetchone(); conn.close()
    if not r: return False, "شما ثبت‌نام نکرده‌اید."
    now = time.time()
    if r[2] > now: return False, f"😵 خسته شدی! انرژی صفره.\n⏱ {int(r[2] - now)} ثانیه دیگه استراحت کن."
    if now - r[0] < 10: return False, f"⏳ صبر کن! {int(10 - (now - r[0]))} ثانیه تا ریپ بعدی."
    return True, ""

def consume_energy(uid):
    conn = db(); c = conn.cursor()
    c.execute("SELECT energy FROM users WHERE user_id=?", (uid,))
    energy = c.fetchone()[0]
    new_energy = energy - ENERGY_COST
    exhausted = 0
    if new_energy <= 0:
        new_energy = 0
        exhausted = int(time.time()) + EXHAUSTION_TIME
    c.execute("UPDATE users SET energy=?, exhausted_until=?, last_rip=? WHERE user_id=?", (new_energy, exhausted, time.time(), uid))
    conn.commit(); conn.close()
    return new_energy, exhausted

def ab_cd(uid, aid):
    conn = db(); c = conn.cursor()
    c.execute("SELECT last_used FROM ability_cooldowns WHERE user_id=? AND ability_id=?", (uid, aid))
    r = c.fetchone(); conn.close()
    if not r: return 0
    return max(0, int(ABILITY_COOLDOWN - (time.time()-r[0])))

def set_ab_cd(uid, aid):
    conn = db(); c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO ability_cooldowns (user_id,ability_id,last_used) VALUES (?,?,?)", (uid, aid, time.time()))
    conn.commit(); conn.close()

def find_ability(text, abilities):
    text = text.strip().lower()
    for ab in abilities:
        if text == ab[1].lower() or text == ab[2]: return ab
        if text in [a.strip().lower() for a in ab[3].split(',')]: return ab
    return None

def simulate(power, defense, bonus=0):
    a = power + bonus + random.randint(-10,10)
    d = defense + random.randint(-10,10)
    return ("goal", a-d) if a > d else ("save", d-a)

def get_image(key):
    conn = db(); c = conn.cursor()
    c.execute("SELECT file_id FROM bot_images WHERE key=?", (key,))
    r = c.fetchone(); conn.close()
    return r[0] if r and r[0] else None

def set_image(key, fid, uid):
    conn = db(); c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO bot_images (key,file_id,updated_at,updated_by) VALUES (?,?,?,?)", (key, fid, int(time.time()), uid))
    conn.commit(); conn.close()
import telebot
from telebot import types
import time
from config import TOKEN, OWNER_ID, MAX_GOALS
from database import init_db, seed, db
from utils import *

bot = telebot.TeleBot(TOKEN)

def show_main_menu(chat_id, uid, name, edit_msg_id=None):
    user = get_user(uid)
    rank = get_rank(user[2])
    text = f"🎮✨ **Blue Lock Bot** ✨🎮\n\n👋 سلام {name}!\n🏆 رنک: {rank} ({user[2]} امتیاز)\n⚡ انرژی: {user[8]}/100\n"
    if user[9] > time.time(): text += f"😵 خسته (تا {int(user[9]-time.time())} ثانیه)\n"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("🎯 ریپ بزن", callback_data="menu_rip"), types.InlineKeyboardButton("🛡 اسلات", callback_data="menu_slots"))
    markup.add(types.InlineKeyboardButton("📊 آمار", callback_data="menu_stats"), types.InlineKeyboardButton("🏆 لیدربورد", callback_data="menu_top"))
    markup.add(types.InlineKeyboardButton("📖 Abilityها", callback_data="menu_abilities"))
    if uid == OWNER_ID: markup.add(types.InlineKeyboardButton("👑 پنل مالک", callback_data="menu_admin"))
        
    banner = get_image('welcome_banner')
    if edit_msg_id:
        if banner: bot.edit_message_caption(caption=text, chat_id=chat_id, message_id=edit_msg_id, reply_markup=markup, parse_mode='Markdown')
        else: bot.edit_message_text(text, chat_id=chat_id, message_id=edit_msg_id, reply_markup=markup, parse_mode='Markdown')
    else:
        if banner: bot.send_photo(chat_id, banner, caption=text, reply_markup=markup, parse_mode='Markdown')
        else: bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id; name = message.from_user.first_name
    if is_banned(uid): bot.reply_to(message, "🚫✨ دسترسی مسدود! ✨🚫"); return
    if not get_user(uid):
        conn = db(); c = conn.cursor(); c.execute("INSERT INTO users (user_id,name) VALUES (?,?)", (uid, name)); conn.commit(); conn.close()
    show_main_menu(message.chat.id, uid, name)

@bot.message_handler(commands=['rip'])
def rip_cmd(message):
    uid = message.from_user.id
    if is_banned(uid): return
    if not get_slots(uid): bot.reply_to(message, "🎰✨ اول کاراکتر انتخاب کن! ✨🎰\n📌 /slots"); return
    status, msg = check_rip_status(uid)
    if not status: bot.reply_to(message, msg); return
        
    bot.send_message(message.chat.id, "🎯✨ **انتخاب هدف** ✨🎯\n\n📌 روی پیام هر کاراکتر Reply بزن + اسم Ability!")
    conn = db(); c = conn.cursor(); c.execute("SELECT * FROM characters ORDER BY RANDOM() LIMIT 4"); chars = c.fetchall(); conn.close()
    
    for ch in chars:
        caption = f"🎭✨ **{ch[1]}** ✨🎭\n\n🛡 دفاع: {ch[3]}\n🌀 دریبل‌دفاع: {ch[4]}\n⚔ حمله: {ch[5]}\n\n📌 Reply بزن + اسم Ability!"
        sent = bot.send_photo(message.chat.id, ch[6], caption=caption, parse_mode='Markdown') if ch[6] else bot.send_message(message.chat.id, caption, parse_mode='Markdown')
        conn = db(); c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO character_messages (message_id,chat_id,character_id,expires_at) VALUES (?,?,?,?)", (sent.message_id, message.chat.id, ch[0], time.time()+600))
        conn.commit(); conn.close()

@bot.message_handler(func=lambda m: m.reply_to_message is not None)
def handle_reply(message):
    uid = message.from_user.id
    if is_banned(uid): return
    rid = message.reply_to_message.message_id
    conn = db(); c = conn.cursor()
    c.execute("SELECT character_id FROM character_messages WHERE message_id=? AND expires_at>?", (rid, time.time()))
    r = c.fetchone(); conn.close()
    if not r: return
    
    status, msg = check_rip_status(uid)
    if not status: bot.reply_to(message, msg); return
        
    abilities = get_abilities(uid)
    if not abilities: bot.reply_to(message, "❌ Ability نداری! /slots"); return
    ab = find_ability(message.text, abilities)
    if not ab: bot.reply_to(message, "❌✨ Ability پیدا نشد! ✨❌\n📖 /abilities"); return
        
    cd = ab_cd(uid, ab[0])
    if cd > 0: bot.reply_to(message, f"⏳ {ab[2]} — {cd} ثانیه کول‌داون داره!"); return
        
    energy_left, exhausted_until = consume_energy(uid)
    conn = db(); c = conn.cursor(); c.execute("SELECT name,defense FROM characters WHERE id=?", (r[0],)); ch = c.fetchone(); conn.close()
    res, diff = simulate(ab[4], ch[1])
    
    if res == "goal":
        pts = 10 if diff > 20 else 7
        text = f"⚽✨ **گل!!!** ✨⚽\n\n🎭 {ch[0]}\n🎯 {ab[2]} ({ab[1]})\n💪 {ab[4]} vs 🛡 {ch[1]}\n\n🏆 +{pts} امتیاز\n⚡ انرژی: {energy_left}/100"
    else:
        pts = -5
        text = f"🧤✨ **مهار!** ✨🧤\n\n🎭 {ch[0]}\n🎯 {ab[2]}\n💪 {ab[4]} vs 🛡 {ch[1]}\n\n🏆 {pts} امتیاز\n⚡ انرژی: {energy_left}/100"
    if exhausted_until > 0: text += f"\n\n😵 **انرژی تموم شد!**\n⏱ باید ۲ دقیقه استراحت کنی."
        
    conn = db(); c = conn.cursor()
    c.execute("UPDATE users SET rank_points=rank_points+? WHERE user_id=?", (pts, uid))
    if res == "goal":
        c.execute("UPDATE users SET goals=goals+1, game_goals=game_goals+1 WHERE user_id=?", (uid,))
        c.execute("SELECT game_goals FROM users WHERE user_id=?", (uid,)); gg = c.fetchone()[0]
    else:
        c.execute("UPDATE users SET saves=saves+1 WHERE user_id=?", (uid,)); gg = 0
    conn.commit(); conn.close()
    set_ab_cd(uid, ab[0])
    
    if res == "goal" and gg >= MAX_GOALS:
        text += f"\n\n🎉✨ بازی تموم شد! {MAX_GOALS} گل زدی! ✨🎉"
        conn = db(); c = conn.cursor(); c.execute("UPDATE users SET game_goals=0 WHERE user_id=?", (uid,)); conn.commit(); conn.close()
        
    try: bot.edit_message_caption(caption=text, chat_id=message.chat.id, message_id=rid, reply_markup=None, parse_mode='Markdown')
    except:
        try: bot.edit_message_text(text, chat_id=message.chat.id, message_id=rid, reply_markup=None, parse_mode='Markdown')
        except: bot.reply_to(message, text, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    uid = call.from_user.id; data = call.data; chat_id = call.message.chat.id; msg_id = call.message.message_id
    if data == "menu_rip": bot.answer_callback_query(call.id, "🎯 /rip رو بزن!")
    elif data == "menu_stats":
        u = get_user(uid)
        t = f"📊✨ **آمار شما** ✨📊\n\n👤 {u[1]}\n🏆 {get_rank(u[2])} ({u[2]})\n⚽ {u[3]}\n🧤 {u[4]}\n⚡ انرژی: {u[8]}/100"
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 برگشت", callback_data="back_main"))
        try: bot.edit_message_caption(caption=t, chat_id=chat_id, message_id=msg_id, reply_markup=markup, parse_mode='Markdown')
        except: bot.edit_message_text(t, chat_id=chat_id, message_id=msg_id, reply_markup=markup, parse_mode='Markdown')
        bot.answer_callback_query(call.id)
    elif data == "back_main": show_main_menu(chat_id, uid, call.from_user.first_name, edit_msg_id=msg_id); bot.answer_callback_query(call.id)
    elif data == "menu_abilities":
        abs_ = get_abilities(uid)
        t = "📖✨ **Abilityهای شما** ✨📖\n\n" if abs_ else "📖✨ Ability نداری! /slots"
        for a in abs_: t += f"• {a[2]} ({a[1]}) — ⏱{a[5]}s\n"
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 برگشت", callback_data="back_main"))
        bot.edit_message_text(t, chat_id=chat_id, message_id=msg_id, reply_markup=markup, parse_mode='Markdown')
        bot.answer_callback_query(call.id)

if __name__ == "__main__":
    init_db()
    seed()
    print("🚀✨ Blue Lock Bot روشن شد! ✨🚀")
    bot.infinity_polling()