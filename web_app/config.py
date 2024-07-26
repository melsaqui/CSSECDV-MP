import os
from dotenv import load_dotenv
SECRET_KEY = 'sssssssseeeeeeeeeeecrettt'

# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))
import logging
logging.basicConfig(
     format="{asctime} - {levelname} - {message}",
     style="{",
     datefmt="%Y-%m-%d %H:%M",
     level=logging.DEBUG,
     filename="log.txt"
)

load_dotenv("../")
# Enable debug mode.
DEBUG = False
#Make your own .env file with your mysql configurations
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD =  os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")
MYSQL_CURSORCLASS= 'DictCursor'
