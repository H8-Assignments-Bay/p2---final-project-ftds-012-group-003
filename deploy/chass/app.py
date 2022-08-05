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
import re
import string
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
warnings.simplefilter(action='ignore', category=FutureWarning)
import warnings
warnings.filterwarnings('ignore') 


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

## Document Preprocessing
def document_processing(document):
    document = document.lower()
    document = document.translate(str.maketrans("","",string.punctuation))
    document = re.sub("[^A-Za-z\s']"," ", document)
    document = re.sub(r'http\S+', '', document) # remove links
    document = re.sub(r"www.\S+", " ", document) # remove link
    document = document.strip()
    stemmer = StemmerFactory().create_stemmer()
    document = stemmer.stem(document)
    return document

#getOTP
def generateOTP() :
    digits = "0123456789"
    OTP = ""
    for i in range(5) :
        OTP += digits[math.floor(random.random() * 10)]
    return OTP

# response if trouble
def response_trouble(teks, phase):
    print(phase)
    if phase==0:
        if teks == '#gantiATM':
            response= """Baik kak aku bantu proses pergantian ATM ya, Sebelumnya ada beberapa syarat yang harus dilengkapi yaitu dengan isi data diri. Pertama silahkan ketikkan data dengan format *Nama, Nomor Rekening, No Handphone, Email*
            """
            return 1, response, 1
        else:
            proba=model.predict_proba([teks])[0]
            if proba.max()<0.25: response="Maaf Kak Saya Tidak Mengerti(from response trouble)"
            else:
                tag=model.predict([teks])[0]
                response=jp.get_response(tag)
                return 0, response, None
    elif phase==1:
        data_nasabah=teks.split(',')
        data_nasabah=[dt.strip() for dt in data_nasabah]
        try:
            print(data_nasabah)
            query=f"select * from nasabah where no_rekening='{data_nasabah[1]}' and nama= '{data_nasabah[0]}' and no_hp='{data_nasabah[2]}' and email='{data_nasabah[3]}'"
            print(query)
            data_f_sql=cursor.execute(query).fetchall()[0]
            otp=generateOTP()
            query_2=f"UPDATE nasabah set otp={otp} WHERE no_rekening='{data_nasabah[1]}'"
            cursor.execute(query_2)
            con.commit()
            response="Kami telah mengirim kode OTP melalui no HP Anda. Silakan balas pesan ini dengan format *no rekening, otp*"
            return 1, response, 2
        except Exception as error:
            print(error, 'response_trouble')
            response='data yang anda masukkan salah, silahkan masukkaan kembali data anda'
            return 1, response, 1
    elif phase==2:
        data_nasabah=teks.split(',')
        data_nasabah=[dt.strip() for dt in data_nasabah]
        try:
            query=f"SELECT * FROM nasabah WHERE no_rekening = '{data_nasabah[0]}' AND otp={data_nasabah[1]}"
            data_f_sql=cursor.execute(query).fetchall()[0]
            response="Selamat kakak akan menerima kartu ATM baru! Tunggu kami ya kak maksimal 3x24 jam kartu ATM baru kakak sampai rumah"
            query_2=f"UPDATE nasabah set otp=null WHERE no_rekening='{data_nasabah[0]}'"
            cursor.execute(query_2)
            con.commit()
            return 0, response, None
        except Exception as error:
            print(error,  'response_trouble')
            response='data yang anda masukkan salah(from response trouble)'
            return 1, response, 2

        
## get response
def response(data):
    data.iloc[:]['text']=data['text'].apply(document_processing)
    resp=[]
    for d in data.values:
        try:
            query=f"""SELECT is_trouble, phase FROM direct_massage 
                                        WHERE 
                                            sender={d[1]} AND
                                            is_trouble=1 AND
                                            ID=(SELECT MAX(ID) FROM direct_massage WHERE sender={d[1]})"""
            q_result=cursor.execute(query).fetchall()[0]
            t, r, phase=response_trouble(d[0],q_result[1])
            resp.append([r, t, phase])
        except Exception as error:
            print(error, '-response')
            proba=model.predict_proba([d[0]])[0]
            if proba.max()<0.2: resp.append(["Maaf Kak Saya Tidak Mengerti(from respons)", False, None])
            else:
                tag=model.predict([d[0]])[0]
                if tag=='ganti ATM':t=1
                else: t= 0
                r=jp.get_response(tag)
                resp.append([r, t, 0])
    print(resp)
    return resp

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
        massage[['response','is_trouble', 'phase']]=response(massage[['text','sender']])
        for mas in massage['ID'].values:
            # print(massage[massage.ID==mas].response.values[0])
            try:
                api.send_direct_message(massage[massage.ID==mas].sender.values[0], massage[massage.ID==mas].response.values[0])
            except Exception as error:
                print(error, '->cek response')
        return True, massage
    else:
        return False, None

con = create_connection("twit copy.db")
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
    if got: 
        data.to_sql('direct_massage', con=con, method='multi', if_exists='append', index=False)
        print(f'Data baru sejumlah {data.shape[0]}')
    else: print("No Massage")
    

def ulang():
    print("start siap")
    global start
    i=0
    progress=load_lottieurl("https://assets6.lottiefiles.com/packages/lf20_2cnqtinl.json")
    with st_lottie_spinner(progress, key="progress", height=135):
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
    massage, api=login(cunsumer_key, cunsumer_secret, app_key, app_secret)
    if api is not None:
        islogin=True 
        st.info(massage)
    else:
        st.warning(massage)
        islogin=False
if islogin:
    name=api.get_settings()["screen_name"]
    col=st.columns([2,6,6])
    with col[0]:
        st.empty()
        start= st.button("Start Chat Boot")
        if st.button("Stop Chat Boot"):
            start = False
    
    with col[1]:
        if start: 
            ulang()
        else: st.image("assets/proses.png")

    df=pd.read_sql("select text, response from direct_massage Order by ID desc", con)
    df
    
else:
    st.markdown("""
    <h2 style="color:#26608e;">You Must Login First</h2>
    """, unsafe_allow_html=True)
    st.write("If you haven't registered yet, please register at https://developer.twitter.com/ to get the cunsomer key, cunsomer secret, app key, and app secret.")

