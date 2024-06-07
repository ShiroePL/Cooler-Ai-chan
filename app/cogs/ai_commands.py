import discord
from discord.ext import commands
from app.utils.ai_related.groq_api import send_to_groq
from app.utils.ai_related.groq_service import GroqService
from app.utils.logger import logger
groq_service = GroqService()
class AICommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.groq_service = None
        
    def get_groq_service(self):
        if self.groq_service is None:
            self.groq_service = GroqService()
        return self.groq_service
    


    @commands.command(name='ask')
    async def ask(self, ctx, *, question):
        try:
            logger.debug(f"------- \nCommand ASK used by user {ctx.author.name}")
            messages = await groq_service.ask_question(ctx.author.name, question)
            response, _, _, _ = send_to_groq(messages)
            logger.debug(f"Sending response: {response}\n-------------")
            await ctx.send(response)
        except Exception as ex:
            logger.error(f"Error in Ask command: {ex}")
            await ctx.send("Sorry, something went wrong while processing your request.")
        
    

    @commands.command()
    async def chat(self, ctx, *, question: str):
        try:
            logger.debug(f"------- \nCommand CHAT used by user {ctx.author.name}")
            
            messages = await groq_service.assemble_chat_history(ctx, question)
            response, prompt_tokens, completion_tokens, total_tokens = send_to_groq(messages)
            logger.info(f"Prompt tokens: {prompt_tokens}")
            logger.info(f"Completion tokens: {completion_tokens}")
            logger.info(f"Total tokens: {total_tokens}")
            logger.debug(f"Sending response: {response}\n-------------")
            await ctx.send(response)
        except Exception as ex:
            logger.error(f"Error in Chat command: {ex}")
            await ctx.send("Sorry, something went wrong while processing your request.")


async def setup(bot):
    await bot.add_cog(AICommands(bot))
