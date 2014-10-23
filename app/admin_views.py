from flask.ext.admin.contrib.sqla import ModelView

class RecipeView(ModelView):
	column_list = ('id', 'name', 'description', 'directions', 'prep_time', 'cook_time', 'ingredients')

class IngredientView(ModelView):
	column_list = ('id', 'name')

class ModifierView(ModelView):
	column_list = ('id', 'name')

class ModifiedIngredientView(ModelView):
	column_list = ('id', 'amount', 'unit', 'ingredient')