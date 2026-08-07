import os

# Telegram API
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# --- Telegram API ---
# Теперь данные берутся из .env, а не захардкожены
TG_API_ID = os.getenv('TG_API_ID')
TG_API_HASH = os.getenv('TG_API_HASH')
TG_CHANNELS = ['csharpdevjob', 'job_dotnet', 'g_jobbot', 'DotNetRuJobs', 'g_jobbot']
TG_KEYWORDS = ['c#', '.net', 'asp', 'dotnet', 'backend', 'разработчик', 'winforms', 'wpf', 'blazor', 'razor', '']

SEARCH_QUERY = 'C# .NET'
PAGES_TO_SCAN = 50  # Количество страниц для сайтов

# Настройки LLM
OLLAMA_MODEL = "akdengi/saiga-llama3-8b"
OLLAMA_TEMPERATURE = 0.0

# Пути к файлам
RAW_DATA_DIR = "data/raw/"
PROCESSED_DATA_DIR = "data/processed/"
FINAL_DATA_DIR = "data/final/"

# Убедимся, что папки существуют
os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
os.makedirs(FINAL_DATA_DIR, exist_ok=True)