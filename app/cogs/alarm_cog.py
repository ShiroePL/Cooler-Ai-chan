from datetime import datetime
from discord.ext import commands
import discord
import asyncio
import re
import logging
import time
from app.services.database_service import DatabaseService
from app.utils.logger import logger


class AlarmCog(commands.Cog):
    """Alarm commands. use **+alarmhelp** for more info."""

    def __init__(self, bot):
        self.bot = bot
        self.database = DatabaseService()
        self.alarms = {}

    @commands.hybrid_command(name='alarmhelp', help="Show the alarm help message.")
    async def show_alarm_help(self, ctx):
        embed = discord.Embed(title="⏰ Alarm Help ⏰", color=0x00FF00)
        embed.add_field(name="How to Use Alarms, prefix '+' or '/' commands", value=(
            "1. **Set an Alarm:** Use the command `+alarm [time] [note]`. Example: **`+alarm 20d 1h 10m 5s meeting`**\n"
            "2. **Stop an Alarm:** Use the command `+alarmstop [dynamic_id]` to stop an active alarm. Example: **`+alarmstop 1`**\n"
            "3. **List Alarms:** Use the command `+alarmlist` to view all active alarms.\n"
            "4. **Clear Alarms:** Use the command `+alarmclear` to stop all active alarms.\n"
            "**Dynamic ID:** The ID for stopping an alarm is dynamically assigned in the list. It starts from 1 for the nearest alarm."
        ), inline=False)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)


    @commands.hybrid_command(name='alarm', help="Set an alarm. Usage: +alarm 5m [note] or +alarm 5d 1h 30m 10s [note]")
    async def alarm(self, ctx, *, args: str):
        user_id = ctx.message.author.id
        channel_id = ctx.message.channel.id
        if not args:
            await ctx.send("Please provide a valid time format and an optional note.")
            return

        # Separate time and note
        time_str, note = self.extract_time_and_note(args.split())

        try:
            seconds = self.parse_time(time_str)
            if seconds is None or seconds > 31536000:  # Limit to 365 days (365 * 86400)
                await ctx.send("Please use a valid time format (e.g., 5m, 10s, 1h 30m 10s, 7d) and within 365 days.")
                return

            trigger_time = int(time.time()) + seconds

            user_alarms = self.database.get_user_alarms(user_id)
            if len(user_alarms) >= 10:
                await ctx.send("You have reached the maximum limit of 10 active alarms.")
                return

            task = self.bot.loop.create_task(self.start_alarm(ctx, trigger_time, note))
            alarm_id = self.database.insert_alarm(user_id, channel_id, trigger_time, note)
            self.alarms[alarm_id] = task
            await ctx.send(f"Alarm set for {time_str}. I will notify you when the time is up. Note: {note}")

        except ValueError as e:
            await ctx.send(f"An error occurred: {e}")


    @commands.hybrid_command(name='alarmstop', help="Stop the current alarm if one is set. Usage: +stop_alarm [dynamic_id]")
    async def stop_alarm(self, ctx, dynamic_id: int = None):
        user_id = ctx.message.author.id
        user_alarms = sorted(self.database.get_user_alarms(user_id), key=lambda x: x[1])
        if dynamic_id is None or dynamic_id < 1 or dynamic_id > len(user_alarms):
            await ctx.send("Please provide a valid dynamic ID of the alarm you want to stop.")
            return

        alarm_id = user_alarms[dynamic_id - 1][0]  # Get the actual alarm ID from the dynamic ID

        if alarm_id in self.alarms:
            self.alarms[alarm_id].cancel()
            self.database.delete_alarm(alarm_id)
            del self.alarms[alarm_id]
            await ctx.send(f"Alarm {dynamic_id} has been cancelled, {ctx.message.author.mention}.")
        else:
            await ctx.send(f"Alarm {dynamic_id} does not exist, {ctx.message.author.mention}.")

    @commands.hybrid_command(name='alarmlist', help="List active alarms. Usage: +alarmlist [optional: username]")
    async def alarm_list(self, ctx, username: str = None):
        if username is None:
            # Show alarms for the command user
            user_id = ctx.author.id
            target_user = ctx.author
        else:
            # Try to find the specified user
            target_user = None
            for guild in self.bot.guilds:
                for member in guild.members:
                    if username.lower() in member.name.lower() or (member.nick and username.lower() in member.nick.lower()):
                        target_user = member
                        break
                if target_user:
                    break
            
            if target_user is None:
                await ctx.send(f"User '{username}' not found.")
                return
            
            user_id = target_user.id
        
        user_alarms = sorted(self.database.get_user_alarms(user_id), key=lambda x: x[1])
        if not user_alarms:
            if username is None:
                await ctx.send("You don't have any active alarms.")
            else:
                await ctx.send(f"{target_user.display_name} doesn't have any active alarms.")
            return

        embed = discord.Embed(
            title=f"⏰ Active Alarms for {target_user.display_name} ⏰", 
            color=0x00FF00
        )
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)

        for idx, alarm in enumerate(user_alarms):
            alarm_id, trigger_time, note = alarm
            trigger_time_dt = datetime.fromtimestamp(trigger_time)
            time_remaining = trigger_time_dt - datetime.now()
            time_remaining_str = str(time_remaining).split('.')[0]  # Remove microseconds

            # Truncate note if it's too long
            if len(note) > 50:
                note = note[:50] + "..."

            embed.add_field(
                name=f"Alarm {idx + 1}",
                value=(
                    f"**Time:** {trigger_time_dt.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"**In:** {time_remaining_str}\n"
                    f"**Note:** {note}"
                ),
                inline=True
            )

        await ctx.send(embed=embed)


    @commands.hybrid_command(name="alarmclear", help="Stop all active alarms for the user.")
    async def stop_all_alarms(self, ctx):
        user_id = ctx.message.author.id
        user_alarms = self.database.get_user_alarms(user_id)
        for alarm in user_alarms:
            alarm_id = alarm[0]
            if alarm_id in self.alarms:
                self.alarms[alarm_id].cancel()
                del self.alarms[alarm_id]
        self.database.delete_user_alarms(user_id)
        await ctx.send(f"All alarms have been cancelled, {ctx.message.author.mention}.")

    async def start_alarm(self, ctx, trigger_time, note):
        await asyncio.sleep(max(0, trigger_time - int(time.time())))
        await ctx.send(f"{ctx.message.author.mention} Time's up! Note: {note}")
        user_id = ctx.message.author.id
        alarm_id = self.get_alarm_id_by_user_time(user_id, trigger_time)
        if alarm_id in self.alarms:
            del self.alarms[alarm_id]
            self.database.delete_alarm(alarm_id)

    def get_alarm_id_by_user_time(self, user_id, trigger_time):
        alarms = self.database.get_user_alarms(user_id)
        for alarm in alarms:
            if alarm[1] == trigger_time:
                return alarm[0]
        return None

    def extract_time_and_note(self, args):
        """Extract time and note from arguments."""
        logger.info(f"Extracting time and note from args: {args}")
        time_str = []
        note = []
        for arg in args:
            if re.match(r'^\d+[dhms]$', arg.lower()):
                time_str.append(arg)
            else:
                note.append(arg)
        extracted_time_str = ' '.join(time_str)
        extracted_note = ' '.join(note)
        logger.info(f"Extracted time: {extracted_time_str}, note: {extracted_note}")
        return extracted_time_str, extracted_note

    def parse_time(self, time_str: str) -> int:
        """Parse the time string and return the time in seconds."""
        time_str = time_str.strip().lower()
        total_seconds = 0
        matches = re.findall(r'(\d+)([dhms])', time_str)

        if not matches:
            logger.error(f"No matches found in time string: {time_str}")
            return None

        for value, unit in matches:
            value = int(value)
            if unit == 's':
                total_seconds += value
            elif unit == 'm':
                total_seconds += value * 60
            elif unit == 'h':
                total_seconds += value * 3600
            elif unit == 'd':
                total_seconds += value * 86400

        logger.info(f"Parsed time string '{time_str}' to {total_seconds} seconds.")
        return total_seconds if total_seconds > 0 else None



    async def check_existing_alarms(self):
        """Check for existing alarms in the database and schedule them."""
        logger.info("Retrieving alarms from the database...")
        try:
            alarms = self.database.get_alarms()
            logger.info(f"Retrieved {len(alarms)} alarms from the database.")
            current_time = int(time.time())
            for alarm_id, user_id, channel_id, trigger_time, note in alarms:
                logger.info(f"Processing alarm: {alarm_id}, User: {user_id}, Channel: {channel_id}, Time: {trigger_time}, Note: {note}")
                channel = self.bot.get_channel(channel_id)
                if not channel:
                    logger.error(f"Channel {channel_id} not found for alarm {alarm_id}")
                    continue
                
                if trigger_time <= current_time:
                    # Alarm time has passed, send a notification after a short delay
                    logger.info(f"Alarm {alarm_id} time has passed. Scheduling missed alarm notification.")
                    self.bot.loop.create_task(self.send_missed_alarm(channel, user_id, trigger_time, note, alarm_id))
                else:
                    # Schedule future alarms
                    logger.info(f"Scheduling future alarm: {alarm_id}")
                    task = self.bot.loop.create_task(self.resume_alarm(channel, user_id, trigger_time, note, alarm_id))
                    self.alarms[alarm_id] = task
            logger.info("Completed checking existing alarms.")
        except Exception as e:
            logger.error(f"Error while checking existing alarms: {e}")

    async def send_missed_alarm(self, channel, user_id, trigger_time, note, alarm_id):
        try:
            await asyncio.sleep(10)  # Wait for the bot to start successfully
            await channel.send(f"<@{user_id}> Your alarm was missed while the bot was offline. Note: {note}")
            self.database.delete_alarm(alarm_id)
        except Exception as e:
            logger.error(f"Error while sending missed alarm: {e}")

    async def resume_alarm(self, channel, user_id, trigger_time, note, alarm_id):
        try:
            await asyncio.sleep(max(0, trigger_time - int(time.time())))
            await channel.send(f"<@{user_id}> Time's up! Note: {note}")
            if alarm_id in self.alarms:
                del self.alarms[alarm_id]
                self.database.delete_alarm(alarm_id)
        except Exception as e:
            logger.error(f"Error while resuming alarm: {e}")

async def setup(bot):
    await bot.add_cog(AlarmCog(bot))