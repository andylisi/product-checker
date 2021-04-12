from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, URL
import re
from productchecker.models import User


password_min = 4
password_max = 50
username_min = 4
username_max = 20
product_url_max = 30

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
                           DataRequired(), Length(min=username_min, max=username_max)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(min=password_min, max=password_max)])
    confirm_password = PasswordField('Confirm Password', validators=[
                                     DataRequired(), Length(min=password_min, max=password_max), EqualTo('password')])
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

class UpdateAccountForm(FlaskForm):
    username = StringField('Username', validators=[
                           DataRequired(), Length(min=username_min, max=username_max)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password')
    confirm_password = PasswordField('Confirm Password', validators=[EqualTo('password')])
    submit = SubmitField('Submit')

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
        if username.data != current_user.username:
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
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email already in use.')

    def validate_password(self, password):
        '''Check to see if password field is populated. If it is,
            then check length requirements.

        Args:
            self: Registration form
            username: user input for email field
        Returns:
            bool: True for email unavailable, email for available
        Raises:
            ValueError: Email not available
        '''
        #if field is populated and not between pw min and max requirements.
        #if it is not populated, a condition in route dictates it will not update
        if password.data != '' and len(password.data) < password_min or len(password.data) > password_max:
            raise ValidationError('Field must be between ' + str(password_min) + ' and ' +
                                    str(password_max) +' characters long')


class ProductForm(FlaskForm):
    alias = StringField('alias', validators=[DataRequired(),Length(max=product_url_max)])
    url = StringField('url', validators=[URL()])
    submit = SubmitField('Submit')

    def validate_url(self, url):
        regex = re.compile('^(https|http):\/\/www\.(bestbuy|amazon)\.com')
        if not regex.match(url.data):
            raise ValidationError('Retailer must be Bestbuy or Amazon')