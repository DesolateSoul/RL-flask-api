def test_create_video(test_client, auth_tokens):
    """Тест создания видео через API"""
    response = test_client.post('/create_video', data={
        'title': 'Test Video',
        'description': 'Test Description',
        'gravity': '-10',
        'enable_wind': 'False',
        'wind_power': '15.0',
        'turbulence_power': '1.5'
    }, headers={
        'Cookie': auth_tokens['session']
    })

    assert response.status_code == 302  # Редирект после создания
    assert '/video/' in response.location


def test_get_video(test_client, auth_tokens):
    """Тест получения информации о видео"""
    # Сначала создаем видео
    test_client.post('/create_video', data={
        'title': 'Test Video',
        'description': 'Test Description',
        'gravity': '-10',
        'enable_wind': 'False',
        'wind_power': '15.0',
        'turbulence_power': '1.5'
    }, headers={
        'Cookie': auth_tokens['session']
    })

    # Получаем информацию о видео
    response = test_client.get('/video/1', headers={
        'Cookie': auth_tokens['session']
    })
    assert response.status_code == 200
    assert b'Test Video' in response.data


def test_delete_video(test_client, auth_tokens):
    """Тест удаления видео"""
    # Создаем видео
    test_client.post('/create_video', data={
        'title': 'To Delete',
        'description': 'Will be deleted',
        'gravity': '-10',
        'enable_wind': 'False',
        'wind_power': '15.0',
        'turbulence_power': '1.5'
    }, headers={
        'Cookie': auth_tokens['session']
    })

    # Удаляем видео
    response = test_client.post('/video/delete/1', headers={
        'Cookie': auth_tokens['session']
    })
    assert response.status_code == 302
    assert '/videos' in response.location


def test_api_create_video(test_client):
    """Тест API создания видео"""
    response = test_client.get(
        '/lunar_lander/api/v1.0/getvideo?gravity=-10&enable_wind=False&wind_power=15.0&turbulence_power=1.5'
    )
    assert response.status_code == 200
    data = response.get_json()
    assert 'ID' in data
    assert 'Status' in data