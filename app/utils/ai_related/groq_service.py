import re
from app.utils.ai_related.prompt_templates import basic_prompt, history_prompt
from app.utils.logger import logger

class GroqService:

    async def ask_question(self, author, user_message):
        try:
            # Gluing discord username to the message
            logger.info(f"Question: {user_message}")
            messages = [
                {"role": "system", "content": basic_prompt},
                {"role": "user", "content": f"{author}: {user_message}"},
            ]
            #logger.debug(f"Messages: {messages}")
            return messages
        except Exception as ex:
            logger.error(f"Error in ask_question: {ex}")
            return "Sorry, something went wrong while processing your request."
        
    async def assemble_chat_history(self, context, user_message):
        try:
            logger.info(f"Question: {user_message}")
            messages = [message async for message in context.channel.history(limit=50)]
            #logger.debug(f"Fetched messages: {[message.content for message in messages]}")

            chat_messages = []
            previous_author = None
            concatenated_content = ""

            for message in reversed(messages):
                author = message.author
                current_author = author.nick if author.nick else author.name
                #logger.debug(f"Processing message from {current_author}: {message.content}")

                if current_author == previous_author:
                    concatenated_content += "\n" + message.content
                else:
                    if concatenated_content:
                        chat_messages.append({
                            "role": "assistant" if previous_author in ["AI-Chan", "Kiki_chan"] else "user",
                            "content": f"{previous_author}: {concatenated_content}"
                        })

                    previous_author = current_author
                    concatenated_content = message.content

            # Add the last concatenated message
            if concatenated_content:
                chat_messages.append({
                    "role": "assistant" if previous_author in ["AI-Chan", "Kiki_chan"] else "user",
                    "content": f"{previous_author}: {concatenated_content}"
                })

            # Insert the basic prompt and history prompt at the beginning
            chat_messages.insert(0, {"role": "system", "content": basic_prompt})
            chat_messages.insert(1, {"role": "system", "content": history_prompt})

            # Add the final instruction prompt and user message at the end
            chat_messages.extend([
                {"role": "user", "content": "That was all history. Take a deep breath, relax a little. "
                                            "Think about history you just got, and using this knowledge, try to answer the next question as best as you can."},
                {"role": "user", "content": f"{context.author.name}: {user_message}"}
            ])

            #logger.debug(f"Final chat messages: {chat_messages}")
            return chat_messages

        except Exception as ex:
            logger.exception("Error in assemble_chat_history")
            raise

    def remove_special_chars(self, input):
        return re.sub(r'[^0-9a-zA-Z]', '', input)
