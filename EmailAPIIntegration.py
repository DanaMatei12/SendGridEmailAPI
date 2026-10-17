# https://app.sendgrid.com/guide/integrate/langs/python
import os
from dotenv import load_dotenv

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL")
SENDGRID_TO_EMAILS = os.getenv("SENDGRID_TO_EMAILS")

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

message = Mail(
    from_email=SENDGRID_FROM_EMAIL,
    to_emails=SENDGRID_TO_EMAILS,
    subject='Sending with Twilio SendGrid',
    html_content='With <strong>Python</strong>')
try:
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    # sg.set_sendgrid_data_residency("eu")
    # uncomment the above line if you are sending mail using a regional EU subuser
    response = sg.send(message)
    print(response.status_code)
    print(response.body)
    print(response.headers)
except Exception as e:
    print(e.message)