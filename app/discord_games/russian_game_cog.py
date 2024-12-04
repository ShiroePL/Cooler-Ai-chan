import asyncio
from discord.ext import commands
from app.services.gambling_service import GamblingService
from app.services.database_service import DatabaseService
from app.utils.command_utils import custom_command

class RussianGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot       
        self.database = DatabaseService()
        self.gambling_service = GamblingService()
        self.time = 0

    @commands.hybrid_command(name='russian')
    async def russian(self, ctx, exp: str):
        try:
            if not self.gambling_service.joinable:
                await ctx.send("Game has already been started!")
                return

            try:
                amount = int(exp)
            except ValueError:
                await ctx.send("You need to specify an amount of exp you want to bet!\nex. +russian 30")
                return

            total_exp = 0
            message = await ctx.send("React to participate ↑_(ΦwΦ)Ψ")
            await message.add_reaction('💀')

            users = []

            def check(reaction, user):
                return str(reaction.emoji) == '💀' and reaction.message.id == message.id

            timer = 15
            while timer > 0:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=1, check=check)
                    if user not in users and not user.bot:
                        users.append(user)
                except asyncio.TimeoutError:
                    pass
                timer -= 1

            if len(users) < 2:
                await ctx.send("EVERYONE scared to join huh? Minimum 2 cattos required for the game to start!")
                return

            for user in users:
                if self.database.get_total_exp(user.id) < amount:
                    await ctx.send(f"{user.mention} is broke as heck and cannot join\nGo get some exp and don't waste OUR time")
                    users.remove(user)
                else:
                    self.database.add_exp(user.id, -amount)
                    total_exp += amount

            if len(users) >= 2:
                await ctx.send("THE GAME IS ABOUT TO BEGIN!")
                await self.gambling_service.russian_game(users, ctx, total_exp)
            else:
                await ctx.send("EVERYONE scared to join huh? Minimum 2 cattos required for the game to start!")

        except Exception as e:
            print(e)

async def setup(bot):
    await bot.add_cog(RussianGame(bot))
