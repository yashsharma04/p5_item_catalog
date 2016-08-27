from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
app = Flask(__name__)
# from sqlalchemy import Column, ForeignKey, Integer, String

# configuration
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem
# login session as a dict 
from flask import session as login_session
import random , string 
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError 
import  httplib2 
import json 
from flask import make_response
from flask import request

CLIENT_ID = json.loads(open('client_secret.json','r').read())['web']['client_id']
# CLIENT_ID = "1054080080208-epjk604hq2jbh8e8rad200q17v3pfn7q.apps.googleusercontent.com"
# print CLIENT_ID
# CLIENT_ID = "eJIBxeeX_g5_IkKPf_mFu5Zo"

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/login')
def showLogin():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
	login_session['state']= state 
	return render_template('login.html',STATE=state)

@app.route('/gconnect',methods=['POST'])
def gconnect():
	state = request.form['state']
	print state
	print "hello"
	if state!=login_session['state']:
		response = make_response(json.dumps('Invalid state parameter '),401)		
		response.headers['Content-Type'] = 'application/json'		
		return response 
	code = request.form['auth']
	print code
	try :
		oauth_flow = flow_from_clientsecrets('client_secret.json',scope='')
		oauth_flow.redirect_uri = 'postmessage'		
		credentials = oauth_flow.step2_exchange(code)
	except  FlowExchangeError: 
		response = make_response(json.dumps('Failed to upgrade the authorization code '),401)
		response.headers['Content-Type'] = 'application/json'		
		return response 

	access_token = credentials.access_token
	url = ('https://www.gooogleapis.com/oauth2/v1/tokeninfo?access_token=%s'%access_token)
	h = httplib2.Http()
	result = json.loads(h.request(url,'GET')[1])		
	# if error abort 	
	if result.get('error') is not None :
		response = make_response(json.dumps(result.get('error')),50)
		response.headers['Content-Type'] = 'application/json'

	gplus_id = credentials.id_token['sub']
	if result['user_id']!=gplus_id :
		response = make_response (json.dumps('Tokens user id doesnt match given user id '),401)
		response.headers['Content-Type'] = 'application/json'		
		return response 

	# verify access token
	if result['issued_to']!=CLIENT_ID :
		response = make_response(json.dumps("Tokens client id does not match apps  "),401)
		print "Tokens client id does not match apps "		
		response.headers['Content-Type'] = 'application/json'		
		return response 

	# check to see if user is already logged in 
	stored_credentials = login_session.get('credentials')	
	stored_gplus_id = login_session.get('gplus_id')
	if stored_credentials is not None and gplus_id == stored_gplus_id:
		response = make_response(json.dumps('Current user is already connected '),200)		
		response.headers['Content-Type'] = 'application/json'		
	# set access token 
	login_session['credentials']= credentials
	login_session['gplus_id'] = gplus_id

	# get user info 
	userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
	params = {'access_token':credentials.access_token,'alt':'json'}	
	answer = request.get(userinfo_url ,params=params)
	data = json.loads(answer.text)

	login_session['username'] = data['name']
	login_session['picture'] = data['picture']
	login_session['email']=data['email']
	output = ""
	output += '<h1>Welcome, '
	output += login_session['username']
	output += '!</h1>'
	output += '<img src="'
	output += login_session['picture']
	output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
	flash("you are now logged in as %s" % login_session['username'])
	print "done!"
	return output

@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session['access_token']
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: ' 
    print login_session['username']
    if access_token is None:
 	print 'Access Token is None'
    	response = make_response(json.dumps('Current user not connected.'), 401)
    	response.headers['Content-Type'] = 'application/json'
    	return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
	del login_session['access_token'] 
    	del login_session['gplus_id']
    	del login_session['username']
    	del login_session['email']
    	del login_session['picture']
    	response = make_response(json.dumps('Successfully disconnected.'), 200)
    	response.headers['Content-Type'] = 'application/json'
    	return response
    else:
	
    	response = make_response(json.dumps('Failed to revoke token for given user.', 400))
    	response.headers['Content-Type'] = 'application/json'
    	return response


