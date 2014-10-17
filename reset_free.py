from app import db, models
from sqlalchemy import update

users = db.session.query(models.User)

for user in users:
	user.free_credits = 100

db.session.commit()