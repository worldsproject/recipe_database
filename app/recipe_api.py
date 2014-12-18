from flask.ext.restful import Resource, reqparse
from flask import jsonify, abort
from app import app, api, db, models
from sqlalchemy import update

from sqlalchemy_searchable import parse_search_query
from sqlalchemy_utils.expressions import (
    tsvector_match, tsvector_concat, to_tsquery
)


def user_able(user_key):
	if user_key == app.config['API_KEY']:
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

def json_recipe(recipe, admin=False):
	rv = {}

	rv['name'] = recipe.name
	rv['directions'] = recipe.directions
	rv['description'] = recipe.description
	rv['prep_time'] = recipe.prep_time
	rv['cook_time'] = recipe.cook_time
	rv['image'] = recipe.image
	rv['id'] = recipe.id
	rv['origin'] = recipe.credit
	i = []

	for ing in recipe.ingredients:
		ings = {}

		ings['original'] = ing.original
		ings['name'] = db.session.query(models.Ingredient_Name).filter(models.Ingredient_Name.id == ing.name).first().name
		ings['unit'] = ing.unit
		ings['amount'] = ing.amount
		ings['modifiers'] = ing.modifiers
		if admin:
			ings['id'] = ing.id

		i.append(ings)

	rv['ingredients'] = i

	return rv

def get_unknown():
	unknown = db.session.query(models.Ingredient_Name).filter(models.Ingredient_Name.name == 'unknown')

	if unknown.count() < 1:
		ingn = models.Ingredient_Name(name='unknown')
		db.session.add(ingn)
		db.session.commit()

		return ingn.id
	else:
		return unknown.first().id

def add_ingredient_name(name, unknown_id):
	if len(name) < 1:
		return unknown_id

	name = name.lower()

	ing = db.session.query(models.Ingredient_Name).filter(models.Ingredient_Name.name == name)

	if ing.count() < 1:
		new_ing = models.Ingredient_Name(name=name)
		db.session.add(new_ing)
		db.session.commit()
		return new_ing.id
	else:
		return ing.first().id

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

			if args['with'] == None:
				args['with'] = []

			if args['without'] == None:
				args['without'] = []

			for ing in args['with']:
				q = db.session.query(models.Recipe).join(models.Ingredient, models.Recipe.ingredients).join(models.Ingredient_Name).filter(models.Ingredient_Name.name == ing)
				t = q
				print('With: ' + str(q.count()))

			for ing in args['without']:
				q = db.session.query(models.Recipe).join(models.Ingredient, models.Recipe.ingredients).join(models.Ingredient_Name).filter(models.Ingredient_Name.name == ing)
				print('Without: ' + str(q.count()))
				if t != None:
					t = t.except_(q)
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
			combined_search_vector = tsvector_concat(
				models.Recipe.search_vector,
				models.Ingredient.search_vector
			)

			recipes = (
				db.session.query(models.Recipe)
				.join(models.Ingredient, models.Recipe.ingredients)
				.filter(
					tsvector_match(
						combined_search_vector,
						to_tsquery(
							'simple',
							parse_search_query(args['name'])
						),
					)
				)
			)

			rv = []

			for r in recipes:
				rv.append(json_recipe(r))

			return(rv)
		else:
			abort(403)

class RecipeAddAPI(Resource):
	def __init__(self):
		self.reqparse = reqparse.RequestParser()
		self.reqparse.add_argument('name', type=str, required=True)
		self.reqparse.add_argument('description', type=str)
		self.reqparse.add_argument('directions', type=str, action='append', required=True)
		self.reqparse.add_argument('prep_time', type=str)
		self.reqparse.add_argument('cook_time', type=str)
		self.reqparse.add_argument('image', type=str)
		self.reqparse.add_argument('ingredient', type=str, action='append', required=True)
		self.reqparse.add_argument('key', type=str, required=True)
		self.reqparse.add_argument('credit', type=str, required=True)

	def post(self):
		args = self.reqparse.parse_args()

		if args['key'] != app.config['API_KEY']:
			abort(403)

		unknown_id = get_unknown()

		recipe = models.Recipe(
			name = args['name'],
			description = args['description'],
			prep_time = args['prep_time'],
			cook_time = args['cook_time'],
			image = args['image'],
			credit = args['credit'])

		db.session.add(recipe)

		dirs = ''
		if args['directions'] is not None:
			for d in args['directions']:
				dirs = dirs + '|' + d

		recipe.directions = dirs

		for i in args['ingredient']:
			#ingredients are given in the form original/\amount/\unit/\name/\modifiers with
			#modifiers being optional

			ing = i.split('/\\')
			if len(ing) != 4 and len(ing) != 5:
				return i, 403

			ingredient = None
			if len(ing) == 4:
				n = add_ingredient_name(ing[3], unknown_id)
				ingredient = models.Ingredient(
					original = ing[0],
					amount = ing[1],
					unit = ing[2],
					name = n)

			if len(ing) == 5:
				n =add_ingredient_name(ing[3], unknown_id)
				ingredient = models.Ingredient(
					original = ing[0],
					amount = ing[1],
					unit = ing[2],
					name = n,
					modifiers = ing[4])

			db.session.add(ingredient)
			recipe.ingredients.append(ingredient)

		db.session.commit()
		return "Recipe Added", 201

class ResetFree(Resource):
	def __init__(self):
		self.reqparse.add_argument('key', type=str, required=True)

	def get(self):
		args = self.reqparse.parse_args()

		if args['key'] == app.config['API_KEY']:
			users = db.session.query(models.User)

			for user in users:
				user.free_credits = 100

			db.session.commit()

			return "Free Credits Reset", 201
		else:
			return 403


class ReportError(Resource):
	def __init__(self):
		self.reqparse = reqparse.RequestParser()
		self.reqparse.add_argument('id', type=str, required=True)
		self.reqparse.add_argument('reason', type=str)

	def post(self):
		args = self.reqparse.parse_args()

		body = "Recipe ID: " + args['id']

		if args['reason'] != None:
			body = body + "\nReason for being incorrect: " + args['reason']

		app.logger.error(body)

		return "Bad Recipe Reported", 200

api.add_resource(RecipeAPI, '/api/v1/recipes/<int:id>')
api.add_resource(RecipeTitleAPI, '/api/v1/recipes/')
api.add_resource(IngredientAPI, '/api/v1/ingredients')
api.add_resource(RecipeAddAPI, '/api/v1/add')
api.add_resource(ResetFree, '/api/v1/reset')
api.add_resource(ReportError, '/api/v1/report_error')
