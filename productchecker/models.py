import requests, re, time, logging, threading
from datetime import datetime
from productchecker import db, login_manager, app
from productchecker.notifications import sendNotification
from flask_login import UserMixin, current_user
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from sqlalchemy import func, case, literal_column


logging.basicConfig(filename='./tmp/PC.log', 
                    level=logging.ERROR, 
                    format='%(asctime)s %(threadName)s %(levelname)s %(name)s %(message)s')
logger=logging.getLogger(__name__)


@login_manager.user_loader
def load_user(user_id):
    """Used by Flask login manager to store currently authenticated user information.

    Fills out remainging attributes of current_user to be stored in memory so that
    db queries are not required everytime a user attr is needed.
    
    Args:
        user_id: ID of current user.
    
    Returns:
        All user attributes.
    """
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    """User class stores all User attributes and preferences.

    SQLAlchemy will store class data in memory until db.session.commit() is called.
    It will then write everything to database.

    Attributes:
        id: Unique user id set by system. *PK*
        username: Unique username chosen by user.
        email: Unique email address chosen by user.
        password: Hashed and salted password chosen by user.
        discord_webhook: URL of webhook(nullable).
        discord_active: Discord Alerting on/off.
        help_active: Help context - not currently in use.
        check_freq: Product checking frequency in seconds.
        products: Not materialzed in db. Defines table relationship.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    discord_webhook = db.Column(db.String(150), nullable=True)
    discord_active = db.Column(db.Boolean, nullable=False, default=0)
    help_active = db.Column(db.Boolean, nullable=False, default=1)
    check_freq = db.Column(db.Integer, nullable=False, default=60)
    products = db.relationship('Product', backref='user', lazy=True)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        '''__repr__ is used to compute the “official” string representation of an object 
        # and is typically used for debugging.
        '''
        return f"User('{self.id}', '{self.username}', '{self.email}')"


class Product(db.Model):
    """Product class stores all Product attributes about a single product.

    SQLAlchemy will store class data in memory until db.session.commit() is called.
    It will then write everything to database.

    Attributes:
        id: Unique product id set by system. *PK*
        alias: Easy to remember name set by user.
        brand: Brand according to retailer. Pulled on initial product check by beautiful soup.
        model: Model according to retailer. Pulled on initial product check by beautiful soup.
        retailer: Parsed from URL.
        url: Product URL provided by user.
        date_added: Timestamp product was added by user.
        user_id: User that added product. *FK*
        history: Not materialzed in db. Defines table relationship.
    """
    id = db.Column(db.Integer, primary_key=True)
    alias = db.Column(db.String(30), unique=False, nullable=False)
    brand = db.Column(db.String(30), nullable=False)
    model = db.Column(db.String(30), unique=False, nullable=False)
    retailer = db.Column(db.String(30), nullable=False)
    url = db.Column(db.String(250), unique=False, nullable=False)
    date_added = db.Column(db.DateTime, nullable=False, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    history = db.relationship('ProductHistory', cascade="all,delete", backref='product', lazy=True)

    def __repr__(self):
        return f"Product('{self.id}','{self.alias}','{self.brand}', '{self.model}', '{self.date_added}')"

    def get_page_html(self):
        """Get product page HTML to be parsed by Beautiful Soup.

        Headers are necessary to combat anti-bot measures taken by retailers.

        Returns:
            HTML content of the page.
        """
        headers = {
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
            'Accept-Language' : 'en-US,en;q=0.5',
            'Accept-Encoding' : 'gzip', 
            'DNT' : '1' # Do Not Track Request Header 
            }
        try:
            page = requests.get(self.url, headers=headers)
        except Exception as e:
            page=''
            logger.error(e)
            return page
        return page.content

    def check_url(self):
        """Check the page of a product to update ProductHistory.

        Depending on the retailer, differenct HTML elements will be checked.
        Bestbuy seems to have standard HTML element ID's and classes while 
        Amazon seems to have a variety. Due to this several try/excepts are
        needed to check for different elements.
        """
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
            except AttributeError:
                try:
                    brand_tag = soup.find("a", {"class": "a-link-normal qa-byline-url"}).text
                except AttributeError:
                    try:
                        brand_tag = soup.find("a", {"id": "bylineInfo"}).text
                    except AttributeError as e:
                        brand_tag = 'Unavailable'
                        logger.error(e)
            finally:
                brand_text = brand_tag.strip('\n')
                if brand_text.startswith('Brand: '):
                    brand_text = brand_text.replace('Brand: ', '')
                elif brand_text.startswith('Visit the '):
                    brand_text = brand_text.replace('Visit the ', '')
                self.brand = brand_text

            #Try known model tags, if no tags found mark as Unavailable
            try:
                model_tag = soup.find("span", {"id": "productTitle"}).text
            except AttributeError:
                try:
                    model_tag = soup.find("span", {"class": "a-size-large product-title-word-break"}).text
                except AttributeError:
                    try:
                        model_tag = soup.find("span", {"class": "a-size-large qa-title-text"}).text
                    except AttributeError as e:
                        model_tag = 'Unavailable'
                        logger.error(e)
            finally:
                self.model = model_tag.strip('\n')

    def get_attr(self, form):
        """Assigns attributes passed by form.

        When a user adds a new product, will asssign attributes according
        to user input and then check the URL to assign remaining attributes.

        Args:
            form: wtform with data submitted by user.
        """
        self.url = form.url.data
        self.alias = form.alias.data
        self.user = current_user
        self.check_url()
    
    @classmethod
    def check_all(cls):
        """Checks all distinct products in the product table.

        Will first query for a list of all distinct products and then 
        attempt to update all products history. If product was not previously
        in stock but now is, it will notify user if notifications are turned on.
        """
        distinct_products = cls.query.distinct(cls.id)
        for product in distinct_products:
            #Capture prev stock status before adding new
            previous_stock = Product.previous_stock(product.id)
            #Check new history and append to Product's history.
            new_history = ProductHistory()
            try:
                new_history.check_url(product)
            except Exception as e:
                logger.error(e)
                return
            product.history.append(new_history)

            #If user notifcations on, previously wasnt in stock and now is in stock, send notification.
            if  product.user.discord_active and\
                not previous_stock and\
                new_history.stock:
                    sendNotification(product, new_history)
            db.session.commit()

    @classmethod
    def get_user_products(cls, user):
        """Returns a list of all products belonging to a user.

        Args:
            user: A user object.
        """
        products = db.session.query(Product.id, Product.alias, Product.brand, Product.model, Product.retailer, Product.url,\
                                case((ProductHistory.stock==1,literal_column("'Yes'")),(ProductHistory.stock==0,literal_column("'No'"))).label('stock'),\
                                ProductHistory.price, func.max(ProductHistory.checked_ts).label('checked_ts'))\
        .filter(Product.user_id==user)\
        .filter(Product.id==ProductHistory.product_id)\
        .group_by(Product.id).all()
        return products

    @classmethod
    def get_history(cls, product_id):
        """Returns a list of all history belonging to a product.

        Args:
            product_id: ID of a product.
        """
        history = db.session.query(Product.alias, Product.id, ProductHistory.stock,func.min(ProductHistory.price).label('price'),func.strftime('%m-%d-%Y', ProductHistory.checked_ts).label('date'))\
            .filter(Product.id==product_id)\
            .filter(ProductHistory.product_id==product_id)\
            .group_by('date')\
            .all()
        return history

    @classmethod
    def previous_stock(cls, product_id):
        """Returns boolean of last known stock status of a product.

        Args:
            product_id: ID of a product.
        """
        previous_history = db.session.query(ProductHistory.stock, func.max(ProductHistory.checked_ts).label('checked_ts'))\
            .filter(Product.id==product_id)\
            .filter(ProductHistory.product_id==product_id)\
            .group_by(Product.id)\
            .all()
        return bool(previous_history[0].stock)

    @classmethod
    def product_check_loop(cls):
        """Runs the Product.check_all() in a controlled loop.

        Initiated by a daemon thread upon init, it will check all the products
        in a loop which the loop time is dictated by AppAttr.product_check_frequency.
        This time is dictated by the last user to update their Product Check Frequency
        within Account page.
        """
        while(1):
            check_freq = AppAttr.get_check_freq()

            start = datetime.now()
            print(f"--Thread {threading.get_ident()}: Begin Product Check - {start}--")
            cls.check_all()
            end = datetime.now()
            print(f"--Thread {threading.get_ident()}: Product Check Complete - {end}--")
            loop_time = int((end-start).total_seconds())

            #Run loop every <user_seconds>. If loop takes longer,
            #ignore sleep and just run as fast as possible.
            try:
                print(f"--Thread {threading.get_ident()}: Sleep for {check_freq-(loop_time)} seconds")
                time.sleep(max(0,(check_freq-(loop_time))))
            except ValueError as e: 
                logger.error(e)


class ProductHistory(db.Model):
    """ProductHistory class stores all product data related to stock and price.

    SQLAlchemy will store class data in memory until db.session.commit() is called.
    It will then write everything to database.

    Attributes:
        id: Unique ProductHistory id set by system. *PK*
        product_id: ID of the product that the history belongs to. *FK*
        stock: Stock status at the time it was checked.
        price: Price at the time it was checked.
        checked_ts: Timestamp when product was checked.
    """
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    stock = db.Column(db.Boolean, nullable=False)
    price = db.Column(db.Float, nullable=True)
    checked_ts = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def get_page_html(self, product):
        """Get product page HTML to be parsed by Beautiful Soup.

        Headers are necessary to combat anti-bot measures taken by retailers.

        Args:
            product: A product object.

        Returns:
            HTML content of the page.
        """
        headers = {
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
            'Accept-Language' : 'en-US,en;q=0.5',
            'Accept-Encoding' : 'gzip', 
            'DNT' : '1' # Do Not Track Request Header 
            }
        page = requests.get(product.url, headers=headers)
        return page.content

    def check_url(self, product):
        """Check the page of a product to update ProductHistory.

        Depending on the retailer, differenct HTML elements will be checked.
        Bestbuy seems to have standard HTML element ID's and classes while 
        Amazon seems to have a variety. Due to this several try/excepts are
        needed to check for different elements.

        Args:
            product: A product object.
        """
        page_html = self.get_page_html(product)
        soup = BeautifulSoup(page_html, 'html.parser')
        self.product_id = product.id

        if product.retailer == 'bestbuy':
            #Best Buy changes the button class depending if item is in stock or not.
            if soup.find("button", {"class": "btn btn-primary btn-lg btn-block btn-leading-ficon add-to-cart-button"}) != None:
                self.stock = True
            else:
                self.stock = False

            #price
            try: 
                price_div = soup.find('div', {'class' : 'priceView-hero-price priceView-customer-price'})
                string_price = price_div.span.text
                self.price = float(string_price[1:].replace(',',''))#remove leading $ and any comma's
            except AttributeError as e:
                self.price = 'null'
                logger.error(e)
        
        elif product.retailer == 'amazon':
            #stock
            try:
                soup.find('div', {'id': 'addToCart_feature_div'})
                self.stock = True
            except AttributeError as e:
                self.stock = False
                logger.error(e)

            #price
            try:
                price_div = soup.find('span', {'id' : 'priceblock_ourprice'}).text.strip('\n')
                self.price = float(price_div[1:].replace(',',''))#remove leading $ and any comma's
            except AttributeError:
                try:
                    price_div = soup.find('span', {'id' : 'priceblock_dealprice'}).text.strip('\n')
                    self.price = float(price_div[1:].replace(',',''))#remove leading $ and any comma's
                except AttributeError:
                    try:
                        price_div = soup.find('span', {'id' : 'price_inside_buybox'}).text.strip('\n')
                        self.price = float(price_div[1:].replace(',',''))#remove leading $ and any comma's
                    except AttributeError as e:
                        self.price = None
                        logger.error(e)

    def __repr__(self):
        return f"ProductHistory('{self.id}','{self.product_id}','{self.stock}','{self.price}','{self.checked_ts}')"


class AppAttr(db.Model, UserMixin):
    """AppAttr class stores all top level Application attributes.

    It is currently used to help share data between threads as threads in Flask are context dependent.
    The thread that begins in init.py which is the product checking daemon, has no access to the mainthread
    which can store things like current_user. In order to access the current users product check frequency,
    this classs was necessary so additional threads can read values from db. May be used further in the future.

    Attributes:
        id: 1 row to store all Application Atttributes.
        product_check_freq: Sets the time that the product checking thread will sleep between checks.
    """
    id = db.Column(db.Integer, primary_key=True)
    product_check_freq = db.Column(db.Integer, nullable=False, default=60)

    @classmethod
    def update_check_freq(cls, check_freq):
        """Updates the product check frequency.

        When a user updates their check frequency, it is also written to the 
        AppAttr.product_check_freq attribute.

        Args:
            check_freq: product check frequency in seconds.
        """
        app_attrs = cls.query.first()
        app_attrs.product_check_freq = check_freq
        db.session.commit()

    @classmethod
    def get_check_freq(cls):
        """Returns the product check frequency.
        """
        app_attrs = cls.query.first()
        return app_attrs.product_check_freq

    def __repr__(self):
        return f"User('{self.id}', '{self.product_check_freq}')"