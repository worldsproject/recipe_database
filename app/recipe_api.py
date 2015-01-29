from flask.ext.restful import Resource, reqparse
from flask import abort, redirect
from app import app, api, db, models

from sqlalchemy_searchable import parse_search_query
from sqlalchemy_utils.expressions import (
    tsvector_match, tsvector_concat, to_tsquery
)


def user_able(user_key):
	"""
	Checks if a given user (based on their api key) is able to use the API,
	(they have free or paid credits)
	If a key given is a master key (from the config) always returns true.
	"""
	if user_key == app.config['API_KEY']:
		return True

	user = db.session.query(models.User).filter(models.User.key == user_key)\
	                                    .first()

	if user.free_credits > 0:
		user.free_credits = user.free_credits - 1
		db.session.commit()
		return True

	if user.credits > 0:
		user.credits = user.credits - 1
		db.session.commit()
		return True

	return False

def json_recipe(recipe, admin=False):
	"""
	Given a recipe, turns it into a json string. If admin is true,
	returns the ingredient id and admin key as well.
	"""
	returned_json = {}

	returned_json['name'] = recipe.name
	returned_json['directions'] = recipe.directions
	returned_json['description'] = recipe.description
	returned_json['prep_time'] = recipe.prep_time
	returned_json['cook_time'] = recipe.cook_time
	returned_json['image'] = recipe.image
	returned_json['id'] = recipe.id
	returned_json['origin'] = recipe.credit
	i = []

	for ing in recipe.ingredients:
		ings = {}

		ings['original'] = ing.original
		ings['name'] = db.session.query(models.Ingredient_Name) \
		                 .filter(models.Ingredient_Name.id == ing.name) \
		                 .first().name
		ings['unit'] = ing.unit
		ings['amount'] = ing.amount
		ings['modifiers'] = ing.modifiers
		if admin:
			ings['id'] = ing.id

		i.append(ings)

	returned_json['ingredients'] = i

	if admin:
		returned_json['key'] = app.config['API_KEY']

	return returned_json

def get_unknown():
	""" Gets the placeholder ingredient name """
	unknown = db.session.query(models.Ingredient_Name) \
	            .filter(models.Ingredient_Name.name == 'unknown')

	if unknown.count() < 1:
		ingn = models.Ingredient_Name(name='unknown')
		db.session.add(ingn)
		db.session.commit()

		return ingn.id
	else:
		return unknown.first().id

def add_ingredient_name(name):
	""" Adds a given name to ingredient_name if it does not exist.
	If given an empty string, returns the unknown name.
	"""
	if len(name) < 1:
		return get_unknown()

	name = name.lower()

	ing = db.session.query(models.Ingredient_Name) \
	        .filter(models.Ingredient_Name.name == name)

	if ing.count() < 1:
		new_ing = models.Ingredient_Name(name=name)
		db.session.add(new_ing)
		db.session.commit()
		return new_ing.id
	else:
		return ing.first().id


def get_recipe(recipe_id):
	"""
	Gets the recipe by given id.
	"""
	return db.session.query(models.Recipe) \
	         .filter(models.Recipe.id == recipe_id).first()


def is_admin(key):
	""" Allows admin access. If the key does not match, will immediatly abort.
	Otherwise nothing happens and can continue as if you have admin priv.
	"""
	if key != app.config['API_KEY']:
		abort(403)


