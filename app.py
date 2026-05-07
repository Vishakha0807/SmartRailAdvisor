# ============================================
# SMART RAIL ADVISOR — app_trial.py
# New Interface with Train Animation
# ============================================

import os
import joblib
import sqlite3
import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
from math import ceil
import plotly.graph_objects as go
import calendar
import time

os.chdir(r'C:\Users\HP\SmartRailAdvisor')

# ══════════════════════════════════════
# PAGE CONFIG — MUST BE FIRST
# ══════════════════════════════════════
st.set_page_config(
    page_title="Smart Rail Advisor",
    page_icon ="🚂",
    layout    ="wide",
    initial_sidebar_state="collapsed")

# ══════════════════════════════════════
# CSS
# ══════════════════════════════════════
st.markdown("""
<style>
#MainMenu{visibility:hidden}
footer{visibility:hidden}
header{visibility:hidden}

/* Buttons */
.stButton>button{
    background:linear-gradient(
        135deg,#4f46e5,#7c3aed);
    color:white;border:none;
    border-radius:12px;
    font-weight:700;
    padding:14px 24px;
    width:100%;font-size:16px;
    transition:all 0.3s ease;}
.stButton>button:hover{
    transform:translateY(-2px);
    box-shadow:0 8px 20px
    rgba(79,70,229,0.4);}

/* Tabs */
.stTabs [data-baseweb="tab"]{
    font-weight:600;font-size:13px;}

/* Train animation keyframes */
@keyframes chug {
    0%  {transform:translateX(0px);}
    25% {transform:translateX(8px);}
    50% {transform:translateX(0px);}
    75% {transform:translateX(-8px);}
    100%{transform:translateX(0px);}
}
@keyframes smoke {
    0%  {opacity:1;transform:
         translateY(0px) scale(1);}
    100%{opacity:0;transform:
         translateY(-30px) scale(2);}
}
@keyframes track {
    0%  {background-position:0px 0px;}
    100%{background-position:
         -60px 0px;}
}
@keyframes fadeIn {
    from{opacity:0;
         transform:translateY(20px);}
    to  {opacity:1;
         transform:translateY(0px);}
}
@keyframes blink {
    0%,100%{opacity:0.3;}
    50%    {opacity:1;}
}
@keyframes slide-right {
    0%  {transform:translateX(-100vw);}
    100%{transform:translateX(100vw);}
}
</style>
""",unsafe_allow_html=True)

# ══════════════════════════════════════
# LOAD MODELS
# ══════════════════════════════════════
@st.cache_resource
def load_models():
    m = {}
    try:
        m['fare'] = joblib.load(
            'fare_model.pkl')
    except:
        st.error("fare_model.pkl missing!")
        st.stop()
    try:
        m['waitlist'] = joblib.load(
            'waitlist_model.pkl')
    except:
        st.error(
            "waitlist_model.pkl missing!")
        st.stop()
    try:
        m['crowd'] = joblib.load(
            'overcrowding_model.pkl')
    except:
        st.error(
            "overcrowding_model.pkl missing!")
        st.stop()
    try:
        m['delay'] = joblib.load(
            'delay_model.pkl')
    except:
        st.error(
            "delay_model.pkl missing!")
        st.stop()
    return m

models = load_models()

# ══════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════
festival_map = {
    'Normal':0,'Summer':1,'Holi':2,
    'Independence':3,'Diwali':4,
    'Christmas':5,'New Year':6,
    'Post-Diwali':6
}
class_map  = {'SL':0,'3A':1,'2A':2,'1A':3}
crowd_back = {0:'Low',1:'Medium',2:'High'}

MONTH_FESTIVAL = {
    1:'New Year',2:'Normal',3:'Holi',
    4:'Normal',5:'Summer',6:'Summer',
    7:'Normal',8:'Independence',
    9:'Normal',10:'Diwali',
    11:'Post-Diwali',12:'Christmas'
}
FESTIVAL_SURGE = {
    'Normal':0,'New Year':15,'Holi':28,
    'Independence':10,'Diwali':67,
    'Christmas':20,'Summer':35,
    'Post-Diwali':30
}
TRAIN_BASE_DELAY = {
    'Rajdhani':12,'Duronto':18,
    'Shatabdi':15,'Superfast':28,
    'Express':42,'Passenger':75
}
TRAIN_PUNCTUALITY = {
    'Rajdhani':0.88,'Duronto':0.82,
    'Shatabdi':0.85,'Superfast':0.70,
    'Express':0.58,'Passenger':0.35
}
ROUTE_BASE_DELAY = {
    ('Nagpur','Mumbai Central')  :35,
    ('Mumbai Central','Nagpur')  :35,
    ('Nagpur','New Delhi')       :45,
    ('New Delhi','Nagpur')       :45,
    ('Mumbai Central','New Delhi'):50,
    ('New Delhi','Mumbai Central'):50,
    ('New Delhi','Kolkata')      :55,
    ('Kolkata','New Delhi')      :55,
    ('Chennai Central','Bangalore'):25,
    ('Bangalore','Chennai Central'):25,
}
FESTIVAL_DELAY = {
    'Diwali':2.1,'Summer':1.6,
    'Holi':1.4,'Christmas':1.3,
    'New Year':1.2,'Independence':1.1,
    'Normal':1.0,'Post-Diwali':1.3
}
TIME_FACTOR = {
    'Early Morning':0.70,
    'Morning'      :0.85,
    'Afternoon'    :1.00,
    'Evening'      :1.30,
    'Night'        :1.15,
    'Late Night'   :1.25
}
SEASON_FACTORS = {
    'offseason':1.00,'normal':0.90,
    'weekend'  :0.75,'summer':0.55,
    'festival' :0.35
}
WL_CHANCES = {
    (1,3):0.92,(4,7):0.75,
    (8,12):0.58,(13,20):0.35,
    (21,35):0.20,(36,99):0.10
}

# ══════════════════════════════════════
# CITIES
# ══════════════════════════════════════
CITIES = sorted(list(set([
    'Mumbai Central','Mumbai CST',
    'Pune','Nagpur','Nashik',
    'Aurangabad','Solapur','Kolhapur',
    'Amravati','Nanded','Latur',
    'Akola','Jalgaon','Chandrapur',
    'Wardha','Dhule','Yavatmal',
    'New Delhi','Delhi Junction',
    'Hazrat Nizamuddin','Gurgaon',
    'Faridabad','Ghaziabad',
    'Lucknow','Varanasi','Agra',
    'Kanpur','Prayagraj','Mathura',
    'Meerut','Bareilly','Moradabad',
    'Gorakhpur','Jhansi','Aligarh',
    'Jaipur','Jodhpur','Udaipur',
    'Kota','Ajmer','Bikaner',
    'Ahmedabad','Surat','Vadodara',
    'Rajkot','Bhavnagar','Jamnagar',
    'Bhopal','Indore','Jabalpur',
    'Gwalior','Ujjain','Sagar',
    'Rewa','Satna','Ratlam',
    'Bangalore','Mysore','Hubli',
    'Mangalore','Belgaum','Davangere',
    'Chennai Central','Chennai Egmore',
    'Coimbatore','Madurai','Trichy',
    'Salem','Tirunelveli','Vellore',
    'Hyderabad','Secunderabad',
    'Visakhapatnam','Vijayawada',
    'Warangal','Guntur','Nellore',
    'Tirupati','Nizamabad',
    'Kochi','Thiruvananthapuram',
    'Kozhikode','Thrissur','Kollam',
    'Kannur','Palakkad',
    'Kolkata','Howrah','Siliguri',
    'Asansol','Durgapur','Kharagpur',
    'Patna','Gaya','Muzaffarpur',
    'Bhagalpur','Darbhanga',
    'Ranchi','Jamshedpur','Dhanbad',
    'Bokaro','Hazaribagh',
    'Bhubaneswar','Cuttack','Rourkela',
    'Berhampur','Sambalpur','Puri',
    'Guwahati','Dibrugarh','Silchar',
    'Amritsar','Ludhiana','Jalandhar',
    'Patiala','Bathinda','Pathankot',
    'Chandigarh','Shimla','Dehradun',
    'Haridwar','Rishikesh',
    'Raipur','Bilaspur','Durg',
    'Goa','Margao','Vasco da Gama',
    'Jammu','Udhampur',
    'Shirdi','Vrindavan',
    'Bodh Gaya','Dwarka',
    'Rameswaram','Tirupati',
])))

# ══════════════════════════════════════
# DISTANCES
# ══════════════════════════════════════
CITY_DISTANCES = {
    'Nagpur-Mumbai Central'      :837,
    'Nagpur-New Delhi'           :1092,
    'Nagpur-Pune'                :598,
    'Nagpur-Hyderabad'           :503,
    'Nagpur-Chennai Central'     :1068,
    'Nagpur-Kolkata'             :1066,
    'Nagpur-Bangalore'           :1050,
    'Nagpur-Bhopal'              :357,
    'Nagpur-Jabalpur'            :295,
    'Nagpur-Raipur'              :298,
    'Nagpur-Wardha'              :79,
    'Nagpur-Amravati'            :156,
    'Nagpur-Akola'               :247,
    'Mumbai Central-New Delhi'   :1384,
    'Mumbai Central-Kolkata'     :1968,
    'Mumbai Central-Bangalore'   :981,
    'Mumbai Central-Chennai Central':1279,
    'Mumbai Central-Ahmedabad'   :493,
    'Mumbai Central-Pune'        :192,
    'Mumbai Central-Goa'         :588,
    'Mumbai Central-Hyderabad'   :711,
    'Mumbai Central-Surat'       :263,
    'Mumbai Central-Nashik'      :167,
    'New Delhi-Kolkata'          :1453,
    'New Delhi-Chennai Central'  :2175,
    'New Delhi-Bangalore'        :2150,
    'New Delhi-Hyderabad'        :1563,
    'New Delhi-Amritsar'         :449,
    'New Delhi-Jaipur'           :303,
    'New Delhi-Lucknow'          :511,
    'New Delhi-Varanasi'         :764,
    'New Delhi-Dehradun'         :302,
    'New Delhi-Chandigarh'       :245,
    'New Delhi-Agra'             :195,
    'New Delhi-Patna'            :995,
    'New Delhi-Bhopal'           :706,
    'Kolkata-Chennai Central'    :1659,
    'Kolkata-Hyderabad'          :1181,
    'Kolkata-Bhubaneswar'        :441,
    'Kolkata-Ranchi'             :384,
    'Kolkata-Patna'              :531,
    'Kolkata-Guwahati'           :982,
    'Chennai Central-Bangalore'  :362,
    'Chennai Central-Hyderabad'  :626,
    'Chennai Central-Kochi'      :648,
    'Chennai Central-Coimbatore' :496,
    'Chennai Central-Madurai'    :462,
    'Chennai Central-Tirupati'   :148,
    'Bangalore-Hyderabad'        :569,
    'Bangalore-Goa'              :582,
    'Bangalore-Kochi'            :572,
    'Bangalore-Mysore'           :139,
    'Bangalore-Mangalore'        :352,
    'Hyderabad-Visakhapatnam'    :621,
    'Hyderabad-Vijayawada'       :274,
    'Hyderabad-Warangal'         :148,
    'Pune-Goa'                   :452,
    'Pune-Hyderabad'             :556,
    'Pune-Nashik'                :211,
    'Lucknow-Varanasi'           :286,
    'Lucknow-Patna'              :572,
    'Lucknow-Gorakhpur'          :269,
    'Lucknow-Kanpur'             :75,
    'Jaipur-Ahmedabad'           :572,
    'Jaipur-Jodhpur'             :316,
    'Jaipur-Udaipur'             :396,
    'Jaipur-Ajmer'               :132,
    'Ahmedabad-Surat'            :265,
    'Ahmedabad-Vadodara'         :100,
    'Ahmedabad-Rajkot'           :216,
    'Patna-Gaya'                 :100,
    'Patna-Muzaffarpur'          :75,
    'Patna-Varanasi'             :228,
    'Patna-Ranchi'               :346,
    'Bhopal-Indore'              :187,
    'Bhopal-Jabalpur'            :295,
    'Bhopal-Gwalior'             :423,
    'Guwahati-Dibrugarh'         :439,
    'Guwahati-Kolkata'           :982,
    'Kochi-Thiruvananthapuram'   :220,
    'Kochi-Kozhikode'            :190,
    'Bhubaneswar-Cuttack'        :28,
    'Bhubaneswar-Puri'           :60,
    'Amritsar-Ludhiana'          :133,
    'Amritsar-New Delhi'         :449,
    'Raipur-Bilaspur'            :130,
    'Raipur-Nagpur'              :298,
    'Ranchi-Jamshedpur'          :130,
    'Ranchi-Dhanbad'             :164,
    'Goa-Mumbai Central'         :588,
    'Haridwar-New Delhi'         :214,
    'Haridwar-Dehradun'          :54,
    'Varanasi-Prayagraj'         :128,
    'Varanasi-Gorakhpur'         :230,
    'Tirupati-Chennai Central'   :148,
    'Tirupati-Bangalore'         :257,
}

