import mysql.connector

def connect():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='Aa123456aa',
        port='3306',
        database='saints'
    )