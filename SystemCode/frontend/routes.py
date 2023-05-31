from flask import jsonify, render_template, session,url_for,redirect,flash,request
from frontend import app
from frontend.forms import SignupForm, LoginForm,SurveyForm,CareerInterstForm
from flask_login import login_user, login_required, current_user, logout_user
from frontend.models import User, Query, Course, Favourite, Recommendation,Completed,skill
from frontend import bcrypt, db
from frontend.models import User,Course
# from Recommendation import recommend
from datetime import datetime
from Recommendation.recommend import recommend_default
from Recommendation.recommend import recommend
from Recommendation.recommend import load_pickle,tfidf_vectorizer_filepath,tfidf_data_filepath,categorical_data_filepath
import pytz
import numpy as np
import config
from Recommendation.recommend_job import recommend_job_role_based
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
import json
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
        email= form.email.data
        em=User.query.filter_by(email=email).first()
        if em:
            flash("User already exist,please try another email",category='danger')
            return redirect(url_for('signup'))
        username = form.username.data
        user = User.query.filter_by(username=username).first()
        if user:
            flash("User already exist,please try another username",category='danger')
            return redirect(url_for('signup'))
        password = bcrypt.generate_password_hash(form.password.data)
        user = User(name=name,email=email, username=username, password=password)
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
        course.difficulty = difficulty.get(course.difficulty, "Beginner")
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
        course.difficulty = difficulty.get(course.difficulty, "Beginner")
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
    current_id = current_user.userID
    course=(Course.query.filter_by(courseID=CourseID).first())
    difficulty = {0: "Beginner", 1: "Intermediate", 2: "Advanced"}
    duration = {0: "Short", 1: "Medium", 2: "Long"}
    free_option = {0: "Paid", 1: "Free"}
    platform = {0:'AWS',1:'dataCamp',2:'Edureka',3:'Edx',4:'freecodeCamp',5:'FutureLearn',6:'Independent',7:'Linkedin',8:'Microsoft',9:'Pluralsight',10:'Udacity',11:'Udemy',12:'Coursera'}

    fav_query = Favourite().query.filter_by(userID=current_id)
    favlist = []
    for item in fav_query:
        favlist.append(item.courseID)

    comp_query = Completed().query.filter(and_(Completed.userID == current_id, Completed.courseID == CourseID)).first()
    is_completed = comp_query
    

    course.difficulty = difficulty.get(course.difficulty, "Beginner")
    course.duration = duration.get(course.duration, "Unknown")
    course.free_option = free_option.get(course.free_option, "Unknown")
    course.platform=platform.get(course.platform,"Unkown")

    return render_template('coursedisplay.html', course=course,favlist=favlist, is_completed=is_completed)
@app.route('/history', methods=['GET'])
@login_required
def history():
    # Check if user is signed in
    if not current_user.is_authenticated:
        return redirect(url_for('/'))

    # Render list of historical queries
    title = 'My past searches'
    current_id = current_user.userID
    history_queries = Query().query.filter_by(userID=current_id).order_by(Query.query_count.desc())
    # if len(historySearches) > 5:
    #    historySearches = historySearches[0:5]
    query_free_option = {0: "Free and paid courses", 1: "Only free courses"}
    query_difficulty = {0: "Any", 1: "Beginner", 2: "Intermediate", 3: "Advanced"}
    query_duration = {0: "Any", 1: "Short", 2: "Medium", 3: "Long"}
    output_list = []
    for ind_query in history_queries:
        # ind_query.query_difficulty = query_difficulty.get(ind_query.query_difficulty, "Unknown")
        # ind_query.query_duration = query_duration.get(ind_query.query_duration, "Unknown")
        # ind_query.query_free_option = query_free_option.get(ind_query.query_free_option, "Unknown")
        difficulty = query_difficulty.get(ind_query.query_difficulty, "Beginner")
        duration = query_duration.get(ind_query.query_duration, "Unknown")
        free_option = query_free_option.get(ind_query.query_free_option, "Unknown")
        past_time = datetime.utcnow()-ind_query.query_time
        if past_time.days > 0:
            time_string = str(int(past_time.days)) + " days ago"
        elif past_time.seconds > 3600:
            time_string = str(int(past_time.seconds/3600)) + " hours ago"
        elif past_time.seconds > 60:
            time_string = str(int(past_time.seconds / 60)) + " minutes ago"
        else:
            time_string = str(int(past_time.seconds)) + " seconds ago"
        output = [ind_query.query_text,duration, difficulty, free_option, time_string , ind_query.query_count]
        output_list.append(output)
    nquery = len(output_list)
    return render_template('history.html', title=title, output_list=output_list, nquery=nquery, history=True)

