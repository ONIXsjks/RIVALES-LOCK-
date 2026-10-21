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
    c.execute('''CREATE TABLE IF NOT EXISTS matches (
        chat_id INTEGER PRIMARY KEY, p1_id INTEGER, p2_id INTEGER, 
        p1_goals INTEGER DEFAULT 0, p2_goals INTEGER DEFAULT 0, 
        turn_id INTEGER)''')
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

# ✨ دقیقاً ۳ Ability برای هر کاراکتر (یکی شوت/دریبل، یکی دفاع/بلاک، یکی ویژه)
ABILITIES = [
    # Isagi
    ("Direct Shot","شوت مستقیم","directshot",80,20,"shot","Isagi Yoichi",0),
    ("Metavision","دید فراگیر","metavision",85,20,"defend","Isagi Yoichi",800),
    ("Protagonist Aura","هاله قهرمان","protagonist",95,20,"block","Isagi Yoichi",15000),
    # Rin
    ("Gyro Shot","شوت چرخشی","gyro",85,20,"shot","Itoshi Rin",0),
    ("Predator Eye","چشم شکارچی","predatoreye",90,20,"defend","Itoshi Rin",10000),
    ("Berserker Mode","حالت دیوانه","berserker",95,20,"block","Itoshi Rin",25000),
    # Kaiser
    ("Kaiser Impact","ضربه کایزر","kaiser",95,20,"shot","Michael Kaiser",0),
    ("Kaiser Dribble","دریبل کایزر","kdrib",90,20,"dribble","Michael Kaiser",10000),
    ("Emperor Aura","هاله امپراتور","emperor",95,20,"block","Michael Kaiser",25000),
    # Bachira
    ("Elastic Dribble","دریبل الاستیک","elastic",85,20,"dribble","Meguru Bachira",0),
    ("Flow Defense","دفاع جریان","flowdef",80,20,"defend","Meguru Bachira",9000),
    ("Monster Dribble","دریبل هیولا","monsterdrib",90,20,"dribble","Meguru Bachira",12000),
    # Nagi
    ("Trap Master","استاد تله","trap",90,20,"dribble","Seishiro Nagi",0),
    ("Nagi Shot","شوت ناگی","nagishot",85,20,"shot","Seishiro Nagi",8000),
    ("Genius Trap","تله نابغه","geniustrap",95,20,"block","Seishiro Nagi",20000),
    # Barou
    ("Barou Charge","حمله بارو","barou",90,20,"shot","Barou Shoei",0),
    ("King Dribble","دریبل پادشاه","kingdrib",85,20,"dribble","Barou Shoei",10000),
    ("King Mode","حالت پادشاه","kingmode",95,20,"block","Barou Shoei",22000),
    # Chigiri
    ("Speed Dribble","دریبل سرعتی","speed",90,20,"dribble","Chigiri",0),
    ("Chigiri Defense","دفاع چیگیری","chigiridef",75,20,"defend","Chigiri",7000),
    ("Red Panther","پلنگ سرخ","redpanther",95,20,"block","Chigiri",20000),
    # Shido
    ("Bicycle Kick","قیچی برگردون","bicycle",85,20,"shot","Ryusei Shido",0),
    ("Shido Dribble","دریبل شیدو","shidodrib",85,20,"dribble","Ryusei Shido",9000),
    ("Berserker Rage","خشم دیوانه","rage",95,20,"block","Ryusei Shido",25000),
    # Sae
    ("Magician Dribble","دریبل جادوگر","magician",90,20,"dribble","Itoshi Sae",0),
    ("Sae Defense","دفاع سائه","saedef",85,20,"defend","Itoshi Sae",9000),
    ("Genius Mode","حالت نابغه","genius",95,20,"block","Itoshi Sae",25000),
    # Aiku
    ("Slide Tackle","تکل سرشی","slide",85,20,"defend","Oliver Aiku",0),
    ("Aiku Header","ضربه سر آیکو","aikuheader",85,20,"shot","Oliver Aiku",9000),
    ("Captain Mode","حالت کاپیتان","captain",90,20,"block","Oliver Aiku",20000),
    # Yukimiya
    ("Sniper Shot","شوت تک‌تیرانداز","sniper",85,20,"shot","Kenyu Yukimiya",0),
    ("Gyro Dribble","دریبل چرخشی","gyrodrib",80,20,"dribble","Kenyu Yukimiya",7000),
    ("Yukimiya Defense","دفاع یوکیمیا","yukidef",80,20,"defend","Kenyu Yukimiya",8000),
    # Aryu
    ("Iron Wall","دیوار آهنی","ironwall",90,20,"defend","Jyubei Aryu",0),
    ("Aryu Shot","شوت آریو","aryushot",75,20,"shot","Jyubei Aryu",6000),
    ("Aryu Block","بلاک آریو","aryublock",90,20,"block","Jyubei Aryu",9000),
    # Lorenzo
    ("Aura Defense","دفاع هاله‌ای","aura",90,20,"defend","Don Lorenzo",0),
    ("Lorenzo Dribble","دریبل لورنزو","lordrib",85,20,"dribble","Don Lorenzo",8000),
    ("Monster Mode","حالت هیولا","monster",95,20,"block","Don Lorenzo",15000),
    # Noa
    ("God Mode","حالت خدا","godmode",100,20,"block","Noel Noa",0),
    ("Noa Shot","شوت نوآ","noashot",95,20,"shot","Noel Noa",15000),
    ("Perfect Vision","دید کامل","perfectvision",95,20,"defend","Noel Noa",12000),
    # Lavinho
    ("Samba Dribble","دریبل سامبا","samba",95,20,"dribble","Lavinho",0),
    ("Lavinho Shot","شوت لاوینیو","lavishot",90,20,"shot","Lavinho",10000),
    ("Lavinho Defense","دفاع لاوینیو","lavidef",85,20,"defend","Lavinho",9000),
    # Loki
    ("God Speed","سرعت خدا","godspeed",95,20,"dribble","Julian Loki",0),
    ("Loki Shot","شوت لوکی","lokishot",85,20,"shot","Julian Loki",9000),
    ("Loki Defense","دفاع لوکی","lokidef",80,20,"defend","Julian Loki",8000),
    # Ness
    ("Ness Pass","پاس نس","ness",75,20,"dribble","Alexis Ness",0),
    ("Ness Shot","شوت نس","nessshot",80,20,"shot","Alexis Ness",7000),
    ("Ness Defense","دفاع نس","nessdef",80,20,"defend","Alexis Ness",7000),
    # Hiori
    ("Hiori Pass","پاس هیوری","hiori",80,20,"dribble","Yo Hiori",0),
    ("Hiori Shot","شوت هیوری","hiorishot",80,20,"shot","Yo Hiori",7000),
    ("Hiori Defense","دفاع هیوری","hioridef",80,20,"defend","Yo Hiori",7000),
    # Karasu
    ("Karasu Defense","دفاع کاراسو","karasu",85,20,"defend","Tabito Karasu",0),
    ("Karasu Dribble","دریبل کاراسو","karasudrib",80,20,"dribble","Tabito Karasu",7000),
    ("Karasu Shot","شوت کاراسو","karasushot",75,20,"shot","Tabito Karasu",6000),
    # Niko
    ("Block","بلاک","block",75,20,"block","Ikki Niko",0),
    ("Niko Defense","دفاع نیکو","nikodef",80,20,"defend","Ikki Niko",7000),
    ("Niko Dribble","دریبل نیکو","nikodrib",75,20,"dribble","Ikki Niko",6000),
    # Otoya
    ("Otoya Stealth","مخفی‌کاری اوتویا","otoya",80,20,"dribble","Eita Otoya",0),
    ("Otoya Shot","شوت اوتویا","otoyashot",80,20,"shot","Eita Otoya",7000),
    ("Ninja Defense","دفاع نینجا","ninjadef",80,20,"defend","Eita Otoya",8000),
    # Kurona
    ("Kurona Dash","جهش کورونا","kurona",80,20,"dribble","Ranze Kurona",0),
    ("Kurona Defense","دفاع کورونا","koronadef",85,20,"defend","Ranze Kurona",8000),
    ("Kurona Pass","پاس کورونا","koronapass",80,20,"dribble","Ranze Kurona",7000),
    # Gagamaru
    ("Gagamaru Save","سیو گاگامارو","gagamaru",90,20,"block","Gin Gagamaru",0),
    ("Wild Save","سیو وحشی","wildsave",95,20,"block","Gin Gagamaru",15000),
    ("Gagamaru Defense","دفاع گاگامارو","gagadef",95,20,"defend","Gin Gagamaru",10000),
    # Sendo
    ("Sendo Strike","ضربه سندو","sendo",85,20,"shot","Sendo",0),
    ("Sendo Dribble","دریبل سندو","sendodrib",75,20,"dribble","Sendo",6000),
    ("Sendo Defense","دفاع سندو","sendodef",80,20,"defend","Sendo",7000),
    # Zantetsu
    ("Zantetsu Dash","جهش زانتتسو","zantetsu",80,20,"dribble","Zantetsu",0),
    ("Zantetsu Shot","شوت زانتتسو","zantetsushot",75,20,"shot","Zantetsu",6000),
    ("Zantetsu Defense","دفاع زانتتسو","zantetsudef",75,20,"defend","Zantetsu",6000),
    # Nanase
    ("Nanase Stamina","استقامت ناناسه","nanase",80,20,"defend","Nanase",0),
    ("Nanase Dribble","دریبل ناناسه","nanasedrib",75,20,"dribble","Nanase",6000),
    ("Nanase Defense","دفاع ناناسه","nanasedef",80,20,"defend","Nanase",7000),
    # Igaguri
    ("Igaguri Foul","خطای ایگاگوری","igaguri",60,20,"defend","Igaguri",0),
    ("Igaguri Dive","شیرجه ایگاگوری","dive",55,20,"block","Igaguri",4000),
    ("Igaguri Dribble","دریبل ایگاگوری","igaguridrib",60,20,"dribble","Igaguri",5000),
    # Kusu
    ("Kusu Control","کنترل کوسو","kusu",75,20,"dribble","Kusu",0),
    ("Kusu Shot","شوت کوسو","kusushot",75,20,"shot","Kusu",6000),
    ("Kusu Defense","دفاع کوسو","kusudef",75,20,"defend","Kusu",6000),
    # Agi
    ("Agi Control","کنترل آگی","agi",75,20,"dribble","Agi",0),
    ("Agi Shot","شوت آگی","agishot",75,20,"shot","Agi",6000),
    ("Agi Defense","دفاع آگی","agidef",75,20,"defend","Agi",6000),
    # Reo
    ("Mikage Copy","کپی میکاگه","mikage",85,20,"block","Reo Mikage",0),
    ("Reo Dribble","دریبل رئو","reodrib",80,20,"dribble","Reo Mikage",7000),
    ("Reo Defense","دفاع رئو","reodef",80,20,"defend","Reo Mikage",8000),
    # Kiyora
    ("Kiyora Vision","دید کیورا","kiyora",80,20,"defend","Jin Kiyora",0),
    ("Kiyora Dribble","دریبل کیورا","kiyoradrib",80,20,"dribble","Jin Kiyora",7000),
    ("Kiyora Shot","شوت کیورا","kiyorashot",75,20,"shot","Jin Kiyora",6000),
    # Onazi
    ("Onazi Shot","شوت اونازی","onazi",75,20,"shot","Onazi",0),
    ("Onazi Dribble","دریبل اونازی","onazidrib",75,20,"dribble","Onazi",6000),
    ("Onazi Defense","دفاع اونازی","onazidef",75,20,"defend","Onazi",6000),
    # Knight
    ("Knight Shield","سپر نایت","knight",80,20,"defend","Teddy Knight",0),
    ("Knight Shot","شوت نایت","knightshot",75,20,"shot","Teddy Knight",6000),
    ("Knight Tackle","تکل نایت","knighttackle",85,20,"defend","Teddy Knight",8000),
    # Chevalier
    ("Chevalier Step","قدم شوالیه","chevalier",80,20,"dribble","Charles Chevalier",0),
    ("Chevalier Shot","شوت شوالیه","chevshot",75,20,"shot","Charles Chevalier",6000),
    ("Chevalier Defense","دفاع شوالیه","chevdef",80,20,"defend","Charles Chevalier",7000),
    # Snuffy
    ("Snuffy Snake","مار اسنافی","snuffy",85,20,"shot","Mark Snuffy",0),
    ("Snuffy Dribble","دریبل اسنافی","snuffydrib",80,20,"dribble","Mark Snuffy",7000),
    ("Snuffy Defense","دفاع اسنافی","snuffydef",85,20,"defend","Mark Snuffy",8000),
    # Cavascoz
    ("Cavascoz Magic","جادوی کاواسکوز","cavascoz",85,20,"dribble","Pablo Cavascoz",0),
    ("Cavascoz Shot","شوت کاواسکوز","cavshot",80,20,"shot","Pablo Cavascoz",7000),
    ("Cavascoz Defense","دفاع کاواسکوز","cavdef",85,20,"defend","Pablo Cavascoz",8000),
    # Silva
    ("Silva Wall","دیوار سیلوا","silva",90,20,"defend","Dada Silva",0),
    ("Silva Shot","شوت سیلوا","silvashot",85,20,"shot","Dada Silva",8000),
    ("Silva Power","قدرت سیلوا","silvapower",90,20,"block","Dada Silva",9000),
    # Blake
    ("Blake Speed","سرعت بلیک","blake",85,20,"dribble","Blake",0),
    ("Blake Shot","شوت بلیک","blakeshot",80,20,"shot","Blake",7000),
    ("Blake Defense","دفاع بلیک","blakedef",80,20,"defend","Blake",7000),
    # Prince
    ("Prince Power","قدرت پرینس","prince",90,20,"shot","Chris Prince",0),
    ("Prince Defense","دفاع پرینس","princedef",90,20,"defend","Chris Prince",9000),
    ("Perfect Body","بدن کامل","perfectbody",95,20,"block","Chris Prince",15000),
    # Luna
    ("Luna Shot","شوت لونا","luna",90,20,"shot","Leonardo Luna",0),
    ("Moon Dribble","دریبل ماه","moon",85,20,"dribble","Leonardo Luna",8000),
    ("Night Defense","دفاع شب","nightdef",85,20,"defend","Leonardo Luna",8000),
    # Iglesias
    ("Bunny Hop","پرش خرگوشی","bunny",80,20,"dribble","Bunny Iglesias",0),
    ("Bunny Shot","شوت خرگوشی","bunnyshot",75,20,"shot","Bunny Iglesias",6000),
    ("Bunny Defense","دفاع خرگوشی","bunnydef",80,20,"defend","Bunny Iglesias",7000),
    # Lockhart
    ("Lock Defense","دفاع قفل","lock",85,20,"defend","Lockhart",0),
    ("Lock Dribble","دریبل قفل","lockdrib",75,20,"dribble","Lockhart",6000),
    ("Lock Shot","شوت قفل","lockshot",75,20,"shot","Lockhart",6000),
    # Hugo
    ("Hugo Defense","دفاع هوگو","hugo",80,20,"defend","Vivian Hugo",0),
    ("Wall Defense","دفاع دیواری","walldef",85,20,"defend","Vivian Hugo",8000),
    ("Hugo Shot","شوت هوگو","hugoshot",75,20,"shot","Vivian Hugo",6000),
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