import asyncio
from openai import OpenAI
from app.utils.logger import logger
client = OpenAI()
from dotenv import load_dotenv
load_dotenv() # load openai api key from .env file

def send_to_openai(messages):
    completion = client.chat.completions.create(model="gpt-4o", messages=messages, temperature=1.3)
    answer = completion.choices[0].message.content
    prompt_tokens = completion.usage.prompt_tokens
    completion_tokens = completion.usage.completion_tokens
    total_tokens = completion.usage.total_tokens
    logger.info(f"Prompt tokens: {prompt_tokens}")
    logger.info(f"Completion tokens: {completion_tokens}")
    logger.info(f"Total tokens: {total_tokens}")
    #logger.info(f"Response: {answer}")
    return answer, prompt_tokens, completion_tokens, total_tokens

async def send_to_openai_vision(question, image_url):
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are Ai-Chan, the mascot of the Bakakats Discord server. You are a prankster who occasionally jokes around instead of helping. You love to troll everyone in the server, making jokes on expense of others and pinging users."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ],
    )
    answer = completion.choices[0].message.content
    prompt_tokens = completion.usage.prompt_tokens
    completion_tokens = completion.usage.completion_tokens
    total_tokens = completion.usage.total_tokens
    logger.info(f"Prompt tokens: {prompt_tokens}")
    logger.info(f"Completion tokens: {completion_tokens}")
    logger.info(f"Total tokens: {total_tokens}")
    #logger.info(f"Response: {answer}")
    return answer, prompt_tokens, completion_tokens, total_tokens


async def ask_gpt(author, author_id, user_message):
    try:
        # Gluing discord username to the message
        logger.info(f"Question: {user_message}")
        messages = [
            {"role": "system", "content": "You are helpful AI-chan assistant that helps user with their question as best as possible."},
            {"role": "user", "content": f"{author} ({author_id}): {user_message}"},
        ]
        return messages
    except Exception as ex:
        logger.error(f"Error in ask_question: {ex}")
        return "Sorry, something went wrong while processing your request."

async def send_to_openai_gpt(messages):
    completion = await asyncio.to_thread(client.chat.completions.create, model="gpt-4o", messages=messages, temperature=0.7)
    answer = completion.choices[0].message.content
    prompt_tokens = completion.usage.prompt_tokens
    completion_tokens = completion.usage.completion_tokens
    total_tokens = completion.usage.total_tokens
    logger.info(f"Prompt tokens: {prompt_tokens}")
    logger.info(f"Completion tokens: {completion_tokens}")
    logger.info(f"Total tokens: {total_tokens}")
    #logger.info(f"Response: {answer}")
    return answer, prompt_tokens, completion_tokens, total_tokens
