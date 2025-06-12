import pytest
import os

if __name__ == '__main__':
    # Запуск тестов с покрытием
    pytest.main([
        '-v',
        '--cov=app',
        '--cov-report=term-missing',
        'tests/'
    ])