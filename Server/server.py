# -*- coding: utf-8 -*-

from flask import Flask, request
from Crypto.Cipher import DES
import config as Config
import threading
import platform
import sqlite3
import json
import os

# Для получение правильного пути к файлам сервера
def get_true_server_folder_path():
	if platform.system() == 'Windows':
		true_slash = '\\'
	else:
		true_slash = '/'

	path = os.getcwd().split(true_slash)
	if path[-1] != 'Server' and path[-2] != 'Server':
		path.append('Server')
	else:
		del path[len(path) - 2]
	return true_slash.join(path)

# Создание всех нужных переменных/констант
# ==================================================================
SERVER_FOLDER_PATH = get_true_server_folder_path()
lock = threading.Lock()
app = Flask(__name__)
# ==================================================================

# Обычные функции
# ==================================================================
def clear_key(key: str): # Получение чистого ключа из пароля
	key = ''.join(list(key)[0:8]).encode('UTF-8')
	return key

def encrypt(key: str, data): # Шифрование
	def pad(data):
		while len(data) % 8 != 0:
			data += b' '
		return data

	key = clear_key(key)
	des = DES.new(key, DES.MODE_ECB)
	padded_data = pad(data.encode('UTF-8'))
	encrypted_data = des.encrypt(padded_data)
	return encrypted_data

def decrypt(key: str, encrypted_data): # Дешифровка
	key = clear_key(key)
	des = DES.new(key, DES.MODE_ECB)
	decrypted_data = des.decrypt(encrypted_data)
	return decrypted_data.decode('UTF-8').strip()

def find_folder(path: str, folder_name: str): # Поиск папки
	find_folder_status = False
	for folder in os.listdir(path):
		if folder == folder_name:
			find_folder_status = True
			break
	return find_folder_status
# ==================================================================

# Создание всех нужных папок и подключение DB проекта "VK Bot"
# ==================================================================
if find_folder(SERVER_FOLDER_PATH, 'Files') != True:
	os.mkdir(f'{SERVER_FOLDER_PATH}/Files')

db = sqlite3.connect(f'{SERVER_FOLDER_PATH}/Files/VK_Bot-Accounts.db', check_same_thread=False)
sql = db.cursor()

sql.execute("""
	CREATE TABLE IF NOT EXISTS Accounts(
		Login TEXT,
		Mail TEXT,
		Password BLOB
	)
""")
db.commit()
# ==================================================================

# Логика сервера для проекта "VK Bot"
# ==================================================================
def check_user_data(func): # Декоратор
	def wrapper(login, bot_name=None):
		try:
			user_data = json.loads(request.data.decode('UTF-8'))
			password = user_data['Password']

			lock.acquire(True)
			sql.execute(f"SELECT * From Accounts WHERE Login = '{login}'")
			account = sql.fetchone()
			lock.release()

			if account != None:
				enrypted_password = encrypt(password, password)
				if enrypted_password == account[2]:
					if bot_name != None:
						if find_folder(f'{SERVER_FOLDER_PATH}/Files/{account[0]}', bot_name) == True:
							return func(user_data, login, bot_name)
						else:
							return json.dumps(
								{
									'Answer': f'Бота под именем "{bot_name}" не существует!'
								}, ensure_ascii=False
							), 400
					else:
						return func(user_data, login)
				else:
					return json.dumps(
						{
							'Answer': 'Был передан неверный "Password"!'
						}, ensure_ascii=False
					), 400
			else:
				return json.dumps(
					{
						'Answer': 'Был передан неверный "Login"!'
					}, ensure_ascii=False
				), 400
		except:
			return json.dumps(
				{
					'Answer': 'Неизвестная ошибка на сервере!'
				}, ensure_ascii=False
			), 400
	wrapper.__name__ = func.__name__
	return wrapper

