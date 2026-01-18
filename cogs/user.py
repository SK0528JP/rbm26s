import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import pytz

class UserInspector(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stb_blue = 0x4285F4
        self.jst = pytz.timezone('Asia/Tokyo')

    @app_commands.command(name="user-inspect", description="ユーザーの詳細情報（ステータス・アクティビティ・デバイス等）を解析します。")
    @app_commands.describe(member="解析対象のユーザー")
    async def inspect(self, interaction: discord.Interaction, member: discord.Member = None):
        """ユーザー情報の完全解析（プレゼンス・デバイス・アイコン対応版）"""
        
        # 1. 処理中メッセージ
        process_embed = discord.Embed(
            description="🔄 ユーザープロファイルをスキャン中...",
            color=self.stb_blue
        )
        await interaction.response.send_message(embed=process_embed)

        target = member or interaction.user
        
        # --- データ解析セクション ---

        # 1. 時間計算
        now = datetime.now(pytz.utc)
        created_delta = (now - target.created_at).days
        joined_delta = (now - target.joined_at).days

        # 2. ロール（@everyone除外・上位表示）
        roles = sorted(target.roles, key=lambda r: r.position, reverse=True)
        role_mentions = [r.mention for r in roles if r != interaction.guild.default_role]
        role_display = " ".join(role_mentions) if role_mentions else "なし"

        # 3. デバイス状態の正確な取得
        clients = []
        if str(target.desktop_status) != 'offline': clients.append("🖥️ Desktop")
        if str(target.mobile_status) != 'offline': clients.append("📱 Mobile")
        if str(target.web_status) != 'offline': clients.append("🌐 Web")
        client_display = " / ".join(clients) if clients else "⚫ Offline"

        # 4. アクティビティ（ゲーム・Spotify・カスタムステータス）の解析
        activities = []
        # カスタムステータス
        for activity in target.activities:
            if isinstance(activity, discord.CustomActivity):
                emoji = f"{activity.emoji} " if activity.emoji else ""
                name = activity.name if activity.name else ""
                activities.append(f"💭 **ステータス:** {emoji}{name}")
            elif isinstance(activity, discord.Spotify):
                activities.append(f"🎵 **Spotify:** {activity.title} / {activity.artist}")
            elif isinstance(activity, discord.Game):
                activities.append(f"🎮 **Game:** {activity.name}")
            elif isinstance(activity, discord.Streaming):
                activities.append(f"📡 **Streaming:** {activity.name}")
            elif activity.type == discord.ActivityType.listening and not isinstance(activity, discord.Spotify):
                activities.append(f"🎧 **Listening:** {activity.name}")
            elif activity.type == discord.ActivityType.watching:
                activities.append(f"📺 **Watching:** {activity.name}")

        activity_display = "\n".join(activities) if activities else "アクティビティなし"

        # 5. バッジ（パブリックフラグ）の完全取得
        flags = []
        uf = target.public_flags
        if uf.staff: flags.append("<:staff:1> Discord Staff") # 必要なら絵文字IDを入れる、ここはテキストで代用
        if uf.partner: flags.append("Partner")
        if uf.hypesquad: flags.append("HypeSquad Events")
        if uf.bug_hunter: flags.append("Bug Hunter (Green)")
        if uf.bug_hunter_level_2: flags.append("Bug Hunter (Gold)")
        if uf.early_supporter: flags.append("Early Supporter")
        if uf.verified_bot_developer: flags.append("Bot Developer")
        if uf.active_developer: flags.append("Active Developer")
        # HypeSquad Houses
        if uf.hypesquad_balance: flags.append("HypeSquad Balance")
        if uf.hypesquad_bravery: flags.append("HypeSquad Bravery")
        if uf.hypesquad_brilliance: flags.append("HypeSquad Brilliance")
        
        flag_display = ", ".join(flags) if flags else "なし"

        # 6. ステータス表示（全体）
        status_map = {
            discord.Status.online: "🟢 オンライン",
            discord.Status.idle: "🌙 退席中",
            discord.Status.dnd: "⛔ 取り込み中",
            discord.Status.offline: "⚪ オフライン"
        }
        main_status = status_map.get(target.status, "不明")


        # --- Embed生成セクション ---
        
        embed = discord.Embed(
            title=f"User Analysis: {target.display_name}",
            color=target.color if target.color != discord.Color.default() else self.stb_blue, # ユーザーカラーがあれば優先
            timestamp=datetime.now()
        )

        # サムネイルと「拡大表示」リンクの作成
        embed.set_thumbnail(url=target.display_avatar.url)
        
        # ユーザー基本情報（IDをここに明記）
        embed.add_field(
            name="🆔 識別データ",
            value=(
                f"**User ID:** `{target.id}`\n"
                f"**Mention:** {target.mention}\n"
                f"**Icon:** [拡大表示・ダウンロード]({target.display_avatar.url})" # ここで拡大リンクを提供
            ),
            inline=False
        )

        # ステータス・デバイス・アクティビティ
        embed.add_field(
            name="📡 現在の状況",
            value=(
                f"**Main Status:** {main_status}\n"
                f"**Devices:** {client_display}\n"
                f"**Activities:**\n{activity_display}"
            ),
            inline=False
        )

        # アカウント属性
        embed.add_field(
            name="🛡️ アカウント属性",
            value=(
                f"**Badges:** {flag_display}\n"
                f"**Bot:** {'🤖 Yes' if target.bot else '👤 No'}\n"
                f"**Created:** <t:{int(target.created_at.timestamp())}:D> ({created_delta} days ago)\n"
                f"**Joined:** <t:{int(target.joined_at.timestamp())}:D> ({joined_delta} days ago)"
            ),
            inline=False
        )

        # ロール
        embed.add_field(
            name=f"🎭 保有ロール ({len(roles)-1})", # @everyone分を引く
            value=role_display if len(role_display) < 1024 else "（多すぎるため省略）",
            inline=False
        )

        embed.set_footer(text="Rb m/26S User Inspection System • 瑞典技術設計局")

        # 結果を送信（編集）
        await interaction.edit_original_response(embed=embed)

async def setup(bot):
    await bot.add_cog(UserInspector(bot))
