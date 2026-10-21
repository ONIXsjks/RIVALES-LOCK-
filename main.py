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

def show_main_menu(chat_id, uid, name, edit_msg_id=None):
    user = get_user(uid)
    rank, max_energy = get_rank(user[2])
    energy = user[8] if user[8] is not None else max_energy
    text = f"🎮✨ **Blue Lock Bot** ✨🎮\n\n👋 سلام {name}!\n🏆 رنک: {rank} ({user[2]} امتیاز)\n⚡ انرژی: {energy}/{max_energy}\n"
    if user[9] and user[9] > time.time(): text += f"😵 خسته (تا {int(user[9]-time.time())} ثانیه)\n"
    
    ev = get_active_event()
    if ev: text += f"\n🎉 **رویداد فعال:** {ev[1]}\n"
        
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("🛡 اسلات‌های من", callback_data="menu_slots"), types.InlineKeyboardButton("👤 پروفایل من", callback_data="menu_profile"))
    markup.add(types.InlineKeyboardButton("🛒 فروشگاه Ability", callback_data="menu_shop"), types.InlineKeyboardButton("📖 Abilityهای من", callback_data="menu_abilities"))
    markup.add(types.InlineKeyboardButton("🏆 لیدربورد", callback_data="menu_top"), types.InlineKeyboardButton("📜 تاریخچه", callback_data="menu_history"))
    if uid == OWNER_ID: markup.add(types.InlineKeyboardButton("👑 پنل مالک", callback_data="menu_admin"))
        
    banner = get_image('welcome_banner')
    if edit_msg_id:
        try:
            if banner: bot.edit_message_caption(caption=text, chat_id=chat_id, message_id=edit_msg_id, reply_markup=markup, parse_mode='Markdown')
            else: bot.edit_message_text(text, chat_id=chat_id, message_id=edit_msg_id, reply_markup=markup, parse_mode='Markdown')
        except: pass
    else:
        if banner: bot.send_photo(chat_id, banner, caption=text, reply_markup=markup, parse_mode='Markdown')
        else: bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id; name = message.from_user.first_name
    if is_banned(uid): bot.reply_to(message, "🚫✨ دسترسی مسدود! ✨🚫"); return
    if not get_user(uid):
        conn = db(); c = conn.cursor(); c.execute("INSERT INTO users (user_id,name) VALUES (?,?)", (uid, name)); conn.commit(); conn.close()
    show_main_menu(message.chat.id, uid, name)

@bot.message_handler(commands=['slots'])
def slots_cmd(message, edit_msg_id=None):
    uid = message.from_user.id
    slots = get_slots(uid)
    text = "🛡✨ **اسلات‌های کاراکتر شما** ✨🛡\n\n"
    for i in range(1,4):
        s = next((x for x in slots if x[0]==i), None)
        text += f"{i}️⃣ {s[2] if s else '⚪ خالی'}\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i in range(1,4):
        s = next((x for x in slots if x[0]==i), None)
        label = f"🔄 تغییر اسلات {i} ({s[2][:12]})" if s else f"➕ افزودن به اسلات {i}"
        markup.add(types.InlineKeyboardButton(label, callback_data=f"editslot_{i}"))
    markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data="back_main"))
    
    if edit_msg_id: bot.edit_message_text(text, chat_id=message.chat.id, message_id=edit_msg_id, reply_markup=markup)
    else: bot.send_message(message.chat.id, text, reply_markup=markup)

def show_profile(chat_id, uid, edit_msg_id=None):
    u = get_user(uid)
    slots = get_slots(uid)
    rank, max_energy = get_rank(u[2])
    energy = u[8] if u[8] is not None else max_energy
    
    text = f"👤✨ **پروفایل {u[1]}** ✨👤\n\n🏆 رنک: {rank} ({u[2]} امتیاز)\n⚡ انرژی: {energy}/{max_energy}\n⚽ گل‌ها: {u[3]}\n🧤 مهارها: {u[4]}\n\n🎭 **کاراکترهای شما:**\n"
    if not slots: text += "⚪ هنوز کاراکتری انتخاب نکردی!"
    else:
        for s in slots: text += f"• {s[2]}\n"
    
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 برگشت", callback_data="back_main"))
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
    
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 برگشت", callback_data="back_main"))
    if edit_msg_id: bot.edit_message_text(text, chat_id=chat_id, message_id=edit_msg_id, reply_markup=markup, parse_mode='Markdown')
    else: bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')

