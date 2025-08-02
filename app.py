

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.base import MenuLink
from flask_admin.menu import MenuView
from flask_admin.contrib.sqla import ModelView
from models import db, User, PortfolioItem, Review, Like, Comment
from datetime import datetime
import os
import threading
import requests
from flask import jsonify

app = Flask(__name__)
app.config['SECRET_KEY'] = 'BGWa4bZNOriWsw7WejMomQXzj-9ICH3dQz6Tkw9GYakDYLDQPB8AVxU-8jwdXtpWLjohP2Zvnuuc2zhdXtEBhME'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'} # Add this line
app.config['FLASK_ADMIN_SWATCH'] = 'slate'  # Темная тема для админки

# Конфигурация Telegram бота
TELEGRAM_BOT_TOKEN = "7711849755:AAHvzB4Y0j80mBoy-r7yhEvnPwu_l_BR5PY"
TELEGRAM_ADMIN_CHAT_ID = "ВАШ_CHAT_ID"  # Замените на реальный chat_id

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Кастомные ModelView для админки
class BaseModelView(ModelView):
    def __init__(self, model, session, name=None, category=None, endpoint=None, url=None, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        
        super(BaseModelView, self).__init__(model, session, name=name, category=category, endpoint=endpoint, url=url)
def send_telegram_notification(message):
    """Отправка уведомления в Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_ADMIN_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        app.logger.error(f"Ошибка отправки в Telegram: {e}")

def async_send_telegram(message):
    """Асинхронная отправка уведомления"""
    thread = threading.Thread(target=send_telegram_notification, args=(message,))
    thread.start()

# Кастомный AdminIndexView для проверки прав доступа
class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'admin'
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))
    
# Кастомные ModelView для админки с проверкой доступа
class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'admin'
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

# Обновляем все ModelView, чтобы они наследовались от SecureModelView
class UserModelView(SecureModelView):
    column_list = ('id', 'username', 'email', 'role', 'species', 'is_approved', 'rating')
    column_searchable_list = ('username', 'email')
    column_filters = ('role', 'is_approved')
    form_columns = ('username', 'email', 'role', 'species', 'is_approved', 'style', 'rating')
    column_editable_list = ('is_approved',)
    
    # Добавляем галочку верификации в список пользователей
    def _is_approved_formatter(view, context, model, name):
        if model.is_approved:
            return '<span class="fa fa-check-circle" style="color: green;"></span>'
        return ''
    
    column_formatters = {
        'is_approved': _is_approved_formatter
    }

class PortfolioModelView(SecureModelView):
    column_list = ('id', 'title', 'artist', 'created_at')
    column_searchable_list = ('title',)
    form_columns = ('title', 'description', 'image_url', 'artist')

class ReviewModelView(SecureModelView):
    column_list = ('id', 'artist', 'client', 'rating', 'created_at')
    form_columns = ('content', 'rating', 'artist', 'client')

class LikeModelView(SecureModelView):
    column_list = ('id', 'user', 'artist', 'created_at')
    form_columns = ('user', 'artist')

class CommentModelView(SecureModelView):
    column_list = ('id', 'content', 'user', 'portfolio_item', 'created_at')
    form_columns = ('content', 'user', 'portfolio_item')


# Инициализация админ-панели с кастомным индексным представлением
admin = Admin(app, name='FurryArt Admin', template_mode='bootstrap3', index_view=MyAdminIndexView())

# Регистрация моделей в админке
admin.add_view(UserModelView(User, db.session, name='Пользователи'))
admin.add_view(PortfolioModelView(PortfolioItem, db.session, name='Портфолио'))
admin.add_view(ReviewModelView(Review, db.session, name='Отзывы'))
admin.add_view(LikeModelView(Like, db.session, name='Лайки'))
admin.add_view(CommentModelView(Comment, db.session, name='Комментарии'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    artists = User.query.filter_by(role='artist', is_approved=True).order_by(User.rating.desc()).limit(12).all()
    return render_template('index.html', artists=artists)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        species = request.form.get('species')
        
        if not all([username, email, password, role, species]):
            flash('Пожалуйста, заполните все обязательные поля', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Это имя пользователя уже занято', 'danger')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('Этот email уже зарегистрирован', 'danger')
            return redirect(url_for('register'))

        user = User(
            username=username,
            email=email,
            role=role,
            species=species
        )
        user.password = password  # Используем setter для установки пароля
        
        if role == 'artist':
            user.style = request.form.get('style', '')
            user.experience = int(request.form.get('experience', 0))
            user.price_per_hour = float(request.form.get('price_per_hour', 0))
        
        db.session.add(user)
        db.session.commit()
        
        # Отправка уведомления админам
        if user.role == 'artist':
            message = f"🎨 Новый художник зарегистрировался!\n\nИмя: {user.username}\nСпециализация: {user.species}\nСтиль: {user.style}"
            async_send_telegram(message)

        login_user(user)
        flash('Регистрация прошла успешно!', 'success')
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.verify_password(password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Неверный email или пароль', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Добавление комментария
@app.route('/portfolio/<int:item_id>/comment', methods=['POST'])
@login_required
def add_comment(item_id):
    item = PortfolioItem.query.get_or_404(item_id)
    content = request.form.get('content')
    
    if not content:
        flash('Комментарий не может быть пустым', 'danger')
        return redirect(url_for('artist_profile', artist_id=item.artist_id))
    
    comment = Comment(
        content=content,
        user_id=current_user.id,
        portfolio_item_id=item.id
    )
    db.session.add(comment)
    db.session.commit()
    
    flash('Комментарий добавлен', 'success')
    return redirect(url_for('artist_profile', artist_id=item.artist_id))

# Удаление комментария
@app.route('/comment/delete/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    artist_id = comment.portfolio_item.artist_id
    
    if comment.user_id != current_user.id and current_user.role != 'admin':
        flash('Вы не можете удалить этот комментарий', 'danger')
        return redirect(url_for('artist_profile', artist_id=artist_id))
    
    db.session.delete(comment)
    db.session.commit()
    flash('Комментарий удален', 'success')
    return redirect(url_for('artist_profile', artist_id=artist_id))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user, artist=current_user)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        # Используем get() вместо прямого доступа, чтобы избежать ошибок
        current_user.bio = request.form.get('bio', '')
        current_user.telegram = request.form.get('telegram', '')
        current_user.species = request.form.get('species', current_user.species)
        
        # Обработка загрузки аватара
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                current_user.avatar = filename
        
        # Обновление данных для художников
        if current_user.role == 'artist':
            current_user.style = request.form.get('style', current_user.style)
            current_user.experience = int(request.form.get('experience', 0))
            current_user.price_per_hour = float(request.form.get('price_per_hour', 0))
        
        db.session.commit()
        flash('Профиль успешно обновлен', 'success')
        return redirect(url_for('profile'))
    
    return render_template('edit_profile.html', user=current_user)

@app.route('/artist/<int:artist_id>')
def artist_profile(artist_id):
    artist = User.query.get_or_404(artist_id)
    
    # Проверяем, авторизован ли пользователь, прежде чем проверять лайки
    is_liked = False
    if current_user.is_authenticated:
        is_liked = Like.query.filter_by(user_id=current_user.id, artist_id=artist_id).first() is not None
    
    return render_template('artist_profile.html',
                         artist=artist,
                         is_liked=is_liked,
                         current_user=current_user)

@app.route('/artist/<int:artist_id>/like', methods=['POST'])
@login_required
def toggle_like(artist_id):
    like = Like.query.filter_by(user_id=current_user.id, artist_id=artist_id).first()
    if like:
        db.session.delete(like)
    else:
        like = Like(user_id=current_user.id, artist_id=artist_id)
        db.session.add(like)
    db.session.commit()
    return redirect(url_for('artist_profile', artist_id=artist_id))

@app.route('/portfolio/add', methods=['GET', 'POST'])
@login_required
def add_portfolio_item():
    if current_user.role != 'artist':
        flash('Только художники могут добавлять работы в портфолио', 'warning')
        return redirect(url_for('profile'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        image_url = request.form.get('image_url')  # В реальном проекте используйте загрузку файлов

        if not title or not image_url:
            flash('Заполните все обязательные поля', 'danger')
            return redirect(url_for('add_portfolio_item'))

        new_item = PortfolioItem(
            title=title,
            description=description,
            image_url=image_url,
            artist_id=current_user.id
        )
        
        db.session.add(new_item)
        db.session.commit()
        flash('Работа добавлена в портфолио', 'success')
        return redirect(url_for('profile'))

    return render_template('add_portfolio_item.html')

@app.route('/portfolio/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_portfolio_item(item_id):
    item = PortfolioItem.query.get_or_404(item_id)
    if item.artist_id != current_user.id:
        flash('Вы не можете удалить эту работу', 'danger')
        return redirect(url_for('profile'))
    
    db.session.delete(item)
    db.session.commit()
    flash('Работа удалена из портфолио', 'success')
    return redirect(url_for('profile'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)


    #TODO: Придумать чтонибудь еще.