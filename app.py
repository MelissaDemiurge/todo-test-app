import os

from flask import Flask
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

from routes import tasks_bp

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')

# Инициализация защиты CSRF
csrf = CSRFProtect(app)

# Регистрируем Blueprint с маршрутами задач
app.register_blueprint(tasks_bp)

if __name__ == '__main__':
    app.run(debug=True)
