from flask import Flask, redirect, url_for, session, request, jsonify, Markup
from flask_oauthlib.client import OAuth
from flask import render_template
from time import localtime, strftime
from bson.objectid import ObjectId

import pprint
import os
import json
import pymongo
import dns
import sys

app = Flask(__name__)


url = 'mongodb+srv://{}:{}@{}/{}'.format(
    os.environ["MONGO_USERNAME"],
    os.environ["MONGO_PASSWORD"],
    os.environ["MONGO_HOST"],
    os.environ["MONGO_DBNAME"]
)
client = pymongo.MongoClient(os.environ["MONGO_HOST"])
db = client[os.environ["MONGO_DBNAME"]]
collection = db['cookieStats']

app.debug = True #Change this to False for production
app.secret_key = os.environ['SECRET_KEY'] #used to sign session cookies
oauth = OAuth(app)



github = oauth.remote_app(
    'github',
    consumer_key=os.environ['GITHUB_CLIENT_ID'], #your web app's "username" for github's OAuth
    consumer_secret=os.environ['GITHUB_CLIENT_SECRET'],#your web app's "password" for github's OAuth
    request_token_params={'scope': 'user:email'}, #request read-only access to the user's email.  For a list of possible scopes, see developer.github.com/apps/building-oauth-apps/scopes-for-oauth-apps
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize' #URL for github's OAuth login
)

@app.context_processor
def inject_logged_in():
    return {"logged_in":('github_token' in session)}

@app.route("/")
def render_main():
    return render_template('game.html')

@app.route("/game")
def render_game():
    print(collection.count_documents({}))
    return render_template('game.html')

@app.route("/stats")
def render_stats():

    return render_template('stats.html')

@app.route("/save", methods=["POST"])
def render_save():

    pprint.pprint(session)
    post = {"Github Name": session['user_data']['login'] ,  "cookies": request.form['cookies'] , "cookiesPerClick": request.form['cookiesPerClick'], "cookiesPerSecond": request.form['cookiesPerSecond']}

    if post.find_one({"Github Name": session['user_data']['login']}) is not None:
        collection.update_one({"Github Name": session['user_data']['login']}, {'$set':{'cookies' : request.form['cookies']} ,'$set':{'cookiesPerClick' : request.form['cookiesPerClick']} ,  '$set':{'cookiesPerSecond' : request.form['cookiesPerSecond']}   })
    else:
        pprint.pprint("HERE")
        collection.insert_one(post)


    return redirect("/game")



@app.route('/login')
def login():
    return github.authorize(callback=url_for('authorized', _external=True, _scheme='http')) #callback URL must match the pre-configured callback URL

@app.route('/logout')
def logout():
    session.clear()
    return render_template('game.html', message='You were logged out')

@app.route('/login/authorized')
def authorized():
    resp = github.authorized_response()
    if resp is None:
        session.clear()
        message = 'Access denied: reason=' + request.args['error'] + ' error=' + request.args['error_description'] + ' full=' + pprint.pformat(request.args)
    else:
        try:
            session['github_token'] = (resp['access_token'], '') #save the token to prove that the user logged in
            session['user_data']=github.get('user').data
            message='You were successfully logged in as ' + session['user_data']['login']
        except Exception as inst:
            session.clear()
            print(inst)
            message='Unable to login, please try again.'
    return render_template('game.html')

#the tokengetter is automatically called to check who is logged in.
@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')


if __name__ == '__main__':
    os.system("echo json(array) > file")
    app.run()
