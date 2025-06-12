def test_register(test_client):
    """Тест регистрации нового пользователя"""
    response = test_client.post('/register', data={
        'username': 'newuser',
        'email': 'new@example.com',
        'password': 'newpass'
    })
    assert response.status_code == 302  # Редирект после успешной регистрации
    assert '/login' in response.location


def test_login(test_client):
    """Тест входа пользователя"""
    # Сначала регистрируем пользователя
    test_client.post('/register', data={
        'username': 'loginuser',
        'email': 'login@example.com',
        'password': 'loginpass'
    })

    # Пытаемся войти
    response = test_client.post('/login', data={
        'username': 'loginuser',
        'password': 'loginpass'
    })
    assert response.status_code == 302
    assert '/videos' in response.location


def test_protected_route(test_client, auth_tokens):
    """Тест доступа к защищенному маршруту"""
    response = test_client.get('/videos', headers={
        'Cookie': auth_tokens['session']
    })
    assert response.status_code == 200