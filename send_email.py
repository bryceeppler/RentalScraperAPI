import boto3
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import base64
import requests

from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import base64
import requests
AWS_REGION = "us-east-1"
async def send_email(listings, recipients):
    client = boto3.client('ses', region_name=AWS_REGION)
    subject = "New listings within the polygon!"

    # Create the HTML email body
    body = f"""
    <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .listing {{
                    display: flex;
                    flex-wrap: wrap;
                    margin-bottom: 20px;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    padding: 10px;
                }}
                .listing img {{
                    max-width: 150px;
                    max-height: 150px;
                    margin-right: 20px;
                    object-fit: cover;
                }}
                .listing-info {{
                    flex: 1;
                }}
                .listing-title {{
                    font-size: 1.2em;
                    font-weight: bold;
                }}
                .listing-price {{
                    font-size: 1.1em;
                    color: #4CAF50;
                }}
                .listing-link {{
                    text-decoration: none;
                    color: #2196F3;
                }}
            </style>
        </head>
        <body>
            <h1>New listings within the polygon!</h1>
    """

    for listing in listings:
        image_url = listing['images'][0] if listing['images'] else 'https://via.placeholder.com/150'
        image_data = requests.get(image_url).content
        image = MIMEImage(image_data)

        body += f"""
            <div class="listing">
                <img src="{
                image_url
                }" alt="{listing['title']}">
                <div class="listing-info">
                    <div class="listing-title">{listing['title']}</div>
                    <div class="listing-price">{listing['price']}</div>
                    <a class="listing-link" href="{listing['link']}">View Listing</a>
                </div>
            </div>
        """

    body += "</body></html>"

    # Create the email message
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))



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
