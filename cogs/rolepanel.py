import discord
from discord import app_commands
from discord.ext import commands

# 1. 常設ボタンの挙動を定義
class RoleButton(discord.ui.Button):
    def __init__(self, role: discord.Role):
        # custom_id を固定することで、ボットの再起動後も動作を継続させます
        super().__init__(
            label=f"ロールの付与 / 解除",
            style=discord.ButtonStyle.primary,
            custom_id=f"utility_role_toggle_{role.id}",
            emoji="✅"
        )

    async def callback(self, interaction: discord.Interaction):
        # custom_id からロールIDを抽出
        role_id = int(self.custom_id.split("_")[-1])
        role = interaction.guild.get_role(role_id)

        if not role:
            return await interaction.response.send_message("エラー: 対象のロールが見つかりませんでした。", ephemeral=True)

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"**{role.name}** を解除しました。", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"**{role.name}** を付与しました。", ephemeral=True)

# 2. Viewクラス（再起動耐性を持たせるための設定）
class RoleButtonView(discord.ui.View):
    def __init__(self, role: discord.Role = None):
        super().__init__(timeout=None) # 永続化に必須の設定
        if role:
            self.add_item(RoleButton(role))

class RolePanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.brand_color = 0x4285F4 # クリーンなブルー

    @app_commands.command(name="role-panel-create", description="ロール付与用のパネルを作成します。")
    @app_commands.describe(title="パネルのタイトル", description="パネルの説明文", role="対象のロール")
    @app_commands.checks.has_permissions(administrator=True)
    async def create_panel(self, interaction: discord.Interaction, title: str, description: str, role: discord.Role):
        """シンプルで分かりやすいロールパネルを送信します。"""
        
        await interaction.response.send_message("🔄 パネルを生成中...", ephemeral=True)

        embed = self._create_embed(title, description, role)
        view = RoleButtonView(role)
        
        await interaction.channel.send(embed=embed, view=view)
        await interaction.edit_original_response(content="✅ パネルの作成が完了しました。")

    @app_commands.command(name="role-panel-edit", description="既存のロールパネルを更新します。")
    @app_commands.describe(message_id="編集したいパネルのメッセージID", title="新しいタイトル", description="新しい説明文", role="対象ロール")
    @app_commands.checks.has_permissions(administrator=True)
    async def edit_panel(self, interaction: discord.Interaction, message_id: str, title: str, description: str, role: discord.Role):
        """既存のパネル内容を修正します。"""
        try:
            target_message = await interaction.channel.fetch_message(int(message_id))
            
            if target_message.author != self.bot.user:
                return await interaction.response.send_message("ボット自身が作成したパネルのみ編集可能です。", ephemeral=True)

            embed = self._create_embed(title, description, role)
            view = RoleButtonView(role)
            
            await target_message.edit(embed=embed, view=view)
            await interaction.response.send_message("✅ パネルの内容を更新しました。", ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"⚠️ エラーが発生しました: {e}", ephemeral=True)

    def _create_embed(self, title: str, description: str, role: discord.Role):
        """装飾を抑えた、可読性の高いEmbedを生成"""
        embed = discord.Embed(
            title=title,
            description=(
                f"{description}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"**対象ロール:** {role.mention}\n"
                f"ボタンを押すことで、自動的にロールの付け替えが行われます。"
            ),
            color=self.brand_color
        )
        embed.set_footer(text="Role Management System")
        return embed

async def setup(bot):
    await bot.add_cog(RolePanel(bot))
