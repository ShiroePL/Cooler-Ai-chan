import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    GUILD_ID = int(os.getenv('GUILD_ID'))
    ai_groq_key = os.getenv('AI_GROQ_KEY')

    @staticmethod
    def get_groq_api_keys():
        api_keys = []
        i = 1
        while True:
            key = os.getenv(f'AI_GROQ_KEY{i}')
            if key is None:
                break
            api_keys.append(key)
            i += 1
        return api_keys
    
    LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', 'app/persistent_data/logs/discord_bot.log')
    LOKI_URL = os.getenv('LOKI_URL', 'http://localhost:3100')
    PREFIX = os.getenv('PREFIX', '+')
    ENVIROMENT = os.getenv('ENVIROMENT', 'production')
    master_user_id = int(os.getenv('MASTER_USER_ID'))
    nequs_id = int(os.getenv('NEQUS_ID'))
    # Game configuration
    COOLDOWN_MINUTES = 1  # Set this to the appropriate value for testing
    # Alternatively, use hours if you decide to use a longer interval
    COOLDOWN_HOURS = 4 # Example value for a 3-hour cooldown
    REFERENCE_HOUR = 0  # Reference hour to start the intervals

    EMOJI_API_KEY = os.getenv('EMOJI_API_KEY')
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
    TOMORROW_API_KEY= os.getenv('TOMORROW_API_KEY')