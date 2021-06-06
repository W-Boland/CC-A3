from flask import Flask, request, render_template, redirect, session, jsonify
from boto3.dynamodb.conditions import Key, Attr
from dotenv import load_dotenv

import boto3
import os
import requests


application = Flask(__name__)
application.secret_key = 'thisisthesecretkey'
load_dotenv()

def auth():
    if session.get('login')== True:
        return True
    else: 
        return False

# Check to see if an image exists 
def is_url_image(image_url):
   image_formats = ("image/png", "image/jpeg", "image/jpg")
   r = requests.head(image_url)
   if r.headers["content-type"] in image_formats:
      return True
   return False

# Create a new user and add to the current table for AWS 
def create_user(email, user_name, password):
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
    table = dynamodb.Table('Login')
    response = table.put_item(
        Item={
            'email': email,
            'user_name': user_name,
            'password': password
        }
    )
    return 

# Retrive the users Profile picture


def sort_function(value):
    return value["rating"]

def query_favs(limit):

    # Connect to the Dynamodb using Boto3
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
    table = dynamodb.Table('Favourites')
    response = table.query(
        KeyConditionExpression=Key('email').eq(session['email']),
    )
    sortedList = sorted(response['Items'], key=sort_function, reverse=True)
    return sortedList[:limit]



def query_drinks():

    # Connect to the Dynamodb using Boto3
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
    table = dynamodb.Table('Drinks')
    response = table.query(
        KeyConditionExpression=Key('email').eq(session['email']),
    )
    return response['Items']


def ingredients_user():
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
    table = dynamodb.Table('Bar')
    response = table.query(
        KeyConditionExpression=Key('email').eq(session['email']),
    )
    return response['Items']

def query_users(email, password=None):
    
    # Connect to the Dynamodb using Boto3
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')

    # Check if a password has been passed in.. 
    if not password:
        table = dynamodb.Table('Login')
        response = table.query(
            KeyConditionExpression=Key('email').eq(email)
        )
    # Otherwise you just want to return all emails 
    else:
        table = dynamodb.Table('Login')
        response = table.query(
            FilterExpression=Attr('password').eq(password),
            KeyConditionExpression=Key('email').eq(email)
        )
    # Return results
    return response['Items']


def removeItem(item):
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
    table = dynamodb.Table('Bar')
    print(item)
    response = table.delete_item(Key={
        'email': session['email'],
        'ingredients': item
    })
    return 

def ingredientlist_query(search):
    # call api to return list of all ingredients 
    parameters = {
        "i": "list"
    }
    response = (requests.get((os.environ.get("API_GATEWAY_ENDPOINT_URL") + '/list'), params=parameters))
    data = response.json()
    return data

def add_ingredient(ingredient):
    ingredientUrl = ingredient.replace(" ","%20")
    # Change for Jager since it has an accent
    if ingredient == "Jagermeister":
        ingredient = "Jägermeister"

    url = "https://www.thecocktaildb.com/images/ingredients/" + ingredientUrl + "-small.png"
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
    table = dynamodb.Table('Bar')
    response = table.put_item(
        Item={
        'email': session['email'],
        'ingredients': ingredient.title(),
        'drink': "true",
        'img': url
    })
    return 

def get_list_ingredients(info):
    ingredients = [] 
    for i in range(15):
        string = 'strIngredient' + str(i+1)
        if info['drinks'][0][string] is None:
            break
        elif info['drinks'][0][string] == '':
            break
        else:
            ingredients.append(info['drinks'][0][string].title())      
    return ingredients 

def get_current_ingredients(drinkIngredients):
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
    ingredient = []
    returnList = []
    table = dynamodb.Table('Bar')
    response = table.query(
        KeyConditionExpression=Key('email').eq(session['email']),
    )

    for items in response['Items']:
        ingredient.append(items['ingredients'])

    for item in drinkIngredients:
        if item in ingredient:
            returnList.append("1")
        else:
            returnList.append("0")
    
    return returnList 


def get_list_measure(info):

    measures = [] 
    for i in range(15):
        string = 'strMeasure' + str(i+1)
        if info['drinks'][0][string] is None:
            break
        elif info['drinks'][0][string] == '':
            break
        else:
            measures.append(info['drinks'][0][string].title())      
    return measures 

# Defualt index 
@application.route('/')
def index():
    if auth():
        response = (requests.get((os.environ.get("API_GATEWAY_ENDPOINT_URL")) + '/popular'))
        json_object = response.json()
        return render_template('home.html', data=json_object)
    else: 
        return redirect('/login')
        
