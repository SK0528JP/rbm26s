import discord
from discord.ext import commands
import os
import asyncio
import logging
import traceback

# 1. ログの設定（Actionsのコンソールでエラーを追いやすくする）
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')
logger = logging.getLogger('RbBot')

class RbBot(commands.Bot):
    def __init__(self):
        # 必要な権限（Intents）の設定
        intents = discord.Intents.default()
        intents.message_content = True  # メッセージ内容の取得
        intents.members = True          # メンバー情報の取得
        
        super().__init__(
            command_prefix="!", 
            intents=intents,
            help_command=None
        )
        
        # 開発拠点：瑞典技術設計局 のギルドID
        self.dev_guild_id = 1372567395419291698

    async def setup_hook(self):
        """Bot起動時に一度だけ実行される初期設定"""
        logger.info("--- Starting Cog Loading Sequence ---")
        
        # cogs フォルダ内の Python ファイルを自動的にロード
        # 将来的に cogs/twitter.py などが増えても自動で認識されます
        target_cog = "cogs.youtube_monitor"
        try:
            await self.load_extension(target_cog)
            logger.info(f"Successfully loaded extension: {target_cog}")
        except Exception as e:
            logger.error(f"Failed to load extension {target_cog}.")
            traceback.print_exc()

        # スラッシュコマンドの同期設定
        dev_guild = discord.Object(id=self.dev_guild_id)
        
        # 開発サーバーへの即時反映用コピー
        self.tree.copy_global_to(guild=dev_guild)
        await self.tree.sync(guild=dev_guild)
        
        # 全サーバーへのグローバル同期（反映には時間がかかります）
        await self.tree.sync()
        
        logger.info(f"Slash commands synced to Guild: {self.dev_guild_id}")

    async def on_ready(self):
        """BotがDiscordに接続した際の処理"""
        logger.info(f"--- Rb m/26S System Online ---")
        logger.info(f"Logged in as: {self.user} (ID: {self.user.id})")
        logger.info(f"Base of Operations: 瑞典技術設計局")
        
        # 5.5時間 (19,800秒) のタイマーを開始
        # GitHub Actionsの6時間制限に抵触する前に安全に終了させる
        logger.info("Cycle timer started: 5.5 hours remaining.")
        await asyncio.sleep(19800)
        
        logger.info("Duty cycle completed. Initiating graceful shutdown for rotation...")
        await self.close()

    async def on_error(self, event, *args, **kwargs):
        """グローバルエラーハンドリング"""
        logger.error(f"Event Error: {event}")
        traceback.print_exc()

if __name__ == "__main__":
    bot = RbBot()
    token = os.getenv("DISCORD_TOKEN")
    
    if token:
        try:
            bot.run(token)
        except Exception as e:
            logger.critical(f"Bot failed to start: {e}")
    else:
        logger.critical("DISCORD_TOKEN is missing from Environment Variables.")
