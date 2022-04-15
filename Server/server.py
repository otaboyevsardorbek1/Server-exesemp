# -*- coding: utf-8 -*-

from flask import Flask, request
from Crypto.Cipher import DES
import config as Config
import threading
import platform
import sqlite3
import json
import os

# Если сервер на хосте
if platform.system() == 'Windows':
	true_slash = '\\'
else:
	true_slash = '/'

path = os.getcwd().split(true_slash)
if path[-1] != 'Server' and path[-2] != 'Server':
	path.append('Server')
else:
	del path[len(path) - 2]
PATH = true_slash.join(path)

# Создание всех нужных переменных
# ==================================================================
lock = threading.Lock()
app = Flask(__name__)
# ==================================================================

# Подключение DB для проекта "VK Bot"
# ==================================================================
try:
	os.mkdir(f'{PATH}/Files')
except FileExistsError:
	pass

vk_bot_accounts_db = sqlite3.connect(f'{PATH}/Files/VK_Bot-Accounts-DataBase.db', check_same_thread = False)
vk_bot_accounts_sql = vk_bot_accounts_db.cursor()

vk_bot_accounts_sql.execute("""
	CREATE TABLE IF NOT EXISTS Accounts(
		Login TEXT,
		Password BLOB
	)
""")
vk_bot_accounts_db.commit()
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

def find_file_or_folder(path: str, name: str): # Посик файл/папки
	find_file_or_folder_status = False
	for i in os.listdir(path):
		if i == name:
			find_file_or_folder_status = True
			break
	return find_file_or_folder_status
# ==================================================================

# Логика сервера для проекта "VK Bot"
# ==================================================================
def check_user_login_and_password_and_bot_name(func): # Декоратор
	def wrapper(login, bot_name):
		try:
			user_data = json.loads(request.data.decode('UTF-8'))
			password = user_data['Password']

			lock.acquire(True)
			vk_bot_accounts_sql.execute(f"SELECT * From Accounts WHERE Login = '{login}'")
			account = vk_bot_accounts_sql.fetchone()
			lock.release()

			if account != None:
				enrypted_password = encrypt(password, password)
				if enrypted_password == account[1]:
					if find_file_or_folder(f'{PATH}/Files/{account[0]}', bot_name) == True:
						return func(user_data, login, bot_name)
					else:
						return json.dumps(
							{
								'Answer': f'Бот под именем "{bot_name}" не существует!'
							}, ensure_ascii=False
						), 400
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

def check_user_login_and_password(func): # Декоратор
	def wrapper(login):
		try:
			user_data = json.loads(request.data.decode('UTF-8'))
			password = user_data['Password']

			lock.acquire(True)
			vk_bot_accounts_sql.execute(f"SELECT * From Accounts WHERE Login = '{login}'")
			account = vk_bot_accounts_sql.fetchone()
			lock.release()

			if account != None:
				enrypted_password = encrypt(password, password)
				if enrypted_password == account[1]:
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

@app.route('/vk_bot/registration_account', methods=['POST'])
def registration_account(): # Регистрация
	try:
		user_data = json.loads(request.data.decode('UTF-8'))
		login = user_data['Login']
		password_1 = user_data['Password_1']
		password_2 = user_data['Password_2']

		correct_user_data = True
		if login == '' and password_1 == '' and password_2 == '':
			server_error_answer = 'Введите "Login", "Password_1", "Password_2"!'
			correct_user_data = False
		elif login == '' and password_1 == '':
			server_error_answer = 'Введите "Login" и "Password_1"!'
			correct_user_data = False
		elif login == '' and password_2 == '':
			server_error_answer = 'Введите "Login" и "Password_2"!'
			correct_user_data = False
		elif password_1 == '' and password_2 == '':
			server_error_answer = 'Введите "Password_1" и "Password_2"!'
			correct_user_data = False
		elif login == '':
			server_error_answer = 'Введите "Login"!'
			correct_user_data = False
		elif password_1 == '':
			server_error_answer = 'Введите "Password_1"!'
			correct_user_data = False
		elif password_2 == '':
			server_error_answer = 'Введите "Password_2"!'
			correct_user_data = False

		if correct_user_data == True:
			if password_1 == password_2:
				if len(password_1) >= 8:
					lock.acquire(True)
					vk_bot_accounts_sql.execute(f"SELECT * From Accounts WHERE Login = '{login}'")
					account = vk_bot_accounts_sql.fetchone()
					lock.release()

					if account == None:
						# Шифрования пароля
						encrypted_password = encrypt(password_1, password_1)

						# Запись нового аккаунта в базу данных аккаунтов
						vk_bot_accounts_sql.execute("INSERT INTO Accounts VALUES (?, ?)", (login, encrypted_password))
						vk_bot_accounts_db.commit()

						# Создаём директорию для нового аккаунта пользователя
						os.mkdir(f'{PATH}/Files/{login}')

						return json.dumps(
							{
								'Answer': 'Вы успешно создали аккаунт.'
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
					'Answer': server_error_answer
				}, ensure_ascii=False
			), 400
	except:
		return json.dumps(
			{
				'Answer': 'Неизвестная ошибка на сервере!'
			}, ensure_ascii=False
		), 400

