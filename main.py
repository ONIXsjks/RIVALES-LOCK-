import telebot
from telebot import types
import time
import random
from config import TOKEN, OWNER_ID, MAX_GOALS
from database import init_db, seed, db
from utils import (
    get_rank, is_banned, get_user, get_slots, get_abilities,
    check_rip_status, consume_energy, ab_cd, set_ab_cd,
    find_ability, simulate, get_image, set_image
)
import migration

bot = telebot.TeleBot(TOKEN)
admin_states = {}

def show_main_menu(chat_id, uid, name, edit_msg_id=None):
    user = get_user(uid)
    rank = get_rank(user[2])
    energy = user[8] if user[8] is not None else 100
    text = f"🎮✨ **Blue Lock Bot** ✨🎮\n\n👋 سلام {name}!\n🏆 رنک: {rank} ({user[2]} امتیاز)\n⚡ انرژی: {energy}/100\n"
    if user[9] and user[9] > time.time(): text += f"😵 خسته (تا {int(user[9]-time.time())} ثانیه)\n"
    text += "\n📌 **چطور بازی کنیم؟**\n1️⃣ اول ۳ تا کاراکتر برای خودت انتخاب کن.\n2️⃣ بعد برو توی گروه و روی پیام یه کاربر دیگه Reply بزن و اسم Ability رو بنویس!\n"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("🛡 اسلات‌های من", callback_data="menu_slots"), types.InlineKeyboardButton("📊 آمار من", callback_data="menu_stats"))
    markup.add(types.InlineKeyboardButton("🏆 لیدربورد", callback_data="menu_top"), types.InlineKeyboardButton("📖 Abilityها", callback_data="menu_abilities"))
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
def slots_cmd(message):
    uid = message.from_user.id
    slots = get_slots(uid)
    text = "🛡✨ **اسلات‌های کاراکتر** ✨🛡\n\n"
    for i in range(1,4): # فقط ۳ اسلات
        s = next((x for x in slots if x[0]==i), None)
        text += f"{i}️⃣ {s[2] if s else '⚪ خالی'}\n"
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    for i in range(1,4):
        s = next((x for x in slots if x[0]==i), None)
        label = f"{i}️⃣ {s[2][:10]}" if s else f"{i}️⃣ ➕"
        markup.add(types.InlineKeyboardButton(label, callback_data=f"editslot_{i}"))
    markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data="back_main"))
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(func=lambda m: m.reply_to_message is not None)
def handle_reply(message):
    uid = message.from_user.id
    if is_banned(uid): return
    
    target_user = message.reply_to_message.from_user
    if target_user.id == uid or target_user.is_bot: return 
    
    status, msg = check_rip_status(uid)
    if not status: bot.reply_to(message, msg); return
        
    abilities = get_abilities(uid)
    if not abilities: bot.reply_to(message, "❌ Ability نداری! اول /slots رو بزن و کاراکتر انتخاب کن."); return
        
    ab = find_ability(message.text, abilities)
    if not ab: bot.reply_to(message, "❌✨ Ability پیدا نشد! ✨❌\n📖 /abilities"); return
        
    cd = ab_cd(uid, ab[0])
    if cd > 0: bot.reply_to(message, f"⏳ {ab[2]} — {cd} ثانیه کول‌داون داره!"); return
        
    target_slots = get_slots(target_user.id)
    if not target_slots:
        bot.reply_to(message, f"❌ {target_user.first_name} هنوز کاراکتر انتخاب نکرده! بگو اول /slots رو بزنه."); return

    # ✨ اینجا کاربر باید انتخاب کنه با کدوم کاراکترش حمله کنه
    user_slots = get_slots(uid)
    markup = types.InlineKeyboardMarkup(row_width=1)
    for slot in user_slots:
        markup.add(types.InlineKeyboardButton(f"⚔ {slot[2]}", callback_data=f"attack_{target_user.id}_{ab[0]}_{slot[1]}"))
    
    text = f"🎯 **انتخاب مهاجم**\n\nشما می‌خواهید با Ability **{ab[2]}** به {target_user.first_name} حمله کنید.\nبا کدوم کاراکترت حمله می‌کنی؟"
    bot.reply_to(message, text, reply_markup=markup, parse_mode='Markdown')

