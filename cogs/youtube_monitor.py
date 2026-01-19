import discord
from discord import app_commands
from discord.ext import commands, tasks
import feedparser
import json
import os
import asyncio
import re
import requests
from datetime import datetime

class YouTubeMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = "UC1owxxoNexXWbJ-ri7r5-ww"
        self.rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={self.channel_id}"
        self.yt_red = 0xFF0000 
        
        # 外部ストレージ設定 (Mizunori.TDB Persistent Protocol)
        self.gist_id = os.getenv("GIST_ID")
        self.gist_token = os.getenv("GIST_TOKEN")
        self.filename = "rb_m26s_data.json"

        # メモリ上のデータ構造（欠落防止用初期値）
        self.data_cache = {
            "channel_id": None, 
            "role_id": None, 
            "last_video_id": "",
            "last_updated": ""
        }

        self.monitor_loop.start()

    def cog_unload(self):
        self.monitor_loop.cancel()

    def sync_gist(self, action="load", new_data=None):
        """Gist外部メモリとのデータ同期プロトコル"""
        if not self.gist_id or not self.gist_token:
            print("[CRITICAL] Rb m/26S Error: Gist credentials missing in Environment Variables.")
            return self.data_cache

        headers = {
            "Authorization": f"token {self.gist_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        url = f"https://api.github.com/gists/{self.gist_id}"

        try:
            if action == "load":
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code == 200:
                    files = response.json().get("files", {})
                    if self.filename in files:
                        content = files[self.filename].get("content", "{}")
                        self.data_cache.update(json.loads(content))
                        print(f"[INFO] Rb m/26S: Data recovered from Gist.")
                return self.data_cache

            elif action == "save" and new_data:
                self.data_cache.update(new_data)
                self.data_cache["last_updated"] = datetime.now().isoformat()
                
                payload = {
                    "files": {
                        self.filename: {
                            "content": json.dumps(self.data_cache, indent=4, ensure_ascii=False)
                        }
                    }
                }
                res = requests.patch(url, headers=headers, json=payload, timeout=15)
                if res.status_code == 200:
                    print(f"[INFO] Rb m/26S: Persistent memory updated.")
                else:
                    print(f"[ERROR] Rb m/26S Sync Failed: {res.status_code}")

        except Exception as e:
            print(f"[ERROR] Rb m/26S Protocol Exception: {e}")
        
        return self.data_cache

    @tasks.loop(minutes=5)
    async def monitor_loop(self):
        """YouTube監視・通知・同期の統合サイクル"""
        await self.bot.wait_until_ready()

        # 1. ロードプロトコル
        data = await asyncio.to_thread(self.sync_gist, "load")
        target_channel_id = data.get("channel_id")
        last_notified_id = data.get("last_video_id", "")

        if not target_channel_id:
            return

        try:
            # 2. RSSスキャン
            feed = await asyncio.to_thread(feedparser.parse, self.rss_url)
            if not feed or not feed.entries:
                return

            latest = feed.entries[0]
            video_id = latest.yt_videoid
            video_url = latest.link

            # 3. 新着判定
            if video_id != last_notified_id:
                channel = self.bot.get_channel(int(target_channel_id))
                if not channel:
                    channel = await self.bot.fetch_channel(int(target_channel_id))

                # --- 埋め込みメッセージ構築 (Rb m/26S Standard) ---
                summary = re.sub('<[^<]+?>', '', latest.summary) if hasattr(latest, 'summary') else ""
                summary = (summary[:110] + '...') if len(summary) > 110 else (summary or "No description.")

                embed = discord.Embed(
                    title=f"📽️ {latest.title}",
                    url=video_url,
                    description=(
                        f"**{latest.author}** が新しい動画を公開しました\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"**【 概要 】**\n"
                        f"```text\n{summary}\n```"
                    ),
                    color=self.yt_red,
                    timestamp=datetime.now()
                )
                
                # チャンネルアイコンを動的に取得
                icon_url = f"https://www.google.com/s2/favicons?sz=128&domain_url={latest.author_detail.href}"
                embed.set_author(name="YouTube Update", icon_url=icon_url)
                embed.set_image(url=f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg")
                embed.set_footer(text="Rb m/26S Broadcaster • Mizunori.TDB")

                view = discord.ui.View()
                view.add_item(discord.ui.Button(label="動画を見る", style=discord.ButtonStyle.link, url=video_url, emoji="▶️"))

                role_id = data.get("role_id")
                mention = f"<@&{role_id}>" if role_id else ""
                
                # 送信
                await channel.send(content=mention, embed=embed, view=view)

                # 4. セーブプロトコル（IDを即座に永続化）
                await asyncio.to_thread(self.sync_gist, "save", {"last_video_id": video_id})

        except Exception as e:
            print(f"[ERROR] Monitor Cycle Aborted: {e}")

    @app_commands.command(name="admin-yt-setup", description="YouTube通知システムを構成し、Gistとリンクします。")
    @app_commands.describe(channel="通知先のテキストチャンネル", role="メンションするロール（任意）")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction, channel: discord.TextChannel, role: discord.Role = None):
        """管理用：通知システムの永続構成プロトコル"""
        await interaction.response.send_message("🔄 **Gist Persistence Protocol: 同期中...**", ephemeral=True)
        
        try:
            role_id = role.id if role else None
            # 設定をGistへ強制書き込み
            new_config = {
                "channel_id": str(channel.id),
                "role_id": str(role_id) if role_id else None
            }
            await asyncio.to_thread(self.sync_gist, "save", new_config)
            
            embed = discord.Embed(
                title="📡 監視プロトコル リンク完了",
                description=(
                    "YouTube監視システムが正常に構成されました。\n"
                    "データはGist外部メモリに永続化されています。"
                ),
                color=0x2ECC71
            )
            embed.add_field(name="TARGET", value=channel.mention, inline=True)
            embed.add_field(name="ROLE", value=role.mention if role else "None", inline=True)
            embed.set_footer(text="Mizunori.TDB System Integrated")
            
            await interaction.edit_original_response(content=None, embed=embed)
            self.monitor_loop.restart()

        except Exception as e:
            await interaction.edit_original_response(content=f"⚠️ 構成失敗: {e}")

async def setup(bot):
    await bot.add_cog(YouTubeMonitor(bot))