@app.route('/vk_bot/authorization_at_account', methods=['POST'])
def authorization_at_account(): # Авторизация
	try:
		user_data = json.loads(request.data.decode('UTF-8'))
		login = user_data['Login']
		password = user_data['Password']

		correct_user_data = True
		if login == '' and password == '':
			server_error_answer = 'Введите "Login" и "Password"!'
			correct_user_data = False
		elif login == '':
			server_error_answer = 'Введите "Login"!'
			correct_user_data = False
		elif password == '':
			server_error_answer = 'Введите "Password"!'
			correct_user_data = False

		if correct_user_data == True:
			lock.acquire(True)
			vk_bot_accounts_sql.execute(f"SELECT * From Accounts WHERE Login = '{login}'")
			account = vk_bot_accounts_sql.fetchone()
			lock.release()

			if account != None:
				enrypted_password = encrypt(password, password)
				if enrypted_password == account[1]:
					for folder in os.listdir(f'{PATH}/Files/{account[0]}'):
						with open(f'{PATH}/Files/{account[0]}/{folder}/User-Commands.json', 'rb') as file:
							user_commands = file.read()
							user_commands = decrypt(password, user_commands)
							user_commands = json.loads(user_commands)
						for user_command in user_commands:
							if len(user_command.items()) != len(Config.USER_BOT_COMMANDS[0].items()) or len(user_command['Flags'].items()) != len(Config.USER_BOT_COMMANDS[0]['Flags'].items()):
								with open(f'{PATH}/Files/{account[0]}/{folder}/User-Commands.json', 'wb') as file:
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
					'Answer': server_error_answer
				}, ensure_ascii=False
			), 400
	except:
		return json.dumps(
			{
				'Answer': 'Неизвестная ошибка на сервере!'
			}, ensure_ascii=False
		), 400

@app.route('/vk_bot/<string:login>/create_user_bot', methods=['POST'])
@check_user_login_and_password
def create_user_bot(user_data: dict, login: str): # Создание бота
	bot_name = user_data['Bot_Name']
	bot_settings = user_data['Bot_Settings']
	password = user_data['Password']

	server_answer = ''
	if bot_name == '':
		server_answer += 'придумайте имя боту'
	if bot_settings['VK_Token'] == '':
		if server_answer == 'придумайте имя боту':
			server_answer += ' и '
		server_answer += 'введите "VK Token"'
	if bot_settings['Group_ID'] == '':
		if server_answer.find('введите "VK Token"') != -1:
			server_answer += ' и "Group ID"'
		else:
			server_answer += 'введите "Group ID"'
	server_answer += '!'
	server_answer = list(server_answer)[0].capitalize() + ''.join(list(server_answer)[1:-1])
	if server_answer ==  'Придумайте имя боту и введите "VK Token" и "Group ID"':
		server_answer = 'Заполните форму добавления бота!'

	if server_answer == '!':
		if find_file_or_folder(f'{PATH}/Files/{login}', bot_name) == False:
			bot_files_path = f'{PATH}/Files/{login}/{bot_name}'
			os.mkdir(bot_files_path)

			with open(f'{bot_files_path}/Bot-Settings.json', 'wb') as file:
				bot_settings = json.dumps(bot_settings, ensure_ascii=False, indent=2)
				bot_settings = encrypt(password, bot_settings)
				file.write(bot_settings)
			with open(f'{bot_files_path}/User-Commands.json', 'wb') as file:
				user_commands = json.dumps(Config.USER_BOT_COMMANDS, ensure_ascii=False, indent=2)
				user_commands = encrypt(password, user_commands)
				file.write(user_commands)
			with open(f'{bot_files_path}/Log.txt', 'wb') as file:
				log = json.dumps([], ensure_ascii=False, indent=2)
				log = encrypt(password, log)
				file.write(log)
			db = sqlite3.connect(f'{bot_files_path}/VK_Bot-Users-DataBase.db')
			db.close()

			return json.dumps(
				{
					'Answer': 'Успешное создание бота.'
				}, ensure_ascii=False
			), 200
		else:
			return json.dumps(
				{
					'Answer': f'Бот под именем "{bot_name}" уже существует!'
				}, ensure_ascii=False
			), 400
	else:
		return json.dumps(
			{
				'Answer': server_answer
			}, ensure_ascii=False
		), 400

