import asyncio
from openai import OpenAI
from app.utils.logger import logger
from app.utils.ai_related.prompt_templates import get_basic_prompt
from app.utils.helpers import get_bot_name_from_context
client = OpenAI()
from dotenv import load_dotenv
load_dotenv() # load openai api key from .env file

def send_to_openai(messages):
    completion = client.chat.completions.create(model="gpt-5-mini", messages=messages, temperature=1.3)
    answer = completion.choices[0].message.content
    prompt_tokens = completion.usage.prompt_tokens
    completion_tokens = completion.usage.completion_tokens
    total_tokens = completion.usage.total_tokens
    logger.info(f"Prompt tokens: {prompt_tokens}")
    logger.info(f"Completion tokens: {completion_tokens}")
    logger.info(f"Total tokens: {total_tokens}")
    #logger.info(f"Response: {answer}")
    return answer, prompt_tokens, completion_tokens, total_tokens

async def send_to_openai_vision(question, image_url, ctx=None):
    bot_name = get_bot_name_from_context(ctx) if ctx else 'Ai-Chan'
    system_prompt = get_basic_prompt(bot_name)
    
    completion = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": system_prompt},
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


async def ask_gpt(author, author_id, user_message, ctx=None):
    try:
        # Gluing discord username to the message
        logger.info(f"Question: {user_message}")
        bot_name = get_bot_name_from_context(ctx) if ctx else 'Ai-Chan'
        system_prompt = f"You are helpful {bot_name} assistant that helps user with their question as best as possible."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{author} ({author_id}): {user_message}"},
        ]
        return messages
    except Exception as ex:
        logger.error(f"Error in ask_question: {ex}")
        return "Sorry, something went wrong while processing your request."

async def send_to_openai_gpt(messages):
    completion = await asyncio.to_thread(client.chat.completions.create, model="gpt-5-mini", messages=messages, temperature=0.7)
    answer = completion.choices[0].message.content
    prompt_tokens = completion.usage.prompt_tokens
    completion_tokens = completion.usage.completion_tokens
    total_tokens = completion.usage.total_tokens
    logger.info(f"Prompt tokens: {prompt_tokens}")
    logger.info(f"Completion tokens: {completion_tokens}")
    logger.info(f"Total tokens: {total_tokens}")
    #logger.info(f"Response: {answer}")
    return answer, prompt_tokens, completion_tokens, total_tokens
