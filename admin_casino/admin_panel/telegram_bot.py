import os
import subprocess
import logging

logger = logging.getLogger(__name__)

def start_bot(bot_token, welcome_message, button_url, folder_name, bot_username):
    # Путь к директории ботов
    bot_directory = os.path.join('/root/bots', folder_name)
    os.makedirs(bot_directory, exist_ok=True)
    
    # Путь к файлу бота
    bot_script_path = os.path.join(bot_directory, 'bot.py')

    # Получаем абсолютный путь к шаблону
    current_directory = os.path.dirname(os.path.abspath(__file__))
    template_file_path = os.path.join(current_directory, 'bot_template.py')

    # Чтение шаблона и подстановка переменных
    with open(template_file_path, 'r') as template_file:
        bot_script_content = template_file.read().format(
            bot_token=bot_token,
            welcome_message=welcome_message,
            button_url=button_url
        )
    
    # Запись скрипта бота в папку
    with open(bot_script_path, 'w') as bot_file:
        bot_file.write(bot_script_content)

    # Запуск бота в screen
    command = f'screen -dmS {bot_username} bash -c "python3 {bot_script_path}"'
    subprocess.run(command, shell=True, check=True)


def is_bot_running(bot_username):
    command = f"screen -ls | grep {bot_username}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return bot_username in result.stdout

def restart_bot(bot_username, bot_token, welcome_message, folder_name):
    if stop_bot(bot_username):
        start_bot(bot_token, welcome_message, folder_name, bot_username)
    else:
        logger.error(f"Не удалось перезапустить бота {bot_username}.")
        return False

def stop_bot(bot_username):
    if is_bot_running(bot_username):
        command = f'screen -S {bot_username} -X quit'
        try:
            subprocess.run(command, shell=True, check=True)
            logger.info(f"Бот {bot_username} успешно остановлен.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка остановки бота {bot_username}: {e}")
            return False
    else:
        logger.warning(f"Бот {bot_username} не запущен.")
        return False
