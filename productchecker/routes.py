from flask import render_template, url_for, flash, redirect, request
from productchecker import app, db, bcrypt
from productchecker.forms import RegistrationForm, LoginForm, UpdateAccountForm, ProductForm
from productchecker.models import User, Product, ProductHistory
from flask_login import login_user, logout_user, current_user, login_required
import logging, sys
from productchecker.get_product_info import checkProduct
from sqlalchemy import func

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

#threading.Thread(target=bb.checkPage, args=(url,)).start()

@app.route("/")
@app.route("/dashboard")
@login_required
def dashboard():
    Product.check_all()
    sql = "Select p.alias,p.brand,p.model,p.retailer,CASE ph.stock WHEN True THEN 'Yes' ELSE 'No' END,ph.price,MAX(ph.checked_ts)\
            FROM product_history ph\
            Join product p\
            ON ph.product_id=p.id\
            WHERE p.user_id = :cur_usr\
            GROUP BY ph.product_id;"
    #we can pass parameters into query like with cur_usr
    products = db.session.execute(sql, {'cur_usr': current_user.id}).fetchall()
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
            logging.info('User ' + user.username + ' succesfully authenticated')

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
        logging.info('User ' + current_user.username + ' changed password to ' + current_user.password)

        current_user.username = form.username.data
        current_user.email = form.email.data

        if form.password.data != '':
            current_user.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        current_user.discord_webhook = form.discord_webhook.data

        if form.discord_active:
            current_user.discord_active = 1
        else:
            current_user.discord_active = 0

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