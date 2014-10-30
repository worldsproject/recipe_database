from flask.ext.restful import Resource, reqparse
from flask import jsonify
from app import api, db, models

def user_able(user_key):
	if user_key == config.API_KEY:
		return True
	
	user = db.session.query(models.User).filter(models.User.key == user_key).first()

	if user.free_credits > 0:
		user.free_credits = user.free_credits - 1;
		db.session.commit()
		return True

	if user.credits > 0:
		user.credits = user.credits - 1;
		db.session.commit()
		return True

	return False

def json_recipe(recipe):
	rv = {}

	rv['name'] = recipe.name
	rv['directions'] = recipe.directions
	i = []

	for ing in recipe.ingredients:
		ings = {}
		ings['name'] = ing.name
		ings['unit'] = ing.unit
		ings['amount'] = ing.amount
		ings['modifiers'] = ing.modifiers
		
		i.append(ings)

	rv['ingredients'] = i

	return rv


class IngredientAPI(Resource):
	def __init__(self):
		self.reqparse = reqparse.RequestParser()
		self.reqparse.add_argument('with', type=str, help='Ingredients that you require in your recipe.', action='append')
		self.reqparse.add_argument('without', type=str, help='Ingredients that cannot be in your recipe.', action='append')
		self.reqparse.add_argument('key', required=True, type=str, help="Your API key is required.")

	def post(self):
		args = self.reqparse.parse_args()

		if user_able(args['key']):
			t = None
			for ing in args['with']:
				q = db.session.query(models.Recipe).join(models.Ingredient).filter(models.Ingredient.name == ing)

				if t is not None:
					t = t.intersect(q)
				else:
					t = q

			for ing in args['without']:
				q = db.session.query(models.Recipe).join(models.Ingredient).filter(models.Ingredient.name != ing)

				if t is not None:
					t = t.intersect(q)
				else:
					t = q				

			rv = []

			for r in t:
				rv.append(json_recipe(r))

			return rv


class RecipeAPI(Resource):
	def __init__(self):
		self.reqparse = reqparse.RequestParser()
		self.reqparse.add_argument('key', type=str, required=True, help='Your API Key is required.')

	def get(self, id):
		args = self.reqparse.parse_args()
		if user_able(args['key']):
			recipe = db.session.query(models.Recipe).filter(models.Recipe.id == id).first()
			
			return(json_recipe(recipe))
		else:
			abort(403)

class RecipeTitleAPI(Resource):
	def __init__(self):
		self.reqparse = reqparse.RequestParser()
		self.reqparse.add_argument('key', type=str, required=True, help='Your API Key is required.')
		self.reqparse.add_argument('name', type=str, required=True, help='Your search terms are required.')

	def post(self):
		args = self.reqparse.parse_args()

		if user_able(args['key']):
			recipes = models.Recipe.query.whoosh_search(args['name']).all()
			print(recipes)

			rv = []

			for r in recipes:
				rv.append(json_recipe(r))

			return(rv)
		else:
			abort(403)

api.add_resource(RecipeAPI, '/api/v1/recipes/<int:id>')	
api.add_resource(RecipeTitleAPI, '/api/v1/recipes/')
api.add_resource(IngredientAPI, '/api/v1/ingredients')