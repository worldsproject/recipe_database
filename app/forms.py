from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, PasswordField, SelectField
from wtforms.validators import DataRequired, EqualTo

class LoginForm(Form):
    email = TextField('Email', validators = [DataRequired()])
    password = TextField('Password', validators = [DataRequired()])
    remember_me = BooleanField('remember_me', default = False)

class RegisterForm(Form):
	email = TextField('Email', validators = [DataRequired()])
	password = PasswordField('password', validators = [DataRequired(), EqualTo('confirm_password', message='Passwords do not Match.')])
	confirm_password = PasswordField('Confirm Password')
