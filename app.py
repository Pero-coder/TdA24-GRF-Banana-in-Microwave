from openai import OpenAI
from dotenv import load_dotenv
from flask import Flask
import os

load_dotenv()

app = Flask(__name__)

client = OpenAI(
  api_key=os.environ.get("OPENAI_API_KEY")
)

# request to chatgpt API
completion = client.chat.completions.create(
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
