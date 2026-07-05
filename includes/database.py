import mysql.connector

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root123",
    database="TalentBridge"
)

cursor = connection.cursor()

print("Database Connected Successfully!")