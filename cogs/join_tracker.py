import discord
from discord.ext import commands
from datetime import datetime
import pytz

class JoinTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stb_blue = 0x4285F4
        self.invites = {}  # 招待リンクのキャッシュ {guild_id: {code: invite}}

    @commands.Cog.listener()
    async def on_ready(self):
        """起動時に既存の招待リンクの情報をキャッシュします"""
        for guild in self.bot.guilds:
            try:
                self.invites[guild.id] = {invite.code: invite for invite in await guild.invites()}
            except discord.Forbidden:
                pass

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """ボットが新しいサーバーに参加した際にキャッシュを更新します"""
        try:
            self.invites[guild.id] = {invite.code: invite for invite in await guild.invites()}
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """メンバー参加時に招待元を特定し、詳細情報を出力します"""
        guild = member.guild
        system_channel = guild.system_channel
        
        # システムチャンネルが設定されていない場合は処理を中断
        if not system_channel:
            return

        # 招待リンクを特定
        invites_before = self.invites.get(guild.id, {})
        invites_after = {}
        try:
            invites_after = {invite.code: invite for invite in await guild.invites()}
        except discord.Forbidden:
            return # 招待リンク取得権限がない場合

        # どのリンクの使用回数が増えたかを探す
        used_invite = None
        for code, invite in invites_after.items():
            if code in invites_before and invite.uses > invites_before[code].uses:
                used_invite = invite
                break
        
        # キャッシュを更新
        self.invites[guild.id] = invites_after

        # 情報の解析
        now = datetime.now(pytz.utc)
        created_delta = (now - member.created_at).days
        
        # デザイン：北欧風・清潔なウェルカムレポート
        embed = discord.Embed(
            title="New Member Joined",
            description=f"{member.mention} さん、サーバーへようこそ。",
            color=self.stb_blue,
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        # 招待情報のセクション
        if used_invite:
            invite_info = (
                f"**コード:** `{used_invite.code}`\n"
                f"**作成者:** {used_invite.inviter.mention if used_invite.inviter else '不明'}\n"
                f"**リンク先:** {used_invite.channel.mention}"
            )
        else:
            invite_info = "特定できませんでした（バニティURLやボットによる招待など）"

        embed.add_field(name="📍 招待情報", value=invite_info, inline=False)

        # アカウント情報のセクション
        embed.add_field(
            name="📅 ユーザータイムライン",
            value=(
                f"**アカウント作成:** <t:{int(member.created_at.timestamp())}:F>\n"
                f"**経過日数:** 約 {created_delta} 日前"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🆔 ユーザーデータ",
            value=f"**ID:** `{member.id}`\n**参加時刻:** <t:{int(member.joined_at.timestamp())}:t>",
            inline=False
        )

        embed.set_footer(text="Rb m/26S Security Protocol • 瑞典技術設計局")

        await system_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(JoinTracker(bot))
