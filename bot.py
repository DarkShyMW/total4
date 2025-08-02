# Обновленный bot.py
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

TOKEN = "7711849755:AAHvzB4Y0j80mBoy-r7yhEvnPwu_l_BR5PY"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Управление художниками", callback_data='manage_artists')],
        [InlineKeyboardButton("Последние регистрации", callback_data='recent_signups')],
        [InlineKeyboardButton("Статистика", callback_data='stats')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        '👋 Привет! Я бот платформы ArtPlatform.\n\n'
        'Я буду отправлять вам уведомления и помогать управлять платформой.',
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'manage_artists':
        # Здесь будет логика получения художников
        await query.edit_message_text("Функция в разработке...")
    elif query.data == 'recent_signups':
        # Здесь будет логика получения последних регистраций
        await query.edit_message_text("Последние регистрации:\n\n1. ArtistFox - 5 мин назад\n2. WolfPainter - 15 мин назад")
    elif query.data == 'stats':
        # Здесь будет статистика
        await query.edit_message_text("Статистика платформы:\n\nХудожники: 42\nКлиенты: 128\nЗаказы: 56")

async def notify_new_user(context: ContextTypes.DEFAULT_TYPE, user_data: dict):
    """Отправка уведомления о новом пользователе"""
    message = (
        f"🆕 Новый {user_data['role']}!\n\n"
        f"Имя: {user_data['username']}\n"
        f"Email: {user_data['email']}\n"
        f"Специализация: {user_data['species']}"
    )
    
    if user_data['role'] == 'artist':
        message += f"\nСтиль: {user_data['style']}"
    
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text=message
    )

def main():
    token = os.getenv('TELEGRAM_BOT_TOKEN', TOKEN)
    application = Application.builder().token(token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    application.run_polling()

if __name__ == '__main__':
    main()