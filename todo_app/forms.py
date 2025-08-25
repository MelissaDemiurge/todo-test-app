from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, BooleanField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, Regexp

# 🔷 Общий миксин для поля title
class TitleFormMixin:
    title = StringField(
        'Название задачи',
        validators=[
            DataRequired(message='Название не может быть пустым'),
            Length(max=24, message='Название должно быть не длиннее 24 символов')
        ],
        filters=[lambda s: s.strip() if s else s]
    )

# 🔷 Общий миксин для скрытого поля task_id
class TaskIdFormMixin:
    task_id = HiddenField(validators=[DataRequired()])

# 🟢 Форма добавления новой задачи
class TaskForm(FlaskForm, TitleFormMixin):
    submit = SubmitField('Добавить')

# 🔵 Форма отметки задачи как выполненной
class MarkDoneForm(FlaskForm, TaskIdFormMixin):
    submit = SubmitField('Отметить как выполненную')

# 🔴 Форма удаления задачи
class DeleteForm(FlaskForm, TaskIdFormMixin):
    submit = SubmitField('Удалить')

# 🟡 Форма редактирования задачи
class EditForm(FlaskForm, TitleFormMixin, TaskIdFormMixin):
    done = BooleanField('Выполнена')
    submit = SubmitField('Сохранить')

class BulkDeleteForm(FlaskForm):
    ids = StringField('ids', validators=[DataRequired(message='Не выбрано ни одной задачи')])


class LoginForm(FlaskForm):
    username = StringField('Имя пользователя или email', validators=[DataRequired(), Length(max=254)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=8, max=128)])
    remember = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegisterForm(FlaskForm):
    username = StringField(
        'Имя пользователя',
        validators=[
            DataRequired(),
            Length(min=5, max=24, message='От 5 до 24 символов'),
            Regexp(r'^[a-z][a-z0-9_]*$', flags=0, message='Только латиница, цифры и _, начинаться с буквы')
        ]
    )
    email = StringField('Email', validators=[Optional(), Email(), Length(max=254)])
    password = PasswordField(
        'Пароль',
        validators=[
            DataRequired(),
            Length(min=8, max=128),
            Regexp(r'^[A-Za-z0-9!@#\$%\^&\*\-_=\+\.]{8,128}$', message='Недопустимые символы в пароле')
        ]
    )
    password2 = PasswordField('Повтор пароля', validators=[DataRequired(), EqualTo('password', message='Пароли должны совпадать')])
    submit = SubmitField('Зарегистрироваться')