import asyncio
import discord
from discord.ext import commands
import requests
from app.utils.ai_related.groq_api import send_to_groq, send_to_groq_vision
from app.utils.ai_related.groq_service import GroqService
from app.utils.logger import logger
from app.utils.command_utils import custom_command
import os
import time
import re

class AICommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.groq_service = GroqService(bot)
        self.last_everyone_ping = 0  # Track timestamp of last @everyone ping
        self.everyone_ping_cooldown = 120  # 2 minutes in seconds

    def filter_everyone_ping(self, response: str) -> str:
        """Remove @everyone ping if on cooldown, otherwise update last ping time"""
        current_time = int(time.time())
        if '@everyone' in response:
            if current_time - self.last_everyone_ping < self.everyone_ping_cooldown:
                # Remove the @everyone ping if on cooldown
                logger.info("Removing @everyone ping due to cooldown")
                return response.replace('@everyone', '')
            else:
                # Update last ping time
                self.last_everyone_ping = current_time
        return response

    # Create helper methods for the commands
    async def _process_ask(self, ctx, question, model):
        try:
            logger.debug(f"------- \nCommand ASK used by user {ctx.author.name} with model {model}")
            messages = await self.groq_service.ask_question(ctx.author.name, ctx.author.id, question)
            response, _, _, _ = send_to_groq(messages, model=model)
            response = self.filter_everyone_ping(response)
            logger.debug(f"Sending response: {response}\n-------------")
            await ctx.send(response)
        except Exception as ex:
            logger.error(f"Error in Ask command: {ex}")
            await ctx.send("Sorry, something went wrong while processing your request.")

    async def _process_chat(self, ctx, question, model):
        try:
            logger.debug(f"------- \nCommand CHAT used by user {ctx.author.name} with model {model}")
            messages = await self.groq_service.assemble_chat_history(ctx)
            messages = await self.groq_service.add_command_messages(ctx, messages, question)
            response, prompt_tokens, completion_tokens, total_tokens = send_to_groq(messages, model=model)
            response = self.filter_everyone_ping(response)
            logger.info(f"Prompt tokens: {prompt_tokens}")
            logger.info(f"Completion tokens: {completion_tokens}")
            logger.info(f"Total tokens: {total_tokens}")
            logger.debug(f"Sending response: {response}\n-------------")
            await ctx.send(response)
        except Exception as ex:
            logger.error(f"Error in Chat command: {ex}")
            await ctx.send("Sorry, something went wrong while processing your request.")

    async def _process_informative_question(self, ctx, question, model):
        try:
            logger.debug(f"------- \nCommand INFORMATIVE QUESTION used by user {ctx.author.name} with model {model}")
            
            # Create a dictionary-specific prompt without web search
            enhanced_question = f"""
            You are a helpful assistant that answers questions that user ask truthfully and honestly.
            User question: {question}

            Format your response using clean Discord markdown for better readability.
"""
            logger.info("Using helpful assistant model")
            
            # Send directly to Groq without the standard prompts
            messages = [
                {"role": "user", "content": enhanced_question}
            ]
            
            logger.info(f"Sending request to AI model: {model}")
            logger.info(f"Messages: {messages}")
            response, prompt_tokens, completion_tokens, total_tokens = send_to_groq(messages, model=model)
            response = self.filter_everyone_ping(response)
            
            logger.info(f"Prompt tokens: {prompt_tokens}")
            logger.info(f"Completion tokens: {completion_tokens}")
            logger.info(f"Total tokens: {total_tokens}")
            logger.debug(f"Sending informative response: {response}\n-------------")
            
            # Check if response is too long for Discord (2000 chars)
            if len(response) <= 2000:
                await ctx.send(response)
            else:
                # Smart splitting that respects markdown
                await self.send_split_message(ctx, response)
            
        except Exception as ex:
            logger.error(f"Error in Informative Question command: {str(ex)}", exc_info=True)
            await ctx.send(f"Sorry, something went wrong while processing your request: {str(ex)}")

    async def _process_dictionary_definition(self, ctx, word, model):
        try:
            logger.debug(f"------- \nCommand DICTIONARY used by user {ctx.author.name} with model {model}")
            
            # Create a dictionary-specific prompt
            dictionary_prompt = f"""
Define the word or phrase: {word}

Respond in a dictionary style format with:
1. Word type (noun, verb, adjective, etc.)
2. Pronunciation guide (if relevant)
3. All different meanings/definitions (if multiple exist)
4. Example sentences showing usage
5. Etymology or origin (if notable)

Keep definitions concise and clear as if from a real dictionary book. Use clean formatting.
"""
            logger.info("Processing dictionary definition request")
            
            # Send directly to Groq without the standard prompts
            messages = [
                {"role": "user", "content": dictionary_prompt}
            ]
            
            logger.info(f"Sending request to AI model for dictionary definition: {model}")
            logger.info(f"Messages: {messages}")
            response, prompt_tokens, completion_tokens, total_tokens = send_to_groq(messages, model=model)
            response = self.filter_everyone_ping(response)
            
            logger.info(f"Prompt tokens: {prompt_tokens}")
            logger.info(f"Completion tokens: {completion_tokens}")
            logger.info(f"Total tokens: {total_tokens}")
            logger.debug(f"Sending dictionary definition: {response}\n-------------")
            
            # Check if response is too long for Discord (2000 chars)
            if len(response) <= 2000:
                await ctx.send(response)
            else:
                # Smart splitting that respects markdown
                await self.send_split_message(ctx, response)
            
        except Exception as ex:
            logger.error(f"Error in Dictionary command: {str(ex)}", exc_info=True)
            await ctx.send(f"Sorry, something went wrong while looking up that word: {str(ex)}")

    async def send_split_message(self, ctx, message):
        """
        Splits a long message intelligently, trying to preserve markdown structure
        """
        try:
            logger.info(f"Splitting message of length {len(message)} characters")
            
            # Maximum Discord message length
            max_length = 2000
            
            # If message is short enough, just send it
            if len(message) <= max_length:
                await ctx.send(message)
                return
                
            # Try to split at markdown headers first
            chunks = []
            header_pattern = re.compile(r'\n#{1,6} ')
            
            # Find all markdown headers
            header_matches = list(header_pattern.finditer(message))
            
            if header_matches and len(header_matches) > 1:
                # First chunk starts at beginning of message
                start_pos = 0
                
                for match in header_matches:
                    match_pos = match.start()
                    
                    # If adding this section would exceed limit, create a new chunk
                    if match_pos - start_pos > max_length:
                        # Find a good breaking point within max_length
                        text_to_split = message[start_pos:start_pos + max_length]
                        
                        # Try to break at a paragraph
                        last_para = text_to_split.rfind('\n\n')
                        if last_para != -1 and last_para > max_length / 2:
                            # Good paragraph break point found
                            chunks.append(message[start_pos:start_pos + last_para])
                            start_pos += last_para
                        else:
                            # No good paragraph, try a line break
                            last_line = text_to_split.rfind('\n')
                            if last_line != -1 and last_line > max_length / 2:
                                chunks.append(message[start_pos:start_pos + last_line])
                                start_pos += last_line + 1
                            else:
                                # No good breaks, force a break at max_length
                                chunks.append(message[start_pos:start_pos + max_length])
                                start_pos += max_length
                    
                    # If we're within limit for a section break
                    if match_pos - start_pos < max_length:
                        chunks.append(message[start_pos:match_pos])
                        start_pos = match_pos
                
                # Add the final chunk
                if start_pos < len(message):
                    chunks.append(message[start_pos:])
            else:
                # No proper headers found, fall back to paragraph splitting
                paragraphs = message.split('\n\n')
                current_chunk = ""
                
                for paragraph in paragraphs:
                    # If adding this paragraph would exceed limit, create a new chunk
                    if len(current_chunk) + len(paragraph) + 2 > max_length:
                        if current_chunk:
                            chunks.append(current_chunk)
                        
                        # If a single paragraph is too long, need to split it
                        if len(paragraph) > max_length:
                            # Split into sentences or even mid-paragraph if needed
                            remaining = paragraph
                            while remaining:
                                if len(remaining) <= max_length:
                                    chunks.append(remaining)
                                    remaining = ""
                                else:
                                    # Try to find a sentence break
                                    last_sentence = remaining[:max_length].rfind('. ')
                                    if last_sentence != -1 and last_sentence > max_length / 2:
                                        chunks.append(remaining[:last_sentence+1])
                                        remaining = remaining[last_sentence+2:]
                                    else:
                                        # No good sentence break, force a break
                                        chunks.append(remaining[:max_length])
                                        remaining = remaining[max_length:]
                        else:
                            current_chunk = paragraph
                    else:
                        if current_chunk:
                            current_chunk += "\n\n" + paragraph
                        else:
                            current_chunk = paragraph
                
                # Add the final chunk
                if current_chunk:
                    chunks.append(current_chunk)
            
            # If we somehow didn't create any chunks, fall back to simple splitting
            if not chunks:
                simple_chunks = [message[i:i+max_length] for i in range(0, len(message), max_length)]
                chunks = simple_chunks
            
            # Send all chunks
            logger.info(f"Sending message in {len(chunks)} chunks")
            for i, chunk in enumerate(chunks):
                if chunk.strip():  # Only send non-empty chunks
                    await ctx.send(chunk)
            
        except Exception as ex:
            logger.error(f"Error in send_split_message: {str(ex)}", exc_info=True)
            # Fall back to simple splitting if smart splitting fails
            for i in range(0, len(message), max_length):
                await ctx.send(message[i:i+max_length])

    async def _process_web_search(self, ctx, word, model):
        try:
            logger.debug(f"------- \nCommand WEB used by user {ctx.author.name} with model {model}")
            
            # Create a dictionary-specific prompt
            dictionary_prompt = f"""
Search the web for the following question: {word}
Keep the response concise and clear. Use clean formatting.
"""
            logger.info("Processing web search request")
            
            # Send directly to Groq without the standard prompts
            messages = [
                {"role": "user", "content": dictionary_prompt}
            ]
            
            logger.info(f"Sending request to AI model for web search: {model}")
            logger.info(f"Messages: {messages}")
            response, prompt_tokens, completion_tokens, total_tokens = send_to_groq(messages, model=model)
            response = self.filter_everyone_ping(response)
            
            logger.info(f"Prompt tokens: {prompt_tokens}")
            logger.info(f"Completion tokens: {completion_tokens}")
            logger.info(f"Total tokens: {total_tokens}")
            logger.debug(f"Sending web search: {response}\n-------------")
            
            # Check if response is too long for Discord (2000 chars)
            if len(response) <= 2000:
                await ctx.send(response)
            else:
                # Smart splitting that respects markdown
                await self.send_split_message(ctx, response)
            
        except Exception as ex:
            logger.error(f"Error in Web Search command: {str(ex)}", exc_info=True)
            await ctx.send(f"Sorry, something went wrong while searching the web: {str(ex)}")
    
    # Command implementations that use the helper methods
    @commands.hybrid_command(name='ask', help="Ask a question to the AI.")
    async def ask_command(self, ctx, *, question):
        await self._process_ask(ctx, question, "meta-llama/llama-4-maverick-17b-128e-instruct")
        
    @commands.hybrid_command(name='web', help="Ask a question to the AI with web search.")
    async def web_command(self, ctx, *, question):
        await self._process_web_search(ctx, question, "compound-beta")

    # doesnt work its too long or something
    #@commands.hybrid_command(name='local_web', help="Ask a question to the AI using newer model.")
    #async def local_ask_command(self, ctx, *, question):
    #    await self._process_ask(ctx, question, "compound-beta-mini")

    #@commands.hybrid_command(name='local_ask', help="Ask a question to the AI using newer model.")
    #async def local_ask_command(self, ctx, *, question):
    #    await self._process_ask(ctx, question, "mlewd-v2.4-13b")

    @commands.hybrid_command(name='chat', help="Chat with the AI.")
    async def chat_command(self, ctx, *, question: str):
        await self._process_chat(ctx, question, "meta-llama/llama-4-maverick-17b-128e-instruct")

    @commands.hybrid_command(
    name='d', 
    aliases=['dict', 'dictionary'],
    help="Look up a dictionary definition."
    )
    async def dictionary_command(self, ctx, *, question: str):
        await self._process_dictionary_definition(ctx, question, "meta-llama/llama-4-maverick-17b-128e-instruct")

    @commands.hybrid_command(
        name='q',
        aliases=['question'],
        help="Search for information using AI."
    )
    async def information_command(self, ctx, *, question: str):
        await self._process_informative_question(ctx, question, "meta-llama/llama-4-maverick-17b-128e-instruct")


    #@commands.hybrid_command(name='local_chat', help="Chat with the AI using newer model.")
    #async def local_chat_command(self, ctx, *, question: str):
    #    await self._process_chat(ctx, question, "mlewd-v2.4-13b")


    @commands.hybrid_command(name='askgpt', help="Ask a question to the AI.")
    async def askgpt(self, ctx, *, question):
        try:
            if ctx.author.id == 366046822885490689:
                await ctx.send("Fuck off Nequs, give me back 6$, and another 6$, then you can use it.")
            else:
                await ctx.send("Sorry, tell Nequs to give me back 6$ + 6$, then you can use it.")
        except Exception as ex:
            logger.error(f"Error in Ask command: {ex}")
            await ctx.send("Sorry, something went wrong while processing your request.")
            
    @commands.hybrid_command(name='tts_test', help="Say a text to the AI.")
    async def tts_test(self, ctx, *, text: str):
        logger.info(f"Say command triggered by {ctx.author.name}")
        try:
            # Print current working directory to know where we are
            current_dir = os.getcwd()
            logger.info(f"Current working directory: {current_dir}")
            
            audio_path = "test_audio.wav"
            full_path = os.path.abspath(audio_path)
            logger.info(f"Attempting to access audio file at: {audio_path}")
            logger.info(f"Full path to audio file: {full_path}")
            
            # Check if file exists
            if not os.path.exists(audio_path):
                logger.error(f"Audio file not found at: {audio_path}")
                await ctx.send("Error: Test audio file not found.")
                return
                
            logger.info("Sending audio file...")
            audio_file = await ctx.send(file=discord.File(audio_path))
            
            
            
        except Exception as e:
            logger.error(f"Error in Say command: {str(e)}", exc_info=True)
            await ctx.send(f"Error: {str(e)}")

    @commands.hybrid_command(name='vision', help="Ask a question to the AI with an image.")
    async def groq_vision(self, ctx, *, question: str):
        try:
            logger.debug(f"------- \nCommand GROQ VISION used by user {ctx.author.name}")
            
            # Check if an attachment is present in the message
            if not ctx.message.attachments:
                await ctx.send("Please upload an image along with your question for this command.")
                return
            
            # Get the first attachment (you can handle multiple if needed)
            attachment = ctx.message.attachments[0]
            attachment_url = attachment.url  # Get the attachment's URL
            logger.debug(f"Attachment URL: {attachment_url}")
            
            await ctx.defer()  # Defer response to avoid timeout
            
            # Send the question and attachment URL to your processing function
            response = await send_to_groq_vision(question, attachment_url)
            
            if isinstance(response, tuple):
                response, _, _, _ = response
            
            logger.debug(f"Sending response: {response}\n-------------")
            
            # Check if response is longer than Discord's message limit (2000 characters)
            if len(response) > 2000:
                for i in range(0, len(response), 2000):
                    await ctx.send(response[i:i+2000])
            else:
                await ctx.send(response)
        
        except Exception as ex:
            logger.error(f"Error in Vision command: {ex}")
            await ctx.send("Sorry, something went wrong while processing your request.")



async def setup(bot):
    logger.info("Setting up AICommands cog...")
    cog = AICommands(bot)
    await bot.add_cog(cog)
    logger.info("AICommands cog setup complete")
