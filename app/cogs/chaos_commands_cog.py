import discord
from discord.ext import commands
import asyncio
from app import config
from app.utils.command_utils import custom_command
from app.utils.logger import logger
import re

master_user_id = config.Config.master_user_id

class ChaosCommands(commands.Cog):
    """A collection of chaotic commands for fun and mischief."""
    def __init__(self, bot):
        self.bot = bot

    @custom_command(name='timeout', help="Temporarily mutes a user for a specified duration.")
    async def timeout(self, ctx, member: discord.Member, duration: int = 20):
        """
        Temporarily restrict a user from sending messages for the specified duration (default 20 seconds).
        """
        if ctx.author.id != master_user_id:
            await ctx.send("You are not authorized to use this command.")
            return
        
        role = discord.utils.get(ctx.guild.roles, name='Muted')
        
        # If the role doesn't exist, create it
        if not role:
            role = await ctx.guild.create_role(name='Muted', reason='To use for muting users temporarily')
            for channel in ctx.guild.channels:
                await channel.set_permissions(role, send_messages=False, speak=False)
        
        await member.add_roles(role)
        await ctx.send(f'{member.mention} has been muted for {duration} seconds as a prank!')

        await asyncio.sleep(duration)
        
        await member.remove_roles(role)
        await ctx.send(f'{member.mention} has been unmuted.')
    

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            # If the bot is responding to a command, track the user who initiated the command
            if message.reference and message.reference.resolved:
                referenced_message = message.reference.resolved
                if referenced_message.author != self.bot.user:
                    self.last_command_user[message.channel.name] = referenced_message.author.name
            return  
        
        # roblox filter
        roblox_patterns = [
            r"\b(?:r[\W_]*o[\W_]*b[\W_]*l[\W_]*o[\W_]*x)\b",  # Matches 'roblox' with variations
            r"\b(?:r[\W_]*o[\W_]*b[\W_]*u[\W_]*x)\b",          # Matches 'robux' with variations
            r"\b(?:b[\W_]*l[\W_]*o[\W_]*x)\b",                 # Matches 'blox' with variations
            r"\b(?:b[\W_]*l[\W_]*o[\W_]*s)\b"                  # Matches 'blos' with variations
        ]

        if any(re.search(pattern, message.content, re.IGNORECASE) for pattern in roblox_patterns):
            logger.debug(f"Roblox word detected in message: {message.content}")
            await message.delete()
            await message.channel.send(f"<:pandafbi:1195713733142511706>{message.author.mention} said: **{message.content}** and we don't want roblox here! <:deletedis:1196019787084615770>")

async def setup(bot):
    await bot.add_cog(ChaosCommands(bot))
