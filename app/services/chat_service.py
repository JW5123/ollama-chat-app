from openai import OpenAI
from app.config import BASE_URL, API_KEY, MODEL

class ChatService:
    def __init__(self):
        self.client = OpenAI(
            base_url=BASE_URL,
            api_key=API_KEY,
        )
    
    def chat(self, history):
        response = self.client.chat.completions.create(
            model=MODEL,
            messages=history,
            temperature=0.7
        )
        return response.choices[0].message.content