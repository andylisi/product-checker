from flask import Flask, render_template, url_for
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
@app.route("/home")
def home():
    return render_template("dashboard.html", products=products)


@app.route("/settings")
def settings():
    return render_template("settings.html")


@app.route("/register")
def register():
    form = RegistrationForm()
    return render_template('register.html', title='Register', form=form)


@app.route("/login")
def login():
    form = LoginForm()
    return render_template('login.html', title='Login', form=form)


if __name__ == '__main__':
    app.run(debug == True)
