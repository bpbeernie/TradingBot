import datetime
from email.mime.text import MIMEText
import smtplib
import ssl
import json
from threading import Thread

from base64 import urlsafe_b64encode

PATH_TO_CRED = './Mail/credentials.json'
FROM_EMAIL = "bpbeernie.trading@gmail.com"
SETUP = False

def setup():
    global SETUP
    
    if SETUP:
        return
    
    global PORT
    global PASSWORD
    global USERNAME
    global SERVER
    
    with open(PATH_TO_CRED) as f:
        cred = json.load(f)
    
        PORT = cred["PORT"]
        PASSWORD = cred["PASSWORD"]
        USERNAME = cred["USERNAME"]
        SERVER = cred["SERVER"]
        
        SETUP = True

def sendEmail(header, body):
    thread = Thread(target = emailThread, args=(header,body))
    thread.start()

def emailThread(header, body):
    try:
        setup()
        body = f"{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n{body}"
        send_message("bpbeernie@gmail.com", header, body)

    except Exception as error:
        print(f"Failed to send email an error occurred: {error}")
        
def send_message(destination, obj, body):
    message = 'Subject: {}\n\n{}'.format(obj, body)
    
    service = ssl.create_default_context()
    
    with smtplib.SMTP_SSL(SERVER, PORT, context=service) as server:
        server.login(USERNAME, PASSWORD)
        server.sendmail(FROM_EMAIL, destination, message)


def build_message(destination, obj, body):
    message = MIMEText(body)
    message["to"] = destination
    message["from"] = FROM_EMAIL
    message["subject"] = obj

    return {"raw": urlsafe_b64encode(message.as_bytes()).decode()}
