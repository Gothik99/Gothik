from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler, MessageHandler, Filters, CallbackQueryHandler
from database import Database
from keyboards import Keyboards
from config import Config
import os
import logging

# Состояния для ConversationHandler
PROJECT_ADDRESS, PROJECT_DESCRIPTION, PROJECT_DESIGN, PROJECT_LOCK_CODE = range(4)
BROADCAST_MESSAGE = range(1)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()

class AdminHandlers:
    @staticmethod
    def admin_menu(update: Update, context: CallbackContext):
        user = update.effective_user
        if user.id not in Config.ADMIN_IDS:
            update.message.reply_text("⛔ У вас нет доступа к этой команде.")
            return
        
        update.message.reply_text(
            "👨‍💻 Панель администратора",
            reply_markup=Keyboards.main_menu('admin')
        )
    
    @staticmethod
    def manage_workers(update: Update, context: CallbackContext):
        user = update.effective_user
        if user.id not in Config.ADMIN_IDS:
            update.message.reply_text("⛔ У вас нет доступа к этой команде.")
            return
        
        update.message.reply_text(
            "👥 Управление работниками",
            reply_markup=Keyboards.workers_management_keyboard()
        )
    
    @staticmethod
    def show_pending_workers(update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        
        pending_workers = db.get_pending_workers()
        if not pending_workers:
            query.edit_message_text("📭 Нет новых заявок на доступ.")
            return
        
        for worker in pending_workers:
            worker_info = (f"👤 {worker['first_name']} {worker['last_name']}\n"
                          f"📧 @{worker['username']}\n"
                          f"🆔 ID: {worker['user_id']}")
            
            query.edit_message_text(
                worker_info,
                reply_markup=Keyboards.worker_actions_keyboard(worker['user_id'])
            )
            break  # Показываем по одному, обработка через callback
    
    @staticmethod
    def handle_worker_approval(update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        
        action, worker_id = query.data.split('_')
        worker_id = int(worker_id)
        worker = db.get_user(worker_id)
        
        if action == 'approve':
            db.update_user_role(worker_id, 'worker')
            context.bot.send_message(
                worker_id,
                "✅ Ваш запрос на доступ одобрен!\nТеперь вы можете использовать все функции бота.",
                reply_markup=Keyboards.main_menu('worker')
            )
            query.edit_message_text(f"✅ Пользователь @{worker['username']} одобрен.")
        else:
            db.update_user_role(worker_id, 'rejected')
            context.bot.send_message(
                worker_id,
                "❌ Ваш запрос на доступ был отклонен администратором."
            )
            query.edit_message_text(f"❌ Пользователь @{worker['username']} отклонен.")
    
    @staticmethod
    def show_workers_list(update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        
        workers = db.get_all_workers()
        if not workers:
            query.edit_message_text("👷 Нет зарегистрированных работников.")
            return
        
        workers_list = "\n".join(
            [f"👤 {w['first_name']} {w['last_name']} (@{w['username']}) - 🆔 {w['user_id']}" 
             for w in workers]
        )
        
        query.edit_message_text(f"👷 Список работников:\n\n{workers_list}")
    
    @staticmethod
    def start_add_project(update: Update, context: CallbackContext):
        user = update.effective_user
        if user.id not in Config.ADMIN_IDS:
            update.message.reply_text("⛔ У вас нет доступа к этой команде.")
            return
        
        update.message.reply_text(
            "🏗 Введите адрес объекта:",
            reply_markup=Keyboards.back_keyboard()
        )
        return PROJECT_ADDRESS
    
    @staticmethod
    def get_project_address(update: Update, context: CallbackContext):
        context.user_data['project_address'] = update.message.text
        update.message.reply_text("📝 Введите описание проекта:")
        return PROJECT_DESCRIPTION
    
    @staticmethod
    def get_project_description(update: Update, context: CallbackContext):
        context.user_data['project_description'] = update.message.text
        update.message.reply_text("📎 Прикрепите PDF файл с дизайн-проектом:")
        return PROJECT_DESIGN
    
    @staticmethod
    def get_project_design(update: Update, context: CallbackContext):
        if not update.message.document or not update.message.document.file_name.endswith('.pdf'):
            update.message.reply_text("❌ Пожалуйста, прикрепите файл в формате PDF.")
            return PROJECT_DESIGN
        
        design_file = update.message.document
        design_path = os.path.join(Config.TEMP_DIR, design_file.file_name)
        
        os.makedirs(Config.TEMP_DIR, exist_ok=True)
        
        file = context.bot.get_file(design_file.file_id)
        file.download(design_path)
        
        context.user_data['project_design_path'] = design_path
        update.message.reply_text("🔑 Введите код доступа к замку:")
        return PROJECT_LOCK_CODE
    
    @staticmethod
    def get_project_lock_code(update: Update, context: CallbackContext):
        lock_code = update.message.text
        project_id = db.add_project(
            context.user_data['project_address'],
            context.user_data['project_description'],
            context.user_data['project_design_path'],
            lock_code,
            update.effective_user.id
        )
        
        update.message.reply_text(
            f"✅ Проект успешно добавлен (ID: {project_id})",
            reply_markup=Keyboards.main_menu('admin')
        )
        
        # Очистка временных данных
        context.user_data.clear()
        return ConversationHandler.END
    
    @staticmethod
    def cancel_project_creation(update: Update, context: CallbackContext):
        user = update.effective_user
        update.message.reply_text(
            "❌ Создание проекта отменено.",
            reply_markup=Keyboards.main_menu('admin')
        )
        
        # Удаление временных файлов
        if 'project_design_path' in context.user_data:
            try:
                os.remove(context.user_data['project_design_path'])
            except:
                pass
        
        context.user_data.clear()
        return ConversationHandler.END
    
    @staticmethod
    def show_projects_list(update: Update, context: CallbackContext):
        projects = db.get_projects()
        if not projects:
            update.message.reply_text("📭 Нет добавленных проектов.")
            return
        
        update.message.reply_text(
            "🏗 Выберите проект:",
            reply_markup=Keyboards.projects_keyboard(projects)
        )
    
    @staticmethod
    def show_project_details(update: Update, context: CallbackContext):
        project_address = update.message.text[2:]  # Убираем эмодзи
        projects = db.get_projects()
        
        for project in projects:
            if project['address'] == project_address:
                message = (f"🏠 Адрес: {project['address']}\n"
                          f"📅 Дата создания: {project['created_at']}\n"
                          f"👤 Ответственный: {project['first_name']} {project['last_name']}\n"
                          f"📝 Описание: {project['description']}")
                
                update.message.reply_text(
                    message,
                    reply_markup=Keyboards.project_details_keyboard(project['project_id'])
                )
                break
    
    @staticmethod
    def project_details_callback(update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        
        action, project_id = query.data.split('_')
        project = db.get_project(project_id)
        
        if action == 'design':
            try:
                with open(project['design_pdf_path'], 'rb') as file:
                    context.bot.send_document(
                        chat_id=query.message.chat_id,
                        document=file,
                        caption=f"📄 Дизайн-проект для {project['address']}"
                    )
            except Exception as e:
                logger.error(f"Error sending design file: {e}")
                query.edit_message_text("❌ Ошибка при загрузке файла.")
        
        elif action == 'lock':
            query.edit_message_text(f"🔑 Код замка для {project['address']}: {project['lock_code']}")
        
        elif action == 'calculations':
            calculations = db.get_user_calculations(project['created_by'])
            if not calculations:
                query.edit_message_text("📭 Нет расчетов для этого проекта.")
                return
            
            calc_list = "\n".join(
                [f"🧱 {c['material_type']} - {c['quantity']} {Config.MATERIALS[c['material_type'].lower()]['unit']} (Площадь: {c['area']} м²)"
                 for c in calculations if c['project_id'] == int(project_id)]
            )
            
            query.edit_message_text(f"📊 Расчеты для {project['address']}:\n\n{calc_list}")
    
    @staticmethod
    def start_broadcast(update: Update, context: CallbackContext):
        user = update.effective_user
        if user.id not in Config.ADMIN_IDS:
            update.message.reply_text("⛔ У вас нет доступа к этой команде.")
            return
        
        update.message.reply_text(
            "📢 Введите сообщение для рассылки всем работникам:",
            reply_markup=Keyboards.back_keyboard()
        )
        return BROADCAST_MESSAGE
    
    @staticmethod
    def confirm_broadcast(update: Update, context: CallbackContext):
        context.user_data['broadcast_message'] = update.message.text
        update.message.reply_text(
            f"📢 Сообщение для рассылки:\n\n{update.message.text}\n\nОтправить?",
            reply_markup=Keyboards.broadcast_confirmation_keyboard()
        )
        return ConversationHandler.END
    
    @staticmethod
    def send_broadcast(update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        
        if query.data == 'broadcast_confirm':
            workers = db.get_all_workers()
            message = context.user_data['broadcast_message']
            
            success = 0
            failed = 0
            
            for worker in workers:
                try:
                    context.bot.send_message(worker['user_id'], f"📢 Сообщение от администратора:\n\n{message}")
                    success += 1
                except:
                    failed += 1
            
            query.edit_message_text(f"✅ Сообщение отправлено {success} работникам.\nНе удалось отправить: {failed}")
        
        elif query.data == 'broadcast_edit':
            query.edit_message_text("📢 Введите новое сообщение для рассылки:")
            return BROADCAST_MESSAGE
        else:
            query.edit_message_text("❌ Рассылка отменена.")
        
        context.user_data.clear()
    
    @staticmethod
    def cancel_broadcast(update: Update, context: CallbackContext):
        update.message.reply_text(
            "❌ Рассылка отменена.",
            reply_markup=Keyboards.main_menu('admin')
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    @staticmethod
    def show_messages(update: Update, context: CallbackContext):
        user = update.effective_user
        messages = db.get_user_messages(user.id)
        
        if not messages:
            update.message.reply_text("📭 У вас нет новых сообщений.")
            return
        
        for msg in messages[:5]:  # Показываем последние 5 сообщений
            update.message.reply_text(f"📩 От {msg['sender_name']}:\n\n{msg['text']}")