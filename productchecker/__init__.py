from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

USE_MYSQL = False 

app = Flask(__name__)
app.config['SECRET_KEY'] = '2rQ5uFcZHFB5iEvw4ZVYgSFYgozDUjA9'
if USE_MYSQL:                                                                                                                                                                  
     app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://USERNAME:PASSWORD@localhost/DATABASENAME'                                                                                
else:                                                                                                                                                                          
     app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  #function name of login route for redirect
login_manager.login_message_category = 'danger'

#needed down here to avoid circular import
from productchecker import routes