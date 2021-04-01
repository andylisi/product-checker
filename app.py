from flask import Flask, render_template, url_for, flash, redirect
from forms import RegistrationForm, LoginForm

app = Flask(__name__)

app.config['SECRET_KEY'] = '2rQ5uFcZHFB5iEvw4ZVYgSFYgozDUjA9'

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
