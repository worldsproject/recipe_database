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