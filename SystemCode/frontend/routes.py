from flask import render_template, session,url_for,redirect,flash,request
from frontend import app
from frontend.forms import SignupForm, LoginForm,SurveyForm,CareerInterstForm
from flask_login import login_user, login_required, current_user, logout_user
from frontend.models import User, Query, Course, Favourite, Recommendation
from frontend import bcrypt, db
from frontend.models import User,Course
# from Recommendation import recommend
from Recommendation.recommend import recommend_default
from Recommendation.recommend import recommend
from Recommendation.recommend import load_pickle,tfidf_vectorizer_filepath,tfidf_data_filepath,categorical_data_filepath
import pytz
import numpy as np
import config
from Recommendation.recommend_job import recommend_job_role_based
# Initialize for Default 10 most popular courses
rating_tuples = db.session.query(Course.popularity_index).order_by(Course.courseID)
rating_data = np.array([x[0] for x in rating_tuples])
default_courses = recommend_default(rating_data)



# Initialized Data for Recommender Module
tfidf_vectorizer = load_pickle(tfidf_vectorizer_filepath)
tfidf_data = load_pickle(tfidf_data_filepath)
categorical_data = load_pickle(categorical_data_filepath)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
@login_required
def home():
    title = 'Course Recommender'
    if not current_user.is_authenticated:
        return redirect(url_for('/'))
    return render_template('home.html',title=title,home=True)
