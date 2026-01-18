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

    @app_commands.command(name="user-inspect", description="指定されたユーザーのあらゆる公開情報を詳細に解析します。")
    @app_commands.describe(member="解析対象のユーザー（メンションまたはID）")
    async def inspect(self, interaction: discord.Interaction, member: discord.Member = None):
        """ユーザーに関する公開データを極限まで抽出します。"""
        target = member or interaction.user
        
        # 1. 時間データの解析（JST換算と経過日数）
        now = datetime.now(pytz.utc)
        created_delta = (now - target.created_at).days
        joined_delta = (now - target.joined_at).days

        # 2. ロール情報の詳細
        # 役職順にソートし、@everyoneを除外
        roles = sorted(target.roles, key=lambda r: r.position, reverse=True)
        role_mentions = [r.mention for r in roles if r != interaction.guild.default_role]
        role_display = " ".join(role_mentions) if role_mentions else "なし"

        # 3. 権限（パーミッション）の抽出
        # 重要な権限をピックアップして表示
        important_perms = []
        perms = dict(target.guild_permissions)
        key_perms = {
            "administrator": "管理者",
            "manage_guild": "サーバー管理",
            "manage_channels": "チャンネル管理",
            "manage_roles": "ロール管理",
            "manage_messages": "メッセージ管理",
            "mention_everyone": "全員メンション",
            "mute_members": "メンバーミュート",
            "kick_members": "キック権限",
            "ban_members": "BAN権限"
        }
        for codename, jpname in key_perms.items():
            if perms.get(codename):
                important_perms.append(f"`{jpname}`")
        
        perm_display = " ".join(important_perms) if important_perms else "一般権限"

        # 4. バッジ（フラグ）の解析
        flags = []
        user_flags = target.public_flags
        if user_flags.staff: flags.append("Discord Staff")
        if user_flags.partner: flags.append("Partnered Server Owner")
        if user_flags.hypesquad: flags.append("HypeSquad Events")
        if user_flags.bug_hunter: flags.append("Bug Hunter (Green)")
        if user_flags.bug_hunter_level_2: flags.append("Bug Hunter (Gold)")
        if user_flags.early_supporter: flags.append("Early Supporter")
        if user_flags.verified_bot_developer: flags.append("Verified Bot Dev")
        if user_flags.active_developer: flags.append("Active Developer")
        
        flag_display = ", ".join(flags) if flags else "なし"

        # 5. ステータスとアクティビティ
        status_map = {
            discord.Status.online: "🟢 オンライン",
            discord.Status.idle: "🌙 退席中",
            discord.Status.dnd: "⛔ 取り込み中",
            discord.Status.offline: "⚪ オフライン"
        }
        status_text = status_map.get(target.status, "不明")

        # 6. デザイン構成（Embed）
        embed = discord.Embed(
            title=f"User Analysis Report: {target}",
            description=f"ID: `{target.id}`",
            color=self.stb_blue,
            timestamp=datetime.now()
        )

        embed.set_thumbnail(url=target.display_avatar.url)
        if target.desktop_status != discord.Status.offline: embed.set_author(name="Desktop Connected", icon_url="https://www.gstatic.com/images/icons/material/system/2x/desktop_windows_black_24dp.png")

        # セクション：アカウントタイムライン
        embed.add_field(
            name="📅 タイムライン",
            value=(
                f"**作成日:** <t:{int(target.created_at.timestamp())}:F> ({created_delta}日前)\n"
                f"**参加日:** <t:{int(target.joined_at.timestamp())}:F> ({joined_delta}日前)"
            ),
            inline=False
        )

        # セクション：メンバー属性
        embed.add_field(
            name="👤 属性",
            value=(
                f"**ニックネーム:** {target.display_name}\n"
                f"**ステータス:** {status_text}\n"
                f"**バッジ:** {flag_display}\n"
                f"**ボット:** {'はい' if target.bot else 'いいえ'}"
            ),
            inline=True
        )

        # セクション：接続デバイス
        embed.add_field(
            name="📱 接続環境",
            value=(
                f"**モバイル:** {'接続中' if target.is_on_mobile() else '--'}\n"
                f"**デスクトップ:** {'接続中' if target.desktop_status != discord.Status.offline else '--'}"
            ),
            inline=True
        )

        # セクション：権限・役割
        embed.add_field(
            name="🔑 主要権限",
            value=perm_display,
            inline=False
        )

        embed.add_field(
            name=f"🎭 保有ロール ({len(role_mentions)})",
            value=role_display if len(role_display) < 1024 else "ロール数が多すぎるため表示を省略しました。",
            inline=False
        )

        # ボイスチャンネル情報（接続中のみ）
        if target.voice:
            embed.add_field(
                name="🔊 ボイスチャンネル",
                value=f"{target.voice.channel.name} に接続中",
                inline=False
            )

        embed.set_footer(text="Rb m/26S User Inspection System • 瑞典技術設計局")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(UserInspector(bot))
