import peewee as pw
from playhouse.fields import PasswordField
import datetime

db = pw.SqliteDatabase('database.db')


def initialize_database():
    User.create_table(fail_silently=True)
    Task.create_table(fail_silently=True)
    try:
        user = User.create(
            username='root',
            password='123'
        )

        Task.create(
            user=user,
            text="Example"
        )
    except pw.IntegrityError:
        pass


class BaseModel(pw.Model):
    class Meta:
        database = db


class User(BaseModel):
    username = pw.CharField(max_length=70, unique=True)
    password = PasswordField()
    state = pw.BooleanField(default=True)

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.state

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return '<User %r>' % self.username


class Task(BaseModel):
    user = pw.ForeignKeyField(User, related_name='tasks')
    text = pw.TextField()
    deadline_date = pw.DateField(default=datetime.date.today())
