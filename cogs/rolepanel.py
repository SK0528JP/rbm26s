import discord
from discord import app_commands
from discord.ext import commands

# ボタンの動作を定義するViewクラス（編集時にも再利用します）
class RoleButtonView(discord.ui.View):
    def __init__(self, target_role: discord.Role):
        super().__init__(timeout=None)
        self.target_role = target_role

    @discord.ui.button(label="ロールを受け取る / 返却する", style=discord.ButtonStyle.primary, custom_id="role_toggle_button")
    async def toggle_role(self, button_interaction: discord.Interaction, button: discord.ui.Button):
        if self.target_role in button_interaction.user.roles:
            await button_interaction.user.remove_roles(self.target_role)
            await button_interaction.response.send_message(f"**{self.target_role.name}** を返却しました。", ephemeral=True)
        else:
            await button_interaction.user.add_roles(self.target_role)
            await button_interaction.response.send_message(f"**{self.target_role.name}** を付与しました。", ephemeral=True)

class RolePanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stb_blue = 0x4285F4

    @app_commands.command(name="role-panel-create", description="新しくロールパネルを作成します。")
    @app_commands.describe(title="パネルのタイトル", description="パネルの説明文", role="対象のロール")
    @app_commands.checks.has_permissions(administrator=True)
    async def create_panel(self, interaction: discord.Interaction, title: str, description: str, role: discord.Role):
        embed = self._create_embed(title, description, role)
        view = RoleButtonView(role)
        
        await interaction.response.send_message("パネルを作成しました。", ephemeral=True)
        await interaction.channel.send(embed=embed, view=view)

    @app_commands.command(name="role-panel-edit", description="既存のロールパネルを編集します。")
    @app_commands.describe(message_id="編集したいパネルのメッセージID", title="新しいタイトル", description="新しい説明文", role="新しい対象ロール")
    @app_commands.checks.has_permissions(administrator=True)
    async def edit_panel(self, interaction: discord.Interaction, message_id: str, title: str, description: str, role: discord.Role):
        try:
            # メッセージIDから対象のメッセージを取得
            msg_id_int = int(message_id)
            target_message = await interaction.channel.fetch_message(msg_id_int)
            
            # ボット自身のメッセージか確認
            if target_message.author != self.bot.user:
                return await interaction.response.send_message("当設計局が作成したメッセージのみ編集可能です。", ephemeral=True)

            embed = self._create_embed(title, description, role)
            view = RoleButtonView(role)
            
            await target_message.edit(embed=embed, view=view)
            await interaction.response.send_message("パネルの更新が完了しました。", ephemeral=True)
            
        except ValueError:
            await interaction.response.send_message("有効なメッセージIDを入力してください。", ephemeral=True)
        except discord.NotFound:
            await interaction.response.send_message("対象のパネルが見つかりませんでした。このチャンネル内で実行してください。", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"エラーが発生しました: {e}", ephemeral=True)

    def _create_embed(self, title: str, description: str, role: discord.Role):
        """北欧風の清潔なEmbedを生成する共通メソッド"""
        embed = discord.Embed(
            title=title,
            description=f"{description}\n\n**対象ロール:** {role.mention}",
            color=self.stb_blue
        )
        embed.set_footer(text="Rb m/26S Role Management System")
        return embed

async def setup(bot):
    await bot.add_cog(RolePanel(bot))
