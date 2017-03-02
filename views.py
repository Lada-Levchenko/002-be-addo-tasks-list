from flask import Flask
from flask import g, request, redirect, url_for, render_template

from flask_login import LoginManager, current_user, login_user, logout_user
from models import User, Task, initialize_database

from forms import RegistrationForm

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
        tasks = Task.select(Task, User).join(User).where(User.id == g.user.get_id()).order_by(Task.deadline_date.desc())
        return render_template('index.html', tasks=tasks)
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form['username']
    password = request.form['password']

    registered_user = User.filter(User.username == username).first()

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
        registered_user = User.filter(User.username == form.username.data).first()
        if registered_user is None:
            registered_user = User.create(username=form.username.data, password=form.password.data)
            login_user(registered_user)
            return redirect(url_for('index'))
        return redirect(url_for('login'))
    return render_template('registration.html', form=form)


if __name__ == "__main__":
    initialize_database()
    app.run()
