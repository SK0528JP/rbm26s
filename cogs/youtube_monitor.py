import discord
from discord import app_commands
from discord.ext import commands, tasks
import feedparser
import json
import os
import asyncio
import re
import logging
from datetime import datetime

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Rb_m26S.YouTube')

class YouTubeMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = "UC1owxxoNexXWbJ-ri7r5-ww"
        self.rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={self.channel_id}"
        self.yt_red = 0xFF0000 

        # 実行ファイルの場所を基準にパスを絶対パス化
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_path = os.path.join(base_dir, "config.json")
        self.history_path = os.path.join(base_dir, "last_video_id.txt")

        self.monitor_loop.start()

    def cog_unload(self):
        self.monitor_loop.cancel()

    def load_config(self):
        """設定ファイルを安全に読み込みます（型チェック付き）"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # データの妥当性チェック
                    if isinstance(data, dict) and data.get("channel_id"):
                        return data
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Config Load Error: {e}")
        return {"channel_id": None, "role_id": None}

    def save_config(self, channel_id, role_id):
        """設定を物理ファイルに強制書き込みします"""
        try:
            data = {
                "channel_id": str(channel_id),
                "role_id": str(role_id) if role_id else None
            }
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except IOError as e:
            logger.error(f"Config Save Error: {e}")
            return False

    def get_last_id(self):
        """履歴ファイルを読み込みます"""
        if os.path.exists(self.history_path):
            try:
                with open(self.history_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except IOError:
                return ""
        return ""

    def save_last_id(self, video_id):
        """最新動画IDを保存します"""
        try:
            with open(self.history_path, "w", encoding="utf-8") as f:
                f.write(str(video_id))
        except IOError as e:
            logger.error(f"History Save Error: {e}")

    @tasks.loop(minutes=5)
    async def monitor_loop(self):
        """Rb m/26S 監視プロトコル：完全耐性ループ"""
        await self.bot.wait_until_ready()

        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"[{now_str}] Initiating RSS Scan...")

        config = self.load_config()
        target_id = config.get("channel_id")

        if not target_id:
            logger.warning("Monitor Standby: No target channel configured.")
            return

        try:
            # ネットワークエラー対策: タイムアウト付きでRSS取得
            feed = await asyncio.wait_for(
                asyncio.to_thread(feedparser.parse, self.rss_url),
                timeout=30.0
            )
            
            if not feed or not hasattr(feed, 'entries') or len(feed.entries) == 0:
                return

            latest = feed.entries[0]
            video_id = latest.get('yt_videoid')
            if not video_id: return

            last_id = self.get_last_id()

            if video_id != last_id:
                # チャンネルの解決（キャッシュ -> 取得の2段構え）
                channel = self.bot.get_channel(int(target_id))
                if not channel:
                    try:
                        channel = await self.bot.fetch_channel(int(target_id))
                    except Exception:
                        logger.error(f"Fatal: Could not resolve channel ID {target_id}")
                        return

                # コンテンツの安全な抽出
                video_url = latest.get('link', '')
                video_title = latest.get('title', 'Unknown Title')
                author_name = latest.get('author', 'YouTube Creator')
                author_url = latest.author_detail.href if hasattr(latest, 'author_detail') else ""
                
                summary = latest.get('summary', "概要はありません。")
                summary = re.sub('<[^<]+?>', '', summary)
                summary = (summary[:120] + '...') if len(summary) > 120 else summary

                # UI構築
                embed = discord.Embed(
                    title=f"📽️ {video_title}",
                    url=video_url,
                    description=(
                        f"**{author_name}** が最新映像を公開\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"```text\n{summary}\n```"
                    ),
                    color=self.yt_red,
                    timestamp=datetime.now()
                )
                embed.set_author(name="YouTube Update", icon_url="https://www.gstatic.com/youtube/img/branding/favicon/favicon_144x144.png")
                embed.set_image(url=f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg")
                embed.set_footer(text="Rb m/26S Broadcaster • Mizunori.TDB", icon_url=self.bot.user.display_avatar.url)

                view = discord.ui.View()
                view.add_item(discord.ui.Button(label="視聴する", style=discord.ButtonStyle.link, url=video_url, emoji="▶️"))

                role_id = config.get("role_id")
                mention = f"<@&{role_id}>" if role_id else ""
                
                await channel.send(content=mention, embed=embed, view=view)
                self.save_last_id(video_id)
                logger.info(f"Notification Sent: {video_id}")

        except asyncio.TimeoutError:
            logger.error("RSS Scan Timeout: Connection unstable.")
        except Exception as e:
            logger.error(f"Critical Loop Error: {e}")

    @app_commands.command(name="admin-yt-setup", description="YouTube通知システムを構成します。")
    @app_commands.describe(channel="通知先のチャンネル", role="メンションするロール（任意）")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction, channel: discord.TextChannel, role: discord.Role = None):
        """管理用設定プロトコル"""
        await interaction.response.send_message("🔄 構成を物理メモリに同期中...", ephemeral=True)
        
        role_id = role.id if role else None
        if self.save_config(channel.id, role_id):
            embed = discord.Embed(
                title="📡 監視プロトコル：リンク完了",
                description="Rb m/26S 規格に基づき、物理ファイルへの保存と監視を開始しました。",
                color=0x2ECC71
            )
            embed.add_field(name="TARGET", value=channel.mention, inline=True)
            embed.add_field(name="ROLE", value=role.mention if role else "None", inline=True)
            embed.set_footer(text="Mizunori.TDB System Integrated")
            
            await interaction.edit_original_response(content=None, embed=embed)
            self.monitor_loop.restart()
        else:
            await interaction.edit_original_response(content="⚠️ 書き込みエラー：ファイルシステムを確認してください。")

async def setup(bot):
    await bot.add_cog(YouTubeMonitor(bot))
