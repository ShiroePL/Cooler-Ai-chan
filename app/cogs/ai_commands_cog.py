import asyncio
import discord
from discord.ext import commands
import requests
from app.utils.ai_related.groq_api import send_to_groq, send_to_groq_vision
from app.utils.ai_related.groq_service import GroqService
from app.utils.ai_related.chatgpt_api import send_to_openai_vision, send_to_openai_gpt, send_to_openai, ask_gpt
from app.utils.logger import logger
from app.utils.command_utils import custom_command
import os
import time

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

    # Command implementations that use the helper methods
    @commands.hybrid_command(name='ask', help="Ask a question to the AI.")
    async def ask_command(self, ctx, *, question):
        await self._process_ask(ctx, question, "meta-llama/llama-4-maverick-17b-128e-instruct")
        
    @commands.hybrid_command(name='new_ask', help="Ask a question to the AI using newer model.")
    async def new_ask_command(self, ctx, *, question):
        await self._process_ask(ctx, question, "meta-llama/llama-4-maverick-17b-128e-instruct")

    #@commands.hybrid_command(name='local_ask', help="Ask a question to the AI using newer model.")
    #async def local_ask_command(self, ctx, *, question):
    #    await self._process_ask(ctx, question, "mlewd-v2.4-13b")

    @commands.hybrid_command(name='chat', help="Chat with the AI.")
    async def chat_command(self, ctx, *, question: str):
        await self._process_chat(ctx, question, "meta-llama/llama-4-maverick-17b-128e-instruct")

    @commands.hybrid_command(name='new_chat', help="Chat with the AI using newer model.")
    async def new_chat_command(self, ctx, *, question: str):
        await self._process_chat(ctx, question, "meta-llama/llama-4-maverick-17b-128e-instruct")

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