def show_shop(chat_id, uid, edit_msg_id=None):
    u = get_user(uid)
    text = f"🛒✨ **فروشگاه Ability** ✨🛒\n\n💰 امتیاز شما: {u[2]}\n\n📌 Ability مورد نظر رو بخر:"
    
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
        text = "🛒✨ **فروشگاه** ✨🛒\n\n👀 هیچ Ability جدیدی برای کاراکترهای شما نیست! (همه رو داری یا کاراکترهات Ability جدیدی ندارن)."
    else:
        for ab in shop_abs:
            markup.add(types.InlineKeyboardButton(f"{ab[1]} ({ab[2]}💰)", callback_data=f"buy_{ab[0]}_{ab[2]}"))
            
    markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data="back_main"))
    
    if edit_msg_id: bot.edit_message_text(text, chat_id=chat_id, message_id=edit_msg_id, reply_markup=markup, parse_mode='Markdown')
    else: bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.reply_to_message is not None)
def handle_reply(message):
    uid = message.from_user.id
    if is_banned(uid): return
    
    target_user = message.reply_to_message.from_user
    if target_user.id == uid or target_user.is_bot: return 
    
    status, msg = check_rip_status(uid)
    if not status: bot.reply_to(message, msg); return
        
    abilities = get_abilities(uid)
    if not abilities: bot.reply_to(message, "❌ Ability نداری! /slots"); return
        
    ab = find_ability(message.text, abilities)
    if not ab: bot.reply_to(message, "❌✨ Ability پیدا نشد! ✨❌\n📖 /abilities"); return
        
    cd = ab_cd(uid, ab[0])
    if cd > 0: bot.reply_to(message, f"⏳ {ab[2]} — {cd} ثانیه کول‌داون داره!"); return
        
    target_slots = get_slots(target_user.id)
    if not target_slots:
        bot.reply_to(message, f"❌ {target_user.first_name} هنوز کاراکتر انتخاب نکرده!"); return

    user_slots = get_slots(uid)
    markup = types.InlineKeyboardMarkup(row_width=1)
    for slot in user_slots:
        markup.add(types.InlineKeyboardButton(f"⚔ {slot[2]}", callback_data=f"attack_{uid}_{target_user.id}_{ab[0]}_{slot[1]}"))
    
    text = f"🎯 **انتخاب مهاجم**\n\nشما می‌خواهید با Ability **{ab[2]}** به {target_user.first_name} حمله کنید.\nبا کدوم کاراکترت حمله می‌کنی؟"
    bot.reply_to(message, text, reply_markup=markup, parse_mode='Markdown')

