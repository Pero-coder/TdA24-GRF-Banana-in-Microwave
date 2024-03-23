from openai import OpenAI
from dotenv import load_dotenv
from flask import Flask, request, render_template, redirect, session
from pymongo.mongo_client import MongoClient
from datetime import timedelta
import secrets
import os
from typing import List, Dict, Any
import json
from bson import json_util

import models
import utils


load_dotenv()

mongodb_client = MongoClient(
    f'mongodb+srv://{os.environ.get("MONGO_USERNAME")}:{os.environ.get("MONGO_PWD")}@cluster0.ebiunpa.mongodb.net/?retryWrites=true&w=majority'
)
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Generate a random secret key
app.permanent_session_lifetime = timedelta(hours=4)  # Session expires after 4 hours

db = mongodb_client.project_activities_database
activities_db = db.activities
activities_to_approve_db = db.activities_to_approve
credentials_db = db.credentials
ai_summaries_db = db.ai_summaries


openai_client = OpenAI(
  api_key=os.environ.get("OPENAI_API_KEY")
)


@app.route('/hello-world')
def hello_world():

    # request to chatgpt API
    completion = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Učitel Masarykovy univerzity v Brně"},
            {"role": "user", "content": "Řekněte mi základní informace o škole"}
        ]
    )

    return completion.choices[0].message.content


@app.route('/', methods=["GET"])
def homepage():
    uuids = request.args.getlist('uuid')
    last_search = request.args.get('last_search', "")
    no_results = request.args.get('no_results', "")

    if no_results:
        found_activities = []
        ai_generated_descriptions = []

    elif uuids:
        found_activities = list(activities_db.find({"_id": {"$in": uuids}}))
        ai_generated_descriptions = list(ai_summaries_db.find({"_id": {"$in": uuids}}))
    else:
        found_activities = list(activities_db.find())
        ai_generated_descriptions = list(ai_summaries_db.find())


    activities_and_descriptions = zip(found_activities, ai_generated_descriptions)

    return render_template("homepage.html", last_search=last_search, activities_and_descriptions=activities_and_descriptions)

@app.route("/aktivita")
def activity_empty():
    return redirect('/')

@app.route('/aktivita/<string:activity_uuid>', methods=["GET"])
def aktivita_page(activity_uuid: str):

    activity_get = utils.get_specific_activity(activity_uuid)
    
    if activity_get[1] != 200:
        return "Aktivita nebyla nalezena!", 200

    return render_template("activity_page.html", **activity_get[0])


# Login page
@app.route("/login", methods=["GET", "POST"])
def lecturer_login():

    if bool(session.get("logged_in")):
        return redirect("/admin-zone")

    if request.method == "GET":
        return render_template("login_page.html")

    elif request.method == "POST":

        request_json: dict = request.get_json() # {"username": "", "password": ""}

        username: str|None = request_json.get("username")
        password: str|None = request_json.get("password")

        if username is None or password is None:
            return {"code": 401, "message": "Wrong username or password"}, 401
        
        username = username.strip()
        password = password.strip()
        
        if username == '' or password == '':
            return {"code": 401, "message": "Wrong username or password"}, 401

        admin_credentials = credentials_db.find_one({"username": {"$eq": username}})

        if not bool(admin_credentials):
            return {"code": 401, "message": "Wrong username or password"}, 401
        
        hashed_password = admin_credentials.get("hashed_password")


        if not utils.check_hash_bcrypt(password, hashed_password):
            return {"code": 401, "message": "Wrong username or password"}, 401

        session["logged_in"] = True

        return redirect('/admin-zone')

    return {"code": 405, "message": "Method not allowed"}, 405


@app.route("/logout")
def logout_lecturer():
    session.clear() # delete cookies
    return redirect('/login')


@app.route('/admin-zone', methods=["GET"])
def admin_page():

    if not bool(session.get("logged_in")):
        return redirect("/login")
    
    all_activities_to_approve = list(activities_to_approve_db.find())

    return render_template("admin-zone_page.html", activities_count=str(len(all_activities_to_approve)), activities=all_activities_to_approve)


