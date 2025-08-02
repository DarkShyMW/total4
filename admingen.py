from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    admin = User(
        username='darkshy',
        email='1@1.ru',
        password=generate_password_hash('123'),
        role='admin',
        species='admin',
        is_approved=True
    )
    db.session.add(admin)
    db.session.commit()