def get_distance(a,b):
    k1=f"{a}-{b}"; k2=f"{b}-{a}"
    if k1 in CITY_DISTANCES:
        return CITY_DISTANCES[k1]
    elif k2 in CITY_DISTANCES:
        return CITY_DISTANCES[k2]
    REGIONS = {
        'North':['New Delhi','Chandigarh',
            'Amritsar','Dehradun',
            'Haridwar','Agra'],
        'South':['Chennai Central',
            'Bangalore','Hyderabad',
            'Kochi','Coimbatore',
            'Madurai'],
        'East' :['Kolkata','Howrah',
            'Patna','Ranchi',
            'Bhubaneswar','Guwahati'],
        'West' :['Mumbai Central',
            'Pune','Ahmedabad',
            'Surat','Goa'],
        'Central':['Nagpur','Bhopal',
            'Indore','Raipur']
    }
    def reg(c):
        for r,cs in REGIONS.items():
            if c in cs: return r
        return 'Central'
    r1=reg(a); r2=reg(b)
    if r1==r2: return 300
    elif set([r1,r2])==\
         set(['North','South']):
        return 2000
    elif set([r1,r2])==\
         set(['East','West']):
        return 1800
    elif 'Central' in [r1,r2]:
        return 800
    else: return 1000

# ══════════════════════════════════════
# ML FUNCTIONS
# ══════════════════════════════════════
def make_fare_inp(d,c,f,l,m):
    return pd.DataFrame({
        'from_station':[0],
        'to_station'  :[0],
        'distance_km' :[d],
        'travel_class':[class_map[c]],
        'travel_date' :[0],
        'month'       :[m],
        'festival'    :[festival_map[f]],
        'lead_days'   :[l],
        'waitlist_no' :[5],
        'confirmed'   :[0],
        'crowd_level' :[1]
    })

def make_wl_inp(d,c,f,l,m):
    return pd.DataFrame({
        'from_station':[0],
        'to_station'  :[0],
        'distance_km' :[d],
        'travel_class':[class_map[c]],
        'travel_date' :[0],
        'month'       :[m],
        'festival'    :[festival_map[f]],
        'lead_days'   :[l],
        'waitlist_no' :[5],
        'fare'        :[500],
        'crowd_level' :[1]
    })

def make_crowd_inp(d,c,f,l,m):
    return pd.DataFrame({
        'from_station':[0],
        'to_station'  :[0],
        'distance_km' :[d],
        'travel_class':[class_map[c]],
        'travel_date' :[0],
        'month'       :[m],
        'festival'    :[festival_map[f]],
        'lead_days'   :[l],
        'waitlist_no' :[5],
        'fare'        :[500],
        'confirmed'   :[0]
    })

def predict_fare(d,c,f,l,m):
    return round(float(
        models['fare'].predict(
            make_fare_inp(d,c,f,l,m)
        )[0]),2)

def predict_conf(d,c,f,l,m):
    p=models['waitlist']\
      .predict_proba(
          make_wl_inp(d,c,f,l,m))[0]
    return round(float(p[1])*100,1)

def predict_crowd(d,c,f,l,m):
    p=models['crowd'].predict(
        make_crowd_inp(d,c,f,l,m))[0]
    return crowd_back[p]

def calc_delay(fs,ts,fest,tt,tslot):
    rb=ROUTE_BASE_DELAY.get((fs,ts),40)
    ff=FESTIVAL_DELAY.get(fest,1.0)
    tf=TIME_FACTOR[tslot]
    trf=TRAIN_BASE_DELAY[tt]/40
    delay=round(rb*ff*tf*trf,1)
    ontime=TRAIN_PUNCTUALITY[tt]*100
    ontime=round(max(10,min(95,
        ontime*(1/tf))),1)
    return delay,ontime

def comfort_score(crowd,conf,
                  delay,cls,fest):
    s=100
    if crowd=='High': s-=30
    if crowd=='Medium': s-=15
    if conf<50: s-=20
    if conf<70: s-=10
    if delay>60: s-=20
    if delay>30: s-=10
    if fest!='Normal': s-=10
    if cls=='1A': s+=10
    if cls=='SL': s-=10
    return max(0,min(100,s))

def best_train(crowd,conf,delay):
    if delay<=20 and crowd!='High':
        return 'Rajdhani','88% on-time'
    elif conf<60:
        return 'Duronto',\
               'Better availability'
    elif crowd=='High':
        return 'Shatabdi','85% on-time'
    else:
        return 'Express','Economical'

def get_lead_factor(ld):
    if ld>=60: return 1.00
    elif ld>=30: return 0.82
    elif ld>=15: return 0.58
    elif ld>=7 : return 0.38
    else: return 0.14

def get_wl_chance(wl):
    for (lo,hi),c in WL_CHANCES.items():
        if lo<=wl<=hi: return c
    return 0.10

def get_status(pos,season,ld):
    sf=SEASON_FACTORS[season]
    lf=get_lead_factor(ld)
    base=sf*lf
    pen=max(0,(pos-1)*0.03)
    final=base-pen
    if final>=0.70:
        return 'CNF',100
    elif final>=0.50:
        wn=int((0.70-final)*15)+1
        return f'RAC/{wn}',\
            int(get_wl_chance(wn)*100)
    elif final>=0.25:
        wn=int((0.50-final)*30)+1
        return f'WL/{wn}',\
            int(get_wl_chance(wn)*100)
    else:
        wn=int((0.50-final)*50)+10
        return f'WL/{wn}',\
            int(get_wl_chance(
                min(wn,99))*100)

def get_group_fare(dist,cls,
                   season,ld,month):
    fm={'offseason':'Normal',
        'normal':'Normal',
        'weekend':'Normal',
        'summer':'Summer',
        'festival':'Diwali'}
    return predict_fare(
        dist,cls,fm[season],ld,month)