class IngredientAPI(Resource):
	""" Returns a list of recipes
	that either have or do not have the given ingredients.
	"""
	def __init__(self):
		self.reqparse = reqparse.RequestParser()
		self.reqparse.add_argument('with', type=str, \
			help='Ingredients that you require in your recipe.', action='append')
		self.reqparse.add_argument('without', type=str, \
			help='Ingredients that cannot be in your recipe.', action='append')
		self.reqparse.add_argument('key', required=True, type=str, \
			help="Your API key is required.")

	def post(self):
		""" POST access to searching for recipes by their ingredients. """
		args = self.reqparse.parse_args()

		if user_able(args['key']):
			recipes = None

			if args['with'] == None:
				args['with'] = []

			if args['without'] == None:
				args['without'] = []

			for ing in args['with']:
				query = db.session.query(models.Recipe) \
				          .join(models.Ingredient, models.Recipe.ingredients) \
				          .join(models.Ingredient_Name) \
				          .filter(models.Ingredient_Name.name == ing)
				recipes = query

			for ing in args['without']:
				query = db.session.query(models.Recipe) \
				          .join(models.Ingredient, models.Recipe.ingredients) \
				          .join(models.Ingredient_Name) \
				          .filter(models.Ingredient_Name.name == ing)

				if recipes != None:
					recipes = recipes.except_(query)
				else:
					recipes = query

			returned_recipes = []

			for recipe in recipes:
				returned_recipes.append(json_recipe(recipe))

			return returned_recipes


class RecipeAPI(Resource):
	""" Gets a single recipe by its id.
	"""
	def __init__(self):
		self.reqparse = reqparse.RequestParser()
		self.reqparse.add_argument('key', type=str, \
			                       required=True, help='Your API Key is required.')

	def get(self, recipe_id):
		""" Get access for accessing a single recipe by its id. """
		args = self.reqparse.parse_args()
		if user_able(args['key']):
			recipe = get_recipe(recipe_id)

			return json_recipe(recipe)
		else:
			abort(403)

class RecipeTitleAPI(Resource):
	""" Allows full text search of recipes.
	"""
	def __init__(self):
		self.reqparse = reqparse.RequestParser()
		self.reqparse.add_argument('key', type=str, \
			                       required=True, help='Your API Key is required.')
		self.reqparse.add_argument('name', type=str, \
			                       required=True, help='Your search terms are required.')

	def post(self):
		""" POST access for full-text search of recipes. """
		args = self.reqparse.parse_args()

		if user_able(args['key']):
			combined_search_vector = tsvector_concat( \
				models.Recipe.search_vector, \
				models.Ingredient.search_vector \
			)

			recipes = ( \
				db.session.query(models.Recipe) \
				.join(models.Ingredient, models.Recipe.ingredients) \
				.filter( \
					tsvector_match( \
						combined_search_vector, \
						to_tsquery( \
							'simple', \
							parse_search_query(args['name']) \
						), \
					) \
				) \
			)

			returned_recipes = []

			for recipe in recipes:
				returned_recipes.append(json_recipe(recipe))

			return returned_recipes
		else:
			abort(403)

class RecipeAddAPI(Resource):
	""" Adds a recipe to the database. As of right now, only allows admin
	to add recipes.
	"""
	def __init__(self):
		self.reqparse = reqparse.RequestParser()
		self.reqparse.add_argument('name', type=str, required=True)
		self.reqparse.add_argument('description', type=str)
		self.reqparse.add_argument('directions', type=str, \
			                       action='append', required=True)
		self.reqparse.add_argument('prep_time', type=str)
		self.reqparse.add_argument('cook_time', type=str)
		self.reqparse.add_argument('image', type=str)
		self.reqparse.add_argument('ingredient', \
			                       type=str, \
			                       action='append', \
			                       required=True)
		self.reqparse.add_argument('key', type=str, required=True)
		self.reqparse.add_argument('credit', type=str, required=True)

	def post(self):
		""" POST access for adding a recipe. """
		args = self.reqparse.parse_args()

		is_admin(args['key'])

		recipe = models.Recipe( \
			name=args['name'], \
			description=args['description'], \
			prep_time=args['prep_time'], \
			cook_time=args['cook_time'], \
			image=args['image'], \
			credit=args['credit'])

		db.session.add(recipe)

		directions = ''
		if args['directions'] is not None:
			for direction in args['directions']:
				directions = directions + '|' + direction

		recipe.directions = directions

		for i in args['ingredient']:
			#ingredients are given in the form
			#original/\amount/\unit/\name/\modifiers
			#with modifiers being optional

			ing = i.split('/\\')
			if len(ing) != 4 and len(ing) != 5:
				return i, 403

			ingredient = None
			if len(ing) == 4:
				ingredient_name = add_ingredient_name(ing[3])
				ingredient = models.Ingredient( \
					original=ing[0], \
					amount=ing[1], \
					unit=ing[2], \
					name=ingredient_name)

			if len(ing) == 5:
				ingredient_name = add_ingredient_name(ing[3])
				ingredient = models.Ingredient( \
					original=ing[0], \
					amount=ing[1], \
					unit=ing[2], \
					name=ingredient_name, \
					modifiers=ing[4])

			db.session.add(ingredient)
			recipe.ingredients.append(ingredient)

		db.session.commit()
		return "Recipe Added", 201