@app.route('/vk_bot/<string:login>/get_user_bot_list', methods=['POST'])
@check_user_login_and_password
def get_user_bot_list(user_data: dict, login: str): # Получение списка ботов
	return json.dumps(
		{
			'Answer': 'Запрос к списку ботов был успешно выполнен.',
			'User_Bot_List': os.listdir(f'{PATH}/Files/{login}')
		}, ensure_ascii=False
	), 200

@app.route('/vk_bot/<string:login>/delete_user_bot', methods=['POST'])
@check_user_login_and_password
def delete_user_bot(user_data: dict, login: str): # Удаление бота
	bot_name = user_data['Bot_Name']

	if find_file_or_folder(f'{PATH}/Files/{login}', bot_name) == True:
		for file in os.listdir(f'{PATH}/Files/{login}/{bot_name}'):
			os.remove(f'{PATH}/Files/{login}/{bot_name}/{file}')
		os.rmdir(f'{PATH}/Files/{login}/{bot_name}')

		return json.dumps(
			{
				'Answer': 'Успешное удаление бота.'
			}, ensure_ascii=False
		), 200
	else:
		return json.dumps(
			{
				'Answer': f'Бот под именем "{bot_name}" не существует!'
			}, ensure_ascii=False
		), 400

@app.route('/vk_bot/<string:login>/<string:bot_name>/bot_settings/get', methods=['POST'])
@check_user_login_and_password_and_bot_name
def user_bot_settings_get(user_data: dict, login: str, bot_name: str): # Получение настроек бота
	password = user_data['Password']

	with open(f'{PATH}/Files/{login}/{bot_name}/Bot-Settings.json', 'rb') as file:
		bot_settings = file.read()
		bot_settings = decrypt(password, bot_settings)
		bot_settings = json.loads(bot_settings)

	return json.dumps(
		{
			'Answer': 'Запрос к файлу "Bot-Settings.json" бота "{bot_name}" был успешно выполнен.',
			'Bot_Settings': bot_settings
		}, ensure_ascii=False
	), 200

@app.route('/vk_bot/<string:login>/<string:bot_name>/bot_settings/update', methods=['POST'])
@check_user_login_and_password_and_bot_name
def user_bot_settings_update(user_data: dict, login: str, bot_name: str): # Обновление настроек бота
	password = user_data['Password']

	with open(f'{PATH}/Files/{login}/{bot_name}/Bot-Settings.json', 'wb') as file:
		bot_settings = json.dumps(user_data['Bot_Settings'], ensure_ascii=False, indent=2)
		bot_settings = encrypt(password, bot_settings)
		file.write(bot_settings)

	return json.dumps(
		{
			'Answer': 'Запрос к файлу "Bot-Settings.json" бота "{bot_name}" был успешно выполнен.'
		}, ensure_ascii=False
	), 200

@app.route('/vk_bot/<string:login>/<string:bot_name>/user_commands/get', methods=['POST'])
@check_user_login_and_password_and_bot_name
def user_commands_get(user_data: dict, login: str, bot_name: str): # Получение команд бота
	password = user_data['Password']

	with open(f'{PATH}/Files/{login}/{bot_name}/User-Commands.json', 'rb') as file:
		user_commands = file.read()
		user_commands = decrypt(password, user_commands)
		user_commands = json.loads(user_commands)

	return json.dumps(
		{
			'Answer': 'Запрос к файлу "User-Commands.json" бота "{bot_name}" был успешно выполнен.',
			'User_Commands': user_commands
		}, ensure_ascii=False
	), 200

