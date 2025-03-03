from twilio.rest import Client
import sendgrid
from sendgrid.helpers.mail import Mail
import os
from prisma import Prisma

# Twilio and SendGrid setup
TWILIO_SID = os.getenv('TWILIO_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')

client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)

def send_sms(to, message):
    client.messages.create(body=message, from_=os.getenv('TWILIO_PHONE_NUMBER'), to=to)

def send_email(to, subject, content):
    email = Mail(from_email=os.getenv('SENDGRID_FROM_EMAIL'), to_emails=to, subject=subject, plain_text_content=content)
    sg.send(email)

async def notify_user(user_id, message):
    prisma = Prisma()
    await prisma.connect()

    contacts = await prisma.notificationcontact.find_many(where={"userId": user_id})

    for contact in contacts:
        if contact.type == 'phone':
            send_sms(contact.value, message)
        elif contact.type == 'email':
            send_email(contact.value, 'Security Alert', message)

    await prisma.disconnect()

# Call this function within existing alert handlers 