class ResetFree(Resource):
	""" Resets free credits. Admin access only.
	"""
	def __init__(self):
		self.reqparse = reqparse.RequestParser()
		self.reqparse.add_argument('key', type=str, required=True)

	def get(self):
		""" GET access for resetting free credits. """
		args = self.reqparse.parse_args()

		is_admin(args['key'])

		users = db.session.query(models.User)

		for user in users:
			user.free_credits = 100

		db.session.commit()

		return "Free Credits Reset", 201


class ReportError(Resource):
	""" Allows people to report erronious recipes.
	Does not consume API usage.
	"""
	def __init__(self):
		self.reqparse = reqparse.RequestParser()
		self.reqparse.add_argument('id', type=str, required=True)
		self.reqparse.add_argument('reason', type=str)

	def post(self):
		""" POST access for reporting errors in recipes. """
		args = self.reqparse.parse_args()

		body = "Recipe ID: " + args['id']

		if args['reason'] != None:
			body = body + "\nReason for being incorrect: " + args['reason']

		app.logger.error(body)

		return "Bad Recipe Reported", 200

class AddIngredientToRecipe(Resource):
	""" Adds an ingredient to a recipe. Reuses ingredient names,
	if possible, but will create a new ingredient.
	"""
	def __init__(self):
		self.reqparse = reqparse.RequestParser()
		self.reqparse.add_argument('key', type=str, required=True)
		self.reqparse.add_argument('name', type=str, required=True)
		self.reqparse.add_argument('unit', type=str, required=True)
		self.reqparse.add_argument('amount', type=float, required=True)
		self.reqparse.add_argument('recipe_id', type=int, required=True)
		self.reqparse.add_argument('modifiers', type=str)

	def post(self):
		""" POST access for adding an ingredient to a recipe. """
		args = self.reqparse.parse_args()

		is_admin(args['key'])

		name = add_ingredient_name(args['name'])
		ingredient = models.Ingredient( \
			original='Added and Edited from original recipe.', \
			amount=args['amount'], \
			unit=args['unit'], \
			name=name, \
			modifiers=args['modifiers'])

		recipe = get_recipe(args['recipe_id'])
		recipe.ingredients.append(ingredient)

		db.session.commit()

		return redirect('/recipe_edit/' + str(args['recipe_id']))

class DeleteIngredientFromRecipe(Resource):
	""" Removes an ingreidnet from a recipe. Only removes the link to
	the recipe, but does not delete the ingredient from the database.
	"""
	def __init__(self):
		self.reqparse = reqparse.RequestParser()
		self.reqparse.add_argument('key', type=str, required=True)
		self.reqparse.add_argument('recipe_id', type=str, required=True)
		self.reqparse.add_argument('ingredient_id', type=str, required=True)

	def post(self):
		""" POST access for removing ingredients from a recipe. """

		args = self.reqparse.parse_args()

		is_admin(args['key'])

		recipe = get_recipe(args['recipe_id'])
		ingredient = db.session.query(models.Ingredient) \
		.filter(models.Ingredient.id == args['ingredient_id']).first()
		recipe.ingredients.remove(ingredient)
		db.session.commit()

		return redirect('/recipe_edit/' + args['recipe_id'])

