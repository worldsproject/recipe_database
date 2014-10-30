from flask.ext.admin.contrib.sqla import ModelView
from app.views import current_user

class RecipeView(ModelView):
    def is_accessible(self):
        return current_user.has_role("admin")

    column_list = ('id', 'name', 'description', 'directions', 'prep_time', 'cook_time', 'ingredients')

class IngredientView(ModelView):
    def is_accessible(self):
        return current_user.has_role("admin")

    column_list = ('id', 'amount', 'unit', 'name')