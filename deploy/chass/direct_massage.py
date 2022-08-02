import json
from hamcrest import none
import pandas as pd
from random import choice
import streamlit as st
import tweepy
import sqlite3
import pandas as pd
import pickle
import warnings
from util import JSONParser
warnings.simplefilter(action='ignore', category=FutureWarning)

class DirectMassage:
    def __init__(self):
        self.initial=0
        self.API=None
        self.intents = []
        self.responses = {}

    jp=JSONParser()
    jp.parse("data/intents.json")
        
    def login(self, c_key,c_secret, a_key, a_secret):
        auth = tweepy.OAuthHandler(c_key, c_secret)
        auth.set_access_token(a_key, a_secret)
        self.api = tweepy.API(auth)
        try:
            self.api.verify_credentials()
            return "Login Succes", self.api
        except:
            return"Error during authentication", None
    
    def open_model(self, model_path):
        with open (model_path, 'rb') as f:
            self.model = pickle.load(f)
    
    def get_model(self):
        return self.model
        
    def get_api(self):
        return self.api


    ## get response
    def response(self, data, model):
        tag= model.predict(data)
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
        try:
            pesan=self.api.get_direct_messages()
            df= pd.DataFrame([[int(s.id), s.created_timestamp, s.message_create['message_data']['text'], s.message_create['target']['recipient_id'], s.message_create['sender_id']] for s in pesan], columns=('ID', 'created at', 'text', 'recipient', 'sender' ))
            return df[df.sender!='492948056']
        except Exception as error:
            print(error)

    ## check new massage
    def cek_response(self, api, cursor):
        max_id=cursor.execute('SELECT MAX(ID) FROM direct_massage').fetchall()[0][0]
        if max_id==None:max_id=0
        new_massage=get_massage(api)
        if new_massage.ID.max()>max_id:
            massage=new_massage[new_massage.ID>max_id]
            massage['response']=response(massage['text'])
            print(f"Ada {massage.shape[0]} pesan baru")
            for mas in massage.ID:
                try:
                    self.api.send_direct_message(massage[massage.ID==mas].sender[0], massage[massage.ID==mas].response[0])
                except Exception as error:
                    print(error)
            return True, massage
        else:
            print(f"Tidak ada pesan")
            return False, None

    con = create_connection("twit copy 2.db")
    cursor=con.cursor()





##################################################################
    def parse(self, json_path):
        with open(json_path) as data_file:
            self.data = json.load(data_file)

        for intent in self.data['intents']:
            for pattern in intent['patterns']:
                self.chat.append(pattern)
                self.intents.append(intent['tag'])
            for resp in intent['responses']:
                if intent['tag'] in self.responses.keys():
                    self.responses[intent['tag']].append(resp)
                else:
                    self.responses[intent['tag']] = [resp]

        self.df = pd.DataFrame({'chat_input': self.chat,
                                'intents': self.intents})

    def get_dataframe(self):
        return self.df

    def get_response(self, intent):
        return choice(self.responses[intent])