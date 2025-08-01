from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length

# 🔷 Общий миксин для поля title
class TitleFormMixin:
    title = StringField(
        'Название задачи',
        validators=[
            DataRequired(message='Название не может быть пустым'),
            Length(max=24, message='Название должно быть не длиннее 24 символов')
        ]
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