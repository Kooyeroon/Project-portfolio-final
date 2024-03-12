from beam import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    loads = db.relationship('LoadsBeam', backref='user', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class LoadsBeam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.Float, nullable=False)
    shear_force = db.Column(db.Float, nullable=False)
    bending_moment= db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
            return f"LoadsBeam('{self.position}', '{self.shear_force}', '{self.bending_moment}', '{self.user}')"