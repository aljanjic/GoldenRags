from django.shortcuts import render
from .forms import ScrapeForm
from selenium import webdriver
import time, json, random
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import re
from twilio.rest import Client
import random




def get_driver(product_url):
  # Set options to make browsing easier
  options = webdriver.ChromeOptions()
  options.add_argument("disable-infobars")
  options.add_argument("start-maximized")
  options.add_argument("disable-dev-shm-usage")
  options.add_argument("no-sandbox")
  options.add_experimental_option("excludeSwitches", ["enable-automation"])
  options.add_argument("disable-blink-features=AutomationControlled")
  driver = webdriver.Chrome(options=options)
  driver.get(f"{product_url}")
  return driver


def get_krpu(product_url, item_color='', item_size='', send_sms=''):

  attempt = 1
  found = False
  info = ''
  # if itemSize != 'X':
  #     buy = input('Zelis li da proizvod bude kupljen "da/ne"?: ').lower()

  print('Looking for Krpa')
  driver = get_driver(product_url)

  content = driver.page_source

  soup = BeautifulSoup(content, 'html.parser')

  with open('dostupnost.txt', 'w+') as f:
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

  # Print the result
  for size in result['sizes']:
    if size['name'] == item_size:
      if size['availability'] != 'in_stock':
         
        print(f'Not available {attempt}')
        time.sleep(random.randint(30, 60))
      else:
        print('Item found')
        time.sleep(2)
        send_email(product_url, item_color, item_size, send_sms)
        # if buy == 'YES':
        #   buy_product(driver, soup, item_size, item_color)
  if item_size == 'X':
    print(result)


def send_email(url, itemColor, itemSize, sms):

  sender = os.getenv('GOLDEN_MAIL')
  # Add variable for  receiver email address
  receiver = os.getenv('RECEIVER_MAIL')
  password = os.getenv('GOLDEN_PASSWORD')

  product_name = ''
  match = re.search(r"/([^/]+)-p\d+\.html", url)
  if match:
    product_name = match.group(1).replace("-", " ").upper()

  message = MIMEMultipart()
  message['From'] = sender
  message['To'] = receiver
  message[
    'Subject'] = f'{itemColor} {product_name} is available. Size: {itemSize}'

  body = f"""
    <h2>{itemColor} {product_name} is available. Size: {itemSize}</h2>
    
    {product_name} je na stanju
    <a href={url}'> Kupi odmah! </a>
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
  if sms == 'YES':
    print('Bupi-bupi I send SMS but you need to remove comment from the code')
    #send_sms(itemColor, itemSize, product_name, url)


def send_sms(itemColor, itemSize, product_name, url):
  account_sid = os.environ['TWILIO_ACCOUNT_SID']
  auth_token = os.environ['TWILIO_AUTH_TOKEN']
  client = Client(account_sid, auth_token)

  message = client.messages \
                  .create(
                       body=f"""
                       {itemColor} {product_name} Size: {itemSize} is now available. Buy it now on: {url}
                       """,
                       from_= os.getenv('TWILIO_NUMBER'),
                       to= os.getenv('RECEIVER_NUMBER')
                   )

  print(message.sid)


def scrape_view(request):
    if request.method == 'POST':
        form = ScrapeForm(request.POST)
        if form.is_valid():
            product_url = form.cleaned_data['product_url']
            item_color = form.cleaned_data['item_color']
            item_size = form.cleaned_data['item_size'].upper()
            send_sms = form.cleaned_data['send_sms']
        
            get_krpu(product_url, item_color, item_size, send_sms)
            pass
    else:
        form = ScrapeForm()
    return render(request, 'GoldenRagsApp/index.html', {'form': form})
