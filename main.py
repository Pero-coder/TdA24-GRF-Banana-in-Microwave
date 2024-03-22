from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI()
client = OpenAI(
  api_key=os.environ.get("OPENAI_API_KEY")
)