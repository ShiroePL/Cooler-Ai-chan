from openai import OpenAI
import os

YOUR_API_KEY = os.getenv("PERPLEXITY_API")
print(YOUR_API_KEY)
messages = [
    {
        "role": "system",
        "content": (
            "You are an artificial intelligence assistant and you need to "
            "retrive information from the internet, being as accurate as possible."
        ),
    },
    {   
        "role": "user",
        "content": (
            "hi! what do we know about new llama 4 model?"
        ),
    },
]

client = OpenAI(api_key=YOUR_API_KEY, base_url="https://api.perplexity.ai")

# chat completion without streaming
response = client.chat.completions.create(
    model="sonar",
    messages=messages,
)
print(response)