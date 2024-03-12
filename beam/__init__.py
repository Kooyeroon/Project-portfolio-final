import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

app = Flask(__name__)
app.config['SECRET_KEY'] = '522006c50113414fb6ced20412eb5a4f'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///beam.db'
#postgres://forbeamcalculator_user:o2x9V0FZTGaWYGffQLOUwAw38cFCGvwv@dpg-cno0ppfsc6pc73banv7g-a.oregon-postgres.render.com/forbeamcalculator
db = SQLAlchemy(app)
app.app_context().push()

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from beam import routes
