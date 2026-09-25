import pymysql
from src.config import HOST, SSH_USER, PASSWORD, DATABASE, PORT

connect_db = {
    "host": f"{HOST}",
    "user": f"{SSH_USER}",
    "port": PORT,
    "password": f"{PASSWORD}",
    "database": f"{DATABASE}",
}
client_db = pymysql.connect(**connect_db)
