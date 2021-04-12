import datetime
import requests
from bs4 import BeautifulSoup
#from playsound import playsound

#Spoofing the user agent request
def get_page_html(url):
    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}
    page = requests.get(url, headers=headers)
    return page.content

#Checking the url
def check_url(url):
    page_html = get_page_html(url)
    soup = BeautifulSoup(page_html, 'html.parser')
    price_div = soup.find('div', {'class' : 'priceView-hero-price priceView-customer-price'})
    string_price = price_div.span.text
    price = float(string_price[1:].replace(',',''))#remove leading $ and any comma's
    brand = soup.find("a", {"class": "btn btn-link v-medium btn-brand-link"}).text
    model = soup.find("h1", {"class": "heading-5 v-fw-regular"}).text
    #Best Buy changes the button class depending if item is in stock or not.
    if soup.find("button", {"class": "btn btn-primary btn-lg btn-block btn-leading-ficon add-to-cart-button"}):
        available = 1
    else:
        available = 0

    date_checked = datetime.datetime.now()

check_url('https://www.bestbuy.com/site/nvidia-geforce-rtx-3090-24gb-gddr6x-pci-express-4-0-graphics-card-titanium-and-black/6429434.p?skuId=6429434')