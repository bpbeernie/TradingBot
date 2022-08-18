from __future__ import print_function
import os
import pickle
import datetime
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from email.mime.text import MIMEText

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from base64 import urlsafe_b64encode

PATH_TO_CRED = './Mail/credentials.json'
SCOPES = ['https://mail.google.com/']
FROM_EMAIL = 'bpbeernie.trading@gmail.com'

def sendEmail(header, body):
    try:
        body = f"{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n{body}"
        
        service = gmail_authenticate()
        
        send_message(service, 'bpbeernie@gmail.com', header, body)
        
    except HttpError as error:
        print(f'An error occurred: {error}')

def send_message(service, destination, obj, body):
    return service.users().messages().send(
      userId="me",
      body=build_message(destination, obj, body)
    ).execute()

def build_message(destination, obj, body):
    message = MIMEText(body)
    message['to'] = destination
    message['from'] = FROM_EMAIL
    message['subject'] = obj

    return {'raw': urlsafe_b64encode(message.as_bytes()).decode()}


def gmail_authenticate():
    creds = None
    # the file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # if there are no (valid) credentials availablle, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(PATH_TO_CRED, SCOPES)

            creds = flow.run_local_server(port=0)
        # save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)