# Show all restaurants
@app.route('/')
@app.route('/restaurant/')
def showRestaurants():
    restaurants = session.query(Restaurant).all()
    return render_template('restaurants.html', restaurants=restaurants)


# @app.route('/')
# @app.route('/restaurants/<int:restaurant_id>/')
# def restaurantMenu(restaurant_id):
#     restaurant = session.query(Restaurant).first()
#     items = session.query(MenuItem).filter_by(restaurant_id=restaurant.id)
#     # output =''
#     # for i in items:
#     # 	output +=i.name
#     # 	output +=i.price
#     # 	output +=i.description
#     # 	output +='</br>'
#     # return output
#     return render_template('menu.html', restaurant=restaurant, items=items)


# Create a new restaurant
@app.route('/restaurant/new/', methods=['GET', 'POST'])
def newRestaurant():
    if request.method == 'POST':
        newRestaurant = Restaurant(name=request.form['name'])
        session.add(newRestaurant)
        session.commit()
        return redirect(url_for('showRestaurants'))
    else:
        return render_template('newRestaurant.html')
    # return "This page will be for making a new restaurant"


@app.route('/restaurant/<int:restaurant_id>/edit/', methods=['GET', 'POST'])
def editRestaurant(restaurant_id):
    editedRestaurant = session.query(
        Restaurant).filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedRestaurant.name = request.form['name']
            return redirect(url_for('showRestaurants'))
    else:
        return render_template(
            'editRestaurant.html', restaurant=editedRestaurant)

    # return 'This page will be for editing restaurant %s' % restaurant_id


# Delete a restaurant


@app.route('/restaurant/<int:restaurant_id>/delete/', methods=['GET', 'POST'])
def deleteRestaurant(restaurant_id):
    restaurantToDelete = session.query(
        Restaurant).filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        session.delete(restaurantToDelete)
        session.commit()
        return redirect(
            url_for('showRestaurants', restaurant_id=restaurant_id))
    else:
        return render_template(
            'deleteRestaurant.html', restaurant=restaurantToDelete)
    # return 'This page will be for deleting restaurant %s' % restaurant_id

    # Show a restaurant menu
@app.route('/restaurant/<int:restaurant_id>/')
@app.route('/restaurant/<int:restaurant_id>/menu/')
def showMenu(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()
    return render_template('menu.html', items=items, restaurant=restaurant)
    # return 'This page is the menu for restaurant %s' % restaurant_id


@app.route('/restaurant/JSON')
def restaurantsJSON():
    restaurants = session.query(Restaurant).all()
    return jsonify(restaurants=[r.serialize for r in restaurants])

@app.route(
    '/restaurant/<int:restaurant_id>/menu/new/', methods=['GET', 'POST'])
def newMenuItem(restaurant_id):
    if request.method == 'POST':
        newItem = MenuItem(name=request.form['name'], description=request.form[
                           'description'], price=request.form['price'], course=request.form['course'], restaurant_id=restaurant_id)
        session.add(newItem)
        session.commit()
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    else:
        return render_template('newmenuitem.html', restaurant_id=restaurant_id)

    # return render_template('newMenuItem.html', restaurant=restaurant)


@app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/edit/', methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
    editedItem = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['price']:
            editedItem.price = request.form['price']
        if request.form['course']:
            editedItem.course = request.form['course']
        session.add(editedItem)
        session.commit()
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    else:
        return render_template('editmenuitem.html', restaurant_id=restaurant_id, menu_id=menu_id, i=editedItem)


@app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/delete', methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
    itemToDelete = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    else:
        return render_template('deletemenuitem.html', i=itemToDelete)

# api endpoint GET


@app.route('/restaurants/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(
        restaurant_id=restaurant_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])

# API endpoint


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
    menuItem = session.query(MenuItem).filter_by(id=menu_id).one()
    return jsonify(MenuItem=menuItem.serialize)

if __name__ == '__main__':
    app.secret_key = "super_secret_key"
    app.debug = True
    app.run(host='', port=8080)
