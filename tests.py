import os
import json

from config import basedir
from app import app, db, models, user_datastore
from app.models import *

from flask.ext.security import current_user
from flask.ext.security.utils import login_user

import unittest
from flask.ext.testing import TestCase

f = open('data/recipe.clean.json').read()
data = json.loads(f)

def add_if_not_exist(item, which):
	if which == 'ingredients':
		if db.session.query(models.Ingredient).filter_by(name=item).count() < 1:
			i = models.Ingredient(name=item)
			db.session.add(i)
			return i
		else:
			return db.session.query(models.Ingredient).filter_by(name=item).first()

	if which == 'modifier':
		if db.session.query(models.Modifier).filter_by(name=item).count() < 1:
			m = models.Modifier(name=item)
			db.session.add(m)
			return m
		else:
			return db.session.query(models.Modifier).filter_by(name=item).first()

class DatabaseTestCase(TestCase):
	key = None
	data = None

	def create_app(self):
		app.config['TESTING']
		app.config['WTF_CSRF_ENABLED'] = False
		app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'test.db')
		return app

	def setUp(self):
		db.create_all()

		#Load in our test recipes.
		
		for d in data:
			title = d['title']
			directions = d['directions']

			ingredients = d['ingredients']

			step_number = 1;
			steps = ''

			mis = []

			for direction in directions:
				steps = steps + str(step_number) + ': ' + direction + "\n"
				step_number = step_number + 1

			for ingredient in ingredients:
				amount = ingredient['amount']
				modifiers = ingredient['modifiers']
				ing = ingredient['ingredient']

			i = add_if_not_exist(ing, 'ingredients')
			m = []

			for mod in modifiers:
				m.append(add_if_not_exist(mod, 'modifier'))

			amount = amount.split(' ')

			if(len(amount) > 2):
				m.append(add_if_not_exist(" ".join(amount[2:]), 'modifier'))

			if(len(amount) == 1):
				amount.append('')
		
			mi = models.ModifiedIngredient(amount=amount[0], unit=amount[1], ingredient=i.id, modifiers=m)
			db.session.add(mi)
			mis.append(mi)

	def tearDown(self):
		db.session.remove()
		db.drop_all()

	def test_retrieveRecipe(self):
		with app.app_context():
			request = self.client.get('/api/v1/recipes/1', data=dict(
			key=app.config.API_KEY))
			print(request.data)
			assert(False)
			assert(json.loads(str(request.data)) == data[0])

	# def test_singleIngredient(self):
	# 	assert(False)

	# def test_twoIngredients(self):
	# 	assert(False)

	# def test_oneWithOneWithout(self):
	# 	assert(False)


if __name__ == '__main__':
	unittest.main()