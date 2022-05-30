from flask import Flask, render_template, request, session, jsonify
import urllib.request
from pusher import Pusher
from datetime import datetime
import httpagentparser
import json
import os
import hashlib

import detection
from dbsetup import create_connection, create_session, update_or_create_page, select_all_sessions, \
    select_all_user_visits, select_all_pages, select_all_details, create_record
from json2html import *

app = Flask(__name__)
app.secret_key = os.urandom(24)

# configure pusher object
pusher = Pusher(
    app_id="1400593",
    key="e520069b0c8944b239bf",
    secret="489bf0661e34da2aa35c",
    cluster="ap2"
)

database = "./pythonsqlite.db"
conn = create_connection(database)
c = conn.cursor()

userOS = None
userIP = None
userCity = None
userBrowser = None
userCountry = None
userContinent = None
sessionID = None


def main():
    global conn, c


def parseVisitor(data):
    update_or_create_page(c, data)
    pusher.trigger(u'pageview', u'new', {
        u'page': data[0],
        u'session': sessionID,
        u'ip': userIP
    })
    pusher.trigger(u'numbers', u'update', {
        u'page': data[0],
        u'session': sessionID,
        u'ip': userIP
    })


@app.before_request
def getAnalyticsData():
    global userOS, userBrowser, userIP, userContinent, userCity, userCountry, sessionID
    userInfo = httpagentparser.detect(request.headers.get('User-Agent'))
    userOS = userInfo['platform']['name']
    userBrowser = userInfo['browser']['name']
    userIP = "2405:0201:e008:c0f6:b530:9c20:d8ed:f478" if request.remote_addr == '127.0.0.1' else request.remote_addr
    api = "https://www.iplocate.io/api/lookup/" + userIP
    try:
        resp = urllib.request.urlopen(api)
        result = resp.read()
        result = json.loads(result.decode("utf-8"))
        userCountry = result["country"]
        userContinent = result["continent"]
        userCity = result["city"]
    except:
        print("Could not find: ", userIP)
    getSession()


def getSession():
    global sessionID
    time = datetime.now().replace(microsecond=0)
    if 'user' not in session:
        lines = (str(time) + userIP).encode('utf-8')
        session['user'] = hashlib.md5(lines).hexdigest()
        sessionID = session['user']
        pusher.trigger(u'session', u'new', {
            u'ip': userIP,
            u'continent': userContinent,
            u'country': userCountry,
            u'city': userCity,
            u'os': userOS,
            u'browser': userBrowser,
            u'session': sessionID,
            u'time': str(time),
        })
        data = [userIP, userContinent, userCountry, userCity, userOS, userBrowser, sessionID, time]
        create_session(c, data)
    else:
        sessionID = session['user']


@app.route('/')
def index():
    data = ['home', sessionID, str(datetime.now().replace(microsecond=0))]
    parseVisitor(data)
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/contactus')
def contactus():
    return render_template('contacts.html')


@app.route('/dashboard/<session_id>', methods=['GET'])
def sessionPages(session_id):
    result = select_all_user_visits(c, session_id)
    return render_template("dashboard-single.html", data=result)


@app.route('/get-all-sessions')
def get_all_sessions():
    data = []
    dbRows = select_all_sessions(c)
    for row in dbRows:
        data.append({
            'ip': row['ip'],
            'continent': row['continent'],
            'country': row['country'],
            'city': row['city'],
            'os': row['os'],
            'browser': row['browser'],
            'session': row['session'],
            'time': row['created_at']
        })
    return jsonify(data)


@app.route('/contact', methods=['POST', 'GET'])
def contact():
    if request.method == detection.compare():
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        country = request.form['country']
        websiteaddress = request.form['websiteaddress']
        data = [firstname, lastname, country, websiteaddress]
        create_record(c, data)
    return render_template("result.html")


@app.route('/view')
def view():
    data = []
    dbRows = select_all_details(c)
    for row in dbRows:
        data.append({
            'firstname': row['firstname'],
            'lastname': row['lastname'],
            'country': row['country'],
            'weblink': row['weblink'],
        })

    table_data = (json2html.convert(data))
    return table_data


if __name__ == '__main__':
    main()
    app.run(debug=True)
