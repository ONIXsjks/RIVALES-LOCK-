import telebot
from telebot import types
import time
import random
from config import TOKEN, OWNER_ID, MAX_GOALS
from database import init_db, seed, db
from utils import (
    get_rank, is_banned, get_user, get_slots, get_abilities,
    check_rip_status, consume_energy, ab_cd, set_ab_cd,
    find_ability, simulate, get_image, set_image, log_history, get_active_event
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
    energy = user[8] if user[8] is not None else max_energy
    coins = user[10] if len(user) > 10 and user[10] is not None else 0
    text = f"🎮✨ **Blue Lock Bot** ✨🎮\n\n👋 سلام {name}!\n🏆 رنک: {rank} ({user[2]} امتیاز)\n⚡ انرژی: {energy}/{max_energy}\n🪙 سکه: {coins}\n"
    if user[9] and user[9] > time.time(): text += f"😵 خسته (تا {int(user[9]-time.time())} ثانیه)\n"
    
    ev = get_active_event()
    if ev: text += f"\n🎉 **رویداد فعال:** {ev[1]}\n"
        
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("🛡 اسلات‌های من", callback_data=f"menu_slots_{uid}"), types.InlineKeyboardButton("👤 پروفایل من", callback_data=f"menu_profile_{uid}"))
    markup.add(types.InlineKeyboardButton("🛒 فروشگاه Ability", callback_data=f"menu_shop_{uid}"), types.InlineKeyboardButton("📖 Abilityهای من", callback_data=f"menu_abilities_{uid}"))
    markup.add(types.InlineKeyboardButton("🏆 لیدربورد", callback_data=f"menu_top_{uid}"), types.InlineKeyboardButton("📜 تاریخچه", callback_data=f"menu_history_{uid}"))
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
    u = get_user(uid)
    slots = get_slots(uid)
    rank, max_energy = get_rank(u[2])
    energy = u[8] if u[8] is not None else max_energy
    coins = u[10] if len(u) > 10 and u[10] is not None else 0
    
    text = f"👤✨ **پروفایل {u[1]}** ✨👤\n\n🏆 رنک: {rank} ({u[2]} امتیاز)\n⚡ انرژی: {energy}/{max_energy}\n🪙 سکه: {coins}\n⚽ گل‌ها: {u[3]}\n🧤 مهارها: {u[4]}\n\n🎭 **کاراکترهای شما:**\n"
    if not slots: text += "⚪ هنوز کاراکتری انتخاب نکردی!"
    else:
        for s in slots: text += f"• {s[2]}\n"
    
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 برگشت", callback_data=f"back_main_{uid}"))
    photo_id = slots[0][3] if slots and slots[0][3] else None
    
    if edit_msg_id:
        try: bot.delete_message(chat_id, edit_msg_id)
        except: pass
    if photo_id: bot.send_photo(chat_id, photo_id, caption=text, reply_markup=markup, parse_mode='Markdown')
    else: bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')

def show_history(chat_id, uid, edit_msg_id=None):
    conn = db(); c = conn.cursor()
    c.execute("SELECT ability_name, result, points FROM history WHERE attacker_id=? ORDER BY id DESC LIMIT 10", (uid,))
    hist = c.fetchall(); conn.close()
    
    text = "📜✨ **۱۰ بازی آخر شما** ✨📜\n\n"
    if not hist: text += "هنوز بازی نکردی!"
    else:
        for h in hist:
            icon = "⚽ گل" if h[1] == "goal" else "🧤 مهار"
            sign = "+" if h[2] > 0 else ""
            text += f"• {h[0]} | {icon} | {sign}{h[2]} امتیاز\n"
    
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 برگشت", callback_data=f"back_main_{uid}"))
    edit_to_text(chat_id, edit_msg_id, text, markup)

