from celery import shared_task
import time, json, random
from bs4 import BeautifulSoup
from selenium import webdriver
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from twilio.rest import Client

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


@shared_task
def get_rags_async(product_url, item_color, item_size, send_sms, phone_number, receivers_email, product_name):

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

  item_found = False
  
  # Print the result
  for size in result['sizes']:
    if size['name'] == item_size:
      if size['availability'] != 'in_stock':
         
        print(f'Not available #figure out how to insert attempt')
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