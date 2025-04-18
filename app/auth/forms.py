from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
from flask_babel import lazy_gettext as _l
from app.models import User
import sqlalchemy as sa
from app import db

class Login(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember me'))
    submit = SubmitField(_l('Login'))

class RegistrationForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    email = EmailField(_l('Enail'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    repeat_password = PasswordField(_l('Repear password'), validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Reguester'))

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(User.username == username.data))
        if user is not None:
            raise ValidationError("Please use a different username.")
    
    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(User.email == email.data))
        if user is not None:
            raise ValidationError("Please use a different email address.")
        
class RessetPassworRequestForm(FlaskForm):
    email = EmailField(_l('Your email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('submit'))
    
class ResetPassword(FlaskForm):
    password=PasswordField(_l('Password'), validators=[DataRequired()])
    repeat_password = PasswordField(_l('Repeat password'), validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Reset password'))