# ══════════════════════════════════════
# DATABASE
# ══════════════════════════════════════
def init_db():
    conn=sqlite3.connect('rail_advisor.db')
    c=conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS
        searches(
            id INTEGER PRIMARY KEY,
            from_station TEXT,
            to_station TEXT,
            travel_date TEXT,
            travel_class TEXT,
            fare REAL,
            confirmation REAL,
            crowd TEXT,
            comfort_score INTEGER,
            searched_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit(); conn.close()

def save_search(fs,ts,td,cls,
                fare,conf,crowd,score):
    try:
        conn=sqlite3.connect(
            'rail_advisor.db')
        c=conn.cursor()
        c.execute("""
            INSERT INTO searches
            (from_station,to_station,
             travel_date,travel_class,
             fare,confirmation,
             crowd,comfort_score)
            VALUES(?,?,?,?,?,?,?,?)
        """,(fs,ts,str(td),cls,
             fare,conf,crowd,score))
        conn.commit(); conn.close()
    except: pass

init_db()

# ══════════════════════════════════════
# PDF GENERATOR
# ══════════════════════════════════════
def make_solo_pdf(data):
    from fpdf import FPDF
    import tempfile
    pdf=FPDF()
    pdf.add_page()

    # Dark header
    pdf.set_fill_color(15,23,42)
    pdf.rect(0,0,210,40,'F')
    pdf.set_text_color(255,255,255)
    pdf.set_font('Helvetica','B',20)
    pdf.set_xy(10,8)
    pdf.cell(0,10,'SMART RAIL ADVISOR',
             ln=True)
    pdf.set_font('Helvetica','',10)
    pdf.set_xy(10,22)
    pdf.cell(0,8,'Solo Journey Report - AI ML Railway Intelligence',
             ln=True)

    pdf.set_text_color(0,0,0)
    pdf.set_xy(10,48)
    pdf.set_font('Helvetica','B',14)
    pdf.cell(0,8,
        f"Route: {data['fs']}  to  {data['ts']}",
        ln=True)
    pdf.set_font('Helvetica','',11)
    pdf.set_xy(10,58)
    pdf.cell(0,7,
        f"Date: {data['td'].strftime('%d %B %Y')}"
        f"  |  Class: {data['cls']}"
        f"  |  Train: {data['tt']}"
        f"  |  Distance: {data['dist']} km",
        ln=True)

    pdf.line(10,70,200,70)
    pdf.set_xy(10,74)
    pdf.set_font('Helvetica','B',12)
    pdf.cell(0,8,'AI Predictions',ln=True)
    pdf.set_font('Helvetica','',11)

    rows=[
        ('Predicted Fare',
         f"Rs. {data['fare']:,.0f}"),
        ('Confirmation Chance',
         f"{data['conf']:.1f}%"),
        ('Expected Crowd',data['crowd']),
        ('Expected Delay',
         f"{data['delay']} min"),
        ('On-Time Probability',
         f"{data['ontime']}%"),
        ('Festival',
         f"{data['fest']} (+{data['surge']}%)"),
        ('Comfort Score',
         f"{data['score']} / 100"),
        ('Best Train',data['bt']),
    ]
    y=84
    for lbl,val in rows:
        pdf.set_xy(10,y)
        pdf.set_font('Helvetica','B',10)
        pdf.cell(75,7,f"{lbl}:")
        pdf.set_font('Helvetica','',10)
        pdf.cell(0,7,val,ln=True)
        y+=8

    pdf.line(10,y+2,200,y+2)
    pdf.set_xy(10,y+6)
    pdf.set_font('Helvetica','B',12)
    pdf.cell(0,8,'Recommendation',ln=True)
    pdf.set_font('Helvetica','',10)
    y+=16
    if data['conf']>=70 and \
       data['surge']<=25 and \
       data['delay']<=30:
        rec="BOOK NOW! Good fare, high confirmation, low delay. Best time to book!"
    elif data['surge']>50:
        rec=f"CHANGE DATE! {data['fest']} surge +{data['surge']}%. Travel before or after festival to save money."
    elif data['conf']<50:
        rec=f"BOOK WITH CAUTION! Only {data['conf']:.1f}% confirmation. Consider {data['bt']} for better chances."
    else:
        rec=f"GOOD TO GO! Book {data['ld']} days in advance for best fare of Rs.{data['fare']:,.0f}."
    pdf.set_xy(10,y)
    pdf.multi_cell(0,7,rec)

    pdf.set_xy(10,272)
    pdf.set_font('Helvetica','I',8)
    pdf.set_text_color(128,128,128)
    pdf.cell(0,5,
        f"Smart Rail Advisor  |  "
        f"MCA Final Year Project  |  "
        f"Generated: "
        f"{date.today().strftime('%d %B %Y')}",
        align='C')

    with tempfile.NamedTemporaryFile(
        delete=False,suffix='.pdf') as t:
        pdf.output(t.name)
        tmp=t.name
    with open(tmp,'rb') as f:
        return f.read()

def make_group_pdf(data):
    from fpdf import FPDF
    import tempfile
    pdf=FPDF()
    pdf.add_page()

    pdf.set_fill_color(6,78,59)
    pdf.rect(0,0,210,40,'F')
    pdf.set_text_color(255,255,255)
    pdf.set_font('Helvetica','B',20)
    pdf.set_xy(10,8)
    pdf.cell(0,10,'SMART RAIL ADVISOR',
             ln=True)
    pdf.set_font('Helvetica','',10)
    pdf.set_xy(10,22)
    pdf.cell(0,8,'Group Travel Report - AI ML Railway Intelligence',
             ln=True)

    pdf.set_text_color(0,0,0)
    pdf.set_xy(10,48)
    pdf.set_font('Helvetica','B',14)
    pdf.cell(0,8,
        f"Route: {data['from_st']}"
        f"  to  {data['to_st']}",ln=True)
    pdf.set_font('Helvetica','',11)
    pdf.set_xy(10,58)
    pdf.cell(0,7,
        f"Date: "
        f"{data['travel_date'].strftime('%d %B %Y')}"
        f"  |  Distance: {data['distance']} km"
        f"  |  Class: {data['g_class']}",
        ln=True)

    pdf.line(10,70,200,70)
    pdf.set_xy(10,74)
    pdf.set_font('Helvetica','B',12)
    pdf.cell(0,8,'Group Summary',ln=True)
    pdf.set_font('Helvetica','',11)

    rows2=[
        ('Total Passengers',
         str(int(data['n']))),
        ('Total Group Fare',
         f"Rs. {data['total_fare']:,.0f}"),
        ('Per Person (avg)',
         f"Rs. {data['total_fare']/data['n']:,.0f}"),
        ('Confirmed',
         f"{data['cnf_count']}/{int(data['n'])}"),
        ('At Risk (WL/RAC)',
         f"{data['wl_count']+data['rac_count']}"
         f"/{int(data['n'])}"),
        ('Season',data['g_season']),
        ('Lead Time',
         f"{data['g_lead']} days"),
    ]
    y=84
    for lbl,val in rows2:
        pdf.set_xy(10,y)
        pdf.set_font('Helvetica','B',10)
        pdf.cell(75,7,f"{lbl}:")
        pdf.set_font('Helvetica','',10)
        pdf.cell(0,7,val,ln=True)
        y+=8

    pdf.line(10,y+2,200,y+2)
    pdf.set_xy(10,y+6)
    pdf.set_font('Helvetica','B',12)
    pdf.cell(0,8,'Passenger Status',ln=True)
    pdf.set_font('Helvetica','',10)
    y+=16
    for s in data['statuses']:
        pdf.set_xy(10,y)
        pdf.cell(0,7,
            f"{s['name']} ({s['type']})"
            f"   -   {s['status']}"
            f"  ({s['chance']}% chance)",
            ln=True)
        y+=7
        if y>260: break

    pdf.set_xy(10,272)
    pdf.set_font('Helvetica','I',8)
    pdf.set_text_color(128,128,128)
    pdf.cell(0,5,
        f"Smart Rail Advisor  |  "
        f"MCA Final Year Project  |  "
        f"Generated: "
        f"{date.today().strftime('%d %B %Y')}",
        align='C')

    with tempfile.NamedTemporaryFile(
        delete=False,suffix='.pdf') as t:
        pdf.output(t.name)
        tmp=t.name
    with open(tmp,'rb') as f:
        return f.read()

# ══════════════════════════════════════
# TRAIN ANIMATION SCREEN
# ══════════════════════════════════════
def show_splash():
    splash=st.empty()
    splash.markdown("""
<div style="
    position:fixed;top:0;left:0;
    width:100vw;height:100vh;
    background:linear-gradient(
        135deg,#0f0c29,#302b63,
        #24243e);
    display:flex;flex-direction:column;
    align-items:center;
    justify-content:center;
    z-index:9999;">

    <div style="
        font-size:28px;
        font-weight:900;
        color:white;
        letter-spacing:4px;
        margin-bottom:8px;">
        🚂 SMART RAIL ADVISOR
    </div>

    <div style="
        color:#a5b4fc;
        font-size:14px;
        letter-spacing:2px;
        margin-bottom:60px;">
        AI · ML · RAILWAY INTELLIGENCE
    </div>

    <div style="
        width:80vw;
        max-width:600px;
        position:relative;
        height:80px;">

        <!-- Track -->
        <div style="
            position:absolute;
            bottom:10px;left:0;
            width:100%;height:6px;
            background:repeating-linear-gradient(
                90deg,
                #475569 0px,#475569 20px,
                transparent 20px,
                transparent 30px);
            border-radius:3px;">
        </div>

        <!-- Train moving across -->
        <div style="
            position:absolute;
            bottom:14px;
            font-size:52px;
            animation:slide-right 2s
            linear forwards;">
            🚂
        </div>
    </div>

    <div style="
        color:#c7d2fe;
        font-size:16px;
        margin-top:20px;
        animation:blink 1s
        ease-in-out infinite;">
        Loading your journey planner...
    </div>
</div>
""",unsafe_allow_html=True)
    time.sleep(2.5)
    splash.empty()

# ══════════════════════════════════════
# TRAIN LOADING (for analysis)
# ══════════════════════════════════════
def train_loading(msg="Analyzing..."):
    return st.markdown(f"""
<div style="
    background:linear-gradient(
        135deg,#0f0c29,#302b63);
    border-radius:20px;
    padding:40px 20px;
    text-align:center;
    margin:16px 0;">
    <div style="
        font-size:52px;
        display:inline-block;
        animation:chug 0.6s
        ease-in-out infinite;">
        🚂
    </div>
    <div style="
        background:#334155;
        height:6px;
        border-radius:3px;
        margin:20px 40px;
        overflow:hidden;">
        <div style="
            height:100%;width:40%;
            background:linear-gradient(
                90deg,transparent,
                #a5b4fc,white,
                #a5b4fc,transparent);
            animation:slide-right 1s
            linear infinite;">
        </div>
    </div>
    <div style="
        color:white;
        font-size:18px;
        font-weight:700;">
        {msg}
    </div>
    <div style="
        color:#a5b4fc;
        font-size:22px;
        letter-spacing:8px;
        margin-top:8px;
        animation:blink 0.8s
        ease-in-out infinite;">
        · · · · ·
    </div>
    <div style="
        color:#64748b;
        font-size:12px;
        margin-top:6px;">
        Running 9 AI Models
    </div>
</div>""",unsafe_allow_html=True)

# ══════════════════════════════════════
# LOCKED TAB
# ══════════════════════════════════════
def show_locked(title,sub,
                color,bg,icon):
    st.markdown(f"""
<div style="
    background:{bg};
    border:2px solid {color};
    border-radius:16px;
    padding:48px 24px;
    text-align:center;
    margin:24px 0;">
    <div style="font-size:56px;">
        {icon}</div>
    <div style="
        font-size:22px;
        font-weight:800;
        color:{color};
        margin-top:16px;">
        {title}</div>
    <div style="
        color:#64748b;
        font-size:14px;
        margin-top:8px;">
        {sub}</div>
</div>""",unsafe_allow_html=True)

# ══════════════════════════════════════
# NAVBAR
# ══════════════════════════════════════
def show_navbar(mode=None):
    mode_badge=""
    if mode=='solo':
        mode_badge="""
<div style="
    background:#4f46e5;
    color:white;
    border-radius:20px;
    padding:4px 16px;
    font-size:13px;
    font-weight:700;">
    👤 Solo Mode
</div>"""
    elif mode=='group':
        mode_badge="""
<div style="
    background:#059669;
    color:white;
    border-radius:20px;
    padding:4px 16px;
    font-size:13px;
    font-weight:700;">
    👥 Group Mode
</div>"""
    st.markdown(f"""
<div style="
    background:#0f172a;
    padding:14px 24px;
    border-radius:14px;
    margin-bottom:20px;
    display:flex;
    align-items:center;
    justify-content:space-between;">
    <div style="display:flex;
        align-items:center;gap:12px;">
        <div style="
            background:linear-gradient(
                135deg,#4f46e5,#7c3aed);
            border-radius:10px;
            padding:8px;
            font-size:22px;">🚂</div>
        <div>
            <div style="
                color:white;
                font-weight:900;
                font-size:18px;
                letter-spacing:1px;">
                SMART RAIL ADVISOR
            </div>
            <div style="
                color:#94a3b8;
                font-size:11px;">
                AI · ML · Railway Intelligence
            </div>
        </div>
    </div>
    <div>{mode_badge}</div>
</div>""",unsafe_allow_html=True)

# ══════════════════════════════════════
# SPLASH SCREEN — only on first visit
# ══════════════════════════════════════
if 'splash_done' not in \
        st.session_state:
    show_splash()
    st.session_state['splash_done']=True

# ══════════════════════════════════════
# MODE SELECTION SCREEN
# ══════════════════════════════════════
if 'mode' not in st.session_state:

    show_navbar()

    st.markdown("""
<div style="
    background:linear-gradient(
        135deg,#0f0c29,#302b63,
        #4338ca);
    padding:40px 30px;
    border-radius:20px;
    text-align:center;
    margin-bottom:32px;">
    <div style="
        font-size:32px;
        font-weight:900;
        color:white;">
        🚂 Plan Your Journey Smarter
    </div>
    <div style="
        color:#c7d2fe;
        font-size:16px;
        margin-top:10px;">
        AI-powered fare prediction,
        waitlist analysis and
        travel insights
    </div>
</div>""",unsafe_allow_html=True)

    st.markdown("""
<div style="
    text-align:center;
    margin-bottom:24px;">
    <div style="
        font-size:26px;
        font-weight:800;
        color:#1e293b;">
        How are you travelling today?
    </div>
    <div style="
        color:#64748b;
        font-size:15px;
        margin-top:6px;">
        Choose your travel mode
        to get started
    </div>
</div>""",unsafe_allow_html=True)

    col1,col2 = st.columns(2,gap="large")

    with col1:
        st.markdown("""
<div style="
    background:linear-gradient(
        160deg,#fafaff,#ede9fe);
    border:3px solid #4f46e5;
    border-radius:24px;
    padding:40px 28px;
    text-align:center;
    margin-bottom:16px;
    min-height:340px;">
    <div style="font-size:72px;">
        👤
    </div>
    <div style="
        font-size:26px;
        font-weight:900;
        color:#4f46e5;
        margin-top:16px;">
        Solo Travel
    </div>
    <div style="
        color:#64748b;
        font-size:14px;
        margin-top:14px;
        line-height:2.2;">
        ✅ Fare prediction<br>
        ✅ Waitlist confirmation check<br>
        ✅ Crowd & Delay prediction<br>
        ✅ Festival surge alerts<br>
        ✅ AI recommendation<br>
        ✅ Journey summary + PDF
    </div>
</div>""",unsafe_allow_html=True)
        if st.button(
            "👤 I'm Travelling Solo",
            key="solo_btn",
            use_container_width=True):
            st.session_state['mode']='solo'
            st.rerun()

    with col2:
        st.markdown("""
<div style="
    background:linear-gradient(
        160deg,#f0fdf4,#dcfce7);
    border:3px solid #059669;
    border-radius:24px;
    padding:40px 28px;
    text-align:center;
    margin-bottom:16px;
    min-height:340px;">
    <div style="font-size:72px;">
        👥
    </div>
    <div style="
        font-size:26px;
        font-weight:900;
        color:#059669;
        margin-top:16px;">
        Group Travel
    </div>
    <div style="
        color:#64748b;
        font-size:14px;
        margin-top:14px;
        line-height:2.2;">
        ✅ Group fare calculator<br>
        ✅ CNF/WL/RAC per passenger<br>
        ✅ Senior & Child discounts<br>
        ✅ Lower berth advice<br>
        ✅ Split vs Together advisor<br>
        ✅ Group summary + PDF
    </div>
</div>""",unsafe_allow_html=True)
        if st.button(
            "👥 We're a Group",
            key="group_btn",
            use_container_width=True):
            st.session_state['mode']='group'
            st.rerun()

    st.stop()

# ══════════════════════════════════════
# AFTER MODE IS SELECTED
# ══════════════════════════════════════
mode = st.session_state['mode']
show_navbar(mode)

# Back button
back1,back2,back3 = st.columns([1,4,1])
with back1:
    if st.button("← Back to Mode Select",
                 key="back_btn"):
        for k in ['mode','analyzed',
                  'from_st','to_st',
                  'travel_date',
                  'travel_class',
                  'train_type',
                  'time_slot',
                  'distance',
                  'fare','conf','crowd',
                  'delay','ontime',
                  'score','fest','surge',
                  'lead_days','bt','br']:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()

# Mode banner
if mode=='solo':
    st.markdown("""
<div style="
    background:linear-gradient(
        135deg,#ede9fe,#fafaff);
    border-left:5px solid #4f46e5;
    border-radius:12px;
    padding:14px 20px;
    margin-bottom:20px;
    display:flex;
    align-items:center;
    gap:12px;">
    <span style="font-size:28px;">
        👤</span>
    <div>
        <div style="
            font-weight:800;
            color:#4f46e5;
            font-size:16px;">
            Solo Travel Mode
        </div>
        <div style="
            color:#64748b;
            font-size:13px;">
            Fill journey details below
            and click Analyze
        </div>
    </div>
</div>""",unsafe_allow_html=True)
else:
    st.markdown("""
<div style="
    background:linear-gradient(
        135deg,#dcfce7,#f0fdf4);
    border-left:5px solid #059669;
    border-radius:12px;
    padding:14px 20px;
    margin-bottom:20px;
    display:flex;
    align-items:center;
    gap:12px;">
    <span style="font-size:28px;">
        👥</span>
    <div>
        <div style="
            font-weight:800;
            color:#059669;
            font-size:16px;">
            Group Travel Mode
        </div>
        <div style="
            color:#64748b;
            font-size:13px;">
            Fill route below,
            then go to Group Planner tab
        </div>
    </div>
</div>""",unsafe_allow_html=True)

st.markdown("---")

# ══════════════════════════════════════
# SEARCH BAR — COMMON FOR BOTH
# ══════════════════════════════════════
st.markdown("### 🔍 Enter Journey Details")

c1,c2,c3,c4 = st.columns(4)
with c1:
    from_st=st.selectbox(
        "🏠 From Station",CITIES,
        index=CITIES.index('Nagpur')
        if 'Nagpur' in CITIES else 0)
with c2:
    to_st=st.selectbox(
        "📍 To Station",CITIES,
        index=CITIES.index('Mumbai Central')
        if 'Mumbai Central' in CITIES
        else 1)
with c3:
    travel_date=st.date_input(
        "📅 Travel Date",
        value=date.today(),
        min_value=date.today())
with c4:
    travel_class=st.selectbox(
        "💺 Class",
        ['SL','3A','2A','1A'])

c5,c6 = st.columns(2)
with c5:
    train_type=st.selectbox(
        "🚂 Train Type",
        ['Rajdhani','Duronto','Shatabdi',
         'Superfast','Express','Passenger'])
with c6:
    time_slot=st.selectbox(
        "⏰ Time Slot",
        ['Early Morning','Morning',
         'Afternoon','Evening',
         'Night','Late Night'])

distance=get_distance(from_st,to_st)
st.info(
    f"📏 Distance: **{distance} km**  "
    f"|  Route: **{from_st} → {to_st}**")

# ══════════════════════════════════════
# ANALYZE BUTTON
# ══════════════════════════════════════
if mode=='solo':
    btn_txt="🔍 Analyze My Journey — Get AI Predictions"
else:
    btn_txt="💾 Save Route & Go to Group Planner →"

if st.button(btn_txt,key="analyze_btn"):

    if from_st==to_st:
        st.error(
            "❌ From and To cannot "
            "be same!")
        st.stop()

    if travel_date<date.today():
        st.error(
            "❌ Select a future date!")
        st.stop()

    if mode=='group':
        # Just save the route
        st.session_state.update({
            'from_st'     :from_st,
            'to_st'       :to_st,
            'travel_date' :travel_date,
            'travel_class':travel_class,
            'train_type'  :train_type,
            'time_slot'   :time_slot,
            'distance'    :distance,
        })
        st.success(
            "✅ Route saved! "
            "Now click **👥 Group Planner** "
            "tab to analyze your group!")
        st.stop()

    # Solo — show train animation
    ph=st.empty()
    with ph.container():
        train_loading(
            "🔍 Analyzing your journey...")

    month=travel_date.month
    fest=MONTH_FESTIVAL[month]
    surge=FESTIVAL_SURGE[fest]
    today=date.today()
    ld=max(1,(travel_date-today).days)

    fare=predict_fare(
        distance,travel_class,fest,ld,month)
    conf=predict_conf(
        distance,travel_class,fest,ld,month)
    crowd=predict_crowd(
        distance,travel_class,fest,ld,month)
    delay,ontime=calc_delay(
        from_st,to_st,fest,
        train_type,time_slot)
    score=comfort_score(
        crowd,conf,delay,
        travel_class,fest)
    bt,br=best_train(crowd,conf,delay)
    save_search(
        from_st,to_st,
        travel_date,travel_class,
        fare,conf,crowd,score)

    time.sleep(2)
    ph.empty()

    st.session_state.update({
        'analyzed'    :True,
        'from_st'     :from_st,
        'to_st'       :to_st,
        'travel_date' :travel_date,
        'travel_class':travel_class,
        'train_type'  :train_type,
        'time_slot'   :time_slot,
        'distance'    :distance,
        'fare'        :fare,
        'conf'        :conf,
        'crowd'       :crowd,
        'delay'       :delay,
        'ontime'      :ontime,
        'score'       :score,
        'fest'        :fest,
        'surge'       :surge,
        'lead_days'   :ld,
        'bt'          :bt,
        'br'          :br,
    })
    st.success(
        f"✅ Analysis complete! "
        f"**{from_st} → {to_st}** "
        f"| {distance} km")

# ══════════════════════════════════════
# FLAGS
# ══════════════════════════════════════
is_solo  = (mode=='solo' and
            'analyzed' in st.session_state)
is_group = (mode=='group')

# ══════════════════════════════════════
# TABS
# ══════════════════════════════════════
t1,t2,t3,t4,t5,t6,t7,t8 = st.tabs([
    "🚂 Journey Analysis",
    "👥 Group Planner",
    "📅 Festival Calendar",
    "⚠️ Fare Alerts",
    "🔍 Anomaly Detection",
    "🕐 Delay Predictor",
    "⚡ Model Performance",
    "📋 Journey Summary",
])

# ══════════════════════════════════════
# TAB 1 — JOURNEY ANALYSIS (SOLO ONLY)
# ══════════════════════════════════════
with t1:
    if is_group:
        show_locked(
            "Journey Analysis — Solo Only",
            "You are in Group Mode. "
            "Click ← Back button above "
            "to switch to Solo Travel.",
            "#7c3aed","#faf5ff","🔒")

    elif not is_solo:
        st.markdown("""
<div style="
    background:#f0f9ff;
    border:1.5px solid #bae6fd;
    border-radius:16px;
    padding:48px;
    text-align:center;">
    <div style="font-size:52px;">🔍</div>
    <div style="
        font-size:20px;
        font-weight:700;
        color:#0369a1;
        margin-top:16px;">
        Enter journey details above
    </div>
    <div style="
        color:#64748b;
        font-size:14px;
        margin-top:8px;">
        and click Analyze to see
        AI predictions!
    </div>
</div>""",unsafe_allow_html=True)

    else:
        fs   =st.session_state['from_st']
        ts   =st.session_state['to_st']
        td   =st.session_state['travel_date']
        cls  =st.session_state['travel_class']
        tt   =st.session_state['train_type']
        dist =st.session_state['distance']
        fare =st.session_state['fare']
        conf =st.session_state['conf']
        crowd=st.session_state['crowd']
        delay=st.session_state['delay']
        score=st.session_state['score']
        fest =st.session_state['fest']
        surge=st.session_state['surge']
        ld   =st.session_state['lead_days']
        bt   =st.session_state['bt']
        br   =st.session_state['br']
        month=td.month

        st.markdown("### 📊 Key Metrics")
        m1,m2,m3,m4=st.columns(4)
        avg=1184
        diff=round((fare-avg)/avg*100,1)
        m1.metric("💰 Predicted Fare",
            f"₹{fare:,.0f}",
            f"▼{abs(diff)}% below avg"
            if diff<0 else
            f"▲{diff}% above avg")
        m2.metric("🎫 Confirmation",
            f"{conf:.1f}%",
            "✅ Safe" if conf>=70 else
            "⚠️ Book early" if conf>=50
            else "❌ Risky")
        m3.metric("👥 Crowd",crowd,
            "🟢 Comfortable"
            if crowd=='Low' else
            "🟡 Moderate"
            if crowd=='Medium' else
            "🔴 Crowded")
        m4.metric("⏰ Delay",
            f"{delay} min",
            "🟢 LOW" if delay<=20 else
            "🟡 MEDIUM" if delay<=45
            else "🔴 HIGH")

        st.divider()
        if surge>=50:
            st.error(
                f"🚨 **{fest}** "
                f"+{surge}% surge! "
                f"Consider different date!")
        elif surge>=25:
            st.warning(
                f"⚠️ **{fest}** +{surge}%."
                f" Book 30 days early!")
        elif surge>0:
            st.info(
                f"ℹ️ **{fest}** "
                f"+{surge}% low surge.")
        else:
            st.success(
                "✅ No surge — best time!")

        st.divider()
        st.markdown("### 💺 Class Comparison")
        cf2={}
        for c in ['SL','3A','2A','1A']:
            cf2[c]=predict_fare(
                dist,c,fest,ld,month)
        mn=min(cf2.values())
        mx=max(cf2.values())
        cnames={'SL':'Sleeper',
                '3A':'AC 3-Tier',
                '2A':'AC 2-Tier',
                '1A':'First AC'}
        cols=st.columns(4)
        for i,c in enumerate(
                ['SL','3A','2A','1A']):
            f=cf2[c]
            if f==mn:
                bdr="#059669";bg="#f0fdf4"
                tag="💚 Cheapest"
            elif f==mx:
                bdr="#dc2626";bg="#fff5f5"
                tag="🔴 Costliest"
            else:
                bdr="#e2e8f0";bg="white"
                tag="Selected" \
                    if c==cls else ""
            cols[i].markdown(f"""
<div style="border:2px solid {bdr};
    border-radius:12px;padding:14px;
    text-align:center;background:{bg};">
    <div style="font-weight:700;
        font-size:14px;">
        {cnames[c]}</div>
    <div style="font-size:24px;
        font-weight:900;color:#4f46e5;">
        ₹{f:,.0f}</div>
    <div style="font-size:11px;
        color:#64748b;">{tag}</div>
</div>""",unsafe_allow_html=True)

        st.divider()
        st.markdown("### 🎛️ Fare Simulator")
        sc1,sc2=st.columns(2)
        with sc1:
            sim_days=st.slider(
                "📅 Days before journey",
                1,60,ld)
        with sc2:
            sim_cls=st.select_slider(
                "💺 Class",
                ['SL','3A','2A','1A'],cls)
        sf=predict_fare(
            dist,sim_cls,fest,sim_days,month)
        bf=predict_fare(
            dist,sim_cls,fest,21,month)
        sav=round(sf-bf,2)
        s1,s2,s3=st.columns(3)
        s1.metric("💰 Simulated",
                  f"₹{sf:,.0f}")
        s2.metric("🏆 Best (21 days)",
                  f"₹{bf:,.0f}")
        s3.metric("💸 Saving",
                  f"₹{abs(sav):,.0f}",
                  "Book 21 days early!"
                  if sav>0 else
                  "Already optimal!")

        st.divider()
        st.markdown(
            "### 🤖 AI Recommendation")
        cc="#059669" if score>=80 \
           else "#d97706" if score>=60 \
           else "#dc2626"
        cl="Excellent!" if score>=80 \
           else "Good" if score>=60 \
           else "Needs Attention"
        st.markdown(f"""
<div style="border:2px solid #4f46e5;
    border-radius:16px;padding:20px;
    background:#fafaff;">
    <div style="font-weight:800;
        font-size:16px;color:#4f46e5;
        margin-bottom:14px;">
        🏆 Best Option for Your Journey
    </div>
    <div style="display:flex;
        gap:24px;flex-wrap:wrap;">
        <div>
            <span style="color:#64748b;
                font-size:12px;">
                BEST TRAIN</span><br>
            <strong style="font-size:16px;">
                {bt}</strong>
            <span style="color:#64748b;">
                — {br}</span>
        </div>
        <div>
            <span style="color:#64748b;
                font-size:12px;">
                COMFORT SCORE</span><br>
            <strong style="font-size:16px;
                color:{cc};">
                {score}/100 — {cl}
            </strong>
        </div>
        <div>
            <span style="color:#64748b;
                font-size:12px;">
                FESTIVAL</span><br>
            <strong style="font-size:16px;">
                {fest} +{surge}%</strong>
        </div>
    </div>
</div>""",unsafe_allow_html=True)

        scores2={
            "💰 Value for Money":
                max(0,100-int(diff*2))
                if diff>0 else 90,
            "🎫 Confirmation Chance":
                int(conf),
            "👥 Travel Comfort":score,
            "🛡️ Safe from Surge":
                max(0,100-surge),
            "⏰ Delay Risk":
                max(0,100-int(delay))
        }
        for lbl,val in scores2.items():
            cl2,cl3=st.columns([1,3])
            cl2.write(lbl)
            clr="#059669" if val>=70 \
                else "#d97706" \
                if val>=40 else "#dc2626"
            cl3.markdown(f"""
<div style="background:#f1f5f9;
    border-radius:10px;height:22px;
    margin-top:8px;">
    <div style="background:{clr};
        width:{val}%;height:22px;
        border-radius:10px;
        text-align:right;
        padding-right:8px;color:white;
        font-size:12px;
        line-height:22px;">
        {val}%</div></div>""",
            unsafe_allow_html=True)

        st.markdown("#### 💡 Final Advice")
        if conf>=70 and surge<=25 \
                and delay<=30:
            st.success(
                f"✅ **BOOK NOW!** "
                f"₹{fare:,.0f} fare, "
                f"{conf:.1f}% confirmed!")
        elif surge>50:
            st.error(
                f"🚨 **CHANGE DATE!** "
                f"{fest} +{surge}%!")
        elif conf<50:
            st.warning(
                f"⚠️ Only {conf:.1f}% "
                f"confirmation. Try {bt}!")
        else:
            st.info(
                f"📊 Book {ld} days early"
                f" for best fare!")

        st.markdown(
            "#### 🚂 All Train Options")
        trains=['Rajdhani','Duronto',
                'Shatabdi','Superfast',
                'Express','Passenger']
        tc=st.columns(3)
        for i,tr in enumerate(trains):
            td2=TRAIN_BASE_DELAY[tr]
            tp=int(
                TRAIN_PUNCTUALITY[tr]*100)
            clr="#059669" if tp>=80 \
                else "#d97706" \
                if tp>=60 else "#dc2626"
            hl="border:2px solid #4f46e5;"\
               if tr==tt else \
               "border:1px solid #e2e8f0;"
            bg2="#f5f3ff" \
                if tr==tt else "white"
            tc[i%3].markdown(f"""
<div style="{hl}border-radius:10px;
    padding:12px;margin-bottom:8px;
    background:{bg2};">
    <strong>{tr}</strong><br>
    <span style="color:{clr};
        font-size:12px;">
        {tp}% on-time</span><br>
    <span style="color:#64748b;
        font-size:11px;">
        ~{td2} min avg delay</span>
</div>""",unsafe_allow_html=True)

# ══════════════════════════════════════
# TAB 2 — GROUP PLANNER (GROUP ONLY)
# ══════════════════════════════════════
with t2:
    if is_solo:
        show_locked(
            "Group Planner — Group Only",
            "You are in Solo Mode. "
            "Click ← Back button above "
            "to switch to Group Travel.",
            "#059669","#f0fdf4","🔒")
    else:
        st.markdown(
            "### 👥 Group Travel Planner")

        # Route card
        st.markdown(f"""
<div style="
    background:linear-gradient(
        135deg,#f0fdf4,#dcfce7);
    border:1.5px solid #059669;
    border-radius:14px;
    padding:18px 24px;
    margin-bottom:20px;">
    <div style="
        font-weight:700;
        color:#059669;
        font-size:15px;">
        🚂 Your Route
    </div>
    <div style="
        font-size:24px;
        font-weight:900;
        margin-top:6px;">
        {from_st} → {to_st}
    </div>
    <div style="
        color:#64748b;
        font-size:13px;
        margin-top:4px;">
        📏 {distance} km  ·
        📅 {travel_date.strftime('%d %b %Y')}
    </div>
    <div style="
        color:#94a3b8;
        font-size:12px;
        margin-top:4px;">
        💡 Change route using
        search bar above
    </div>
</div>""",unsafe_allow_html=True)

        # Auto detect season
        g_month=travel_date.month
        auto_f=MONTH_FESTIVAL[g_month]
        auto_s=FESTIVAL_SURGE[auto_f]
        is_wknd=travel_date.weekday()>=5
        if auto_s>=50: ai=4
        elif auto_s>=35: ai=3
        elif auto_s>=10: ai=1
        elif is_wknd: ai=2
        else: ai=0

        g1,g2,g3=st.columns(3)
        with g1:
            g_class=st.selectbox(
                "💺 Travel Class",
                ['SL','3A','2A','1A'],
                key="g_class")
        with g2:
            g_season=st.selectbox(
                "🌤️ Season",
                ['offseason','normal',
                 'weekend','summer',
                 'festival'],
                index=ai,key="g_season")
        with g3:
            g_lead=st.selectbox(
                "📅 Lead Time (days)",
                [60,30,15,7,2],
                index=1,key="g_lead")

        st.caption(
            f"🗓️ Auto-detected season: "
            f"**{auto_f}** "
            f"(+{auto_s}% surge) "
            f"for "
            f"{travel_date.strftime('%B %Y')}"
            f" — you can change above")

        st.markdown("#### 👤 Passengers")
        n=st.number_input(
            "Number of passengers",
            min_value=2,max_value=20,
            value=4,key="g_count")

        if n>6:
            pnrs=ceil(n/6)
            st.warning(
                f"⚠️ Group of {n} needs "
                f"**{pnrs} separate PNR** "
                f"bookings. Max 6 per PNR "
                f"on IRCTC.")

        st.markdown(
            "#### 📋 Passenger Details")
        passengers=[]
        h0,h1,h2,h3=st.columns(
            [1,2,2,2])
        h0.markdown("**#**")
        h1.markdown("**Name**")
        h2.markdown("**Type**")
        h3.markdown("**Special Need**")

        for i in range(int(n)):
            p1,p2,p3,p4=st.columns(
                [1,2,2,2])
            p1.write(f"{i+1}")
            nm=p2.text_input("N",
                value=f"Passenger {i+1}",
                key=f"nm_{i}",
                label_visibility="collapsed")
            pt=p3.selectbox("T",
                ['Adult','Senior','Child'],
                key=f"pt_{i}",
                label_visibility="collapsed")
            sp=p4.selectbox("S",
                ['None','Lower Berth',
                 'Window','Wheelchair'],
                key=f"sp_{i}",
                label_visibility="collapsed")
            passengers.append({
                'name':nm,
                'type':pt.lower(),
                'special':sp
            })

        st.markdown("---")

        if st.button(
            "🧮 Check Availability & "
            "Calculate Group Fare",
            key="g_analyze"):

            g_dist=distance

            # Train animation for group
            gph=st.empty()
            with gph.container():
                train_loading(
                    "🔍 Analyzing your group...")

            base=get_group_fare(
                g_dist,g_class,
                g_season,g_lead,g_month)
            total_fare=0
            breakdown=[]
            for p in passengers:
                f=base
                if p['type']=='child':
                    f=round(f*0.5,2)
                    disc="50% off"
                elif p['type']=='senior':
                    f=round(f*0.6,2)
                    disc="40% off"
                else:
                    disc="Full fare"
                total_fare+=f
                breakdown.append({
                    'name':p['name'],
                    'type':p['type'],
                    'fare':f,'disc':disc})

            cnf=0;rac=0;wl=0
            statuses=[]
            for i,p in enumerate(
                    passengers):
                status,chance=get_status(
                    i+1,g_season,g_lead)
                if 'CNF' in status: cnf+=1
                elif 'RAC' in status: rac+=1
                else: wl+=1
                statuses.append({
                    'name'  :p['name'],
                    'status':status,
                    'chance':chance,
                    'type'  :p['type']})
            grp_pct=round(cnf/n*100,1)

            time.sleep(2)
            gph.empty()

            # Save for PDF
            st.session_state[
                'grp_result']={
                'from_st'    :from_st,
                'to_st'      :to_st,
                'travel_date':travel_date,
                'distance'   :distance,
                'g_class'    :g_class,
                'g_season'   :g_season,
                'g_lead'     :g_lead,
                'n'          :n,
                'total_fare' :total_fare,
                'cnf_count'  :cnf,
                'rac_count'  :rac,
                'wl_count'   :wl,
                'statuses'   :statuses,
            }

            # Summary cards
            st.markdown(
                "### 📊 Group Summary")
            sc1,sc2,sc3,sc4=\
                st.columns(4)
            sc1.metric("💰 Total Fare",
                f"₹{total_fare:,.0f}")
            sc2.metric("👤 Per Person",
                f"₹{total_fare/n:,.0f}")
            sc3.metric("✅ Confirmed",
                f"{cnf}/{int(n)}")
            sc4.metric("⚠️ At Risk",
                f"{wl+rac}/{int(n)}")

            st.divider()
            st.markdown(
                "### 🎫 Passenger Status")
            for s in statuses:
                if 'CNF' in s['status']:
                    bg2="#f0fdf4"
                    bdr2="#059669"
                    ico="✅"
                elif 'RAC' in s['status']:
                    bg2="#faf5ff"
                    bdr2="#7c3aed"
                    ico="🔄"
                else:
                    bg2="#fffbeb"
                    bdr2="#d97706"
                    ico="⏳"
                st.markdown(f"""
<div style="background:{bg2};
    border-left:4px solid {bdr2};
    border-radius:8px;
    padding:12px 16px;
    margin-bottom:8px;
    display:flex;
    justify-content:space-between;
    align-items:center;">
    <div>
        <strong>{s['name']}</strong>
        <span style="color:#64748b;
            font-size:12px;
            margin-left:8px;">
            ({s['type']})
        </span>
    </div>
    <div>
        <span style="font-weight:700;">
            {ico} {s['status']}
        </span>
        <span style="color:#64748b;
            font-size:12px;
            margin-left:8px;">
            {s['chance']}% chance
        </span>
    </div>
</div>""",unsafe_allow_html=True)

            st.divider()
            st.markdown(
                "### 💰 Fare Breakdown")
            fare_df=pd.DataFrame([{
                '#'   :i+1,
                'Name':b['name'],
                'Type':b['type'].title(),
                'Fare':f"₹{b['fare']:,.0f}",
                'Note':b['disc']
            } for i,b in enumerate(
                breakdown)])
            st.dataframe(fare_df,
                use_container_width=True,
                hide_index=True)

            st.divider()
            st.markdown(
                "### 💡 What Should We Do?")
            r1,r2,r3,r4=st.tabs([
                "📌 Book As-Is",
                "🔀 Split Groups",
                "📅 Change Date",
                "🏆 Best Advice"])

            with r1:
                if grp_pct==100:
                    st.success(
                        "✅ All confirmed!"
                        " Safe to book!")
                elif grp_pct>=70:
                    st.warning(
                        f"⚠️ {cnf} confirmed,"
                        f" {wl+rac} at risk!")
                    st.info(
                        "Tatkal opens at "
                        "10AM (AC) / "
                        "11AM (non-AC)")
                else:
                    st.error(
                        "🚨 High risk! "
                        "Consider alternatives!")

            with r2:
                if wl+rac>0:
                    st.markdown(
                        f"**Group A ({cnf})**"
                        f" → This train ✅")
                    st.markdown(
                        f"**Group B ({wl+rac})**"
                        f" → Next available train")
                    st.info(
                        "Both meet at destination!")
                else:
                    st.success(
                        "✅ No split needed!")

            with r3:
                for bs in [
                        'offseason','normal']:
                    if bs!=g_season:
                        bf3=get_group_fare(
                            g_dist,g_class,
                            bs,60,g_month)
                        bt3=round(bf3*n,2)
                        sv3=round(
                            total_fare-bt3,2)
                        if sv3>0:
                            st.markdown(
                                f"📅 **{bs.title()}"
                                f" season** → "
                                f"₹{bt3:,.0f} "
                                f"(save ₹{sv3:,.0f}!)")

            with r4:
                if grp_pct==100:
                    st.success(
                        "✅ TRAVEL TOGETHER!")
                elif grp_pct>=70:
                    st.warning(
                        "⚠️ BOOK + MONITOR PNR")
                elif grp_pct>=40:
                    st.error(
                        "🔀 SPLIT RECOMMENDED")
                else:
                    st.error(
                        "🚨 CHANGE DATE!")

            st.divider()
            st.markdown(
                "### 🛏️ Berth Advice")
            bc={'SL':3,'3A':3,
                '2A':3,'1A':2}
            nl=[p for p in passengers
                if p['type'] in
                ['senior','child']]
            ln=len(nl)
            la=bc[g_class]
            if ln==0:
                st.success(
                    "✅ No special berth needed!")
            elif ln<=la:
                st.success(
                    f"✅ {ln} lower berth(s)"
                    f" available in {g_class}!")
            else:
                st.warning(
                    f"⚠️ Need {ln} lower berths"
                    f" but only {la} available."
                    f" Consider upgrading class!")

        with st.expander(
                "❓ WL Number Guide"):
            st.markdown("""
| Lead Time | Expected WL |
|-----------|-------------|
| 60+ days | WL 1-5 |
| 30 days | WL 5-15 |
| 15 days | WL 15-30 |
| 7 days | WL 30-50 |
| 2 days | WL 50+ |
            """)

# ══════════════════════════════════════
# TAB 3 — FESTIVAL CALENDAR (BOTH)
# ══════════════════════════════════════
with t3:
    st.markdown(
        "### 📅 Festival Surge Analyzer")

    fest_date=travel_date
    st.info(
        f"📅 Using your travel date: "
        f"**{fest_date.strftime('%d %B %Y')}**")

    month2=fest_date.month
    is_wknd2=fest_date.weekday()>=5
    festival2=MONTH_FESTIVAL[month2]
    surge2=FESTIVAL_SURGE[festival2]
    if is_wknd2: surge2+=10

    fc1,fc2,fc3,fc4=st.columns(4)
    fc1.metric("📅 Your Date",
        fest_date.strftime("%d %b %Y"),
        festival2)
    fc2.metric("📈 Surge",
        f"+{surge2}%",
        "Weekend +10%"
        if is_wknd2 else "Weekday")
    fc3.metric("💺 Availability",
        "Very Low" if surge2>=50 else
        "Low" if surge2>=25 else
        "Moderate" if surge2>=10 else
        "High")
    fc4.metric("📆 Book By",
        "60+ days" if surge2>=50 else
        "30 days" if surge2>=25 else
        "15 days" if surge2>=10 else
        "Anytime")

    st.divider()
    if surge2>=50:
        st.error(
            f"🚨 **{festival2}** "
            f"+{surge2}% HIGH SURGE! "
            f"Strongly consider changing date!")
    elif surge2>=25:
        st.warning(
            f"⚠️ **{festival2}** "
            f"+{surge2}%. Book 30 days early!")
    elif surge2>0:
        st.info(
            f"ℹ️ **{festival2}** "
            f"+{surge2}% low surge.")
    else:
        st.success(
            "✅ Perfect time to travel! "
            "No surge!")

    st.divider()
    months3=list(range(1,13))
    mnames3=['Jan','Feb','Mar','Apr',
             'May','Jun','Jul','Aug',
             'Sep','Oct','Nov','Dec']
    surges3=[FESTIVAL_SURGE[
        MONTH_FESTIVAL[m]]
        for m in months3]
    colors3=[]
    for i,m in enumerate(months3):
        s=surges3[i]
        if m==month2:
            colors3.append('#6600cc')
        elif s>=50:
            colors3.append('#dc2626')
        elif s>=25:
            colors3.append('#d97706')
        elif s>=10:
            colors3.append('#16a34a')
        else:
            colors3.append('#bbf7d0')

    fig3=go.Figure(go.Bar(
        x=mnames3,y=surges3,
        marker_color=colors3,
        text=[f"+{s}%" for s in surges3],
        textposition='outside'))
    fig3.update_layout(
        title="Monthly Surge % "
              "(Your travel month in purple)",
        height=320,
        plot_bgcolor='white',
        showlegend=False,
        margin=dict(t=40,b=20))
    st.plotly_chart(
        fig3,use_container_width=True)

    st.divider()
    st.markdown("#### 💡 Cheaper Alternatives")
    alts2=[]
    for m in range(1,13):
        f3=MONTH_FESTIVAL[m]
        s3=FESTIVAL_SURGE[f3]
        if s3<surge2-10:
            try:
                alt_d=fest_date.replace(
                    month=m,
                    day=min(15,
                    calendar.monthrange(
                    fest_date.year,m)[1]))
                alts2.append({
                    'date':alt_d,'fest':f3,
                    'surge':s3,
                    'save':surge2-s3})
            except: pass
    alts2.sort(key=lambda x:
        abs(x['date'].month-month2))
    alts2=alts2[:3]
    if alts2:
        ac=st.columns(3)
        for i,alt in enumerate(alts2):
            c2="#059669" \
               if alt['surge']<=10 \
               else "#d97706"
            ac[i].markdown(f"""
<div style="border:2px solid {c2};
    border-radius:12px;padding:16px;
    text-align:center;
    background:#f0fdf4;">
    <div style="font-weight:800;
        font-size:15px;">
        {alt['date'].strftime('%d %b')}
    </div>
    <div style="color:#64748b;
        font-size:12px;">
        {alt['fest']}</div>
    <div style="color:{c2};
        font-weight:700;">
        +{alt['surge']}%</div>
    <div style="color:#059669;
        font-size:12px;">
        Save {alt['save']}%!</div>
</div>""",unsafe_allow_html=True)
    else:
        st.success(
            "✅ Your date already "
            "has the lowest surge!")

# ══════════════════════════════════════
# TAB 4 — FARE ALERTS (BOTH)
# ══════════════════════════════════════
with t4:
    st.markdown("### ⚠️ Fare Alerts")

    month4=travel_date.month
    fest4=MONTH_FESTIVAL[month4]
    surge4=FESTIVAL_SURGE[fest4]
    dist4=distance
    cls4=travel_class

    if is_solo and \
            'analyzed' in st.session_state:
        fare4=st.session_state['fare']
        ld4=st.session_state['lead_days']
    else:
        fare4=predict_fare(
            dist4,cls4,fest4,30,month4)
        ld4=30

    normal_fare=predict_fare(
        dist4,cls4,'Normal',30,month4)
    diff4=round(
        (fare4-normal_fare)/
        normal_fare*100,1)

    al1,al2,al3=st.columns(3)
    al1.metric("📅 Your Fare",
        f"₹{fare4:,.0f}",
        f"+{diff4}% vs normal"
        if diff4>0 else
        f"{diff4}% vs normal")
    al2.metric("📊 Normal Fare",
        f"₹{normal_fare:,.0f}")
    al3.metric("🎉 Festival Impact",
        f"+{surge4}%",fest4)

    st.divider()
    if diff4>=50:
        st.error(
            f"🚨 **SPIKE ALERT!** "
            f"Fare is {diff4}% above normal!")
    elif diff4>=25:
        st.warning(
            f"⚠️ Elevated fare +{diff4}%")
    elif diff4>0:
        st.info(
            f"ℹ️ Slightly above "
            f"normal +{diff4}%")
    else:
        st.success(
            f"✅ GREAT DEAL! "
            f"{abs(diff4)}% below normal!")

    st.divider()
    lead_opts=[1,3,7,15,21,30,45,60]
    lead_fares=[predict_fare(
        dist4,cls4,fest4,ld2,month4)
        for ld2 in lead_opts]
    fig4=go.Figure(go.Scatter(
        x=lead_opts,y=lead_fares,
        mode='lines+markers',
        line=dict(color='#4f46e5',width=3),
        marker=dict(size=8)))
    fig4.update_layout(
        title="Fare vs Days Before Journey",
        xaxis_title="Days in Advance",
        yaxis_title="Predicted Fare ₹",
        height=300,
        plot_bgcolor='white')
    st.plotly_chart(
        fig4,use_container_width=True)

    best_ld4=lead_opts[
        lead_fares.index(min(lead_fares))]
    best_lf4=min(lead_fares)
    st.success(
        f"💡 **Best time to book: "
        f"{best_ld4} days in advance** "
        f"→ ₹{best_lf4:,.0f} "
        f"(save ₹{fare4-best_lf4:,.0f}!)")

# ══════════════════════════════════════
# TAB 5 — ANOMALY DETECTION (BOTH)
# ══════════════════════════════════════
with t5:
    st.markdown("### 🔍 Anomaly Detection")
    a1,a2,a3=st.columns(3)
    a1.metric("🔍 Total Records","50,000")
    a2.metric("🚨 Anomalies Found",
              "2,810","5.6% of data")
    a3.metric("⚠️ Suspicious",
              "2,183","4.4% of data")
    st.divider()
    if os.path.exists('anomaly_chart.png'):
        st.image('anomaly_chart.png',
            caption="Fare Anomaly Chart",
            use_container_width=True)

    st.divider()
    st.markdown("#### 🎫 Live Fare Checker")
    chk1,chk2=st.columns(2)
    with chk1:
        check_fare=st.number_input(
            "Enter fare amount (₹)",
            min_value=100,max_value=10000,
            value=1500,step=100)
    with chk2:
        check_cls=st.selectbox(
            "Travel Class",
            ['SL','3A','2A','1A'],
            key="check_class")
    if st.button("🔍 Check This Fare"):
        try:
            df_chk=pd.read_csv(
                'train_data.csv')
            cf=df_chk[
                df_chk['travel_class']
                ==check_cls]['fare']
            mf=cf.mean()
            sf2=cf.std()
            z=(check_fare-mf)/sf2
            st.write(
                f"Normal avg for {check_cls}:"
                f" ₹{mf:,.0f} | "
                f"Z-Score: {z:.2f}")
            if z>3:
                st.error(
                    f"🚨 HIGH ANOMALY! "
                    f"₹{check_fare:,} is "
                    f"₹{check_fare-mf:,.0f} "
                    f"above normal!")
            elif z>2:
                st.warning(
                    "⚠️ Suspicious fare! "
                    "Slightly above normal.")
            elif z<-2:
                st.success(
                    f"💚 GREAT DEAL! "
                    f"₹{mf-check_fare:,.0f} "
                    f"below normal!")
            else:
                st.success(
                    "✅ Normal fare. "
                    "Safe to book!")
        except Exception as e:
            st.error(f"Error: {e}")

# ══════════════════════════════════════
# TAB 6 — DELAY PREDICTOR (BOTH)
# ══════════════════════════════════════
with t6:
    st.markdown(
        "### 🕐 Train Delay Predictor")

    fest6=MONTH_FESTIVAL[
        travel_date.month]

    if is_solo and \
            'analyzed' in st.session_state:
        delay6=st.session_state['delay']
        ontime6=st.session_state['ontime']
        tt6=st.session_state['train_type']
        tslot6=st.session_state['time_slot']
    else:
        delay6,ontime6=calc_delay(
            from_st,to_st,fest6,
            train_type,time_slot)
        tt6=train_type
        tslot6=time_slot

    d1,d2,d3,d4=st.columns(4)
    d1.metric("⏰ Expected Delay",
        f"{delay6} min",
        "🟢 LOW" if delay6<=20 else
        "🟡 MEDIUM" if delay6<=45
        else "🔴 HIGH")
    d2.metric("✅ On-Time Probability",
        f"{ontime6}%",
        "Good" if ontime6>=75 else
        "Average" if ontime6>=50
        else "Poor")
    d3.metric("🚂 Your Train",tt6,
        f"{int(TRAIN_PUNCTUALITY[tt6]*100)}"
        f"% punctual")
    d4.metric("🏆 Best Train",
        "Rajdhani","88% on-time")

    st.divider()
    if delay6<=20:
        st.success(
            f"🟢 LOW RISK — "
            f"Only {delay6} min expected. "
            f"{tt6} is a good choice!")
    elif delay6<=45:
        st.warning(
            f"🟡 MEDIUM RISK — "
            f"{delay6} min expected. "
            f"Keep buffer time!")
    else:
        st.error(
            f"🔴 HIGH RISK — "
            f"{delay6} min expected! "
            f"Consider Rajdhani/Shatabdi!")

    st.divider()
    st.markdown("#### 🚂 Train Comparison")
    trains6=['Rajdhani','Duronto',
             'Shatabdi','Superfast',
             'Express','Passenger']
    tc6=st.columns(3)
    for i6,tr6 in enumerate(trains6):
        td6=TRAIN_BASE_DELAY[tr6]
        tp6=int(
            TRAIN_PUNCTUALITY[tr6]*100)
        clr8="#059669" if tp6>=80 \
             else "#d97706" \
             if tp6>=60 else "#dc2626"
        hl6="border:2px solid #4f46e5;"\
            if tr6==tt6 else \
            "border:1px solid #e2e8f0;"
        bg6="#f5f3ff" \
            if tr6==tt6 else "white"
        tc6[i6%3].markdown(f"""
<div style="{hl6}border-radius:10px;
    padding:10px;margin-bottom:8px;
    background:{bg6};">
    <strong>{tr6}</strong><br>
    <span style="color:{clr8};
        font-size:12px;">
        {tp6}% on-time</span><br>
    <span style="color:#64748b;
        font-size:11px;">
        ~{td6} min avg</span>
</div>""",unsafe_allow_html=True)

    buf6=delay6+30
    btime6=min(TIME_FACTOR,
        key=TIME_FACTOR.get)
    adv1,adv2=st.columns(2)
    adv1.info(
        f"🔄 Keep **{buf6} min** "
        f"buffer for connections")
    adv2.info(
        f"⏰ Best time slot: "
        f"**{btime6}** (least delay)")

    if os.path.exists(
            'monthly_delay_chart.png'):
        st.image(
            'monthly_delay_chart.png',
            use_container_width=True)

# ══════════════════════════════════════
# TAB 7 — MODEL PERFORMANCE (BOTH)
# ══════════════════════════════════════
with t7:
    st.markdown("### ⚡ Model Performance")
    st.info(
        "📚 Technical metrics for "
        "academic evaluation.")

    s1,s2,s3,s4=st.columns(4)
    s1.metric("💰 Fare Model",
              "99.63%","R² Score")
    s2.metric("🎫 Waitlist",
              "76%","Accuracy")
    s3.metric("👥 Crowd",
              "74%","High Class F1")
    s4.metric("⏰ Delay Model",
              "97.5%","R² Score")

    st.divider()
    st.markdown(
        "#### 📊 Algorithm Comparison")
    algo_df=pd.DataFrame({
        'Model':['Linear Regression',
                 'Random Forest',
                 'XGBoost'],
        'R² Score':[56.7,98.2,99.63],
        'MAE (₹)':[578.53,96.54,42.79],
        'Status':['❌ Poor',
                  '✅ Good','🏆 Best']})
    st.dataframe(algo_df,
        use_container_width=True,
        hide_index=True)

    fig7=go.Figure(go.Bar(
        x=['Linear\nRegression',
           'Random\nForest','XGBoost'],
        y=[56.7,98.2,99.63],
        marker_color=[
            '#94a3b8','#64748b','#4f46e5'],
        text=['56.7%','98.2%','99.63%'],
        textposition='outside'))
    fig7.update_layout(
        title="R² Score Comparison",
        yaxis=dict(range=[0,110]),
        height=280,
        plot_bgcolor='white',
        showlegend=False,
        margin=dict(t=40,b=20))
    st.plotly_chart(
        fig7,use_container_width=True)

    st.divider()
    mc1,mc2=st.columns(2)
    with mc1:
        st.markdown("""
<div style="border:1.5px solid #4f46e5;
    border-radius:12px;padding:16px;
    background:#fafaff;">
    <div style="font-weight:800;
        color:#4f46e5;font-size:14px;
        margin-bottom:10px;">
        💰 Fare Prediction Model
    </div>
    <table style="width:100%;
        font-size:13px;">
        <tr><td style="color:#64748b;">
            Algorithm</td>
            <td><b>XGBoost Regressor
            </b></td></tr>
        <tr><td style="color:#64748b;">
            R² Score</td>
            <td><b style="color:#059669;">
            0.9963 (99.63%)</b></td></tr>
        <tr><td style="color:#64748b;">
            MAE</td>
            <td><b>₹42.79</b></td></tr>
        <tr><td style="color:#64748b;">
            5-Fold CV</td>
            <td><b>0.9963 ± 0.0001
            </b></td></tr>
        <tr><td style="color:#64748b;">
            Overfitting</td>
            <td><b style="color:#059669;">
            None detected</b></td></tr>
    </table>
</div>""",unsafe_allow_html=True)

    with mc2:
        st.markdown("""
<div style="border:1.5px solid #059669;
    border-radius:12px;padding:16px;
    background:#f0fdf4;">
    <div style="font-weight:800;
        color:#059669;font-size:14px;
        margin-bottom:10px;">
        🎫 Waitlist Predictor Model
    </div>
    <table style="width:100%;
        font-size:13px;">
        <tr><td style="color:#64748b;">
            Algorithm</td>
            <td><b>XGBoost Classifier
            </b></td></tr>
        <tr><td style="color:#64748b;">
            Accuracy</td>
            <td><b style="color:#059669;">
            76%</b></td></tr>
        <tr><td style="color:#64748b;">
            Precision</td>
            <td><b>75%</b></td></tr>
        <tr><td style="color:#64748b;">
            F1 Score</td>
            <td><b>75%</b></td></tr>
        <tr><td style="color:#64748b;">
            True Positives</td>
            <td><b>2,435</b></td></tr>
    </table>
</div>""",unsafe_allow_html=True)

    st.markdown("<br>",
                unsafe_allow_html=True)
    mc3,mc4=st.columns(2)
    with mc3:
        st.markdown("""
<div style="border:1.5px solid #d97706;
    border-radius:12px;padding:16px;
    background:#fffbeb;">
    <div style="font-weight:800;
        color:#d97706;font-size:14px;
        margin-bottom:10px;">
        👥 Overcrowding Predictor
    </div>
    <table style="width:100%;
        font-size:13px;">
        <tr><td style="color:#64748b;">
            Algorithm</td>
            <td><b>XGBoost Classifier
            </b></td></tr>
        <tr><td style="color:#64748b;">
            Overall Accuracy</td>
            <td><b>56%</b></td></tr>
        <tr><td style="color:#64748b;">
            High Class</td>
            <td><b style="color:#059669;">
            74% ← Key metric</b></td></tr>
        <tr><td style="color:#64748b;">
            Note</td>
            <td><b style="color:#d97706;">
            Overlap expected</b></td></tr>
    </table>
</div>""",unsafe_allow_html=True)

    with mc4:
        st.markdown("""
<div style="border:1.5px solid #0891b2;
    border-radius:12px;padding:16px;
    background:#f0f9ff;">
    <div style="font-weight:800;
        color:#0891b2;font-size:14px;
        margin-bottom:10px;">
        ⏰ Delay Predictor Model
    </div>
    <table style="width:100%;
        font-size:13px;">
        <tr><td style="color:#64748b;">
            Algorithm</td>
            <td><b>XGBoost Regressor
            </b></td></tr>
        <tr><td style="color:#64748b;">
            R² Score</td>
            <td><b style="color:#059669;">
            0.9750 (97.5%)</b></td></tr>
        <tr><td style="color:#64748b;">
            MAE</td>
            <td><b>3.73 min</b></td></tr>
        <tr><td style="color:#64748b;">
            Routes</td>
            <td><b>50 real routes</b>
            </td></tr>
    </table>
</div>""",unsafe_allow_html=True)

    st.divider()
    di1,di2,di3,di4=st.columns(4)
    di1.metric("📊 Records","50,000")
    di2.metric("📋 Columns","15")
    di3.metric("🗺️ Routes","50")
    di4.metric("🏙️ Cities","200+")

    if os.path.exists(
            'fare_vs_distance.png'):
        st.image('fare_vs_distance.png',
            use_container_width=True)

# ══════════════════════════════════════
# TAB 8 — JOURNEY SUMMARY (BOTH+PDF)
# ══════════════════════════════════════
with t8:
    st.markdown("### 📋 Journey Summary")

    if mode=='solo':
        if 'analyzed' not in \
                st.session_state:
            st.info(
                "🔍 Analyze your journey "
                "first using the search "
                "bar above!")
        else:
            fs8=st.session_state['from_st']
            ts8=st.session_state['to_st']
            td8=st.session_state[
                'travel_date']
            cls8=st.session_state[
                'travel_class']
            tt8=st.session_state[
                'train_type']
            dist8=st.session_state[
                'distance']
            fare8=st.session_state['fare']
            conf8=st.session_state['conf']
            crowd8=st.session_state[
                'crowd']
            delay8=st.session_state[
                'delay']
            ontime8=st.session_state[
                'ontime']
            score8=st.session_state[
                'score']
            fest8=st.session_state['fest']
            surge8=st.session_state[
                'surge']
            ld8=st.session_state[
                'lead_days']
            bt8=st.session_state['bt']
            month8=td8.month

            # PDF download
            pb1,pb2=st.columns([3,1])
            with pb2:
                if st.button(
                    "Download PDF",
                    key="solo_pdf_btn"):
                    pdf_data=make_solo_pdf({
                        'fs':fs8,'ts':ts8,
                        'td':td8,'cls':cls8,
                        'tt':tt8,'dist':dist8,
                        'fare':fare8,
                        'conf':conf8,
                        'crowd':crowd8,
                        'delay':delay8,
                        'ontime':ontime8,
                        'score':score8,
                        'fest':fest8,
                        'surge':surge8,
                        'ld':ld8,'bt':bt8,
                    })
                    st.download_button(
                        label="Save PDF",
                        data=pdf_data,
                        file_name=f"SmartRail_"
                            f"{fs8}_to_{ts8}.pdf",
                        mime="application/pdf")
                    st.success("PDF ready!")

            # Header
            sc8="#059669" if score8>=80 \
                else "#d97706" \
                if score8>=60 else "#dc2626"
            st.markdown(f"""
<div style="background:linear-gradient(
    135deg,#0f172a,#1e1b4b);
    border-radius:16px;padding:24px;
    margin-bottom:16px;color:white;">
    <div style="display:flex;
        justify-content:space-between;
        align-items:center;
        flex-wrap:wrap;gap:16px;">
        <div>
            <div style="font-size:22px;
                font-weight:800;">
                🚂 Your Journey Report
            </div>
            <div style="color:#c7d2fe;
                font-size:16px;
                margin-top:4px;">
                {fs8} → {ts8}
            </div>
            <div style="color:#94a3b8;
                font-size:13px;
                margin-top:4px;">
                {td8.strftime('%d %B %Y')}
                · {cls8} · {tt8}
                · {dist8} km
            </div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:44px;
                font-weight:900;
                color:{sc8};">
                {score8}</div>
            <div style="color:#94a3b8;
                font-size:12px;">
                COMFORT /100</div>
        </div>
    </div>
</div>""",unsafe_allow_html=True)

            # Decision
            if conf8>=70 and \
               surge8<=25 and delay8<=30:
                st.markdown("""
<div style="background:#f0fdf4;
    border:2px solid #059669;
    border-radius:12px;padding:20px;
    text-align:center;
    margin-bottom:16px;">
    <div style="font-size:28px;
        font-weight:900;color:#059669;">
        ✅ YES — BOOK NOW!</div>
    <div style="color:#166534;
        font-size:14px;margin-top:8px;">
        Good fare · High confirmation
        · Low delay
    </div>
</div>""",unsafe_allow_html=True)
            elif surge8>50:
                st.markdown(f"""
<div style="background:#fff5f5;
    border:2px solid #dc2626;
    border-radius:12px;padding:20px;
    text-align:center;
    margin-bottom:16px;">
    <div style="font-size:28px;
        font-weight:900;color:#dc2626;">
        ⚠️ WAIT — CHANGE DATE!</div>
    <div style="color:#991b1b;
        font-size:14px;margin-top:8px;">
        {fest8} +{surge8}% surge!
    </div>
</div>""",unsafe_allow_html=True)
            elif conf8<50:
                st.markdown(f"""
<div style="background:#fffbeb;
    border:2px solid #d97706;
    border-radius:12px;padding:20px;
    text-align:center;
    margin-bottom:16px;">
    <div style="font-size:28px;
        font-weight:900;color:#d97706;">
        ⚠️ BOOK WITH CAUTION</div>
    <div style="color:#92400e;
        font-size:14px;margin-top:8px;">
        Only {conf8:.1f}% confirmation
    </div>
</div>""",unsafe_allow_html=True)
            else:
                st.markdown(f"""
<div style="background:#f0f9ff;
    border:2px solid #0891b2;
    border-radius:12px;padding:20px;
    text-align:center;
    margin-bottom:16px;">
    <div style="font-size:28px;
        font-weight:900;color:#0891b2;">
        📊 GOOD TO GO!</div>
    <div style="color:#164e63;
        font-size:14px;margin-top:8px;">
        Book {ld8} days early!
    </div>
</div>""",unsafe_allow_html=True)

            st.divider()
            st.markdown(
                "#### 📌 Key Information")

            avg8=1184
            diff8=round(
                (fare8-avg8)/avg8*100,1)
            fc8c="#059669" if diff8<0 \
                else "#dc2626"
            cc8="#059669" if conf8>=70 \
                else "#d97706" \
                if conf8>=50 else "#dc2626"
            crc8="#059669" \
                 if crowd8=='Low' else \
                 "#d97706" \
                 if crowd8=='Medium' \
                 else "#dc2626"
            dc8="#059669" if delay8<=20 \
                else "#d97706" \
                if delay8<=45 else "#dc2626"
            sc9="#059669" if surge8==0 \
                else "#d97706" \
                if surge8<=25 else "#dc2626"

            info_cards=[
                ("💰 How much will I pay?",
                 f"₹{fare8:,.0f}",
                 "▼ Below avg — great deal!"
                 if diff8<0 else
                 f"▲ {diff8}% above average",
                 fc8c),
                ("🎫 Will waitlist confirm?",
                 f"{conf8:.1f}%",
                 "Likely YES ✅"
                 if conf8>=70 else
                 "Maybe ⚠️" if conf8>=50
                 else "Risky ❌",
                 cc8),
                ("👥 How crowded?",
                 crowd8,"",crc8),
                ("⏰ Will train be on time?",
                 f"{delay8} min",
                 f"{ontime8}% on-time chance",
                 dc8),
                ("🎉 Festival impact?",
                 f"+{surge8}%",fest8,sc9),
                ("🚂 Best train?",bt8,
                 f"{int(TRAIN_PUNCTUALITY[bt8]*100)}"
                 f"% on-time",
                 "#4f46e5"),
            ]

            for q,val,sub,clr in \
                    info_cards:
                st.markdown(f"""
<div style="background:white;
    border:1.5px solid #e2e8f0;
    border-radius:12px;
    padding:16px;
    margin-bottom:10px;">
    <div style="font-weight:700;
        font-size:14px;color:#374151;">
        {q}</div>
    <div style="font-size:28px;
        font-weight:900;
        color:{clr};margin-top:6px;">
        {val}</div>
    <div style="color:#64748b;
        font-size:13px;">{sub}</div>
</div>""",unsafe_allow_html=True)

            st.divider()
            st.markdown(
                "#### 💰 Money Saving Tips")
            bf8=predict_fare(
                dist8,cls8,fest8,21,month8)
            sv8=round(fare8-bf8,2)
            sl8=predict_fare(
                dist8,'SL',fest8,ld8,month8)
            sv_sl8=round(fare8-sl8,2)
            tips=[]
            if sv8>0:
                tips.append(
                    f"📅 Book 21 days early"
                    f" → save **₹{sv8:,.0f}**")
            if sv_sl8>0 and cls8!='SL':
                tips.append(
                    f"💺 Choose Sleeper"
                    f" → save **₹{sv_sl8:,.0f}**")
            if surge8>0:
                tips.append(
                    f"🗓️ Avoid {fest8}"
                    f" (+{surge8}% surge)")
            if tips:
                for t in tips:
                    st.markdown(f"✅ {t}")
            else:
                st.success(
                    "✅ Already at best price!")

            st.divider()
            st.markdown("#### ⚠️ Warnings")
            warns=[]
            if surge8>25:
                warns.append(
                    f"🎉 {fest8} "
                    f"+{surge8}% higher prices!")
            if delay8>30:
                warns.append(
                    f"⏰ {delay8} min delay!"
                    f" Keep buffer time.")
            if crowd8=='High':
                warns.append(
                    "👥 Very crowded! "
                    "Book immediately.")
            if conf8<60:
                warns.append(
                    f"🎫 Only {conf8:.1f}% "
                    f"confirmation — risky!")
            if ld8<7:
                warns.append(
                    "📅 Last minute booking"
                    " — consider Tatkal!")
            if warns:
                for w in warns:
                    st.warning(w)
            else:
                st.success(
                    "✅ No major concerns!"
                    " Have a great journey!")

            # Footer
            st.markdown(f"""
<div style="background:#0f172a;
    border-radius:12px;padding:16px;
    text-align:center;color:#94a3b8;
    font-size:12px;margin-top:24px;">
    <strong style="color:white;">
        SMART RAIL ADVISOR
    </strong><br>
    Generated on
    {date.today().strftime('%d %B %Y')}
    · XGBoost ML · 99.63% Accuracy<br>
    <em>MCA Final Year Project · Nagpur
    </em>
</div>""",unsafe_allow_html=True)

    else:
        # GROUP SUMMARY
        if 'grp_result' not in \
                st.session_state:
            st.info(
                "🔍 Go to **Group Planner** "
                "tab, add passenger details "
                "and click "
                "**Check Availability** "
                "to see summary here!")
        else:
            gr=st.session_state[
                'grp_result']

            # PDF download
            pb1g,pb2g=st.columns([3,1])
            with pb2g:
                if st.button(
                    "Download PDF",
                    key="grp_pdf_btn"):
                    pdf_grp=make_group_pdf(gr)
                    st.download_button(
                        label="Save PDF",
                        data=pdf_grp,
                        file_name=f"Group_"
                            f"{gr['from_st']}"
                            f"_to_"
                            f"{gr['to_st']}.pdf",
                        mime="application/pdf")
                    st.success("PDF ready!")

            # Header
            st.markdown(f"""
<div style="background:linear-gradient(
    135deg,#0f172a,#064e3b);
    border-radius:16px;padding:24px;
    color:white;margin-bottom:16px;">
    <div style="font-size:22px;
        font-weight:800;">
        👥 Group Travel Summary
    </div>
    <div style="color:#6ee7b7;
        font-size:16px;margin-top:4px;">
        {gr['from_st']} → {gr['to_st']}
    </div>
    <div style="color:#94a3b8;
        font-size:13px;margin-top:4px;">
        {gr['travel_date'].strftime('%d %B %Y')}
        · {gr['distance']} km
        · {gr['g_class']} Class
        · {int(gr['n'])} passengers
    </div>
</div>""",unsafe_allow_html=True)

            # Summary metrics
            gc1,gc2,gc3,gc4=st.columns(4)
            gc1.metric("💰 Total Fare",
                f"₹{gr['total_fare']:,.0f}")
            gc2.metric("👤 Per Person",
                f"₹{gr['total_fare']/gr['n']:,.0f}")
            gc3.metric("✅ Confirmed",
                f"{gr['cnf_count']}"
                f"/{int(gr['n'])}")
            gc4.metric("⚠️ At Risk",
                f"{gr['wl_count']+gr['rac_count']}"
                f"/{int(gr['n'])}")

            st.divider()

            # Festival alert
            month_g=gr['travel_date'].month
            fest_g=MONTH_FESTIVAL[month_g]
            surge_g=FESTIVAL_SURGE[fest_g]
            if surge_g>=50:
                st.error(
                    f"🚨 **{fest_g}** "
                    f"+{surge_g}% surge! "
                    f"Book 60 days early!")
            elif surge_g>=25:
                st.warning(
                    f"⚠️ **{fest_g}** "
                    f"+{surge_g}%."
                    f" Book 30 days early!")
            else:
                st.success(
                    f"✅ {fest_g} — Good "
                    f"time for group travel!")

            st.divider()

            # Passenger status
            st.markdown(
                "#### 🎫 Passenger Status")
            for s in gr['statuses']:
                if 'CNF' in s['status']:
                    bg2="#f0fdf4"
                    bdr2="#059669"
                    ico="✅"
                elif 'RAC' in s['status']:
                    bg2="#faf5ff"
                    bdr2="#7c3aed"
                    ico="🔄"
                else:
                    bg2="#fffbeb"
                    bdr2="#d97706"
                    ico="⏳"
                st.markdown(f"""
<div style="background:{bg2};
    border-left:4px solid {bdr2};
    border-radius:8px;
    padding:12px 16px;
    margin-bottom:8px;
    display:flex;
    justify-content:space-between;
    align-items:center;">
    <div>
        <strong>{s['name']}</strong>
        <span style="color:#64748b;
            font-size:12px;
            margin-left:8px;">
            ({s['type']})</span>
    </div>
    <div>
        <span style="font-weight:700;">
            {ico} {s['status']}
        </span>
        <span style="color:#64748b;
            font-size:12px;
            margin-left:8px;">
            {s['chance']}% chance
        </span>
    </div>
</div>""",unsafe_allow_html=True)

            st.divider()

            # Quick fare estimate
            st.markdown(
                "#### 💰 Fare by Class"
                " (per person, 30 days lead)")
            qf1,qf2,qf3,qf4=st.columns(4)
            for i,cls_q in enumerate(
                    ['SL','3A','2A','1A']):
                qf=predict_fare(
                    gr['distance'],cls_q,
                    fest_g,30,month_g)
                [qf1,qf2,qf3,qf4][i]\
                    .metric(cls_q,
                        f"₹{qf:,.0f}",
                        "per person")

            # Footer
            st.markdown(f"""
<div style="background:#0f172a;
    border-radius:12px;padding:16px;
    text-align:center;color:#94a3b8;
    font-size:12px;margin-top:24px;">
    <strong style="color:white;">
        SMART RAIL ADVISOR
    </strong><br>
    Generated on
    {date.today().strftime('%d %B %Y')}
    · Group Travel Mode<br>
    <em>MCA Final Year Project 
    </em>
</div>""",unsafe_allow_html=True)
