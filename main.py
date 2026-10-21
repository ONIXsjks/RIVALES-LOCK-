import telebot
from telebot import types
import time
import random
from config import TOKEN, OWNER_ID, MAX_GOALS
from database import init_db, seed, db
from utils import (
    get_rank, is_banned, get_user, get_slots, get_abilities,
    ab_cd, set_ab_cd, find_ability, simulate,
    get_image, set_image, log_history, get_active_event
)
import migration

bot = telebot.TeleBot(TOKEN)
admin_states = {}

def edit_to_text(chat_id, msg_id, text, markup=None):
    try:
        bot.edit_message_text(text, chat_id=chat_id, message_id=msg_id, reply_markup=markup, parse_mode='Markdown')
    except Exception:
        try: bot.delete_message(chat_id, msg_id)
        except: pass
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')

def show_main_menu(chat_id, uid, name, edit_msg_id=None):
    user = get_user(uid)
    rank, max_energy = get_rank(user[2])
    coins = user[10] if len(user) > 10 and user[10] is not None else 0
    
    text = f"🎮✨ **Blue Lock Bot** ✨🎮\n\n👋 سلام {name}!\n🏆 رنک: {rank} ({user[2]} امتیاز)\n🪙 سکه: {coins}\n"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("🛡 اسلات‌های من", callback_data=f"menu_slots_{uid}"), types.InlineKeyboardButton("👤 پروفایل من", callback_data=f"menu_profile_{uid}"))
    markup.add(types.InlineKeyboardButton("🛒 فروشگاه", callback_data=f"menu_shop_{uid}"), types.InlineKeyboardButton("📖 Abilityها", callback_data=f"menu_abilities_{uid}"))
    markup.add(types.InlineKeyboardButton("🏆 لیدربورد", callback_data=f"menu_top_{uid}"), types.InlineKeyboardButton("❓ راهنما", callback_data=f"menu_help_{uid}"))
    if uid == OWNER_ID: markup.add(types.InlineKeyboardButton("👑 پنل مالک", callback_data=f"menu_admin_{uid}"))
        
    banner = get_image('welcome_banner')
    if edit_msg_id:
        try: bot.delete_message(chat_id, edit_msg_id)
        except: pass
    if banner: bot.send_photo(chat_id, banner, caption=text, reply_markup=markup, parse_mode='Markdown')
    else: bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id; name = message.from_user.first_name
    if is_banned(uid): bot.reply_to(message, "🚫✨ دسترسی مسدود! ✨🚫"); return
    if not get_user(uid):
        conn = db(); c = conn.cursor(); c.execute("INSERT INTO users (user_id,name) VALUES (?,?)", (uid, name)); conn.commit(); conn.close()
    show_main_menu(message.chat.id, uid, name)

def show_profile(chat_id, uid, edit_msg_id=None):
    u = get_user(uid); slots = get_slots(uid); coins = u[10] if len(u) > 10 and u[10] is not None else 0
    text = f"👤✨ **پروفایل {u[1]}** ✨👤\n\n🏆 رنک: {get_rank(u[2])[0]} ({u[2]} امتیاز)\n🪙 سکه: {coins}\n\n🎭 **اسلات‌های شما:**\n"
    if not slots: text += "⚪ خالی!"
    else:
        for s in slots: text += f"{s[0]}️⃣ {s[2]} ({s[3]})\n"
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 برگشت", callback_data=f"back_main_{uid}"))
    photo_id = slots[0][4] if slots and slots[0][4] else None
    if edit_msg_id:
        try: bot.delete_message(chat_id, edit_msg_id)
        except: pass
    if photo_id: bot.send_photo(chat_id, photo_id, caption=text, reply_markup=markup, parse_mode='Markdown')
    else: bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')

