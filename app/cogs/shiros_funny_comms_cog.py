import discord
from discord.ext import commands
from app import config
import re

class ShirosCommands(commands.Cog):
    """A collection of chaotic commands for fun and mischief."""
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='bigger', help="Make the emote bigger, just use command and put emote. It's slash/prefix command.") # this works with prefix and slash, but prefix not deleting 
    async def bigger(self, ctx, emote: str):
        """
        Takes an emote name and replaces the command message with the emote URL.
        """
        # Regex to find the emote ID from the message
        emote_pattern = re.compile(r'<a?:\w+:(\d+)>')
        match = emote_pattern.search(emote)
        
        if match:
            emote_id = match.group(1)
            emote_url = f'https://cdn.discordapp.com/emojis/{emote_id}.webp?size=128&quality=lossless'
            await ctx.send(emote_url)
        else:
            await ctx.send("Emote not found. Please use a valid emote.")

async def setup(bot):
    await bot.add_cog(ShirosCommands(bot))