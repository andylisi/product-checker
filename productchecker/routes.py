from flask import render_template, url_for, flash, redirect, request, abort
from productchecker import app, db, bcrypt
from productchecker.forms import RegistrationForm, LoginForm, UpdateAccountForm, ProductForm
from productchecker.models import User, Product, ProductHistory, AppAttr
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
    """Returns the dashboard for for the authenticated user.

    User's products are passed through to the template, flask 
    will then render the appropriate html.

    """
    products = Product.get_user_products(current_user.id)
    return render_template("dashboard.html", products=products)


@app.route("/register", methods=['GET', 'POST'])
def register():
    """The page where users register for an account.

    User's will be required to provide a username, email, password,
    and confirmation of password.

    Returns:
        register: The page where registration for new users takes place.
        dashboard: If user is already authenticated, they will be redirected to their 
            dashboard with any products they have added. If user is new, they will be
            shown a new dashboard with welcome message.
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        #arg1 data, arg2 category
        flash(f'Account creation success - Welcome {form.username.data}!', 'success')
        flash(f'Add a product to get started. Click on the "?" for help.', 'info')
        return redirect(url_for('add_product'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    """The page where users login once they have an account.

    User's will be required to provide a username and correct password. Optionally 
    may choose "remember me" which will cache user auth status.

    Returns:
        login: The page where users login to site.
        dashboard: If user is already authenticated, they will be redirected to their 
            dashboard with any products they have added. If user was trying to visit
            a different page when their session ended, they will be redirected to 
            the page they were trying to visit.
    """
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
    """Ends user session and redirects to login page.

    Returns:
        login: The page where users login to site.
    """
    logout_user()
    return redirect(url_for('login'))


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    """The page where users can udpate account information, preferences, and notifications.

    Note: Currently Product Check Frequency will right to Application Attribute and effectively
    whoever updates check freq last, will dictate how frequently checks are performed.

    Returns:
        account: Account page.
    """
    form = UpdateAccountForm()
    if form.validate_on_submit():

        current_user.username = form.username.data
        current_user.email = form.email.data

        if form.password.data != '':
            current_user.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        current_user.discord_webhook = form.discord_webhook.data
        current_user.discord_active = bool(form.discord_active.data)
        # Set for user profile and application attribute so check_all thread can read value.
        # Cannot share data between threads so this allows other threads to read from db.
        current_user.check_freq = form.check_freq.data
        AppAttr.update_check_freq(form.check_freq.data)
        db.session.commit()
        flash('Account Updated', 'success')
        return redirect(url_for('account'))

    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.discord_webhook.data = current_user.discord_webhook
        form.discord_active.data = current_user.discord_active
        form.check_freq.data = current_user.check_freq
    return render_template('account.html', form=form)


@app.route("/add_product", methods=['GET', 'POST'])
@login_required
def add_product():
    """Returns page where users add new products they wish to track. 

    Upon success redirects to dashboard.
    """
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
    """Button on Dashboard table data that will delete product from databse.

    Will delete product and any product history and therefore stop tracking history
    in subsequent product checks.

    Args:
        product_id: Product ID that will be deleted
    Returns:
        dashboard: Dashboard page.
    """
    product = Product.query.get_or_404(product_id)
    if product.user_id != current_user.id:
        abort(403)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('dashboard'))


@app.route("/product/<int:product_id>/graph", methods=['GET'])
@login_required
def graph(product_id):
    """Button on Dashboard table data that show a graph of a single products stock and price.

    Data must be queried and prepared before being passed to graph page. Chart.js used for 
    graphs. Data and labels are bare minimum to pass and each must be prepared as list with 
    same amount of items. Also chose to prepare pointBackgroundColor to indicate in stock or
    not by setting red or green.

    Args:
        product_id: Product ID that graph will be generated for
    Returns:
        graph: Graph page for product.
    """
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

    labels = [row[4] for row in product_history]
    return render_template('graph.html', values=values, labels=labels, alias=alias, stock=stock)

