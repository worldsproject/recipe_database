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

@app.route('/recipe_edit/<int:recipe_id>')
@admin_permission.require()
def edit_recipe(recipe_id):
	recipe = db.session.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
	from app.recipe_api import json_recipe

	return render_template('edit_recipe.html', recipe=json_recipe(recipe, admin=True))

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