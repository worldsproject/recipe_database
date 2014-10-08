import hashlib, time, random

from app import db
from flask.ext.security import UserMixin, RoleMixin


roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

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

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))
    
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
 
    email = db.Column(db.String(120), index=True, unique=True)
    free_credits = db.Column(db.Integer, default=100)
    credits = db.Column(db.Integer)
    key = db.Column(db.String(32))

    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    def generate_key(self):
        m = hashlib.md5()
        m.update(self.email.encode('utf-8'))
        m.update(str(time.time()).encode('utf-8'))
        m.update(str(random.random()).encode('utf-8'))
        self.key = m.hexdigest()

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

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