from flask import Flask, render_template, request, session, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

class TaskForm(FlaskForm):
    title = StringField('Название задачи', validators=[DataRequired()])
    submit = SubmitField('Добавить')

@app.route('/', methods=['GET', 'POST'])
def index():
    form = TaskForm()

    if 'tasks' not in session:
        session['tasks'] = []
    
    if form.validate_on_submit():
        new_task = {'title': form.title.data, 'done': False}
        session['tasks'].append(new_task)
        session.modified = True
        return redirect(url_for('index'))
    return render_template('index.html', tasks=session.get('tasks', []), form=form)

if __name__ == '__main__':
    app.run(debug=True)