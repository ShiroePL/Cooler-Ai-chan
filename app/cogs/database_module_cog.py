import discord
from discord.ext import commands
from app.services.database_service import DatabaseService
from app.utils.command_utils import custom_command
from app.utils.helpers import get_bot_name_from_context

class DatabaseModule(commands.Cog):
    """Pls do not mess with it
    """
    def __init__(self, bot):
        self.bot = bot
        self.database = DatabaseService()

    @commands.hybrid_command(name='levelinfo')
    async def get_user(self, ctx):
        user_id = ctx.author.id
        info = self.database.get_level_info(user_id)
        await ctx.send(f"Gozaimas! o/ How's grinding?\nLevel: {info[0]}\nExperience: {info[1]}\nTotal Experience: {info[2]}")

    @commands.hybrid_command(name='botinfo')
    async def bot_info(self, ctx):
        bot_name = get_bot_name_from_context(ctx)
        bot_id = 452541322667229194
        info = self.database.get_level_info(bot_id)
        await ctx.send(f"Here are {bot_name}'s stats! OwO\nLevel: {info[0]}\nExperience: {info[1]}")

    @commands.hybrid_command(name='leaderboard')
    async def get_leaderboard(self, ctx):
        leaderboard = self.database.get_leaderboard()
        await ctx.send(leaderboard)

    @custom_command(name='addexp')
    async def add_exp(self, ctx, number: str):
        try:
            await ctx.send("HAHA! You wish! Turned off for now!")
            # amount = int(number)
            # level_up = self.database.add_exp(ctx.author.id, amount)
            # await ctx.send(f"Added {amount} exp.")
            # if level_up:
            #     await ctx.send("Congratulations! You've leveled up to the next level.")
        except ValueError:
            await ctx.send("Invalid number.")

    @commands.hybrid_command(name='listusers')
    async def list_users(self, ctx):
        self.database.list_users()
        await ctx.send("Listed all users in the console.")

async def setup(bot):
    await bot.add_cog(DatabaseModule(bot))
