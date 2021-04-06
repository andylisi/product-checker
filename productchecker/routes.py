from flask import render_template, url_for, flash, redirect
from productchecker import app, db, bcrypt
from productchecker.forms import RegistrationForm, LoginForm
from productchecker.models import User, Product

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
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        #arg1 data, arg2 category
        flash(f'Account creation success - Welcome {form.username.data}!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.username.data == 'admin' and form.password.data == 'admin':
                    #arg1 data, arg2 category
            flash('Login Success', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccesful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)