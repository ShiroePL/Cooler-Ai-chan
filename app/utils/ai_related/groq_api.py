import time
from app.utils.logger import logger
from groq import Groq
from app.config import Config

api_keys = Config.get_groq_api_keys()
current_key_index = 0
client = Groq(api_key=api_keys[current_key_index])


token_count = 0
start_time = None

def reset_token_count():
    global token_count, start_time
    token_count = 0
    start_time = None

def rotate_api_key():
    global current_key_index, client
    current_key_index = (current_key_index + 1) % len(api_keys)
    client = Groq(api_key=api_keys[current_key_index])
    logger.debug(f"Rotated API key to: {current_key_index}")

def send_to_groq(messages):
    """Send a list of messages to the Groq API and return the response, prompt tokens, completion tokens, and total tokens."""
    global token_count, start_time

    # If this is the first request, set the start time
    if start_time is None:
        start_time = time.time()

    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    
    if elapsed_time > 60:
        reset_token_count()
        start_time = time.time()

    if token_count >= 6000:
        rotate_api_key()
        reset_token_count()
        start_time = time.time()

    completion = client.chat.completions.create(
        #model="llama3-70b-8192", 
        model="llama-3.3-70b-versatile", 
        messages=messages
    )
    answer = completion.choices[0].message.content
    prompt_tokens = completion.usage.prompt_tokens
    completion_tokens = completion.usage.completion_tokens
    total_tokens = completion.usage.total_tokens
    
    token_count += total_tokens
    logger.info(f"Total tokens in rotation: {token_count}")   
    return answer, prompt_tokens, completion_tokens, total_tokens


async def send_to_groq_vision(question, image_url):
    """Send question with picture, return the response, prompt tokens, completion tokens, and total tokens."""
    global token_count, start_time

    # If this is the first request, set the start time
    if start_time is None:
        start_time = time.time()

    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    
    if elapsed_time > 60:
        reset_token_count()
        start_time = time.time()

    if token_count >= 6000:
        rotate_api_key()
        reset_token_count()
        start_time = time.time()
    print(f"Image URL in send to groq funciuons: {image_url}")
    
    completion = client.chat.completions.create(
        #model="llama3-70b-8192", 
        model="llama-3.2-90b-vision-preview", 
        messages=[
            # this groq says tdont work now {"role": "system", "content": "You are Ai-Chan, the mascot of the Bakakats Discord server. You are a prankster who occasionally jokes around instead of helping. You love to troll everyone in the server, making jokes on expense of others and pinging users."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ]
    )
    answer = completion.choices[0].message.content
    prompt_tokens = completion.usage.prompt_tokens
    completion_tokens = completion.usage.completion_tokens
    total_tokens = completion.usage.total_tokens
    
    token_count += total_tokens
    logger.info(f"Total tokens in rotation: {token_count}")   
    return answer, prompt_tokens, completion_tokens, total_tokens