@app.route('/login', methods=['GET', 'POST'])
def login():
    title = 'Login'
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form=LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember = form.remember.data
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=remember)
            print(remember)
            flash('Login successful', category='success')
            if request.args.get('next'):
                next_page = request.args.get('next')
                return redirect(next_page)
            return redirect(url_for('home'))
        else:
            flash('User not exists or password not match', category='danger')
    return render_template('login.html',title=title,form=form,login=True)
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    title = 'Sign up'
    form = SignupForm()
    if form.validate_on_submit():
        name = form.name.data
        username = form.username.data
        password = bcrypt.generate_password_hash(form.password.data)
        user = User(name=name, username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Successfully registered!', category='success')
        return redirect(url_for('login'))
    return render_template('signup.html', title=title,form=form,signup=True)

@app.route('/query', methods=['GET', 'POST'])
@login_required
def query():

    # Check if user is signed in
    if not current_user.is_authenticated:
        return redirect(url_for('/'))
    # Initialization
    current_id = current_user.userID
    title = 'Personalized course recommendations'
    form = SurveyForm()

    # Validate form submission and update database based on query session
    if form.validate_on_submit():
        query_text = form.topic.data
        query_duration = form.duration.data
        query_difficulty = form.difficulty.data
        query_free_option = form.freePaid.data

        # Infer Recommendations
        query_input = [query_text, int(query_duration), int(query_difficulty), int(query_free_option)]
        query_courses = recommend(user_input=query_input, rating_data=rating_data,
                                  tfidf_vectorizer=tfidf_vectorizer, tfidf_data=tfidf_data,
                                  categorical_data=categorical_data)

        # Check if there is any courses recommended
        if len(query_courses) == 0:
            flash('There are no courses found, please try again', category='warning')
            return redirect(url_for('query'))
        # Update query session to Query database
        count = Query.query.filter_by(userID=current_id).order_by(Query.query_count.desc()).first()
        if count is None:
            query_count = 0
        else:
            query_count = int(count.query_count)
        query = Query(query_count=query_count + 1, userID=current_id, query_text=query_text,
                      query_duration=query_duration, query_difficulty=query_difficulty,
                      query_free_option=query_free_option)
        db.session.add(query)

        # Update query results for current query session to Recommendation database
        for idx, item in enumerate(query_courses):
            existing_rec=Recommendation.query.filter_by(userID=current_id,courseID=item).first()
            if existing_rec is None:
                rec = Recommendation(userID=current_id, query_count=query_count + 1, ranking=idx, courseID=item)
                db.session.add(rec)
        db.session.commit()

        # Redirect and pass-on user inputs for inferrence in results route
        flash('Got your preferences!', category='success')
        return redirect(url_for('results', query_text=query_text, query_duration=query_duration,
                                query_difficulty=query_difficulty, query_free_option=query_free_option))

    # Renders query form
    return render_template('query.html',form=form,query=True)



@app.route('/results', methods=['GET', 'POST'])
@login_required
def results():
    title = 'Recommendation Results'
    # Check if user is signed in
    if not current_user.is_authenticated:
        return redirect(url_for('/'))

    # Initialization
    current_id = current_user.userID
    query_text = request.args.get('query_text')
    query_duration = request.args.get('query_duration')
    query_difficulty = request.args.get('query_difficulty')
    query_free_option = request.args.get('query_free_option')

    # Check if there is missing query inputs
    if (query_text is None) | (query_duration is None) | (query_difficulty is None) | (query_free_option is None):
        flash('Please fill in your preferences below', category='warning')
        return redirect(url_for('query'))

    # Infer recommendations
    query_input = [query_text, int(query_duration), int(query_difficulty), int(query_free_option)]
    query_courses = recommend(user_input=query_input, rating_data=rating_data,
                              tfidf_vectorizer=tfidf_vectorizer, tfidf_data=tfidf_data,
                              categorical_data=categorical_data)
    rec_list = []
    for item in query_courses:
        rec_list.append(Course.query.filter_by(courseID=item).first())

    # Render Query Results
    difficulty = {0: "Beginner", 1: "Intermediate", 2: "Advanced"}
    duration = {0: "Short", 1: "Medium", 2: "Long"}
    free_option = {0: "Paid", 1: "Free"}
    platform = {0:'AWS',1:'dataCamp',2:'Edureka',3:'Edx',4:'freecodeCamp',5:'FutureLearn',6:'Independent',7:'Linkedin',8:'Microsoft',9:'Pluralsight',10:'Udacity',11:'Udemy',12:'Coursera'}
    fav_query = Favourite().query.filter_by(userID=current_id)
    favlist = []
    for item in fav_query:
        favlist.append(item.courseID)
    for course in rec_list:
        course.difficulty = difficulty.get(course.difficulty, "Unknown")
        course.duration = duration.get(course.duration, "Unknown")
        course.free_option = free_option.get(course.free_option, "Unknown")
        course.platform=platform.get(course.platform,"Unkown")
    return render_template('results.html', title=title, rec_list=rec_list, favlist=favlist, query=True)

@app.route('/query2', methods=['GET', 'POST'])
@login_required
def query2():

    # Check if user is signed in
    if not current_user.is_authenticated:
        return redirect(url_for('/'))
    # Initialization
    current_id = current_user.userID
    title = 'Personalized course recommendations2'
    form = CareerInterstForm()

    # Validate form submission and update database based on query session
    if form.validate_on_submit():
        query_text = form.topic.data
        query_duration = form.duration.data
        query_difficulty = form.difficulty.data
        query_free_option = form.freePaid.data

        # Infer Recommendations
        query_input = [query_text, int(query_duration), int(query_difficulty), int(query_free_option)]
        query_courses = recommend_job_role_based(user_input=query_input, rating_data=rating_data,
                                  tfidf_vectorizer=tfidf_vectorizer, tfidf_data=tfidf_data,
                                  categorical_data=categorical_data)

        # Check if there is any courses recommended
        if len(query_courses) == 0:
            flash('There are no courses found, please try again', category='warning')
            return redirect(url_for('query2'))
        # Update query session to Query database
        count = Query.query.filter_by(userID=current_id).order_by(Query.query_count.desc()).first()
        if count is None:
            query_count = 0
        else:
            query_count = int(count.query_count)
        query = Query(query_count=query_count + 1, userID=current_id, query_text=query_text,
                      query_duration=query_duration, query_difficulty=query_difficulty,
                      query_free_option=query_free_option)
        db.session.add(query)

        # Update query results for current query session to Recommendation database
        for idx, item in enumerate(query_courses):
            existing_rec=Recommendation.query.filter_by(userID=current_id,courseID=item).first()
            if existing_rec is None:
                rec = Recommendation(userID=current_id, query_count=query_count + 1, ranking=idx, courseID=item)
                db.session.add(rec)
        db.session.commit()

        # Redirect and pass-on user inputs for inferrence in results route
        flash('Got your preferences!', category='success')
        return redirect(url_for('results2', query_text=query_text, query_duration=query_duration,
                                query_difficulty=query_difficulty, query_free_option=query_free_option))

    # Renders query form
    return render_template('query2.html',form=form,query2=True)


@app.route('/results2', methods=['GET', 'POST'])
@login_required
def results2():
    title = 'Recommendation Results'
    # Check if user is signed in
    if not current_user.is_authenticated:
        return redirect(url_for('/'))

    # Initialization
    current_id = current_user.userID
    query_text = request.args.get('query_text')
    query_duration = request.args.get('query_duration')
    query_difficulty = request.args.get('query_difficulty')
    query_free_option = request.args.get('query_free_option')

    # Check if there is missing query inputs
    if (query_text is None) | (query_duration is None) | (query_difficulty is None) | (query_free_option is None):
        flash('Please fill in your preferences below', category='warning')
        return redirect(url_for('query'))

    # Infer recommendations
    query_input = [query_text, int(query_duration), int(query_difficulty), int(query_free_option)]
    query_courses = recommend_job_role_based(user_input=query_input, rating_data=rating_data,
                              tfidf_vectorizer=tfidf_vectorizer, tfidf_data=tfidf_data,
                              categorical_data=categorical_data)
    rec_list = []
    for item in query_courses:
        rec_list.append(Course.query.filter_by(courseID=item).first())

    # Render Query Results
    difficulty = {0: "Beginner", 1: "Intermediate", 2: "Advanced"}
    duration = {0: "Short", 1: "Medium", 2: "Long"}
    free_option = {0: "Paid", 1: "Free"}
    platform = {0:'AWS',1:'dataCamp',2:'Edureka',3:'Edx',4:'freecodeCamp',5:'FutureLearn',6:'Independent',7:'Linkedin',8:'Microsoft',9:'Pluralsight',10:'Udacity',11:'Udemy',12:'Coursera'}
    fav_query = Favourite().query.filter_by(userID=current_id)
    favlist = []
    for item in fav_query:
        favlist.append(item.courseID)
    for course in rec_list:
        course.difficulty = difficulty.get(course.difficulty, "Unknown")
        course.duration = duration.get(course.duration, "Unknown")
        course.free_option = free_option.get(course.free_option, "Unknown")
        course.platform=platform.get(course.platform,"Unkown")
    return render_template('results2.html', title=title, rec_list=rec_list, favlist=favlist, query=True)

# @app.route('/viewprofile')
# @login_required
# def viewprofile():
#     return render_template('viewprofile.html')

@app.route('/coursedisplay/<CourseID>')
@login_required
def coursedisplay(CourseID):
    print("innnnnnnnnnnnnn")
    course=(Course.query.filter_by(courseID=CourseID).first())

    return render_template('coursedisplay.html',course=course)
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
