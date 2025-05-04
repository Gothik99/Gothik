import os

class Config:
    # Токен бота
    BOT_TOKEN = os.getenv('BOT_TOKEN', '7582181232:AAHq281v3UmM19PFbzm6aKTuxqWm0VOSON4')
    
    # ID администратора (можно несколько через запятую)
    ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '821813425').split(',')]
    
    # Настройки базы данных
    DATABASE_NAME = 'database.db'
    
    # Логирование
    LOG_FILE = 'bot.log'
    
    # Пути для временных файлов
    TEMP_DIR = 'temp'
    
    # Материалы и их расчетные параметры
    MATERIALS = {
        'штукатурка': {'unit': 'кг/м²', 'thickness_dependent': True},
        'стяжка': {'unit': 'кг/м²', 'thickness_dependent': True},
        'краска': {'unit': 'л/м²', 'thickness_dependent': False},
        'затирка': {'unit': 'кг/м²', 'thickness_dependent': True},
        'наливной пол': {'unit': 'кг/м²', 'thickness_dependent': True},
        'кирпич': {'unit': 'шт/м²', 'thickness_dependent': False},
        'гипсокартон': {'unit': 'лист', 'thickness_dependent': False},
        'плитка': {'unit': 'шт/м²', 'thickness_dependent': False},
        'обои': {'unit': 'рулон', 'thickness_dependent': False},
        'лак': {'unit': 'л/м²', 'thickness_dependent': False}
    }
    
    # Коэффициенты запаса материалов
    SAFETY_FACTOR = 1.1