def show_help(chat_id, uid, edit_msg_id=None):
    text = """❓ **راهنمای بازی**
    
1. **انتخاب کاراکتر:** قبل از بازی، ۳ کاراکتر انتخاب کن:
   - اسلات ۱: مهاجم (FW)
   - اسلات ۲: هافبک (MF)
   - اسلات ۳: مدافع (DF) یا دروازه‌بان (GK)

2. **شروع بازی:** روی پیام حریف ریپلای بزن و بنویس `Start match`.

3. **حمله:** 
   - دریبل بزن (اگه موفق شدی، شانس شوتت بیشتر میشه)
   - پاس بده (حریف می‌تونه قطع پاس کنه)
   - شوت بزن (اگه به محدوده شوت رسیده باشی)

4. **دفاع:**
   - جلوی دریبل: دفاع
   - جلوی پاس: قطع پاس
   - جلوی شوت: بلاک (دروازه‌بان: سیو)

5. **پایان:** هر کی زودتر ۳ گل بزنه برنده‌ست و ۱۰۰۰ سکه می‌گیره!"""
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 برگشت", callback_data=f"back_main_{uid}"))
    edit_to_text(chat_id, edit_msg_id, text, markup)

def show_shop(chat_id, uid, edit_msg_id=None):
    u = get_user(uid); coins = u[10] if len(u) > 10 and u[10] is not None else 0
    text = f"🛒✨ **فروشگاه Ability** ✨🛒\n\n🪙 سکه شما: {coins}\n\n📌 Ability مورد نظر رو بخر:"
    conn = db(); c = conn.cursor()
    c.execute("""SELECT a.id, a.name_fa, a.price FROM abilities a
                 JOIN character_abilities ca ON a.id = ca.ability_id
                 JOIN user_slots us ON ca.character_id = us.character_id
                 WHERE us.user_id = ? AND a.id NOT IN (SELECT ability_id FROM user_abilities WHERE user_id=?)
                 AND a.price > 0 GROUP BY a.id ORDER BY a.price ASC LIMIT 15""", (uid, uid))
    shop_abs = c.fetchall(); conn.close()
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    if not shop_abs: text = "🛒✨ **فروشگاه** ✨🛒\n\n👀 هیچ Ability جدیدی برای کاراکترهای شما نیست!"
    else:
        for ab in shop_abs: markup.add(types.InlineKeyboardButton(f"{ab[1]} ({ab[2]}🪙)", callback_data=f"buy_{ab[0]}_{ab[2]}_{uid}"))
    markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data=f"back_main_{uid}"))
    edit_to_text(chat_id, edit_msg_id, text, markup)

@bot.message_handler(func=lambda m: m.reply_to_message is not None)
def handle_reply(message):
    uid = message.from_user.id
    if is_banned(uid): return
    
    target_user = message.reply_to_message.from_user
    if target_user.id == uid or target_user.is_bot: return
    
    if message.text.lower().strip() != "start match": return
    
    slots1 = get_slots(uid)
    slots2 = get_slots(target_user.id)
    if len(slots1) < 3 or len(slots2) < 3:
        bot.reply_to(message, "❌ هر دو بازیکن باید ۳ کاراکتر انتخاب کرده باشن!"); return

    conn = db(); c = conn.cursor()
    c.execute("DELETE FROM matches WHERE chat_id=?", (message.chat.id,))
    c.execute("INSERT INTO matches (chat_id, p1_id, p2_id, p1_goals, p2_goals, turn_id) VALUES (?, ?, ?, 0, 0, ?)", 
              (message.chat.id, uid, target_user.id, uid))
    conn.commit(); conn.close()

    text = f"⚔️ **بازی شروع شد!**\n\n{message.from_user.first_name} در برابر {target_user.first_name}\n\n🎯 توپ اول دست {message.from_user.first_name} هست.\nبا کاراکتر مهاجمت (FW) حمله کن!"
    bot.send_message(message.chat.id, text, reply_markup=get_attack_menu(uid), parse_mode='Markdown')

def get_attack_menu(uid):
    slots = get_slots(uid)
    markup = types.InlineKeyboardMarkup(row_width=1)
    for slot in slots:
        markup.add(types.InlineKeyboardButton(f"{slot[0]}️⃣ {slot[2]} ({slot[3]})", callback_data=f"act_{slot[1]}"))
    return markup

