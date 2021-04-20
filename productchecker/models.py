import requests
import re
from datetime import datetime
from productchecker import db, login_manager
from flask_login import UserMixin, current_user
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from sqlalchemy import func, case, literal_column

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# This class will create a table schema within the db.
# Set datatypes, uqique, req/nullable and keys
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    discord_webhook = db.Column(db.String(150), nullable=True)
    discord_active = db.Column(db.Boolean, nullable=True, default=0)
    products = db.relationship('Product', backref='user', lazy=True)

    def __repr__(self):
        '''__repr__ is used to compute the “official” string representation of an object 
        # and is typically used for debugging.
        '''
        return f"User('{self.id}', '{self.username}', '{self.email}')"


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    alias = db.Column(db.String(30), unique=False, nullable=False)
    brand = db.Column(db.String(30), nullable=False)
    model = db.Column(db.String(30), unique=False, nullable=False)
    retailer = db.Column(db.String(30), nullable=False)
    url = db.Column(db.String(150), unique=False, nullable=False)
    date_added = db.Column(db.DateTime, nullable=False, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    history = db.relationship('ProductHistory', cascade="all,delete", backref='product', lazy=True)

    def __repr__(self):
        return f"Product('{self.id}','{self.alias}','{self.brand}', '{self.model}', '{self.date_added}')"

    #Spoofing the user agent request
    def get_page_html(self):
        headers = {
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
            'Accept-Language' : 'en-US,en;q=0.5',
            'Accept-Encoding' : 'gzip', 
            'DNT' : '1' # Do Not Track Request Header 
            }
        page = requests.get(self.url, headers=headers)
        return page.content

    #Checking the url
    def check_url(self):
        page_html = self.get_page_html()
        soup = BeautifulSoup(page_html, 'html.parser')

        retailer_domain = urlparse(self.url).netloc.split(".")
        self.retailer = retailer_domain[1]

        if self.retailer == 'bestbuy':
            self.brand = soup.find("a", {"class": "btn btn-link v-medium btn-brand-link"}).text
            self.model = soup.find("h1", {"class": "heading-5 v-fw-regular"}).text
        elif self.retailer == 'amazon':
            #Amazon pages are not very standardized. Have to try several tags
            try:
                brand_tag = soup.find("div", {"id": "mbc"})
                brand_tag = brand_tag.get('data-brand')
            except:
                pass

                try:
                    brand_tag = soup.find("a", {"class": "a-link-normal qa-byline-url"}).text
                except:
                    pass

                    try:
                        brand_tag = soup.find("a", {"id": "bylineInfo"}).text
                    except:
                        pass
                        
                        try:
                            brand_tag = 'Unknown'
                        except:
                            pass
            finally:
                brand_text = brand_tag.strip('\n')
                if brand_text.startswith('Brand: '):
                    brand_text = brand_text.replace('Brand: ', '')
                self.brand = brand_text

            #model
            try:
                model_tag = soup.find("span", {"id": "productTitle"}).text
            except:
                pass

                try:
                    model_tag = soup.find("span", {"class": "a-size-large product-title-word-break"}).text
                except:
                    pass

                    try:
                        model_tag = soup.find("span", {"class": "a-size-large qa-title-text"}).text
                    except:
                        model_tag = 'Unknown'
            finally:
                self.model = model_tag.strip('\n')

    def get_attr(self, form):
        self.url = form.url.data
        self.alias = form.alias.data
        self.user = current_user
        self.check_url()
        print(self)
    
    @classmethod
    def check_all(cls):
        distinct_products = cls.query.distinct(cls.id)
        for product in distinct_products:
            product_history = ProductHistory()
            product_history.check_url(product)
            product.history.append(product_history)
        db.session.commit()

    @classmethod
    def get_user_products(cls, user):
        products = db.session.query(Product.id, Product.alias, Product.brand, Product.model, Product.retailer,\
                                case((ProductHistory.stock==1,literal_column("'Yes'")),(ProductHistory.stock==0,literal_column("'No'"))).label('stock'),\
                                ProductHistory.price, func.max(ProductHistory.checked_ts).label('checked_ts'))\
        .filter(Product.user_id==user)\
        .filter(Product.id==ProductHistory.product_id)\
        .group_by(Product.id).all()
        return products

    @classmethod
    def get_history(cls, product_id):
        history = db.session.query(Product.alias, Product.id, ProductHistory.stock,func.min(ProductHistory.price).label('price'),func.strftime('%m-%d-%Y', ProductHistory.checked_ts).label('date'))\
            .filter(Product.id==product_id)\
            .filter(ProductHistory.product_id==product_id)\
            .group_by('date')\
            .all()
        return history


class ProductHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    stock = db.Column(db.Boolean, nullable=False)
    price = db.Column(db.Float, nullable=True)
    checked_ts = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def get_page_html(self, product):
        headers = {
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
            'Accept-Language' : 'en-US,en;q=0.5',
            'Accept-Encoding' : 'gzip', 
            'DNT' : '1' # Do Not Track Request Header 
            }
        page = requests.get(product.url, headers=headers)
        return page.content

    #Checking the url
    def check_url(self, product):
        page_html = self.get_page_html(product)
        soup = BeautifulSoup(page_html, 'html.parser')
        self.product_id = product.id

        if product.retailer == 'bestbuy':
            #Best Buy changes the button class depending if item is in stock or not.
            if soup.find("button", {"class": "btn btn-primary btn-lg btn-block btn-leading-ficon add-to-cart-button"}):
                self.stock = True
            else:
                self.stock = False

            #price
            price_div = soup.find('div', {'class' : 'priceView-hero-price priceView-customer-price'})
            if price_div:
                string_price = price_div.span.text
                self.price = float(string_price[1:].replace(',',''))#remove leading $ and any comma's
            else:
                self.price = 'null'
        
        elif product.retailer == 'amazon':
            if soup.find('div', {'id': 'addToCart_feature_div'}):
                self.stock = True
            else:
                self.stock = False

            #price
            try:
                price_div = soup.find('span', {'id' : 'priceblock_ourprice'}).text
            except:
                pass
                
                try:
                    price_div = None
                except:
                    pass

            finally:
                if price_div != None:
                    self.price = float(price_div[1:].replace(',',''))#remove leading $ and any comma's
                else:
                    self.price = price_div

    
    def __repr__(self):
        return f"ProductHistory('{self.id}','{self.product_id}','{self.stock}','{self.price}','{self.checked_ts}')"