from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI()
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

# outputs only AI response message
print(completion.choices[0].message.content)