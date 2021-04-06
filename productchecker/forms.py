from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from productchecker.models import User


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
                           DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(min=2, max=50)])
    confirm_password = PasswordField('Confirm Password', validators=[
                                     DataRequired(), Length(min=2, max=50), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        '''Check to see if username already exists

        Args:
            self: Registration form
            username: user input for username field
        Returns:
            bool: True for username unavailable, False for available
        Raises:
            ValueError: Username not available
        '''
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username unavailable.')

    def validate_email(self, email):
        '''Check to see if email already exists

        Args:
            self: Registration form
            username: user input for email field
        Returns:
            bool: True for email unavailable, email for available
        Raises:
            ValueError: Email not available
        '''
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already in use.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')
