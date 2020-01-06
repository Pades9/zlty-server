from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_pushjack import FlaskAPNS
from flask_pushjack import FlaskGCM
from flask_apscheduler import APScheduler

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
# auto = Autodoc(app)
clientapns = FlaskAPNS()
clientapns.init_app(app)
clientgcm = FlaskGCM()
clientgcm.init_app(app)
scheduler = APScheduler()
