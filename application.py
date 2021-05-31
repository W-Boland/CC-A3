from flask import Flask, request, render_template, redirect, session
from boto3.dynamodb.conditions import Key, Attr
import boto3

application = Flask(__name__)
application.secret_key = 'thisisthesecretkey'

def auth():
    if session.get('login')== True:
        return True
    else: 
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

# Defualt index 
@application.route('/')
def index():
    if auth():
        return render_template('base.html')
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
            return redirect('/')
    else:
        return render_template('login.html')


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