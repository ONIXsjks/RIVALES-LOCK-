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
        text = "🛒✨ **فروشگاه** ✨🛒\n\n👀 هیچ Ability جدیدی برای کاراکترهای شما نیست!"
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
    if not status: 
        bot.reply_to(message, msg, parse_mode='Markdown')
        return
        
    cd = ab_cd(uid, ab[0])
    if cd > 0: 
        bot.reply_to(message, f"⏳ {ab[2]} — {cd} ثانیه کول‌داون داره!", parse_mode='Markdown')
        return
        
    target_slots = get_slots(target_user.id)
    if not target_slots:
        bot.reply_to(message, f"❌ {target_user.first_name} هنوز کاراکتر انتخاب نکرده!"); return

    user_slots = get_slots(uid)
    markup = types.InlineKeyboardMarkup(row_width=1)
    for slot in user_slots:
        markup.add(types.InlineKeyboardButton(f"⚔ {slot[2]}", callback_data=f"atk_{target_user.id}_{uid}_{ab[0]}_{slot[1]}"))
    
    text = f"🎯 **انتخاب مهاجم**\n\nشما می‌خواهید با Ability **{ab[2]}** به {target_user.first_name} حمله کنید.\nبا کدوم کاراکترت حمله می‌کنی؟"
    bot.reply_to(message, text, reply_markup=markup, parse_mode='Markdown')

def start_defense_phase(chat_id, attacker_id, target_id, ability_id, char_id):
    conn = db(); c = conn.cursor()
    c.execute("SELECT name_fa FROM abilities WHERE id=?", (ability_id,))
    ab_name = c.fetchone()[0]
    conn.close()
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🛡 دفاع می‌کنم", callback_data=f"def_{attacker_id}_{target_id}_{ability_id}_{char_id}"))
    markup.add(types.InlineKeyboardButton("❌ فرار می‌کنم", callback_data=f"flee_{attacker_id}_{target_id}_{ability_id}_{char_id}"))
    
    text = f"⚠️ **هشدار حمله!**\n\nیک کاربر با Ability **{ab_name}** به شما حمله کرده!\nآیا می‌خواهید دفاع کنید؟"
    try:
        bot.send_message(target_id, text, reply_markup=markup, parse_mode='Markdown')
        bot.send_message(chat_id, f"🛡 به {target_id} پیام دفاع ارسال شد.")
    except:
        bot.send_message(chat_id, "❌ نتونستم به حریف پیام بدم. باید حتماً بات رو استارت کرده باشه.")

