import mysql.connector
import config

def get_db_connection():
    return mysql.connector.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        port=config.DB_PORT,
        password=config.DB_PASSWORD,
        database=config.DB_NAME
    )
