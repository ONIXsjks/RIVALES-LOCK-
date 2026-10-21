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
    c.execute('''CREATE TABLE IF NOT EXISTS bot_images (
        key TEXT PRIMARY KEY, file_id TEXT, updated_at INTEGER, updated_by INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT, attacker_id INTEGER, target_id INTEGER, 
        ability_name TEXT, result TEXT, points INTEGER, timestamp INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, reward_multiplier REAL DEFAULT 1.0, 
        is_active INTEGER DEFAULT 1)''')
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
    ("Direct Shot","شوت مستقیم","directshot",80,20,"shot","Isagi Yoichi"),
    ("Gyro Shot","شوت چرخشی","gyro",85,20,"shot","Itoshi Rin"),
    ("Kaiser Impact","ضربه کایزر","kaiser",95,20,"shot","Michael Kaiser"),
    ("Bicycle Kick","قیچی برگردون","bicycle",85,20,"shot","Ryusei Shido"),
    ("Barou Charge","حمله بارو","barou",90,20,"shot","Barou Shoei"),
    ("Sniper Shot","شوت تک‌تیرانداز","sniper",85,20,"shot","Kenyu Yukimiya"),
    ("Elastic Dribble","دریبل الاستیک","elastic",85,20,"dribble","Meguru Bachira"),
    ("Speed Dribble","دریبل سرعتی","speed",90,20,"dribble","Chigiri"),
    ("God Speed","سرعت خدا","godspeed",95,20,"dribble","Julian Loki"),
    ("Magician Dribble","دریبل جادوگر","magician",90,20,"dribble","Itoshi Sae"),
    ("Metavision","دید فراگیر","metavision",85,20,"defend","Isagi Yoichi"),
    ("Predator Eye","چشم شکارچی","predatoreye",90,20,"defend","Itoshi Rin"),
    ("Iron Wall","دیوار آهنی","ironwall",90,20,"defend","Jyubei Aryu"),
    ("Aura Defense","دفاع هاله‌ای","aura",90,20,"defend","Don Lorenzo"),
    ("Flow","جریان","flow",90,20,"special","Meguru Bachira"),
    ("Protagonist Aura","هاله قهرمان","protagonist",95,20,"special","Isagi Yoichi"),
    ("Emperor Aura","هاله امپراتور","emperor",95,20,"special","Michael Kaiser"),
    ("God Mode","حالت خدا","godmode",100,20,"special","Noel Noa"),
    ("Berserker Mode","حالت دیوانه","berserker",95,20,"special","Ryusei Shido"),
    ("Trap Master","استاد تله","trap",85,20,"dribble","Seishiro Nagi"),
    ("Karasu Defense","دفاع کاراسو","karasu",80,20,"defend","Tabito Karasu"),
    ("Mikage Copy","کپی میکاگه","mikage",85,20,"special","Reo Mikage"),
    ("Aiku Tackle","تکل آیکو","aiku",85,20,"defend","Oliver Aiku"),
    ("Kiyora Vision","دید کیورا","kiyora",80,20,"defend","Jin Kiyora"),
    ("Hiori Pass","پاس هیوری","hiori",80,20,"dribble","Yo Hiori"),
    ("Ness Pass","پاس نس","ness",75,20,"dribble","Alexis Ness"),
    ("Sendo Strike","ضربه سندو","sendo",85,20,"shot","Sendo"),
    ("Otoya Stealth","مخفی‌کاری اوتویا","otoya",80,20,"dribble","Eita Otoya"),
    ("Kurona Dash","جهش کورونا","kurona",80,20,"dribble","Ranze Kurona"),
    ("Gagamaru Save","سیو گاگامارو","gagamaru",90,20,"defend","Gin Gagamaru"),
    ("Zantetsu Dash","جهش زانتتسو","zantetsu",75,20,"dribble","Zantetsu"),
    ("Nanase Stamina","استقامت ناناسه","nanase",75,20,"defend","Nanase"),
    ("Igaguri Foul","خطای ایگاگوری","igaguri",60,20,"defend","Igaguri"),
    ("Kusu Control","کنترل کوسو","kusu",75,20,"dribble","Kusu"),
    ("Agi Control","کنترل آگی","agi",75,20,"dribble","Agi"),
    ("Onazi Shot","شوت اونازی","onazi",75,20,"shot","Onazi"),
    ("Knight Shield","سپر نایت","knight",80,20,"defend","Teddy Knight"),
    ("Chevalier Step","قدم شوالیه","chevalier",80,20,"dribble","Charles Chevalier"),
    ("Lavinho Dance","رقص لاوینیو","lavinho",95,20,"dribble","Lavinho"),
    ("Luna Shot","شوت لونا","luna",90,20,"shot","Leonardo Luna"),
    ("Prince Power","قدرت پرینس","prince",90,20,"shot","Chris Prince"),
    ("Snuffy Snake","مار اسنافی","snuffy",85,20,"shot","Mark Snuffy"),
    ("Cavascoz Magic","جادوی کاواسکوز","cavascoz",85,20,"dribble","Pablo Cavascoz"),
    ("Silva Wall","دیوار سیلوا","silva",90,20,"defend","Dada Silva"),
    ("Blake Speed","سرعت بلیک","blake",85,20,"dribble","Blake"),
    ("Lockhart Lock","قفل لاکهارت","lockhart",85,20,"defend","Lockhart"),
    ("Hugo Defense","دفاع هوگو","hugo",80,20,"defend","Vivian Hugo"),
]

def seed():
    conn = db(); c = conn.cursor()
    for ch in CHARACTERS:
        try: c.execute("INSERT INTO characters (name,tier,defense,dribble_defense,attack) VALUES (?,?,?,?,?)", ch)
        except: pass
    for ab in ABILITIES:
        try: c.execute("INSERT INTO abilities (name_en,name_fa,aliases,power,cooldown,category,owner) VALUES (?,?,?,?,?,?,?)", ab)
        except: pass
    
    c.execute("INSERT OR IGNORE INTO character_abilities (character_id, ability_id) SELECT c.id, a.id FROM characters c, abilities a WHERE c.name = a.owner")
    c.execute('''INSERT OR IGNORE INTO character_abilities (character_id, ability_id)
                 SELECT c.id, a.id FROM characters c, abilities a 
                 WHERE c.id NOT IN (SELECT character_id FROM character_abilities) 
                 AND a.category IN ('shot', 'dribble', 'defend') GROUP BY c.id HAVING COUNT(a.id) <= 2''')
    conn.commit(); conn.close()