@app.route('/vk_bot/register_account', methods=['POST'])
def register_account(): # Регистрация
	try:
		user_data = json.loads(request.data.decode('UTF-8'))
		login = user_data['Login']
		mail = user_data['Mail']
		password_1 = user_data['Password_1']
		password_2 = user_data['Password_2']

		invalid_form_reg = []
		if login == '':
			invalid_form_reg.append('"Login"')
		if mail == '':
			invalid_form_reg.append('"Mail"')
		if password_1 == '':
			invalid_form_reg.append('"Password_1"')
		if password_2 == '':
			invalid_form_reg.append('"Password_2"')
		server_answer = f"Введите {', '.join(invalid_form_reg)}!"

		if server_answer == 'Введите !':
			if password_1 == password_2:
				if len(password_1) >= 8:
					lock.acquire(True)
					sql.execute(f"SELECT * From Accounts WHERE Login = '{login}'")
					account = sql.fetchone()
					lock.release()

					if account == None:
						os.mkdir(f'{SERVER_FOLDER_PATH}/Files/{login}')

						lock.acquire(True)
						encrypted_password = encrypt(password_1, password_1)
						sql.execute("INSERT INTO Accounts VALUES (?, ?, ?)", (login, mail, encrypted_password))
						db.commit()
						lock.release()

						return json.dumps(
							{
								'Answer': 'Ожидание подтверждения почты.'
							}, ensure_ascii=False
						), 200
					else:
						return json.dumps(
							{
								'Answer': f'Login "{login}" уже занят!'
							}, ensure_ascii=False
						), 400
				else:
					return json.dumps(
						{
							'Answer': f'Пароль должен быть не менее 8 символов!'
						}, ensure_ascii=False
					), 400
			else:
				return json.dumps(
					{
						'Answer': f'Пароли не совпадают!'
					}, ensure_ascii=False
				), 400
		else:
			return json.dumps(
				{
					'Answer': server_answer
				}, ensure_ascii=False
			), 400
	except:
		return json.dumps(
			{
				'Answer': 'Неизвестная ошибка на сервере!'
			}, ensure_ascii=False
		), 400

@app.route('/vk_bot/authorize_in_account', methods=['POST'])
def authorize_in_account(): # Авторизация
	try:
		user_data = json.loads(request.data.decode('UTF-8'))
		login = user_data['Login']
		password = user_data['Password']

		server_answer = ''
		if login == '' and password == '':
			server_answer = 'Введите "Login" и "Password"!'
		elif login == '':
			server_answer = 'Введите "Login"!'
		elif password == '':
			server_answer = 'Введите "Password"!'

		if server_answer == '':
			lock.acquire(True)
			sql.execute(f"SELECT * From Accounts WHERE Login = '{login}'")
			account = sql.fetchone()
			lock.release()

			if account != None:
				enrypted_password = encrypt(password, password)
				if enrypted_password == account[2]:
					for folder in os.listdir(f'{SERVER_FOLDER_PATH}/Files/{account[0]}'):
						with open(f'{SERVER_FOLDER_PATH}/Files/{account[0]}/{folder}/User-Commands.json', 'rb') as file:
							user_commands = file.read()
							user_commands = decrypt(password, user_commands)
							user_commands = json.loads(user_commands)
						for user_command in user_commands:
							if len(user_command.items()) != len(Config.USER_BOT_COMMANDS[0].items()) or len(user_command['Flags'].items()) != len(Config.USER_BOT_COMMANDS[0]['Flags'].items()):
								with open(f'{SERVER_FOLDER_PATH}/Files/{account[0]}/{folder}/User-Commands.json', 'wb') as file:
									user_commands = json.dumps(Config.USER_BOT_COMMANDS, ensure_ascii=False, indent=2)
									user_commands = encrypt(password, user_commands)
									file.write(user_commands)
					return json.dumps(
						{
							'Answer': 'Вы успешно авторизовались.'
						}, ensure_ascii=False
					), 200
				else:
					return json.dumps(
						{
							'Answer': 'Неверный "Login" или "Password"!'
						}, ensure_ascii=False
					), 400
			else:
				return json.dumps(
					{
						'Answer': 'Такого аккаунта не существует!'
					}, ensure_ascii=False
				), 400
		else:
			return json.dumps(
				{
					'Answer': server_answer
				}, ensure_ascii=False
			), 400
	except:
		return json.dumps(
			{
				'Answer': 'Неизвестная ошибка на сервере!'
			}, ensure_ascii=False
		), 400

@app.route('/vk_bot/<string:login>/create_bot', methods=['POST'])
@check_user_data
def create_user_bot(user_data: dict, login: str): # Создание бота
	bot_name = user_data['Bot_Name']
	bot_settings = user_data['Bot_Settings']
	vk_token = bot_settings['VK_Token']
	group_id = bot_settings['Group_ID']
	password = user_data['Password']

	server_answer = ''
	if vk_token == '' and group_id == '':
		server_answer = 'Заполните форму добавления бота!'
	elif vk_token == '':
		server_answer = 'Введите "VK_Token"!'
	elif group_id == '':
		server_answer = 'Введите "Group_ID"!'

	if server_answer == '':
		if find_folder(f'{SERVER_FOLDER_PATH}/Files/{login}', bot_name) == False:
			os.mkdir(f'{SERVER_FOLDER_PATH}/Files/{login}/{bot_name}')
			with open(f'{SERVER_FOLDER_PATH}/Files/{login}/{bot_name}/Bot-Settings.json', 'wb') as file:
				bot_settings = json.dumps(bot_settings, ensure_ascii=False, indent=2)
				bot_settings = encrypt(password, bot_settings)
				file.write(bot_settings)
			with open(f'{SERVER_FOLDER_PATH}/Files/{login}/{bot_name}/User-Commands.json', 'wb') as file:
				user_commands = json.dumps(Config.USER_BOT_COMMANDS, ensure_ascii=False, indent=2)
				user_commands = encrypt(password, user_commands)
				file.write(user_commands)
			with open(f'{SERVER_FOLDER_PATH}/Files/{login}/{bot_name}/Log.txt', 'wb') as file:
				log = json.dumps([], ensure_ascii=False, indent=2)
				log = encrypt(password, log)
				file.write(log)
			db = sqlite3.connect(f'{SERVER_FOLDER_PATH}/Files/{login}/{bot_name}/VK_Bot-Users-DataBase.db')
			db.close()

			return json.dumps(
				{
					'Answer': 'Успешное создание бота.'
				}, ensure_ascii=False
			), 200
		else:
			return json.dumps(
				{
					'Answer': f'Бота под именем "{bot_name}" уже существует!'
				}, ensure_ascii=False
			), 400
	else:
		return json.dumps(
			{
				'Answer': server_answer
			}, ensure_ascii=False
		), 400

