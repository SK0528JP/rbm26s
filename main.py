import discord
from discord.ext import commands
import os
import asyncio
import logging
import traceback

# ログの設定（Actionsの実行ログからエラーを特定しやすくする）
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')
logger = logging.getLogger('RbBot')

class RbBot(commands.Bot):
    def __init__(self):
        # 権限(Intents)の定義
        intents = discord.Intents.default()
        intents.message_content = True  # メッセージ読み取り権限
        intents.members = True          # メンションやロール操作用
        
        super().__init__(
            command_prefix="!", 
            intents=intents,
            help_command=None
        )
        
        # 開発拠点：瑞典技術設計局 (Guild ID)
        self.dev_guild_id = 1372567395419291698

    async def setup_hook(self):
        """Bot起動時の初期化シーケンス"""
        logger.info("--- Initializing Systems ---")
        
        # cogsフォルダ内のファイルを自動探索してロード
        # これにより ping.py や youtube_monitor.py が自動的に読み込まれます
        cog_dir = "./cogs"
        if os.path.exists(cog_dir):
            for filename in os.listdir(cog_dir):
                if filename.endswith(".py") and not filename.startswith("__"):
                    cog_name = f"cogs.{filename[:-3]}"
                    try:
                        await self.load_extension(cog_name)
                        logger.info(f"Module Loaded: {cog_name}")
                    except Exception as e:
                        logger.error(f"Failed to load {cog_name}: {e}")
                        traceback.print_exc()
        else:
            logger.warning("Warning: 'cogs' directory not found.")

        # スラッシュコマンドの同期
        # 開発サーバーへの即時反映用
        dev_guild = discord.Object(id=self.dev_guild_id)
        self.tree.copy_global_to(guild=dev_guild)
        await self.tree.sync(guild=dev_guild)
        
        # 全サーバーへのグローバル同期（反映に最大1時間程度）
        await self.tree.sync()
        
        logger.info(f"Slash commands synchronized to Dev-Base: {self.dev_guild_id}")

    async def on_ready(self):
        """オンライン接続時の処理"""
        logger.info(f"--- Rb m/26S Online ---")
        logger.info(f"Logged in as: {self.user} (ID: {self.user.id})")
        
        # 5.5時間 (19,800秒) の運用サイクルを開始
        # GitHub Actionsの制限時間を考慮し、自動でバトンタッチする設計
        logger.info("Starting 5.5-hour operational cycle...")
        await asyncio.sleep(19800)
        
        logger.info("Operational cycle limit reached. Initiating automatic shutdown.")
        await self.close()

    async def on_error(self, event, *args, **kwargs):
        """システムエラーログ"""
        logger.error(f"Critical Event Error: {event}")
        traceback.print_exc()

if __name__ == "__main__":
    # 環境変数からトークンを取得
    token = os.getenv("DISCORD_TOKEN")
    
    if token:
        bot = RbBot()
        try:
            bot.run(token)
        except Exception as e:
            logger.critical(f"System failed to start: {e}")
    else:
        logger.critical("Error: DISCORD_TOKEN is not defined in GitHub Secrets.")
