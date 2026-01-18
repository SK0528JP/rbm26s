import discord
from discord.ext import commands
import os
import asyncio
import logging
import logging.handlers
from datetime import datetime
import pytz

# 1. 高度なロギング設定 (Debugging Perfection)
# ログフォルダが存在しない場合は作成
if not os.path.exists('logs'):
    os.makedirs('logs')

# ログのフォーマット設定（日付、レベル、メッセージ）
formatter = logging.Formatter(
    fmt='[{asctime}] [{levelname:<8}] {name}: {message}',
    datefmt='%Y-%m-%d %H:%M:%S',
    style='{'
)

# コンソールへの出力設定
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

# ファイルへの出力設定（ローテーション機能付き：ログが増えすぎないよう管理）
file_handler = logging.handlers.RotatingFileHandler(
    filename='logs/system.log',
    encoding='utf-8',
    maxBytes=5 * 1024 * 1024,  # 5MBごとに新しいファイルへ
    backupCount=5              # 最新5世代まで保存
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG) # ファイルには詳細なデバッグ情報を残す

# ルートロガーの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Discordライブラリ自体のログも調整
logging.getLogger('discord').setLevel(logging.WARNING)


class SwedishTechBot(commands.Bot):
    def __init__(self):
        # 2. 必要な権限（Intents）の確保
        intents = discord.Intents.default()
        intents.message_content = True # メッセージ内容の読み取り
        intents.members = True         # メンバー情報の取得（JoinTracker等で使用）
        intents.invites = True         # 招待情報の取得（JoinTrackerで使用）
        
        super().__init__(
            command_prefix="!", # Slash Commandメインだが、緊急用として設定
            intents=intents,
            help_command=None   # デフォルトのヘルプは無効化（自作UIへ移行のため）
        )
        self.jst = pytz.timezone('Asia/Tokyo')

    async def setup_hook(self):
        """起動時の初期化処理：Cogsのロードとコマンド同期"""
        logger.info("Initializing system modules...")
        
        # cogsフォルダ内の拡張機能を自動ロード
        loaded_cogs = 0
        if os.path.exists('./cogs'):
            for filename in os.listdir('./cogs'):
                if filename.endswith('.py'):
                    try:
                        await self.load_extension(f'cogs.{filename[:-3]}')
                        logger.info(f'Module Loaded: {filename}')
                        loaded_cogs += 1
                    except Exception as e:
                        logger.error(f'Failed to load extension {filename}: {e}', exc_info=True)
        else:
            logger.warning("'cogs' directory not found. Running without extensions.")

        # スラッシュコマンドの同期（サーバーへの登録）
        logger.info("Syncing application commands...")
        try:
            synced = await self.tree.sync()
            logger.info(f'Command Tree Synced: {len(synced)} commands active.')
        except Exception as e:
            logger.error(f'Failed to sync command tree: {e}', exc_info=True)
        
        logger.info(f"Setup complete. {loaded_cogs} modules loaded.")

    async def on_ready(self):
        """ボット起動完了時のイベント"""
        
        # 3. ステータスとアクティビティの設定
        # ステータス: 退席中 (Idle)
        # メッセージ: "Made by Mizunori.TDB"
        await self.change_presence(
            status=discord.Status.idle,
            activity=discord.Game(name="Made by Mizunori.TDB")
        )
        
        now = datetime.now(self.jst).strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f'--------------------------------------------------')
        logger.info(f'Logged in as: {self.user.name} (ID: {self.user.id})')
        logger.info(f'System Time : {now} JST')
        logger.info(f'Status Set  : Idle (退席中)')
        logger.info(f'Activity Set: "Made by Mizunori.TDB"')
        logger.info(f'--------------------------------------------------')
        logger.info('Rb m/26S is fully operational and standing by.')

# 4. エントリポイント
async def main():
    bot = SwedishTechBot()
    
    # トークンの取得（環境変数推奨）
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        logger.critical("DISCORD_TOKEN environment variable is not set.")
        return

    async with bot:
        await bot.start(token)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Ctrl+C 等で停止した場合のクリーンアップ
        logger.info("System shutdown requested by user.")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
