from flask_login import UserMixin
from datetime import datetime

from frontend import db, login


@login.user_loader
def load_user(user_id):
    return User.query.filter_by(userID=user_id).first()


class User(db.Model, UserMixin):
    userID = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
<<<<<<< HEAD
    lastname = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
=======
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)
>>>>>>> 6c0e89db97f4816598271558c6e63692985f1fae

    def __repr__(self):
        return '<User %r>' % self.username

    def get_id(self):
        return self.userID

<<<<<<< HEAD

class Query(db.Model, UserMixin):
    queryID = db.Column(db.Integer, primary_key=True)
    query_count = db.Column(db.Integer, nullable=False)
    userID = db.Column(db.Integer, nullable=False)
    query_time = db.Column(db.DateTime, default=datetime.utcnow)
    query_text = db.Column(db.String(200))
    query_duration = db.Column(db.Integer, nullable=False)
    query_difficulty = db.Column(db.Integer)
    query_free_option = db.Column(db.Integer, nullable=False)


=======
>>>>>>> 6c0e89db97f4816598271558c6e63692985f1fae
class Course(db.Model):
    courseID = db.Column(db.Integer, primary_key=True, nullable=False)
    title = db.Column(db.Text, nullable=False)
    url = db.Column(db.Text, nullable=False)
    categories = db.Column(db.Text, nullable=False)
<<<<<<< HEAD
    description_short = db.Column(db.Text, nullable=False)
    description_long = db.Column(db.Text, nullable=False)
=======
    description_short = db.Column(db.Text,nullable=False)
    description_long = db.Column(db.Text,nullable=False)
>>>>>>> 6c0e89db97f4816598271558c6e63692985f1fae
    difficulty = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    free_option = db.Column(db.Integer, nullable=False)
    number_of_enroll = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    paid_option = db.Column(db.Text, nullable=False)
    language = db.Column(db.Text, nullable=False)
    subtitle = db.Column(db.Text, nullable=False)
    platform = db.Column(db.Integer, nullable=False)
    provider = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.Text, nullable=False)
    popularity_index = db.Column(db.Float, nullable=False)
<<<<<<< HEAD

=======
    keyword = db.Column(db.Text,nullable=False)
>>>>>>> 6c0e89db97f4816598271558c6e63692985f1fae

class Favourite(db.Model):
    userID = db.Column(db.Integer, primary_key=True)
    courseID = db.Column(db.Integer, primary_key=True, nullable=False)

<<<<<<< HEAD

=======
>>>>>>> 6c0e89db97f4816598271558c6e63692985f1fae
class Recommendation(db.Model):
    userID = db.Column(db.Integer, primary_key=True)
    query_count = db.Column(db.Integer, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    courseID = db.Column(db.Integer, primary_key=True, nullable=False)

<<<<<<< HEAD

if __name__ == '__main__':
    db.create_all()
    
=======
class Query(db.Model, UserMixin):
    queryID = db.Column(db.Integer, primary_key=True)
    query_count = db.Column(db.Integer, nullable=False)
    userID = db.Column(db.Integer, nullable=False)
    query_time = db.Column(db.DateTime, default=datetime.utcnow)
    query_text = db.Column(db.String(200))
    query_duration = db.Column(db.Integer, nullable=False)
    query_difficulty = db.Column(db.Integer)
    query_free_option = db.Column(db.Integer, nullable=False)

class skill(db.Model):
    userID = db.Column(db.Integer, primary_key=True)
    skill=db.Column(db.Text)

class career_path(db.Model, UserMixin):
    userID = db.Column(db.Integer, primary_key=True)
    career=db.Column(db.Text,nullable=False)
>>>>>>> 6c0e89db97f4816598271558c6e63692985f1fae
