# Import Library
# Import Library
from twython import Twython
import sqlite3
from time import sleep
import numpy as np
import requests
import json
import pandas as pd
import io
import pickle
from tqdm import tqdm
import warnings
from util import JSONParser
warnings.simplefilter(action='ignore', category=FutureWarning)
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
## open model pkl
def open_model(model_path):
    with open (model_path, 'rb') as f:
        model = pickle.load(f)
    return model
model=open_model("model/model_2.pkl")
## get response
def response(data):
    tag=model.predict(data)
    response=[]
    for t in tag:
        response.append(jp.get_response(t))
    return response

## connection database
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Exception as e:
        print(e)
    return conn
## grab massage
def get_massage(api):
    pesan=api.get_direct_messages()
    df= pd.DataFrame([[int(s.id), s.created_timestamp, s.message_create['message_data']['text'], s.message_create['target']['recipient_id'], s.message_create['sender_id']] for s in pesan], columns=('ID', 'created at', 'text', 'recipient', 'sender' ))
    return df[df.sender!='492948056']
## check new massage
def cek_response(api, cursor):
    max_id=cursor.execute('SELECT MAX(ID) FROM direct_massage').fetchall()[0][0]
    if max_id==None:max_id=0
    new_massage=get_massage(api)
    # print(new_massage.ID.max().type)
    if new_massage.ID.max()>max_id:
        massage=new_massage[new_massage.ID>max_id]
        massage['response']=response(massage['text'])
        print(f"Ada {massage.shape[0]} pesan baru")
        for mas in massage.ID:
            try:
                api.send_direct_message(massage[massage.ID==mas].sender[0], massage[massage.ID==mas].response[0])
            except Exception as error:
                print(error)
        return True, massage
    else:
        return False, None
        # print("tidak ada pesan baru")
# Main Menu
## Connection Database
con = create_connection("twit copy.db")
cursor=con.cursor()
## run bot