from openai import OpenAI
from dotenv import load_dotenv
from flask import Flask, request, render_template
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
credentials_db = db.credentials


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

@app.route('/')
def homepage():
    found_activities: List[Dict[str, Any]] = list(activities_db.find())
    return render_template("homepage.html", activities=found_activities)


# APIs

@app.route('/api/activity', methods=["POST"])
def create_activity():

    if request.method == 'POST':
        request_json = request.get_json()

        new_activity_object = models.ActivityModel(**request_json)
        success = utils.add_activity_to_db(new_activity_object)

        if not success:
            return {"code": 400, "message": "Activity has wrong format"}, 400

        else:
            return utils.get_specific_activity(new_activity_object.uuid)
    
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
    deleted = utils.delete_activity(activity_uuid)

    if not deleted:
        return {"code": 404, "message": "Activity not found"}, 404
    else:
        return {"code": 200, "message": "Activity deleted successfully"}, 200


if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(debug=True, host='0.0.0.0')
