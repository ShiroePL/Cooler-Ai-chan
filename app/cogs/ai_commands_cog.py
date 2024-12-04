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

class AICommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.groq_service = GroqService()  
         

    @commands.hybrid_command(name='ask', help="Ask a question to the AI.")
    async def ask(self, ctx, *, question):
        try:
            logger.debug(f"------- \nCommand ASK used by user {ctx.author.name}")
            messages = await self.groq_service.ask_question(ctx.author.name, ctx.author.id, question)
            response, _, _, _ = send_to_groq(messages)
            logger.debug(f"Sending response: {response}\n-------------")
            await ctx.send(response)
        except Exception as ex:
            logger.error(f"Error in Ask command: {ex}")
            await ctx.send("Sorry, something went wrong while processing your request.")
        
    

    @commands.hybrid_command(name='chat', help="Chat with the AI.")
    async def chat(self, ctx, *, question: str):
        try:
            logger.debug(f"------- \nCommand CHAT used by user {ctx.author.name}")
            messages = await self.groq_service.assemble_chat_history(ctx)
            messages = await self.groq_service.add_command_messages(ctx, messages, question)
            response, prompt_tokens, completion_tokens, total_tokens = send_to_groq(messages)
            logger.info(f"Prompt tokens: {prompt_tokens}")
            logger.info(f"Completion tokens: {completion_tokens}")
            logger.info(f"Total tokens: {total_tokens}")
            logger.debug(f"Sending response: {response}\n-------------")
            await ctx.send(response)
        except Exception as ex:
            logger.error(f"Error in Chat command: {ex}")
            await ctx.send("Sorry, something went wrong while processing your request.")

    @commands.hybrid_command(name='askgpt', help="Ask a question to the AI.")
    async def askgpt(self, ctx, *, question):
        try:
            logger.debug(f"------- \nCommand ASK used by user {ctx.author.name}")
            messages = await ask_gpt(ctx.author.name, ctx.author.id, question)
            
            # Defer the response to avoid timeout
            await ctx.defer()

            # Send the "bot is thinking" message
            thinking_message = await ctx.send("🤔 I'm thinking...")

            try:
                # Await the send_to_openai function with a timeout
                response = await asyncio.wait_for(send_to_openai_gpt(messages), timeout=20.0)
            except asyncio.TimeoutError:
                await thinking_message.delete()
                await ctx.send("Sorry, the request timed out. Please try again.")
                return
            
            if isinstance(response, tuple):
                response, _, _, _ = response

            logger.debug(f"Sending response: {response}\n-------------")
            
            # Delete the "bot is thinking" message
            await thinking_message.delete()

            # Split the response into chunks if it exceeds the Discord message limit
            if len(response) > 2000:
                for i in range(0, len(response), 2000):
                    await ctx.send(response[i:i+2000])
            else:
                await ctx.send(response)
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


    @commands.hybrid_command(name='oldask', help="Ask a question to the AI.")
    async def oldask(self, ctx, *, question):
        try:
            logger.debug(f"------- \nCommand ASK used by user {ctx.author.name}")
            messages = await self.groq_service.ask_question(ctx.author.name, ctx.author.id, question)
            response, _, _, _ = send_to_openai(messages)
            logger.debug(f"Sending response: {response}\n-------------")
            await ctx.send(response)
        except Exception as ex:
            logger.error(f"Error in Ask command: {ex}")
            await ctx.send("Sorry, something went wrong while processing your request.")
        
    

    @commands.hybrid_command(name='oldchat', help="Chat with the AI.")
    async def oldchat(self, ctx, *, question: str):
        try:
            logger.debug(f"------- \nCommand CHAT used by user {ctx.author.name}")
            
            messages = await self.groq_service.assemble_chat_history(ctx)
            messages = await self.groq_service.add_command_messages(ctx, messages, question)
            response, prompt_tokens, completion_tokens, total_tokens = send_to_openai(messages)
            logger.info(f"Prompt tokens: {prompt_tokens}")
            logger.info(f"Completion tokens: {completion_tokens}")
            logger.info(f"Total tokens: {total_tokens}")
            logger.debug(f"Sending response: {response}\n-------------")
            await ctx.send(response)
        except Exception as ex:
            logger.error(f"Error in Chat command: {ex}")
            await ctx.send("Sorry, something went wrong while processing your request.")

    @commands.hybrid_command(name='vision', help="Ask a question to the AI with an image.")
    async def vision(self, ctx, *args, attachment: discord.Attachment = None):
        try:
            question = " ".join(args)  # This will combine all the arguments into one string
            logger.debug(f"------- \nCommand VISION used by user {ctx.author.name}")
            logger.debug(f"Attachment: {attachment}")
            # Check if an attachment was provided
            if attachment is None and ctx.message.attachments:
                attachment = ctx.message.attachments[0]

            if attachment:
                await ctx.defer()  # Defer the response to avoid timeout
                attachment_url = attachment.url  # Get the attachment's URL
                
                # Correctly await and unpack the response
                response = await send_to_openai_vision(question, attachment_url)
                
                if isinstance(response, tuple):
                    response, _, _, _ = response

                logger.debug(f"Sending response: {response}\n-------------")
                
                # Split the response into chunks if it exceeds the Discord message limit
                if len(response) > 2000:
                    for i in range(0, len(response), 2000):
                        await ctx.send(response[i:i+2000])
                else:
                    await ctx.send(response)
            else:
                await ctx.send("No attachments found. Please upload an image with your question.")
        except Exception as ex:
            logger.error(f"Error in Vision command: {ex}")
            await ctx.send("Sorry, something went wrong while processing your request.")

    @commands.hybrid_command(name='groq_vision', help="Ask a question to the AI with an image.")
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
