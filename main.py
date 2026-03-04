import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import json
import asyncio

TOKEN = "YOUR_TOKEN_HERE"

# ================== IDS ==================
INFRACTION_CHANNEL_ID = 1454919487903109161
BLACKLIST_CHANNEL_ID = 1473501284316352593
PROMOTION_CHANNEL_ID = 1297339994842595398
STAFF_LOG_CHANNEL_ID = 1478873218688487485

ROLE_1 = 1458973048001532136
ROLE_2 = 1458973055924834305

APPEAL_LINK = "https://docs.google.com/forms/d/e/1FAIpQLSfSo_KOuQ_QxBKW5-5twHeW2pKoIK2RFGbhgZZD4NE1ATpOnQ/viewform?usp=dialog"

# ================== BOT SETUP ==================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

strike_file = "strikes.json"

def load_strikes():
    try:
        with open(strike_file, "r") as f:
            return json.load(f)
    except:
        return {}

def save_strikes(data):
    with open(strike_file, "w") as f:
        json.dump(data, f, indent=4)

strike_counts = load_strikes()

def has_permission(member):
    return any(role.id in [ROLE_1, ROLE_2] for role in member.roles)

# ================== ROTATING STATUS ==================
statuses = [
    "Watching over AZDPS",
    "Promoting AZDPS",
    "Keeping Arizona safe"
]

@tasks.loop(seconds=10)
async def change_status():
    for status in statuses:
        await bot.change_presence(activity=discord.Game(name=status))
        await asyncio.sleep(10)

@bot.event
async def on_ready():
    change_status.start()
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

# ==========================================================
# ===================== INFRACTION =========================
# ==========================================================

