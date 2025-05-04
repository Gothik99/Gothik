import os
from config import Config

def ensure_temp_dir():
    """Создает временную директорию, если она не существует"""
    os.makedirs(Config.TEMP_DIR, exist_ok=True)

def cleanup_temp_files():
    """Очищает временную директорию"""
    for filename in os.listdir(Config.TEMP_DIR):
        file_path = os.path.join(Config.TEMP_DIR, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")