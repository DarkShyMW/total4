from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)  # Переименовали поле
    avatar = db.Column(db.String(200), default='default_avatar.png')
    role = db.Column(db.String(20), nullable=False, default='client')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    telegram = db.Column(db.String(100))
    bio = db.Column(db.Text)
    species = db.Column(db.String(50))
    is_approved = db.Column(db.Boolean, default=False)
    def is_verified(self):
        return self.is_approved
    
    # Для художников
    style = db.Column(db.String(100))
    rating = db.Column(db.Float, default=0.0)
    experience = db.Column(db.Integer)
    price_per_hour = db.Column(db.Float)
    
    # Отношения
    portfolio_items = db.relationship('PortfolioItem', back_populates='artist')
    reviews_received = db.relationship('Review', back_populates='artist', foreign_keys='Review.artist_id')
    reviews_given = db.relationship('Review', back_populates='client', foreign_keys='Review.client_id')
    likes_received = db.relationship('Like', back_populates='artist', foreign_keys='Like.artist_id')
    likes_given = db.relationship('Like', back_populates='user', foreign_keys='Like.user_id')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class PortfolioItem(db.Model):
    __tablename__ = 'portfolio_items'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    artist_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    artist = db.relationship('User', back_populates='portfolio_items')

    def __repr__(self):
        return f'<PortfolioItem {self.title}>'

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    artist_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    artist = db.relationship('User', foreign_keys=[artist_id], back_populates='reviews_received')
    client = db.relationship('User', foreign_keys=[client_id], back_populates='reviews_given')

    def __repr__(self):
        return f'<Review {self.id}>'

class Like(db.Model):
    __tablename__ = 'likes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', foreign_keys=[user_id], back_populates='likes_given')
    artist = db.relationship('User', foreign_keys=[artist_id], back_populates='likes_received')

    def __repr__(self):
        return f'<Like {self.id}>'