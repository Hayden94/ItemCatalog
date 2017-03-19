from flask import Flask,  render_template, request, redirect, url_for, flash, jsonify
app = Flask(__name__)

from flask import session as login_session
import random, string

# from oauth2client.client import flow_from_clientsecrets
# from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

# import CRUD operations
from db_setup import Base, Category, Item
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker

#Create session and connect to DB
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')
@app.route('/categories')
def showMain():
    return render_template('main.html')

@app.route('/login')
def showLogin():
    return render_template('login.html')

@app.route('/categories/new')
def newCategory():
    return render_template('newCategory.html')

@app.route('/categories/<int:category_id>/')
def showCategory(category_id):
    return render_template('showCategory.html')

@app.route('/categories/<int:category_id>/edit')
def editCategory(category_id):
    return render_template('editCategory.html')

@app.route('/categories/<int:category_id>/delete')
def deleteCategory(category_id):
    return render_template('deleteCategory.html')

@app.route('/categories/<int:category_id>/new')
def newItem(category_id):
    return render_template('newItem.html')

@app.route('/categories/<int:category_id>/<int:item_id>/')
def showItem(category_id, item_id):
    return render_template('showItem.html')

@app.route('/categories/<int:category_id>/<int:item_id>/edit')
def editItem(category_id, item_id):
    return render_template('editItem.html')

@app.route('/categories/<int:category_id>/<int:item_id>/delete')
def deleteItem(category_id, item_id):
    return render_template('deleteItem.html')



if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 8000)
