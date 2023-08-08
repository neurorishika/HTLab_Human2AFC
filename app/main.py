from flask import Flask, jsonify, render_template, request, redirect, Response
from .experiments import MultiLevelMarkov

# add support for server-side sessions to identify different users
from flask_session import Session
from flask import session

# data manipulation
import numpy as np
import pandas as pd
import os

# load environment variables and pymongo
from dotenv import load_dotenv
from pymongo import MongoClient

# load the environment variables
load_dotenv()

# create a function to connect to the mongodb database
def connect_to_db():
    """
    Connect to the mongodb database
    """
    try:
        # get the mongodb credentials
        mongodb_url = os.environ.get('MONGO_URL')
        mongodb_dbname = os.environ.get('MONGO_DBNAME')

        print('Connecting to the database at {}'.format(mongodb_url))

        # connect to the database
        client = MongoClient(mongodb_url)
        db = client[mongodb_dbname]
        return db,client
    except:
        print('Error connecting to the database. Please check.')

# connect to the database
DB,client = connect_to_db()

# create the flask app
app = Flask(__name__, template_folder='../templates',static_folder='../static')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = '/tmp/'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
Session(app)

task_ids = [3151,13151]
max_trials = 500
min_trials = 30
naive_trials = 5
max_winnings = 15 # in dollars
unit_winnings = max_winnings/(300*(max_trials-naive_trials)) # in dollars

def valid_tasks(uniqueID,db,all_task_ids):
    """
    Return a list of valid task ids for the user
    """
    already_played = []
    # look through the collections in the database
    collections = db.list_collection_names()
    for collection in collections:
        # check if the collection is for the user
        if uniqueID == collection.split('_')[0]:
            # get the task ids
            already_played.append(int(collection.split('_')[1]))
    if app.debug:
        print("Already played: {}".format(already_played))
    # remove the task ids from the list of all task ids
    valid_tasks = [task_id for task_id in all_task_ids if task_id not in already_played]
    return valid_tasks

def verify_uid(uniqueID):
    """
    Verify that the uniqueID is valid (10 characters long, alphanumeric)
    """
    if len(uniqueID) != 10:
        return False
    if not np.all([char in list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for char in uniqueID]):
        return False
    return True

experiments = {}
 
@app.route("/")
def home_view():
        # check if the user is logged in
        if not session.get("uniqueID"):
                return redirect("/login")
        # if logged in, check if the user has an experiment
        if session.get("uniqueID") in experiments:
                return redirect("/experiment")
        # if not, create a new experiment
        session_id = session.get("uniqueID")
        # get a random task id from the list of valid task ids
        valid = valid_tasks(session_id,DB,task_ids)
        if len(valid) == 0:
                return render_template("notasks.html")
        task_id = np.random.choice(valid)
        # check if app is in debug mode
        if app.debug:
                experiments[session_id] = MultiLevelMarkov(task_id,max_trials,min_trials,naive_trials,DB,debug=True)
        else:
                experiments[session_id] = MultiLevelMarkov(task_id,max_trials,min_trials,naive_trials,DB,debug=False)
        return render_template("home.html", min_trials=min_trials, max_trials=max_trials)

# login
@app.route("/login", methods=["GET", "POST"])
def login_view():
        # check if username is provided in the url
        if request.args.get("uniqueID"):
                # store the username in the session
                input_uid = request.args.get("uniqueID")
                if not verify_uid(input_uid):
                        message = "The uniqueID you provided is not valid. Please try again."
                        return render_template("failed.html",message=message,addl_message="")
                session["uniqueID"] = input_uid
                # redirect to the home page
                return redirect("/")

        # check for form submission
        if request.method == "POST":
                # get the username
                input_uid = request.form.get("uniqueID")
                if not verify_uid(input_uid):
                        message = "The uniqueID you provided is not valid. Please try again."
                        return render_template("failed.html",message=message,addl_message="")
                # store the username in the session
                session["uniqueID"] = input_uid
                # redirect to the home page
                return redirect("/")
        
        return render_template("login.html")

# logout
@app.route("/logout")
def logout_view():
        if not session.get("uniqueID") or session.get("uniqueID") not in experiments:
                return redirect("/login")
        # write experiment data to database
        session_id = session.get("uniqueID")
        experiment = experiments[session_id]
        confirmation = experiment.write_to_database(session_id)
        # remove the experiment from the dictionary
        del experiments[session_id]
        # remove the uniqueID from the sessions
        session.pop("uniqueID", None)
        if request.args.get("direct")=='yes':
                return redirect("/login")
        # redirect to the home page
        if confirmation == "no_trials":
                message = "Unfortunately, we did not register any trials for you. Please try again."
                addl_message = f"You can try again by clicking <a href='/login?uniqueID={session_id}'>here</a>."
                return render_template("failed.html",message=message,addl_message=addl_message)
        elif confirmation == "not_enough_trials":
                message = "Unfortunately, you did not complete enough trials to be eligible for payment. Please try again."
                addl_message = f"You can try again by clicking <a href='/login?uniqueID={session_id}'>here</a>."
                return render_template("failed.html",message=message,addl_message=addl_message)
        else:
                return render_template("confirmation.html",confirmation=confirmation,id=session_id)