@app.route('/vk_bot/<string:login>/get_bots_list', methods=['POST'])
@check_user_data
def get_user_bots_list(user_data: dict, login: str): # Получение списка ботов
	return json.dumps(
		{
			'Answer': 'Запрос к списку ботов был успешно выполнен.',
			'User_Bot_List': os.listdir(f'{SERVER_FOLDER_PATH}/Files/{login}')
		}, ensure_ascii=False
	), 200

@app.route('/vk_bot/<string:login>/delete_bot', methods=['POST'])
@check_user_data
def delete_user_bot(user_data: dict, login: str): # Удаление бота
	bot_name = user_data['Bot_Name']

	if find_folder(f'{SERVER_FOLDER_PATH}/Files/{login}', bot_name) == True:
		for file in os.listdir(f'{SERVER_FOLDER_PATH}/Files/{login}/{bot_name}'):
			os.remove(f'{SERVER_FOLDER_PATH}/Files/{login}/{bot_name}/{file}')
		os.rmdir(f'{SERVER_FOLDER_PATH}/Files/{login}/{bot_name}')

		return json.dumps(
			{
				'Answer': 'Успешное удаление бота.'
			}, ensure_ascii=False
		), 200
	else:
		return json.dumps(
			{
				'Answer': f'Бота под именем "{bot_name}" не существует!'
			}, ensure_ascii=False
		), 400

@app.route('/vk_bot/<string:login>/<string:bot_name>/get_bot_settings', methods=['POST'])
@check_user_data
def get_bot_settings(user_data: dict, login: str, bot_name: str): # Получение настроек бота
	password = user_data['Password']

	with open(f'{SERVER_FOLDER_PATH}/Files/{login}/{bot_name}/Bot-Settings.json', 'rb') as file:
		bot_settings = file.read()
		bot_settings = decrypt(password, bot_settings)
		bot_settings = json.loads(bot_settings)

	return json.dumps(
		{
			'Answer': 'Запрос к файлу "Bot-Settings.json" бота "{bot_name}" был успешно выполнен.',
			'Bot_Settings': bot_settings
		}, ensure_ascii=False
	), 200

@app.route('/vk_bot/<string:login>/<string:bot_name>/update_bot_settings', methods=['POST'])
@check_user_data
def update_bot_settings(user_data: dict, login: str, bot_name: str): # Обновление настроек бота
	password = user_data['Password']

	with open(f'{SERVER_FOLDER_PATH}/Files/{login}/{bot_name}/Bot-Settings.json', 'wb') as file:
		bot_settings = json.dumps(user_data['Bot_Settings'], ensure_ascii=False, indent=2)
		bot_settings = encrypt(password, bot_settings)
		file.write(bot_settings)

	return json.dumps(
		{
			'Answer': 'Запрос к файлу "Bot-Settings.json" бота "{bot_name}" был успешно выполнен.'
		}, ensure_ascii=False
	), 200

@app.route('/vk_bot/<string:login>/<string:bot_name>/get_bot_commands_list', methods=['POST'])
@check_user_data
def get_bot_commands_list(user_data: dict, login: str, bot_name: str): # Получение команд бота
	password = user_data['Password']

	with open(f'{SERVER_FOLDER_PATH}/Files/{login}/{bot_name}/User-Commands.json', 'rb') as file:
		user_commands = file.read()
		user_commands = decrypt(password, user_commands)
		user_commands = json.loads(user_commands)

	return json.dumps(
		{
			'Answer': 'Запрос к файлу "User-Commands.json" бота "{bot_name}" был успешно выполнен.',
			'User_Commands': user_commands
		}, ensure_ascii=False
	), 200

