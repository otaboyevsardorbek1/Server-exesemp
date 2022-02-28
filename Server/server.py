# -*- coding: utf-8 -*-

from flask import Flask, request
from Crypto.Cipher import DES
import platform
import sqlite3
import random
import json
import os

# Узнаем текущию деректорию (Нужно для хоста)
# ==================================================================
PATH = os.getcwd()
if platform.system() == 'Windows':
	PATH = PATH.split('\\')
	PATH = '/'.join(PATH[0:len(PATH) - 1])
else:
	PATH += '/Server'
# ==================================================================

# Создание всех нужных переменных
# ==================================================================
app = Flask(__name__)

accounts = {}
# ==================================================================

# Обычные функции
# ==================================================================
def clear_key(key):
	if len(key) < 8:
		while len(key) < 8:
			key += 'd'
		key = key.encode('UTF-8')
	else:
		key = ''.join(list(key)[0:8]).encode('UTF-8')
	return key

def encrypt(key, data):
	def pad(data):
		while len(data) % 8 != 0:
			data += b' '
		return data

	key = clear_key(key)
	des = DES.new(key, DES.MODE_ECB)
	padded_data = pad(data.encode('UTF-8'))
	encrypted_data = des.encrypt(padded_data)
	return encrypted_data

def decrypt(key, encrypted_data):
	key = clear_key(key)
	des = DES.new(key, DES.MODE_ECB)
	decrypted_data = des.decrypt(encrypted_data)
	return decrypted_data.decode('UTF-8').strip()

def generate_unique_key():
	uniqu_key = ''
	for i in range(20):
		uniqu_key += random.choice('abcdefghijklnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890')
	return uniqu_key
# ==================================================================

# Подключение основной DB
# ==================================================================
db = sqlite3.connect(f'{PATH}/Files/VK_Bot-Accounts-DataBase.db', check_same_thread = False)
sql = db.cursor()

sql.execute("""
	CREATE TABLE IF NOT EXISTS Accounts(
		Login TEXT,
		Password BLOB,
		Unique_Key TEXT
	)
""")
db.commit()
# ==================================================================

# Подключение DB пользователей
# ==================================================================
for account in sql.execute("SELECT * From Accounts"):
	accounts.update(
		{
			account[2]: {
				'db': sqlite3.connect(f'{PATH}/Files/{account[2]}/VK_Bot-Users-DataBase.db', check_same_thread = False)
			}
		}
	)
	accounts.update(
		{
			account[2]: {
				'Bot_Settings': f'{PATH}/Files/{account[2]}/Bot-Settings.json',
				'User_Commands': f'{PATH}/Files/{account[2]}/User-Commands.json',
				'Log': f'{PATH}/Files/{account[2]}/Log.txt',
				'sql': accounts[account[2]]['db'].cursor(),
				'db': accounts[account[2]]['db']
			}
		}
	)
# ==================================================================

