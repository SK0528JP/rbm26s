import discord
from discord.ext import commands
import os
import asyncio
import logging

# ログの設定（Actionsのログで動作を確認しやすくするため）
logging.basicConfig(level=logging.INFO)

class RbBot(commands.Bot):
    def __init__(self):
        # 必要なインテントをすべて有効化
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True # メンバー管理等が必要な場合のため
        
        super().__init__(
            command_prefix="!", 
            intents=intents,
            help_command=None
        )
        
        # 開発拠点（瑞典技術設計局）のギルドID
        self.dev_guild_id = 1372567395419291698

    async def setup_hook(self):
        """Bot起動時に実行される初期設定"""
        # Cogsの読み込み
        # ファイルパスは 'cogs.youtube_monitor' と想定
        await self.load_extension("cogs.youtube_monitor")
        
        # 開発用ギルドへのスラッシュコマンド同期（即時反映用）
        dev_guild = discord.Object(id=self.dev_guild_id)
        self.tree.copy_global_to(guild=dev_guild)
        await self.tree.sync(guild=dev_guild)
        
        # グローバル同期（他サーバー用、反映に時間がかかる）
        await self.tree.sync()
        
        print(f"Commands synced to Guild: {self.dev_guild_id}")

    async def on_ready(self):
        print(f"--- Rb m/26S Online ---")
        print(f"Logged in as: {self.user.name}")
        print(f"Node: 瑞典技術設計局 (Dev-Base)")
        
        # 5.5時間 (19,800秒) のカウントダウン開始
        # この時間が経過すると、次のGitHub Actionsへバトンタッチするために終了する
        await asyncio.sleep(19800)
        print("Cycle limit reached. Syncing memory and rotating instance...")
        await self.close()

if __name__ == "__main__":
    bot = RbBot()
    token = os.getenv("DISCORD_TOKEN")
    
    if token:
        try:
            bot.run(token)
        except Exception as e:
            print(f"Fatal Error: {e}")
    else:
        print("Error: DISCORD_TOKEN is not set in Environment Variables.")
