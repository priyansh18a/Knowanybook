import os

from flask import Flask, session, render_template,Blueprint, redirect, url_for, request, flash,jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_session import Session
from sqlalchemy import create_engine
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_login import LoginManager,login_required, current_user,login_user,logout_user
from models import userdata,books,review
import flask_whooshalchemyplus
from flask_whooshalchemyplus import index_all
import requests
import sys, json


app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")
engine = create_engine(os.getenv("DATABASE_URL"))


# Configure session to use filesystem
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['SECRET_KEY'] = '9OLWxND4o83j4K4iuopO'
app.config['WHOOSH_BASE'] = 'path/to/whoosh/base'

# Set up databasappe
db = SQLAlchemy(app)
db.init_app(app)
flask_whooshalchemyplus.init_app(app)    # initialize
index_all(app)

flask_whooshalchemyplus.whoosh_index(app, books)



@app.route("/")
def index():
    return render_template("index.html")

@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html",name=current_user.name)

@app.route("/books")
@login_required
def books_data():
    Books = books.query.all()
    return render_template('books.html',Books= Books)

@app.route("/books/<int:id>", methods=['POST'])
def books_post(id):
    count = 0
    rate = 0
    book  = books.query.get(id)
    count = book.review_count
    rating = request.form.get('Rating')
    opinion = request.form.get('opinion')
    user = review.query.filter_by(user=current_user.email,books_id=id).first()

    if user:
        flash('You can review any book only one time') #sern bx +3q if a user is found, we want to him not to submit again
        return redirect( url_for('book_page', isbn=book.isbn))

    reviews = review(user = current_user.email,review_data=opinion,books_id=id)
    db.session.add(reviews)
    db.session.commit()
    rate = book.rating
    #((Overall Rating * Total Rating) + new Rating) / (Total Rating + 1)
    if(rate == None):
        count = 0
        rate = 0
    rate = float(rate)
    rating = float(rating)
    rating = ((rate*count)+rating)/(count+1)
    book2 = books.query.get(id)
    book2.rating = rating
    book2.review_count =  count +1
    return redirect(url_for('books_data'))

@app.route("/login")
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False


    user = userdata.query.filter_by(email=email).first()

    # check if user actually exists
    # take the user supplied password, hash it, and compare it to the hashed password in database
    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('login')) # if user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)
    return redirect(url_for('profile'))

@app.route('/search')
def search():
    Books = books.query.whoosh_search(request.args.get('query'),like=True).all()
    if not Books:
        flash('No Match found!')
        return render_template('books.html' ,Books= Books)
    return render_template('books.html' ,Books= Books)

@app.route('/book/<string:isbn>')
def book_page(isbn):
    Books =[]
    res = requests.get("https://www.goodreads.com/book/review_counts.json?key=UOI8GNPPDPNcoCOWu7iDbg&isbns=" + isbn)
    Books = books.query.filter_by(isbn=isbn).first()
    if not Books:
        flash('No Match found!')
    if res.status_code == 200:
        res == 0
        data = res.json()
        average_rating  = data["books"][0]["average_rating"]
        work_ratings_count = data["books"][0]["work_ratings_count"]
    elif res.status_code != 200:
        average_rating = 'Not Available'
        work_ratings_count = 'Not Available'
    reviews = review.query.filter_by(books_id = Books.id)
    return render_template('book_page.html', Books=Books,average_rating=average_rating,work_ratings_count= work_ratings_count,reviews =reviews)


@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    user = userdata.query.filter_by(email=email).first()

    if user:
        flash('Email address already exists') # if a user is found, we want to redirect back to signup page so user can try again
        return redirect(url_for('signup'))

    # create new user with the form data. Hash the password so plaintereturn redirect('/')xt version isn't saved.
    new_user = userdata(email=email, name=name, password=generate_password_hash(password, method='sha256'))

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/api/<string:isbn>')
@login_required
def get_book(isbn):
    book = books.query.filter_by(isbn=isbn).first()
    if book is None:
        return jsonify({"error": "Invalid flight_id"}), 422
    return jsonify({
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "isbn": book.isbn,
        "review_count": book.review_count,
        "average_score": book.rating
    })

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
    return userdata.query.get(int(user_id))

if __name__ =='__main__'   :
    app.run(debug = True)
