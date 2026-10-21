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