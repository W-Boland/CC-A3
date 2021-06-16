import requests
import boto3
from boto3.dynamodb.conditions import Key, Attr
import json 
def lambda_handler(event, context):   
    print('------------------------')
    print(event)
    #1. Iterate over each record
    try:
        for record in event['Records']:
            #2. Handle event by type
            if record['eventName'] == 'INSERT':
                handle_insert(record)
            elif record['eventName'] == 'MODIFY':
                handle_modify(record)
            elif record['eventName'] == 'REMOVE':
                handle_remove(record)
        print('------------------------')
        return "Success!"
    except Exception as e: 
        print(e)
        print('------------------------')
        return "Error"

def add_to_db(email, drinkId, name, img):
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
    table = dynamodb.Table('Drinks')
    response = table.put_item(
        Item={
            'email': email,
            'id': drinkId,
            'name': name,
            'img': img
        }
    )
    return 

def get_current(email):
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
    table = dynamodb.Table('Bar')
    response = table.query(
        KeyConditionExpression=Key('email').eq(email)
    )
    return response['Items']

def current_drink(email):
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
    table = dynamodb.Table('Drinks')
    response = table.query(
        KeyConditionExpression=Key('email').eq(email)
    )
    return response['Items']

def handle_insert(record):
    newImage = record['dynamodb']['NewImage']
    email = newImage['email']['S']
    ingredient = newImage['ingredients']['S']
    items = get_current(email)
    print(items)
    currentIngredients = [str(ingredient)]
    for item in items:
        currentIngredients.append(str(item['ingredients']))

    response = requests.get("https://www.thecocktaildb.com/api/json/v1/1/filter.php?i=" + str(ingredient))
    json_obj = response.json()

    total = 0 
    add = []
    name = []
    img = []
    for drinks in json_obj['drinks']:
        id = drinks['idDrink']
        drink = requests.get("https://www.thecocktaildb.com/api/json/v1/1/lookup.php?i=" + id).json()

        ing = [] 
        for i in range(10):
            string = 'strIngredient' + str(i+1)
            if drink['drinks'][0][string] is None:
                continue
            elif drink['drinks'][0][string] == '':
                continue
            else:
                ing.append((drink['drinks'][0][string]).title())

        if set(ing).issubset(currentIngredients):
            add.append(drink['drinks'][0]['idDrink'])
            name.append(drink['drinks'][0]['strDrink'])
            img.append(drink['drinks'][0]['strDrinkThumb'])

    currentDrinks = current_drink(email)

    if not currentDrinks: 
        add_to_db(email, add, name, img)
    else:
        currentId = currentDrinks[0]['id']
        currentName = currentDrinks[0]['name']
        currentImg = currentDrinks[0]['img']
        updateId = currentId + list(set(add) - set(currentId))
        updateName = currentName + list(set(name) - set(currentName))
        updateImg = currentImg + list(set(img) - set(currentImg))
        add_to_db(email, updateId, updateName, updateImg)

    print("Done handling INSERT Event")


def handle_modify(record):
	print("Done handling MODIFY Event")

def handle_remove(record):
	print("Done handling REMOVE Event")