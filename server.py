from flask import Flask, jsonify, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from forms import LoginForm, TodoForm
from flask_bootstrap import Bootstrap
import datetime
import bcrypt       # hash password
import os           # generate token
import binascii     # generate token
from datetime import datetime

app = Flask(__name__)
bootstrap = Bootstrap(app)

# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.secret_key = "SECRET_KEY"


# Todo TABLE Configuration
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    todo = db.Column(db.String(50), nullable=False)
    due = db.Column(db.String(10), nullable=True)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


# User TABLE Configuration
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    token = db.Column(db.String(50), nullable=True)
    token_expiration_date = db.Column(db.String(10), nullable=True)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


def date_today():
    return datetime.today().strftime('%Y-%m-%d')


def authorization_ok(id, token):
    user = db.session.query(User).filter_by(id=id).first()
    if not user:
        return False
    if user.token != token:
        return False
    if user.token_expiration_date < date_today():
        return False
    return True


@app.route("/")
def home():
    return redirect("/login")


@app.route("/login", methods=["POST", "GET"])
def login():
    error_msg = ""
    form = LoginForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            password=form.password.data
        )
        user_from_db = db.session.query(User).filter_by(email=form.email.data).first()
        if not user_from_db:
            error_msg = "invalid user"
        elif not bcrypt.checkpw(form.password.data.encode('utf8'), user_from_db.password):
            error_msg = "invalid password"
        else:
            user_from_db.token = binascii.hexlify(os.urandom(20)).decode()
            user_from_db.token_expiration_date = date_today()
            db.session.commit()
            return redirect(url_for('get_todos', user_id=user_from_db.id, token=user_from_db.token))
    return render_template("login.html", form=form, msg=error_msg)


@app.route("/signup", methods=["POST", "GET"])
def signup():
    error_msg = ""
    form = LoginForm()
    if form.validate_on_submit():
        new_user = User(
            email=form.email.data,
            password=bcrypt.hashpw(form.password.data.encode('utf8'), bcrypt.gensalt()),
            token="",
            token_expiration_date=""
        )
        if db.session.query(User.id).filter_by(email=form.email.data).first() is None:
            new_user.token = binascii.hexlify(os.urandom(20)).decode()
            new_user.token_expiration_date = date_today()
            db.session.add(new_user)
            db.session.commit()
            db.session.refresh(new_user)  # to get the auto-generated id from the db into our new_user object
            return redirect(url_for('get_todos', user_id=new_user.id, token=new_user.token))
        else:
            error_msg = "User already exists"
    return render_template("signup.html", form=form, msg=error_msg)


@app.route("/todos", methods=["GET"])
def get_todos():
    user_id = request.args.get('user_id')
    token = request.args.get('token')
    user = db.session.query(User).filter_by(id=user_id).first()
    print(user)
    print(authorization_ok(user_id, token))
    if user and authorization_ok(user_id, token):
        form = TodoForm()
        todos = db.session.query(Todo).filter_by(user_id=user_id).order_by(Todo.due.asc())
        return render_template("index.html", form=form, todos=todos, user=user)
    else:
        form = LoginForm()
        error_msg = "Authorization problem"
        return render_template("login.html", form=form, msg=error_msg)


# Create Todo
@app.route("/create", methods=["POST"])
def create_todo():
    user_id = request.args.get('user_id')
    token = request.args.get('token')

    if authorization_ok(user_id, token):
        data = request.form
        new_todo = Todo(
            todo=data["todo"],
            due=data["due"],
            user_id=user_id,
        )
        db.session.add(new_todo)
        db.session.commit()
        return redirect(url_for('get_todos', user_id=user_id, token=token))
    else:
        form = LoginForm()
        error_msg = "Authorization problem"
        render_template("login.html", form=form, msg=error_msg)


# Update Todo
@app.route("/update", methods=["GET", "POST"])
def update_todo():
    user_id = request.args.get('user_id')
    token = request.args.get('token')
    if authorization_ok(user_id, token):
        user = db.session.query(User).filter_by(id=user_id).first()
        form = TodoForm()
        if form.validate_on_submit():
            data = request.form
            todo_id = data["id"]
            todo = db.session.query(Todo).filter_by(id=todo_id).first()
            todo.todo = data["todo"]
            todo.due = data["due"]
            todo.user_id = user_id
            db.session.commit()
            return redirect(url_for('get_todos', user_id=user_id, token=token))
        todo_id = request.args.get('todo_id')
        todo = db.session.query(Todo).filter_by(id=todo_id).first()
        if todo.due:
            form = TodoForm(
                id=todo.id,
                todo=todo.todo,
                due=datetime.strptime(todo.due, '%Y-%m-%d').date()
            )
        else:
            form = TodoForm(
                id=todo.id,
                todo=todo.todo,
                due=None
            )
        return render_template("update.html", form=form, user=user, todo=todo)
    else:
        form = LoginForm()
        error_msg = "Authorization problem"
        render_template("login.html", form=form, msg=error_msg)


# Delete Todo
@app.route("/delete", methods=["GET"])
def delete_todo():
    user_id = request.args.get('user_id')
    token = request.args.get('token')
    if authorization_ok(user_id, token):
        todo_id = request.args.get('todo_id')
        todo = Todo.query.get(todo_id)
        if todo:
            db.session.delete(todo)
            db.session.commit()
            return redirect(url_for('get_todos', user_id=user_id, token=token))
        else:
            return jsonify(error={"Not Found": "Sorry, we don't have a todo with that id."}), 404
    else:
        form = LoginForm()
        error_msg = "Authorization problem"
        render_template("login.html", form=form, msg=error_msg)


if __name__ == "__main__":
    app.run(debug=True)