@app.route('/vk_bot/<string:login>/<string:bot_name>/update_bot_commands_list', methods=['POST'])
@check_user_data
def update_bot_commands_list(user_data: dict, login: str, bot_name: str): # Обновление команд бота
	password = user_data['Password']

	with open(f'{SERVER_FOLDER_PATH}/Files/{login}/{bot_name}/User-Commands.json', 'wb') as file:
		user_commands = json.dumps(user_data['User_Commands'], ensure_ascii=False, indent=2)
		user_commands = encrypt(password, user_commands)
		file.write(user_commands)

	return json.dumps(
		{
			'Answer': 'Запрос к файлу "User-Commands.json" бота "{bot_name}" был успешно выполнен.'
		}, ensure_ascii=False
	), 200

@app.route('/vk_bot/<string:login>/<string:bot_name>/get_bot_log', methods=['POST'])
@check_user_data
def get_bot_log(user_data: dict, login: str, bot_name: str): # Получение логов бота
	password = user_data['Password']

	with open(f'{SERVER_FOLDER_PATH}/Files/{login}/{bot_name}/Log.txt', 'rb') as file:
		log = file.read()
		log = decrypt(password, log)
		log = json.loads(log)

	return json.dumps(
		{
			'Answer': 'Запрос к файлу "Log.txt" бота "{bot_name}" был успешно выполнен.',
			'Log': log
		}, ensure_ascii=False
	), 200

@app.route('/vk_bot/<string:login>/<string:bot_name>/update_bot_log', methods=['POST'])
@check_user_data
def update_bot_log(user_data: dict, login: str, bot_name: str): # Обновление логов бота
	password = user_data['Password']

	with open(f'{SERVER_FOLDER_PATH}/Files/{login}/{bot_name}/Log.txt', 'wb') as file:
		log = json.dumps(user_data['Log'], ensure_ascii=False, indent=2)
		log = encrypt(password, log)
		file.write(log)

	return json.dumps(
		{
			'Answer': 'Запрос к файлу "Log.txt" бота "{bot_name}" был успешно выполнен.'
		}, ensure_ascii=False
	), 200

@app.route('/vk_bot/<string:login>/<string:bot_name>/database/fetchone', methods=['POST'])
@check_user_data
def bot_database_fetchone(user_data: dict, login: str, bot_name: str): # Поиск одной записи в БД
	vk_bot_db = sqlite3.connect(f'{SERVER_FOLDER_PATH}/Files/{login}/{bot_name}/VK_Bot-Users-DataBase.db', check_same_thread = False)
	vk_bot_sql = vk_bot_db.cursor()
	vk_bot_sql.execute(user_data['SQLite3_Command'])
	result = vk_bot_sql.fetchone()
	vk_bot_db.close()

	return json.dumps(
		{
			'Answer': 'Запрос к базе данных бота "{bot_name}" был успешно выполнен.',
			'Result': result
		}, ensure_ascii=False
	), 200

@app.route('/vk_bot/<string:login>/<string:bot_name>/database/fetchall', methods=['POST'])
@check_user_data
def bot_database_fetchall(user_data: dict, login: str, bot_name: str): # Поиск несколько записей в БД
	vk_bot_db = sqlite3.connect(f'{SERVER_FOLDER_PATH}/Files/{login}/{bot_name}/VK_Bot-Users-DataBase.db', check_same_thread = False)
	vk_bot_sql = vk_bot_db.cursor()
	vk_bot_sql.execute(user_data['SQLite3_Command'])
	result = vk_bot_sql.fetchall()
	vk_bot_db.close()

	return json.dumps(
		{
			'Answer': 'Запрос к базе данных бота "{bot_name}" был успешно выполнен.',
			'Result': result
		}, ensure_ascii=False
	), 200

@app.route('/vk_bot/<string:login>/<string:bot_name>/database/edit', methods=['POST'])
@check_user_data
def bot_database_edit(user_data: dict, login: str, bot_name: str): # Редактирования БД
	vk_bot_db = sqlite3.connect(f'{SERVER_FOLDER_PATH}/Files/{login}/{bot_name}/VK_Bot-Users-DataBase.db', check_same_thread = False)
	vk_bot_sql = vk_bot_db.cursor()

	if 'Values' in user_data:
		vk_bot_sql.execute(user_data['SQLite3_Command'], user_data['Values'])
	else:
		vk_bot_sql.execute(user_data['SQLite3_Command'])
	vk_bot_db.commit()
	vk_bot_db.close()

	return json.dumps(
		{
			'Answer': 'Запрос к базе данных бота "{bot_name}" был успешно выполнен.'
		}, ensure_ascii=False
	), 200
# ==================================================================

if __name__ == '__main__':
	app.run(debug = True)