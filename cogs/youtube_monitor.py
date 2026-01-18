import discord
from discord import app_commands
from discord.ext import commands, tasks
import feedparser
import json
import os
import asyncio

class YouTubeMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = "UC1owxxoNexXWbJ-ri7r5-ww"
        self.rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={self.channel_id}"
        self.config_path = "config.json"
        self.history_path = "last_video_id.txt"
        
        # 監視ループの開始
        self.monitor_loop.start()

    def cog_unload(self):
        self.monitor_loop.cancel()

    def load_config(self):
        """設定ファイル(config.json)の読み込み"""
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                return json.load(f)
        return {"channel_id": None, "role_id": None}

    def save_config(self, channel_id, role_id):
        """設定ファイル(config.json)の保存"""
        with open(self.config_path, "w") as f:
            json.dump({"channel_id": channel_id, "role_id": role_id}, f, indent=4)

    def get_last_id(self):
        """最後に通知した動画IDの取得"""
        if os.path.exists(self.history_path):
            with open(self.history_path, "r") as f:
                return f.read().strip()
        return ""

    def save_last_id(self, video_id):
        """最新の動画IDを保存"""
        with open(self.history_path, "w") as f:
            f.write(video_id)

    @tasks.loop(minutes=5)
    async def monitor_loop(self):
        """5分おきの監視ループ"""
        config = self.load_config()
        target_channel_id = config.get("channel_id")
        target_role_id = config.get("role_id")

        if not target_channel_id:
            return # 通知先が設定されていなければ何もしない

        # RSSフィードの解析
        try:
            feed = feedparser.parse(self.rss_url)
            if not feed.entries:
                return

            latest_video = feed.entries[0]
            video_id = latest_video.yt_videoid
            video_url = latest_video.link
            
            # 前回のIDと比較
            last_id = self.get_last_id()

            if video_id != last_id:
                channel = self.bot.get_channel(int(target_channel_id))
                if channel:
                    mention = f"<@&{target_role_id}>" if target_role_id else ""
                    content = f"{mention}\n**動画投稿通知**：最新動画が公開されました\n{video_url}"
                    await channel.send(content)
                    self.save_last_id(video_id)
        except Exception as e:
            print(f"Monitor Loop Error: {e}")

    @app_commands.command(name="admin-yt-setup", description="通知先チャンネルとメンション用ロールを設定する。")
    @app_commands.describe(channel="通知を送信するチャンネル", role="メンションするロール")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction, channel: discord.TextChannel, role: discord.Role):
        """管理者用設定コマンド"""
        try:
            self.save_config(channel.id, role.id)
            await interaction.response.send_message(
                f"通知設定を更新しました\n送信先: {channel.mention}\n対象ロール: {role.mention}\n設定完了✅。",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"設定中にエラーが発生しました: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(YouTubeMonitor(bot))
