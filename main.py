import os
import subprocess

from dotenv import load_dotenv

from src.telegram_bot.bot import MedBot

load_dotenv()

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
RASA_TOKEN = os.getenv('RASA_TOKEN')

bot = MedBot(BOT_TOKEN, RASA_TOKEN)


if __name__ == '__main__':
    bot.run()
    
    # start the Rasa server
    # subprocess.Popen(['rasa', 'run', f'--auth-token {str(RASA_TOKEN)}', '-m', 'models', '--enable-api', '--cors', '*', '--debug'])
    
    