def execute_action(chat_id, attacker_id, target_id, char_id, action, ability_id=None):
    conn = db(); c = conn.cursor()
    
    c.execute("SELECT name FROM characters WHERE id=?", (char_id,))
    attacker_char = c.fetchone()[0]
    
    c.execute("SELECT defense FROM characters WHERE id=?", (char_id,))
    atk_stat = c.fetchone()[0] if action == "shot" else 80
    
    if ability_id:
        c.execute("SELECT name_fa, power FROM abilities WHERE id=?", (ability_id,))
        ab = c.fetchone()
        atk_power = ab[1]
        ab_name = ab[0]
    else:
        atk_power = 30
        ab_name = "ساده"
    
    c.execute("SELECT name FROM users WHERE user_id=?", (target_id,))
    target_name = c.fetchone()[0]
    
    def_power = 30 
    def_result = random.randint(0, 100)
    
    if atk_power + random.randint(-10, 10) > def_power + random.randint(-10, 10):
        res = "success"
        if action == "shot":
            c.execute("UPDATE matches SET p1_goals = p1_goals + 1 WHERE p1_id=?", (attacker_id,))
            c.execute("UPDATE matches SET p2_goals = p2_goals + 1 WHERE p2_id=?", (attacker_id,))
            c.execute("UPDATE users SET coins = coins + 50 WHERE user_id=?", (attacker_id,))
            text = f"⚽✨ **گل!!!** ✨⚽\n\n🎯 **{attacker_char}** با **{ab_name}** گل زد!\n\n🏆 +50 سکه"
        else:
            text = f"⚡ **موفقیت!**\n\n🎯 **{attacker_char}** با **{ab_name}** موفق شد!"
    else:
        res = "fail"
        text = f"🧤 **ناموفق!**\n\n🛡 **{target_name}** جلوی **{ab_name}** رو گرفت!"
    
    conn.commit(); conn.close()
    bot.send_message(chat_id, text, parse_mode='Markdown')
    
    if action == "shot":
        conn = db(); c = conn.cursor()
        c.execute("SELECT p1_goals, p2_goals FROM matches WHERE chat_id=?", (chat_id,))
        match = c.fetchone()
        if match and (match[0] >= 3 or match[1] >= 3):
            winner = "تیم ۱" if match[0] >= 3 else "تیم ۲"
            conn = db(); c = conn.cursor()
            c.execute("UPDATE users SET coins = coins + 1000 WHERE user_id=?", (attacker_id,))
            c.execute("DELETE FROM matches WHERE chat_id=?", (chat_id,))
            conn.commit(); conn.close()
            bot.send_message(chat_id, f"🏆 **بازی تموم شد!**\n{winner} برنده شد با نتیجه {match[0]}-{match[1]}!", parse_mode='Markdown')
        conn.close()

