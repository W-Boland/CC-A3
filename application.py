from flask import Flask, request, render_template
from boto3.dynamodb.conditions import Key, Attr
import boto3

application = Flask(__name__)

def user_subscriptions():
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
    table = dynamodb.Table('Subscription')
    response = table.query(KeyConditionExpression=Key('email').eq("s36569030@student.rmit.edu.au"))
    items = list(response['Items'])
    return items
    

@application.route("/")
def index():
    subs = user_subscriptions()
    return render_template('index.html', subs=subs)


if __name__ == '__main__':
    application.run()