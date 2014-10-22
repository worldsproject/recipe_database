from app import app, db, models, user_datastore, recipe_api, api
from sqlalchemy import or_
from flask import request, render_template, url_for, redirect, flash, abort

import json
import requests

import stripe

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

@app.route('/test')
def test():
	r1 = db.session.query(models.Recipe).join(models.ModifiedIngredient, models.Recipe.ingredients).join(models.Ingredient).filter(models.Ingredient.name == 'garlic')
	r2 = db.session.query(models.Recipe).join(models.ModifiedIngredient, models.Recipe.ingredients).join(models.Ingredient).filter(models.Ingredient.name == 'black beans')
	r3 = r1.intersect(r2)
	print(r3.count())

	s = ''

	for x in r3:
		s = s + x.name + '<br>'

	return s

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
	user.generate_key()

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

@app.route('/credit', methods=['POST'])
def credit():
	stripe.api_key = app.config['TEST_PRIVATE_TOKEN']
	token = request.form['stripeToken']
	amount = request.form['price']
	email = request.form['stripeEmail']

	if amount == '5':
		amount = 500
	elif amount == '10':
		amount = 1000
	elif amount == '20':
		amount = 2000
	else:
		return abort(503)

	customer = stripe.Customer.create(
		email = email,
		card = token)

	charge = stripe.Charge.create(
		customer = customer.id,
		amount = amount,
		currency = 'usd',
		description = 'Buying ' + str(amount) + '0 API credits.')

	if current_user.credits is None:
		current_user.credits = (amount*10)
	else:
		current_user.credits = current_user.credits + (amount*10)
	db.session.commit()

	flash(str(amount) + " credits have been added.")
	return redirect(url_for('user'))

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
		
		mi = models.ModifiedIngredient(amount=amount[0], unit=amount[1], ingredient=i.id, modifiers=m)
		db.session.add(mi)
		mis.append(mi)

	recipe = models.Recipe(name=title, directions=steps, ingredients=mis)
	db.session.add(recipe)
	db.session.commit()
	return 'Woah'