# download all data
@app.route("/download")
def download_view():
        # find all collections
        collections = DB.list_collection_names()
        # loop through collections and convert to pandas dataframe
        dfs = []
        for collection in collections:
                df = pd.DataFrame(DB[collection].find())
                # add collection name as a column
                df['collection'] = collection
                dfs.append(df)
        # create a single dataframe
        df = pd.concat(dfs)
        # convert to csv
        csv = df.to_csv(index=False)
        # send csv to client
        return Response(
                csv,
                mimetype="text/csv",
                headers={"Content-disposition":
                        "attachment; filename=data.csv"})



# generate new UniqueID
@app.route("/generateID", methods=["GET", "POST"])
def generateID_view():
        # generate a random alphanumeric string of length 7
        uniqueID = ''.join(np.random.choice(list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'),10))
        # check if the uniqueID already exists in database by looping through all collections and checking if the uniqueID is in the collection name
        collections = DB.list_collection_names()
        for collection in collections:
                if uniqueID in collection:
                        # if the uniqueID exists, generate a new one
                        return redirect("/generateID")
        # if the uniqueID does not exist, show a page with the uniqueID and a link to redirect to the login page with the uniqueID
        return render_template("newID.html",id=uniqueID)


@app.route("/experiment")
def experiment_view():
        # reset the experiment
        if not session.get("uniqueID") or session.get("uniqueID") not in experiments:
                return redirect("/login")
        # experiment = experiments[session.get("uniqueID")]
        # experiment.reset()
        return render_template("experiment.html")

# GET requests

@app.route("/get_left_string") 
def get_left_string():
        """
        Get the string for the left option
        """
        if not session.get("uniqueID") or session.get("uniqueID") not in experiments:
                return redirect("/login")
        experiment = experiments[session.get("uniqueID")]
        left_string, _, _, _ = experiment.get_next_trial()
        # max trials reached
        if left_string is None:
                return redirect("/logout")
        # send the string to the client as a json object
        return jsonify(left_string=left_string)

@app.route("/get_right_string")
def get_right_string():
        """
        Get the string for the right option
        """
        if not session.get("uniqueID") or session.get("uniqueID") not in experiments:
                return redirect("/login")
        experiment = experiments[session.get("uniqueID")]
        _, _, right_string, _ = experiment.get_next_trial()
        # max trials reached
        if right_string is None:
                return redirect("/logout")
        # send the string to the client as a json object
        return jsonify(right_string=right_string)

@app.route("/get_points_and_trial")
def get_points_and_trial():
        """
        Get the current points and trials
        """
        if not session.get("uniqueID") or session.get("uniqueID") not in experiments:
                return redirect("/login")
        experiment = experiments[session.get("uniqueID")]
        points = experiment.current_points
        trial = experiment.current_trial
        winnings = round(points*unit_winnings,2) # round to 2 decimal places
        # send the string to the client as a json object
        return jsonify(points=points, trial=trial, winnings=winnings)

@app.route("/get_left_reward")
def get_left_reward():
        """
        Get the reward for the left option
        """
        if not session.get("uniqueID") or session.get("uniqueID") not in experiments:
                return redirect("/login")
        experiment = experiments[session.get("uniqueID")]
        _, left_reward, _, _ = experiment.get_next_trial()
        # send the string to the client as a json object
        return jsonify(left_reward=left_reward)

@app.route("/get_right_reward")
def get_right_reward():
        """
        Get the reward for the right option
        """
        if not session.get("uniqueID") or session.get("uniqueID") not in experiments:
                return redirect("/login")
        experiment = experiments[session.get("uniqueID")]
        _, _, _, right_reward = experiment.get_next_trial()
        # send the string to the client as a json object
        return jsonify(right_reward=right_reward)

# record responses
@app.route("/left_response")
def left_response():
        """
        Record the response for the left option
        """
        if not session.get("uniqueID") or session.get("uniqueID") not in experiments:
                return redirect("/login")
        experiment = experiments[session.get("uniqueID")]
        left_string, left_reward, _, _ = experiment.get_next_trial()
        experiment.record_response(left_string, left_reward)
        print("left response recorded")
        return jsonify(success=True)

@app.route("/right_response")
def right_response():
        """
        Record the response for the right option
        """
        if not session.get("uniqueID") or session.get("uniqueID") not in experiments:
                return redirect("/login")
        experiment = experiments[session.get("uniqueID")]
        _, _, right_string, right_reward = experiment.get_next_trial()
        experiment.record_response(right_string, right_reward)
        print("right response recorded")
        return jsonify(success=True)

@app.route("/is_debug_mode")
def is_debug_mode():
        """
        Check if debug mode is on
        """
        return jsonify(debug=app.debug)