@bot.tree.command(name="infractiondps", description="Issue an infraction")
@app_commands.describe(
    member="Member",
    action="Infraction Type",
    appealable="Appealable?",
    reason="Reason",
    duration="Duration (7d / 12h)",
    proof="Proof attachment (Required for Blacklist)"
)
@app_commands.choices(
    action=[
        app_commands.Choice(name="Strike", value="Strike"),
        app_commands.Choice(name="Suspend", value="Suspend"),
        app_commands.Choice(name="Terminate", value="Terminate"),
        app_commands.Choice(name="Warning", value="Warning"),
        app_commands.Choice(name="Blacklist", value="Blacklist"),
    ],
    appealable=[
        app_commands.Choice(name="Yes", value="Yes"),
        app_commands.Choice(name="No", value="No"),
    ]
)
async def infractiondps(
    interaction: discord.Interaction,
    member: discord.Member,
    action: app_commands.Choice[str],
    appealable: app_commands.Choice[str],
    reason: str,
    duration: str,
    proof: discord.Attachment = None
):

    await interaction.response.defer(ephemeral=True)

    if not has_permission(interaction.user):
        await interaction.followup.send("❌ No permission.", ephemeral=True)
        return

    moderator = interaction.user
    user_id = str(member.id)

    # ================= BLACKLIST =================
    if action.value == "Blacklist":

        if not (duration.endswith("d") or duration.endswith("h")):
            await interaction.followup.send("❌ Duration must end in d or h.", ephemeral=True)
            return

        if not proof:
            await interaction.followup.send("❌ Proof attachment required.", ephemeral=True)
            return

        embed = discord.Embed(
            title="AZDPS Permanent Blacklist",
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Name:", value=member.mention, inline=False)
        embed.add_field(name="Reason:", value=reason, inline=False)
        embed.add_field(name="Duration:", value=duration, inline=False)
        embed.add_field(name="Proof:", value=f"[Click to View]({proof.url})", inline=False)
        embed.add_field(name="Approved by:", value="Must be a COL+", inline=False)
        embed.add_field(name="Appeal:", value=appealable.value, inline=False)

        await bot.get_channel(BLACKLIST_CHANNEL_ID).send(embed=embed)

        # DM
        dm = discord.Embed(
            title="AZDPS Blacklist Notice",
            description="You have been permanently blacklisted.",
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow()
        )
        dm.add_field(name="Reason", value=reason, inline=False)
        dm.add_field(name="Duration", value=duration, inline=False)
        dm.add_field(name="Moderator", value=moderator.mention, inline=False)

        if appealable.value == "Yes":
            dm.add_field(name="Appeal", value=f"[Submit Appeal]({APPEAL_LINK})", inline=False)

        try:
            await member.send(embed=dm)
        except:
            pass

        await interaction.guild.ban(member, reason=f"BLACKLIST: {reason}")

        await interaction.followup.send("✅ User blacklisted.", ephemeral=True)
        return

    # ================= NORMAL INFRACTIONS =================

    strike_counts[user_id] = strike_counts.get(user_id, 0)

    if action.value == "Strike":
        strike_counts[user_id] += 1
        save_strikes(strike_counts)

    current_strikes = strike_counts.get(user_id, 0)

    embed = discord.Embed(
        title="AZDPS Infraction",
        color=discord.Color.red(),
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="User", value=member.mention, inline=False)
    embed.add_field(name="Action", value=action.value, inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Duration", value=duration, inline=False)
    embed.add_field(name="Current Strikes", value=str(current_strikes), inline=False)
    embed.add_field(name="Appealable", value=appealable.value, inline=False)
    embed.add_field(name="Moderator", value=moderator.mention, inline=False)

    message = await bot.get_channel(INFRACTION_CHANNEL_ID).send(content=member.mention, embed=embed)

    # DM
    dm = discord.Embed(
        title="AZDPS Infraction Notice",
        color=discord.Color.red(),
        timestamp=datetime.utcnow()
    )
    dm.add_field(name="Action", value=action.value, inline=False)
    dm.add_field(name="Reason", value=reason, inline=False)
    dm.add_field(name="Duration", value=duration, inline=False)
    dm.add_field(name="Current Strikes", value=str(current_strikes), inline=False)
    dm.add_field(name="Moderator", value=moderator.mention, inline=False)

    try:
        await member.send(embed=dm)
    except:
        pass

    if action.value in ["Strike", "Suspend", "Terminate"] and appealable.value == "Yes":
        thread = await message.create_thread(name="Appeal", auto_archive_duration=10080)
        await thread.send("Appeal your infraction here.")

    await interaction.followup.send("✅ Infraction issued.", ephemeral=True)

# ==========================================================
# ======================== BAN =============================
# ==========================================================

@bot.tree.command(name="ban", description="Ban a user")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str):

    await interaction.response.defer(ephemeral=True)

    if not has_permission(interaction.user):
        await interaction.followup.send("❌ No permission.", ephemeral=True)
        return

    moderator = interaction.user

    dm = discord.Embed(
        title="AZDPS Ban Notice",
        color=discord.Color.dark_red(),
        timestamp=datetime.utcnow()
    )
    dm.add_field(name="Reason", value=reason, inline=False)
    dm.add_field(name="Moderator", value=moderator.mention, inline=False)
    dm.add_field(name="Appeal", value=f"[Submit Appeal]({APPEAL_LINK})", inline=False)

    try:
        await member.send(embed=dm)
    except:
        pass

    await interaction.guild.ban(member, reason=reason)

    await interaction.followup.send("✅ User banned.", ephemeral=True)

# ==========================================================
# ======================== KICK ============================
# ==========================================================

@bot.tree.command(name="kick", description="Kick a user")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str):

    await interaction.response.defer(ephemeral=True)

    if not has_permission(interaction.user):
        await interaction.followup.send("❌ No permission.", ephemeral=True)
        return

    await interaction.guild.kick(member, reason=reason)
    await interaction.followup.send("✅ User kicked.", ephemeral=True)

# ==========================================================
# ======================== MUTE ============================
# ==========================================================

@bot.tree.command(name="mute", description="Mute a user")
async def mute(interaction: discord.Interaction, member: discord.Member, duration: str, reason: str):

    await interaction.response.defer(ephemeral=True)

    if not has_permission(interaction.user):
        await interaction.followup.send("❌ No permission.", ephemeral=True)
        return

    if not (duration.endswith("d") or duration.endswith("h")):
        await interaction.followup.send("❌ Duration must end in d or h.", ephemeral=True)
        return

    hours = 0
    if duration.endswith("h"):
        hours = int(duration[:-1])
    if duration.endswith("d"):
        hours = int(duration[:-1]) * 24

    until = datetime.utcnow() + discord.utils.timedelta(hours=hours)

    await member.timeout(until, reason=reason)

    await interaction.followup.send("✅ User muted.", ephemeral=True)

# ==========================================================

bot.run(TOKEN)