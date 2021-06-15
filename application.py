from flask import Flask, request, render_template, redirect, session, jsonify
from boto3.dynamodb.conditions import Key, Attr
from dotenv import load_dotenv

import boto3
import os
import requests
import datetime
import random 

application = Flask(__name__)
application.secret_key = 'thisisthesecretkey'
STREAM_NAME = "Olands-bevvies"
load_dotenv()

def get_data():
    return {
        'EVENT_TIME': datetime.datetime.now().isoformat(),
        'TICKER': random.choice(['AAPL', 'AMZN', 'MSFT', 'INTC', 'TBV']),
        'PRICE': round(random.random() * 100, 2)}

def generate(stream_name, kinesis_client):
    data = get_data()
    print(data)
    response = kinesis_client.put_record(
        DeliveryStreamName=stream_name,
        Record={
            'Data': json.dumps(data)
        })

    return response


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

def query_saved_drinks():
    # Connect to the Dynamodb using Boto3
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
    table = dynamodb.Table('Saved')
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

def add_ingredient(ingredient, drink):
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
        'drink': drink,
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

def saved_status(id):
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
    table = dynamodb.Table('Saved')
    response = table.query(
        KeyConditionExpression=
            Key('email').eq(session['email']) & Key('drinkId').eq(id)
    )
    if not response['Items']:
        return False
    else:
        return True 


def save_drink(saveState, id, drinkInfo):
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
    table = dynamodb.Table('Saved')

    imgURL = drinkInfo['drinks'][0]['strDrinkThumb']
    name = drinkInfo['drinks'][0]['strDrink']

    if saveState == "save":
        # add this saved drink to db 
        response = table.put_item(
            Item={
            'email': session['email'],
            'drinkId': id,
            'name': name,
            'img': imgURL
        })   
    elif saveState == "unsave":
        # remove this drink from db 
        response = table.delete_item(Key={
            'email': session['email'],
            'drinkId': id,
        })
    return 

# Defualt index 
@application.route('/')
def index():
    if auth():
        response = (requests.get((os.environ.get("API_GATEWAY_ENDPOINT_URL")) + '/popular'))
        json_object = response.json()
        return render_template('home.html', data=json_object)
    else: 
        return redirect('/login')

@application.route('/drink/<id>', methods=['POST'])  
@application.route('/drink/<id>')
def drink(id):
    if auth():
        parameters = {
            "i": id
        }
        response = (requests.get((os.environ.get("API_GATEWAY_ENDPOINT_URL") + '/id'), params=parameters))
        drinkInfo = response.json()
        if request.method == 'POST':
            if request.form.get('save'):
                save_drink("save", id, drinkInfo)
            elif request.form.get('unsave'):
                save_drink("unsave", id, drinkInfo)

        listIngredients = get_list_ingredients(drinkInfo) 
        listmeasure = get_list_measure(drinkInfo) 
        number = len(listIngredients)
        currentIngredients = get_current_ingredients(listIngredients)
        savedStatus = saved_status(id)
        return render_template('drink.html', 
            drink=drinkInfo['drinks'][0], 
            ingredients=listIngredients,
            measure=listmeasure,
            number=number,
            currentBarIngredients=currentIngredients,
            saved=savedStatus
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

        drinkId = None
        drinkImg = None
        number = 0
        drinkName = None
        empty = None
        favourites = None
        savedId = []
        savedImg = []
        savedNumber = 5
        savedName = []
        noneSaved = True

        favourites = query_favs(5)
        drinks = query_drinks()
        savedDrinks = query_saved_drinks()

        if not savedDrinks:
            noneSaved=True
        else:
            noneSaved=False
            drinkName = drinks[0]['name']
            drinkId =  drinks[0]['id']
            drinkImg = drinks[0]['img']
            number = len(drinkId)

            for save in savedDrinks:
                savedId.append(save['drinkId'])
                savedName.append(save['name'])
                savedImg.append(save['img'])

            savedNumber = len(savedId)

        if not drinks:
            empty="true"

        return render_template('dashboard.html', 
            id=drinkId, 
            img=drinkImg, 
            number=number, 
            name=drinkName, 
            empty=empty,
            favs=favourites,
            savedId=savedId,
            savedImg=savedImg,
            savedNumber=savedNumber,
            savedName=savedName,
            noneSaved=noneSaved
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
        drink = "false"
        if request.method == 'POST':
            if request.form["submit"] == "search":
                ingredientList = ingredientlist_query(request.form['search'])
            elif request.form["submit"] == "add":
                if request.form.get("check"):
                    drink = "true"
                add_ingredient(request.form['ingredient'], drink)
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