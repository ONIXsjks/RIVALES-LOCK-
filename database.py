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
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, tier TEXT, role TEXT,
        defense INTEGER, dribble_defense INTEGER, attack INTEGER, photo_file_id TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS abilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name_en TEXT UNIQUE, name_fa TEXT,
        aliases TEXT, power INTEGER, cooldown INTEGER DEFAULT 20, category TEXT, owner TEXT, price INTEGER DEFAULT 50)''')
    c.execute('''CREATE TABLE IF NOT EXISTS character_abilities (
        character_id INTEGER, ability_id INTEGER, PRIMARY KEY (character_id, ability_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS ability_cooldowns (
        user_id INTEGER, ability_id INTEGER, last_used INTEGER, PRIMARY KEY (user_id, ability_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS bot_images (
        key TEXT PRIMARY KEY, file_id TEXT, updated_at INTEGER, updated_by INTEGER)''')
    conn.commit(); conn.close()

# 📋 کاراکترها با پست (FW, MF, DF, GK)
CHARACTERS = [
    ("Noel Noa","master","FW",95,90,95),("Lavinho","master","FW",85,95,90),("Leonardo Luna","master","FW",80,85,90),
    ("Chris Prince","master","FW",90,80,85),("Mark Snuffy","master","FW",85,75,80),("Pablo Cavascoz","master","MF",80,85,85),
    ("Julian Loki","master","FW",75,95,85),("Dada Silva","master","DF",85,80,75),("Blake","master","FW",80,75,80),
    ("Bunny Iglesias","world_class","FW",75,70,75),("Lockhart","world_class","FW",70,65,70),("Itoshi Sae","world_class","MF",85,90,85),
    ("Vivian Hugo","world_class","MF",70,75,70),("Don Lorenzo","world_class","DF",85,80,75),("Michael Kaiser","world_class","FW",80,85,90),
    ("Teddy Knight","world_class","MF",70,70,75),("Charles Chevalier","world_class","MF",75,80,75),("Itoshi Rin","world_class","FW",90,85,90),
    ("Meguru Bachira","world_class","MF",65,95,80),("Tabito Karasu","world_class","DF",80,75,75),("Ikki Niko","world_class","DF",75,70,65),
    ("Reo Mikage","world_class","MF",80,85,75),("Kenyu Yukimiya","world_class","FW",70,85,75),("Ryusei Shido","world_class","FW",75,80,90),
    ("Barou Shoei","world_class","FW",70,75,95),("Alexis Ness","world_class","MF",75,75,70),("Jin Kiyora","world_class","DF",80,75,70),
    ("Onazi","world_class","FW",70,65,75),("Seishiro Nagi","world_class","FW",65,85,90),("Oliver Aiku","world_class","DF",90,80,70),
    ("Agi","world_class","FW",65,70,75),("Ranze Kurona","world_class","MF",70,80,65),("Eita Otoya","world_class","FW",65,85,75),
    ("Kusu","world_class","MF",70,70,70),("Jyubei Aryu","world_class","DF",85,65,70),("Yo Hiori","world_class","MF",65,75,70),
    ("Sendo","world_class","FW",75,65,80),("Isagi Yoichi","world_class","MF",75,70,85),("Chigiri","world_class","FW",65,90,80),
    ("Igaguri","world_class","DF",60,55,50),("Gin Gagamaru","world_class","GK",85,70,65),("Zantetsu","world_class","FW",75,65,70),
    ("Nanase","world_class","DF",70,70,65),("Fukaku","world_class","GK",80,60,60),
]

# ✨ Abilityها (۳ تا برای هر کاراکتر بر اساس پست)
ABILITIES = [
    # FW (مهاجم‌ها)
    ("Direct Shot","شوت مستقیم","directshot",80,20,"shot","Isagi Yoichi",0),
    ("Metavision","دید فراگیر","metavision",85,20,"dribble","Isagi Yoichi",800),
    ("Protagonist Aura","هاله قهرمان","protagonist",95,20,"mode","Isagi Yoichi",15000),
    ("Gyro Shot","شوت چرخشی","gyro",85,20,"shot","Itoshi Rin",0),
    ("Predator Eye","چشم شکارچی","predatoreye",90,20,"dribble","Itoshi Rin",10000),
    ("Berserker Mode","حالت دیوانه","berserker",95,20,"mode","Itoshi Rin",25000),
    ("Kaiser Impact","ضربه کایزر","kaiser",95,20,"shot","Michael Kaiser",0),
    ("Kaiser Dribble","دریبل کایزر","kdrib",90,20,"dribble","Michael Kaiser",10000),
    ("Emperor Aura","هاله امپراتور","emperor",95,20,"mode","Michael Kaiser",25000),
    ("Trap Master","استاد تله","trap",90,20,"dribble","Seishiro Nagi",0),
    ("Nagi Shot","شوت ناگی","nagishot",85,20,"shot","Seishiro Nagi",8000),
    ("Genius Trap","تله نابغه","geniustrap",95,20,"mode","Seishiro Nagi",20000),
    ("Barou Charge","حمله بارو","barou",90,20,"shot","Barou Shoei",0),
    ("King Dribble","دریبل پادشاه","kingdrib",85,20,"dribble","Barou Shoei",10000),
    ("King Mode","حالت پادشاه","kingmode",95,20,"mode","Barou Shoei",22000),
    ("Speed Dribble","دریبل سرعتی","speed",90,20,"dribble","Chigiri",0),
    ("Chigiri Shot","شوت چیگیری","chigirishot",85,20,"shot","Chigiri",9000),
    ("Red Panther","پلنگ سرخ","redpanther",95,20,"mode","Chigiri",20000),
    ("Bicycle Kick","قیچی برگردون","bicycle",85,20,"shot","Ryusei Shido",0),
    ("Shido Dribble","دریبل شیدو","shidodrib",85,20,"dribble","Ryusei Shido",9000),
    ("Berserker Rage","خشم دیوانه","rage",95,20,"mode","Ryusei Shido",25000),
    ("God Speed","سرعت خدا","godspeed",95,20,"dribble","Julian Loki",0),
    ("Loki Shot","شوت لوکی","lokishot",85,20,"shot","Julian Loki",9000),
    ("Speed Mode","حالت سرعت","speedmode",95,20,"mode","Julian Loki",22000),
    ("Sniper Shot","شوت تک‌تیرانداز","sniper",85,20,"shot","Kenyu Yukimiya",0),
    ("Gyro Dribble","دریبل چرخشی","gyrodrib",80,20,"dribble","Kenyu Yukimiya",7000),
    ("Yukimiya Mode","حالت یوکیمیا","yukimode",90,20,"mode","Kenyu Yukimiya",15000),
    ("Lavinho Shot","شوت لاوینیو","lavishot",90,20,"shot","Lavinho",0),
    ("Samba Dribble","دریبل سامبا","samba",95,20,"dribble","Lavinho",12000),
    ("Dance Mode","حالت رقص","dance",95,20,"mode","Lavinho",25000),
    ("Noa Shot","شوت نوآ","noashot",95,20,"shot","Noel Noa",0),
    ("Noa Dribble","دریبل نوآ","noadrib",95,20,"dribble","Noel Noa",15000),
    ("God Mode","حالت خدا","godmode",100,20,"mode","Noel Noa",30000),
    ("Prince Power","قدرت پرینس","prince",90,20,"shot","Chris Prince",0),
    ("Prince Dribble","دریبل پرینس","princedrib",85,20,"dribble","Chris Prince",8000),
    ("King Mode","حالت پادشاه","kingmode2",95,20,"mode","Chris Prince",20000),
    ("Luna Shot","شوت لونا","luna",90,20,"shot","Leonardo Luna",0),
    ("Moon Dribble","دریبل ماه","moon",85,20,"dribble","Leonardo Luna",8000),
    ("Night Mode","حالت شب","nightmode",95,20,"mode","Leonardo Luna",20000),
    ("Blake Shot","شوت بلیک","blakeshot",80,20,"shot","Blake",0),
    ("Blake Speed","سرعت بلیک","blakespeed",85,20,"dribble","Blake",7000),
    ("Blake Mode","حالت بلیک","blakemode",90,20,"mode","Blake",15000),
    ("Bunny Shot","شوت خرگوشی","bunnyshot",75,20,"shot","Bunny Iglesias",0),
    ("Bunny Hop","پرش خرگوشی","bunny",80,20,"dribble","Bunny Iglesias",6000),
    ("Bunny Mode","حالت خرگوشی","bunnymode",85,20,"mode","Bunny Iglesias",12000),
    ("Lock Shot","شوت قفل","lockshot",75,20,"shot","Lockhart",0),
    ("Lock Dribble","دریبل قفل","lockdrib",75,20,"dribble","Lockhart",6000),
    ("Lock Mode","حالت قفل","lockmode",85,20,"mode","Lockhart",12000),
    ("Sendo Strike","ضربه سندو","sendo",85,20,"shot","Sendo",0),
    ("Sendo Dribble","دریبل سندو","sendodrib",75,20,"dribble","Sendo",6000),
    ("Sendo Mode","حالت سندو","sendomode",90,20,"mode","Sendo",15000),
    ("Onazi Shot","شوت اونازی","onazi",75,20,"shot","Onazi",0),
    ("Onazi Dribble","دریبل اونازی","onazidrib",75,20,"dribble","Onazi",6000),
    ("Onazi Mode","حالت اونازی","onazimode",85,20,"mode","Onazi",12000),
    ("Agi Shot","شوت آگی","agishot",75,20,"shot","Agi",0),
    ("Agi Control","کنترل آگی","agi",75,20,"dribble","Agi",6000),
    ("Agi Mode","حالت آگی","agimode",85,20,"mode","Agi",12000),
    ("Otoya Shot","شوت اوتویا","otoyashot",80,20,"shot","Eita Otoya",0),
    ("Otoya Stealth","مخفی‌کاری اوتویا","otoya",80,20,"dribble","Eita Otoya",7000),
    ("Ninja Mode","حالت نینجا","ninja",85,20,"mode","Eita Otoya",12000),
    ("Zantetsu Shot","شوت زانتتسو","zantetsushot",75,20,"shot","Zantetsu",0),
    ("Zantetsu Dash","جهش زانتتسو","zantetsu",80,20,"dribble","Zantetsu",6000),
    ("Zantetsu Mode","حالت زانتتسو","zantetsumode",85,20,"mode","Zantetsu",12000),
    
    # MF (هافبک‌ها)
    ("Sae Shot","شوت سائه","saeshot",85,20,"shot","Itoshi Sae",0),
    ("Magician Dribble","دریبل جادوگر","magician",90,20,"dribble","Itoshi Sae",10000),
    ("Sae Pass","پاس سائه","saepass",90,20,"pass","Itoshi Sae",9000),
    ("Ness Shot","شوت نس","nessshot",80,20,"shot","Alexis Ness",0),
    ("Ness Pass","پاس نس","ness",75,20,"pass","Alexis Ness",7000),
    ("Ness Dribble","دریبل نس","nessdrib",80,20,"dribble","Alexis Ness",7000),
    ("Hiori Shot","شوت هیوری","hiorishot",80,20,"shot","Yo Hiori",0),
    ("Hiori Pass","پاس هیوری","hiori",80,20,"pass","Yo Hiori",7000),
    ("Hiori Dribble","دریبل هیوری","hioridrib",80,20,"dribble","Yo Hiori",7000),
    ("Karasu Shot","شوت کاراسو","karasushot",75,20,"shot","Tabito Karasu",0),
    ("Karasu Pass","پاس کاراسو","karasupass",85,20,"pass","Tabito Karasu",8000),
    ("Karasu Dribble","دریبل کاراسو","karasudrib",80,20,"dribble","Tabito Karasu",7000),
    ("Reo Shot","شوت رئو","reoshot",80,20,"shot","Reo Mikage",0),
    ("Reo Dribble","دریبل رئو","reodrib",80,20,"dribble","Reo Mikage",7000),
    ("Reo Pass","پاس رئو","reopass",80,20,"pass","Reo Mikage",7000),
    ("Kiyora Shot","شوت کیورا","kiyorashot",75,20,"shot","Jin Kiyora",0),
    ("Kiyora Dribble","دریبل کیورا","kiyoradrib",80,20,"dribble","Jin Kiyora",7000),
    ("Kiyora Pass","پاس کیورا","kiyorapass",80,20,"pass","Jin Kiyora",7000),
    ("Kusu Shot","شوت کوسو","kusushot",75,20,"shot","Kusu",0),
    ("Kusu Dribble","دریبل کوسو","kusudrib",75,20,"dribble","Kusu",6000),
    ("Kusu Pass","پاس کوسو","kusupass",75,20,"pass","Kusu",6000),
    ("Chevalier Shot","شوت شوالیه","chevshot",75,20,"shot","Charles Chevalier",0),
    ("Chevalier Dribble","دریبل شوالیه","chevdrib",80,20,"dribble","Charles Chevalier",7000),
    ("Chevalier Pass","پاس شوالیه","chevpass",80,20,"pass","Charles Chevalier",7000),
    ("Bachira Dribble","دریبل باچیرا","elastic",85,20,"dribble","Meguru Bachira",0),
    ("Bachira Pass","پاس باچیرا","bachirapass",80,20,"pass","Meguru Bachira",8000),
    ("Bachira Shot","شوت باچیرا","bachirashot",80,20,"shot","Meguru Bachira",8000),
    ("Snuffy Shot","شوت اسنافی","snuffyshot",85,20,"shot","Mark Snuffy",0),
    ("Snuffy Pass","پاس اسنافی","snuffypass",85,20,"pass","Mark Snuffy",8000),
    ("Snuffy Dribble","دریبل اسنافی","snuffydrib",85,20,"dribble","Mark Snuffy",8000),
    ("Cavascoz Shot","شوت کاواسکوز","cavshot",80,20,"shot","Pablo Cavascoz",0),
    ("Cavascoz Pass","پاس کاواسکوز","cavpass",85,20,"pass","Pablo Cavascoz",8000),
    ("Cavascoz Dribble","دریبل کاواسکوز","cavdrib",85,20,"dribble","Pablo Cavascoz",8000),
    ("Teddy Shot","شوت تدی","teddyshot",75,20,"shot","Teddy Knight",0),
    ("Teddy Pass","پاس تدی","teddypass",80,20,"pass","Teddy Knight",7000),
    ("Teddy Dribble","دریبل تدی","teddydrib",75,20,"dribble","Teddy Knight",6000),
    ("Hugo Shot","شوت هوگو","hugoshot",75,20,"shot","Vivian Hugo",0),
    ("Hugo Pass","پاس هوگو","hugopass",80,20,"pass","Vivian Hugo",7000),
    ("Hugo Dribble","دریبل هوگو","hugodrib",75,20,"dribble","Vivian Hugo",6000),

    # DF (مدافع‌ها)
    ("Silva Shot","شوت سیلوا","silvashot",85,20,"shot","Dada Silva",0),
    ("Silva Defense","دفاع سیلوا","silvadef",90,20,"defend","Dada Silva",9000),
    ("Silva Block","بلاک سیلوا","silvablock",90,20,"block","Dada Silva",9000),
    ("Lorenzo Dribble","دریبل لورنزو","lordrib",85,20,"dribble","Don Lorenzo",0),
    ("Lorenzo Defense","دفاع لورنزو","lordef",90,20,"defend","Don Lorenzo",10000),
    ("Lorenzo Block","بلاک لورنزو","lorblock",90,20,"block","Don Lorenzo",10000),
    ("Niko Defense","دفاع نیکو","nikodef",80,20,"defend","Ikki Niko",0),
    ("Niko Pass","پاس نیکو","nikopass",80,20,"pass","Ikki Niko",7000),
    ("Niko Block","بلاک نیکو","nikoblock",80,20,"block","Ikki Niko",7000),
    ("Aiku Defense","دفاع آیکو","aikudef",90,20,"defend","Oliver Aiku",0),
    ("Aiku Tackle","تکل آیکو","slide",85,20,"defend","Oliver Aiku",9000),
    ("Aiku Block","بلاک آیکو","aikublock",90,20,"block","Oliver Aiku",9000),
    ("Kurona Dribble","دریبل کورونا","kurona",80,20,"dribble","Ranze Kurona",0),
    ("Kurona Defense","دفاع کورونا","koronadef",85,20,"defend","Ranze Kurona",8000),
    ("Kurona Pass","پاس کورونا","koronapass",80,20,"pass","Ranze Kurona",7000),
    ("Aryu Defense","دفاع آریو","aryudef",90,20,"defend","Jyubei Aryu",0),
    ("Aryu Block","بلاک آریو","aryublock",90,20,"block","Jyubei Aryu",9000),
    ("Aryu Shot","شوت آریو","aryushot",75,20,"shot","Jyubei Aryu",6000),
    ("Igaguri Foul","خطای ایگاگوری","igaguri",60,20,"defend","Igaguri",0),
    ("Igaguri Dive","شیرجه ایگاگوری","dive",55,20,"block","Igaguri",4000),
    ("Igaguri Pass","پاس ایگاگوری","igaguripass",60,20,"pass","Igaguri",4000),
    ("Nanase Stamina","استقامت ناناسه","nanase",80,20,"defend","Nanase",0),
    ("Nanase Pass","پاس ناناسه","nanasepass",80,20,"pass","Nanase",7000),
    ("Nanase Block","بلاک ناناسه","nanaseblock",80,20,"block","Nanase",7000),

    # GK (دروازه‌بان‌ها)
    ("Gagamaru Save","سیو گاگامارو","gagamaru",90,20,"block","Gin Gagamaru",0),
    ("Gagamaru Pass","پاس گاگامارو","gagapass",85,20,"pass","Gin Gagamaru",8000),
    ("Wild Save","سیو وحشی","wildsave",95,20,"block","Gin Gagamaru",15000),
    ("Fukaku Save","سیو فوکاکو","fukakusave",85,20,"block","Fukaku",0),
    ("Fukaku Pass","پاس فوکاکو","fukakupass",80,20,"pass","Fukaku",7000),
    ("Fukaku Defense","دفاع فوکاکو","fukakudef",85,20,"defend","Fukaku",7000),
]

def seed():
    conn = db(); c = conn.cursor()
    
    # 🛑 فقط اتصال Abilityها به کاراکترها رو پاک میکنیم (نه کاربرا)
    c.execute("DELETE FROM character_abilities")
    
    for ch in CHARACTERS:
        # چک میکنیم کاراکتر هست یا نه
        c.execute("SELECT id FROM characters WHERE name=?", (ch[0],))
        if not c.fetchone():
            try: c.execute("INSERT INTO characters (name,tier,role,defense,dribble_defense,attack) VALUES (?,?,?,?,?,?)", ch)
            except: pass
        else:
            try: c.execute("UPDATE characters SET role=?, tier=? WHERE name=?", (ch[2], ch[1], ch[0]))
            except: pass
            
    for ab in ABILITIES:
        try: c.execute("INSERT INTO abilities (name_en,name_fa,aliases,power,cooldown,category,owner,price) VALUES (?,?,?,?,?,?,?,?)", ab)
        except: pass
    
    c.execute("INSERT OR IGNORE INTO character_abilities (character_id, ability_id) SELECT c.id, a.id FROM characters c, abilities a WHERE c.name = a.owner")
    conn.commit(); conn.close()