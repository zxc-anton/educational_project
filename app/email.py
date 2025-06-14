from app import mail
from flask_mail import Message
from threading import Thread
from flask import current_app

def send_async_mail(app, msg):
    with app.app_context():
        mail.send(msg)

def send_mail(subject, sender, recipients, text_body, html_body, attachments=None, sync=False):
    msq = Message(subject, sender=sender, recipients=recipients)
    msq.body = text_body
    msq.html = html_body
    if attachments:
        for attachment in attachments:
            msq.attach(*attachment)
    if sync:
        send_async_mail(app=current_app._get_current_object(), msg=msq)
    else:
        Thread(target=send_async_mail, args=(current_app._get_current_object(), msq)).start()

    