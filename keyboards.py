from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from config import Config

class Keyboards:
    @staticmethod
    def main_menu(user_role):
        if user_role == 'admin':
            buttons = [
                ['📊 Калькулятор материалов'],
                ['🏗 Проекты', '👥 Работники'],
                ['📢 Рассылка', '📩 Сообщения']
            ]
        elif user_role == 'worker':
            buttons = [
                ['📊 Калькулятор материалов'],
                ['🏗 Проекты', '📩 Сообщения']
            ]
        else:
            buttons = [['🚪 Запросить доступ']]
        
        return ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    
    @staticmethod
    def materials_keyboard():
        materials = list(Config.MATERIALS.keys())
        buttons = [materials[i:i+2] for i in range(0, len(materials), 2)]
        buttons.append(['🔙 Назад'])
        return ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    
    @staticmethod
    def projects_keyboard(projects):
        buttons = [[f"🏠 {project['address']}"] for project in projects]
        buttons.append(['🔙 Назад'])
        return ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    
    @staticmethod
    def confirm_keyboard():
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Подтвердить", callback_data="confirm"),
             InlineKeyboardButton("❌ Отменить", callback_data="cancel")]
        ])
    
    @staticmethod
    def workers_management_keyboard():
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Заявки на доступ", callback_data="pending_workers")],
            [InlineKeyboardButton("👷 Список работников", callback_data="workers_list")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back")]
        ])
    
    @staticmethod
    def worker_actions_keyboard(worker_id):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{worker_id}"),
             InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{worker_id}")]
        ])
    
    @staticmethod
    def broadcast_confirmation_keyboard():
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Отправить всем", callback_data="broadcast_confirm")],
            [InlineKeyboardButton("✏️ Редактировать", callback_data="broadcast_edit")],
            [InlineKeyboardButton("❌ Отменить", callback_data="broadcast_cancel")]
        ])
    
    @staticmethod
    def project_details_keyboard(project_id):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Расчеты", callback_data=f"calculations_{project_id}")],
            [InlineKeyboardButton("📄 Дизайн-проект", callback_data=f"design_{project_id}")],
            [InlineKeyboardButton("🔑 Код замка", callback_data=f"lock_{project_id}")]
        ])
    
    @staticmethod
    def back_keyboard():
        return ReplyKeyboardMarkup([['🔙 Назад']], resize_keyboard=True)