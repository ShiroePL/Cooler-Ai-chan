import discord
from discord.ext import commands
import asyncio

class TeaTimerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tea_timers = {}  # {user_id: (timer, end_time)}
        self.default_times = {}  # {user_id: default_time_in_seconds}

    def parse_time(self, time_str):
        # Replace ',' or '.' with ':' for uniform handling
        time_str = time_str.replace(',', ':').replace('.', ':')

        # Handle different time formats
        if ':' in time_str:
            parts = time_str.split(':')
            if len(parts) == 2:
                minutes, seconds = map(int, parts)
            else:
                raise ValueError("Invalid time format")
        else:
            minutes, seconds = int(time_str), 0

        # Adjust time if seconds > 59
        if seconds > 59:
            minutes += 1
            seconds = 0

        # Limit to 59:59
        minutes = min(minutes, 59)

        return int(minutes * 60 + seconds)

    @commands.hybrid_command(name='tea', help="Start a tea timer. Usage: /tea [time]")
    async def tea(self, ctx, time_str: str = None):
        user_id = ctx.author.id

        if time_str is None:
            if user_id in self.default_times:
                seconds = self.default_times[user_id]
            else:
                await ctx.send("Please provide a time or set a default time with /settea.")
                return
        else:
            try:
                seconds = self.parse_time(time_str)
            except ValueError:
                await ctx.send("Invalid time format. Please use 'm:ss', 'm.ss', 'm,ss' or 'm'")
                return

        # Cancel existing timer if any
        if user_id in self.tea_timers:
            self.tea_timers[user_id][0].cancel()

        # Start new timer
        end_time = ctx.message.created_at.timestamp() + seconds
        timer = asyncio.create_task(self.tea_timer(ctx, seconds))
        self.tea_timers[user_id] = (timer, end_time)

        await ctx.send(f"Tea timer set for {seconds // 60}:{seconds % 60:02d}.")

    async def tea_timer(self, ctx, seconds):
        await asyncio.sleep(seconds)
        await ctx.send(f"{ctx.author.mention}, your tea is ready!")
        del self.tea_timers[ctx.author.id]

    @commands.hybrid_command(name='teahelp', help="Show current tea timer status")
    async def teahelp(self, ctx):
        user_id = ctx.author.id
        embed = discord.Embed(title="Tea Timer Help", color=discord.Color.green())

        if user_id in self.tea_timers:
            _, end_time = self.tea_timers[user_id]
            remaining = max(0, int(end_time - ctx.message.created_at.timestamp()))
            embed.add_field(name="Current Timer", value=f"{remaining // 60}:{remaining % 60:02d}")
        else:
            embed.add_field(name="Current Timer", value="No active timer")

        if user_id in self.default_times:
            default = self.default_times[user_id]
            embed.add_field(name="Default Time", value=f"{default // 60}:{default % 60:02d}")
        else:
            embed.add_field(name="Default Time", value="Not set")

        await ctx.send(embed=embed)

    @commands.hybrid_command(name='settea', help="Set default tea timer. Usage: /settea [time]")
    async def settea(self, ctx, time_str: str):
        try:
            seconds = self.parse_time(time_str)
            self.default_times[ctx.author.id] = seconds
            await ctx.send(f"Default tea timer set to {seconds // 60}:{seconds % 60:02d}.")
        except ValueError:
            await ctx.send("Invalid time format. Please use 'm:ss', 'm.ss', or 'm'.")

    @commands.hybrid_command(name='stoptea', help="Stop the current tea timer")
    async def stoptea(self, ctx):
        user_id = ctx.author.id
        if user_id in self.tea_timers:
            self.tea_timers[user_id][0].cancel()
            del self.tea_timers[user_id]
            await ctx.send("Tea timer stopped.")
        else:
            await ctx.send("No active tea timer to stop.")

async def setup(bot):
    await bot.add_cog(TeaTimerCog(bot))
