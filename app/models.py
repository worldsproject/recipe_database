import hashlib, time, random

from app import db, app
from flask.ext.security import UserMixin, RoleMixin


roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

ingredients = db.Table('ingredients',
    db.Column('recipe', db.Integer, db.ForeignKey('recipe.id')),
    db.Column('ingredient', db.Integer, db.ForeignKey('ingredient.id'))
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
    __searchable__ = ['name', 'description', 'directions']

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.Text)
    description = db.Column(db.Text)
    directions = db.Column(db.Text)
    prep_time = db.Column(db.String(15))
    cook_time = db.Column(db.String(15))
    image = db.Column(db.Text)
    ingredients = db.relationship('Ingredient', secondary=ingredients)
    credit = db.Column(db.String)

class Ingredient(db.Model):
    __tablename__ = 'ingredient'
    __searchable__ = ['name', 'modifiers', 'original']

    id = db.Column(db.Integer, primary_key=True)
    original = db.Column(db.Text)
    name = db.Column(db.Text, index=True)
    amount = db.Column(db.String(10))
    unit = db.Column(db.String(20))
    modifiers = db.Column(db.Text)
