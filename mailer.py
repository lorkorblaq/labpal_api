from flask_mail import Message
from config import mail
from flask import current_app, render_template
import os

def mailer(emailh, subjecth, htmlh):
    # with current_app.app_context():
    message = Message(
        subject=subjecth,
        recipients=[emailh],
    )
    message.html = htmlh
    try:
        return mail.send(message)
    except Exception as e:
        return f'Failed to send email: {str(e)}'

def app_mail(email, subject, data):
    html_content = render_template("templates_for_mail/app.html", data=data)
    mailer(email, subject, html_content)
    return "Mail sent"

    