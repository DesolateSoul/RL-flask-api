import paths
import pytest
from app import app
from database import init_db
import os


@pytest.fixture(scope='module')
def test_client():
    # Используем временную базу данных для тестов
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'

    with app.test_client() as testing_client:
        with app.app_context():
            init_db("sqlite:///test.db")
        yield testing_client

    # Удаляем тестовую базу после завершения
    if os.path.exists('test.db'):
        os.remove('test.db')


@pytest.fixture(scope='function')
def auth_tokens(test_client):
    # Регистрируем тестового пользователя
    test_client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass'
    })

    # Логинимся и получаем токен (если используете JWT)
    login_response = test_client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass'
    })

    # Возвращаем данные для аутентификации
    return {
        'session': login_response.headers.get('Set-Cookie'),
        'user_id': 1  # Первый пользователь
    }