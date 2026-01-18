import discord
from discord import app_commands
from discord.ext import commands

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="ボットの応答速度を測定します")
    async def ping(self, interaction: discord.Interaction):
        """生存確認用コマンド"""
        # 応答速度をミリ秒で計算
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(
            f"Pong! (応答速度: {latency}ms)\nRb m/26S システムは正常に稼働中です。",
            ephemeral=False
        )

async def setup(bot):
    await bot.add_cog(Ping(bot))
