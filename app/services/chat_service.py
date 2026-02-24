from openai import OpenAI
from app.config import BASE_URL, API_KEY, MODEL

class ChatService:
    def __init__(self):
        self.client = OpenAI(
            base_url=BASE_URL,
            api_key=API_KEY,
        )

    def chat_stream(self, history, model: str = None):
        stream = self.client.chat.completions.create(
            model=model or MODEL,
            messages=history,
            temperature=0.7,
            # max_tokens=512,
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content