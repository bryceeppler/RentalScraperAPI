import boto3
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

async def send_email(listings, recipients):
    client = boto3.client('ses')
    subject = "New listings within the polygon!"
    
    body = f"Here are the new listings:\n\n"
    for listing in listings:
        body += f"{listing['title']} - {listing['link']}\n"
    
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        response = client.send_raw_email(
            Source=os.environ['SENDER_EMAIL'] if 'SENDER_EMAIL' in os.environ else 'eppler97@gmail.com',
            Destinations=recipients,
            RawMessage={
                'Data': msg.as_string()
            }
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])