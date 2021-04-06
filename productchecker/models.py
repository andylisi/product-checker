from datetime import datetime
from productchecker import db

# This class will create a table schema within the db.
# Set datatypes, uqique, req/nullable and keys
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    products = db.relationship('Product', backref='user', lazy=True)

    #__repr__ is used to compute the “official” string representation of an object 
    # and is typically used for debugging.
    def __repr__(self):
        return f"User('{self.id}', '{self.username}', '{self.email}', '{self.image_file}')"

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(30), unique=True, nullable=False)
    retailer = db.Column(db.String(30), nullable=False)
    url = db.Column(db.String(150), unique=True, nullable=False)
    date_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Product('{self.name}', '{self.retailer}', '{self.date_added}')"
