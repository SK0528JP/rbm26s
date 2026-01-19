import discord
from discord import app_commands
from discord.ext import commands

# 1. Viewクラス：再起動後も「custom_id」を拾えるように定義
class RoleButtonView(discord.ui.View):
    def __init__(self):
        # タイムアウトをNoneに設定し、永続化
        super().__init__(timeout=None)

    # ボタンを静的に配置（IDを固定）
    # 複数のロールを作りたい場合は、ここを動的にするのではなく、
    # 起動時に「既に発行したID」を登録する必要があります。
    # 汎用性を高めるため、インタラクションのみを拾う設計にします。

    @discord.ui.button(
        label="ロールの付与 / 解除",
        style=discord.ButtonStyle.primary,
        custom_id="rb_m26s_role_toggle_button", # 完全に固定
        emoji="✅"
    )
    async def toggle_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 埋め込みの description や footer から対象ロールを特定する設計、
        # あるいは Gist に保存したロールIDを使用します。
        
        # 今回は最も堅牢な「EmbedからIDを読み取る」または「Gist連携」ですが、
        # シンプルに「Embed内のメンションからIDを抽出」するロジックにします。
        description = interaction.message.embeds[0].description
        role_id_match = re.search(r'<@&(\d+)>', description)
        
        if not role_id_match:
            return await interaction.response.send_message("エラー: ロールIDを特定できませんでした。", ephemeral=True)
            
        role_id = int(role_id_match.group(1))
        role = interaction.guild.get_role(role_id)

        if not role:
            return await interaction.response.send_message("エラー: ロールが見つかりません。", ephemeral=True)

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"**{role.name}** を解除しました。", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"**{role.name}** を付与しました。", ephemeral=True)

import re

class RolePanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.brand_color = 0x4285F4

    # 💡 ここが最重要！再起動のたびにボタンの「待ち受け」を再開する
    @commands.Cog.listener()
    async def on_ready(self):
        # ボット起動時に、このViewをリスナーとして登録
        self.bot.add_view(RoleButtonView())
        print(f"[INFO] Persistent Role View registered.")

    @app_commands.command(name="role-panel-create", description="ロール付与用のパネルを作成します。")
    @app_commands.describe(title="パネルのタイトル", description="説明文", role="対象ロール")
    @app_commands.checks.has_permissions(administrator=True)
    async def create_panel(self, interaction: discord.Interaction, title: str, description: str, role: discord.Role):
        await interaction.response.send_message("🔄 生成中...", ephemeral=True)

        embed = self._create_embed(title, description, role)
        # 固定された custom_id を持つ View を送信
        await interaction.channel.send(embed=embed, view=RoleButtonView())
        await interaction.edit_original_response(content="✅ 永続化パネルを作成しました。")

    @app_commands.command(name="role-panel-edit", description="既存のロールパネルを更新します。")
    async def edit_panel(self, interaction: discord.Interaction, message_id: str, title: str, description: str, role: discord.Role):
        try:
            target_message = await interaction.channel.fetch_message(int(message_id))
            embed = self._create_embed(title, description, role)
            await target_message.edit(embed=embed, view=RoleButtonView())
            await interaction.response.send_message("✅ パネルを更新しました。", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"⚠️ エラー: {e}", ephemeral=True)

    def _create_embed(self, title: str, description: str, role: discord.Role):
        embed = discord.Embed(
            title=title,
            description=f"{description}\n━━━━━━━━━━━━━━\n**対象ロール:** {role.mention}",
            color=self.brand_color
        )
        embed.set_footer(text="Rb m/26S Role System")
        return embed

async def setup(bot):
    await bot.add_cog(RolePanel(bot))
