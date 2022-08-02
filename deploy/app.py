#Import Library
import pickle
from flask import Flask, request
from time import sleep
import pickle
import warnings
import pandas as pd
from util import JSONParser
warnings.simplefilter(action='ignore', category=FutureWarning)

app=Flask(__name__)

# Access API
import tweepy

# Authenticate to Twitter
auth = tweepy.OAuthHandler("CkhGa0z1CKMlK7GY56Zxh0250", 
    "Iq1o1IwRzuFw6xCandQbGUX1gzx6GezPD7ek1ptbcw46eni3LB")
auth.set_access_token("492948056-n4H0mlG3efeuJnDKkkoyeW9BWbl7kBrI95Dmlup1", 
    "jMSNiTz1mo764Xnz1x8cEAuu2CQRIhRbstAgRiD5WY7cP")

api = tweepy.API(auth)

try:
    api.verify_credentials()
    print("Authentication OK")
except:
    print("Error during authentication")

# import json parser
jp=JSONParser()
jp.parse("data/intents.json")

# Important Function
# open model pkl
def open_model(model_path):
    with open (model_path, 'rb') as f:
        model = pickle.load(f)
    return model
model=open_model("pipe.pkl")

# get response
def response(data):
    tag=model.predict(data)
    response=[]
    for t in tag:
        response.append(jp.get_response(t))
    return response

# connection database

# grab massage
def get_massage(api):
    pesan=api.get_direct_messages()
    df= pd.DataFrame([[s.id, s.created_timestamp, s.message_create['message_data']['text'], s.message_create['target']['recipient_id'], s.message_create['sender_id']] for s in pesan], columns=('ID', 'created at', 'text', 'recipient', 'sender' ))
    return df[df.sender!='492948056']
# check new massage
def check_new_massage(api):
    old_massage=get_massage(api)
    while True:
        max=old_massage.ID.max()
        new_massage=get_massage(api)
        if new_massage.ID.max()>old_massage.ID.max():
            massage=new_massage[new_massage.ID>max]
            massage['response']=response(massage['text'])
            print(f"Ada {massage.shape[0]} pesan baru")
            old_massage=new_massage
            for mas in massage.ID:
                api.send_direct_message(massage[massage.ID==mas].sender[0], massage[massage.ID==mas].response[0])
        else:
            print("tidak ada pesan baru")
        sleep(65)
# Main Menu
@app.route('/')
def homepage():
    check_new_massage(api)
    # return 'halo'
# run bot

# app.run(debug=True)
    

