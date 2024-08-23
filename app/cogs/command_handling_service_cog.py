import random
import os
import json
import re
from discord.ext import commands
from discord.utils import get
from app.services.database_service import DatabaseService
from app.config import Config
from app.utils.logger import logger
from datetime import datetime

class CommandHandlingService(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database = DatabaseService()
        self.log_file_index = 0
        self.max_messages_per_file = 1000  # Example threshold
        self.log_directory = "app/persistent_data/logs/message_logs"
        os.makedirs(self.log_directory, exist_ok=True)
        self.current_log_file = self.get_latest_log_file()
        logger.info("CommandHandlingService initialized")
        self.previous_author = {}  # Dictionary to track the last author per channel
        self.last_command_user = {}

    def get_new_log_file(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file_index += 1
        return os.path.join(self.log_directory, f"log_{timestamp}_{self.log_file_index}.json")

    def get_latest_log_file(self):
        log_files = sorted(os.listdir(self.log_directory), reverse=True)
        if log_files:
            latest_log_file = os.path.join(self.log_directory, log_files[0])
            with open(latest_log_file, 'r') as f:
                data = json.load(f)
            if len(data) < self.max_messages_per_file:
                self.log_file_index = int(log_files[0].split('_')[-1].split('.')[0])  # Update the log file index
                return latest_log_file
        
        return self.get_new_log_file()

    def sanitize_message(self, message):
        # Replace mentions with usernames
        sanitized_message = message.content
        for user_mention in message.mentions:
            sanitized_message = sanitized_message.replace(f"<@{user_mention.id}>", f"@{user_mention.name}")
        return sanitized_message

    def log_message(self, author, channel, message):
        if not message.content and message.attachments:
            return  # Skip logging if the message is empty and only contains attachments

        sanitized_message = self.sanitize_message(message)

        log_entry = {
            "author": str(author),
            "channel": str(channel),
            "message": sanitized_message,
        }

        if not os.path.exists(self.current_log_file):
            with open(self.current_log_file, 'w') as f:
                json.dump([log_entry], f, indent=4)
        else:
            with open(self.current_log_file, 'r+') as f:
                data = json.load(f)
                data.append(log_entry)
                f.seek(0)
                json.dump(data, f, indent=4)

        if len(data) >= self.max_messages_per_file:
            self.current_log_file = self.get_new_log_file()

    @commands.Cog.listener()
    async def on_message(self, message):
        logger.debug("----------")
        if message.author.bot:
            # If the bot is responding to a command, track the user who initiated the command
            if message.reference and message.reference.resolved:
                referenced_message = message.reference.resolved
                if referenced_message.author != self.bot.user:
                    self.last_command_user[message.channel.name] = referenced_message.author.name
            return  

        
        # Check if the message is a command
        if message.content.startswith(Config.PREFIX):
            self.last_command_user[message.channel.name] = message.author.name
            return

        # Clear the last command user if someone else sends a message
        channel_name = message.channel.name
        author_name = message.author.name
        channel_id = message.channel.id
        author_id = message.author.id
        if self.last_command_user.get(channel_name) == author_name:
            pass
        elif not message.author.bot:
            self.last_command_user[channel_name] = None

        # Respond to greetings
        greetings = ["hello", "hi", "yo", "hey", "ohayo", "henlo", "oi", "ahoy"]
        if any(word in message.content.lower().split() for word in greetings):
            logger.debug(f"Greeting detected in message: {message.content}")
            emote = get(self.bot.emojis, name="hi")
            if emote:
                logger.debug(f"Emote 'hi' found: {emote}")
                await message.add_reaction(emote)
            else:
                logger.error("Emote 'hi' not found in the server.")

        

        # Lottery reaction
        if random.randint(1, 100000) == 1:
            emote = random.choice(message.guild.emojis)
            await message.add_reaction(emote)
            exp_gain = random.randint(10, 100)
            await message.channel.send(f"{message.author.mention}!! You just won a lottery with 0.001% chance! +{exp_gain} exp for you for free!")
            self.database.add_exp(message.author.id, exp_gain)

        # Level up for chatting
        if os.path.exists(self.database.path):
            if channel_id not in self.previous_author:
                self.previous_author[channel_id] = None  # Initialize if not present

            # Allow users and the bot to gain experience points but ensure users get exp even after bot responses
            if self.previous_author[channel_id] != author_id and self.last_command_user.get(channel_id) != author_id:
                level_up, _ = self.database.add_exp(author_id, 1)
                if level_up:
                    await message.channel.send(f"🎉 Level Up! 🎉 Congratulations! {message.author.mention}! You leveled up from babbling so much!\n GRIND GRIND GRIND")

            self.previous_author[channel_id] = author_id
        logger.info(f"Message from {message.author} in {message.channel}: {message.content}")
        


        

        # Log the message
        self.log_message(message.author, message.channel, message)
        print(f"last command user: {self.last_command_user}")
        # Process message
        user = message.author
        channel = message.channel
        #logger.debug(f"Processing message from {user} in {channel}: {message.content}")
        logger.debug("----------")
        await self.bot.process_commands(message)

    @commands.Cog.listener()
    async def on_command_error(self, context, error):
        if isinstance(error, commands.CommandInvokeError):
            await context.send(f"Error: {str(error)}")

async def setup(bot):  
    await bot.add_cog(CommandHandlingService(bot))