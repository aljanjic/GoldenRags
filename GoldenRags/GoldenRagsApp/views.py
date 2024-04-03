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


def get_rags(product_url, item_color='', item_size='', send_sms='', phone_number = '', receivers_email = '', product_name = ''):




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
        email_notification(product_url, item_color, item_size, receivers_email, product_name)
        if send_sms == True:
            print('Bupi-bupi I send SMS but you need to remove comment from the code')
            #sms_notification(product_url, item_color, item_size, phone_number, product_name)
            global found
            found = True
  if item_size == 'X':
    print(result['sizes'])


def email_notification(product_url, item_color, item_size, receivers_email, product_name):

  sender = os.getenv('GOLDEN_MAIL')
  #receiver = receivers_email
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
                       from_= os.getenv('TWILIO_NUMBER'),
                       to = phone_number
                       #to= os.getenv('RECEIVER_NUMBER')
                   )

  print(message.sid)


def scrape_view(request):
    if request.method == 'POST':
        form = ScrapeForm(request.POST)
        if form.is_valid():
            product_url = form.cleaned_data['product_url']
            item_color = form.cleaned_data['item_color'].strip()
            item_size = form.cleaned_data['item_size'].upper()
            send_sms = form.cleaned_data['send_sms']       
            phone_number = form.cleaned_data['phone_number']
            receivers_email = form.cleaned_data['receivers_email']

            product_name = ''
            match = re.search(r"/([^/]+)-p\d+\.html", product_url)
            if match:
                product_name = match.group(1).replace("-", " ").upper()

            global attempt
            attempt = 1
            global found
            found = False
            info = ''
            while found == False:
                get_rags(product_url, item_color, item_size, send_sms, phone_number, receivers_email, product_name)
                attempt += 1
            pass
    else:
        form = ScrapeForm()
    return render(request, 'GoldenRagsApp/index.html', {'form': form})