def show_shop(chat_id, uid, edit_msg_id=None):
    u = get_user(uid)
    coins = u[10] if len(u) > 10 and u[10] is not None else 0
    text = f"🛒✨ **فروشگاه Ability** ✨🛒\n\n🪙 سکه شما: {coins}\n\n📌 Ability مورد نظر رو بخر:"
    
    conn = db(); c = conn.cursor()
    c.execute("""SELECT a.id, a.name_fa, a.price FROM abilities a
                 JOIN character_abilities ca ON a.id = ca.ability_id
                 JOIN user_slots us ON ca.character_id = us.character_id
                 WHERE us.user_id = ? 
                 AND a.id NOT IN (SELECT ability_id FROM user_abilities WHERE user_id=?)
                 AND a.price > 0
                 GROUP BY a.id ORDER BY a.price ASC LIMIT 15""", (uid, uid))
    shop_abs = c.fetchall(); conn.close()
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    if not shop_abs:
        text = "🛒✨ **فروشگاه** ✨🛒\n\n👀 هیچ Ability جدیدی برای کاراکترهای شما نیست! (اول برو توی /slots کاراکتر انتخاب کن)"
    else:
        for ab in shop_abs:
            markup.add(types.InlineKeyboardButton(f"{ab[1]} ({ab[2]}🪙)", callback_data=f"buy_{ab[0]}_{ab[2]}_{uid}"))
            
    markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data=f"back_main_{uid}"))
    edit_to_text(chat_id, edit_msg_id, text, markup)

@bot.message_handler(func=lambda m: m.reply_to_message is not None)
def handle_reply(message):
    uid = message.from_user.id
    if is_banned(uid): return
    
    target_user = message.reply_to_message.from_user
    if target_user.id == uid or target_user.is_bot: return 
    
    abilities = get_abilities(uid)
    if not abilities: return
        
    ab = find_ability(message.text, abilities)
    if not ab: return 
    
    status, msg = check_rip_status(uid)
    if not status: return
        
    cd = ab_cd(uid, ab[0])
    if cd > 0: return
        
    target_slots = get_slots(target_user.id)
    if not target_slots:
        bot.reply_to(message, f"❌ {target_user.first_name} هنوز کاراکتر انتخاب نکرده!"); return

    # ایجاد مچ جدید
    conn = db(); c = conn.cursor()
    c.execute("DELETE FROM matches WHERE chat_id=?", (message.chat.id,))
    c.execute("INSERT INTO matches (chat_id, p1_id, p2_id, p1_goals, p2_goals, turn_id) VALUES (?, ?, ?, 0, 0, ?)", 
              (message.chat.id, uid, target_user.id, uid))
    conn.commit(); conn.close()

    user_slots = get_slots(uid)
    markup = types.InlineKeyboardMarkup(row_width=1)
    for slot in user_slots:
        markup.add(types.InlineKeyboardButton(f"⚔ {slot[2]}", callback_data=f"atk_{target_user.id}_{uid}_{ab[0]}_{slot[1]}"))
    
    text = f"🎯 **شروع بازی!**\n\n{message.from_user.first_name} داره با Ability **{ab[2]}** به {target_user.first_name} حمله می‌کنه!\nبا کدوم کاراکترت حمله می‌کنی؟"
    bot.reply_to(message, text, reply_markup=markup, parse_mode='Markdown')

def start_defense_phase(chat_id, attacker_id, target_id, ability_id, char_id):
    conn = db(); c = conn.cursor()
    c.execute("SELECT name_fa, category FROM abilities WHERE id=?", (ability_id,))
    ab = c.fetchone()
    conn.close()
    
    # تعیین دکمه دفاع/بلاک بر اساس نوع حمله
    action = "دفاع" if ab[1] == "dribble" else "بلاک"
    cb_data = "def" if ab[1] == "dribble" else "blk"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"🛡 {action} می‌کنم", callback_data=f"{cb_data}_{attacker_id}_{target_id}_{ability_id}_{char_id}"))
    
    text = f"⚠️ **هشدار حمله!**\n\nیک کاربر با Ability **{ab[0]}** ({ab[1]}) به شما حمله کرده!\nآیا می‌خواهید {action} کنید؟"
    try:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')
    except:
        bot.send_message(chat_id, "❌ نتونستم به حریف پیام بدم.")