def execute_attack(chat_id, attacker_id, target_id, ability_id, char_id, defense_ability_id=None, simple_defense=False):
    conn = db(); c = conn.cursor()
    c.execute("SELECT name_fa, power FROM abilities WHERE id=?", (ability_id,))
    atk_ab = c.fetchone()
    
    c.execute("SELECT name FROM characters WHERE id=?", (char_id,))
    attacker_char = c.fetchone()[0]
    
    target_slots = get_slots(target_id)
    if not target_slots: return
    target_char = random.choice(target_slots)
    target_char_name = target_char[2]
    
    def_power = 0
    if simple_defense:
        def_power = 30 # قدرت پایه دفاع ساده
    elif defense_ability_id:
        c.execute("SELECT name_fa, power FROM abilities WHERE id=?", (defense_ability_id,))
        def_ab = c.fetchone()
        def_power = def_ab[1]
    
    c.execute("SELECT name FROM users WHERE user_id=?", (target_id,))
    target_name = c.fetchone()[0]
    conn.close()
    
    energy_left, exhausted_until = consume_energy(attacker_id)
    
    atk_power = atk_ab[1] + random.randint(-10, 10)
    def_power_roll = def_power + random.randint(-10, 10)
    
    if atk_power > def_power_roll:
        res = "goal"
        pts = 10
        coins = 10
        text = f"⚽✨ **گل!!!** ✨⚽\n\n🎯 **{attacker_char}** با **{atk_ab[0]}** از **{target_name}** رد شد!\n\n💪 قدرت حمله: {atk_ab[1]} vs 🛡 دفاع: {def_power}\n🏆 +{pts} امتیاز | 🪙 +{coins} سکه"
    else:
        res = "save"
        pts = -5
        coins = 0
        text = f"🧤✨ **مهار!** ✨🧤\n\n🛡 **{target_name}** با کاراکتر **{target_char_name}** جلوی **{atk_ab[0]}** رو گرفت!\n\n💪 قدرت حمله: {atk_ab[1]} vs 🛡 دفاع: {def_power}\n🏆 {pts} امتیاز"
        
    if exhausted_until > 0: text += f"\n\n😵 **انرژی تموم شد!**"
        
    conn = db(); c = conn.cursor()
    c.execute("UPDATE users SET rank_points=rank_points+? WHERE user_id=?", (pts, attacker_id))
    if coins > 0:
        c.execute("UPDATE users SET coins=coins+? WHERE user_id=?", (coins, attacker_id))
    log_history(attacker_id, target_id, atk_ab[0], res, pts)
    
    if res == "goal":
        c.execute("UPDATE users SET goals=goals+1, game_goals=game_goals+1 WHERE user_id=?", (attacker_id,))
        c.execute("SELECT game_goals FROM users WHERE user_id=?", (attacker_id,)); gg = c.fetchone()[0]
    else:
        c.execute("UPDATE users SET saves=saves+1 WHERE user_id=?", (attacker_id,)); gg = 0
    conn.commit(); conn.close()
    set_ab_cd(attacker_id, ability_id)
    
    bot.send_message(chat_id, text, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    uid = call.from_user.id; data = call.data; chat_id = call.message.chat.id; msg_id = call.message.message_id
    
    parts = data.split("_")
    owner_uid = None
    try:
        if parts[-1].isdigit(): owner_uid = int(parts[-1])
    except: pass

    if owner_uid and uid != owner_uid:
        bot.answer_callback_query(call.id, "⛔ این منو مال تو نیست!", show_alert=True)
        return

    if data.startswith("atk_"):
        _, target_id, attacker_id, ability_id, char_id = data.split("_")
        if uid != int(attacker_id): return
        try: bot.delete_message(chat_id, msg_id)
        except: pass
        start_defense_phase(chat_id, int(attacker_id), int(target_id), int(ability_id), int(char_id))
        bot.answer_callback_query(call.id, "حمله آغاز شد!")
        return
        
    elif data.startswith("def_"):
        _, attacker_id, target_id, ability_id, char_id = data.split("_")
        if uid != int(target_id): return
            
        conn = db(); c = conn.cursor()
        c.execute("""SELECT a.id, a.name_fa FROM abilities a
                     JOIN character_abilities ca ON a.id = ca.ability_id
                     JOIN user_slots us ON ca.character_id = us.character_id
                     WHERE us.user_id = ? AND a.category = 'defend'""", (uid,))
        def_abs = c.fetchall(); conn.close()
        
        if not def_abs:
            try: bot.delete_message(chat_id, msg_id)
            except: pass
            bot.answer_callback_query(call.id, "شما Ability دفاعی نداشتید، دفاع ساده انجام شد!")
            execute_attack(chat_id, int(attacker_id), int(target_id), int(ability_id), int(char_id), simple_defense=True)
            return
            
        markup = types.InlineKeyboardMarkup(row_width=1)
        for ab in def_abs:
            markup.add(types.InlineKeyboardButton(ab[1], callback_data=f"execdef_{attacker_id}_{target_id}_{ability_id}_{char_id}_{ab[0]}"))
        bot.edit_message_text("🛡 **انتخاب Ability دفاعی:**", chat_id=chat_id, message_id=msg_id, reply_markup=markup)
        bot.answer_callback_query(call.id)
        
    elif data.startswith("execdef_"):
        _, attacker_id, target_id, ability_id, char_id, def_ab_id = data.split("_")
        if uid != int(target_id): return
        try: bot.delete_message(chat_id, msg_id)
        except: pass
        execute_attack(chat_id, int(attacker_id), int(target_id), int(ability_id), int(char_id), int(def_ab_id))
        bot.answer_callback_query(call.id)
        
    elif data.startswith("flee_"):
        _, attacker_id, target_id, ability_id, char_id = data.split("_")
        if uid != int(target_id): return
        try: bot.delete_message(chat_id, msg_id)
        except: pass
        execute_attack(chat_id, int(attacker_id), int(target_id), int(ability_id), int(char_id))
        bot.answer_callback_query(call.id, "فرار کردی و گل خوردی!")

    elif data.startswith("menu_slots"):
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
        bot.answer_callback_query(call.id)
    elif data.startswith("menu_profile"): show_profile(chat_id, uid, edit_msg_id=msg_id); bot.answer_callback_query(call.id)
    elif data.startswith("menu_history"): show_history(chat_id, uid, edit_msg_id=msg_id); bot.answer_callback_query(call.id)
    elif data.startswith("menu_shop"): show_shop(chat_id, uid, edit_msg_id=msg_id); bot.answer_callback_query(call.id)
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
        bot.answer_callback_query(call.id)
    elif data.startswith("menu_abilities"):
        abs_ = get_abilities(uid)
        t = "📖✨ **Abilityهای شما** ✨📖\n\n" if abs_ else "📖✨ Ability نداری! /slots"
        for a in abs_: t += f"• {a[2]} ({a[1]}) — ⏱{a[5]}s\n"
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 برگشت", callback_data=f"back_main_{uid}"))
        edit_to_text(chat_id, msg_id, t, markup)
        bot.answer_callback_query(call.id)
    elif data.startswith("back_main"): 
        show_main_menu(chat_id, uid, call.from_user.first_name, edit_msg_id=msg_id)
        bot.answer_callback_query(call.id)
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
        bot.answer_callback_query(call.id)
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
        bot.answer_callback_query(call.id)
    elif data.startswith("adm_charimg") and uid == OWNER_ID:
        conn = db(); c = conn.cursor(); c.execute("SELECT id,name FROM characters ORDER BY name ASC"); chars = c.fetchall(); conn.close()
        markup = types.InlineKeyboardMarkup(row_width=2)
        for ch in chars: markup.add(types.InlineKeyboardButton(ch[1], callback_data=f"setcimg_{ch[0]}_{uid}"))
        markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data=f"menu_admin_{uid}"))
        edit_to_text(chat_id, msg_id, "📸 **انتخاب کاراکتر برای گذاشتن عکس:**", markup)
        bot.answer_callback_query(call.id)
    elif data.startswith("setcimg_") and uid == OWNER_ID:
        _, cid, owner = data.split("_")
        admin_states[uid] = f"wait_charimg_{cid}"
        edit_to_text(chat_id, msg_id, "📸 **حالا عکس این کاراکتر رو بفرست:**")
        bot.answer_callback_query(call.id)
    elif data.startswith("adm_event") and uid == OWNER_ID:
        admin_states[uid] = "wait_event_title"
        edit_to_text(chat_id, msg_id, "🎉 **اسم رویداد رو بفرست:**\n(مثلاً: ریپ روی Rin ۲ برابر)")
        bot.answer_callback_query(call.id)
    elif data.startswith("adm_ban") and uid == OWNER_ID:
        admin_states[uid] = "wait_ban_id"
        edit_to_text(chat_id, msg_id, "🚫 **آیدی عددی کاربری که می‌خوای بن کنی رو بفرست:**")
        bot.answer_callback_query(call.id)
    elif data.startswith("adm_images") and uid == OWNER_ID:
        markup = types.InlineKeyboardMarkup(row_width=2)
        for k in ['welcome_banner','rank_bronze','rank_silver','rank_gold','rank_bluelock','rank_legend']:
            markup.add(types.InlineKeyboardButton(k, callback_data=f"imgset_{k}_{uid}"))
        markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data=f"menu_admin_{uid}"))
        edit_to_text(chat_id, msg_id, "🖼✨ انتخاب بنر ✨🖼", markup)
        bot.answer_callback_query(call.id)
    elif data.startswith("imgset_") and uid == OWNER_ID:
        _, key, owner = data.split("_")
        admin_states[uid] = f"wait_img_{key}"
        edit_to_text(chat_id, msg_id, f"🖼✨ {key} ✨🖼\n\n📌 عکس رو بفرست!")
        bot.answer_callback_query(call.id)

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