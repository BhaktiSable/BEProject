from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, RadioField, SelectMultipleField, FieldList, \
    validators, SelectField,EmailField
from wtforms.validators import DataRequired, Length, ValidationError,EqualTo
from frontend.models import User,Course
import email_validator
class SignupForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=1, max=200)])
    email=EmailField('Email',validators=[DataRequired(),validators.Email()])
    username = StringField('Username', validators=[DataRequired(), Length(min=6, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=20)])
    confirmpassword=PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Signup')

    def validate_username(self,username):
        existing_user_username=User.query.filter_by(username=username.data).first()
        return existing_user_username

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=6, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=20)])
    remember = BooleanField('Remember me')
    submit = SubmitField('Login')

class SurveyForm(FlaskForm):
    topic = StringField('What would you like to learn?', validators=[DataRequired(), Length(min=0, max=200)])
    duration = RadioField('Duration*', choices=[(0, 'No preference'), (1, 'Short (1 - 10 hours)'),
                                                (2, 'Medium (10 - 50 hours)'), (3, 'Long (>50 hours)')])
    difficulty = RadioField('Difficulty level*', choices=[(0, 'Any'), (1, 'Beginner'), (2, 'Intermediate'),
                                                          (3, 'Advanced')])
    freePaid = RadioField('Would you be open to paid courses?*',
                          choices=[(0, 'Yes. Show me both paid and free courses'),
                                   (1, 'No. Show me free courses only')], coerce=str)
    recommend = SubmitField('Get courses')

class CareerInterstForm(FlaskForm):
    topic = SelectField('What is your career interests?', choices=[('Data Analyst', 'Data Analyst'), ('Data Scientist', 'Data Scientist'),('Software Developer', 'Software Developer'),('Full Stack Developer','Full Stack Developer'),('Web Developer','Web Developer'),('Cloud Solutions Architect','Cloud Solutions Architect'),('Cybersecurity Analyst','Cybersecurity Analyst'),('Network Administrator','Network Administrator'),('Network Architect','Network Architect'),('Database Administrator','Database Administrator'),('DevOps Engineer','DevOps Engineer'),('Systems Analyst','Systems Analyst'),('Game Developer','Game Developer'),('UI/UX Designer','UI/UX Designer'),('IT Manager','IT Manager')])
    duration = RadioField('Duration*', choices=[(0, 'No preference'), (1, 'Short (1 - 10 hours)'),
                                                (2, 'Medium (10 - 50 hours)'), (3, 'Long (>50 hours)')])
    difficulty = RadioField('Difficulty level*', choices=[(0, 'Any'), (1, 'Beginner'), (2, 'Intermediate'),
                                                          (3, 'Advanced')])
    freePaid = RadioField('Would you be open to paid courses?*',
                          choices=[(0, 'Yes. Show me both paid and free courses'),
                                   (1, 'No. Show me free courses only')], coerce=str)
    recommend = SubmitField('Get courses')