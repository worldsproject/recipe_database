from flask.ext.restful import Resource, reqparse
from flask import jsonify
from app import api, db, models

def user_able(user_key):
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
		ings['name'] = db.session.query(models.Ingredient).filter(models.Ingredient.id == ing.ingredient).first().name
		ings['unit'] = ing.unit
		ings['amount'] = ing.amount
		m = []

		for x in ing.modifiers:
			m.append(x.name)

		ings['modifiers'] = m
		i.append(ings)

	rv['ingredients'] = i

	return rv


class IngredientAPI(Resource):
	def get(self):
		pass

	def post(self):
		pass

class RecipeAPI(Resource):
	def __init__(self):
		self.reqparse = reqparse.RequestParser()
		self.reqparse.add_argument('key', type=str, help='Your API Key is required.')

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
		self.reqparse.add_argument('key', type=str, help='Your API Key is required.')
		self.reqparse.add_argument('name', type=str, help='Your search terms are required.')

	def post(self):
		args = self.reqparse.parse_args()

		if user_able(args['key']):
			recipes = db.session.query(models.Recipe).filter(models.Recipe.name.like("%" + args['name'] + "%")).all()

			rv = []

			for r in recipes:
				rv.append(json_recipe(r))
		else:
			abort(403)

api.add_resource(RecipeAPI, '/api/v1/recipes/<int:id>')	
api.add_resource(RecipeTitleAPI, '/api/v1/recipes/')
api.add_resource(IngredientAPI, '/api/v1/ingredients')