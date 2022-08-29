import boto3
import os

def getUser(id, name):
    dynamoDB=boto3.resource('dynamodb',aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'])
    usrTable = dynamoDB.Table('User') 
    return usrTable.get_item(Key={
                'id': id,
                'name': name
    })

def getScore(id, name):
    dynamoDB=boto3.resource('dynamodb',aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'])
    usrTable = dynamoDB.Table('User') 
    return usrTable.get_item(Key={
                'id': id,
                'name': name
    })['Item']['score']

print(getUser('e793419b-17db-4938-a719-db8bcb929225', 'Eric Zhang'))