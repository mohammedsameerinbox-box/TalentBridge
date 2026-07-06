import pymysql

connection = pymysql.connect(
    host="localhost",
    user="root",
    password="root123",
    database="TalentBridge",
    cursorclass=pymysql.cursors.Cursor
)

cursor = connection.cursor()