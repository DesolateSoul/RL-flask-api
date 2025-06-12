import paths
from flask import Flask, render_template, redirect, url_for, request, flash, session, abort
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from database import init_db, User, Video, Base
from base64 import b64encode
import requests
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Инициализация базы данных
Session = init_db("sqlite:///../RL_Restful_API/app.db")

migrate = Migrate(app, Base)


@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('videos'))


@app.route('/logout')
def logout():
    session.clear()
    flash('Вы успешно вышли из системы.', 'success')
    return redirect(url_for('login'))


@app.route('/videos')
def videos():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db_session = Session()
    try:
        all_videos = db_session.query(Video).all()

        # Подготовка данных для миниатюр
        videos_data = []
        for video in all_videos:
            if video.thumbnail_data:
                thumbnail = b64encode(video.thumbnail_data).decode('utf-8')
            else:
                thumbnail = None
            videos_data.append({
                'id': video.id,
                'title': video.title,
                'thumbnail': thumbnail,
                'user': video.user.username if video.user else 'Unknown'
            })

        return render_template('videos.html', videos=videos_data)
    finally:
        db_session.close()


@app.route('/video/<int:video_id>')
def view_video(video_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db_session = Session()
    try:
        video = db_session.query(Video).filter_by(id=video_id).first()
        if not video:
            abort(404)

        # Преобразуем бинарные данные видео в base64
        video_data = b64encode(video.video_data).decode('utf-8') if video.video_data else None

        return render_template('video_view.html',
                               video=video,
                               video_data=video_data,
                               username=session.get('username'))
    finally:
        db_session.close()


@app.route('/create_video', methods=['GET', 'POST'])
def create_video():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Получаем параметры из формы
        title = request.form['title']
        description = request.form['description']
        gravity = request.form['gravity']
        enable_wind = request.form['enable_wind']
        wind_power = request.form['wind_power']
        turbulence_power = request.form['turbulence_power']

        # Формируем URL для API
        api_url = f"http://127.0.0.1:5001/lunar_lander/api/v1.0/getvideo?gravity={gravity}&enable_wind={enable_wind}&wind_power={wind_power}&turbulence_power={turbulence_power}"

        # Инициализируем db_session до try блока
        db_session = None
        try:
            # Отправляем GET-запрос к API
            response = requests.get(api_url)
            response.raise_for_status()

            # Парсим JSON ответ
            data = response.json()
            video_id = data['ID']

            # Обновляем запись о видео в БД с названием и описанием
            db_session = Session()
            video = db_session.query(Video).filter_by(id=video_id).first()
            if video:
                video.title = title
                video.description = description
                video.user_id = session['user_id']
                db_session.commit()

            flash('Видео успешно создано!', 'success')
            return redirect(url_for('view_video', video_id=video_id))

        except requests.exceptions.RequestException as e:
            flash(f'Ошибка при создании видео: {str(e)}', 'danger')
            return redirect(url_for('create_video'))
        except Exception as e:
            if db_session:  # Проверяем, была ли сессия создана
                db_session.rollback()
            flash(f'Ошибка при сохранении данных: {str(e)}', 'danger')
            return redirect(url_for('create_video'))
        finally:
            if db_session:  # Проверяем, была ли сессия создана
                db_session.close()

    return render_template('create_video.html')


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


@app.route('/video/delete/<int:video_id>', methods=['POST'])
def delete_video(video_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db_session = Session()
    try:
        video = db_session.query(Video).filter_by(id=video_id).first()
        if not video:
            flash('Видео не найдено!', 'danger')
            return redirect(url_for('videos'))

        # Проверяем права: админ или владелец видео
        if session.get('role') != 'admin' and video.user_id != session['user_id']:
            abort(403)

        db_session.delete(video)
        db_session.commit()
        flash('Видео успешно удалено!', 'success')
    except Exception as e:
        db_session.rollback()
        flash(f'Ошибка при удалении видео: {str(e)}', 'danger')
    finally:
        db_session.close()

    return redirect(url_for('videos'))


# Регистрация с установкой роли
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password_hash = generate_password_hash(password)

        db_session = Session()
        try:
            new_user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                role='user',  # По умолчанию обычный пользователь
                created_at=datetime.utcnow()
            )
            db_session.add(new_user)
            db_session.commit()
            flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db_session.rollback()
            flash('Пользователь с таким именем или email уже существует!', 'danger')
        finally:
            db_session.close()

    return render_template('register.html')


# Обновляем вход для сохранения роли в сессии
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db_session = Session()
        user = db_session.query(User).filter_by(username=username).first()
        db_session.close()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role  # Сохраняем роль в сессии
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(url_for('videos'))
        else:
            flash('Неверное имя пользователя или пароль!', 'danger')

    return render_template('login.html')


if __name__ == '__main__':
    app.run(host="192.168.1.73", port=8080, debug=True)
