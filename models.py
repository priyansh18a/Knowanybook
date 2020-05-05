import os

from flask import Flask
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class userdata(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))

class books(db.Model):
    __tablename__ = 'books'
    __searchable__ = ['isbn','title','author']
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    isbn = db.Column(db.String(100), unique=True)
    title = db.Column(db.String(200), unique=True)
    author = db.Column(db.String(200))
    year = db.Column(db.Integer)
    rating = db.Column(db.Numeric(12,1),nullable=False)
    review_count = db.Column(db.Integer,nullable=False)
    review = db.relationship("review",backref="books",lazy=True)

class review(db.Model):
    __tablename__ = "review"
    id = db.Column(db.Integer, primary_key=True)
    user  = db.Column(db.String, nullable=False)
    review_data = db.Column(db.String)
    books_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
