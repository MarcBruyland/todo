from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, PasswordField, DateField
from wtforms.validators import DataRequired, Email


class LoginForm(FlaskForm):
    email = StringField("User name", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField('Submit')


class TodoForm(FlaskForm):
    id = IntegerField('Todo id')
    todo = StringField("Todo", validators=[DataRequired()])
    due = DateField('Due Date', format='%Y-%m-%d')
    user_id = IntegerField('User id')
    email = StringField('User')
    submit = SubmitField('Submit')


