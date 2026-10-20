import telebot
from telebot import types
import sqlite3
import time
import random
import os
from config import TOKEN, OWNER_ID, RIP_COOLDOWN, ABILITY_COOLDOWN, MAX_GOALS, RANKS

bot = telebot.TeleBot(TOKEN)

# 📁 مسیر دائمی دیتابیس
DB_PATH = os.environ.get("DB_PATH", "/app/data/blue_lock.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

admin_states = {}

# ═══════════════════════════════════════
# 💾 دیتابیس
# ═══════════════════════════════════════

def db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = db(); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, name TEXT,
        rank_points INTEGER DEFAULT 0, goals INTEGER DEFAULT 0,
        saves INTEGER DEFAULT 0, last_rip INTEGER DEFAULT 0,
        game_goals INTEGER DEFAULT 0, game_active INTEGER DEFAULT 0,
        photo_path TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_slots (
        user_id INTEGER, slot_number INTEGER, character_id INTEGER,
        PRIMARY KEY (user_id, slot_number))''')
    c.execute('''CREATE TABLE IF NOT EXISTS characters (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE,
        tier TEXT, defense INTEGER, dribble_defense INTEGER,
        attack INTEGER, photo_file_id TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS abilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name_en TEXT UNIQUE,
        name_fa TEXT, aliases TEXT, power INTEGER,
        cooldown INTEGER DEFAULT 30, category TEXT, owner TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS character_abilities (
        character_id INTEGER, ability_id INTEGER,
        PRIMARY KEY (character_id, ability_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS ability_cooldowns (
        user_id INTEGER, ability_id INTEGER, last_used INTEGER,
        PRIMARY KEY (user_id, ability_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS character_messages (
        message_id INTEGER PRIMARY KEY, chat_id INTEGER,
        character_id INTEGER, expires_at INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bot_images (
        key TEXT PRIMARY KEY, file_id TEXT,
        updated_at INTEGER, updated_by INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT,
        reward_multiplier REAL DEFAULT 1.0, starts_at INTEGER,
        ends_at INTEGER, is_active INTEGER DEFAULT 1, photo_file_id TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bans (
        user_id INTEGER PRIMARY KEY, reason TEXT,
        banned_at INTEGER, banned_by INTEGER)''')
    conn.commit(); conn.close()

CHARACTERS = [
    ("Noel Noa","master",95,90,95),("Lavinho","master",85,95,90),
    ("Leonardo Luna","master",80,85,90),("Chris Prince","master",90,80,85),
    ("Mark Snuffy","master",85,75,80),("Pablo Cavascoz","master",80,85,85),
    ("Julian Loki","master",75,95,85),("Dada Silva","master",85,80,75),
    ("Blake","master",80,75,80),
    ("Bunny Iglesias","world_class",75,70,75),("Lockhart","world_class",70,65,70),
    ("Itoshi Sae","world_class",85,90,85),("Vivian Hugo","world_class",70,75,70),
    ("Don Lorenzo","world_class",85,80,75),("Michael Kaiser","world_class",80,85,90),
    ("Teddy Knight","world_class",70,70,75),("Charles Chevalier","world_class",75,80,75),
    ("Itoshi Rin","world_class",90,85,90),("Meguru Bachira","world_class",65,95,80),
    ("Tabito Karasu","world_class",80,75,75),("Ikki Niko","world_class",75,70,65),
    ("Reo Mikage","world_class",80,85,75),("Kenyu Yukimiya","world_class",70,85,75),
    ("Ryusei Shido","world_class",75,80,90),("Barou Shoei","world_class",70,75,95),
    ("Alexis Ness","world_class",75,75,70),("Jin Kiyora","world_class",80,75,70),
    ("Onazi","world_class",70,65,75),("Seishiro Nagi","world_class",65,85,90),
    ("Oliver Aiku","world_class",90,80,70),("Agi","world_class",65,70,75),
    ("Ranze Kurona","world_class",70,80,65),("Eita Otoya","world_class",65,85,75),
    ("Kusu","world_class",70,70,70),("Jyubei Aryu","world_class",85,65,70),
    ("Yo Hiori","world_class",65,75,70),("Sendo","world_class",75,65,80),
    ("Isagi Yoichi","world_class",75,70,85),("Chigiri","world_class",65,90,80),
    ("Igaguri","world_class",60,55,50),("Gin Gagamaru","world_class",85,70,65),
    ("Zantetsu","world_class",75,65,70),("Nanase","world_class",70,70,65),
]

ABILITIES = [
    ("Direct Shot","شوت مستقیم","directshot,دایرکت,شوت مستقیم",80,30,"shot","Isagi Yoichi"),
    ("Gyro Shot","شوت چرخشی","gyro,ژایرو",85,30,"shot","Itoshi Rin"),
    ("Knuckle Shot","شوت بی‌جهت","knuckle,ناکل",85,30,"shot","Michael Kaiser"),
    ("Bicycle Kick","قیچی برگردون","bicycle,قیچی",85,30,"shot","Ryusei Shido"),
    ("Predator Shot","شوت شکارچی","predator,پردیتور",90,30,"shot","Itoshi Rin"),
    ("Kaiser Impact","ضربه کایزر","kaiser,کایزر",95,30,"shot","Michael Kaiser"),
    ("Barou Charge","حمله بارو","barou,بارو",90,30,"shot","Barou Shoei"),
    ("Sniper Shot","شوت تک‌تیرانداز","sniper,اسنایپر",85,30,"shot","Kenyu Yukimiya"),
    ("Trap","تله","trap,ترپ,تله",75,30,"dribble","Isagi Yoichi"),
    ("Elastic Dribble","دریبل الاستیک","elastic,الاستیک",85,30,"dribble","Meguru Bachira"),
    ("Flow Dribble","دریبل جریان","flowdribble,فلو دریبل",85,30,"dribble","Meguru Bachira"),
    ("Speed Dribble","دریبل سرعتی","speed,اسپید",90,30,"dribble","Chigiri"),
    ("God Speed","سرعت خدا","godspeed,گاد اسپید",95,30,"dribble","Julian Loki"),
    ("Magician Dribble","دریبل جادوگر","magician,ماجیشن",90,30,"dribble","Itoshi Sae"),
    ("Block","بلاک","block,بلاک",75,30,"defend","Ikki Niko"),
    ("Slide Tackle","تکل سرشی","slide,اسلاید",85,30,"defend","Oliver Aiku"),
    ("Metavision","دید فراگیر","metavision,متاویژن",85,30,"defend","Isagi Yoichi"),
    ("Aura Defense","دفاع هاله‌ای","aura,آورا",90,30,"defend","Don Lorenzo"),
    ("Iron Wall","دیوار آهنی","ironwall,آیرون وال",90,30,"defend","Jyubei Aryu"),
    ("Predator Eye","چشم شکارچی","predatoreye,پردیتور آی",90,30,"defend","Itoshi Rin"),
    ("Flow","جریان","flow,فلو",90,30,"special","Meguru Bachira"),
    ("Protagonist Aura","هاله قهرمان","protagonist,پروتاگونیست",95,30,"special","Isagi Yoichi"),
    ("Emperor Aura","هاله امپراتور","emperor,امپراتور",95,30,"special","Michael Kaiser"),
    ("God Mode","حالت خدا","godmode,گاد مود",100,30,"special","Noel Noa"),
    ("Berserker Mode","حالت دیوانه","berserker,برزرکر",95,30,"special","Ryusei Shido"),
]

def seed():
    conn = db(); c = conn.cursor()
    for ch in CHARACTERS:
        try: c.execute("INSERT INTO characters (name,tier,defense,dribble_defense,attack) VALUES (?,?,?,?,?)", ch)
        except: pass
    for ab in ABILITIES:
        try: c.execute("INSERT INTO abilities (name_en,name_fa,aliases,power,cooldown,category,owner) VALUES (?,?,?,?,?,?,?)", ab)
        except: pass
    c.execute("INSERT OR IGNORE INTO character_abilities (character_id,ability_id) SELECT c.id,a.id FROM characters c, abilities a WHERE c.name=a.owner")
    conn.commit(); conn.close()

# ═══════════════════════════════════════
# 🛠 کمکی
# ═══════════════════════════════════════

def get_rank(p):
    for t,n in reversed(RANKS):
        if p >= t: return n
    return RANKS[0][1]

def is_owner(uid): return uid == OWNER_ID

def is_banned(uid):
    conn = db(); c = conn.cursor()
    c.execute("SELECT 1 FROM bans WHERE user_id=?", (uid,))
    r = c.fetchone(); conn.close(); return r is not None

def get_user(uid):
    conn = db(); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    r = c.fetchone(); conn.close(); return r

def get_image(key):
    conn = db(); c = conn.cursor()
    c.execute("SELECT file_id FROM bot_images WHERE key=?", (key,))
    r = c.fetchone(); conn.close()
    return r[0] if r and r[0] else None

def set_image(key, fid, uid):
    conn = db(); c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO bot_images (key,file_id,updated_at,updated_by) VALUES (?,?,?,?)",
              (key, fid, int(time.time()), uid))
    conn.commit(); conn.close()

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

def rip_cd(uid):
    conn = db(); c = conn.cursor()
    c.execute("SELECT last_rip FROM users WHERE user_id=?", (uid,))
    r = c.fetchone(); conn.close()
    if not r: return 0
    return max(0, int(RIP_COOLDOWN - (time.time()-r[0])))

def set_rip_cd(uid):
    conn = db(); c = conn.cursor()
    c.execute("UPDATE users SET last_rip=? WHERE user_id=?", (time.time(), uid))
    conn.commit(); conn.close()

def ab_cd(uid, aid):
    conn = db(); c = conn.cursor()
    c.execute("SELECT last_used FROM ability_cooldowns WHERE user_id=? AND ability_id=?", (uid, aid))
    r = c.fetchone(); conn.close()
    if not r: return 0
    return max(0, int(ABILITY_COOLDOWN - (time.time()-r[0])))

def set_ab_cd(uid, aid):
    conn = db(); c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO ability_cooldowns (user_id,ability_id,last_used) VALUES (?,?,?)",
              (uid, aid, time.time()))
    conn.commit(); conn.close()

def find_ability(text, abilities):
    text = text.strip().lower()
    for ab in abilities:
        if text == ab[1].lower() or text == ab[2]:
            return ab
        if text in [a.strip().lower() for a in ab[3].split(',')]:
            return ab
    return None

def simulate(power, defense, bonus=0):
    a = power + bonus + random.randint(-10,10)
    d = defense + random.randint(-10,10)
    return ("goal", a-d) if a > d else ("save", d-a)

def get_image_name(key):
    names = {'welcome_banner':'🎮 بنر اصلی','rank_bronze':'🥉 رنک Bronze',
             'rank_silver':'🥈 رنک Silver','rank_gold':'🥇 رنک Gold',
             'rank_bluelock':'💎 رنک Blue Lock','rank_legend':'👑 رنک Legend',
             'event_banner':'🎉 بنر رویداد','profile_default':'👤 پروفایل پیش‌فرض'}
    return names.get(key, key)

# ═══════════════════════════════════════
# 🏠 /start
# ═══════════════════════════════════════

@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id; name = message.from_user.first_name
    if is_banned(uid):
        bot.reply_to(message, "🚫✨ دسترسی مسدود! ✨🚫"); return
    user = get_user(uid)
    if not user:
        conn = db(); c = conn.cursor()
        c.execute("INSERT INTO users (user_id,name) VALUES (?,?)", (uid, name))
        conn.commit(); conn.close()
        text = f"🎮✨ به Blue Lock Bot خوش اومدی! ✨🎮\n\n👋 سلام {name}!\n⚽ با ریپ زدن گل بزن و رنک بگیر!\n\n📌 اول: ۴ کاراکتر انتخاب کن!\n🎰 /slots\n\n🎯 /rip — ریپ\n📊 /stats — آمار\n🏆 /top — لیدربورد\n📖 /abilities — Abilityها"
    else:
        rank = get_rank(user[2])
        text = f"🎮✨ خوش برگشتی {name}! ✨🎮\n\n🏆 رنک: {rank} ({user[2]} امتیاز)\n⚽ گل: {user[3]}\n🧤 مهار: {user[4]}\n\n🔥 چی می‌خوای بکنی؟"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("🎯 ریپ", callback_data="menu_rip"),
               types.InlineKeyboardButton("🛡 اسلات", callback_data="menu_slots"))
    markup.add(types.InlineKeyboardButton("📊 آمار", callback_data="menu_stats"),
               types.InlineKeyboardButton("🏆 لیدربورد", callback_data="menu_top"))
    markup.add(types.InlineKeyboardButton("📖 Abilityها", callback_data="menu_abilities"))
    if is_owner(uid):
        markup.add(types.InlineKeyboardButton("👑 پنل مالک", callback_data="menu_admin"))
    banner = get_image('welcome_banner')
    if banner:
        bot.send_photo(message.chat.id, banner, caption=text, reply_markup=markup)
    else:
        bot.send_message(message.chat.id, text, reply_markup=markup)

# ═══════════════════════════════════════
# 🎯 /rip
# ═══════════════════════════════════════

@bot.message_handler(commands=['rip'])
def rip_cmd(message):
    uid = message.from_user.id
    if is_banned(uid): return
    if not get_slots(uid):
        bot.reply_to(message, "🎰✨ اول کاراکتر انتخاب کن! ✨🎰\n📌 /slots"); return
    rem = rip_cd(uid)
    if rem > 0:
        bot.reply_to(message, f"⏳✨ صبر کن! ✨⏳\n⏱ {rem} ثانیه"); return
    bot.send_message(message.chat.id, "🎯✨ انتخاب هدف ✨🎯\n\n📌 روی پیام هر کاراکتر Reply بزن + اسم Ability!")
    conn = db(); c = conn.cursor()
    c.execute("SELECT * FROM characters ORDER BY RANDOM() LIMIT 4")
    chars = c.fetchall(); conn.close()
    for ch in chars:
        caption = f"🎭✨ {ch[1]} ✨🎭\n\n🛡 دفاع: {ch[3]}\n🌀 دریبل‌دفاع: {ch[4]}\n⚔ حمله: {ch[5]}\n\n📌 Reply بزن + اسم Ability!"
        if ch[6]:
            sent = bot.send_photo(message.chat.id, ch[6], caption=caption)
        else:
            sent = bot.send_message(message.chat.id, caption)
        conn = db(); c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO character_messages (message_id,chat_id,character_id,expires_at) VALUES (?,?,?,?)",
                  (sent.message_id, message.chat.id, ch[0], time.time()+600))
        conn.commit(); conn.close()

# ═══════════════════════════════════════
# 📌 هندلر ریپلای
# ═══════════════════════════════════════

@bot.message_handler(func=lambda m: m.reply_to_message is not None)
def handle_reply(message):
    uid = message.from_user.id
    if is_banned(uid): return
    rid = message.reply_to_message.message_id
    conn = db(); c = conn.cursor()
    c.execute("SELECT character_id FROM character_messages WHERE message_id=? AND expires_at>?",
              (rid, time.time()))
    r = c.fetchone(); conn.close()
    if not r: return
    chid = r[0]
    rem = rip_cd(uid)
    if rem > 0:
        bot.reply_to(message, f"⏳ {rem} ثانیه صبر کن!"); return
    abilities = get_abilities(uid)
    if not abilities:
        bot.reply_to(message, "❌ Ability نداری! /slots"); return
    ab = find_ability(message.text, abilities)
    if not ab:
        bot.reply_to(message, "❌✨ Ability پیدا نشد! ✨❌\n📖 /abilities"); return
    cd = ab_cd(uid, ab[0])
    if cd > 0:
        bot.reply_to(message, f"⏳ {ab[2]} — {cd} ثانیه کول‌داون!"); return
    conn = db(); c = conn.cursor()
    c.execute("SELECT name,defense FROM characters WHERE id=?", (chid,))
    ch = c.fetchone(); conn.close()
    res, diff = simulate(ab[4], ch[1])
    if res == "goal":
        pts = 10 if diff > 20 else 7
        text = f"⚽✨ گل!!! ✨⚽\n\n🎭 {ch[0]}\n🎯 {ab[2]} ({ab[1]})\n💪 {ab[4]} vs 🛡 {ch[1]}\n\n🏆 +{pts}"
    else:
        pts = -5
        text = f"🧤✨ مهار! ✨🧤\n\n🎭 {ch[0]}\n🎯 {ab[2]}\n💪 {ab[4]} vs 🛡 {ch[1]}\n\n🏆 {pts}"
    conn = db(); c = conn.cursor()
    c.execute("UPDATE users SET rank_points=rank_points+? WHERE user_id=?", (pts, uid))
    if res == "goal":
        c.execute("UPDATE users SET goals=goals+1, game_goals=game_goals+1 WHERE user_id=?", (uid,))
        c.execute("SELECT game_goals FROM users WHERE user_id=?", (uid,))
        gg = c.fetchone()[0]
    else:
        c.execute("UPDATE users SET saves=saves+1 WHERE user_id=?", (uid,))
        gg = 0
    conn.commit(); conn.close()
    set_rip_cd(uid); set_ab_cd(uid, ab[0])
    if res == "goal" and gg >= MAX_GOALS:
        text += f"\n\n🎉✨ بازی تموم شد! {MAX_GOALS} گل زدی! ✨🎉"
        conn = db(); c = conn.cursor()
        c.execute("UPDATE users SET game_goals=0 WHERE user_id=?", (uid,))
        conn.commit(); conn.close()
    try:
        bot.edit_message_text(text, chat_id=message.chat.id, message_id=rid, reply_markup=None)
    except:
        bot.reply_to(message, text)

# ═══════════════════════════════════════
# 🛡 /slots
# ═══════════════════════════════════════

@bot.message_handler(commands=['slots'])
def slots_cmd(message):
    uid = message.from_user.id
    slots = get_slots(uid)
    text = "🛡✨ اسلات‌ها ✨🛡\n\n"
    for i in range(1,5):
        s = next((x for x in slots if x[0]==i), None)
        text += f"{i}️⃣ {s[2] if s else '⚪ خالی'}\n"
    abs_ = get_abilities(uid)
    if abs_:
        text += "\n📌 Abilityها:\n"
        for a in abs_: text += f"• {a[2]} ({a[1]})\n"
    markup = types.InlineKeyboardMarkup(row_width=2)
    for i in range(1,5):
        s = next((x for x in slots if x[0]==i), None)
        label = f"{i}️⃣ {s[2][:12]}" if s else f"{i}️⃣ ➕"
        markup.add(types.InlineKeyboardButton(label, callback_data=f"editslot_{i}"))
    bot.send_message(message.chat.id, text, reply_markup=markup)

# ═══════════════════════════════════════
# 🎛 Callback
# ═══════════════════════════════════════

@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    uid = call.from_user.id
    data = call.data
    if data == "menu_rip":
        bot.answer_callback_query(call.id, "🎯 /rip رو بزن!")
    elif data == "menu_slots":
        slots_cmd(call.message); bot.answer_callback_query(call.id)
    elif data == "menu_stats":
        u = get_user(uid)
        if u:
            t = f"📊✨ آمار ✨📊\n\n👤 {u[1]}\n🏆 {get_rank(u[2])} ({u[2]})\n⚽ {u[3]}\n🧤 {u[4]}"
            bot.edit_message_text(t, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
        bot.answer_callback_query(call.id)
    elif data == "menu_top":
        conn = db(); c = conn.cursor()
        c.execute("SELECT name,rank_points FROM users ORDER BY rank_points DESC LIMIT 10")
        top = c.fetchall(); conn.close()
        t = "🏆✨ لیدربورد ✨🏆\n\n"
        for i,(n,p) in enumerate(top,1):
            m = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}️⃣"
            t += f"{m} {n}: {p}\n"
        bot.edit_message_text(t, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
        bot.answer_callback_query(call.id)
    elif data == "menu_abilities":
        abs_ = get_abilities(uid)
        if not abs_:
            t = "📖✨ Ability نداری! /slots"
        else:
            t = "📖✨ Abilityهای تو ✨📖\n\n"
            for a in abs_: t += f"• {a[2]} ({a[1]}) — {a[4]}\n"
        bot.edit_message_text(t, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
        bot.answer_callback_query(call.id)
    elif data == "menu_admin" and is_owner(uid):
        show_admin(call)
    elif data.startswith("editslot_"):
        sn = int(data.split("_")[1])
        conn = db(); c = conn.cursor()
        c.execute("SELECT id,name FROM characters LIMIT 10")
        chars = c.fetchall(); conn.close()
        markup = types.InlineKeyboardMarkup(row_width=2)
        for ch in chars:
            markup.add(types.InlineKeyboardButton(ch[1], callback_data=f"setchar_{sn}_{ch[0]}"))
        markup.add(types.InlineKeyboardButton("🔙", callback_data="menu_slots"))
        bot.edit_message_text(f"🎯 انتخاب برای اسلات {sn}", chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=markup)
        bot.answer_callback_query(call.id)
    elif data.startswith("setchar_"):
        _, sn, cid = data.split("_")
        conn = db(); c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO user_slots (user_id,slot_number,character_id) VALUES (?,?,?)",
                  (uid, int(sn), int(cid)))
        conn.commit(); conn.close()
        bot.answer_callback_query(call.id, "✅ شد!")
        slots_cmd(call.message)

# ═══════════════════════════════════════
# 👑 پنل مالک
# ═══════════════════════════════════════

def show_admin(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("🖼 عکس‌ها", callback_data="adm_images"),
               types.InlineKeyboardButton("📊 آمار کلی", callback_data="adm_stats"))
    bot.edit_message_text("👑✨ پنل مالک ✨👑", chat_id=call.message.chat.id,
                          message_id=call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_"))
def adm_cb(call):
    uid = call.from_user.id
    if not is_owner(uid): return
    d = call.data
    if d == "adm_images":
        markup = types.InlineKeyboardMarkup(row_width=2)
        for k in ['welcome_banner','rank_bronze','rank_silver','rank_gold','rank_bluelock','rank_legend','event_banner','profile_default']:
            markup.add(types.InlineKeyboardButton(get_image_name(k), callback_data=f"imgset_{k}"))
        bot.edit_message_text("🖼✨ انتخاب عکس ✨🖼", chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=markup)
    elif d.startswith("imgset_"):
        key = d.replace("imgset_", "")
        admin_states[uid] = f"wait_img_{key}"
        bot.edit_message_text(f"🖼✨ {get_image_name(key)} ✨🖼\n\n📌 عکس رو بفرست!",
                              chat_id=call.message.chat.id, message_id=call.message.message_id)
    elif d == "adm_stats":
        conn = db(); c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users"); uc = c.fetchone()[0]
        c.execute("SELECT SUM(goals) FROM users"); g = c.fetchone()[0] or 0
        c.execute("SELECT SUM(saves) FROM users"); s = c.fetchone()[0] or 0
        conn.close()
        t = f"📊✨ آمار کلی ✨📊\n\n👥 {uc}\n⚽ {g}\n🧤 {s}"
        bot.edit_message_text(t, chat_id=call.message.chat.id, message_id=call.message.message_id)
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    uid = message.from_user.id
    state = admin_states.get(uid)
    if state and state.startswith("wait_img_"):
        key = state.replace("wait_img_", "")
        fid = message.photo[-1].file_id
        set_image(key, fid, uid)
        del admin_states[uid]
        bot.reply_to(message, f"✅✨ {get_image_name(key)} ست شد! ✨✅")

# ═══════════════════════════════════════
# 🚀 اجرا
# ═══════════════════════════════════════

if __name__ == "__main__":
    init_db()
    seed()
    print(f"🚀✨ Blue Lock Bot روشن شد! ✨🚀\n👑 مالک: {OWNER_ID}")
    bot.infinity_polling()