class EditRecipe(Resource):
	"""
	Allows editing of the entire recipe except ingredients.
	Ingredients are treated seperatly.
	"""
	def __init__(self):
		self.reqparse = reqparse.RequestParser()
		self.reqparse.add_argument('name', type=str, required=True)
		self.reqparse.add_argument('directions', type=str, required=True)
		self.reqparse.add_argument('recipe_id', type=int, required=True)
		self.reqparse.add_argument('key', type=str, required=True)
		self.reqparse.add_argument('prep_time', type=str, required=True)
		self.reqparse.add_argument('cook_time', type=str, required=True)
		self.reqparse.add_argument('image_url', type=str, required=True)
		self.reqparse.add_argument('origin', type=str, required=True)

	def post(self):
		""" POST access to edit the recipe. """
		args = self.reqparse.parse_args()

		is_admin(args['key'])

		recipe = get_recipe(args['recipe_id'])
		recipe.name = args['name']
		recipe.directions = args['directions']
		recipe.prep_time = args['prep_time']
		recipe.cook_time = args['cook_time']
		recipe.image_url = args['image_url']
		recipe.origin = args['origin']
		db.session.commit()

		return redirect('/recipe_edit/' + str(args['recipe_id']))


class EditMealTime(Resource):
	"""
	This is the API access the edits what time of day (breakfast, lunch, etc)
	that the meal is typically eaten.
	"""
	def __init__(self):
		self.reqparse = reqparse.RequestParser()
		self.reqparse.add_argument('key', type=str, required=True)
		self.reqparse.add_argument('id', type=int, required=True)
		self.reqparse.add_argument('meal', type=int, required=True)

	def post(self):
		""" POST access to edit the meal. """

		args = self.reqparse.parse_args()

		is_admin(args['key'])

		recipe = get_recipe(args['id'])
		recipe.meal = args['meal']

		return 200

def get_meal_page(time, page):
	db.session.query(models.Recipe) \
			.filter(models.Recipe.meal == time) \
			.slice(page*10, page*10+10)

class MealTimeAPI(Resource):
	"""
	This API allows getting recipes by their associated meal time.
	The only permitted values for the meal keyword are:
	morning, afternoon, side, dessert or drink. All other values will
	result in returning a 404.

	T
	"""

	def __init__(self):
		self.reqparse = reqparse.RequestParser()
		self.reqparse.add_argument('key', type=str, required=True)
		self.reqparse.add_argument('meal', type=str, required=True)
		self.reqparse.add_argument('page', type=int)

	def post(self):
		""" POST access for searching by meal time. """
		args = self.reqparse.parse_args()

		meal = args['meal']

		if args['page'] is None:
			args['page'] = 0

		if meal == 'morning':
			recipes = get_meal_page(models.morning, args['page'])
		elif meal == 'afternoon':
			recipes = get_meal_page(models.afternoon, args['page'])
		elif meal == 'side':
			recipes = get_meal_page(models.side, args['page'])
		elif meal == 'dessert':
			recipes = get_meal_page(models.dessert, args['page'])
		elif meal == 'drink':
			recipes = get_meal_page(models.drink, args['page'])
		else:
			abort(404)

		returned = []
		for recipe in recipes
			returned.append(json_recipe(recipe))

		return returned




api.add_resource(RecipeAPI, '/api/v1/recipes/<int:recipe_id>')
api.add_resource(RecipeTitleAPI, '/api/v1/recipes/')
api.add_resource(IngredientAPI, '/api/v1/ingredients')
api.add_resource(RecipeAddAPI, '/api/v1/add')
api.add_resource(ResetFree, '/api/v1/reset')
api.add_resource(ReportError, '/api/v1/report_error')
api.add_resource(MealTimeAPI, '/api/v1/by_meal/')
api.add_resource(IngredientListAPI, '/api/v1/ingredient/<string:name>')

#APIs for editing recipes.
api.add_resource(AddIngredientToRecipe, '/api/v1/recipe_edit/add_ingredient')
api.add_resource(DeleteIngredientFromRecipe,\
	'/api/v1/recipe_edit/delete_ingredient')
api.add_resource(EditRecipe, '/api/v1/recipe_edit/edit_recipe')
api.add_resource(EditMealTime, '/api/v1/recipe_edit/edit_meal_time')
