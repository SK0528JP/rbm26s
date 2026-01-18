import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="システムの稼働状況および応答速度を確認します。")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        
        # 北欧風デザイン：シンプルかつ清潔感のあるブルー系を選択
        embed = discord.Embed(
            title="System Operational Status",
            color=0x005B99, # スウェーデン国旗のブルーを想起させる色
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Connection", value="🟢 Stable", inline=True)
        embed.add_field(name="Latency", value=f"{latency}ms", inline=True)
        embed.set_footer(text="Rb m/26S | 瑞典技術設計局")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Ping(bot))
