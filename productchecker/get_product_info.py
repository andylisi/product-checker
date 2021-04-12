import datetime
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
from flask_login import current_user

class checkProduct():
    def __init__(self, form):
        self.url = form.url.data
        self.alias = form.alias.data
        self.user = current_user

        self.check_url()

    #Spoofing the user agent request
    def get_page_html(self):
        headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}
        page = requests.get(self.url, headers=headers)
        return page.content

    #Checking the url
    def check_url(self):
        page_html = self.get_page_html()
        soup = BeautifulSoup(page_html, 'html.parser')
        self.brand = soup.find("a", {"class": "btn btn-link v-medium btn-brand-link"}).text
        self.model = soup.find("h1", {"class": "heading-5 v-fw-regular"}).text

        retailer_domain = urlparse(self.url).netloc.split(".")
        self.retailer = retailer_domain[1]

        self.date_checked = datetime.datetime.now()
        print(self)

            

'''
    #Best Buy changes the button class depending if item is in stock or not.
    if soup.find("button", {"class": "btn btn-primary btn-lg btn-block btn-leading-ficon add-to-cart-button"}):
        product.available = True
    else:
        product.available = False
'''