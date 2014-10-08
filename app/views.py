from app import app, db, models, user_datastore

from flask import request, render_template

import json
import requests

from flask.ext.security import user_registered, login_required, current_user

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/pricing')
def pricing():
	return render_template('pricing.html')

@app.route('/howto')
def how_to_use():
	return render_template('howto.html')

@app.route('/user')
@login_required
def user():
	email = current_user.email
	key = current_user.key
	free = current_user.free_credits
	paid = current_user.credits
	return render_template('user.html', email=email, key=key, free=free, paid=paid)

@user_registered.connect_via(app)
def user_reg(sender, user, **extra):
	print('User!')
	user.generate_key()

@app.route('/api/v1/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe():
	return 'Recipe Got'

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



@app.route('/api/v1/recipes/add', methods=['POST'])
def add_recipe():
	r = json.loads(request.form['recipe'])

	title = r['title']

	directions = r['directions']

	ingredients = r['ingredients']

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
		
		mi = models.ModifiedIngredient(amount=amount[0], unit=amount[1], ingredients=[i], modifiers=m)
		db.session.add(mi)
		mis.append(mi)

	recipe = models.Recipe(name=title, directions=steps, ingredients=mis)
	db.session.add(recipe)
	db.session.commit()
	return 'Woah'
