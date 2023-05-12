from flask import Flask

<<<<<<< HEAD
=======
from flask_bootstrap import Bootstrap
>>>>>>> 6c0e89db97f4816598271558c6e63692985f1fae
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

<<<<<<< HEAD
from config import WebappConfig

app = Flask(__name__)
app.config.from_object(WebappConfig)


db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login = LoginManager(app)
login.login_view = 'login'
login.login_message = 'You must login to access this page'
login.login_message_category = 'info'


from frontend.routes import *
=======

app = Flask(__name__)



import os
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///mydb.db'

db = SQLAlchemy(app)

bootstrap = Bootstrap(app)
bcrypt = Bcrypt(app)

# login = LoginManager(app)
# login.login_view = 'login'
# login.login_message = 'You must login to access this page'
# login.login_message_category = 'info'
login_manager = LoginManager(app)
login_manager=LoginManager(app)
login_manager.init_app(app)
login_manager.login_view="login"
login_manager.login_message = 'You must login to access this page'
login_manager.login_message_category = 'info'


with app.app_context():
    db.create_all()

app.app_context().push()

from frontend.routes import *
>>>>>>> 6c0e89db97f4816598271558c6e63692985f1fae
