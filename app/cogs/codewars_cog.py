import discord
from discord.ext import commands
import aiohttp
import asyncio
from datetime import datetime
import re
from app.utils.logger import logger
from app.utils.command_utils import custom_command

class CodewarsCog(commands.Cog):
    """Codewars integration commands. Use +codewarshelp for more info."""
    
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://www.codewars.com/api/v1"
        self.session = None
        
    async def get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    def cog_unload(self):
        if self.session:
            asyncio.create_task(self.session.close())
    
    def get_rank_color(self, rank_color):
        """Convert Codewars rank color to Discord embed color."""
        color_map = {
            'white': 0xFFFFFF,
            'yellow': 0xFFFF00,
            'blue': 0x0099FF,
            'purple': 0x9900FF,
            'black': 0x000000,
            'red': 0xFF0000
        }
        return color_map.get(rank_color.lower(), 0x00FF00)
    
    def truncate_text(self, text, max_length=1000):
        """Truncate text to fit in embed fields."""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    async def make_api_request(self, endpoint):
        """Make a request to the Codewars API."""
        session = await self.get_session()
        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    return None
                else:
                    logger.error(f"API request failed: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error making API request: {e}")
            return None
    
    @commands.hybrid_command(name='codewarshelp', help="Show the Codewars help message.")
    async def show_codewars_help(self, ctx):
        embed = discord.Embed(title="⚔️ Codewars Commands Help ⚔️", color=0xFF6600)
        
        embed.add_field(name="User Commands", value=(
            "**`+cwuser <username>`** - Get user profile information\n"
            "**`+cwcompleted <username>`** - Show completed challenges\n"
            "**`+cwauthored <username>`** - Show authored challenges\n"
            "**`+cwbest <username>`** - Show user's best/highest rated kata"
        ), inline=False)
        
        embed.add_field(name="Kata Commands", value=(
            "**`+kata <kata_name_or_slug>`** - Get kata information\n"
            "**`+getkyu <1-8>`** - Get a random kata of specific kyu level\n"
            "**`+randomkata`** - Get a random kata recommendation"
        ), inline=False)
        
        embed.add_field(name="Examples", value=(
            "• `+cwuser whiteneko` - Get whiteneko's profile\n"
            "• `+getkyu 4` - Get a 4 kyu kata\n"
            "• `+kata valid-braces` - Get info about Valid Braces kata"
        ), inline=False)
        
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)
    
    @custom_command(name='cwuser', help="Get Codewars user information. Usage: +cwuser <username>")
    async def get_user(self, ctx, username: str):
        if not username:
            await ctx.send("Please provide a username!")
            return
        
        user_data = await self.make_api_request(f"users/{username}")
        
        if not user_data:
            await ctx.send(f"User `{username}` not found on Codewars!")
            return
        
        overall_rank = user_data.get('ranks', {}).get('overall', {})
        rank_color = self.get_rank_color(overall_rank.get('color', 'white'))
        
        embed = discord.Embed(
            title=f"⚔️ {user_data.get('username', username)}",
            color=rank_color,
            url=f"https://www.codewars.com/users/{username}"
        )
        
        if user_data.get('name'):
            embed.add_field(name="Name", value=user_data['name'], inline=True)
        
        embed.add_field(name="Honor", value=f"🏆 {user_data.get('honor', 0):,}", inline=True)
        
        if user_data.get('clan'):
            embed.add_field(name="Clan", value=user_data['clan'], inline=True)
        
        if user_data.get('leaderboardPosition'):
            embed.add_field(name="Leaderboard Position", value=f"#{user_data['leaderboardPosition']:,}", inline=True)
        
        # Overall rank
        if overall_rank:
            embed.add_field(
                name="Overall Rank",
                value=f"**{overall_rank.get('name', 'Unranked')}** ({overall_rank.get('score', 0):,} points)",
                inline=True
            )
        
        # Code challenges stats
        challenges = user_data.get('codeChallenges', {})
        if challenges:
            embed.add_field(
                name="Challenges",
                value=f"✅ Completed: {challenges.get('totalCompleted', 0)}\n📝 Authored: {challenges.get('totalAuthored', 0)}",
                inline=True
            )
        
        # Skills
        skills = user_data.get('skills', [])
        if skills:
            skills_text = ", ".join(skills[:10])  # Show first 10 skills
            if len(skills) > 10:
                skills_text += f" (+{len(skills) - 10} more)"
            embed.add_field(name="Skills", value=skills_text, inline=False)
        
        # Top languages
        languages = user_data.get('ranks', {}).get('languages', {})
        if languages:
            top_langs = sorted(languages.items(), key=lambda x: x[1].get('score', 0), reverse=True)[:5]
            lang_text = ""
            for lang, rank_info in top_langs:
                lang_text += f"**{lang.title()}**: {rank_info.get('name', 'Unranked')} ({rank_info.get('score', 0)} pts)\n"
            embed.add_field(name="Top Languages", value=lang_text, inline=False)
        
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)
    
    @custom_command(name='cwcompleted', help="Show user's completed challenges. Usage: +cwcompleted <username>")
    async def get_completed(self, ctx, username: str, page: int = 0):
        if not username:
            await ctx.send("Please provide a username!")
            return
        
        completed_data = await self.make_api_request(f"users/{username}/code-challenges/completed?page={page}")
        
        if not completed_data:
            await ctx.send(f"No completed challenges found for `{username}`!")
            return
        
        embed = discord.Embed(
            title=f"⚔️ {username}'s Completed Challenges",
            color=0x00FF00,
            url=f"https://www.codewars.com/users/{username}"
        )
        
        total_items = completed_data.get('totalItems', 0)
        total_pages = completed_data.get('totalPages', 0)
        
        embed.add_field(
            name="Statistics",
            value=f"📊 Total: {total_items:,} challenges\n📄 Page: {page + 1}/{total_pages}",
            inline=False
        )
        
        challenges = completed_data.get('data', [])[:10]  # Show first 10
        
        for challenge in challenges:
            completed_at = datetime.fromisoformat(challenge['completedAt'].replace('Z', '+00:00'))
            languages = ", ".join(set(challenge.get('completedLanguages', [])))
            
            embed.add_field(
                name=f"🎯 {challenge['name']}",
                value=f"**Completed:** {completed_at.strftime('%Y-%m-%d')}\n**Languages:** {languages}",
                inline=True
            )
        
        embed.set_footer(text=f"Requested by {ctx.author} • Use +cwcompleted {username} <page> for more", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)
    
    @custom_command(name='cwauthored', help="Show user's authored challenges. Usage: +cwauthored <username>")
    async def get_authored(self, ctx, username: str):
        if not username:
            await ctx.send("Please provide a username!")
            return
        
        authored_data = await self.make_api_request(f"users/{username}/code-challenges/authored")
        
        if not authored_data or not authored_data.get('data'):
            await ctx.send(f"No authored challenges found for `{username}`!")
            return
        
        embed = discord.Embed(
            title=f"📝 {username}'s Authored Challenges",
            color=0xFF6600,
            url=f"https://www.codewars.com/users/{username}"
        )
        
        challenges = authored_data.get('data', [])
        embed.add_field(name="Total Authored", value=f"📊 {len(challenges)} challenges", inline=False)
        
        for challenge in challenges[:10]:  # Show first 10
            rank_text = challenge.get('rankName', 'Unranked')
            tags = ", ".join(challenge.get('tags', [])[:3])  # Show first 3 tags
            languages = ", ".join(challenge.get('languages', [])[:5])  # Show first 5 languages
            
            description = self.truncate_text(challenge.get('description', 'No description'), 100)
            
            embed.add_field(
                name=f"⚔️ {challenge['name']} ({rank_text})",
                value=f"**Tags:** {tags}\n**Languages:** {languages}\n**Description:** {description}",
                inline=False
            )
        
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)
    
    @custom_command(name='kata', help="Get kata information. Usage: +kata <kata_name_or_slug>")
    async def get_kata(self, ctx, *, kata_identifier: str):
        if not kata_identifier:
            await ctx.send("Please provide a kata name or slug!")
            return
        
        kata_data = await self.make_api_request(f"code-challenges/{kata_identifier}")
        
        if not kata_data:
            await ctx.send(f"Kata `{kata_identifier}` not found!")
            return
        
        rank = kata_data.get('rank', {})
        rank_color = self.get_rank_color(rank.get('color', 'white'))
        
        embed = discord.Embed(
            title=f"⚔️ {kata_data['name']}",
            color=rank_color,
            url=kata_data.get('url', f"https://www.codewars.com/kata/{kata_data['slug']}")
        )
        
        embed.add_field(name="Rank", value=rank.get('name', 'Unranked'), inline=True)
        embed.add_field(name="Category", value=kata_data.get('category', 'Unknown').title(), inline=True)
        embed.add_field(name="Vote Score", value=f"⭐ {kata_data.get('voteScore', 0)}", inline=True)
        
        embed.add_field(name="Completions", value=f"✅ {kata_data.get('totalCompleted', 0):,}", inline=True)
        embed.add_field(name="Attempts", value=f"🎯 {kata_data.get('totalAttempts', 0):,}", inline=True)
        embed.add_field(name="Stars", value=f"⭐ {kata_data.get('totalStars', 0):,}", inline=True)
        
        # Languages
        languages = kata_data.get('languages', [])
        if languages:
            embed.add_field(name="Languages", value=", ".join(languages), inline=False)
        
        # Tags
        tags = kata_data.get('tags', [])
        if tags:
            embed.add_field(name="Tags", value=", ".join(tags), inline=False)
        
        # Description
        description = kata_data.get('description', 'No description available')
        description = self.truncate_text(description, 500)
        embed.add_field(name="Description", value=description, inline=False)
        
        # Author
        created_by = kata_data.get('createdBy', {})
        if created_by:
            embed.add_field(name="Created By", value=created_by.get('username', 'Unknown'), inline=True)
        
        # Published date
        published_at = kata_data.get('publishedAt')
        if published_at:
            pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            embed.add_field(name="Published", value=pub_date.strftime('%Y-%m-%d'), inline=True)
        
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)
    
    @custom_command(name='getkyu', help="Get a random kata of specific kyu level. Usage: +getkyu <1-8>")
    async def get_kyu_kata(self, ctx, kyu_level: int):
        if kyu_level < 1 or kyu_level > 8:
            await ctx.send("Kyu level must be between 1 and 8!")
            return
        
        # Since the API doesn't provide direct filtering, we'll get a user's completed
        # challenges and filter for the specific kyu level
        await ctx.send(f"🔍 Searching for {kyu_level} kyu kata... (This might take a moment)")
        
        # This is a simplified implementation - in a real bot you might want to
        # maintain a database of kata or use a different approach
        embed = discord.Embed(
            title=f"⚔️ {kyu_level} Kyu Kata Search",
            color=0xFF6600,
            description=f"Unfortunately, the Codewars API doesn't provide direct filtering by kyu level. "
                       f"You can search for specific kata using `+kata <kata_name>` or browse "
                       f"https://www.codewars.com/kata/search?q=&r%5B%5D=-{kyu_level}&tags=&beta=false"
        )
        
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)
    
    @custom_command(name='cwbest', help="Show user's best/highest rated kata. Usage: +cwbest <username>")
    async def get_best_kata(self, ctx, username: str):
        if not username:
            await ctx.send("Please provide a username!")
            return
        
        # First get user info to check their rank
        user_data = await self.make_api_request(f"users/{username}")
        if not user_data:
            await ctx.send(f"User `{username}` not found on Codewars!")
            return
        
        # Get their completed challenges
        completed_data = await self.make_api_request(f"users/{username}/code-challenges/completed")
        if not completed_data or not completed_data.get('data'):
            await ctx.send(f"No completed challenges found for `{username}`!")
            return
        
        overall_rank = user_data.get('ranks', {}).get('overall', {})
        user_rank = overall_rank.get('rank', 0)
        rank_color = self.get_rank_color(overall_rank.get('color', 'white'))
        
        embed = discord.Embed(
            title=f"🏆 {username}'s Profile & Recent Challenges",
            color=rank_color,
            url=f"https://www.codewars.com/users/{username}"
        )
        
        embed.add_field(name="Current Rank", value=overall_rank.get('name', 'Unranked'), inline=True)
        embed.add_field(name="Honor", value=f"🏆 {user_data.get('honor', 0):,}", inline=True)
        embed.add_field(name="Completed", value=f"✅ {user_data.get('codeChallenges', {}).get('totalCompleted', 0)}", inline=True)
        
        # Show recent challenges
        recent_challenges = completed_data.get('data', [])[:5]
        
        embed.add_field(name="Recent Completions", value="Latest challenges completed:", inline=False)
        
        for challenge in recent_challenges:
            completed_at = datetime.fromisoformat(challenge['completedAt'].replace('Z', '+00:00'))
            languages = ", ".join(set(challenge.get('completedLanguages', []))[:3])
            
            embed.add_field(
                name=f"⚔️ {challenge['name']}",
                value=f"**When:** {completed_at.strftime('%Y-%m-%d')}\n**Languages:** {languages}",
                inline=True
            )
        
        # Recommendation based on user's rank
        if user_rank:
            if user_rank >= -2:  # 1-2 kyu
                recommendation = "Try some 1-2 kyu challenges to push your limits!"
            elif user_rank >= -4:  # 3-4 kyu
                recommendation = "You're doing great! Consider 2-3 kyu challenges for growth."
            elif user_rank >= -6:  # 5-6 kyu
                recommendation = "Keep practicing with 4-5 kyu challenges to improve."
            else:  # 7-8 kyu
                recommendation = "Focus on 6-7 kyu challenges to build fundamentals."
            
            embed.add_field(name="💡 Recommendation", value=recommendation, inline=False)
        
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)
    
    @custom_command(name='randomkata', help="Get a random kata recommendation")
    async def random_kata(self, ctx):
        # This would ideally pull from a curated list of good kata
        # For now, we'll show a message about the limitation
        embed = discord.Embed(
            title="🎲 Random Kata",
            color=0xFF6600,
            description="The Codewars API doesn't provide random kata endpoints. "
                       "Here are some popular kata to try:\n\n"
                       "• **Two Sum** - Find two numbers that add up to target\n"
                       "• **Valid Braces** - Check if brackets are properly closed\n"
                       "• **Multiples of 3 and 5** - Classic FizzBuzz variant\n"
                       "• **Roman Numerals Encoder** - Convert numbers to Roman numerals\n"
                       "• **Sudoku Solution Validator** - Validate Sudoku solutions\n\n"
                       "Use `+kata <kata_name>` to get details about any of these!"
        )
        
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CodewarsCog(bot))
