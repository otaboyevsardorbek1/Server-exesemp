# -*- coding: utf-8 -*-

from flask import Flask, request
from Crypto.Cipher import DES
import config as Config
import platform
import sqlite3
import random
import json
import os

# Если сервер на хосте
PATH = os.getcwd()
if platform.system() == 'Windows':
	PATH = PATH.split('\\')
	PATH = '/'.join(PATH[0:len(PATH) - 1])
else:
	PATH += '/Server'

# Если сервер на PC
# PATH = os.getcwd()
# PATH = PATH.split('\\')
# PATH = '/'.join(PATH[0:len(PATH) - 1])

# Создание всех нужных переменных
# ==================================================================
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
		Password BLOB,
		Unique_Key TEXT
	)
""")
vk_bot_accounts_db.commit()
# ==================================================================

# Обычные функции
# ==================================================================
def clear_key(key): # Получение чистого ключа из пароля
	if len(key) < 8:
		while len(key) < 8:
			key += 'd'
		key = key.encode('UTF-8')
	else:
		key = ''.join(list(key)[0:8]).encode('UTF-8')
	return key

def encrypt(key, data): # Шифрование
	def pad(data):
		while len(data) % 8 != 0:
			data += b' '
		return data

	key = clear_key(key)
	des = DES.new(key, DES.MODE_ECB)
	padded_data = pad(data.encode('UTF-8'))
	encrypted_data = des.encrypt(padded_data)
	return encrypted_data

def decrypt(key, encrypted_data): # Дешифровка
	key = clear_key(key)
	des = DES.new(key, DES.MODE_ECB)
	decrypted_data = des.decrypt(encrypted_data)
	return decrypted_data.decode('UTF-8').strip()

def generate_unique_key(): # Генератор уникального ключа
	uniqu_key = ''
	for i in range(20):
		uniqu_key += random.choice('abcdefghijklnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890')
	return uniqu_key
# ==================================================================

# Логика страниц для проекта "VK Bot"
# ==================================================================
def check_user_login_and_password_and_unique_key(func): # Декоратор
	def wrapper():
		try:
			user_data = json.loads(request.data.decode('UTF-8'))
			login = user_data['Login']
			password = user_data['Password']
			unique_key = user_data['Unique_Key']

			vk_bot_accounts_sql.execute(f"SELECT * From Accounts WHERE Login = '{login}'")
			account = vk_bot_accounts_sql.fetchone()

			if account != None:
				enrypted_password = encrypt(password, password)
				if enrypted_password == account[1]:
					if unique_key  == account[2]:
						return func(user_data)
					else:
						return json.dumps(
						{
							'Answer': 'Был передан неверный "Unique_Key"!'
						}, ensure_ascii = False
					), 400
				else:
					return json.dumps(
					{
						'Answer': 'Был передан неверный "Password"!'
					}, ensure_ascii = False
					), 400
			else:
				return json.dumps(
					{
						'Answer': 'Был передан неверный "Login"!'
					}, ensure_ascii = False
					), 400
		except:
			return json.dumps(
				{
					'Answer': 'Неизвестная ошибка на сервере!'
				}, ensure_ascii = False
			), 400
	wrapper.__name__ = func.__name__
	return wrapper

@app.route('/vk_bot/registration', methods = ['POST'])
def vk_bot_registration(): # Регистрация
	try:
		user_data = json.loads(request.data.decode('UTF-8'))
		login = user_data['Login']
		password = user_data['Password']

		vk_bot_accounts_sql.execute(f"SELECT * From Accounts WHERE Login = '{login}'")
		account = vk_bot_accounts_sql.fetchone()

		if account == None:
			# Шифрования пароля
			encrypted_password = encrypt(password, password)

			# Создания уникального ключа для пользователя
			unique_key = generate_unique_key()

			# Запись нового аккаунта в базу данных аккаунтов
			vk_bot_accounts_sql.execute("INSERT INTO Accounts VALUES (?, ?, ?)", (login, encrypted_password, unique_key))
			vk_bot_accounts_db.commit()

			# Создаём директорию для нового аккаунта пользователя
			os.mkdir(f'{PATH}/Files/{unique_key}')

			# Создание всех нужных файлов юзерав
			for deafault_file in Config.DEAFAULT_FILES:
				find_file = False
				for dir_file in os.listdir(f'{PATH}/Files/{unique_key}'):
					if deafault_file == dir_file:
						find_file = True
				if find_file == False:
					with open(f'{PATH}/Files/{unique_key}/{deafault_file}', 'wb') as file:
						data = json.dumps(Config.DEAFAULT_FILES[deafault_file], ensure_ascii = False, indent = 2)
						data = encrypt(password, data)
						file.write(data)
			vk_bot_user_db = sqlite3.connect(f'{PATH}/Files/{unique_key}/VK_Bot-Users-DataBase.db', check_same_thread = False)
			vk_bot_user_db.close()

			return json.dumps(
				{
					'Answer': 'Вы успешно создали аккаунт.'
				}, ensure_ascii = False
			), 200
		else:
			return json.dumps(
				{
					'Answer': f'Login "{login}" уже занят!'
				}, ensure_ascii = False
			), 400
	except:
		return json.dumps(
			{
				'Answer': 'Неизвестная ошибка на сервере!'
			}, ensure_ascii = False
		), 400

@app.route('/vk_bot/authorization', methods = ['POST'])
def vk_bot_authorization(): # Авторизация
	try:
		user_data = json.loads(request.data.decode('UTF-8'))
		login = user_data['Login']
		password = user_data['Password']

		vk_bot_accounts_sql.execute(f"SELECT * From Accounts WHERE Login = '{login}'")
		account = vk_bot_accounts_sql.fetchone()

		if account != None:
			enrypted_password = encrypt(password, password)
			if enrypted_password == account[1]:
				# Создание всех нужных файлов юзерав
				for deafault_file in Config.DEAFAULT_FILES:
					find_file = False
					for dir_file in os.listdir(f'{PATH}/Files/{account[2]}'):
						if deafault_file == dir_file:
							find_file = True
					if find_file == False:
						with open(f'{PATH}/Files/{account[2]}/{deafault_file}', 'wb') as file:
							data = json.dumps(Config.DEAFAULT_FILES[deafault_file], ensure_ascii = False, indent = 2)
							data = encrypt(password, data)
							file.write(data)
				vk_bot_user_db = sqlite3.connect(f'{PATH}/Files/{account[2]}/VK_Bot-Users-DataBase.db', check_same_thread = False)
				vk_bot_user_db.close()

				return json.dumps(
					{
						'Answer': 'Вы успешно авторизовались.',
						'Unique_Key': account[2]
					}, ensure_ascii = False
				), 200
			else:
				return json.dumps(
					{
						'Answer': 'Неверный "Login" или "Password"!'
					}, ensure_ascii = False
				), 400
		else:
			return json.dumps(
				{
					'Answer': 'Такого аккаунта не существует!'
				}, ensure_ascii = False
			), 400
	except:
		return json.dumps(
			{
				'Answer': 'Неизвестная ошибка на сервере!'
			}, ensure_ascii = False
		), 400

@app.route('/vk_bot/files/bot_settings/get', methods = ['POST'])
@check_user_login_and_password_and_unique_key
def vk_bot_files_bot_settings_get(user_data): # Получение настроек бота
	password = user_data['Password']
	unique_key = user_data['Unique_Key']

	with open(f'{PATH}/Files/{unique_key}/Bot-Settings.json', 'rb') as file:
		bot_settings = file.read()
		bot_settings = decrypt(password, bot_settings)
		bot_settings = json.loads(bot_settings)

	return json.dumps(
		{
			'Answer': 'Запрос к файлу "Bot-Settings.json" был успешно выполнен.',
			'Bot_Settings': bot_settings
		}, ensure_ascii = False
	), 200

@app.route('/vk_bot/files/bot_settings/update', methods = ['POST'])
@check_user_login_and_password_and_unique_key
def vk_bot_files_bot_settings_update(user_data): # Обновление настроек бота
	password = user_data['Password']
	unique_key = user_data['Unique_Key']

	with open(f'{PATH}/Files/{unique_key}/Bot-Settings.json', 'wb') as file:
		bot_settings = json.dumps(user_data['Bot_Settings'], ensure_ascii = False, indent = 2)
		bot_settings = encrypt(password, bot_settings)
		file.write(bot_settings)

	return json.dumps(
		{
			'Answer': 'Запрос к файлу "Bot-Settings.json" был успешно выполнен.'
		}, ensure_ascii = False
	), 200

@app.route('/vk_bot/files/user_commands/get', methods = ['POST'])
@check_user_login_and_password_and_unique_key
def vk_bot_files_user_commands_get(user_data): # Получение команд бота
	password = user_data['Password']
	unique_key = user_data['Unique_Key']

	with open(f'{PATH}/Files/{unique_key}/User-Commands.json', 'rb') as file:
		user_commands = file.read()
		user_commands = decrypt(password, user_commands)
		user_commands = json.loads(user_commands)

	return json.dumps(
		{
			'Answer': 'Запрос к файлу "User-Commands.json" был успешно выполнен.',
			'User_Commands': user_commands
		}, ensure_ascii = False
	), 200

@app.route('/vk_bot/files/user_commands/update', methods = ['POST'])
@check_user_login_and_password_and_unique_key
def vk_bot_files_user_commands_update(user_data): # Обновление команд бота
	password = user_data['Password']
	unique_key = user_data['Unique_Key']

	with open(f'{PATH}/Files/{unique_key}/User-Commands.json', 'wb') as file:
		user_commands = json.dumps(user_data['User_Commands'], ensure_ascii = False, indent = 2)
		user_commands = encrypt(password, user_commands)
		file.write(user_commands)

	return json.dumps(
		{
			'Answer': 'Запрос к файлу "User-Commands.json" был успешно выполнен.'
		}, ensure_ascii = False
	), 200

@app.route('/vk_bot/files/log/get', methods = ['POST'])
@check_user_login_and_password_and_unique_key
def vk_bot_files_log_get(user_data): # Получение логов бота
	password = user_data['Password']
	unique_key = user_data['Unique_Key']

	with open(f'{PATH}/Files/{unique_key}/Log.txt', 'rb') as file:
		log = file.read()
		log = decrypt(password, log)
		log = json.loads(log)

	return json.dumps(
		{
			'Answer': 'Запрос к файлу "Log.txt" был успешно выполнен.',
			'Log': log
		}, ensure_ascii = False
	), 200

@check_user_login_and_password_and_unique_key
@app.route('/vk_bot/files/log/update', methods = ['POST'])
def vk_bot_files_log_update(user_data): # Обновление логов бота
	password = user_data['Password']
	unique_key = user_data['Unique_Key']

	with open(f'{PATH}/Files/{unique_key}/Log.txt', 'wb') as file:
		log = json.dumps(user_data['Log'], ensure_ascii = False, indent = 2)
		log = encrypt(password, log)
		file.write(log)

	return json.dumps(
		{
			'Answer': 'Запрос к файлу "Log.txt" был успешно выполнен.'
		}, ensure_ascii = False
	), 200

@app.route('/vk_bot/files/database/find', methods = ['POST'])
@check_user_login_and_password_and_unique_key
def vk_bot_files_database_find(user_data): # Поиск одной записи в БД
	unique_key = user_data['Unique_Key']

	vk_bot_user_db = sqlite3.connect(f'{PATH}/Files/{unique_key}/VK_Bot-Users-DataBase.db', check_same_thread = False)
	vk_bot_user_sql = vk_bot_user_db.cursor()
	result = vk_bot_user_sql.fetchone()
	vk_bot_user_db.close()

	return json.dumps(
		{
			'Answer': 'Запрос к базе данных был успешно выполнен.',
			'Result': result
		}, ensure_ascii = False
	), 200

@app.route('/vk_bot/files/database/find_all', methods = ['POST'])
@check_user_login_and_password_and_unique_key
def vk_bot_files_database_find_all(user_data): # Поиск несколько записей в БД
	unique_key = user_data['Unique_Key']

	vk_bot_user_db = sqlite3.connect(f'{PATH}/Files/{unique_key}/VK_Bot-Users-DataBase.db', check_same_thread = False)
	vk_bot_user_sql = vk_bot_user_db.cursor()
	result = vk_bot_user_sql.fetchall()
	vk_bot_user_db.close()

	return json.dumps(
		{
			'Answer': 'Запрос к базе данных был успешно выполнен.',
			'Result': result
		}, ensure_ascii = False
	), 200

@app.route('/vk_bot/files/database/edit_database', methods = ['POST'])
@check_user_login_and_password_and_unique_key
def vk_bot_files_database_edit_database(user_data): # Редактирования БД
	unique_key = user_data['Unique_Key']

	vk_bot_user_db = sqlite3.connect(f'{PATH}/Files/{unique_key}/VK_Bot-Users-DataBase.db', check_same_thread = False)
	vk_bot_user_sql = vk_bot_user_db.cursor()

	if 'Values' in user_data:
		vk_bot_user_sql.execute(user_data['SQLite3_Command'], user_data['Values'])
	else:
		vk_bot_user_sql.execute(user_data['SQLite3_Command'])
	vk_bot_user_db.commit()
	vk_bot_user_db.close()

	return json.dumps(
		{
			'Answer': 'Запрос к базе данных был успешно выполнен.'
		}, ensure_ascii = False
	), 200
# ==================================================================

if __name__ == '__main__':
	app.run(debug = True)