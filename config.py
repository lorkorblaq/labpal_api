import os
from flask import Flask
from flask_restful import Api
from flask_mail import Mail

mail_password = os.getenv('MAIL_PASSWORD')

def create_app():
    app = Flask(__name__)

    # Flask-Mail Configuration
    app.config['MAIL_SERVER'] = 'email-smtp.eu-west-1.amazonaws.com'
    app.config['MAIL_PORT'] = 465  # TLS Wrapper port
    app.config['MAIL_USERNAME'] = 'AKIAYDWHTGGLELRQDSFC'  # Replace with your SMTP username
    app.config['MAIL_PASSWORD'] = mail_password  # Replace with your SMTP password
    app.config['MAIL_USE_SSL'] = True  # Using SSL on port 465
    app.config['MAIL_USE_TLS'] = False  # SSL and TLS are mutually exclusive here
    app.config['MAIL_DEFAULT_SENDER'] = ('LabPal', 'labpal@labpal.com.ng')
    app.config['MAIL_SUPPRESS_SEND'] = False
    app.config['MAIL_ASCII_ATTACHMENTS'] = False
    app.config['MAIL_DEBUG'] = True

    return app

app = create_app()
mail = Mail(app)
api = Api(app)