@application.route('/drink/<id>')
def drink(id):
    if auth():
        parameters = {
            "i": id
        }
        response = (requests.get((os.environ.get("API_GATEWAY_ENDPOINT_URL") + '/id'), params=parameters))
        drink_info = response.json()
        listIngredients = get_list_ingredients(drink_info) 
        listmeasure = get_list_measure(drink_info) 
        number = len(listIngredients)
        currentIngredients = get_current_ingredients(listIngredients)

        return render_template('drink.html', 
            drink=drink_info['drinks'][0], 
            ingredients=listIngredients,
            measure=listmeasure,
            number=number,
            currentBarIngredients=currentIngredients
        )
    else: 
        return redirect('/login')

@application.route('/ingredient/<name>')
def ingredient(name):
    if auth():
        parameters = {
            "i": name
        }
        response = (requests.get((os.environ.get("API_GATEWAY_ENDPOINT_URL") + '/ingredient'), params=parameters))
        ingredient_info = response.json()
        return render_template('ingredient.html', ingredient=ingredient_info['ingredients'][0])
    else: 
        return redirect('/login')

@application.route('/login',methods=['POST'])
@application.route('/login')
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check if the Email & Password is Valid
        info = list(query_users(email, password))
        if not info: 
            return render_template('login.html', login='false')
        else: 
            email = info[0]['email']
            userName = info[0]['user_name']  
            session['email'] = email
            session['userName'] = userName
            session['login'] = True
            return redirect('/dashboard')
    else:
        return render_template('login.html')

#Authenticated route 
@application.route('/dashboard')
def dashboard():
    if auth():
        favourites = query_favs(5)
        drinks = query_drinks()
        if not drinks:
            return render_template('dashboard.html', empty="true")
        else:
            drinkName = drinks[0]['name']
            drinkId =  drinks[0]['id']
            drinkImg = drinks[0]['img']
            number = len(drinkId)
            return render_template('dashboard.html', 
                id=drinkId, 
                img=drinkImg, 
                number=number, 
                name=drinkName, 
                favs=favourites
            )
    else: 
        return redirect('/login')

@application.route('/explore')
def explore():
    return render_template('explore.html')


@application.route('/profile',methods=['POST'])
@application.route('/profile')
def profile():
    if auth():
        if request.method == 'POST':
            s3 = boto3.client('s3', region_name='ap-southeast-2')
            img = request.files['file']
            if img:
                filename = session['email'] + ".png"
                img.save(filename)
                s3.upload_file(
                    Bucket = os.environ.get("PROFILE_S3_BUCKET_NAME"),
                    Filename=filename,
                    Key=filename,
                    ExtraArgs={'ACL':'public-read', 'ContentType': 'image/jpeg'}
                )
                os.remove(filename)

        
        email = session['email'].replace("@","%40")
        url = os.environ.get("PROFILE_S3_BUCKET") + email + ".png"

        exists = is_url_image(url)
        print(exists)
        return render_template('profile.html', url=url, img=exists)
    else: 
        return redirect('/login')


@application.route('/404')
def todo():
    return "PAGE NOT COMPLETE"

@application.route('/mybar',methods=['POST'])
@application.route('/mybar')
def mybar():
    if auth():
        ingredientList = None
        if request.method == 'POST':
            if request.form["submit"] == "search":
                ingredientList = ingredientlist_query(request.form['search'])
            elif request.form["submit"] == "add":
                add_ingredient(request.form['ingredient'])
            else:
                removeItem(request.form['submit'])

        ingredients = ingredients_user()
        return render_template('mybar.html', ingredients=ingredients, ingredientList=ingredientList)
    else: 
        redirect('/login')

@application.route('/ingredientInfo', methods=['POST'])
def info():
    name = request.form['ingredient']
    return render_template('ingredientInfo.html', id=name)

@application.route('/logout')
def logout():
    session.pop('login', None)
    session.pop('email', None)
    session.pop('userName', None)
    return redirect('/')

@application.route('/register',methods=['POST'])
@application.route('/register')
def register():
    # check which route we want, with/without POST 
    if request.method == 'POST':
        # Grab that data posted 
        email = request.form['email']
        user_name = request.form['username']
        password = request.form['password']
        # Check if the email exists and if so render page with Email=false 
        info = list(query_users(email))
        # If the list returned is empty then no user otherwise there is a user
        # that contains the same email
        if not info: 
            # add new user into db, redirct to login  
            create_user(email, user_name, password)
            return redirect('/login')
        else:   
            return render_template('register.html',email='true')  

    # if not post then just render normally 
    else:
        return render_template('register.html')

if __name__ == '__main__':
    application.run(debug=True)