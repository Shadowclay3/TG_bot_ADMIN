import telebot
import subprocess
import glob
import os

# Токен вашего бота
TOKEN = ''

bot = telebot.TeleBot(TOKEN)

# Словарь для хранения соответствия названия файла и запущенного процесса
processes = {}

# Флаг, указывающий, что процесс был остановлен для перезапуска
restart_flag = False

@bot.message_handler(commands=['start'])
def handle_start(message):
    keyboard = telebot.types.InlineKeyboardMarkup()

    # Получаем список всех файлов с расширением .py в текущей директории и поддиректориях
    files = glob.glob("**/*.py", recursive=True)

    # Создаем кнопки для каждого файла
    for file in files:
        # Получаем относительный путь файла относительно текущей директории скрипта
        relative_path = os.path.relpath(file)
        
        # Проверяем, содержит ли путь к файлу папку "venv"
        if "venv" in relative_path:
            continue  # Пропускаем файлы из папки "venv"

        button = telebot.types.InlineKeyboardButton(text=relative_path, callback_data=relative_path)
        keyboard.add(button)

    bot.send_message(message.chat.id, '<code>Выберите файл для запуска:</code>', reply_markup=keyboard, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    global restart_flag
    
    file = call.data
    
    if restart_flag:
        restart_flag = False
        
        if file in processes:
            # Останавливаем процесс
            process = processes[file]
            process.kill()
            
            # Запускаем файл заново
            process = subprocess.Popen(['python3', file])
            processes[file] = process
            
            bot.send_message(call.message.chat.id, f'<code>Процесс {file} перезапущен.</code>', parse_mode='HTML')
        else:
            bot.send_message(call.message.chat.id, f'<code>Процесс {file} не найден.</code>', parse_mode='HTML')
    else:
        if file in processes:
            # Останавливаем процесс и удаляем его из словаря
            process = processes[file]
            process.kill()
            del processes[file]
            bot.send_message(call.message.chat.id, f'<code>Процесс  {file} остановлен и удален.</code>', parse_mode='HTML')
        else:
            # Запускаем файл как отдельный процесс
            process = subprocess.Popen(['python3', file])
            processes[file] = process
            bot.send_message(call.message.chat.id, f'<code>Файл {file} запущен.</code>', parse_mode='HTML')

@bot.message_handler(commands=['restart'])
def handle_restart(message):
    global restart_flag
    
    keyboard = telebot.types.InlineKeyboardMarkup()
    
    # Создаем кнопки для каждого запущенного процесса
    for file in processes.keys():
        button = telebot.types.InlineKeyboardButton(text=file, callback_data=file)
        keyboard.add(button)
    
    bot.send_message(message.chat.id, '<code>Выберите файл для перезапуска:</code>', reply_markup=keyboard, parse_mode='HTML')
    
    restart_flag = True

@bot.message_handler(commands=['stop'])
def handle_stop(message):
    keyboard = telebot.types.InlineKeyboardMarkup()
    
    # Создаем кнопки для каждого запущенного процесса
    for file in processes.keys():
        button = telebot.types.InlineKeyboardButton(text=file, callback_data=file)
        keyboard.add(button)
    
    bot.send_message(message.chat.id, '<code>Выберите файл для остановки:</code>', reply_markup=keyboard, parse_mode='HTML')

@bot.message_handler(commands=['cmd'])
def handle_cmd(message):
    cmd = message.text[5:]  # Получаем команду из сообщения пользователя
    if not cmd:
        bot.send_message(message.chat.id, '<code>Вы забыли указать команду. Введите: \n\n/cmd\nкоманда.</code>', parse_mode='HTML')
        return
    # Выполняем команду в терминале
    result = subprocess.check_output(cmd, shell=True).decode('utf-8')
    # Отправляем результат пользователю
    chunk_size = 4096
    for i in range(0, len(result), chunk_size):
        chunk = result[i:i+chunk_size]
        bot.send_message(message.chat.id, f"<code>{chunk}</code>", parse_mode='HTML')

bot.infinity_polling(timeout=999, long_polling_timeout = 5)
