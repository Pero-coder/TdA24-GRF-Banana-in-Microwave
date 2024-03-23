from openai import OpenAI
from dotenv import load_dotenv
from flask import Flask
from pymongo.mongo_client import MongoClient
from datetime import timedelta
import secrets
import os

load_dotenv()

mongodb_client = MongoClient(
    f'mongodb+srv://{os.environ.get("MONGO_USERNAME")}:{os.environ.get("MONGO_PWD")}@cluster0.ebiunpa.mongodb.net/?retryWrites=true&w=majority'
)
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Generate a random secret key
app.permanent_session_lifetime = timedelta(hours=4)  # Session expires after 4 hours
db = mongodb_client.project_activities_database

openai_client = OpenAI(
  api_key=os.environ.get("OPENAI_API_KEY")
)

# request to chatgpt API
completion = openai_client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "Učitel Masarykovy univerzity v Brně"},
        {"role": "user", "content": "Řekněte mi základní informace o škole"}
    ]
)

@app.route('/')
def hello_world():
    return completion.choices[0].message.content


if __name__ == '__main__':
    app.run()