@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    uid = call.from_user.id; data = call.data; chat_id = call.message.chat.id; msg_id = call.message.message_id
    
    if data.startswith("menu_slots"):
        slots = get_slots(uid)
        text = "🛡✨ **اسلات‌های کاراکتر شما** ✨🛡\n\n"
        for i in range(1,4):
            s = next((x for x in slots if x[0]==i), None)
            text += f"{i}️⃣ {s[2] if s else '⚪ خالی'}\n"
        markup = types.InlineKeyboardMarkup(row_width=1)
        for i in range(1,4):
            s = next((x for x in slots if x[0]==i), None)
            label = f"🔄 تغییر اسلات {i}" if s else f"➕ افزودن به اسلات {i}"
            markup.add(types.InlineKeyboardButton(label, callback_data=f"editslot_{i}_{uid}_0"))
        markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data=f"back_main_{uid}"))
        edit_to_text(chat_id, msg_id, text, markup)
    elif data.startswith("menu_profile"): show_profile(chat_id, uid, edit_msg_id=msg_id)
    elif data.startswith("menu_help"): show_help(chat_id, uid, edit_msg_id=msg_id)
    elif data.startswith("menu_shop"): show_shop(chat_id, uid, edit_msg_id=msg_id)
    elif data.startswith("back_main"): show_main_menu(chat_id, uid, call.from_user.first_name, edit_msg_id=msg_id)
    
    elif data.startswith("editslot_"):
        _, sn, owner, page = data.split("_")
        sn = int(sn); page = int(page)
        role = "FW" if sn == 1 else "MF" if sn == 2 else "DF"
        conn = db(); c = conn.cursor(); 
        if sn == 3: c.execute("SELECT id,name FROM characters WHERE role IN ('DF', 'GK') ORDER BY name ASC")
        else: c.execute("SELECT id,name FROM characters WHERE role=? ORDER BY name ASC", (role,))
        chars = c.fetchall(); conn.close()
        per_page = 10; start = page * per_page; end = start + per_page
        page_chars = chars[start:end]
        markup = types.InlineKeyboardMarkup(row_width=2)
        for ch in page_chars: markup.add(types.InlineKeyboardButton(ch[1], callback_data=f"setchar_{sn}_{ch[0]}_{uid}"))
        nav = []
        if page > 0: nav.append(types.InlineKeyboardButton("⬅️ قبلی", callback_data=f"editslot_{sn}_{uid}_{page-1}"))
        if end < len(chars): nav.append(types.InlineKeyboardButton("بعدی ➡️", callback_data=f"editslot_{sn}_{uid}_{page+1}"))
        if nav: markup.add(*nav)
        markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data=f"menu_slots_{uid}"))
        edit_to_text(chat_id, msg_id, f"🎯 انتخاب برای اسلات {sn} (صفحه {page+1})", markup)
        
    elif data.startswith("setchar_"):
        _, sn, cid, owner = data.split("_")
        conn = db(); c = conn.cursor(); c.execute("INSERT OR REPLACE INTO user_slots (user_id,slot_number,character_id) VALUES (?,?,?)", (uid, int(sn), int(cid))); conn.commit(); conn.close()
        bot.answer_callback_query(call.id, "✅ کاراکتر انتخاب شد!")
        
        slots = get_slots(uid)
        text = "🛡✨ **اسلات‌های کاراکتر شما** ✨🛡\n\n"
        for i in range(1,4):
            s = next((x for x in slots if x[0]==i), None)
            text += f"{i}️⃣ {s[2] if s else '⚪ خالی'}\n"
        markup = types.InlineKeyboardMarkup(row_width=1)
        for i in range(1,4):
            s = next((x for x in slots if x[0]==i), None)
            label = f"🔄 تغییر اسلات {i}" if s else f"➕ افزودن به اسلات {i}"
            markup.add(types.InlineKeyboardButton(label, callback_data=f"editslot_{i}_{uid}_0"))
        markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data=f"back_main_{uid}"))
        edit_to_text(chat_id, msg_id, text, markup)

    elif data.startswith("act_"):
        cid = int(data.split("_")[1])
        conn = db(); c = conn.cursor(); c.execute("SELECT name, role FROM characters WHERE id=?", (cid,)); ch = c.fetchone(); conn.close()
        
        markup = types.InlineKeyboardMarkup()
        if ch[1] == 'FW' or ch[1] == 'MF':
            markup.add(types.InlineKeyboardButton("🌀 دریبل", callback_data=f"exec_drib_{cid}"), types.InlineKeyboardButton("⚽ شوت", callback_data=f"exec_shot_{cid}"))
        if ch[1] == 'MF' or ch[1] == 'DF':
            markup.add(types.InlineKeyboardButton("🎯 پاس", callback_data=f"exec_pass_{cid}"))
        edit_to_text(chat_id, msg_id, f"⚔️ با **{ch[0]}** چه کاری می‌کنی؟", markup)

    elif data.startswith("exec_"):
        _, act, cid = data.split("_")
        conn = db(); c = conn.cursor(); c.execute("SELECT p1_id, p2_id FROM matches WHERE chat_id=?", (chat_id,)); match = c.fetchone(); conn.close()
        if not match: return
        target_id = match[1] if match[0] == uid else match[0]
        
        execute_action(chat_id, uid, target_id, int(cid), act)

    elif data.startswith("buy_"):
        _, aid, price, owner = data.split("_")
        aid = int(aid); price = int(price)
        u = get_user(uid); coins = u[10] if len(u) > 10 and u[10] is not None else 0
        if coins < price: bot.answer_callback_query(call.id, "❌ سکه کافی نداری!", show_alert=True)
        else:
            conn = db(); c = conn.cursor()
            c.execute("UPDATE users SET coins=coins-? WHERE user_id=?", (price, uid))
            c.execute("INSERT OR IGNORE INTO user_abilities (user_id,ability_id) VALUES (?,?)", (uid, aid))
            conn.commit(); conn.close()
            bot.answer_callback_query(call.id, "✅ Ability خریداری شد!", show_alert=True)
            show_shop(chat_id, uid, edit_msg_id=msg_id)

if __name__ == "__main__":
    migration.migrate()
    init_db()
    seed()
    print("🚀✨ Blue Lock Bot روشن شد! ✨🚀")
    bot.infinity_polling()