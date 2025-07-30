from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, BooleanField, SubmitField
from wtforms.validators import DataRequired

class TaskForm(FlaskForm):
    title = StringField('Название задачи',
                        validators=[DataRequired(message='Нельзя добавить пустую задачу')])
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
                        validators=[DataRequired(message='Название не может быть пустым')])
    done = BooleanField('Выполнена')
    submit = SubmitField('Сохранить')
