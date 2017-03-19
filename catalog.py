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

#JSON routes
@app.route('/categories/JSON')
def categoriesJSON():
    categories = session.query(Category).all()
    return jsonify(Category=[c.serialize for c in categories])

@app.route('/categories/<int:category_id>/JSON')
def itemsJSON(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).all()
    return jsonify(Items=[i.serialize for i in items])

@app.route('/login')
def showLogin():
    return render_template('login.html')

@app.route('/')
@app.route('/categories')
def showMain():
    categories = session.query(Category).order_by(asc(Category.name))

    return render_template('main.html', categories=categories)

# Category routes
@app.route('/categories/new', methods=['GET', 'POST'])
def newCategory():
    if request.method == 'POST':
        if request.form['name']:
            newCategory = Category(name=request.form['name'])
            session.add(newCategory)
            session.commit()
            flash('Your new category has been created.')

            return redirect(url_for('showMain'))
        else:
            flash('Please enter in a name.')
            return render_template('newCategory.html')
    else:
        return render_template('newCategory.html')

@app.route('/categories/<int:category_id>/')
def showCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).all()

    return render_template('showCategory.html', category=category, items=items)

@app.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
def editCategory(category_id):
    editCategory = session.query(Category).filter_by(id=category_id).one()

    if request.method == 'POST':
        if request.form['name']:
            editCategory.name = request.form['name']
            session.add(editCategory)
            session.commit()
            flash('Your category has been editted.')
            return redirect('/')
        else:
            flash('Please enter in a name.')
            return render_template('editCategory.html', category_id=category_id, category=editCategory)
    else:
        return render_template('editCategory.html', category_id=category_id, category=editCategory)

@app.route('/categories/<int:category_id>/delete', methods=['GET', 'POST'])
def deleteCategory(category_id):
    deleteCategory = session.query(Category).filter_by(id=category_id).one()

    if request.method == 'POST':
        session.delete(deleteCategory)
        session.commit()
        flash('Your category has been deleted.')

        return redirect('/')
    else:
        return render_template('deleteCategory.html', category_id=category_id, category=deleteCategory)

# Item routes
@app.route('/categories/<int:category_id>/new', methods=['GET', 'POST'])
def newItem(category_id):
    if request.method == 'POST':
        if request.form['name']:
            newItem = Item(
                                name=request.form['name'],
                                description=request.form['description'],
                                category_id=category_id
                                )

            session.add(newItem)
            session.commit()
            flash('Your item has been created.')

            return redirect(url_for('showCategory', category_id=category_id))
        else:
            flash('Please enter in a name.')
            return render_template('newItem.html', category_id=category_id)
    else:
        return render_template('newItem.html', category_id=category_id)

@app.route('/categories/<int:category_id>/<int:item_id>/')
def showItem(category_id, item_id):
    item = session.query(Item).filter_by(id=item_id).one()

    return render_template('showItem.html', category_id=category_id, item_id=item_id, item=item)

@app.route('/categories/<int:category_id>/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(category_id, item_id):
    editItem = session.query(Item).filter_by(id=item_id).one()

    if request.method == 'POST':
        if request.form['name']:
            editItem.name = request.form['name']
            editItem.description = request.form['description']

            session.add(editItem)
            session.commit()
            flash('Your item has been editted.')

            return redirect(url_for('showCategory', category_id=category_id))
        else:
            flash('Please enter in a name.')
            return render_template('editItem.html', category_id=category_id, item_id=item_id, item=editItem)
    else:
        return render_template('editItem.html', category_id=category_id, item_id=item_id, item=editItem)

@app.route('/categories/<int:category_id>/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    deleteItem = session.query(Item).filter_by(id=item_id).one()

    if request.method == 'POST':
        session.delete(deleteItem)
        session.commit()
        flash('Your item has been deleted.')

        return redirect(url_for('showCategory', category_id=category_id))

    else:
        return render_template('deleteItem.html', category_id=category_id, item_id=item_id, item=deleteItem)



if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 8000)
