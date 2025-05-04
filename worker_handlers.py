from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler, MessageHandler, Filters
from database import Database
from keyboards import Keyboards
from calculations import MaterialCalculator
import logging

# Состояния для калькулятора
MATERIAL_TYPE, AREA, THICKNESS = range(3)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()

class WorkerHandlers:
    @staticmethod
    def request_access(update: Update, context: CallbackContext):
        user = update.effective_user
        user_data = db.get_user(user.id)
        
        if user_data and user_data['role'] != 'pending':
            update.message.reply_text(
                "⏳ Ваш запрос уже обрабатывается. Пожалуйста, дождитесь ответа администратора."
            )
            return
        
        db.add_user(user.id, user.username, user.first_name, user.last_name, 'pending')
        
        # Уведомление администраторов
        for admin_id in Config.ADMIN_IDS:
            try:
                context.bot.send_message(
                    admin_id,
                    f"🆕 Новый запрос на доступ:\n\n👤 {user.first_name} {user.last_name}\n📧 @{user.username}\n🆔 {user.id}",
                    reply_markup=Keyboards.worker_actions_keyboard(user.id)
                )
            except Exception as e:
                logger.error(f"Error notifying admin {admin_id}: {e}")
        
        update.message.reply_text(
            "✅ Ваш запрос на доступ отправлен администратору. Ожидайте подтверждения."
        )
    
    @staticmethod
    def start_calculation(update: Update, context: CallbackContext):
        update.message.reply_text(
            "🧮 Выберите материал:",
            reply_markup=Keyboards.materials_keyboard()
        )
        return MATERIAL_TYPE
    
    @staticmethod
    def get_material_type(update: Update, context: CallbackContext):
        material = update.message.text.lower()
        if material not in Config.MATERIALS:
            update.message.reply_text("❌ Пожалуйста, выберите материал из списка.")
            return MATERIAL_TYPE
        
        context.user_data['material_type'] = material
        update.message.reply_text("📏 Введите площадь в м²:")
        return AREA
    
    @staticmethod
    def get_area(update: Update, context: CallbackContext):
        try:
            area = float(update.message.text.replace(',', '.'))
            if area <= 0:
                raise ValueError
        except ValueError:
            update.message.reply_text("❌ Пожалуйста, введите корректное положительное число.")
            return AREA
        
        context.user_data['area'] = area
        
        material = Config.MATERIALS[context.user_data['material_type']]
        if material['thickness_dependent']:
            update.message.reply_text("📐 Введите толщину слоя в мм:")
            return THICKNESS
        else:
            return WorkerHandlers.finish_calculation(update, context)
    
    @staticmethod
    def get_thickness(update: Update, context: CallbackContext):
        try:
            thickness = float(update.message.text.replace(',', '.'))
            if thickness <= 0:
                raise ValueError
        except ValueError:
            update.message.reply_text("❌ Пожалуйста, введите корректное положительное число.")
            return THICKNESS
        
        context.user_data['thickness'] = thickness
        return WorkerHandlers.finish_calculation(update, context)
    
    @staticmethod
    def finish_calculation(update: Update, context: CallbackContext):
        material_type = context.user_data['material_type']
        area = context.user_data['area']
        thickness = context.user_data.get('thickness', 0)
        
        quantity = MaterialCalculator.calculate_material(material_type, area, thickness)
        result = MaterialCalculator.format_calculation_result(material_type, area, thickness, quantity)
        
        # Сохранение расчета в базу данных
        projects = db.get_projects()
        if projects:
            update.message.reply_text(
                "🏗 Хотите привязать расчет к проекту?",
                reply_markup=Keyboards.projects_keyboard(projects)
            )
            context.user_data['calculation_result'] = (material_type, area, thickness, quantity)
            return ConversationHandler.END
        else:
            update.message.reply_text(result, reply_markup=Keyboards.main_menu('worker'))
            return ConversationHandler.END
    
    @staticmethod
    def link_calculation_to_project(update: Update, context: CallbackContext):
        project_address = update.message.text[2:]  # Убираем эмодзи
        projects = db.get_projects()
        
        for project in projects:
            if project['address'] == project_address:
                material_type, area, thickness, quantity = context.user_data['calculation_result']
                
                db.add_calculation(
                    update.effective_user.id,
                    project['project_id'],
                    material_type,
                    area,
                    thickness,
                    quantity
                )
                
                result = MaterialCalculator.format_calculation_result(material_type, area, thickness, quantity)
                update.message.reply_text(
                    f"{result}\n\n✅ Расчет привязан к проекту: {project['address']}",
                    reply_markup=Keyboards.main_menu('worker')
                )
                break
        
        context.user_data.clear()
        return ConversationHandler.END
    
    @staticmethod
    def cancel_calculation(update: Update, context: CallbackContext):
        update.message.reply_text(
            "❌ Расчет отменен.",
            reply_markup=Keyboards.main_menu('worker')
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    @staticmethod
    def show_projects_list(update: Update, context: CallbackContext):
        projects = db.get_projects()
        if not projects:
            update.message.reply_text("📭 Нет доступных проектов.")
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
            calculations = db.get_user_calculations(update.effective_user.id)
            if not calculations:
                query.edit_message_text("📭 Нет расчетов для этого проекта.")
                return
            
            calc_list = "\n".join(
                [f"🧱 {c['material_type']} - {c['quantity']} {Config.MATERIALS[c['material_type'].lower()]['unit']} (Площадь: {c['area']} м²)"
                 for c in calculations if c['project_id'] == int(project_id)]
            )
            
            query.edit_message_text(f"📊 Ваши расчеты для {project['address']}:\n\n{calc_list}")
    
    @staticmethod
    def show_messages(update: Update, context: CallbackContext):
        user = update.effective_user
        messages = db.get_user_messages(user.id)
        
        if not messages:
            update.message.reply_text("📭 У вас нет новых сообщений.")
            return
        
        for msg in messages[:5]:  # Показываем последние 5 сообщений
            update.message.reply_text(f"📩 От {msg['sender_name']}:\n\n{msg['text']}")
    
    @staticmethod
    def send_message_to_admin(update: Update, context: CallbackContext):
        if len(context.args) < 1:
            update.message.reply_text("❌ Использование: /message ваш текст сообщения")
            return
        
        message_text = ' '.join(context.args)
        worker = update.effective_user
        
        for admin_id in Config.ADMIN_IDS:
            try:
                context.bot.send_message(
                    admin_id,
                    f"📩 Сообщение от работника {worker.first_name} {worker.last_name} (@{worker.username}):\n\n{message_text}"
                )
            except Exception as e:
                logger.error(f"Error sending message to admin {admin_id}: {e}")
        
        db.add_message(worker.id, admin_id, message_text)
        update.message.reply_text("✅ Ваше сообщение отправлено администратору.")