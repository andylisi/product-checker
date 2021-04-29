from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
import threading

USE_MYSQL = False 

app = Flask(__name__)
app.config['SECRET_KEY'] = '2rQ5uFcZHFB5iEvw4ZVYgSFYgozDUjA9'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
if USE_MYSQL:                                                                                                                                                                  
     app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://USERNAME:PASSWORD@localhost/DATABASENAME'                                                                                
else:                                                                                                                                                                          
     app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'productcheckerapp@gmail.com'
app.config['MAIL_PASSWORD'] = 'pcapplication8@'
mail = Mail(app)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  #function name of login route for redirect
login_manager.login_message_category = 'danger'


#needed down here to avoid circular import
from productchecker import routes
from productchecker.models import Product
#This starts the product checking loop that runs as a seperate
#thread in the background keeping all product stats up to date.
#Needs User context before it can begin.

thread = threading.Thread(target=Product.product_check_loop)
thread.daemon = True
thread.start()