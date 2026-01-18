import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import time

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 瑞典技術設計局 コーポレートカラー (Sweden Blue)
        self.sweden_blue = 0x005B99

    @app_commands.command(
        name="ping", 
        description="システムの稼働状況および応答速度を精密に計測します。"
    )
    async def ping(self, interaction: discord.Interaction):
        """
        システムの応答速度（Latency）を計測し、視覚化されたレポートを生成します。
        """
        # 1. 初期レスポンス（処理中状態の提示）
        process_embed = discord.Embed(
            description="🔄 **System Diagnostic: 信号を送信中...**",
            color=self.sweden_blue
        )
        # 実行開始時間を記録（より精密な計測のため）
        start_time = time.perf_counter()
        await interaction.response.send_message(embed=process_embed)

        # 2. 通信品質の解析
        # APIレイテンシを取得
        api_latency = round(self.bot.latency * 1000)
        # 実行完了までの時間を計測
        end_time = time.perf_counter()
        internal_latency = round((end_time - start_time) * 1000)

        # 3. 品質ステータスの判定（可読性向上のための動的評価）
        if api_latency < 100:
            status_text = "🟢 **Excellent** (安定)"
        elif api_latency < 250:
            status_text = "🟡 **Good** (良好)"
        else:
            status_text = "🔴 **Critical** (遅延発生中)"

        # 4. レポートEmbedの構築（UI/UX最適化デザイン）
        report_embed = discord.Embed(
            title="📡 System Diagnostic Report",
            description=(
                "現在のバックエンドサーバーおよびAPIとの通信品質を測定しました。\n"
                "━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=self.sweden_blue,
            timestamp=datetime.now()
        )

        # 診断結果を整理された階層で表示
        report_embed.add_field(
            name="📊 通信品質", 
            value=status_text, 
            inline=False
        )
        report_embed.add_field(
            name="🛰️ API Latency", 
            value=f"```\n{api_latency} ms\n```", 
            inline=True
        )
        report_embed.add_field(
            name="⚙️ Internal Lag", 
            value=f"```\n{internal_latency} ms\n```", 
            inline=True
        )

        # ブランドの一貫性を保つフッター
        report_embed.set_footer(
            text="Rb m/26S Strategic System | 瑞典技術設計局",
            icon_url=self.bot.user.display_avatar.url
        )

        # 5. 最終的なレポートへ上書き
        await interaction.edit_original_response(embed=report_embed)

async def setup(bot):
    await bot.add_cog(Ping(bot))