@app.route('/history/<int:query_count>', methods=['GET'])
@login_required
def displaypastresult(query_count):
    # Check if user is signed in
    if not current_user.is_authenticated:
        return redirect(url_for('/'))
    title = 'My past searches'

    # Initialize current userID
    current_id = current_user.userID

    # Check if query count page exceed the query results available
    query_count_max = max([int(x[0]) for x in Query().query.with_entities(Query.query_count).
                          filter_by(userID=current_id).all()])
    if query_count > query_count_max:
        return redirect(url_for('history'))

    # Render the results of the given historical query
    query_result = Recommendation().query.filter_by(userID=current_id).filter_by(query_count=query_count)
    query_result_list = []
    for item in query_result:
        query_result_list.append(Course.query.filter_by(courseID=item.courseID).first())
    difficulty = {0: "Beginner", 1: "Intermediate", 2: "Advanced"}
    duration = {0: "Short", 1: "Medium", 2: "Long"}
    free_option = {0: "Paid", 1: "Free"}
    platform = {0:'AWS',1:'dataCamp',2:'Edureka',3:'Edx',4:'freecodeCamp',5:'FutureLearn',6:'Independent',7:'Linkedin',8:'Microsoft',9:'Pluralsight',10:'Udacity',11:'Udemy',12:'Coursera'}
    for course in query_result_list:
        course.difficulty = difficulty.get(course.difficulty, "Beginner")
        course.duration = duration.get(course.duration, "Unknown")
        course.free_option = free_option.get(course.free_option, "Unknown")
        course.platform = platform.get(course.platform, "Unknown")
    fav_query = Favourite().query.filter_by(userID=current_id)
    favlist = []
    for item in fav_query:
        favlist.append(item.courseID)
    return render_template('results.html', title=title, query_count=query_count, rec_list=query_result_list,
                           favlist=favlist, history=True)

@app.route('/mycourse',methods=['GET', 'POST'])
@login_required
def mycourse():
    if not current_user.is_authenticated:
        return redirect(url_for('/'))
    current_id = current_user.userID
    fav_query = Favourite().query.filter_by(userID=current_id)
    fav_list = []
    comp_query = Completed().query.filter_by(userID=current_id)
    comp_list = []
    for item in fav_query:
        fav_list.append(Course.query.filter_by(courseID=item.courseID).first())
        print(fav_list)
    for item in comp_query:
        comp_list.append(Course.query.filter_by(courseID=item.courseID).first())
    difficulty = {0: "Beginner", 1: "Intermediate", 2: "Advanced"}
    duration = {0: "Short", 1: "Medium", 2: "Long"}
    free_option = {0: "Paid", 1: "Free"}
    platform = {0:'AWS',1:'dataCamp',2:'Edureka',3:'Edx',4:'freecodeCamp',5:'FutureLearn',6:'Independent',7:'Linkedin',8:'Microsoft',9:'Pluralsight',10:'Udacity',11:'Udemy',12:'Coursera'}
    for course in fav_list:
        course.difficulty = difficulty.get(course.difficulty, "Beginner")
        course.duration = duration.get(course.duration, "Unknown")
        course.free_option = free_option.get(course.free_option, "Unknown")
        course.platform=platform.get(course.platform,"Unkown")
    for course in comp_list:
        course.difficulty = difficulty.get(course.difficulty, "Beginner")
        course.duration = duration.get(course.duration, "Unknown")
        course.free_option = free_option.get(course.free_option, "Unknown")
        course.platform=platform.get(course.platform,"Unkown")
    return render_template('mycourse.html',fav_list=fav_list,comp_list=comp_list, mycourse=True)


@app.route('/Mark_Completed')
@login_required
def Mark_Completed():
    return render_template('Mark_Completed.html')
    

@app.route('/likeunlike', methods=['POST', 'GET'])
@login_required
def likeunlike():
    if not current_user.is_authenticated:
        return redirect(url_for('/'))
    current_id = current_user.userID
    if request.method == 'POST':
        course_id = request.form['course_id']
        req_type = request.form['type']
        print(current_id)
        print(req_type)
        print(course_id)
        entry = Favourite(userID=current_id, courseID=course_id)
        if req_type == '1':
            db.session.add(entry)
            db.session.commit()
        if req_type == '0':
            entry = Favourite.query.filter_by(userID=current_id, courseID=course_id).first()
            db.session.delete(entry)
            db.session.commit()
    return jsonify('Success')

