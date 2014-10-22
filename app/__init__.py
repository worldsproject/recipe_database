from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask_mail import Mail

from flask.ext.security import SQLAlchemyUserDatastore, Security

from flask.ext.restful import Api

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)

mail = Mail(app)

api = Api(app)

from app import models

user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
security = Security(app, user_datastore)

from app import views