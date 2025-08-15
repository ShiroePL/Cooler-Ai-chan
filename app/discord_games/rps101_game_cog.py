import random
import aiohttp
import discord
from discord.ext import commands
from app.services.gambling_service import GamblingService
from app.services.database_service import DatabaseService
from app.utils.logger import logger
from app.utils.embeds import create_rps101_embed  # Assuming you store your embed functions here
from app.utils.command_utils import custom_command
from app.utils.helpers import get_bot_name_from_context

class RPS101Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database = DatabaseService()
        self.gambling_service = GamblingService()

    @commands.hybrid_command(name='rps')
    async def rps101(self, ctx, thing: str, bet: int):
        try:
            print(f"Received command: +rps {thing} {bet}")
            initial_bet = bet
            if bet <= 0:
                await ctx.send("Invalid bet amount. Please specify a positive bet.")
                return

            user_id = ctx.author.id
            total_exp = self.database.get_total_exp(user_id)
            print(f"User {user_id} has {total_exp} total exp")

            if total_exp < bet:
                await ctx.send("You don't have enough exp to place that bet.")
                return
            else:
                level_up, level_down = self.database.add_exp(user_id, -bet)
                print(f"Deducted {bet} exp from user {user_id}")

            async with aiohttp.ClientSession() as session:
                async with session.get("https://rps101.pythonanywhere.com/api/v1/objects/all") as response:
                    items_response = await response.json()
                    print(f"Items response: {items_response}")

                    if isinstance(items_response, list):
                        items = items_response
                    elif isinstance(items_response, dict) and "objects" in items_response:
                        items = items_response["objects"]
                    else:
                        raise ValueError("Unexpected items response format")
                    print(f"Available items: {items}")

                bot_choice = random.choice(items)
                print(f"Bot choice: {bot_choice}")

                async with session.get(f"https://rps101.pythonanywhere.com/api/v1/match?object_one={thing}&object_two={bot_choice}") as response:
                    match_response = await response.json()
                    print(f"Match response: {match_response}")

                winner = match_response.get("winner")
                outcome = match_response.get("outcome")
                loser = match_response.get("loser")
                print(f"Match result - Winner: {winner}, Outcome: {outcome}, Loser: {loser}")

                if not winner or not loser:
                    await ctx.send("Something went wrong with the match result.")
                    return

                result_message = ""
                color = discord.Color.default()

                win_amount = 0
                
                if winner.lower() == thing.lower():
                    bet += bet * 0.5  # bet plus 50% bonus for winning
                    win_amount = bet
                    level_up, level_down = self.database.add_exp(user_id, bet)
                    result_message = f"🎉 You won! **{winner}** {outcome} **{loser}** 🎉"
                    color = discord.Color.green()
                elif loser.lower() == thing.lower():
                    result_message = f"💔 You lost! **{winner}** {outcome} **{loser}**. Better luck next time! 💔"
                    color = discord.Color.red()
                else:
                    result_message = "🤝 It's a draw. Better luck next time 🤝"
                    color = discord.Color.orange()

                bot_name = get_bot_name_from_context(ctx)
                embed = await create_rps101_embed(ctx, thing, bot_choice, result_message, initial_bet, color, win_amount, bot_name)
                await ctx.send(embed=embed)

                if level_up:
                    await ctx.send(f"🎉 Congratulations {ctx.author.mention}! You've leveled up! ヽ(^o^)ノ")
                elif level_down:
                    await ctx.send(f"💔 Oh no, {ctx.author.mention}! You've leveled down... (；￣Д￣)")
        except Exception as ex:
            logger.error(f"An error occurred: {ex}")
            print(f"An error occurred: {ex}")
            # Refund the bet amount if an error occurs
            self.database.add_exp(user_id, bet)
            await ctx.send("An error occurred. Your exp has been refunded. Please try again later.")

async def setup(bot):
    await bot.add_cog(RPS101Game(bot))
