import discord
from discord import app_commands
from discord.ext import commands, tasks
import feedparser
import json
import os
import asyncio
import re
from datetime import datetime

class YouTubeMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = "UC1owxxoNexXWbJ-ri7r5-ww"
        self.rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={self.channel_id}"
        self.config_path = "config.json"
        self.history_path = "last_video_id.txt"
        self.yt_red = 0xFF0000 # YouTubeのブランドカラー

        self.monitor_loop.start()

    def cog_unload(self):
        self.monitor_loop.cancel()

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                try: return json.load(f)
                except: return {"channel_id": None, "role_id": None}
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
        config = self.load_config()
        target_channel_id = config.get("channel_id")
        target_role_id = config.get("role_id")

        if not target_channel_id:
            return

        try:
            feed = await asyncio.to_thread(feedparser.parse, self.rss_url)
            if not feed.entries:
                return

            latest = feed.entries[0]
            video_id = latest.yt_videoid
            last_id = self.get_last_id()

            if video_id != last_id:
                channel = self.bot.get_channel(int(target_channel_id))
                if channel:
                    # 情報の動的抽出
                    video_url = latest.link
                    video_title = latest.title
                    author_name = latest.author
                    author_url = latest.author_detail.href
                    
                    # 概要文の正規化（RSSからは冒頭のみ取得可能）
                    summary = latest.summary if hasattr(latest, 'summary') else ""
                    summary = re.sub('<[^<]+?>', '', summary) # HTMLタグ除去
                    summary = (summary[:150] + '...') if len(summary) > 150 else summary

                    # 高画質サムネイル
                    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                    # チャンネルアイコンの推測（GoogleのS2サービスを利用）
                    icon_url = f"https://www.google.com/s2/favicons?sz=128&domain_url={author_url}"

                    # --- UI構築: アップグレードデザイン ---
                    embed = discord.Embed(
                        title=video_title,
                        url=video_url,
                        description=f"**{author_name}** が新しい動画を公開しました。\n\n```\n{summary}\n```",
                        color=self.yt_red,
                        timestamp=datetime.now()
                    )
                    
                    embed.set_author(name=f"{author_name} - YouTube", icon_url=icon_url, url=author_url)
                    embed.set_image(url=thumbnail_url)
                    embed.set_footer(text="Rb m/26S Broadcaster • 瑞典技術設計局", icon_url=self.bot.user.display_avatar.url)

                    # リンクボタンの実装
                    view = discord.ui.View()
                    view.add_item(discord.ui.Button(label="動画を視聴する", style=discord.ButtonStyle.link, url=video_url, emoji="▶️"))
                    view.add_item(discord.ui.Button(label="チャンネルへ", style=discord.ButtonStyle.link, url=author_url, emoji="📺"))

                    mention = f"<@&{target_role_id}>" if target_role_id else ""
                    await channel.send(content=mention, embed=embed, view=view)
                    self.save_last_id(video_id)
        except Exception as e:
            print(f"Error: {e}")

    @app_commands.command(name="admin-yt-setup", description="YouTube通知システムを構成します。")
    @app_commands.describe(channel="通知先のテキストチャンネル", role="メンションするロール（任意）")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction, channel: discord.TextChannel, role: discord.Role = None):
        await interaction.response.send_message("🔄 構成を同期中...", ephemeral=True)
        
        try:
            role_id = role.id if role else None
            self.save_config(channel.id, role_id)
            
            embed = discord.Embed(
                title="📡 システム構成完了",
                description=f"YouTube監視プロトコルが正常にリンクされました。",
                color=0x2ECC71 # 成功を示すグリーン
            )
            embed.add_field(name="TARGET CHANNEL", value=channel.mention, inline=True)
            embed.add_field(name="MENTION ROLE", value=role.mention if role else "None", inline=True)
            embed.set_footer(text="Mizunori.TDB System Integrated")
            
            await interaction.edit_original_response(content=None, embed=embed)
        except Exception as e:
            await interaction.edit_original_response(content=f"⚠️ 保存エラー: {e}")

async def setup(bot):
    await bot.add_cog(YouTubeMonitor(bot))
