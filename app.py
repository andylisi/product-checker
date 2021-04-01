from datetime import datetime
from flask import Flask, render_template, url_for, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from forms import RegistrationForm, LoginForm

app = Flask(__name__)
app.config['SECRET_KEY'] = '2rQ5uFcZHFB5iEvw4ZVYgSFYgozDUjA9'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

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
        return f"User('{self.password}', '{self.username}', '{self.email}', '{self.image_file}')"

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(30), unique=True, nullable=False)
    retailer = db.Column(db.String(30), nullable=False)
    url = db.Column(db.String(150), unique=True, nullable=False)
    date_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Product('{self.name}', '{self.retailer}', '{self.date_added}')"

products = [
    {
        'model': 'Macbook',
        'retailer': 'Best Buy',
        'stock': 'yes',
        'date': '2021-3-23'
    },
    {
        'model': 'Vizio TV',
        'retailer': 'Best Buy',
        'stock': 'no',
        'date': '2021-1-10'
    }
]


@app.route("/")
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", products=products)


@app.route("/settings")
def settings():
    return render_template("settings.html")


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        #arg1 data, arg2 category
        flash(f'Success - Welcome {form.username.data}!', 'success')
        return redirect(url_for('home'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.username.data == 'admin' and form.password.data == 'admin':
                    #arg1 data, arg2 category
            flash('Login Success', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccesful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)


if __name__ == '__main__':
    app.run(debug == True)
