import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os
import json
import requests
from datetime import datetime

# --- 永続的なView：チケット管理用（クローズボタン） ---
class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="チケットを閉じる", 
        style=discord.ButtonStyle.danger, 
        custom_id="rb_m26s_ticket_close", 
        emoji="🔒"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """チケットチャンネルを削除する"""
        await interaction.response.send_message("🔓 **チケットを閉鎖します。**\n5秒後にこのチャンネルを削除します。", ephemeral=False)
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete()
        except discord.Forbidden:
            await interaction.channel.send("⚠️ チャンネル削除権限が不足しています（ボットのロール位置を確認してください）。")
        except discord.HTTPException:
            pass

# --- 永続的なView：チケット作成用 ---
class TicketCreateView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="チケットを作成", 
        style=discord.ButtonStyle.success, 
        custom_id="rb_m26s_ticket_create", 
        emoji="📩"
    )
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """チケットチャンネルを作成し、権限を設定する"""
        # 処理中であることをユーザーに伝える
        await interaction.response.defer(ephemeral=True)

        # 1. Gistから現在のチケット番号を取得・更新（非同期スレッド実行）
        data = await self.cog.sync_gist("load")
        count = data.get("ticket_count", 0) + 1
        await self.cog.sync_gist("save", {"ticket_count": count})

        guild = interaction.guild
        user = interaction.user
        
        # 2. パネルが設置されている現在のカテゴリを取得
        target_category = interaction.channel.category
        
        # 3. 権限設定（@everyoneは見れない、作成者と管理者は見れる）
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
                topic=f"User ID: {user.id} | 発行日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            
            # 5. チケット内案内メッセージ
            embed = discord.Embed(
                title=f"🎫 チケット受付 #{count:03d}",
                description=(
                    f"{user.mention} 様、お問い合わせありがとうございます。\n"
                    "スタッフが対応するまで、相談内容をご記入の上お待ちください。\n\n"
                    "**【対応終了後】**\n下のボタンを押すとチャンネルが削除されます。"
                ),
                color=0x2ECC71,
                timestamp=datetime.now()
            )
            embed.set_footer(text="Rb m/26S Support Protocol")
            
            await channel.send(embed=embed, view=TicketControlView())
            
            # 6. 完了報告（作成者にのみ見える）
            await interaction.followup.send(f"✅ チケットを作成しました: {channel.mention}", ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"⚠️ エラーが発生しました: {e}", ephemeral=True)

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gist_id = os.getenv("GIST_ID")
        self.gist_token = os.getenv("GIST_TOKEN")
        self.filename = "rb_m26s_data.json"

    async def sync_gist(self, action="load", new_data=None):
        """Gistとの非同期通信（スレッド化でメインループを止めない）"""
        def _sync_request():
            headers = {"Authorization": f"token {self.gist_token}"}
            url = f"https://api.github.com/gists/{self.gist_id}"
            
            try:
                # ロード
                res = requests.get(url, headers=headers, timeout=10)
                if res.status_code != 200:
                    return {"ticket_count": 0}
                
                content = res.json()["files"].get(self.filename, {}).get("content", "{}")
                data = json.loads(content)
                
                # セーブ
                if action == "save" and new_data:
                    data.update(new_data)
                    payload = {
                        "files": {
                            self.filename: {
                                "content": json.dumps(data, indent=4, ensure_ascii=False)
                            }
                        }
                    }
                    requests.patch(url, headers=headers, json=payload, timeout=10)
                
                return data
            except Exception as e:
                print(f"[ERROR] Gist Sync Error: {e}")
                return {"ticket_count": 0}

        return await asyncio.to_thread(_sync_request)

    @commands.Cog.listener()
    async def on_ready(self):
        """再起動時にボタンの待機状態を復元"""
        self.bot.add_view(TicketCreateView(self))
        self.bot.add_view(TicketControlView())
        print(f"[INFO] Ticket System: Persistent Views Successfully Registered.")

    @app_commands.command(name="ticket-panel-create", description="【運営専用】チケット作成パネルをこのチャンネルに設置します。")
    @app_commands.checks.has_permissions(administrator=True)
    async def create_panel(self, interaction: discord.Interaction, title: str = "お問い合わせ窓口", description: str = "下のボタンを押すと、運営との個別相談チャンネルが作成されます。"):
        """現在のチャンネルにチケットパネルを設置"""
        embed = discord.Embed(
            title=f"📩 {title}",
            description=f"{description}\n\n━━━━━━━━━━━━━━━━━━━━━━\n※チケットはこのカテゴリ内に作成されます。",
            color=0x3498DB
        )
        embed.set_footer(text="Rb m/26S Support System")
        
        await interaction.channel.send(embed=embed, view=TicketCreateView(self))
        await interaction.response.send_message("✅ パネルを設置しました。動作テストを行ってください。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))
