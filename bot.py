import sqlite3
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes

# ========== SETUP DATABASE ==========
def setup_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_seen DATE,
            last_active DATE
        )
    ''')
    conn.commit()
    conn.close()

def add_or_update_user(user_id, username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    today = datetime.now().date()
    
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    exists = c.fetchone()
    
    if exists:
        c.execute('UPDATE users SET last_active = ? WHERE user_id = ?', (today, user_id))
    else:
        c.execute('INSERT INTO users (user_id, username, first_seen, last_active) VALUES (?, ?, ?, ?)',
                  (user_id, username, today, today))
    
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM users')
    total = c.fetchone()[0]
    
    c.execute('''
        SELECT COUNT(*) FROM users 
        WHERE last_active >= date('now', '-30 days')
    ''')
    monthly = c.fetchone()[0]
    
    conn.close()
    return total, monthly

# ========== HANDLER BOT ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_or_update_user(user.id, user.username)
    
    keyboard = [[InlineKeyboardButton("⛏ Buka CASHIFY", web_app=WebAppInfo(url="https://cashify-phi.vercel.app"))]]
    
    await update.message.reply_text(
        f"⛏ Halo {user.first_name}!\n\nKlik tombol di bawah untuk mulai menambang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total, monthly = get_stats()
    await update.message.reply_text(
        f"📊 *Statistik Bot*\n\n"
        f"👥 Total pengguna: *{total:,}*\n"
        f"📅 Monthly aktif (30 hari): *{monthly:,}*\n"
        f"_update: {datetime.now().strftime('%Y-%m-%d')}_",
        parse_mode='Markdown'
    )

async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total, _ = get_stats()
    await update.message.reply_text(f"Total user yang pernah pakai bot ini: {total} orang")

# ========== SETUP MENU COMMAND ==========
async def post_init(app: Application):
    await app.bot.set_my_commands([
        BotCommand("start", "⛏ Launch CASHIFY App"),
        BotCommand("stats", "📊 Lihat statistik pengguna"),
        BotCommand("users", "👥 Lihat total pengguna"),
    ])
    print("Menu command telah diatur!")

# ========== MAIN ==========
def main():
    setup_db()
    
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN tidak ditemukan di environment variables!")
    
    app = Application.builder().token(token).post_init(post_init).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("users", users))
    
    print("Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
