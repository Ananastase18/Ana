import time
import smtplib
import requests
import argparse
import functools
import configparser
from bs4 import BeautifulSoup
from email.message import EmailMessage


def send_email(receiver, subject, body):
    smtp_server = 'smtp.example.com'
    smtp_port = 587
    smtp_user = 'your_email@example.com'
    smtp_password = 'your_password'

    msg = EmailMessage()
    msg['From'] = smtp_user
    msg['To'] = receiver
    msg['Subject'] = subject
    msg.set_content(body)

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        print("Email sent successfully")


def check_price_and_notify(products, _threshold_price, _notification_email):
    for product in products:
        if product['price'] < _threshold_price:
            subject = f"Price Alert: {product['title']}"
            body = f"The price of {product['title']} is now {product['price']} which is below your set threshold."
            send_email(_notification_email, subject, body)


def log_time(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} function took {end_time - start_time:.2f} seconds to complete.")
        return result
    return wrapper


def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    _url = config['DEFAULT']['url']
    _keywords = config['DEFAULT']['keywords']
    _threshold_price = config['DEFAULT']['threshold_price']
    _notification_email = config['DEFAULT']['notification_email']
    return _url, _keywords, _threshold_price, _notification_email


def process_price(price_str):
    if not any(char.isdigit() for char in price_str):
        return None
    return int(''.join(filter(str.isdigit, price_str)))


def scrapping(_url, _keywords, _threshold_price, _notification_email):
    response = requests.get(f'{_url}/oferte/q-{_keywords}/?search%5Border%5D=filter_float_price%3Aasc')

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        product_card_elements = soup.find_all('div', {'data-testid': 'l-card'})

        products = []

        for product_card_element in product_card_elements:
            title = product_card_element.find('h6')
            price = product_card_element.find('p', {'data-testid': 'ad-price'})

            if not title or not price or not process_price(price.text.strip()):
                continue

            title = title.text.strip()
            price = process_price(price.text.strip())

            products.append({
                'title': title,
                'price': price
            })

        products.sort(key=lambda p: p['price'])

        check_price_and_notify(products, _threshold_price, _notification_email)
    else:
        print('Request failed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrap and log prices.')
    parser.add_argument('-log', action='store_true', help='Log the time of the request')

    args = parser.parse_args()

    url, keywords, threshold_price, notification_email = read_config()

    if args.log:
        logged_scrapping = log_time(scrapping)
        logged_scrapping(url, keywords, threshold_price, notification_email)
    else:
        scrapping(url, keywords, threshold_price, notification_email)
