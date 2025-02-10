from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect  # Добавляем CSRF-защиту
from dotenv import load_dotenv  #Для секретного ключа
import os


load_dotenv()  # Загрузка переменных окружения из .env (если есть)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_super_secret_key')  # Лучше хранить в .env
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/schweppes.db'  # Путь к базе данных
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #Отключает предупреждение
app.config['UPLOAD_FOLDER'] = 'app/static/img'  # Папка для загрузки изображений


db = SQLAlchemy(app)
csrf = CSRFProtect(app) #Защита от межсайтовой подделки запросов

# Импортируем routes и models *после* создания app, чтобы избежать циклических зависимостей
from app import routes, models