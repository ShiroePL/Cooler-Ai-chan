import discord
import random
import asyncio
from app.services.database_service import DatabaseService

class GamblingService:
    def __init__(self):
        self.database = DatabaseService()
        self.joinable = True

    async def russian_game(self, users, ctx, total_exp):
        fear_kaomojis = [
            "＼(〇_ｏ)／", "(;;;*_*)", "〜(＞＜)〜", "(ﾉ_ヽ)", 
            "Σ(°△°|||)︴", "(″ロ゛)", "(ノωヽ)", "(/ω＼)"
        ]
        pain_kaomojis = [
            "~(>_<~)", "☆⌒(> _ <)", "☆⌒(>。<)", "(☆_@)", 
            "(×_×)", "٩(× ×)۶", "(×﹏×)"
        ]
        joy_kaomojis = [
            "(* ^ ω ^)", "(((o(°▽°)o)))", "(✯◡✯)", "o(>ω <)o", 
            "(⁀ᗢ⁀)", "ヽ(o＾▽＾o)ノ", "(￣ω￣)", "(⌒▽⌒)☆"
        ]

        self.joinable = False
        i = 0

        while len(users) > 1:
            await ctx.send(f"{users[i].name} presses the revolver to their head and slowly squeezes the trigger... {random.choice(fear_kaomojis)}")
            await asyncio.sleep(3.5)

            if random.randint(0, 2) == 1:
                await ctx.send(f"BOOOM! {users[i].mention} goes down! {random.choice(pain_kaomojis)}")
                users.pop(i)
                i -= 1
            else:
                await ctx.send(f"CLICK! {users[i].mention} passes the gun along.")

            i += 1
            if i == len(users):
                i = 0

        winner = users[0]
        await ctx.send(f"{winner.mention} Congratulations! You won {total_exp} exp! {random.choice(joy_kaomojis)}")
        level_up , _ = self.database.add_exp(winner.id, total_exp)

        if level_up:
            await ctx.send(f"Congratulations {winner.mention}! You leveled up!")

        self.joinable = True

async def level_up_message(ctx):
    return f"🎉 Level Up! 🎉 Congratulations! {ctx.author.mention}, you've leveled up! ヽ(^o^)ノ"

async def level_down_message(ctx):
    return f"💔 Oh no! 💔 {ctx.author.mention}, you've leveled down... (；￣Д￣)"