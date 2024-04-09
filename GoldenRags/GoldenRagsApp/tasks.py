from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from celery.exceptions import Retry
import os
import traceback
import json
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from pyvirtualdisplay import Display


def get_driver(product_url):
    # Set options to make browsing easier
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
   
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    driver.get(f"{product_url}")
    return driver


@shared_task(bind=True, max_retries=6048, default_retry_delay=100)
def get_rags_async(self, product_url, item_color, item_size, send_sms, phone_number, receivers_email, product_name):
    try:
        print('Looking for Krpa')
        
        display = Display(visible=0, size=(800, 600))
        display.start()
        driver = get_driver(product_url)

        content = driver.page_source

        soup = BeautifulSoup(content, 'html.parser')

        with open(f'dostupnost{random.randint(1, 1060)}.txt', 'w+') as f:
            f.write(str(soup))
            f.seek(0)
            content = f.read()

        # Extract the relevant information

        first_name_index = content.find(f'"name":"{item_color}","reference"')
        last_name_index = first_name_index + len('"name": ') + len(item_color)

        first_object_index = content.find('"sizes":[{', first_name_index)
        last_object_index = content.find('],"description"', first_object_index)

        result = {
            'name': content[first_name_index + 8:last_name_index],
            'sizes': content[first_object_index + 9:last_object_index]
        }

        sizes = '[' + result['sizes'] + ']'
        result['sizes'] = json.loads(sizes)

        item_found = False
        display.stop()
        driver.quit()
        # Print the result
        for size in result['sizes']:
            if size['name'] == item_size:
                if size['availability'] != 'in_stock':
                    print(f'Not available #figure out how to insert attempt')
                else:
                    print('Item found')
                    email_notification(product_url, item_color,
                                       item_size, receivers_email, product_name)
                    if send_sms:
                        print(
                            'Bupi-bupi I send SMS but you need to remove comment from the code')
                        # sms_notification(product_url, item_color, item_size, phone_number, product_name)
                    item_found = True
                    break
        if not item_found:
            print("Item not found, will retry...11111111111111111")
            self.retry()
    except Retry as retry_exc:
        print('Scheduling retry...')
        raise retry_exc
    except Exception as exc:
        print('Task failed failed failed failed', traceback.format_exc())



def email_notification(product_url, item_color, item_size, receivers_email, product_name):

    sender = os.getenv('GOLDEN_MAIL')
    # receiver = receivers_email
    receiver = os.getenv('RECEIVER_MAIL')
    password = os.getenv('GOLDEN_PASSWORD')

    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = receiver
    message[
        'Subject'] = f'{item_color} {product_name} is available. Size: {item_size}'

    body = f"""
    <h2>{item_color} {product_name} is available. Size: {item_size}</h2>
    
    {product_name} is available
    <a href={product_url}'> Buy now! </a>
    """
    mimetext = MIMEText(body, 'html')
    message.attach(mimetext)

    server = smtplib.SMTP('smtp.office365.com', 587)
    server.ehlo()
    server.starttls()
    server.login(sender, password)
    message_text = message.as_string()
    server.sendmail(sender, receiver, message_text)
    server.quit()
    global info
    info = 'User was notified about product availability'
    print('Mail sent')
    global found
    found = True


def sms_notification(product_url, item_color, item_size, phone_number, product_name):
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    client = Client(account_sid, auth_token)

    message = client.messages \
                    .create(
                        body=f"""
                       {item_color} {product_name} Size: {item_size} is now available. Buy it now on: {product_url}
                       """,
                        from_=os.getenv('TWILIO_NUMBER'),
                        to=phone_number
                        # to= os.getenv('RECEIVER_NUMBER')
                    )

    print(message.sid)