def execute_action(chat_id, attacker_id, target_id, ability_id, char_id, defense_ability_id=None, simple_defense=False):
    conn = db(); c = conn.cursor()
    c.execute("SELECT name_fa, power, category FROM abilities WHERE id=?", (ability_id,))
    atk_ab = c.fetchone()
    
    c.execute("SELECT name FROM characters WHERE id=?", (char_id,))
    attacker_char = c.fetchone()[0]
    
    target_slots = get_slots(target_id)
    target_char = random.choice(target_slots)
    
    def_power = 30 if simple_defense else 0
    if defense_ability_id:
        c.execute("SELECT power FROM abilities WHERE id=?", (defense_ability_id,))
        def_power = c.fetchone()[0]
    
    c.execute("SELECT name FROM users WHERE user_id=?", (target_id,))
    target_name = c.fetchone()[0]
    conn.close()
    
    atk_power = atk_ab[1] + random.randint(-10, 10)
    def_power_roll = def_power + random.randint(-10, 10)
    
    if atk_power > def_power_roll:
        res = "success"
        text = f"⚡ **موفقیت!**\n\n🎯 **{attacker_char}** با **{atk_ab[0]}** از **{target_name}** رد شد!\n\n💪 قدرت: {atk_ab[1]} vs 🛡 دفاع: {def_power}"
        if atk_ab[2] == "shot":
            # گل زد
            conn = db(); c = conn.cursor()
            c.execute("UPDATE matches SET p1_goals = p1_goals + 1 WHERE p1_id=?", (attacker_id,))
            c.execute("UPDATE matches SET p2_goals = p2_goals + 1 WHERE p2_id=?", (attacker_id,))
            c.execute("UPDATE users SET coins = coins + 50 WHERE user_id=?", (attacker_id,))
            conn.commit(); conn.close()
            text += f"\n\n⚽ **گل!!!** {attacker_char} گل زد!"
    else:
        res = "fail"
        text = f"🧤 **ناموفق!**\n\n🛡 **{target_name}** جلوی **{atk_ab[0]}** رو گرفت!\n\n💪 قدرت: {atk_ab[1]} vs 🛡 دفاع: {def_power}"
        # توپ میره پیش مدافع
        conn = db(); c = conn.cursor()
        c.execute("UPDATE matches SET turn_id=? WHERE chat_id=?", (target_id, chat_id))
        conn.commit(); conn.close()
    
    bot.send_message(chat_id, text, parse_mode='Markdown')
    
    # بررسی پایان بازی (۳ گل)
    conn = db(); c = conn.cursor()
    c.execute("SELECT p1_id, p2_id, p1_goals, p2_goals FROM matches WHERE chat_id=?", (chat_id,))
    match = c.fetchone(); conn.close()
    
    if match:
        p1_id, p2_id, p1_goals, p2_goals = match
        if p1_goals >= 3 or p2_goals >= 3:
            winner = p1_id if p1_goals >= 3 else p2_id
            loser = p2_id if p1_goals >= 3 else p1_id
            conn = db(); c = conn.cursor()
            c.execute("UPDATE users SET coins = coins + 1000 WHERE user_id=?", (winner,))
            c.execute("UPDATE users SET coins = coins + 0 WHERE user_id=?", (loser,))
            c.execute("DELETE FROM matches WHERE chat_id=?", (chat_id,))
            conn.commit(); conn.close()
            bot.send_message(chat_id, f"🏆 **بازی تموم شد!**\n{winner} برنده شد با نتیجه {p1_goals}-{p2_goals}!\n🪙 +1000 سکه به برنده.", parse_mode='Markdown')
