"""All forms, fields and submissions that a user will utilize.

Flask Forms use wtforms for all form handling, validation, and
submission. Each form is represented by a class and optional validation 
methods. Expected field types, labels and validators are all
configured here. The Form will be generated in routes, passed to
the html page, and upon submission, passed back to routes for 
downstream operations. 

Wtforms provide many out of the box validators but custom validators
can also be created as class methods.
"""

from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, RadioField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, URL, NumberRange, Optional
import re
from productchecker.models import User


password_min = 4
password_max = 50
username_min = 4
username_max = 20
product_alias_max = 30
product_url_max = 250
freq_min = 10
freq_max = 86400


class RegistrationForm(FlaskForm):
    """Registration form for initial account creation.

    Attributes:
        username: Username field.
        email: User email field.
        password: User password field.
        confirm_password: Confirm user password field.
        submit: Submit button.
    """

    username = StringField('Username', validators=[
                           DataRequired(), Length(min=username_min, max=username_max)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(min=password_min, max=password_max)])
    confirm_password = PasswordField('Confirm Password', validators=[
                                     DataRequired(), Length(min=password_min, max=password_max), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        '''Checks to see if username already exists.

        Args:
            self: Registration form.
            username: User input for username field.
        Raises:
            ValueError: Username not available.
        '''

        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username unavailable.')

    def validate_email(self, email):
        '''Checks to see if email already exists.

        Args:
            self: Registration form.
            username: User input for email field.
        Returns:
            bool: True for email unavailable, email for available.
        Raises:
            ValueError: Email not available.
        '''

        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already in use.')


class LoginForm(FlaskForm):
    """Login form for existing accounts to authenticate.

    Attributes:
        username: Username field.
        password: Password field.
        remember: Remember me checkbox for broswer cookie.
        submit: Submit button.
    """

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class UpdateAccountForm(FlaskForm):
    """Update account form for credentials, preferences, and notifications.

    Attributes:
        username: Username field.
        email: User email field.
        password: User password field.
        confirm_password: Confirm user password field.
        check_freq: Frequency field for Product.check_all().
        discord_webhook: Discord webhook url field for discord notifications.
        discord_active: Radio button for turning on/off discord notifications.
        submit: Submit button.
    """

    username = StringField('Username', validators=[
                           DataRequired(), Length(min=username_min, max=username_max)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password')
    confirm_password = PasswordField('Confirm Password', validators=[EqualTo('password')])
    check_freq = IntegerField('Check Frequency', validators=[
                           DataRequired(), NumberRange(min=freq_min, max=freq_max)])
    discord_webhook = StringField('Webhook URL')
    discord_active = RadioField(coerce=int, choices=[(1,'On'),(0,'Off')])
    submit = SubmitField('Submit Changes')

    def validate_username(self, username):
        '''Checks to see if username already exists.

        Args:
            self: Registration form.
            username: User input for username field.
        Raises:
            ValueError: Username not available.
        '''

        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username unavailable.')

    def validate_email(self, email):
        '''Checks to see if email already exists.

        Args:
            self: Registration form.
            username: User input for email field.
        Raises:
            ValueError: Email not available.
        '''

        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email already in use.')

    def validate_password(self, password):
        '''Checks to see if password field is populated. If it is,
            then check length requirements.

        Args:
            self: Registration form.
            username: User input for email field.
        Raises:
            ValueError: Email not available.
        '''

        #if field is populated and not between pw min and max requirements.
        #if it is not populated, a condition in route dictates it will not update
        if password.data != '' and len(password.data) < password_min or len(password.data) > password_max:
            raise ValidationError('Field must be between ' + str(password_min) + ' and ' +
                                    str(password_max) +' characters long')
    
    def validate_discord_webhook(self, discord_webhook):
        '''Checks to see if URL is valid Discord webhook.

        Args:
            self: Registration form.
            discord_webhook: Discord webhook URL.
        Raises:
            ValueError: Discord webhook URL is not valid.
        '''

        if not discord_webhook.data=='':
            regex = re.compile('^https:\/\/discord\.com\/api\/webhooks\/')
            if not regex.match(discord_webhook.data):
                raise ValidationError('Please ensure Discord Webhook URL is valid')

    def validate_discord_active(self, discord_webhook):
        '''Turns off radiobutton if no data in webhook URL field.

         Args:
            self: Registration form.
            discord_webhook: Discord webhook URL.
        '''

        if self.discord_active.data==1 and self.discord_webhook.data == '':
                self.discord_active.data=0


class ProductForm(FlaskForm):
    """A form for user to add a new product to user's account to start tracking.

    Attributes:
        alias: Product alias. User's choice.
        url: URL where product can be found for purchase.
        submit: Submit button.
    """

    alias = StringField('alias', validators=[DataRequired(),Length(max=product_alias_max)])
    url = StringField('url', validators=[URL(), Length(max=product_url_max)])
    submit = SubmitField('Submit')

    def validate_url(self, url):
        '''Validates url to see if it is supported retailer.

        Args:
            self: Product form.
            url: URL of product.
        Raises:
            ValueError: Retailer not supported.
        '''

        regex = re.compile('^(https|http):\/\/www\.(bestbuy|amazon)\.com')
        if not regex.match(url.data):
            raise ValidationError('Retailer must be Bestbuy or Amazon')


class RequestResetForm(FlaskForm):
    """A form for user to request a password reset in the event they have forgotten theirs.

    Attributes:
        email: User's email address associated with account.
        submit: Submit button.
    """

    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    """A form for user to reset password once they have received password reset email and token.

    Attributes:
        password: User new password field.
        confirm_password: Confirm user new password field.
        submit: Submit button.
    """

    password = PasswordField('Password', validators=[
                             DataRequired(), Length(min=password_min, max=password_max)])
    confirm_password = PasswordField('Confirm Password', validators=[
                                     DataRequired(), Length(min=password_min, max=password_max), EqualTo('password')])
    submit = SubmitField('Reset Password')