import os
import disnake
from disnake.ext import commands
from dotenv import load_dotenv
import logging
from datetime import datetime

# Створюємо папку для логів, якщо її немає
if not os.path.exists('logs'):
    os.makedirs('logs')

# Налаштування логування
log_filename = f"logs/bot_{datetime.now().strftime('%Y-%m-%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'), # Запис у файл
        logging.StreamHandler() # Вивід у консоль
    ]
)

logger = logging.getLogger('MistraNode')
# Завантажуємо змінні оточення
load_dotenv()

class MistraNode(commands.Bot):
    def __init__(self):
        # Налаштування інтентів
        intents = disnake.Intents.default()
        intents.message_content = True
        intents.members = True 

        super().__init__(
            command_prefix="!",
            intents=intents,
            test_guilds=[1471810518414131233] 
        )

    async def on_ready(self):
        print("-" * 30)
        print(f"[OK] Вузол Mistra Node активовано!")
        print(f"[INFO] Бот: {self.user}")
        print(f"[INFO] Локація: Ірпінь, Україна")
        print("-" * 30)
        
        await self.change_presence(
            activity=disnake.Activity(
                type=disnake.ActivityType.watching, 
                name="за блокчейном та безпекою"
            )
        )

    def load_cogs(self):
        """Динамічне завантаження модулів через абсолютний шлях (без емодзі)"""
        base_path = os.path.dirname(os.path.abspath(__file__))
        cogs_path = os.path.join(base_path, "cogs")

        # Прибрали емодзі, щоб не було UnicodeEncodeError
        print(f"--- Checking directory: {cogs_path} ---")

        if not os.path.exists(cogs_path):
            print(f"ERROR: Directory {cogs_path} not found!")
            return

        for filename in os.listdir(cogs_path):
            if filename.endswith(".py"):
                try:
                    self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"LOADED: {filename}")
                except Exception as e:
                    print(f"FAILED TO LOAD {filename}: {e}")

# Створюємо бота
bot = MistraNode()

# Викликаємо метод завантаження через екземпляр класу
bot.load_cogs()

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("[ERROR] Помилка: DISCORD_TOKEN відсутній у .env")