def execute_attack(chat_id, attacker_id, target_id, ability_id, char_id):
    conn = db(); c = conn.cursor()
    
    # گرفتن اطلاعات Ability
    c.execute("SELECT name_fa, name_en, power FROM abilities WHERE id=?", (ability_id,))
    ab = c.fetchone()
    
    # گرفتن اطلاعات کاراکتر مهاجم و مدافع
    c.execute("SELECT name FROM characters WHERE id=?", (char_id,))
    attacker_char = c.fetchone()[0]
    
    target_slots = get_slots(target_id)
    if not target_slots: return "❌ هدف کاراکتر ندارد."
    target_char = random.choice(target_slots) # رندوم از ۳ کاراکتر هدف
    
    c.execute("SELECT defense FROM characters WHERE id=?", (target_char[1],))
    defense = c.fetchone()[0]
    
    # گرفتن اسم هدف
    c.execute("SELECT name FROM users WHERE user_id=?", (target_id,))
    target_name = c.fetchone()[0]
    conn.close()
    
    energy_left, exhausted_until = consume_energy(attacker_id)
    res, diff = simulate(ab[2], defense)
    
    if res == "goal":
        pts = 10 if diff > 20 else 7
        text = f"⚽✨ **گل!!!** ✨⚽\n\n🎯 با کاراکتر **{attacker_char}** و Ability **{ab[0]} ({ab[1]})** از **{target_char[2]}** (مال {target_name}) رد شدی!\n\n💪 قدرت: {ab[2]} vs 🛡 دفاع: {defense}\n🏆 +{pts} امتیاز\n⚡ انرژی: {energy_left}/100"
    else:
        pts = -5
        text = f"🧤✨ **مهار!** ✨🧤\n\n🛡 کاراکتر **{target_char[2]}** (مال {target_name}) جلوی **{ab[0]}** رو گرفت!\n\n💪 قدرت: {ab[2]} vs 🛡 دفاع: {defense}\n🏆 {pts} امتیاز\n⚡ انرژی: {energy_left}/100"
        
    if exhausted_until > 0: text += f"\n\n😵 **انرژی تموم شد!**\n⏱ باید ۲ دقیقه استراحت کنی."
        
    conn = db(); c = conn.cursor()
    c.execute("UPDATE users SET rank_points=rank_points+? WHERE user_id=?", (pts, attacker_id))
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
    
    if data == "menu_slots": 
        slots_cmd(call.message)
        bot.answer_callback_query(call.id)
    elif data.startswith("attack_"):
        _, target_id, ability_id, char_id = data.split("_")
        bot.edit_message_text("⏳ در حال شبیه‌سازی...", chat_id=chat_id, message_id=msg_id)
        execute_attack(chat_id, uid, int(target_id), int(ability_id), int(char_id))
        bot.answer_callback_query(call.id)
    elif data == "menu_stats":
        u = get_user(uid)
        energy = u[8] if u[8] is not None else 100
        t = f"📊✨ **آمار شما** ✨📊\n\n👤 {u[1]}\n🏆 {get_rank(u[2])} ({u[2]})\n⚽ {u[3]}\n🧤 {u[4]}\n⚡ انرژی: {energy}/100"
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 برگشت", callback_data="back_main"))
        try: bot.edit_message_caption(caption=t, chat_id=chat_id, message_id=msg_id, reply_markup=markup, parse_mode='Markdown')
        except: bot.edit_message_text(t, chat_id=chat_id, message_id=msg_id, reply_markup=markup, parse_mode='Markdown')
        bot.answer_callback_query(call.id)
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
        bot.answer_callback_query(call.id, "✅ شد!")
        slots_cmd(call.message)
    elif data == "menu_admin" and uid == OWNER_ID:
        show_admin(call)
    elif data == "adm_stats" and uid == OWNER_ID:
        conn = db(); c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users"); uc = c.fetchone()[0]
        c.execute("SELECT SUM(goals) FROM users"); g = c.fetchone()[0] or 0
        conn.close()
        t = f"📊✨ آمار کلی ✨📊\n\n👥 {uc}\n⚽ {g}"
        bot.edit_message_text(t, chat_id=chat_id, message_id=msg_id)
        bot.answer_callback_query(call.id)
    elif data == "adm_images" and uid == OWNER_ID:
        markup = types.InlineKeyboardMarkup(row_width=2)
        for k in ['welcome_banner','rank_bronze','rank_silver','rank_gold','rank_bluelock','rank_legend','event_banner','profile_default']:
            markup.add(types.InlineKeyboardButton(k, callback_data=f"imgset_{k}"))
        bot.edit_message_text("🖼✨ انتخاب عکس ✨🖼", chat_id=chat_id, message_id=msg_id, reply_markup=markup)
        bot.answer_callback_query(call.id)
    elif data.startswith("imgset_") and uid == OWNER_ID:
        key = data.replace("imgset_", "")
        admin_states[uid] = f"wait_img_{key}"
        bot.edit_message_text(f"🖼✨ {key} ✨🖼\n\n📌 عکس رو بفرست!", chat_id=chat_id, message_id=msg_id)
        bot.answer_callback_query(call.id)

def show_admin(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("🖼 عکس‌ها", callback_data="adm_images"), types.InlineKeyboardButton("📊 آمار کلی", callback_data="adm_stats"))
    markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data="back_main"))
    bot.edit_message_text("👑✨ **پنل مالک** ✨👑", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    uid = message.from_user.id
    state = admin_states.get(uid)
    if state and state.startswith("wait_img_"):
        key = state.replace("wait_img_", "")
        set_image(key, message.photo[-1].file_id, uid)
        del admin_states[uid]
        bot.reply_to(message, f"✅✨ {key} ست شد! ✨✅")

if __name__ == "__main__":
    migration.migrate()
    init_db()
    seed()
    print("🚀✨ Blue Lock Bot روشن شد! ✨🚀")
    bot.infinity_polling()