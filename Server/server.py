# -*- coding: utf-8 -*-

from flask import Flask, request
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

ACCOUNTS = {}
# ==================================================================

# Обычные функции
# ==================================================================
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
		Password TEXT,
		Unique_Key TEXT
	)
""")
db.commit()
# ==================================================================

# Подключение DB пользователей
# ==================================================================
for account in sql.execute("SELECT * From Accounts"):
	ACCOUNTS.update(
		{
			account[2]: {
				'db': sqlite3.connect(f'{PATH}/Files/{account[2]}/VK_Bot-Users-DataBase.db', check_same_thread = False)
			}
		}
	)
	ACCOUNTS.update(
		{
			account[2]: {
				'Bot_Settings': f'{PATH}/Files/{account[2]}/Bot-Settings.json',
				'User_Commands': f'{PATH}/Files/{account[2]}/User-Commands.json',
				'Log': f'{PATH}/Files/{account[2]}/Log.txt',
				'sql': ACCOUNTS[account[2]]['db'].cursor(),
				'db': ACCOUNTS[account[2]]['db']
			}
		}
	)
# ==================================================================

# Логика страниц для "VK-Bot"
# ==================================================================
@app.route('/vk_bot/registration', methods = ['POST'])
def vk_bot_registration(): # Регистрация
	try:
		user_data = json.loads(request.data.decode('UTF-8'))

		sql.execute(f"SELECT * From Accounts WHERE Login = '{user_data['Login']}'")
		account = sql.fetchone()

		if account == None:
			# Создания уникального ключа для пользователя
			uniqu_key = generate_unique_key()

			# Запись нового аккаунта в базу данных аккаунтов
			sql.execute("INSERT INTO Accounts VALUES (?, ?, ?)", (user_data['Login'], user_data['Password'], uniqu_key))
			db.commit()

			# Создаём директорию для нового аккаунта пользователя
			os.mkdir(f'{PATH}/Files/{uniqu_key}')

			# Создание файла "Bot-Settings.json"
			with open(f'{PATH}/Files/{uniqu_key}/Bot-Settings.json', 'a') as file:
				data = {
					'Automati_Save_Log': False,
					'User_Commands': False,
					'VK_Token': '',
					'Group_ID': ''
				}
				file.write(json.dumps(data, ensure_ascii = False, indent = 2))

			# Создание файла "User-Commands.json"
			with open(f'{PATH}/Files/{uniqu_key}/User-Commands.json', 'a') as file:
				file.write(json.dumps([], ensure_ascii = False, indent = 2))

			# Создание файла "Log.txt.json"
			with open(f'{PATH}/Files/{uniqu_key}/Log.txt', 'a') as file:
				file.write(json.dumps([], ensure_ascii = False, indent = 2))

			# Запись в константу "ACCOUNTS" нового пользователя
			ACCOUNTS.update(
				{
					uniqu_key: {
						'db': sqlite3.connect(f'{PATH}/Files/{uniqu_key}/VK_Bot-Users-DataBase.db', check_same_thread = False)
					}
				}
			)
			ACCOUNTS.update(
				{
					uniqu_key: {
						'Bot_Settings': f'{PATH}/Files/{uniqu_key}/Bot-Settings.json',
						'User_Commands': f'{PATH}/Files/{uniqu_key}/User-Commands.json',
						'Log': f'{PATH}/Files/{uniqu_key}/Log.txt',
						'sql': ACCOUNTS[uniqu_key]['db'].cursor(),
						'db': ACCOUNTS[uniqu_key]['db']
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
					'Answer': f"Login \"{user_data['Login']}\" уже занят!"
				}, ensure_ascii = False
			), 400
	except:
		return json.dumps(
			{
				'Answer': 'Ошибка на сервере!'
			}, ensure_ascii = False
		), 400

@app.route('/vk_bot/authorization', methods = ['POST'])
def vk_bot_authorization(): # Авторизация
	try:
		user_data = json.loads(request.data.decode('UTF-8'))

		sql.execute(f"SELECT * From Accounts WHERE Login = '{user_data['Login']}'")
		account = sql.fetchone()

		if account != None:
			if account[1] == user_data['Password']:
				# Получение настроек бота
				with open(ACCOUNTS[account[2]]['Bot_Settings'], 'r') as file:
					bot_settings = json.loads(file.read())

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
						'Answer': 'Неверный Login или Password!'
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
				'Answer': 'Ошибка на сервере!'
			}, ensure_ascii = False
		), 400

@app.route('/vk_bot/files/bot_settings/update', methods = ['POST'])
def vk_bot_files_bot_settings_update(): # Обновление настроек бота
	try:
		user_data = json.loads(request.data.decode('UTF-8'))
		unique_key = user_data['Unique_Key']

		if unique_key in ACCOUNTS:
			with open(ACCOUNTS[unique_key]['Bot_Settings'], 'w') as file:
				file.write(json.dumps(user_data['Bot_Settings'], ensure_ascii = False, indent = 2))

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
				'Answer': 'Ошибка на сервере!'
			}, ensure_ascii = False
		), 400

@app.route('/vk_bot/files/bot_settings/get', methods = ['POST'])
def vk_bot_files_bot_settings_get(): # Получение настроек бота
	try:
		user_data = json.loads(request.data.decode('UTF-8'))
		unique_key = user_data['Unique_Key']

		if unique_key in ACCOUNTS:
			with open(ACCOUNTS[unique_key]['Bot_Settings'], 'r') as file:
				bot_settings = json.loads(file.read())

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
				'Answer': 'Ошибка на сервере!'
			}, ensure_ascii = False
		), 400

@app.route('/vk_bot/files/user_commands/update', methods = ['POST'])
def vk_bot_files_user_commands_update(): # Обновление команд бота
	try:
		user_data = json.loads(request.data.decode('UTF-8'))
		unique_key = user_data['Unique_Key']

		if unique_key in ACCOUNTS:
			with open(ACCOUNTS[unique_key]['User_Commands'], 'w') as file:
				file.write(json.dumps(user_data['User_Commands'], ensure_ascii = False, indent = 2))

			return json.dumps(
				{
					'Answer': 'Запрос к файлу "User-Commands.json" был успешно выполнен.'
				}, ensure_ascii = False
			), 200
	except:
		return json.dumps(
			{
				'Answer': 'Ошибка на сервере!'
			}, ensure_ascii = False
		), 400

@app.route('/vk_bot/files/user_commands/get', methods = ['POST'])
def vk_bot_files_user_commands_get(): # Получение команд бота
	try:
		user_data = json.loads(request.data.decode('UTF-8'))
		unique_key = user_data['Unique_Key']

		if unique_key in ACCOUNTS:
			with open(ACCOUNTS[unique_key]['User_Commands'], 'r') as file:
				user_commands = json.loads(file.read())

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
				'Answer': 'Ошибка на сервере!'
			}, ensure_ascii = False
		), 400

@app.route('/vk_bot/files/log/update', methods = ['POST'])
def vk_bot_files_log_update(): # Обновление логов бота
	try:
		user_data = json.loads(request.data.decode('UTF-8'))
		unique_key = user_data['Unique_Key']

		if unique_key in ACCOUNTS:
			with open(ACCOUNTS[unique_key]['Log'], 'w') as file:
				file.write(json.dumps(user_data['Log'], ensure_ascii = False, indent = 2))

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
				'Answer': 'Ошибка на сервере!'
			}, ensure_ascii = False
		), 400

@app.route('/vk_bot/files/log/get', methods = ['POST'])
def vk_bot_files_log_get(): # Получение логов бота
	try:
		user_data = json.loads(request.data.decode('UTF-8'))
		unique_key = user_data['Unique_Key']

		if unique_key in ACCOUNTS:
			with open(ACCOUNTS[unique_key]['Log'], 'r') as file:
				log = json.loads(file.read())

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
				'Answer': 'Ошибка на сервере!'
			}, ensure_ascii = False
		), 400

@app.route('/vk_bot/files/database/find', methods = ['POST'])
def vk_bot_files_database_find(): # Поиск одной записи в БД
	try:
		user_data = json.loads(request.data.decode('UTF-8'))
		unique_key = user_data['Unique_Key']

		if unique_key in ACCOUNTS:
			ACCOUNTS[unique_key]['sql'].execute(user_data['SQLite3_Command'])
			result = ACCOUNTS[unique_key]['sql'].fetchone()

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

		if unique_key in ACCOUNTS:
			ACCOUNTS[unique_key]['sql'].execute(user_data['SQLite3_Command'])
			result = ACCOUNTS[unique_key]['sql'].fetchall()

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
				'Answer': 'Ошибка на сервере!'
			}, ensure_ascii = False
		), 400

@app.route('/vk_bot/files/database/edit_database', methods = ['POST'])
def vk_bot_files_database_edit_database(): # Редактирования БД
	try:
		user_data = json.loads(request.data.decode('UTF-8'))
		unique_key = user_data['Unique_Key']

		if unique_key in ACCOUNTS:

			if 'Values' in user_data:
				ACCOUNTS[unique_key]['sql'].execute(user_data['SQLite3_Command'], user_data['Values'])
			else:
				ACCOUNTS[unique_key]['sql'].execute(user_data['SQLite3_Command'])
			ACCOUNTS[unique_key]['db'].commit()

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
				'Answer': 'Ошибка на сервере!'
			}, ensure_ascii = False
		), 400
# ==================================================================

if __name__ == '__main__':
	app.run(debug = True)