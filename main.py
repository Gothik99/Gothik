from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
from admin_handlers import AdminHandlers
from worker_handlers import WorkerHandlers
from shared_handlers import SharedHandlers
from keyboards import Keyboards
from config import Config
import logging
from utils import ensure_temp_dir, cleanup_temp_files

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename=Config.LOG_FILE
)
logger = logging.getLogger(__name__)

def main():
    # Создаем временную директорию
    ensure_temp_dir()
    
    # Инициализация бота
    updater = Updater(Config.BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Обработчики команд
    dp.add_handler(CommandHandler("start", SharedHandlers.start))
    dp.add_handler(CommandHandler("help", SharedHandlers.help))
    dp.add_handler(CommandHandler("message", WorkerHandlers.send_message_to_admin))
    
    # ConversationHandler для администратора (добавление проекта)
    project_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^🏗 Проекты$'), AdminHandlers.start_add_project)],
        states={
            AdminHandlers.PROJECT_ADDRESS: [MessageHandler(Filters.text & ~Filters.command, AdminHandlers.get_project_address)],
            AdminHandlers.PROJECT_DESCRIPTION: [MessageHandler(Filters.text & ~Filters.command, AdminHandlers.get_project_description)],
            AdminHandlers.PROJECT_DESIGN: [MessageHandler(Filters.document.pdf, AdminHandlers.get_project_design)],
            AdminHandlers.PROJECT_LOCK_CODE: [MessageHandler(Filters.text & ~Filters.command, AdminHandlers.get_project_lock_code)]
        },
        fallbacks=[
            CommandHandler('cancel', SharedHandlers.cancel),
            MessageHandler(Filters.regex('^🔙 Назад$'), AdminHandlers.cancel_project_creation)
        ]
    )
    
    # ConversationHandler для рассылки
    broadcast_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^📢 Рассылка$'), AdminHandlers.start_broadcast)],
        states={
            AdminHandlers.BROADCAST_MESSAGE: [MessageHandler(Filters.text & ~Filters.command, AdminHandlers.confirm_broadcast)]
        },
        fallbacks=[
            CommandHandler('cancel', SharedHandlers.cancel),
            MessageHandler(Filters.regex('^🔙 Назад$'), AdminHandlers.cancel_broadcast)
        ]
    )
    
    # ConversationHandler для калькулятора
    calc_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^📊 Калькулятор материалов$'), WorkerHandlers.start_calculation)],
        states={
            WorkerHandlers.MATERIAL_TYPE: [MessageHandler(Filters.text & ~Filters.command, WorkerHandlers.get_material_type)],
            WorkerHandlers.AREA: [MessageHandler(Filters.text & ~Filters.command, WorkerHandlers.get_area)],
            WorkerHandlers.THICKNESS: [MessageHandler(Filters.text & ~Filters.command, WorkerHandlers.get_thickness)]
        },
        fallbacks=[
            CommandHandler('cancel', SharedHandlers.cancel),
            MessageHandler(Filters.regex('^🔙 Назад$'), WorkerHandlers.cancel_calculation)
        ]
    )
    
    # Обработчики сообщений
    dp.add_handler(MessageHandler(Filters.regex('^🚪 Запросить доступ$'), WorkerHandlers.request_access))
    dp.add_handler(MessageHandler(Filters.regex('^👥 Работники$'), AdminHandlers.manage_workers))
    dp.add_handler(MessageHandler(Filters.regex('^📩 Сообщения$'), WorkerHandlers.show_messages))
    dp.add_handler(MessageHandler(Filters.regex('^🔙 Назад$'), SharedHandlers.back_to_menu))
    
    # Обработчики проектов
    dp.add_handler(project_conv_handler)
    dp.add_handler(MessageHandler(Filters.regex('^🏗 Проекты$'), WorkerHandlers.show_projects_list))
    dp.add_handler(MessageHandler(Filters.regex('^🏠 .*'), WorkerHandlers.show_project_details))
    dp.add_handler(MessageHandler(Filters.regex('^🏠 .*'), AdminHandlers.show_project_details))
    
    # Обработчики callback-запросов
    dp.add_handler(CallbackQueryHandler(AdminHandlers.show_pending_workers, pattern='^pending_workers$'))
    dp.add_handler(CallbackQueryHandler(AdminHandlers.show_workers_list, pattern='^workers_list$'))
    dp.add_handler(CallbackQueryHandler(AdminHandlers.handle_worker_approval, pattern='^(approve|reject)_\d+$'))
    dp.add_handler(CallbackQueryHandler(AdminHandlers.project_details_callback, pattern='^(design|lock|calculations)_\d+$'))
    dp.add_handler(CallbackQueryHandler(WorkerHandlers.project_details_callback, pattern='^(design|lock|calculations)_\d+$'))
    dp.add_handler(CallbackQueryHandler(AdminHandlers.send_broadcast, pattern='^broadcast_(confirm|edit|cancel)$'))
    
    # Добавление ConversationHandler
    dp.add_handler(broadcast_conv_handler)
    dp.add_handler(calc_conv_handler)
    
    # Обработчик для привязки расчета к проекту
    dp.add_handler(MessageHandler(Filters.regex('^🏠 .*'), WorkerHandlers.link_calculation_to_project))
    
    # Обработчик неизвестных команд
    dp.add_handler(MessageHandler(Filters.text, SharedHandlers.start))
    
    # Запуск бота
    updater.start_polling()
    logger.info("Бот запущен и работает...")
    updater.idle()
    
    # Очистка временных файлов при завершении
    cleanup_temp_files()

if __name__ == '__main__':
    main()