# Import Library
from time import sleep
import streamlit as st
import tweepy
import sqlite3
from time import sleep
import pandas as pd
import pickle
import requests
import warnings
from util import JSONParser
from streamlit_lottie import st_lottie_spinner
warnings.simplefilter(action='ignore', category=FutureWarning)


log="log:\n"
rem=False
mulai=False
st.set_page_config(
    page_title="Complaint Handler Assistance",
    page_icon="🔄",
    layout="wide",
)

def login(c_key,c_secret, a_key, a_secret):
    auth = tweepy.OAuthHandler(c_key, c_secret)
    auth.set_access_token(a_key, a_secret)
    api = tweepy.API(auth)
    try:
        api.verify_credentials()
        return "Login Succes", api
    except:
        return"Error during authentication", None

# import json parser
jp=JSONParser()
jp.parse("data/intents.json")

# Important Function
## open model pkl
def open_model(model_path):
    with open (model_path, 'rb') as f:
        model = pickle.load(f)
    return model
model=open_model("model_2.pkl")

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
    try:
        pesan=api.get_direct_messages()
        df= pd.DataFrame([[int(s.id), s.created_timestamp, s.message_create['message_data']['text'], s.message_create['target']['recipient_id'], s.message_create['sender_id']] for s in pesan], columns=('ID', 'created at', 'text', 'recipient', 'sender' ))
        return df[df.sender!='492948056']
    except Exception as error:
        print(error)

## check new massage
def cek_response(api, cursor):
    max_id=cursor.execute('SELECT MAX(ID) FROM direct_massage').fetchall()[0][0]
    if max_id==None:max_id=0
    new_massage=get_massage(api)
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
        print(f"Tidak ada pesan")
        return False, None

con = create_connection("twit copy 2.db")
cursor=con.cursor()

def dummy():
    i=0
    print(i)
    i+=1

def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()


def proses():
    got, data= cek_response(api, cursor)
    if got: data.to_sql('direct_massage', con=con, method='multi', if_exists='append', index=False)
    

def ulang():
    global start
    global log
    i=0
    progress=load_lottieurl("https://assets6.lottiefiles.com/packages/lf20_2cnqtinl.json")
    with st_lottie_spinner(progress, key="progress"):
        while start:
            i+=1
            st.empty()
            if i==1: proses()
            if i==62:
                proses()
                i=2
            sleep(1)

st.title("Complaint Handle Assistance")
islogin=False
with st.sidebar:
    st.header("Login here !")
    cunsumer_key=st.text_input("Cunsomer Key :")
    cunsumer_secret=st.text_input("Cunsomer Secret :")
    app_key=st.text_input("App Key :")
    app_secret=st.text_input("App Secret :")
    # submitted = st.button("Login")
    # if submitted:
    massage, api=login(cunsumer_key, cunsumer_secret, app_key, app_secret)
    if api is not None:
        islogin=True 
        st.info(massage)
    else:
        st.warning(massage)
        islogin=False
if islogin:
    name=api.get_settings()["screen_name"]
    # st.markdown(f"""
    # <h4 style="color:#26608e;">User : {name}</h4>
    # """, unsafe_allow_html=True)
    col=st.columns([1,6,6])
    with col[0]:
        st.empty()
        start= st.button("Start")
        if st.button("Stop"):
            start = False
    with col[2]:
        df=pd.read_sql("select text, response from direct_massage Order by ID desc", con)
        df
        # st.text_area("History: ", value=log,  height = 200)
    
    with col[1]:
        if start: 
            ulang()
        else: st.image("assets/proses.png")

    
    
else:
    st.markdown("""
    <h2 style="color:#26608e;">You Must Login First</h2>
    """, unsafe_allow_html=True)
    st.write("If you haven't registered yet, please register at https://developer.twitter.com/ to get the cunsomer key, cunsomer secret, app key, and app secret.")

