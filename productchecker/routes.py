from flask import render_template, url_for, flash, redirect, request, abort
from productchecker import app, db, bcrypt
from productchecker.forms import RegistrationForm, LoginForm, UpdateAccountForm, ProductForm
from productchecker.models import User, Product, ProductHistory
from flask_login import login_user, logout_user, current_user, login_required
import logging, sys
from datetime import datetime
import threading


logging.basicConfig(filename='./tmp/PC.log', 
                    level=logging.ERROR, 
                    format='%(asctime)s %(threadName)s %(levelname)s %(name)s %(message)s')
logger=logging.getLogger(__name__)


@app.route("/")
@app.route("/dashboard")
@login_required
def dashboard():
    products = Product.get_user_products(current_user.id)
    return render_template("dashboard.html", products=products)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
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
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        #If user exists and password hash matches hash stored in db, login success
        #bcrypt.check_password_hash(hashed val, plain text val)
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            #remember keeps user logged in after browser close. Set remember=True
            login_user(user, remember=form.remember.data)
            #If a user was forced to auth from somewhere besides login page,
            # next will be populated with url_for(<whatever next page was supposed to be>)
            # ternary conditional
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccesful. Please check username and password', 'danger')

    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():

        current_user.username = form.username.data
        current_user.email = form.email.data

        if form.password.data != '':
            current_user.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        current_user.discord_webhook = form.discord_webhook.data
        current_user.discord_active = bool(form.discord_active.data)
        db.session.commit()
        flash('Account Updated', 'success')
        return redirect(url_for('account'))

    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.discord_webhook.data = current_user.discord_webhook
        form.discord_active.data = current_user.discord_active
    return render_template('account.html', form=form)


@app.route("/add_product", methods=['GET', 'POST'])
@login_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        new_product = Product()
        new_product.get_attr(form)

        new_product_history = ProductHistory()
        new_product_history.check_url(new_product)

        new_product.history.append(new_product_history)
        db.session.add(new_product)
        db.session.add(new_product_history)
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('add_product.html', title='Add Product', form=form)


@app.route("/product/<int:product_id>/delete", methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.user_id != current_user.id:
        abort(403)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('dashboard'))


@app.route("/product/<int:product_id>/graph", methods=['GET'])
@login_required
def graph(product_id):
    product_history = Product.get_history(product_id)
    alias = product_history[0][0]
    stock = []
    values = []
    for row in product_history:
        if row[2] == 1:
            stock.append("green")
        elif row[2] == 0:
            stock.append("red")
        if row[3] == None:
            values.append('null')
        else:
            values.append(row[3])

    #values = [row[3] for row in product_history]
    labels = [row[4] for row in product_history]
    return render_template('graph.html', values=values, labels=labels, alias=alias, stock=stock)

