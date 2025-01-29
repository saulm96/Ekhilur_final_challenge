import os

DB_USER = "root"
DB_PASSWORD = "123456789"
DB_HOST = "data_ekhilur_final_challenge_db"  # El nombre del servicio en docker-compose
DB_NAME = "ekhilur"

SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
SQLALCHEMY_TRACK_MODIFICATIONS = False