@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    uid = call.from_user.id; data = call.data; chat_id = call.message.chat.id; msg_id = call.message.message_id
    
    if data.startswith("atk_"):
        _, target_id, attacker_id, ability_id, char_id = data.split("_")
        if uid != int(attacker_id): return
        try: bot.delete_message(chat_id, msg_id)
        except: pass
        start_defense_phase(chat_id, int(attacker_id), int(target_id), int(ability_id), int(char_id))
        return
        
    elif data.startswith("def_") or data.startswith("blk_"):
        action = "def" if data.startswith("def_") else "blk"
        _, attacker_id, target_id, ability_id, char_id = data.split("_")
        if uid != int(target_id): return
            
        conn = db(); c = conn.cursor()
        if action == "def":
            c.execute("""SELECT a.id, a.name_fa FROM abilities a
                         JOIN character_abilities ca ON a.id = ca.ability_id
                         JOIN user_slots us ON ca.character_id = us.character_id
                         WHERE us.user_id = ? AND a.category = 'defend'""", (uid,))
        else:
            c.execute("""SELECT a.id, a.name_fa FROM abilities a
                         JOIN character_abilities ca ON a.id = ca.ability_id
                         JOIN user_slots us ON ca.character_id = us.character_id
                         WHERE us.user_id = ? AND a.category = 'block'""", (uid,))
        def_abs = c.fetchall(); conn.close()
        
        if not def_abs:
            try: bot.delete_message(chat_id, msg_id)
            except: pass
            execute_action(chat_id, int(attacker_id), int(target_id), int(ability_id), int(char_id), simple_defense=True)
            return
            
        markup = types.InlineKeyboardMarkup(row_width=1)
        for ab in def_abs:
            markup.add(types.InlineKeyboardButton(ab[1], callback_data=f"exec_{action}_{attacker_id}_{target_id}_{ability_id}_{char_id}_{ab[0]}"))
        bot.edit_message_text("🛡 **انتخاب Ability:**", chat_id=chat_id, message_id=msg_id, reply_markup=markup)
        
    elif data.startswith("exec_"):
        _, action, attacker_id, target_id, ability_id, char_id, def_ab_id = data.split("_")
        if uid != int(target_id): return
        try: bot.delete_message(chat_id, msg_id)
        except: pass
        execute_action(chat_id, int(attacker_id), int(target_id), int(ability_id), int(char_id), int(def_ab_id))
        return

    # منوها (بدون قفل)
    if data.startswith("menu_slots"):
        slots = get_slots(uid)
        text = "🛡✨ **اسلات‌های کاراکتر شما** ✨🛡\n\n"
        for i in range(1,4):
            s = next((x for x in slots if x[0]==i), None)
            text += f"{i}️⃣ {s[2] if s else '⚪ خالی'}\n"
        markup = types.InlineKeyboardMarkup(row_width=1)
        for i in range(1,4):
            s = next((x for x in slots if x[0]==i), None)
            label = f"🔄 تغییر اسلات {i} ({s[2][:12]})" if s else f"➕ افزودن به اسلات {i}"
            markup.add(types.InlineKeyboardButton(label, callback_data=f"editslot_{i}_{uid}_0"))
        markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data=f"back_main_{uid}"))
        edit_to_text(chat_id, msg_id, text, markup)
    elif data.startswith("menu_profile"): show_profile(chat_id, uid, edit_msg_id=msg_id)
    elif data.startswith("menu_history"): show_history(chat_id, uid, edit_msg_id=msg_id)
    elif data.startswith("menu_shop"): show_shop(chat_id, uid, edit_msg_id=msg_id)
    elif data.startswith("buy_"):
        _, aid, price, owner = data.split("_")
        aid = int(aid); price = int(price)
        u = get_user(uid)
        coins = u[10] if len(u) > 10 and u[10] is not None else 0
        if coins < price:
            bot.answer_callback_query(call.id, "❌ سکه کافی نداری!", show_alert=True)
        else:
            conn = db(); c = conn.cursor()
            c.execute("UPDATE users SET coins=coins-? WHERE user_id=?", (price, uid))
            c.execute("INSERT OR IGNORE INTO user_abilities (user_id,ability_id) VALUES (?,?)", (uid, aid))
            conn.commit(); conn.close()
            bot.answer_callback_query(call.id, "✅ Ability خریداری شد!", show_alert=True)
            show_shop(chat_id, uid, edit_msg_id=msg_id)
    elif data.startswith("menu_top"):
        conn = db(); c = conn.cursor(); c.execute("SELECT name,rank_points FROM users ORDER BY rank_points DESC LIMIT 10"); top = c.fetchall(); conn.close()
        t = "🏆✨ **لیدربورد** ✨🏆\n\n"
        for i,(n,p) in enumerate(top,1):
            m = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}️⃣"
            t += f"{m} {n}: {p}\n"
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 برگشت", callback_data=f"back_main_{uid}"))
        edit_to_text(chat_id, msg_id, t, markup)
    elif data.startswith("menu_abilities"):
        abs_ = get_abilities(uid)
        t = "📖✨ **Abilityهای شما** ✨📖\n\n" if abs_ else "📖✨ Ability نداری! /slots"
        for a in abs_: t += f"• {a[2]} ({a[1]}) — ⏱{a[5]}s\n"
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 برگشت", callback_data=f"back_main_{uid}"))
        edit_to_text(chat_id, msg_id, t, markup)
    elif data.startswith("back_main"): 
        show_main_menu(chat_id, uid, call.from_user.first_name, edit_msg_id=msg_id)
    elif data.startswith("editslot_"):
        _, sn, owner, page = data.split("_")
        sn = int(sn); page = int(page)
        conn = db(); c = conn.cursor(); c.execute("SELECT id,name FROM characters ORDER BY name ASC"); chars = c.fetchall(); conn.close()
        
        per_page = 10
        start = page * per_page
        end = start + per_page
        page_chars = chars[start:end]
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        for ch in page_chars: 
            markup.add(types.InlineKeyboardButton(ch[1], callback_data=f"setchar_{sn}_{ch[0]}_{uid}"))
            
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
            label = f"🔄 تغییر اسلات {i} ({s[2][:12]})" if s else f"➕ افزودن به اسلات {i}"
            markup.add(types.InlineKeyboardButton(label, callback_data=f"editslot_{i}_{uid}_0"))
        markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data=f"back_main_{uid}"))
        edit_to_text(chat_id, msg_id, text, markup)
    
    elif data.startswith("menu_admin") and uid == OWNER_ID:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("🖼 عکس بنرها", callback_data=f"adm_images_{uid}"), types.InlineKeyboardButton("📸 عکس کاراکترها", callback_data=f"adm_charimg_{uid}"))
        markup.add(types.InlineKeyboardButton("🎉 ساخت رویداد", callback_data=f"adm_event_{uid}"), types.InlineKeyboardButton("🚫 بن کاربر", callback_data=f"adm_ban_{uid}"))
        markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data=f"back_main_{uid}"))
        edit_to_text(chat_id, msg_id, "👑✨ **پنل مالک** ✨👑", markup)
    elif data.startswith("adm_charimg") and uid == OWNER_ID:
        conn = db(); c = conn.cursor(); c.execute("SELECT id,name FROM characters ORDER BY name ASC"); chars = c.fetchall(); conn.close()
        markup = types.InlineKeyboardMarkup(row_width=2)
        for ch in chars: markup.add(types.InlineKeyboardButton(ch[1], callback_data=f"setcimg_{ch[0]}_{uid}"))
        markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data=f"menu_admin_{uid}"))
        edit_to_text(chat_id, msg_id, "📸 **انتخاب کاراکتر برای گذاشتن عکس:**", markup)
    elif data.startswith("setcimg_") and uid == OWNER_ID:
        _, cid, owner = data.split("_")
        admin_states[uid] = f"wait_charimg_{cid}"
        edit_to_text(chat_id, msg_id, "📸 **حالا عکس این کاراکتر رو بفرست:**")
    elif data.startswith("adm_event") and uid == OWNER_ID:
        admin_states[uid] = "wait_event_title"
        edit_to_text(chat_id, msg_id, "🎉 **اسم رویداد رو بفرست:**\n(مثلاً: ریپ روی Rin ۲ برابر)")
    elif data.startswith("adm_ban") and uid == OWNER_ID:
        admin_states[uid] = "wait_ban_id"
        edit_to_text(chat_id, msg_id, "🚫 **آیدی عددی کاربری که می‌خوای بن کنی رو بفرست:**")
    elif data.startswith("adm_images") and uid == OWNER_ID:
        markup = types.InlineKeyboardMarkup(row_width=2)
        for k in ['welcome_banner','rank_bronze','rank_silver','rank_gold','rank_bluelock','rank_legend']:
            markup.add(types.InlineKeyboardButton(k, callback_data=f"imgset_{k}_{uid}"))
        markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data=f"menu_admin_{uid}"))
        edit_to_text(chat_id, msg_id, "🖼✨ انتخاب بنر ✨🖼", markup)
    elif data.startswith("imgset_") and uid == OWNER_ID:
        _, key, owner = data.split("_")
        admin_states[uid] = f"wait_img_{key}"
        edit_to_text(chat_id, msg_id, f"🖼✨ {key} ✨🖼\n\n📌 عکس رو بفرست!")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    uid = message.from_user.id
    state = admin_states.get(uid)
    if state:
        if state.startswith("wait_img_"):
            key = state.replace("wait_img_", "")
            set_image(key, message.photo[-1].file_id, uid)
            bot.reply_to(message, f"✅ بنر {key} ذخیره شد!")
        elif state.startswith("wait_charimg_"):
            cid = int(state.replace("wait_charimg_", ""))
            conn = db(); c = conn.cursor(); c.execute("UPDATE characters SET photo_file_id=? WHERE id=?", (message.photo[-1].file_id, cid)); conn.commit(); conn.close()
            bot.reply_to(message, "✅ عکس کاراکتر ذخیره شد!")
        del admin_states[uid]
        return

if __name__ == "__main__":
    migration.migrate()
    init_db()
    seed()
    print("🚀✨ Blue Lock Bot روشن شد! ✨🚀")
    bot.infinity_polling()