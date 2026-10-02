import os
from dotenv import load_dotenv

load_dotenv()
SSH_HOST = os.getenv("SSH_HOST")
SSH_USER = os.getenv("SSH_USER")
DEV_STAND = os.getenv("DEV_STAND")
BASE_URL = f"https://{DEV_STAND}.dev-mst.com"
HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT", "2601"))
PASSWORD = os.getenv("PASSWORD", "")
DATABASE = os.getenv("DATABASE")