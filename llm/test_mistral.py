import os
from dotenv import load_dotenv
from mistralai import Mistral

load_dotenv()

API_KEY = os.getenv('MISTRAL_API_KEY')
MODEL = 'mistral-small-latest'

def construct_prompt(text: str) -> str:
    prompt_root = """ Generate 5 multiple choice questions from the following text.
        All the questions must be enclosed in a single JSON object.
        Further each question will be a JSON object in the format:
        question: question, 1: option1, 2: option2, 3:option3, 4:option4, ans: correctoption\n
        Text: """
    
    return prompt_root + text

with open("res.txt", 'r') as f:
    data = f.read()

client = Mistral(api_key=API_KEY)
chat_response = client.chat.complete(
    model=MODEL,
    messages=[{
        "role": "user",
        "content": construct_prompt(data)
    }]
)

print(chat_response.choices[0].message.content)