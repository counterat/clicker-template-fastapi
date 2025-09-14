from dotenv import load_dotenv
import os

load_dotenv()


DBNAME = os.getenv("DBNAME")
DBUSER = os.getenv("DBUSER")
DBPASS = os.getenv("DBPASS")
DBDOMAIN = os.getenv("DBDOMAIN")
BOTTOKEN = os.getenv("BOTTOKEN")
BOTURL = os.getenv("BOTURL")


REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_DB = os.getenv("REDIS_DB")

ENERGY_REFILLS = int(os.getenv("ENERGY_REFILLS"))

REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

ENV = os.getenv("ENV")

DATABASE_URL = f"postgresql+asyncpg://{DBUSER}:{DBPASS}@{DBDOMAIN}:5432/{DBNAME}"
DATABASE_URL_SYNC = f"postgresql://{DBUSER}:{DBPASS}@{DBDOMAIN}:5432/{DBNAME}"

FRONT_URL = os.getenv("FRONT_URL")

def test_user(ip="ubuntu"):
    if ip == "ubuntu":
        return {
            "id":1,
            "first_name":"ubuntu",
            "last_name":"ubuntu",
            "username":"ubuntu",
            "language_code":"ru",
            "name":"name",
            "photo_url":"https://telegra.ph/file/99e7fb4ff14703f8d0d7f.png",
            "is_premium":True,
            
        }
    else:
        return {
            "id":6032759612,
            "first_name":"name",
            "last_name":"name",
            "username":"username",
            "language_code":"ru",
            "name":"name",
            "photo_url":"https://telegra.ph/file/99e7fb4ff14703f8d0d7f.png",
            "is_premium":True,
        }
        
