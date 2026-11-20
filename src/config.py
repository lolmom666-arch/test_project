import os
from dotenv import load_dotenv

load_dotenv()
SSH_USER = os.getenv("SSH_USER")
DEV_STAND = os.getenv("DEV_STAND")
BASE_URL = f"https://{DEV_STAND}.dev-mst.com"
DB_USER = os.getenv("DB_USER")
PASSWORD = os.getenv("PASSWORD", "")