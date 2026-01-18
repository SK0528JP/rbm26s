import discord
from discord import app_commands
from discord.ext import commands

class YouTubeChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.google_blue = 0x4285F4
        self.target_url = "https://youtube.com/channel/UC1owxxoNexXWbJ-ri7r5-ww?si=rR2ig4XU0uUe1gso"

    @app_commands.command(name="yt-channel", description="公式YouTubeチャンネルへの案内を表示します。")
    async def channel_guide(self, interaction: discord.Interaction):
        """公式YouTubeチャンネルへの誘導カードをデプロイします。"""
        
        # デザイン：視認性を重視したインフォメーションカード
        embed = discord.Embed(
            title="Official YouTube Channel",
            description="最新の動画コンテンツやライブ配信をお届けしています。\nぜひチャンネル登録をして、更新をお待ちください。",
            url=self.target_url,
            color=self.google_blue
        )

        # チャンネルのアイコン（YouTube公式のファビコンを借用）
        embed.set_author(
            name="YouTubeで開く", 
            url=self.target_url,
            icon_url="https://www.gstatic.com/youtube/img/branding/favicon/favicon_144x144.png"
        )

        # 誘導を促す画像（必要に応じてバナー画像等のURLに変更可能です）
        # embed.set_image(url="https://path_to_your_banner.png")

        # 押しやすいボタンコンポーネント
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label="チャンネルを表示", 
            style=discord.ButtonStyle.link, 
            url=self.target_url
        ))

        embed.set_footer(text="Rb m/26S Information System • 瑞典技術設計局")

        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(YouTubeChannel(bot))
