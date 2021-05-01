"""ProductChecker is an online product checking application.

It is designed to check the availability and price of products
available on several online retailers. It features the ability
to track availability and price in realtime and provide historical
graphs. 

It also features the ability to be notified in the case where 
products that were previously not in stock, become in stock. 
This functionality utilizes discord webhooks and requires the user
to configure a discord account and accompanying webhook seperately.

__init__.py sets many application wide attributes.

Many of the application wide variables are set and instances are 
instantiated. Ordering is important here for imports to avoid circular
imports. 

The product checking daemon/background service is initiated here
as a seperate daemon thread which will run independently in the 
background until the program closes.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
import threading, logging

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
'''
#Set file_handler config which is system wide.
file_handler = logging.FileHandler('./tmp/pc.log')
logging.basicConfig(level=logging.ERROR, 
                    format='%(asctime)s %(threadName)s %(levelname)s %(name)s %(message)s',
                    handlers=[file_handler])
'''
#Needed down here to avoid circular import
from productchecker import routes
from productchecker.models import Product

#This starts the product checking loop that runs as a seperate
#thread in the background keeping all product stats up to date.
#Needs User context before it can begin.
thread = threading.Thread(target=Product.product_check_loop)
thread.daemon = True
thread.start()