@app.route('/admin-zone/schvaleni/<string:activity_uuid>', methods=["GET"])
def approve_activity_page(activity_uuid: str):

    if not bool(session.get("logged_in")):
        return redirect("/login")
    
    found_activity = activities_to_approve_db.find_one({"_id": {"$eq": activity_uuid}})

    if found_activity is None:
        return "Aktivita neexistuje!", 404

    activity_object = models.ActivityModel(**found_activity)

    return render_template("approval_activity_page.html", **activity_object.model_dump())



@app.route('/tvorba-aktivity', methods=["GET"])
def create_activity_page():

    return render_template("create-activity_page.html")


# APIs

@app.route('/api/activity', methods=["POST"])
def create_activity():

    if request.method == 'POST':
        request_json = request.get_json()

        new_activity_object = models.ActivityModel(**request_json)
        
        #ai_generated_description = utils.create_ai_description(new_activity_object)
        #success_ai_generated_description = utils.add_ai_generated_description(new_activity_object.uuid, ai_generated_description)

        success_creation = utils.add_activity_to_db(new_activity_object)

        if not success_creation:
            return {"code": 400, "message": "Activity has wrong format"}, 400
        
        #elif not success_ai_generated_description:
        #    return {"code": 500, "message": "AI failed to create description"}, 500

        else:
            return new_activity_object.model_dump(), 200
    
    else:
        return {"code": 405, "message": "Method not allowed"}, 405

@app.route('/api/activity', methods=["GET"])
def get_all_activities():

    if request.method == 'GET':
        found_activities: List[Dict[str, Any]] = list(activities_db.find())
        return json.loads(json_util.dumps(found_activities)), 200
    
    else:
        return {"code": 405, "message": "Method not allowed"}, 405

@app.route("/api/activity/<string:activity_uuid>", methods=["GET"])
def get_activity(activity_uuid: str):
    return utils.get_specific_activity(activity_uuid)

@app.route("/api/activity/<string:activity_uuid>", methods=["DELETE"])
def delete_activity(activity_uuid: str):
    
    if request.method == "DELETE":
        utils.delete_ai_description(activity_uuid)
        deleted = utils.delete_activity(activity_uuid)

        if not deleted:
            return {"code": 404, "message": "Activity not found"}, 404
        else:
            return {"code": 200, "message": "Activity deleted successfully"}, 200

    else:
        return {"code": 405, "message": "Method not allowed"}, 405

@app.route("/api/search_ai", methods=["POST"])
def search_activity():

    if request.method == "POST":
        request_json: dict = request.get_json() # {"prompt": ""}
        
        search_text: str|None = request_json.get("prompt")

        if search_text is None or search_text == "":
            return {"code": 400, "message": "Invalid prompt"}, 400


        return {"uuids": utils.ai_search_activities(search_text)}, 200
    
    else:
        return {"code": 405, "message": "Method not allowed"}, 405


@app.route("/api/approve_activity/<string:activity_uuid>", methods=["POST"])
def approve_activity(activity_uuid: str):

    if request.method == 'POST':
        success = utils.approve_activity(activity_uuid)

        if not success:
            return {"code": 404, "message": "Activity not found"}, 404
        else:
            return {"code": 200, "message": "Activity approved successfully"}, 200
    
    else:
        return {"code": 405, "message": "Method not allowed"}, 405


@app.route("/api/reject_activity/<string:activity_uuid>", methods=["POST"])
def reject_activity(activity_uuid: str):

    if request.method == "POST":
        success = utils.reject_activity(activity_uuid)

        if not success:
            return {"code": 404, "message": "Activity not found"}, 404
        else:
            return {"code": 200, "message": "Activity rejected successfully"}, 200
    
    else:
        return {"code": 405, "message": "Method not allowed"}, 405


if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(debug=True, host='0.0.0.0')
