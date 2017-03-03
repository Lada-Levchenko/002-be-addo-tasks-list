from flask import Flask
from flask import g, request, redirect, url_for, render_template

from flask_login import LoginManager, current_user, login_user, logout_user
from models import User, Task, initialize_database

from forms import RegistrationForm, TaskForm, TaskEditForm
import datetime


app = Flask("TaskList")
app.secret_key = 'super secret key'

login_manager = LoginManager(app)
login_manager.login_view = 'login'


@app.before_request
def before_request():
    g.user = current_user


@login_manager.user_loader
def load_user(id):
    return User.get(id=int(id))


@app.route('/', methods=['GET'])
def index():
    if g.user.is_authenticated:
        today = datetime.date.today()
        tasks = Task.select(Task, User).join(User).where(User.id == g.user.get_id()).order_by(Task.deadline_date.asc())
        unfinished_tasks = [task for task in tasks if task.deadline_date < today]
        current_tasks = [task for task in tasks if task.deadline_date == today]
        future_tasks = [task for task in tasks if task.deadline_date > today]
        data = {'unfinished_tasks': unfinished_tasks, 'current_tasks': current_tasks, 'future_tasks': future_tasks}
        return render_template('index.html', **data)
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form['username']
    password = request.form['password']

    registered_user = User.get(User.username == username)

    if registered_user is None:
        return redirect(url_for('login'))  # redirect back to login page if user wasn't found

    if not registered_user.password.check_password(password):
        return redirect(url_for('login'))  # redirect back to login page if incorrect password

    login_user(registered_user)
    return redirect(request.args.get('next') or url_for('index'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    form = RegistrationForm(request.form)
    if request.method == 'GET':
        return render_template('registration.html', form=form)

    if form.validate_on_submit():
        registered_user = User.get(User.username == form.username.data)
        if registered_user is None:
            registered_user = User.create(username=form.username.data, password=form.password.data)
            login_user(registered_user)
            return redirect(url_for('index'))
        return redirect(url_for('login'))
    return render_template('registration.html', form=form)


@app.route('/task', methods=['GET', 'POST'])
def task_create():
    if not g.user.is_authenticated:
        return redirect(url_for('index'))

    form = TaskForm(request.form)
    if request.method == 'GET':
        return render_template('task.html', form=form, form_action="/task")

    if form.validate_on_submit():
        Task.create(user=g.user.get_id(), text=form.text.data, deadline_date=form.date.data)
        return redirect(url_for('index'))
    return render_template('task.html', form=form, form_action="/task")


@app.route('/edit/task/<int:task_id>', methods=['GET', 'POST'])
def task_edit(task_id):
    if not g.user.is_authenticated:
        return redirect(url_for('index'))

    try:
        task = Task.get(Task.id == task_id, Task.user == g.user.get_id())
    except Task.DoesNotExist:
        return redirect(url_for('index'))

    form = TaskEditForm(request.form)
    if request.method == 'GET':
        form.text.data = task.text
        form.date.data = task.deadline_date
        form.complete.data = task.complete
        return render_template('task.html', form=form, form_action="/edit/task/" + str(task_id))

    if form.validate_on_submit():
        task_update = Task.update(text=form.text.data, deadline_date=form.date.data, complete=form.complete.data).where(Task.id == task_id)
        task_update.execute()
        return redirect(url_for('index'))
    return render_template('task.html', form=form, form_action="/edit/task/" + task_id)


@app.route('/delete/task/<int:task_id>', methods=['GET'])
def task_delete(task_id):
    if not g.user.is_authenticated:
        return redirect(url_for('index'))

    try:
        task = Task.get(Task.id == task_id, Task.user == g.user.get_id())
    except Task.DoesNotExist:
        return redirect(url_for('index'))

    task_delete = Task.delete().where(Task.id == task_id)
    task_delete.execute()
    return redirect(url_for('index'))

if __name__ == "__main__":
    initialize_database()
    app.run()