@app.route('/complete', methods=['POST'])
@login_required
def complete():
    if not current_user.is_authenticated:
        return redirect(url_for('/'))

    current_id = current_user.userID

    if request.method == 'POST':
        course_id = request.form['course_id']
        completed = request.form['type']

        print(current_id)
        print(completed)
        print(course_id)
        entry = Completed(userID=current_id, courseID=course_id)
        if completed == '1':
            db.session.add(entry)
            db.session.commit()
        elif completed == '0':
            entry = Completed.query.filter_by(userID=current_id, courseID=course_id).first()
            db.session.delete(entry)
            db.session.commit()

    return jsonify('Success')



@app.route('/submit_skill', methods=['POST'])
@login_required
def submit_skill():
    skill_list = request.form.getlist('skills')
    current_id = current_user.userID
    courseID=Course.courseID
    fav_query = Favourite().query.filter_by(userID=current_id)
    fav_list = []
    comp_query = Completed().query.filter_by(userID=current_id)
    comp_list = []
    for item in fav_query:
        fav_list.append(Course.query.filter_by(courseID=item.courseID).first())
    for item in comp_query:
        comp_list.append(Course.query.filter_by(courseID=item.courseID).first())
    try:
        # Iterate over the submitted skills and save them to the database
        for skill_text in skill_list:
            existing_skill = skill.query.filter_by(userID=current_id, skill=skill_text).first()
            if not existing_skill:
                new_skill = skill(userID=current_id, skill=skill_text)
                db.session.add(new_skill)
        
        db.session.commit()
        flash('Skills saved successfully!', category='success')
    except IntegrityError:
        db.session.rollback()
        flash('An error occurred while saving the skills.', category='error')
    
    difficulty = {0: "Beginner", 1: "Intermediate", 2: "Advanced"}
    duration = {0: "Short", 1: "Medium", 2: "Long"}
    free_option = {0: "Paid", 1: "Free"}
    platform = {0:'AWS',1:'dataCamp',2:'Edureka',3:'Edx',4:'freecodeCamp',5:'FutureLearn',6:'Independent',7:'Linkedin',8:'Microsoft',9:'Pluralsight',10:'Udacity',11:'Udemy',12:'Coursera'}
    for course in fav_list:
        course.difficulty = difficulty.get(course.difficulty, "Beginner")
        course.duration = duration.get(course.duration, "Unknown")
        course.free_option = free_option.get(course.free_option, "Unknown")
        course.platform=platform.get(course.platform,"Unkown")
    for course in comp_list:
        course.difficulty = difficulty.get(course.difficulty, "Beginner")
        course.duration = duration.get(course.duration, "Unknown")
        course.free_option = free_option.get(course.free_option, "Unknown")
        course.platform=platform.get(course.platform,"Unkown")
    
    return render_template('mycourse.html',fav_list=fav_list,comp_list=comp_list,mycourse=True)

@app.route('/Profile')
@login_required
def Profile():
    # Retrieve skills from the database
    current_id = current_user.userID
    skills = skill.query.filter_by(userID=current_id).all()
    fav_query = Favourite().query.filter_by(userID=current_id)
    fav_list = []
    comp_query = Completed().query.filter_by(userID=current_id)
    comp_list = []
    for item in fav_query:
        fav_list.append(Course.query.filter_by(courseID=item.courseID).first())
    for item in comp_query:
        comp_list.append(Course.query.filter_by(courseID=item.courseID).first())
    difficulty = {0: "Beginner", 1: "Intermediate", 2: "Advanced"}
    duration = {0: "Short", 1: "Medium", 2: "Long"}
    free_option = {0: "Paid", 1: "Free"}
    platform = {0:'AWS',1:'dataCamp',2:'Edureka',3:'Edx',4:'freecodeCamp',5:'FutureLearn',6:'Independent',7:'Linkedin',8:'Microsoft',9:'Pluralsight',10:'Udacity',11:'Udemy',12:'Coursera'}
    for course in fav_list:
        course.difficulty = difficulty.get(course.difficulty, "Beginner")
        course.duration = duration.get(course.duration, "Unknown")
        course.free_option = free_option.get(course.free_option, "Unknown")
        course.platform=platform.get(course.platform,"Unkown")
    for course in comp_list:
        course.difficulty = difficulty.get(course.difficulty, "Beginner")
        course.duration = duration.get(course.duration, "Unknown")
        course.free_option = free_option.get(course.free_option, "Unknown")
        course.platform=platform.get(course.platform,"Unkown")
    comp_list_json = json.dumps([course.difficulty for course in comp_list])
    return render_template('Profile.html', skills=skills,fav_list=fav_list,comp_list=comp_list,comp_list_json=comp_list_json,Profile=True)

# @app.route('/index')
# def team():
#     return render_template('team.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
