import os
from dotenv import load_dotenv
from datetime import datetime,date

SECRET_KEY = 'sssssssseeeeeeeeeeecrettt'
#now=datetime.now()
today = date.today()
today=today.strftime('%b_%d_%Y')
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))
#current_time = now.strftime('%H_%M_%S')
file_name =f'log_{str(today)}.txt'
path="./logs//"+file_name

import logging
logging.basicConfig(
     format="{asctime} - {levelname} - {message}",
     style="{",
     datefmt="%Y-%m-%d %H:%M:%S",
     level=logging.DEBUG,
     filename=path
)

load_dotenv("../")
# Enable debug mode.
DEBUG = False #Should be false by default
#Make your own .env file with your mysql configurations
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD =  os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")
MYSQL_CURSORCLASS= 'DictCursor'

# Directory for uploaded files
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'Uploads')  # Absolute path