# Логика страниц для проекта "VK-Bot"
# ==================================================================
@app.route('/vk_bot/registration', methods = ['POST'])
def vk_bot_registration(): # Регистрация
	try:
		user_data = json.loads(request.data.decode('UTF-8'))
		login = user_data['Login']
		password = user_data['Password']

		sql.execute(f"SELECT * From Accounts WHERE Login = '{login}'")
		account = sql.fetchone()

		if account == None:
			# Шифрования пароля
			encrypted_password = encrypt(password, password)
			print(encrypted_password)

			# Создания уникального ключа для пользователя
			uniqu_key = generate_unique_key()

			# Запись нового аккаунта в базу данных аккаунтов
			sql.execute("INSERT INTO Accounts VALUES (?, ?, ?)", (login, encrypted_password, uniqu_key))
			db.commit()

			# Создаём директорию для нового аккаунта пользователя
			os.mkdir(f'{PATH}/Files/{uniqu_key}')

			# Создание файла "Bot-Settings.json"
			with open(f'{PATH}/Files/{uniqu_key}/Bot-Settings.json', 'ab') as file:
				data = {
					'Automati_Save_Log': False,
					'User_Commands': False,
					'VK_Token': '',
					'Group_ID': ''
				}
				data = json.dumps(data, ensure_ascii = False, indent = 2)
				data = encrypt(password, data)
				file.write(data)

			# Создание файла "User-Commands.json"
			with open(f'{PATH}/Files/{uniqu_key}/User-Commands.json', 'ab') as file:
				data = json.dumps([], ensure_ascii = False, indent = 2)
				data = encrypt(password, data)
				file.write(data)


			# Создание файла "Log.txt.json"
			with open(f'{PATH}/Files/{uniqu_key}/Log.txt', 'ab') as file:
				data = json.dumps([], ensure_ascii = False, indent = 2)
				data = encrypt(password, data)
				file.write(data)


			# Запись в константу "accounts" нового пользователя
			accounts.update(
				{
					uniqu_key: {
						'db': sqlite3.connect(f'{PATH}/Files/{uniqu_key}/VK_Bot-Users-DataBase.db', check_same_thread = False)
					}
				}
			)
			accounts.update(
				{
					uniqu_key: {
						'Bot_Settings': f'{PATH}/Files/{uniqu_key}/Bot-Settings.json',
						'User_Commands': f'{PATH}/Files/{uniqu_key}/User-Commands.json',
						'Log': f'{PATH}/Files/{uniqu_key}/Log.txt',
						'sql': accounts[uniqu_key]['db'].cursor(),
						'db': accounts[uniqu_key]['db']
					}
				}
			)

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

		sql.execute(f"SELECT * From Accounts WHERE Login = '{login}'")
		account = sql.fetchone()

		if account != None:
			# Расшифрования пароля
			decrypted_account_password = decrypt(password, account[1])

			if decrypted_account_password == password:
				# Получение настроек бота
				with open(accounts[account[2]]['Bot_Settings'], 'rb') as file:
					bot_settings = file.read()
					bot_settings = decrypt(password, bot_settings)
					bot_settings = json.loads(bot_settings)

				return json.dumps(
					{
						'Answer': 'Вы успешно авторизовались.',
						'Bot_Settings': bot_settings,
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
def vk_bot_files_bot_settings_get(): # Получение настроек бота
	try:
		user_data = json.loads(request.data.decode('UTF-8'))
		password = user_data['Password']
		unique_key = user_data['Unique_Key']

		if unique_key in accounts:
			with open(accounts[unique_key]['Bot_Settings'], 'rb') as file:
				bot_settings = file.read()
				bot_settings = decrypt(password, bot_settings)
				bot_settings = json.loads(bot_settings)

			return json.dumps(
				{
					'Answer': 'Запрос к файлу "Bot-Settings.json" был успешно выполнен.',
					'Bot_Settings': bot_settings
				}, ensure_ascii = False
			), 200
		else:
			return json.dumps(
				{
					'Answer': 'Неизвестная ошибка на сервере!'
				}, ensure_ascii = False
			), 400
	except:
		return json.dumps(
			{
				'Answer': 'Неизвестная ошибка на сервере!'
			}, ensure_ascii = False
		), 400

@app.route('/vk_bot/files/bot_settings/update', methods = ['POST'])
def vk_bot_files_bot_settings_update(): # Обновление настроек бота
	try:
		user_data = json.loads(request.data.decode('UTF-8'))
		password = user_data['Password']
		unique_key = user_data['Unique_Key']

		if unique_key in accounts:
			with open(accounts[unique_key]['Bot_Settings'], 'wb') as file:
				bot_settings = json.dumps(user_data['Bot_Settings'], ensure_ascii = False, indent = 2)
				bot_settings = encrypt(password, bot_settings)
				file.write(bot_settings)

			return json.dumps(
				{
					'Answer': 'Запрос к файлу "Bot-Settings.json" был успешно выполнен.'
				}, ensure_ascii = False
			), 200
		else:
			return json.dumps(
				{
					'Answer': 'Неизвестная ошибка на сервере!'
				}, ensure_ascii = False
			), 400
	except:
		return json.dumps(
			{
				'Answer': 'Неизвестная ошибка на сервере!'
			}, ensure_ascii = False
		), 400

@app.route('/vk_bot/files/user_commands/get', methods = ['POST'])
def vk_bot_files_user_commands_get(): # Получение команд бота
	try:
		user_data = json.loads(request.data.decode('UTF-8'))
		password = user_data['Password']
		unique_key = user_data['Unique_Key']

		if unique_key in accounts:
			with open(accounts[unique_key]['User_Commands'], 'rb') as file:
				user_commands = file.read()
				user_commands = decrypt(password, user_commands)
				user_commands = json.loads(user_commands)

			return json.dumps(
				{
					'Answer': 'Запрос к файлу "Bot-Settings.json" был успешно выполнен.',
					'User_Commands': user_commands
				}, ensure_ascii = False
			), 200
		else:
			return json.dumps(
				{
					'Answer': 'Неизвестная ошибка на сервере!'
				}, ensure_ascii = False
			), 400
	except:
		return json.dumps(
			{
				'Answer': 'Неизвестная ошибка на сервере!'
			}, ensure_ascii = False
		), 400

@app.route('/vk_bot/files/user_commands/update', methods = ['POST'])
def vk_bot_files_user_commands_update(): # Обновление команд бота
	try:
		user_data = json.loads(request.data.decode('UTF-8'))
		password = user_data['Password']
		unique_key = user_data['Unique_Key']

		if unique_key in accounts:
			with open(accounts[unique_key]['User_Commands'], 'wb') as file:
				user_commands = json.dumps(user_data['User_Commands'], ensure_ascii = False, indent = 2)
				user_commands = encrypt(password, user_commands)
				file.write(user_commands)

			return json.dumps(
				{
					'Answer': 'Запрос к файлу "User-Commands.json" был успешно выполнен.'
				}, ensure_ascii = False
			), 200
	except:
		return json.dumps(
			{
				'Answer': 'Неизвестная ошибка на сервере!'
			}, ensure_ascii = False
		), 400

@app.route('/vk_bot/files/log/get', methods = ['POST'])
def vk_bot_files_log_get(): # Получение логов бота
	try:
		user_data = json.loads(request.data.decode('UTF-8'))
		password = user_data['Password']
		unique_key = user_data['Unique_Key']

		if unique_key in accounts:
			with open(accounts[unique_key]['Log'], 'rb') as file:
				log = file.read()
				log = decrypt(password, log)
				log = json.loads(log)

			return json.dumps(
				{
					'Answer': 'Запрос к файлу "Log.txt" был успешно выполнен.',
					'Log': log
				}, ensure_ascii = False
			), 200
		else:
			return json.dumps(
				{
					'Answer': 'Неизвестная ошибка на сервере!'
				}, ensure_ascii = False
			), 400
	except:
		return json.dumps(
			{
				'Answer': 'Неизвестная ошибка на сервере!'
			}, ensure_ascii = False
		), 400

@app.route('/vk_bot/files/log/update', methods = ['POST'])
def vk_bot_files_log_update(): # Обновление логов бота
	try:
		user_data = json.loads(request.data.decode('UTF-8'))
		password = user_data['Password']
		unique_key = user_data['Unique_Key']

		if unique_key in accounts:
			with open(accounts[unique_key]['Log'], 'wb') as file:
				log = json.dumps(user_data['Log'], ensure_ascii = False, indent = 2)
				log = encrypt(password, log)
				file.write(log)

			return json.dumps(
				{
					'Answer': 'Запрос к файлу "Log.txt" был успешно выполнен.'
				}, ensure_ascii = False
			), 200
		else:
			return json.dumps(
				{
					'Answer': 'Неизвестная ошибка на сервере!'
				}, ensure_ascii = False
			), 400
	except:
		return json.dumps(
			{
				'Answer': 'Неизвестная ошибка на сервере!'
			}, ensure_ascii = False
		), 400

@app.route('/vk_bot/files/database/find', methods = ['POST'])
def vk_bot_files_database_find(): # Поиск одной записи в БД
	try:
		user_data = json.loads(request.data.decode('UTF-8'))
		unique_key = user_data['Unique_Key']

		if unique_key in accounts:
			accounts[unique_key]['sql'].execute(user_data['SQLite3_Command'])
			result = accounts[unique_key]['sql'].fetchone()

			return json.dumps(
				{
					'Answer': 'Запрос к базе данных был успешно выполнен.',
					'Result': result
				}, ensure_ascii = False
			), 200
		else:
			return json.dumps(
				{
					'Answer': 'Неизвестная ошибка на сервере!'
				}, ensure_ascii = False
			), 400
	except:
		return json.dumps(
			{
				'Answer': 'Неизвестная ошибка на сервере!'
			}, ensure_ascii = False
		), 400

@app.route('/vk_bot/files/database/find_all', methods = ['POST'])
def vk_bot_files_database_find_all(): # Поиск несколько записей в БД
	try:
		user_data = json.loads(request.data.decode('UTF-8'))
		unique_key = user_data['Unique_Key']

		if unique_key in accounts:
			accounts[unique_key]['sql'].execute(user_data['SQLite3_Command'])
			result = accounts[unique_key]['sql'].fetchall()

			return json.dumps(
				{
					'Answer': 'Запрос к базе данных был успешно выполнен.',
					'Result': result
				}, ensure_ascii = False
			), 200
		else:
			return json.dumps(
				{
					'Answer': 'Неизвестная ошибка на сервере!'
				}, ensure_ascii = False
			), 400
	except:
		return json.dumps(
			{
				'Answer': 'Неизвестная ошибка на сервере!'
			}, ensure_ascii = False
		), 400

@app.route('/vk_bot/files/database/edit_database', methods = ['POST'])
def vk_bot_files_database_edit_database(): # Редактирования БД
	try:
		user_data = json.loads(request.data.decode('UTF-8'))
		unique_key = user_data['Unique_Key']

		if unique_key in accounts:

			if 'Values' in user_data:
				accounts[unique_key]['sql'].execute(user_data['SQLite3_Command'], user_data['Values'])
			else:
				accounts[unique_key]['sql'].execute(user_data['SQLite3_Command'])
			accounts[unique_key]['db'].commit()

			return json.dumps(
				{
					'Answer': 'Запрос к базе данных был успешно выполнен.'
				}, ensure_ascii = False
			), 200
		else:
			return json.dumps(
				{
					'Answer': 'Неизвестная ошибка на сервере!'
				}, ensure_ascii = False
			), 400
	except:
		return json.dumps(
			{
				'Answer': 'Неизвестная ошибка на сервере!'
			}, ensure_ascii = False
		), 400
# ==================================================================

if __name__ == '__main__':
	app.run(debug = True)