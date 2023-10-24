from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import StringField, FloatField, FileField, SubmitField, validators



class LoginForm(FlaskForm):
    username = StringField('Username', validators=[
        validators.InputRequired(),
        validators.Length(min=2, max=20),
        validators.Regexp('^[a-zA-Z]+$', message='Username must contain only letters')
    ])
    password = StringField('Password', validators=[
        validators.InputRequired(),
        validators.Length(min=8, message='Password must be at least 8 characters long'),
        validators.Regexp('^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*()-_=+\\|[\]{};:\'",<.>/?])', 
            message='Password must contain at least one digit, one lowercase letter, one uppercase letter, and one special character'),
        validators.EqualTo('confirm_password', message='Passwords must match')
    ])
    confirm_password = StringField('Confirm Password', validators=[
        validators.InputRequired(),
    ])
    submit = SubmitField('Submit')
