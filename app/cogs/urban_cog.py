import discord
from discord.ext import commands
import aiohttp
from app.utils.logger import logger
from app.utils.embeds import get_urban_embed
from app.services.database_service import DatabaseService
from app.utils.command_utils import custom_command

class UrbanModule(commands.Cog):
    """Urban dictionary services - paid 1 exp per use"""
    def __init__(self, bot):
        self.bot = bot
        self.database = DatabaseService()
        self.get_urban_embed = get_urban_embed

    @commands.hybrid_command(name='urban', help="urban dictionary")
    async def get_urban_dictionary_definition(self, ctx, *, term: str):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"https://api.urbandictionary.com/v0/define?term={term}") as response:
                    if response.status != 200:
                        await ctx.send("Failed to fetch data from Urban Dictionary.")
                        return

                    data = await response.json()
                    results = data.get('list', [])

                    if not results:
                        await ctx.send("Nothing's here.")
                        return

                    page_size = 2  # Number of definitions to display per page
                    results = results[:page_size]

                    embed = self.get_urban_embed(term, results)
                    message = await ctx.send(embed=embed)
                    custom_emoji = "<:kiana:496046467090219040>"

                    try:
                        await message.add_reaction(custom_emoji)
                    except discord.HTTPException:
                        logger.error(f"Unknown Emoji: {custom_emoji}")
            except Exception as ex:
                logger.error(f"Error: {ex}")
                await ctx.send("An error occurred while processing your request.")

async def setup(bot):
    await bot.add_cog(UrbanModule(bot))
