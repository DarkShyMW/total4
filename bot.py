# bot.py - Telegram бот для уведомлений
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
TOKEN = "7711849755:AAHvzB4Y0j80mBoy-r7yhEvnPwu_l_BR5PY"
# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет приветственное сообщение при команде /start"""
    await update.message.reply_text(
        '👋 Привет! Я бот платформы ArtPlatform.\n\n'
        'Я буду отправлять вам уведомления о:\n'
        '- Новых заказах\n'
        '- Отзывах на ваши работы\n'
        '- Обновлениях в проектах\n\n'
        'Просто держите этот чат активным, и вы будете получать важные уведомления!'
    )

async def notify_new_order(context: ContextTypes.DEFAULT_TYPE, order_details: str):
    """Отправляет уведомление о новом заказе"""
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text=f"🆕 Новый заказ!\n\n{order_details}"
    )

def main():
    """Запуск бота"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logging.error("Токен Telegram бота не установлен!")
        return
    
    application = Application.builder().token(token).build()
    
    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    
    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()