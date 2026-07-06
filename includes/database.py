import pymysql
import os

connection = pymysql.connect(
    host=os.environ.get("MYSQLHOST"),
    user=os.environ.get("MYSQLUSER"),
    password=os.environ.get("MYSQLPASSWORD"),
    database=os.environ.get("MYSQLDATABASE"),
    port=int(os.environ.get("MYSQLPORT")),
    cursorclass=pymysql.cursors.Cursor
)

cursor = connection.cursor()