import discord
from discord.ext import commands

class PollManager:
    def __init__(self):
        self.polls = {}  # channel_id -> most recent poll message
    
    def remember_poll(self, message):
        """Store a message as a poll if it meets the criteria"""
        # Use Discord's native Poll API - polls are attached to messages
        if hasattr(message, 'poll') and message.poll is not None:
            self.polls[message.channel.id] = message
            return True
        
        # Fallback for our custom polls if they have a specific embed format
        if message.embeds and len(message.embeds) > 0 and message.embeds[0].title and "POLL:" in message.embeds[0].title:
            self.polls[message.channel.id] = message
            return True
            
        return False
            
    async def pollcheck(self, ctx):
        """Reply to the most recent poll in the channel"""
        channel_id = ctx.channel.id
        
        if channel_id in self.polls:
            poll_message = self.polls[channel_id]
            # Create a reference to the poll message
            reference = discord.MessageReference(
                message_id=poll_message.id, 
                channel_id=poll_message.channel.id, 
                guild_id=poll_message.guild.id
            )
            
            # If it's a Discord native poll, add some info about it
            if hasattr(poll_message, 'poll') and poll_message.poll is not None:
                poll = poll_message.poll
                await ctx.send(f"Here's the poll: **{poll.question}** (Total votes: {poll.total_votes})", 
                              reference=reference)
            else:
                await ctx.send("Here's the most recent poll! Click this message to jump to it.", 
                              reference=reference)
        else:
            # Try to fetch recent messages and find a poll
            try:
                # Get the last 50 messages in the channel
                async for message in ctx.channel.history(limit=50):
                    # Check if this message has a poll
                    if hasattr(message, 'poll') and message.poll is not None:
                        self.polls[channel_id] = message
                        reference = discord.MessageReference(
                            message_id=message.id, 
                            channel_id=message.channel.id, 
                            guild_id=message.guild.id
                        )
                        poll = message.poll
                        await ctx.send(f"Found a poll: **{poll.question}** (Total votes: {poll.total_votes})", 
                                      reference=reference)
                        return
            except Exception as e:
                print(f"Error searching for polls: {e}")
                
            await ctx.send("No polls have been created in this channel recently!")
    
    async def markpoll(self, ctx, message_id=None):
        """Manually mark a message as a poll by ID"""
        if not message_id:
            await ctx.send("Please provide a message ID to mark as a poll.")
            return
            
        try:
            # Try to fetch the message
            message = await ctx.channel.fetch_message(message_id)
            # Check if it's actually a poll
            is_poll = self.remember_poll(message)
            
            if is_poll:
                await ctx.send("That message has been marked as a poll!")
            else:
                # Force mark it as a poll anyway
                self.polls[ctx.channel.id] = message
                await ctx.send("Message marked as a poll (though it doesn't appear to be a native Discord poll).")
        except discord.NotFound:
            await ctx.send("I couldn't find a message with that ID in this channel.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

class PollCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.poll_manager = PollManager()
        
    @commands.Cog.listener()
    async def on_message(self, message):
        # Process all messages to detect polls
        self.poll_manager.remember_poll(message)
        
    @commands.Cog.listener()
    async def on_raw_message_update(self, payload):
        """Listen for message updates that might be polls being created"""
        # Message updates sometimes happen when Discord adds a poll to a message
        channel = self.bot.get_channel(payload.channel_id)
        if channel:
            try:
                message = await channel.fetch_message(payload.message_id)
                self.poll_manager.remember_poll(message)
            except:
                pass
    
    @commands.command()
    async def pollcheck(self, ctx):
        """Replies to the most recent poll in the channel"""
        await self.poll_manager.pollcheck(ctx)
    
    @commands.command()
    async def markpoll(self, ctx, message_id: int = None):
        """Manually mark a message as a poll"""
        await self.poll_manager.markpoll(ctx, message_id)
    
    @commands.command()
    async def poll(self, ctx, question, *options):
        """
        Creates a poll with the given question and options
        Usage: +poll "Is this a good bot?" "Yes" "No" "Maybe"
        """
        if len(options) < 2:
            await ctx.send("You need to provide at least 2 options for a poll!")
            return
            
        if len(options) > 9:
            await ctx.send("You can only have up to 9 options in a poll!")
            return
            
        # Create embed with poll format
        embed = discord.Embed(title=f"POLL: {question}", color=discord.Color.blue())
        
        for i, option in enumerate(options):
            embed.add_field(name=f"Option {i+1}", value=option, inline=False)
        
        poll_message = await ctx.send(embed=embed)
        
        # Add reactions
        for i in range(len(options)):
            await poll_message.add_reaction(f"{i+1}\u20e3")
        
        # Remember this poll
        self.poll_manager.polls[ctx.channel.id] = poll_message

async def setup(bot):
    await bot.add_cog(PollCog(bot)) 