import re
import discord
from discord.ext import commands
from app.services.database_service import DatabaseService
from app.utils.whiteneko_words import WORDS
import random
import asyncio

class WhitenekoModule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database = DatabaseService()
        self.words = WORDS

    @commands.guild_only()
    @commands.has_permissions(kick_members=True, ban_members=True)
    @commands.command(name='nickreset')
    async def reset(self, ctx):
        """Resets all users' nicknames to their default values."""
        for user in ctx.guild.members:
            try:
                await user.edit(nick=None)
            except Exception as ex:
                print(f"Error resetting nickname for user {user.name}: {ex}")

    @commands.command(name='spam')
    async def spam(self, ctx, j: int, *, text: str):
        """Sends a specified message multiple times.
        
        Args:
            j (int): The number of times to send the message.
            text (str): The message to send.
        """
        # Anti-roblox filter for nequs
        roblox_patterns = [
            r"r[\W_]*o[\W_]*b[\W_]*l[\W_]*o[\W_]*x", 
            r"r[\W_]*o[\W_]*b[\W_]*u[\W_]*x", 
            r"b[\W_]*l[\W_]*o[\W_]*x", 
            r"b[\W_]*l[\W_]*o[\W_]*s",
            r"b[\W_]*l[\W_]*o"
        ]
        
        # Check if any pattern matches the text content
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in roblox_patterns):
            await ctx.message.delete()
            await ctx.send(f"<:pandafbi:1195713733142511706>{ctx.author.mention} tried to spam: **{text}** and we don't want roblox here! <:deletedis:1196019787084615770>")
        else:
            await ctx.message.delete()
            for _ in range(j):
                await ctx.send(text)

    @commands.command(name='dm')
    async def dm(self, ctx, user: discord.Member, *, text: str):
        """Sends a direct message to a specified user.
        
        Args:
            user (discord.Member): The user to send the message to.
            text (str): The message to send.
        """
        await ctx.message.delete()
        await user.send(text)
        
    @commands.guild_only()
    @commands.has_permissions(kick_members=True, ban_members=True)
    @commands.command(name='operation')
    async def operation(self, ctx, user: discord.Member):
        """Counts down and kicks a specified user from the server.
        
        Args:
            user (discord.Member): The user to kick.
        """
        for i in range(10, 0, -1):
            await ctx.send(f"Operation {user.mention} starts in {i}...")
            await asyncio.sleep(1)
        await ctx.send(f"Bayo {user.mention}! You have committed war crimes and you are banished to death!")
        await user.kick()

    @commands.guild_only()
    @commands.has_permissions(kick_members=True, ban_members=True)
    @commands.command(name='advertise')
    async def advertise(self, ctx, *, text: str):
        """Sends a specified message to all users via direct message.
        
        Args:
            text (str): The message to send.
        """
        for user in ctx.guild.members:
            try:
                await user.send(text)
            except Exception as ex:
                print(f"Error sending message to user {user.name}: {ex}")

    @commands.guild_only()
    @commands.has_permissions(kick_members=True, ban_members=True)
    @commands.command(name='lmao')
    async def lmao(self, ctx):
        """Changes all users' nicknames to random combinations of words."""
        for user in ctx.guild.members:
            try:
                nickname = f"{random.choice(self.words)} {random.choice(self.words)}"
                await user.edit(nick=nickname)
            except Exception as ex:
                print(ex)

    @commands.guild_only()
    @commands.has_permissions(kick_members=True, ban_members=True)
    @commands.command(name='lmaoo')
    async def lmaoo(self, ctx):
        """Changes all text channel names to random combinations of words."""
        for text_channel in ctx.guild.text_channels:
            try:
                name = f"{random.choice(self.words)} {random.choice(self.words)}"
                await text_channel.edit(name=name)
            except Exception as ex:
                print(ex)

    @commands.command(name='autobots_roll_out')
    async def roll_out(self, ctx):
        """Sends a link to a Transformers GIF."""
        await ctx.send("https://tenor.com/view/roll-out-optimus-transformers-optimusprime-gif-8983715")

async def setup(bot):
    await bot.add_cog(WhitenekoModule(bot))
