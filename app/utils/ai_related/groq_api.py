from app.utils.logger import logger
from groq import Groq
from app.config import Config

client = Groq(api_key=Config.ai_groq_key)

def send_to_groq(messages):
    """Send a list of messages to the Groq API and return the response, prompt tokens, completion tokens, and total tokens."""
    completion = client.chat.completions.create(
        model="llama3-70b-8192", 
        messages=messages
    )
    answer = completion.choices[0].message.content
    prompt_tokens = completion.usage.prompt_tokens
    completion_tokens = completion.usage.completion_tokens
    total_tokens = completion.usage.total_tokens
    
    return answer, prompt_tokens, completion_tokens, total_tokens
