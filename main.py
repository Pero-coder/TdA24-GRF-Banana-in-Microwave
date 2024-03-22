from openai import OpenAI
from dotenv import load_dotenv
from flask import Flask
import os

load_dotenv()

app = Flask(__name__)

client = OpenAI(
  api_key=os.environ.get("OPENAI_API_KEY")
)

completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "Jsi učitel, který vysvětluje python."},
        {"role": "user", "content": "Co je knihovna flask?"}
    ]
)

@app.route('/')
def hello_world():
    return completion.choices[0].message.content


if __name__ == '__main__':
    app.run()
