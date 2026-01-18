import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

class UserInspector(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stb_blue = 0x4285F4

    @app_commands.command(name="user-inspect", description="指定されたユーザーの詳細なプロファイルを取得します。")
    @app_commands.describe(member="情報を取得したいユーザー（メンションまたはID）")
    async def inspect(self, interaction: discord.Interaction, member: discord.Member = None):
        """ユーザーの公開情報を極限まで詳細に表示します。"""
        # 指定がない場合はコマンド実行者を対象にする
        target = member or interaction.user

        # ロールの取得（@everyoneを除外）
        roles = [role.mention for role in target.roles if role != interaction.guild.default_role]
        roles_str = " ".join(roles) if roles else "なし"

        # 権限の要約
        permissions = "管理者" if target.guild_permissions.administrator else "一般ユーザー"

        # デザイン：インフォメーションカード
        embed = discord.Embed(
            title=f"User Profile: {target.display_name}",
            description=f"ID: `{target.id}`",
            color=self.stb_blue,
            timestamp=datetime.now()
        )

        # アバター画像
        embed.set_thumbnail(url=target.display_avatar.url)

        # セクション1：アカウント基本情報
        embed.add_field(
            name="基本データ",
            value=(
                f"**ユーザー名:** {target.name}\n"
                f"**ステータス:** {str(target.status).title()}\n"
                f"**アカウント作成日:** <t:{int(target.created_at.timestamp())}:D>\n"
                f"**サーバー参加日:** <t:{int(target.joined_at.timestamp())}:D>"
            ),
            inline=False
        )

        # セクション2：サーバー内権限・役割
        embed.add_field(
            name="所属・権限",
            value=(
                f"**権限レベル:** {permissions}\n"
                f"**保有ロール:** {roles_str}"
            ),
            inline=False
        )

        # セクション3：追加情報
        embed.add_field(
            name="デバイス・アクティビティ",
            value=f"**モバイル:** {'はい' if target.is_on_mobile() else 'いいえ'}",
            inline=True
        )

        embed.set_footer(text="Rb m/26S User Inspection System • 瑞典技術設計局")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(UserInspector(bot))
