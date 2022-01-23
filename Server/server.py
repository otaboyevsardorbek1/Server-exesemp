from flask import Flask, request
import threading
import platform
import sqlite3
import random
import json
import os

# Узнаем текущию деректорию (Нужно для хоста)
PATH = os.getcwd()
if platform.system() == 'Windows':
	PATH = PATH.split('\\')
	PATH = '/'.join(PATH[0:len(PATH) - 1])
else:
	PATH += '/Server'

def generate_uniqu_key():
	password = ''
	for i in range(20):
		password += random.choice('abcdefghijklnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890')
	return password

lock = threading.Lock()
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

ACCOUNTS = {}
for account in sql.execute("SELECT * From Accounts"):
	dir_find = False
	for dir in os.listdir(f'{PATH}/Files'):
		if dir == account[2]:
			dir_find = True
	if dir_find == False:
		os.mkdir(f'{PATH}/Files/{account[2]}')
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
				'sql': ACCOUNTS[account[2]]['db'].cursor(),
				'db': ACCOUNTS[account[2]]['db']
			}
		}
	)

app = Flask(__name__)

@app.route('/vk_bot/registration', methods = ['POST'])
def vk_api_registration():
	user_data = json.loads(request.data.decode('UTF-8'))
	sql.execute(f"SELECT * From Accounts WHERE Login = '{user_data['Login']}'")
	account = sql.fetchone()
	if account == None:
		sql.execute("INSERT INTO Accounts VALUES (?, ?, ?)", (user_data['Login'], user_data['Password'], generate_uniqu_key()))
		db.commit()
		sql.execute(f"SELECT * From Accounts WHERE Login = '{user_data['Login']}'")
		account = sql.fetchone()
		os.mkdir(f'{PATH}/Files/{account[2]}')
		
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
					'sql': ACCOUNTS[account[2]]['db'].cursor(),
					'db': ACCOUNTS[account[2]]['db']
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

@app.route('/vk_bot/authorization', methods = ['POST'])
def vk_api_authorization():
	user_data = json.loads(request.data.decode('UTF-8'))
	sql.execute(f"SELECT * From Accounts WHERE Login = '{user_data['Login']}'")
	account = sql.fetchone()
	if account != None:
		if account[1] == user_data['Password']:
			return json.dumps(
				{
					'Answer': 'Вы успешно авторизовались.',
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

@app.route('/vk_bot/files/database/find', methods = ['POST'])
def vk_api_database_find():
	try:
		user_data = json.loads(request.data.decode('UTF-8'))
		if user_data['Unique_Key'] in ACCOUNTS:
			ACCOUNTS[user_data['Unique_Key']]['sql'].execute(user_data['SQLite3_Command'])
			result = ACCOUNTS[user_data['Unique_Key']]['sql'].fetchone()
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
def vk_api_database_find_all():
	try:
		user_data = json.loads(request.data.decode('UTF-8'))
		if user_data['Unique_Key'] in ACCOUNTS:
			ACCOUNTS[user_data['Unique_Key']]['sql'].execute(user_data['SQLite3_Command'])
			result = ACCOUNTS[user_data['Unique_Key']]['sql'].fetchall()
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
def vk_api_database_edit_database():
	try:
		user_data = json.loads(request.data.decode('UTF-8'))
		if user_data['Unique_Key'] in ACCOUNTS:
			if 'Values' in user_data:
				ACCOUNTS[user_data['Unique_Key']]['sql'].execute(user_data['SQLite3_Command'], user_data['Values'])
			else:
				ACCOUNTS[user_data['Unique_Key']]['sql'].execute(user_data['SQLite3_Command'])
			ACCOUNTS[user_data['Unique_Key']]['db'].commit()
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

if __name__ == '__main__':
	app.run(debug = True)