import os
from dotenv import load_dotenv

load_dotenv()  # Cargar el archivo .env

DB_USER = os.getenv('DATA_DB_USER')
DB_PASSWORD = os.getenv('DATA_DB_PASSWORD')
DB_HOST = os.getenv('DATA_DB_HOST')  # El nombre del servicio en docker-compose
DB_PORT = os.getenv('DATA_DB_PORT')  # Puerto de la base de datos
DB_NAME = os.getenv('DATA_DB_DATABASE')  # Nombre de la base de datos

SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:3306/{DB_NAME}"
print(f"SQLALCHEMY_DATABASE_URI: {SQLALCHEMY_DATABASE_URI}")
SQLALCHEMY_TRACK_MODIFICATIONS = False