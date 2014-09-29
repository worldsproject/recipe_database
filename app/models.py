class Recipe(db.Model):
	__tablename__ = 'recipe'

	id = db.Column(db.Integer, primary_key=True)

	name = db.Column(db.String(30))
	description = db.Column(db.Text)
	prep_time = db.Column(db.Integer)
	cook_time = db.Column(db.Integer)
	image = db.Column(db.String(32))
	ingredients = db.relationship('ModifiedIngredient', backref='ingredients', lazy='dynamic')

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
	ingredient = db.Column(db.Integer, db.ForeignKey('ingredient.id'))
	modifier = db.Column(db.Integer, db.ForeignKey('modified_ingredient.id'))
	recipe = db.Column(db.Integer, db.ForeignKey('recipe.id'))