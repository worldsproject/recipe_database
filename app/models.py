from app import db

ingredients = db.Table('ingredients',
	db.Column('modified_ingredient', db.Integer, db.ForeignKey('modified_ingredient.id')),
	db.Column('ingredient', db.Integer, db.ForeignKey('ingredient.id'))
	)

modifiers = db.Table('modifiers',
	db.Column('modified_ingredient', db.Integer, db.ForeignKey('modified_ingredient.id')),
	db.Column('modifier', db.Integer, db.ForeignKey('modifier.id'))
	)

modified_ingredients = db.Table('modified_ingredients',
	db.Column('recipe', db.Integer, db.ForeignKey('recipe.id')),
	db.Column('modified_ingredient', db.Integer, db.ForeignKey('modified_ingredient.id'))
	)

class Recipe(db.Model):
	__tablename__ = 'recipe'

	id = db.Column(db.Integer, primary_key=True)

	name = db.Column(db.String(256))
	description = db.Column(db.Text)
	directions = db.Column(db.Text)
	prep_time = db.Column(db.Integer)
	cook_time = db.Column(db.Integer)
	image = db.Column(db.LargeBinary())
	ingredients = db.relationship('ModifiedIngredient', secondary=modified_ingredients)

class Ingredient(db.Model):
	__tablename__ = 'ingredient'

	id = db.Column(db.Integer, primary_key=True)

	name = db.Column(db.String(30), index=True, unique=True)

class Modifier(db.Model):
	__tablename__ = 'modifier'

	id = db.Column(db.Integer, primary_key=True)

	name = db.Column(db.String(30), index=True, unique=True)

class ModifiedIngredient(db.Model):
	__tablename__ = 'modified_ingredient'

	id = db.Column(db.Integer, primary_key=True)

	amount = db.Column(db.Integer)
	unit = db.Column(db.String(20))
	ingredients = db.relationship('Ingredient', secondary=ingredients, 
		backref=db.backref('ingredients', lazy='dynamic'), lazy='dynamic')
	modifiers = db.relationship('Modifier', secondary=modifiers,
		backref=db.backref('modifiers', lazy='dynamic'), lazy='dynamic')