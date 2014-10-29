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

from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView
from app.admin_views import RecipeView, IngredientView, ModifierView, ModifiedIngredientView

admin = Admin(app)
admin.add_view(RecipeView(models.Recipe, db.session))
admin.add_view(ModifiedIngredientView(models.ModifiedIngredient, db.session))
admin.add_view(IngredientView(models.Ingredient, db.session))
admin.add_view(ModifierView(models.Modifier, db.session))

from app import views

#Email errors when not in debug mode
from config import basedir, ADMINS, MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD

if not app.debug:
    import logging
    from logging.handlers import SMTPHandler
    credentials = None
    if MAIL_USERNAME or MAIL_PASSWORD:
        credentials = (MAIL_USERNAME, MAIL_PASSWORD)
    mail_handler = SMTPHandler((MAIL_SERVER, MAIL_PORT), 'no-reply@' + MAIL_SERVER, ADMINS, 'recipe database failure', credentials)
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler('tmp/recipe_database.log', 'a', 1 * 1024 * 1024, 10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('recipe database startup')