def execute_attack(chat_id, attacker_id, target_id, ability_id, char_id):
    conn = db(); c = conn.cursor()
    c.execute("SELECT name_fa, name_en, power FROM abilities WHERE id=?", (ability_id,))
    ab = c.fetchone()
    
    c.execute("SELECT name FROM characters WHERE id=?", (char_id,))
    attacker_char = c.fetchone()[0]
    
    target_slots = get_slots(target_id)
    if not target_slots: return
    target_char = random.choice(target_slots)
    
    c.execute("SELECT defense FROM characters WHERE id=?", (target_char[1],))
    defense = c.fetchone()[0]
    
    c.execute("SELECT name FROM users WHERE user_id=?", (target_id,))
    target_name = c.fetchone()[0]
    conn.close()
    
    multiplier = 1.0
    ev = get_active_event()
    if ev:
        if ev[2] == "global": multiplier = ev[4]
        elif ev[2] == "attack" and target_char[1] == ev[3]: multiplier = ev[4]
        elif ev[2] == "ability" and ability_id == ev[3]: multiplier = ev[4]
    
    energy_left, exhausted_until = consume_energy(attacker_id)
    res, diff = simulate(ab[2], defense)
    
    if res == "goal":
        base_pts = 10 if diff > 20 else 7
        pts = int(base_pts * multiplier)
        text = f"⚽✨ **گل!!!** ✨⚽\n\n🎯 با **{attacker_char}** و **{ab[0]}** از **{target_char[2]}** (مال {target_name}) رد شدی!\n\n💪 قدرت: {ab[2]} vs 🛡 دفاع: {defense}\n🏆 +{pts} امتیاز"
    else:
        pts = int(-5 * multiplier)
        text = f"🧤✨ **مهار!** ✨🧤\n\n🛡 **{target_char[2]}** (مال {target_name}) جلوی **{ab[0]}** رو گرفت!\n\n💪 قدرت: {ab[2]} vs 🛡 دفاع: {defense}\n🏆 {pts} امتیاز"
        
    if multiplier > 1.0: text += f"\n🎉 (رویداد: {multiplier}x)"
    if exhausted_until > 0: text += f"\n\n😵 **انرژی تموم شد!**\n⏱ باید ۲ دقیقه استراحت کنی."
        
    conn = db(); c = conn.cursor()
    c.execute("UPDATE users SET rank_points=rank_points+? WHERE user_id=?", (pts, attacker_id))
    log_history(attacker_id, target_id, ab[1], res, pts)
    
    if res == "goal":
        c.execute("UPDATE users SET goals=goals+1, game_goals=game_goals+1 WHERE user_id=?", (attacker_id,))
        c.execute("SELECT game_goals FROM users WHERE user_id=?", (attacker_id,)); gg = c.fetchone()[0]
    else:
        c.execute("UPDATE users SET saves=saves+1 WHERE user_id=?", (attacker_id,)); gg = 0
    conn.commit(); conn.close()
    set_ab_cd(attacker_id, ability_id)
    
    if res == "goal" and gg >= MAX_GOALS:
        text += f"\n\n🎉✨ بازی تموم شد! {MAX_GOALS} گل زدی! ✨🎉"
        conn = db(); c = conn.cursor(); c.execute("UPDATE users SET game_goals=0 WHERE user_id=?", (attacker_id,)); conn.commit(); conn.close()
        
    bot.send_message(chat_id, text, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    uid = call.from_user.id; data = call.data; chat_id = call.message.chat.id; msg_id = call.message.message_id
    
    # 🔒 قفل امنیتی: فقط صاحب منو می‌تونه دکمه‌ها رو بزنه
    if data.startswith("attack_"):
        _, attacker_id, target_id, ability_id, char_id = data.split("_")
        if uid != int(attacker_id):
            bot.answer_callback_query(call.id, "⛔ این منو مال تو نیست!", show_alert=True)
            return
        bot.edit_message_text("⏳ در حال شبیه‌سازی...", chat_id=chat_id, message_id=msg_id)
        execute_attack(chat_id, uid, int(target_id), int(ability_id), int(char_id))
        bot.answer_callback_query(call.id)
        return
        
    # برای بقیه دکمه‌ها (منوها)، چون از chat_id استفاده می‌کنیم، نیازی به قفل نیست مگر اینکه بخوایم.
    if data == "menu_slots": slots_cmd(call.message, edit_msg_id=msg_id); bot.answer_callback_query(call.id)
    elif data == "menu_profile": show_profile(chat_id, uid, edit_msg_id=msg_id); bot.answer_callback_query(call.id)
    elif data == "menu_history": show_history(chat_id, uid, edit_msg_id=msg_id); bot.answer_callback_query(call.id)
    elif data == "menu_shop": show_shop(chat_id, uid, edit_msg_id=msg_id); bot.answer_callback_query(call.id)
    elif data.startswith("buy_"):
        _, aid, price = data.split("_")
        aid = int(aid); price = int(price)
        u = get_user(uid)
        if u[2] < price:
            bot.answer_callback_query(call.id, "❌ امتیاز کافی نداری!", show_alert=True)
        else:
            conn = db(); c = conn.cursor()
            c.execute("UPDATE users SET rank_points=rank_points-? WHERE user_id=?", (price, uid))
            c.execute("INSERT OR IGNORE INTO user_abilities (user_id,ability_id) VALUES (?,?)", (uid, aid))
            conn.commit(); conn.close()
            bot.answer_callback_query(call.id, "✅ Ability خریداری شد!", show_alert=True)
            show_shop(chat_id, uid, edit_msg_id=msg_id)
    elif data == "menu_top":
        conn = db(); c = conn.cursor(); c.execute("SELECT name,rank_points FROM users ORDER BY rank_points DESC LIMIT 10"); top = c.fetchall(); conn.close()
        t = "🏆✨ **لیدربورد** ✨🏆\n\n"
        for i,(n,p) in enumerate(top,1):
            m = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}️⃣"
            t += f"{m} {n}: {p}\n"
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 برگشت", callback_data="back_main"))
        bot.edit_message_text(t, chat_id=chat_id, message_id=msg_id, reply_markup=markup, parse_mode='Markdown')
        bot.answer_callback_query(call.id)
    elif data == "menu_abilities":
        abs_ = get_abilities(uid)
        t = "📖✨ **Abilityهای شما** ✨📖\n\n" if abs_ else "📖✨ Ability نداری! /slots"
        for a in abs_: t += f"• {a[2]} ({a[1]}) — ⏱{a[5]}s\n"
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 برگشت", callback_data="back_main"))
        bot.edit_message_text(t, chat_id=chat_id, message_id=msg_id, reply_markup=markup, parse_mode='Markdown')
        bot.answer_callback_query(call.id)
    elif data == "back_main": 
        show_main_menu(chat_id, uid, call.from_user.first_name, edit_msg_id=msg_id)
        bot.answer_callback_query(call.id)
    elif data.startswith("editslot_"):
        sn = int(data.split("_")[1])
        conn = db(); c = conn.cursor(); c.execute("SELECT id,name FROM characters ORDER BY name ASC"); chars = c.fetchall(); conn.close()
        markup = types.InlineKeyboardMarkup(row_width=2)
        for ch in chars: markup.add(types.InlineKeyboardButton(ch[1], callback_data=f"setchar_{sn}_{ch[0]}"))
        markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data="back_main"))
        bot.edit_message_text(f"🎯 انتخاب برای اسلات {sn}", chat_id=chat_id, message_id=msg_id, reply_markup=markup)
        bot.answer_callback_query(call.id)
    elif data.startswith("setchar_"):
        _, sn, cid = data.split("_")
        conn = db(); c = conn.cursor(); c.execute("INSERT OR REPLACE INTO user_slots (user_id,slot_number,character_id) VALUES (?,?,?)", (uid, int(sn), int(cid))); conn.commit(); conn.close()
        bot.answer_callback_query(call.id, "✅ کاراکتر انتخاب شد!")
        slots_cmd(call.message, edit_msg_id=msg_id)
    
    # 👑 پنل ادمین
    elif data == "menu_admin" and uid == OWNER_ID:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("🖼 عکس بنرها", callback_data="adm_images"), types.InlineKeyboardButton("📸 عکس کاراکترها", callback_data="adm_charimg"))
        markup.add(types.InlineKeyboardButton("🎉 ساخت رویداد", callback_data="adm_event"), types.InlineKeyboardButton("🚫 بن کاربر", callback_data="adm_ban"))
        markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data="back_main"))
        bot.edit_message_text("👑✨ **پنل مالک** ✨👑", chat_id=chat_id, message_id=msg_id, reply_markup=markup)
        bot.answer_callback_query(call.id)
    elif data == "adm_charimg" and uid == OWNER_ID:
        conn = db(); c = conn.cursor(); c.execute("SELECT id,name FROM characters ORDER BY name ASC"); chars = c.fetchall(); conn.close()
        markup = types.InlineKeyboardMarkup(row_width=2)
        for ch in chars: markup.add(types.InlineKeyboardButton(ch[1], callback_data=f"setcimg_{ch[0]}"))
        markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data="menu_admin"))
        bot.edit_message_text("📸 **انتخاب کاراکتر برای گذاشتن عکس:**", chat_id=chat_id, message_id=msg_id, reply_markup=markup)
        bot.answer_callback_query(call.id)
    elif data.startswith("setcimg_") and uid == OWNER_ID:
        cid = int(data.split("_")[1])
        admin_states[uid] = f"wait_charimg_{cid}"
        bot.edit_message_text("📸 **حالا عکس این کاراکتر رو بفرست:**", chat_id=chat_id, message_id=msg_id)
        bot.answer_callback_query(call.id)
    elif data == "adm_event" and uid == OWNER_ID:
        admin_states[uid] = "wait_event_title"
        bot.edit_message_text("🎉 **اسم رویداد رو بفرست:**\n(مثلاً: ریپ روی Rin ۲ برابر)", chat_id=chat_id, message_id=msg_id)
        bot.answer_callback_query(call.id)
    elif data == "adm_ban" and uid == OWNER_ID:
        admin_states[uid] = "wait_ban_id"
        bot.edit_message_text("🚫 **آیدی عددی کاربری که می‌خوای بن کنی رو بفرست:**", chat_id=chat_id, message_id=msg_id)
        bot.answer_callback_query(call.id)
    elif data == "adm_images" and uid == OWNER_ID:
        markup = types.InlineKeyboardMarkup(row_width=2)
        for k in ['welcome_banner','rank_bronze','rank_silver','rank_gold','rank_bluelock','rank_legend']:
            markup.add(types.InlineKeyboardButton(k, callback_data=f"imgset_{k}"))
        markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data="menu_admin"))
        bot.edit_message_text("🖼✨ انتخاب بنر ✨🖼", chat_id=chat_id, message_id=msg_id, reply_markup=markup)
        bot.answer_callback_query(call.id)
    elif data.startswith("imgset_") and uid == OWNER_ID:
        key = data.replace("imgset_", "")
        admin_states[uid] = f"wait_img_{key}"
        bot.edit_message_text(f"🖼✨ {key} ✨🖼\n\n📌 عکس رو بفرست!", chat_id=chat_id, message_id=msg_id)
        bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    uid = message.from_user.id
    state = admin_states.get(uid)
    if state:
        if state.startswith("wait_img_"):
            key = state.replace("wait_img_", "")
            set_image(key, message.photo[-1].file_id, uid)
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