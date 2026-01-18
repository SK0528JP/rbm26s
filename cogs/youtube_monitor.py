import discord
from discord import app_commands
from discord.ext import commands, tasks
import feedparser
import json
import os
import asyncio
from datetime import datetime

class YouTubeMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = "UC1owxxoNexXWbJ-ri7r5-ww"
        self.rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={self.channel_id}"
        self.config_path = "config.json"
        self.history_path = "last_video_id.txt"
        self.google_blue = 0x4285F4  # Google製品のような鮮やかなブルー
        
        self.monitor_loop.start()

    def cog_unload(self):
        self.monitor_loop.cancel()

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                try:
                    return json.load(f)
                except:
                    return {"channel_id": None, "role_id": None}
        return {"channel_id": None, "role_id": None}

    def save_config(self, channel_id, role_id):
        with open(self.config_path, "w") as f:
            json.dump({"channel_id": channel_id, "role_id": role_id}, f, indent=4)

    def get_last_id(self):
        if os.path.exists(self.history_path):
            with open(self.history_path, "r") as f:
                return f.read().strip()
        return ""

    def save_last_id(self, video_id):
        with open(self.history_path, "w") as f:
            f.write(video_id)

    @tasks.loop(minutes=5)
    async def monitor_loop(self):
        """YouTubeをチェックして新しい動画があれば通知します"""
        config = self.load_config()
        target_channel_id = config.get("channel_id")
        target_role_id = config.get("role_id")

        if not target_channel_id:
            return

        try:
            feed = feedparser.parse(self.rss_url)
            if not feed.entries:
                return

            latest_video = feed.entries[0]
            video_id = latest_video.yt_videoid
            video_url = latest_video.link
            video_title = latest_video.title
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            
            last_id = self.get_last_id()

            if video_id != last_id:
                channel = self.bot.get_channel(int(target_channel_id))
                if channel:
                    # デザイン：すっきりとしたカード風UI
                    embed = discord.Embed(
                        title=video_title,
                        url=video_url,
                        description="新しい動画がアップロードされました。",
                        color=self.google_blue,
                        timestamp=datetime.now()
                    )
                    embed.set_author(name="YouTube Update", icon_url="https://www.gstatic.com/youtube/img/branding/favicon/favicon_144x144.png")
                    embed.set_image(url=thumbnail_url)
                    embed.set_footer(text="Rb m/26S • 瑞典技術設計局")

                    mention = f"<@&{target_role_id}>" if target_role_id else ""
                    await channel.send(content=mention, embed=embed)
                    self.save_last_id(video_id)
        except Exception as e:
            print(f"Error in monitor loop: {e}")

    @app_commands.command(name="admin-yt-setup", description="通知先のチャンネルとロールを設定します。")
    @app_commands.describe(channel="通知を受け取るチャンネル", role="通知時にメンションするロール")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction, channel: discord.TextChannel, role: discord.Role):
        """管理者が通知設定を行うためのコマンド"""
        try:
            self.save_config(channel.id, role.id)
            
            embed = discord.Embed(
                title="設定を保存しました",
                description="これからは、新しい動画が見つかるとこのチャンネルに通知が届きます。",
                color=self.google_blue
            )
            embed.add_field(name="チャンネル", value=channel.mention, inline=True)
            embed.add_field(name="通知ロール", value=role.mention, inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"設定の保存中に問題が発生しました: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(YouTubeMonitor(bot))
