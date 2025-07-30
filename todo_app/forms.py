from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length

class TaskForm(FlaskForm):
    title = StringField('Название задачи',
                        validators=[
                            DataRequired(message='Нельзя добавить пустую задачу'),
                            Length(max=24, message='Название должно быть не длиннее 100 символов')
                        ])
    submit = SubmitField('Добавить')

class MarkDoneForm(FlaskForm):
    task_id = HiddenField(validators=[DataRequired()])
    submit = SubmitField('Отметить как выполненную')

class DeleteForm(FlaskForm):
    task_id = HiddenField(validators=[DataRequired()])
    submit = SubmitField('Удалить')

class EditForm(FlaskForm):
    task_id = HiddenField(validators=[DataRequired()])
    title = StringField('Название задачи',
        validators=[
            DataRequired(message='Название не может быть пустым'),
            Length(max=24, message='Название должно быть не длиннее 100 символов')
        ])
    done = BooleanField('Выполнена')
    submit = SubmitField('Сохранить')
