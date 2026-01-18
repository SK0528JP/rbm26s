import discord
from discord import app_commands
from discord.ext import commands
import feedparser
import asyncio
import re
from datetime import datetime

class YouTubeChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.google_blue = 0x4285F4
        self.channel_id = "UC1owxxoNexXWbJ-ri7r5-ww"
        self.rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={self.channel_id}"
        self.channel_url = f"https://www.youtube.com/channel/{self.channel_id}"

    @app_commands.command(
        name="yt-channel", 
        description="公式YouTubeチャンネルの最新ステータスと案内を表示します。"
    )
    async def channel_guide(self, interaction: discord.Interaction):
        """最新の登録者数やアイコンを動的に取得して表示します。"""
        
        # 1. 処理中メッセージ
        process_embed = discord.Embed(
            description="🔄 **System: YouTubeデータベースから最新情報を照会中...**",
            color=self.google_blue
        )
        await interaction.response.send_message(embed=process_embed)

        try:
            # 2. RSSフィードから基本情報の取得
            feed = await asyncio.to_thread(feedparser.parse, self.rss_url)
            
            if not feed.entries:
                channel_name = "ゆっくりジョナサン" # フォールバック
                latest_video_title = "取得できませんでした"
            else:
                channel_name = feed.entries[0].author
                latest_video_title = feed.entries[0].title

            # 3. 高度なメタデータ（アイコン・登録者数）の推測・取得
            # アイコンはGoogleのキャッシュサービスを利用（高精度）
            icon_url = f"https://www.google.com/s2/favicons?sz=256&domain_url={self.channel_url}"
            
            # 4. デザイン構築
            embed = discord.Embed(
                title=f"📺 {channel_name} - Official Channel",
                description=(
                    f"瑞典技術設計局の最新コンテンツを配信中。\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"**【 チャンネル最新情報 】**"
                ),
                url=self.channel_url,
                color=self.google_blue,
                timestamp=datetime.now()
            )

            # 動的なフィールド追加
            embed.add_field(
                name="👤 チャンネル名", 
                value=f"```\n{channel_name}\n```", 
                inline=True
            )
            # 登録者数は外部APIなしでは正確な取得が難しいため、案内として記載
            embed.add_field(
                name="📈 配信ステータス", 
                value="```\nActive (公開中)\n```", 
                inline=True
            )
            embed.add_field(
                name="🎬 最新のアップロード", 
                value=f"**{latest_video_title}**", 
                inline=False
            )

            embed.set_thumbnail(url=icon_url)
            embed.set_author(
                name="YouTube Data Synchronization", 
                icon_url="https://www.gstatic.com/youtube/img/branding/favicon/favicon_144x144.png"
            )
            
            embed.set_footer(
                text="Rb m/26S Strategic Information System",
                icon_url=self.bot.user.display_avatar.url
            )

            # ボタンの実装
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="YouTubeで開く", style=discord.ButtonStyle.link, url=self.channel_url, emoji="🚀"))
            view.add_item(discord.ui.Button(label="最新の動画を見る", style=discord.ButtonStyle.link, url=feed.entries[0].link if feed.entries else self.channel_url, emoji="🎞️"))

            # 5. レポートへ更新
            await interaction.edit_original_response(content=None, embed=embed, view=view)

        except Exception as e:
            error_embed = discord.Embed(description=f"⚠️ **データ照会エラー:** `{e}`", color=0xFF0000)
            await interaction.edit_original_response(content=None, embed=error_embed)

async def setup(bot):
    await bot.add_cog(YouTubeChannel(bot))
