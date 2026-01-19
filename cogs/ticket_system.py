import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os
import json
import requests
import re
from datetime import datetime

# --- 永続的なView：チケット管理用（クローズボタン） ---
class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="チケットを閉じる", style=discord.ButtonStyle.danger, custom_id="rb_m26s_ticket_close", emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction):
        await interaction.response.send_message("🔓 **チケットを閉鎖します。**\n5秒後にこのチャンネルを削除します。", ephemeral=False)
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete()
        except discord.Forbidden:
            await interaction.channel.send("⚠️ チャンネル削除権限が不足しています。")

# --- 永続的なView：チケット作成用 ---
class TicketCreateView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="チケットを作成", style=discord.ButtonStyle.success, custom_id="rb_m26s_ticket_create", emoji="📩")
    async def create_ticket(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True) # 処理に時間がかかる可能性を考慮

        # 1. Gistから現在のチケット番号を取得して更新
        data = await self.cog.sync_gist("load")
        count = data.get("ticket_count", 0) + 1
        await self.cog.sync_gist("save", {"ticket_count": count})

        guild = interaction.guild
        user = interaction.user
        
        # 2. パネルと同じカテゴリを特定
        target_category = interaction.channel.category
        
        # 3. 権限設定（作成者、管理者、ボットのみ）
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, embed_links=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }

        # 4. チャンネル作成
        channel_name = f"ticket-{count:03d}-{user.name}"
        try:
            channel = await guild.create_text_channel(
                name=channel_name, 
                category=target_category, 
                overwrites=overwrites,
                topic=f"User ID: {user.id} | Created at: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            
            # 5. 案内メッセージ送信
            embed = discord.Embed(
                title=f"🎫 チケット受付 #{count:03d}",
                description=f"{user.mention} 様、お問い合わせありがとうございます。\nスタッフが対応するまで、相談内容をご記入の上お待ちください。\n\n**対応が終了したら下のボタンで閉じてください。**",
                color=0x2ECC71
            )
            embed.set_footer(text="Rb m/26S Support Protocol")
            await channel.send(embed=embed, view=TicketControlView())
            
            await interaction.followup.send(f"✅ チケットを作成しました: {channel.mention}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"⚠️ チャンネル作成に失敗しました: {e}", ephemeral=True)

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gist_id = os.getenv("GIST_ID")
        self.gist_token = os.getenv("GIST_TOKEN")
        self.filename = "rb_m26s_data.json"

    async def sync_gist(self, action="load", new_data=None):
        """Gistとの非同期同期プロトコル"""
        def _sync():
            headers = {"Authorization": f"token {self.gist_token}"}
            url = f"https://api.github.com/gists/{self.gist_id}"
            
            # ロード
            res = requests.get(url, headers=headers)
            if res.status_code != 200: return {"ticket_count": 0}
            
            data_content = res.json()["files"].get(self.filename, {}).get("content", "{}")
            current_data = json.loads(data_content)
            
            # セーブ
            if action == "save" and new_data:
                current_data.update(new_data)
                payload = {"files": {self.filename: {"content": json.dumps(current_data, indent=4, ensure_ascii=False)}}}
                requests.patch(url, headers=headers, json=payload)
            
            return current_data

        return await asyncio.to_thread(_sync)

    @commands.Cog.listener()
    async def on_ready(self):
        # 永続Viewを再起動時にボットに登録
        self.bot.add_view(TicketCreateView(self))
        self.bot.add_view(TicketControlView())
        print(f"[INFO] Ticket System: Persistent Views Registered.")

    @app_commands.command(name="ticket-panel-create", description="【運営専用】チケット作成パネルを現在地に設置します。")
    @app_commands.checks.has_permissions(administrator=True)
    async def create_panel(self, interaction: discord.Interaction, title: str = "お問い合わせ窓口", description: str = "下のボタンを押すと、専用の相談チャンネルが作成されます。"):
        """現在のチャンネルにパネルを設置"""
        embed = discord.Embed(
            title=f"📩 {title}",
            description=f"{description}\n━━━━━━━━━━━━━━\n※チケットは現在のカテゴリ内に作成されます。",
            color=0x3498DB
        )
        embed.set_footer(text="Rb m/26S Support System")
        
        await interaction.channel.send(embed=embed, view=TicketCreateView(self))
        await interaction.response.send_message("✅ チケットパネルを設置しました。このチャンネルが属するカテゴリ内にチケットが作成されます。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))
