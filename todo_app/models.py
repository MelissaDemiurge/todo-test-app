from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint

db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(24), unique=True, nullable=False, index=True)
    email = db.Column(db.String(254), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(16), nullable=False, default='user', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    # Токен активной сессии: гарантирует только одну активную сессию на пользователя
    active_session_token = db.Column(db.String(128), nullable=True, index=True)

    # Связь с задачами
    tasks = db.relationship('Task', back_populates='user', cascade='all, delete-orphan')

    @property
    def is_admin(self) -> bool:
        return (self.role or 'user') == 'admin'

    def __repr__(self):
        return f'<User id={self.id} username="{self.username}" role={self.role}>'

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    # Заголовок уникален в рамках пользователя
    title = db.Column(db.String(24), nullable=False)
    done = db.Column(db.Boolean, default=False, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Владелец задачи
    user = db.relationship('User', back_populates='tasks')

    # Композитное уникальное ограничение (user_id, title)
    __table_args__ = (
        UniqueConstraint('user_id', 'title', name='uq_tasks_user_title'),
    )

    def __repr__(self):
        return f'<Task id={self.id} title="{self.title}" done={self.done} user_id={self.user_id}>'