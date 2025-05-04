from telegram import Update
from telegram.ext import CallbackContext
from database import Database
from keyboards import Keyboards

db = Database()

class SharedHandlers:
    @staticmethod
    def start(update: Update, context: CallbackContext):
        user = update.effective_user
        user_data = db.get_user(user.id)
        
        if not user_data:
            db.add_user(user.id, user.username, user.first_name, user.last_name)
            user_data = db.get_user(user.id)
        
        if user.id in Config.ADMIN_IDS:
            db.update_user_role(user.id, 'admin')
            role = 'admin'
        else:
            role = user_data['role'] if user_data else 'pending'
        
        welcome_text = (
            f"👋 Добро пожаловать, {user.first_name}!\n\n"
            "🏗 Это бот для компании по внутренней отделке помещений.\n"
            "Здесь вы можете рассчитывать материалы, просматривать проекты и общаться с коллегами."
        )
        
        update.message.reply_text(
            welcome_text,
            reply_markup=Keyboards.main_menu(role)
        )
    
    @staticmethod
    def help(update: Update, context: CallbackContext):
        help_text = (
            "ℹ️ Список доступных команд:\n\n"
            "/start - Главное меню\n"
            "/help - Эта справка\n"
            "/message [текст] - Отправить сообщение администратору (для работников)\n\n"
            "📊 Калькулятор материалов - расчет необходимого количества материалов\n"
            "🏗 Проекты - просмотр текущих проектов\n"
            "👥 Работники - управление доступом (для администраторов)\n"
            "📢 Рассылка - отправить сообщение всем работникам (для администраторов)\n"
            "📩 Сообщения - просмотр полученных сообщений"
        )
        
        update.message.reply_text(help_text)
    
    @staticmethod
    def cancel(update: Update, context: CallbackContext):
        user = update.effective_user
        user_data = db.get_user(user.id)
        role = user_data['role'] if user_data else 'pending'
        
        update.message.reply_text(
            "🚫 Текущее действие отменено.",
            reply_markup=Keyboards.main_menu(role)
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    @staticmethod
    def back_to_menu(update: Update, context: CallbackContext):
        user = update.effective_user
        user_data = db.get_user(user.id)
        role = user_data['role'] if user_data else 'pending'
        
        update.message.reply_text(
            "🏠 Главное меню",
            reply_markup=Keyboards.main_menu(role)
        )
        context.user_data.clear()