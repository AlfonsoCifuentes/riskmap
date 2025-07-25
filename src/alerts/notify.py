"""Notification helpers (email + Telegram).
Requires env vars: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, ALERTS_MAIL_TO,
TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
"""

import os
import smtplib
from email.mime.text import MIMEText
import requests
from utils.config import logger

SMTP_HOST=os.getenv("SMTP_HOST")
SMTP_PORT=int(os.getenv("SMTP_PORT","587"))
SMTP_USER=os.getenv("SMTP_USER")
SMTP_PASS=os.getenv("SMTP_PASS")
MAIL_TO=os.getenv("ALERTS_MAIL_TO")
TELEGRAM_TOKEN=os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT=os.getenv("TELEGRAM_CHAT_ID")


def send_email(subject:str,body:str):
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS and MAIL_TO):
        return
    msg=MIMEText(body)
    msg['Subject']=subject
    msg['From']=SMTP_USER
    msg['To']=MAIL_TO
    try:
        with smtplib.SMTP(SMTP_HOST,SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER,SMTP_PASS)
            server.sendmail(SMTP_USER,[MAIL_TO],msg.as_string())
    except Exception as e:
        logger.error(f"Email notify error: {e}")


def send_telegram(body:str):
    if not (TELEGRAM_TOKEN and TELEGRAM_CHAT):
        return
    url=f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url,json={"chat_id":TELEGRAM_CHAT,"text":body})
    except Exception as e:
        logger.error(f"Telegram notify error: {e}")


def send_notification(title:"Riskmap Alert",body:str):
    send_email(title,body)
    send_telegram(body)
