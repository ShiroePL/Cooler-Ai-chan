import re
from app.utils.ai_related.prompt_templates import basic_prompt, history_prompt
from app.utils.logger import logger

class GroqService:
    def __init__(self, bot=None):
        self.basic_prompt = basic_prompt
        self.history_prompt = history_prompt
        self.bot = bot

    async def ask_question(self, author, author_id, user_message):
        try:
            # Gluing discord username to the message
            logger.info(f"Question: {user_message}")
            messages = [
                {"role": "system", "content": basic_prompt},
                {"role": "user", "content": f"{author} ({author_id}): {user_message}"},
            ]
            #logger.debug(f"Messages: {messages}")
            return messages
        except Exception as ex:
            logger.error(f"Error in ask_question: {ex}")
            return "Sorry, something went wrong while processing your request."
        
    async def assemble_chat_history(self, message, include_refs=False):
        """Get chat history with optional reference context
        Args:
            message: The discord message/context object
            include_refs: Whether to include reference information in messages
        """
        try:
            # Handle both Context and Message objects
            if hasattr(message, 'channel'):
                channel = message.channel
            else:
                channel = message

            messages = [msg async for msg in channel.history(limit=30)]

            chat_messages = []
            previous_author = None
            previous_author_id = None
            concatenated_content = ""

            for msg in reversed(messages):
                author = msg.author
                current_author = author.name
                author_id = msg.author.id

                # Handle message references if enabled
                reference_info = ""
                if include_refs and msg.reference and msg.reference.resolved:
                    referenced_msg = msg.reference.resolved
                    reference_info = f" [In reply to: {referenced_msg.author.name}: {referenced_msg.content}]"

                if current_author == previous_author:
                    concatenated_content += "\n" + msg.content + reference_info
                else:
                    if concatenated_content:
                        # Check if bot name is available, otherwise use "AI-Chan"
                        is_assistant = (self.bot and previous_author == self.bot.user.name) or previous_author == "AI-Chan"
                        chat_messages.append({
                            "role": "assistant" if is_assistant else "user",
                            "content": f"{previous_author} ({previous_author_id}): {concatenated_content}"
                        })

                    previous_author = current_author
                    previous_author_id = author_id
                    concatenated_content = msg.content + reference_info

            # Add the last concatenated message
            if concatenated_content:
                # Check if bot name is available, otherwise use "AI-Chan"
                is_assistant = (self.bot and previous_author == self.bot.user.name) or previous_author == "AI-Chan"
                chat_messages.append({
                    "role": "assistant" if is_assistant else "user",
                    "content": f"{previous_author} ({previous_author_id}): {concatenated_content}"
                })

            # Insert the prompts at the beginning
            chat_messages.insert(0, {"role": "system", "content": self.basic_prompt})
            chat_messages.insert(1, {"role": "system", "content": self.history_prompt})

            return chat_messages

        except Exception as ex:
            logger.exception("Error in assemble_chat_history")
            raise


    async def add_command_messages(self, ctx, chat_messages, user_message):

        chat_messages.append({
            "role": "user",
            "content": "That was all history. Take a deep breath, relax a little. "
                    "Think about the history you just got. To mention someone, use their ID like this: <@user_id>. "
                    "Using this knowledge, try to answer the next question as best as you can."
        })
        chat_messages.append({
            "role": "user",
            "content": f"{ctx.author.name} ({ctx.author.id}): {user_message}"
        })
        return chat_messages



    # async def say_good_morning(self, channel_id):
    #     try:
    #         channel = self.bot.get_channel(channel_id)
    #         if channel:
    #             context = await channel.history(limit=30).flatten()
    #             if context:
    #                 chat_history = await self.groq_service.assemble_chat_history(context[0])
    #                 messages = self.groq_service.add_command_messages(chat_history, "Good morning, everyone!", context[0].author)
    #                 additional_message = {
    #                     "role": "user",
    #                     "content": "Now, you're using a function that triggers every morning. Say good morning to everyone, "
    #                             "you can use history to maybe ask about some stuff that transpired before, be funny."
    #                 }
    #                 messages.append(additional_message)
    #                 response, prompt_tokens, completion_tokens, total_tokens = self.groq_service.send_to_groq(messages)
    #                 await channel.send(response)
    #     except Exception as ex:
    #         logger.error(f"Error in say_good_morning: {ex}")




    def remove_special_chars(self, input):
        return re.sub(r'[^0-9a-zA-Z]', '', input)

    