@app.route('/vk_bot/<string:login>/<string:bot_name>/user_commands/update', methods=['POST'])
@check_user_login_and_password_and_bot_name
def user_commands_update(user_data: dict, login: str, bot_name: str): # Обновление команд бота
	password = user_data['Password']

	with open(f'{PATH}/Files/{login}/{bot_name}/User-Commands.json', 'wb') as file:
		user_commands = json.dumps(user_data['User_Commands'], ensure_ascii=False, indent=2)
		user_commands = encrypt(password, user_commands)
		file.write(user_commands)

	return json.dumps(
		{
			'Answer': 'Запрос к файлу "User-Commands.json" бота "{bot_name}" был успешно выполнен.'
		}, ensure_ascii=False
	), 200

@app.route('/vk_bot/<string:login>/<string:bot_name>/log/get', methods=['POST'])
@check_user_login_and_password_and_bot_name
def log_get(user_data: dict, login: str, bot_name: str): # Получение логов бота
	password = user_data['Password']

	with open(f'{PATH}/Files/{login}/{bot_name}/Log.txt', 'rb') as file:
		log = file.read()
		log = decrypt(password, log)
		log = json.loads(log)

	return json.dumps(
		{
			'Answer': 'Запрос к файлу "Log.txt" бота "{bot_name}" был успешно выполнен.',
			'Log': log
		}, ensure_ascii=False
	), 200

@app.route('/vk_bot/<string:login>/<string:bot_name>/log/update', methods=['POST'])
@check_user_login_and_password_and_bot_name
def log_update(user_data: dict, login: str, bot_name: str): # Обновление логов бота
	password = user_data['Password']

	with open(f'{PATH}/Files/{login}/{bot_name}/Log.txt', 'wb') as file:
		log = json.dumps(user_data['Log'], ensure_ascii=False, indent=2)
		log = encrypt(password, log)
		file.write(log)

	return json.dumps(
		{
			'Answer': 'Запрос к файлу "Log.txt" бота "{bot_name}" был успешно выполнен.'
		}, ensure_ascii=False
	), 200

@app.route('/vk_bot/<string:login>/<string:bot_name>/database/find', methods=['POST'])
@check_user_login_and_password_and_bot_name
def user_database_find(user_data: dict, login: str, bot_name: str): # Поиск одной записи в БД
	vk_bot_user_db = sqlite3.connect(f'{PATH}/Files/{login}/{bot_name}/VK_Bot-Users-DataBase.db', check_same_thread = False)
	vk_bot_user_sql = vk_bot_user_db.cursor()
	vk_bot_user_sql.execute(user_data['SQLite3_Command'])
	result = vk_bot_user_sql.fetchone()
	vk_bot_user_db.close()

	return json.dumps(
		{
			'Answer': 'Запрос к базе данных бота "{bot_name}" был успешно выполнен.',
			'Result': result
		}, ensure_ascii=False
	), 200

@app.route('/vk_bot/<string:login>/<string:bot_name>/database/find_all', methods=['POST'])
@check_user_login_and_password_and_bot_name
def user_database_find_all(user_data: dict, login: str, bot_name: str): # Поиск несколько записей в БД
	vk_bot_user_db = sqlite3.connect(f'{PATH}/Files/{login}/{bot_name}/VK_Bot-Users-DataBase.db', check_same_thread = False)
	vk_bot_user_sql = vk_bot_user_db.cursor()
	vk_bot_user_sql.execute(user_data['SQLite3_Command'])
	result = vk_bot_user_sql.fetchall()
	vk_bot_user_db.close()

	return json.dumps(
		{
			'Answer': 'Запрос к базе данных бота "{bot_name}" был успешно выполнен.',
			'Result': result
		}, ensure_ascii=False
	), 200

@app.route('/vk_bot/<string:login>/<string:bot_name>/database/edit_database', methods=['POST'])
@check_user_login_and_password_and_bot_name
def edit_user_database(user_data: dict, login: str, bot_name: str): # Редактирования БД
	vk_bot_user_db = sqlite3.connect(f'{PATH}/Files/{login}/{bot_name}/VK_Bot-Users-DataBase.db', check_same_thread = False)
	vk_bot_user_sql = vk_bot_user_db.cursor()

	if 'Values' in user_data:
		vk_bot_user_sql.execute(user_data['SQLite3_Command'], user_data['Values'])
	else:
		vk_bot_user_sql.execute(user_data['SQLite3_Command'])
	vk_bot_user_db.commit()
	vk_bot_user_db.close()

	return json.dumps(
		{
			'Answer': 'Запрос к базе данных бота "{bot_name}" был успешно выполнен.'
		}, ensure_ascii=False
	), 200
# ==================================================================

if __name__ == '__main__':
	app.run(debug = True)