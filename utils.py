import time
import random
from config import RANKS, ABILITY_COOLDOWN, ENERGY_COST, EXHAUSTION_TIME
from database import db

def get_rank(p):
    for t,n,e in reversed(RANKS):
        if p >= t: return n, e
    return RANKS[0][1], RANKS[0][2]

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
    c.execute("""SELECT us.slot_number,c.id,c.name,c.photo_file_id FROM user_slots us
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
    c.execute("SELECT last_rip, energy, exhausted_until, rank_points FROM users WHERE user_id=?", (uid,))
    r = c.fetchone(); conn.close()
    if not r: return False, "شما ثبت‌نام نکرده‌اید."
    now = time.time()
    
    # گرفتن حداکثر انرژی بر اساس رنک
    _, max_energy = get_rank(r[3])
    
    if r[2] and r[2] > now: return False, f"😵 خسته شدی! انرژی صفره.\n⏱ {int(r[2] - now)} ثانیه دیگه استراحت کن."
    if r[0] and now - r[0] < 10: return False, f"⏳ صبر کن! {int(10 - (now - r[0]))} ثانیه تا ریپ بعدی."
    
    # اگه انرژی از حداکثر رنک کمتر بود، پر کن
    if r[1] < max_energy:
        conn = db(); c = conn.cursor(); c.execute("UPDATE users SET energy=? WHERE user_id=?", (max_energy, uid)); conn.commit(); conn.close()
        
    return True, ""

def consume_energy(uid):
    conn = db(); c = conn.cursor()
    c.execute("SELECT energy, rank_points FROM users WHERE user_id=?", (uid,))
    r = c.fetchone()
    energy = r[0] or 100
    _, max_energy = get_rank(r[1])
    
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

def log_history(attacker_id, target_id, ability_name, result, pts):
    conn = db(); c = conn.cursor()
    c.execute("INSERT INTO history (attacker_id, target_id, ability_name, result, points, timestamp) VALUES (?,?,?,?,?,?)", 
              (attacker_id, target_id, ability_name, result, pts, int(time.time())))
    conn.commit(); conn.close()