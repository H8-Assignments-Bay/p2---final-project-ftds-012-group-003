# Import Library
from socket import create_connection
import sqlite3
from time import sleep
import numpy as np
import requests
import json
import pandas as pd
import warnings
import tweepy
warnings.simplefilter(action='ignore', category=FutureWarning)

class ComplainSearch:
    def __init__(self):
        self.initial=0
        self.path_model=''
        self.path_db=''
        self.path_tf_serving=''

    def set_path(self, path_model, path_db, path_tfserving):
        self.path_model=path_model
        self.path_db=path_db
        self.path_tf_serving=path_tfserving
        create_connection()


    def login(self, c_key,c_secret, a_key, a_secret):
        auth = tweepy.OAuthHandler(c_key, c_secret)
        auth.set_access_token(a_key, a_secret)
        self.api = tweepy.API(auth)
        try:
            self.api.verify_credentials()
            print("Login Succes")
            return True
        except:
            print("Error during authentication")
            return False

    def create_connection(self):
        self.conn = None
        try:
            self.conn = sqlite3.connect(self.path_db)
            self.cursor=self.con.cursor()
        except Exception as e:
            print(e)
    
    def get_predict(self, series):
        X=[]
        for con in series.tolist():
            X.append([con])

        input_data_json = json.dumps({
            "signature_name": "serving_default",
            "instances": X,
            })
            
        r=requests.post(self.path_tf_serving, input_data_json)
        result=r.json()
        result= np.argmax(result['predictions'], axis=1)
        return np.where(result==0,'Neutral', np.where(result==1, 'Negative', 'Positive'))
    
    
    def get_tweet(self, query, result_type='recent'):
        max_id=self.cursor.execute('SELECT MAX(ID) FROM tweet').fetchall()[0][0]
        data = self.api.search_tweets(q=query, 
                            result_type=result_type,
                            count=100, 
                            tweet_mode ='extended', 
                            since_id= max_id)
        
        data= pd.DataFrame([[s.id, s.full_text.replace('\n','').replace('\r',''), s.user.screen_name, s.user.id_str, s.user.followers_count, s.retweet_count, s.favorite_count, s.created_at] for s in data], columns=('ID', 'Texts', 'UserName','UserID', "UserFollowerCount", 'RetweetCount', 'Likes', "CreatedAt"))

        if data.shape[0]>0: 
            data['sentimen']=get_predict(data['Texts'])
            for id in data[(data.sentimen=="Negative")&(data.UserID!='1476341100260388867')].ID:
                try:
                    status="Halo kak @"+data[data.ID==id]["UserName"][0]+". maaf atas ketidaknyamanannya. Untuk     informasi lebih lanjut, cek dm ya"
                    self.api.update_status(status, in_reply_to_status_id=id)
                    self.api.send_direct_message(data[data.ID==id]["UserID"][0],"Maaf kak atas kendala yang dihadapi. Bisa diceritakan lebih detail terkait masalah yang kakak hadapi?")
                except Exception as error:
                    print(error)
        return data
        # else: return "tidak ada tweet"
