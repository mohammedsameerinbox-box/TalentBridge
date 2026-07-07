import pymysql
import os

if os.environ.get("MYSQLHOST"):
    # Render / Railway
    connection = pymysql.connect(
        host=os.environ.get("MYSQLHOST"),
        user=os.environ.get("MYSQLUSER"),
        password=os.environ.get("MYSQLPASSWORD"),
        database=os.environ.get("MYSQLDATABASE"),
        port=int(os.environ.get("MYSQLPORT")),
        cursorclass=pymysql.cursors.Cursor
    )
else:
    # Local MySQL Workbench
    connection = pymysql.connect(
        host="127.0.0.1",
        user="root",
        password="root123",
        database="talentbridge",
        port=3306,
        cursorclass=pymysql.cursors.Cursor
    )

cursor = connection.cursor()