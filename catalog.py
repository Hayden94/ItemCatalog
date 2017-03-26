from flask import Flask,  render_template, request
from flask import redirect, url_for, flash, jsonify
from flask import session as login_session
from flask import make_response

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

import random
import string
import httplib2
import json
import requests
import time

# Import CRUD operations
from db_setup import Base, Category, Item, User
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"

# Create session and connect to DB
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# JSON endpoint routes
@app.route('/categories/JSON')
def categoriesJSON():
    categories = session.query(Category).all()
    return jsonify(Categories=[c.serialize for c in categories])


@app.route('/categories/<int:category_id>/JSON')
def itemsJSON(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).all()
    return jsonify(Items=[i.serialize for i in items])


# Authentication/authorization routes
@app.route('/login')
def showLogin():
    state = ''.join(
                    random.choice(
                                  string.ascii_uppercase + string.digits
                                  ) for x in range(32)
                    )
    login_session['state'] = state
    return render_template('login.html',
                           state=state,
                           login_session=login_session)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter!'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
        credentials = credentials.to_json()
        credentials = json.loads(credentials)
        # print credentials
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials['access_token']
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # print result

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials['id_token']['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials['access_token'], 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])

    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += "<div style='text-align: center; position: relative;"
    output += "margin: 0 auto; display: block;'>"
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!<br>'
    output += login_session['email']
    output += '</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ''' " style = "width: 300px; height: 300px;
                border-radius: 150px;-webkit-border-radius: 150px;
                -moz-border-radius: 150px;"> '''
    output += "</br></br>"
    output += "</div>"
    flash("You are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# User helper models
def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
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
@app.route('/logout')
def gdisconnect():
    access_token = login_session.get('access_token')

    if access_token is None:
        response = make_response(
                                 json.dumps('Current user not connected.'),
                                 401
                                 )
        response.headers['Content-Type'] = 'application/json'
        print "Current user not connected."
        return response

    print 'In gdisconnect access token is %s' % access_token
    print 'User name is: '
    print login_session['username']

    url = (
           'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token
           )
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result

    if result['status'] == '200':
        del login_session['credentials']
        del login_session['access_token']
        del login_session['provider']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully Disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        print "Successfully Disconnected."
        time.sleep(1)
        flash('You have been logged out successfully.')
        return redirect(url_for('showMain'))

    else:
        response = make_response(json.dumps(
                                            """Failed to revoke token
                                            for given user."""
                                            ), 400)
        response.headers['Content-Type'] = 'application/json'
        print "Failed to revoke token for given user."
        return response


# Category Routes
@app.route('/')
@app.route('/categories')
def showMain():
    categories = session.query(Category).order_by(asc(Category.name))
    latest = session.query(Item).order_by(desc(Item.id)).limit(5).all()

    if 'username' not in login_session:
        return render_template('publicHome.html',
                               categories=categories,
                               latest=latest,
                               login_session=login_session)

    return render_template('home.html',
                           categories=categories,
                           latest=latest,
                           login_session=login_session)


@app.route('/categories/new', methods=['GET', 'POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        if request.form['name']:
            newCategory = Category(name=request.form['name'],
                                   user_id=login_session['user_id'])
            session.add(newCategory)
            session.commit()
            flash('Your new category has been created.')

            return redirect(url_for('showMain'))
        else:
            flash('Please enter in a name.')
            return render_template('newCategory.html',
                                   login_session=login_session)
    else:
        return render_template('newCategory.html',
                               login_session=login_session)


@app.route('/categories/<int:category_id>/')
def showCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    creator = getUserInfo(category.user_id)
    items = session.query(Item).filter_by(category_id=category_id).all()

    if 'username' not in login_session:
        return render_template('publicShowCategory.html',
                               category=category,
                               items=items,
                               creator=creator,
                               login_session=login_session)
    else:
        return render_template('showCategory.html',
                               category=category,
                               items=items,
                               creator=creator,
                               login_session=login_session)


@app.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
def editCategory(category_id):
    editCategory = session.query(Category).filter_by(id=category_id).one()

    if 'username' not in login_session:
        return redirect('/login')
    if editCategory.user_id != login_session['user_id']:
        output = ''
        output += '<script>'
        output += 'function alertUser() '
        output += "{alert('You are not authorized to edit this category.');"
        output += "window.location.replace('/');}"
        output += '</script>'
        output += "<body onload='alertUser()''>"
        return output
    if request.method == 'POST':
        if request.form['name']:
            editCategory.name = request.form['name']
            session.add(editCategory)
            session.commit()
            flash('Your category has been editted.')
            return redirect('/')
        else:
            flash('Please enter in a name.')
            return render_template('editCategory.html',
                                   category_id=category_id,
                                   category=editCategory,
                                   login_session=login_session)
    else:
        return render_template('editCategory.html',
                               category_id=category_id,
                               category=editCategory,
                               login_session=login_session)


@app.route('/categories/<int:category_id>/delete', methods=['GET', 'POST'])
def deleteCategory(category_id):
    deleteCategory = session.query(Category).filter_by(id=category_id).one()

    if 'username' not in login_session:
        return redirect('/login')
    if deleteCategory.user_id != login_session['user_id']:
        output = ''
        output += '<script>'
        output += 'function alertUser() '
        output += "{alert('You are not authorized to delete this category.');"
        output += "window.location.replace('/');}"
        output += '</script>'
        output += "<body onload='alertUser()''>"
        return output
    if request.method == 'POST':
        session.delete(deleteCategory)
        session.commit()
        flash('Your category has been deleted.')

        return redirect('/')
    else:
        return render_template('deleteCategory.html',
                               category_id=category_id,
                               category=deleteCategory,
                               login_session=login_session)


# Item routes
@app.route('/categories/<int:category_id>/<int:item_id>/')
def showItem(category_id, item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    creator = getUserInfo(item.user_id)

    return render_template('showItem.html',
                           category_id=category_id,
                           item_id=item_id,
                           item=item,
                           creator=creator,
                           login_session=login_session)


@app.route('/categories/<int:category_id>/new', methods=['GET', 'POST'])
def newItem(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        if request.form['name']:
            newItem = Item(name=request.form['name'],
                           description=request.form['description'],
                           user_id=login_session['user_id'],
                           category_id=category_id)

            session.add(newItem)
            session.commit()
            flash('Your item has been created.')

            return redirect(
                            url_for('showCategory',
                                    category_id=category_id)
                            )
        else:
            flash('Please enter in a name.')
            return render_template('newItem.html',
                                   category_id=category_id,
                                   login_session=login_session)
    else:
        return render_template('newItem.html',
                               category_id=category_id,
                               login_session=login_session)


@app.route(
           '/categories/<int:category_id>/<int:item_id>/edit',
           methods=['GET', 'POST']
           )
def editItem(category_id, item_id):
    editItem = session.query(Item).filter_by(id=item_id).one()

    if 'username' not in login_session:
        return redirect('/login')
    if editItem.user_id != login_session['user_id']:
        output = ''
        output += '<script>'
        output += 'function alertUser() '
        output += "{alert('You are not authorized to edit this item.');"
        output += "window.location.replace('/');}"
        output += '</script>'
        output += "<body onload='alertUser()''>"
        return output
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
            return render_template('editItem.html',
                                   category_id=category_id,
                                   item_id=item_id,
                                   item=editItem,
                                   login_session=login_session)
    else:
        return render_template('editItem.html',
                               category_id=category_id,
                               item_id=item_id,
                               item=editItem,
                               login_session=login_session)


@app.route(
           '/categories/<int:category_id>/<int:item_id>/delete',
           methods=['GET', 'POST']
           )
def deleteItem(category_id, item_id):
    deleteItem = session.query(Item).filter_by(id=item_id).one()

    if 'username' not in login_session:
        return redirect('/login')
    if deleteItem.user_id != login_session['user_id']:
        output = ''
        output += '<script>'
        output += 'function alertUser() '
        output += "{alert('You are not authorized to delete this item.');"
        output += "window.location.replace('/');}"
        output += '</script>'
        output += "<body onload='alertUser()''>"
        return output
    if request.method == 'POST':
        session.delete(deleteItem)
        session.commit()
        flash('Your item has been deleted.')

        return redirect(url_for('showCategory', category_id=category_id))

    else:
        return render_template('deleteItem.html',
                               category_id=category_id,
                               item_id=item_id,
                               item=deleteItem,
                               login_session=login_session)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
