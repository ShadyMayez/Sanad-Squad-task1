import smtplib
from email.mime.text import MIMEText 
from email.mime.multipart import MIMEMultipart
from config import GMAIL_APP_PASSWORD,GMAIL_SENDER,GMAIL_RECIPIENT

def send_report_email(subject:str,body:str)->bool:
    msg= MIMEMultipart()
    msg["Subject"]=subject
    msg["From"]=GMAIL_SENDER
    msg["To"]=GMAIL_RECIPIENT
    msg.attach(MIMEText(body,"html"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
           server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
           server.sendmail(GMAIL_SENDER, GMAIL_RECIPIENT, msg.as_string())
        return True
    except Exception as e : 
        print(f"[ERROR]: an error occured while sending the email :\n-{e}")
        return False