# -*- coding: utf-8 -*-

USER_BOT_COMMANDS = [
	{
		'Command_Name': 'Приветствие нового пользователя',
		'Command': '!Приветствие нового пользователя',
		'Flags': {
			'Message_For_New_User': True,
			'Message_For_Up_Level': False,
			'Show_Command_In_Commands_List': False
		},
		'Command_Answer': """\
Добро пожаловать {user}!
Так как я тебя раньше не видел, попрошу тебя ознакомится с списком команд через команду "!Список команд"."""
	},
	{
		'Command_Name': 'Получение нового уровня',
		'Command': '!Получение нового уровня',
		'Flags': {
			'Message_For_New_User': False,
			'Message_For_Up_Level': True,
			'Show_Command_In_Commands_List': False
		},
		'Command_Answer': 'Пользователь {user} получил новый уровень!'
	},
	{
		'Command_Name': 'Вывод статистики',
		'Command': '!Статистика',
		'Flags': {
			'Message_For_New_User': False,
			'Message_For_Up_Level': False,
			'Show_Command_In_Commands_List': True
		},
		'Command_Answer': """\
Вас зовут: {user}
Ваш балланс: {db[2]}
Ваш уровень: {db[1]}
Ваш опыт: {db[3]}"""
	},
	{
		'Command_Name': 'Вывод статистики другого пользователя',
		'Command': '!Статистика пользователя {take_user_id}',
		'Flags': {
			'Message_For_New_User': False,
			'Message_For_Up_Level': False,
			'Show_Command_In_Commands_List': True
		},
		'Command_Answer': """\
Имя пользователя: {other_user}
Ранг пользователя: {other_db[4]}
Балланс пользователя: {other_db[2]}
Уровень пользователя: {other_db[1]}
Опыт пользователя: {other_db[3]}"""
	},
	{
		'Command_Name': 'Вывод список команд',
		'Command': '!Список команд',
		'Flags': {
			'Message_For_New_User': False,
			'Message_For_Up_Level': False,
			'Show_Command_In_Commands_List': True
		},
		'Command_Answer': """\
Список команд:
{all_commands}"""
	}
]