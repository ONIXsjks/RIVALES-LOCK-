import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "/app/data/blue_lock.db")

def db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = db(); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, name TEXT, rank_points INTEGER DEFAULT 0, coins INTEGER DEFAULT 0,
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
        aliases TEXT, power INTEGER, cooldown INTEGER DEFAULT 20, category TEXT, owner TEXT, price INTEGER DEFAULT 50)''')
    c.execute('''CREATE TABLE IF NOT EXISTS character_abilities (
        character_id INTEGER, ability_id INTEGER, PRIMARY KEY (character_id, ability_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_abilities (
        user_id INTEGER, ability_id INTEGER, PRIMARY KEY (user_id, ability_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS ability_cooldowns (
        user_id INTEGER, ability_id INTEGER, last_used INTEGER, PRIMARY KEY (user_id, ability_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS bot_images (
        key TEXT PRIMARY KEY, file_id TEXT, updated_at INTEGER, updated_by INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT, attacker_id INTEGER, target_id INTEGER, 
        ability_name TEXT, result TEXT, points INTEGER, timestamp INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, event_type TEXT, target_id INTEGER, 
        multiplier REAL, ends_at INTEGER, is_active INTEGER DEFAULT 1)''')
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

# اضافه شدن Abilityهای بیشتر از مانگا (قیمت زیر 100000)
ABILITIES = [
    ("Direct Shot","شوت مستقیم","directshot",80,20,"shot","Isagi Yoichi",0),
    ("Metavision","دید فراگیر","metavision",85,20,"defend","Isagi Yoichi",800),
    ("Protagonist Aura","هاله قهرمان","protagonist",95,20,"special","Isagi Yoichi",15000),
    ("Tadaima","تادایما","tadaima",85,20,"shot","Isagi Yoichi",5000),
    
    ("Gyro Shot","شوت چرخشی","gyro",85,20,"shot","Itoshi Rin",0),
    ("Predator Eye","چشم شکارچی","predatoreye",90,20,"defend","Itoshi Rin",10000),
    ("Berserker Mode","حالت دیوانه","berserker",95,20,"special","Itoshi Rin",25000),
    ("Puppet Master","استاد عروسک","puppet",90,20,"dribble","Itoshi Rin",12000),
    
    ("Kaiser Impact","ضربه کایزر","kaiser",95,20,"shot","Michael Kaiser",0),
    ("Emperor Aura","هاله امپراتور","emperor",95,20,"special","Michael Kaiser",25000),
    ("Kaiser Defense","دفاع کایزر","kdef",85,20,"defend","Michael Kaiser",8000),
    ("Kaiser Dribble","دریبل کایزر","kdrib",90,20,"dribble","Michael Kaiser",10000),

    ("Elastic Dribble","دریبل الاستیک","elastic",85,20,"dribble","Meguru Bachira",0),
    ("Flow Dribble","دریبل جریان","flowdribble",85,20,"dribble","Meguru Bachira",8000),
    ("Flow Defense","دفاع جریان","flowdef",80,20,"defend","Meguru Bachira",9000),
    ("Monster Dribble","دریبل هیولا","monsterdrib",90,20,"dribble","Meguru Bachira",12000),

    ("Trap Master","استاد تله","trap",90,20,"dribble","Seishiro Nagi",0),
    ("Nagi Shot","شوت ناگی","nagishot",85,20,"shot","Seishiro Nagi",8000),
    ("Nagi Defense","دفاع ناگی","nagidef",75,20,"defend","Seishiro Nagi",7000),
    ("Genius Trap","تله نابغه","geniustrap",95,20,"special","Seishiro Nagi",20000),

    ("Barou Charge","حمله بارو","barou",90,20,"shot","Barou Shoei",0),
    ("King Mode","حالت پادشاه","kingmode",95,20,"special","Barou Shoei",22000),
    ("Barou Defense","دفاع بارو","baroudef",80,20,"defend","Barou Shoei",8000),
    ("King Dribble","دریبل پادشاه","kingdrib",85,20,"dribble","Barou Shoei",10000),

    ("Speed Dribble","دریبل سرعتی","speed",90,20,"dribble","Chigiri",0),
    ("Red Panther","پلنگ سرخ","redpanther",95,20,"special","Chigiri",20000),
    ("Chigiri Defense","دفاع چیگیری","chigiridef",75,20,"defend","Chigiri",7000),
    ("Mach Cut","برش ماخ","machcut",85,20,"shot","Chigiri",9000),

    ("Bicycle Kick","قیچی برگردون","bicycle",85,20,"shot","Ryusei Shido",0),
    ("Berserker Rage","خشم دیوانه","rage",95,20,"special","Ryusei Shido",25000),
    ("Wild Defense","دفاع وحشی","wilddef",80,20,"defend","Ryusei Shido",8000),
    ("Shido Dribble","دریبل شیدو","shidodrib",85,20,"dribble","Ryusei Shido",9000),

    ("Magician Dribble","دریبل جادوگر","magician",90,20,"dribble","Itoshi Sae",0),
    ("Sae Shot","شوت سائه","saeshot",85,20,"shot","Itoshi Sae",8000),
    ("Sae Defense","دفاع سائه","saedef",85,20,"defend","Itoshi Sae",9000),
    ("Genius Mode","حالت نابغه","genius",95,20,"special","Itoshi Sae",25000),

    ("Slide Tackle","تکل سرشی","slide",85,20,"defend","Oliver Aiku",0),
    ("Captain Mode","حالت کاپیتان","captain",90,20,"special","Oliver Aiku",20000),
    ("Aiku Defense","دفاع آیکو","aikudef",90,20,"defend","Oliver Aiku",10000),
    ("Aiku Header","ضربه سر آیکو","aikuheader",85,20,"shot","Oliver Aiku",9000),
    
    # ... (بقیه کاراکترها هم به همین شکل Ability اضافه میشه، برای جلوگیری از طولانی شدن، فقط چند نمونه)
]

def seed():
    conn = db(); c = conn.cursor()
    c.execute("DELETE FROM character_abilities")
    
    for ch in CHARACTERS:
        try: c.execute("INSERT INTO characters (name,tier,defense,dribble_defense,attack) VALUES (?,?,?,?,?)", ch)
        except: pass
    for ab in ABILITIES:
        try: c.execute("INSERT INTO abilities (name_en,name_fa,aliases,power,cooldown,category,owner,price) VALUES (?,?,?,?,?,?,?,?)", ab)
        except: pass
    
    c.execute("INSERT OR IGNORE INTO character_abilities (character_id, ability_id) SELECT c.id, a.id FROM characters c, abilities a WHERE c.name = a.owner")
    conn.commit(); conn.close()