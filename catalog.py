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

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu App"

# import CRUD operations
from db_setup import Base, Category, Item, User
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker

#Create session and connect to DB
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

#JSON endpoint routes
@app.route('/categories/JSON')
def categoriesJSON():
    categories = session.query(Category).all()
    return jsonify(Category=[c.serialize for c in categories])

@app.route('/categories/<int:category_id>/JSON')
def itemsJSON(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).all()
    return jsonify(Items=[i.serialize for i in items])

# Authentication/authorization routes
@app.route('/login')
def showLogin():
    return render_template('login.html')

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope="")
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
                                 json.dumps('Failed to upgrade the authorization code.'), 401
                                 )
        response.headers['Content-type'] = 'application/json'
        print "Failed to upgrade the authorization code."
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.
    if result.get('error') in not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        print "error"
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
                                 json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        print "Token's user ID doesn't match given user ID."
        return response

    # verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
                                json.dumps("Token's client ID does not match the app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        print "Token's client ID does not match app's"
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
                                 json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        print "Current user is already connected."
        return response

    # Store the access token in the session for later use.
    loggin_session['credentials'] = credentials
    loggin_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    loggin_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += "<div style='text-align: center; position: relative; margin: 0 auto; display: block;'>"
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    output += "</div>"
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# User helper models
def createUser(login_session):
    newUser = User(
                        name = login_session['username'],
                        email = login_session['email'],
                        picture=login_session['picture']
                        )
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# Gaccount - revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    credentials = login_session.get('credentials')
    access_token = credentials.access_token
    print 'In gdisconnect access token is %s' % access_token
    print 'User name is: '
    print login_session['username']

    if access_token is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.header['Content-Type'] = 'application/json'
        print "Current user not connected."
        return response

    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
            % access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result

    if result['status'] == '200':
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully Disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        print "Successfully Disconnected."
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        print "Failed to revoke token for given user."
        return response

# Category Routes
@app.route('/')
@app.route('/categories')
def showMain():
    categories = session.query(Category).order_by(asc(Category.name))

    return render_template('main.html', categories=categories)

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
@app.route('/categories/<int:category_id>/<int:item_id>/')
def showItem(category_id, item_id):
    item = session.query(Item).filter_by(id=item_id).one()

    return render_template('showItem.html', category_id=category_id, item_id=item_id, item=item)

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
