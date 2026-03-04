import os
import json
import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
from datetime import datetime

# ==============================
# CONFIG
# ==============================

AUTHORIZED_ROLES = [
    1458973048001532136,
    1458973055924834305
]

INFRACTION_CHANNEL_ID = 1454919487903109161
PROMOTION_CHANNEL_ID = 1297339994842595398
STAFF_LOG_CHANNEL_ID = 1478873218688487485

STRIKE_FILE = "strike_data.json"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ==============================
# STRIKE STORAGE
# ==============================

def load_strikes():
    if not os.path.exists(STRIKE_FILE):
        with open(STRIKE_FILE, "w") as f:
            json.dump({}, f)
        return {}
    with open(STRIKE_FILE, "r") as f:
        return json.load(f)

def save_strikes(data):
    with open(STRIKE_FILE, "w") as f:
        json.dump(data, f, indent=4)

strike_counts = load_strikes()

# ==============================
# ROTATING STATUS
# ==============================

statuses = [
    ("watching", "over AZDPS"),
    ("playing", "Promoting AZDPS"),
    ("playing", "Keeping Arizona safe"),
]

@tasks.loop(seconds=10)
async def rotate_status():
    for activity_type, text in statuses:
        if activity_type == "watching":
            activity = discord.Activity(type=discord.ActivityType.watching, name=text)
        else:
            activity = discord.Game(text)

        await bot.change_presence(status=discord.Status.online, activity=activity)
        await asyncio.sleep(10)

@bot.event
async def on_ready():
    if not rotate_status.is_running():
        rotate_status.start()
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

# ==============================
# PERMISSION CHECK
# ==============================

def has_permission(user):
    return any(role.id in AUTHORIZED_ROLES for role in user.roles)

# ==============================
# INFRACTION COMMAND
# ==============================

@bot.tree.command(name="infractiondps", description="Issue an infraction")
@app_commands.describe(
    member="Member",
    action="Infraction Type",
    appealable="Is this infraction appealable?",
    reason="Reason"
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
    reason: str
):

    await interaction.response.defer(ephemeral=True)

    if not has_permission(interaction.user):
        await interaction.followup.send("❌ No permission.", ephemeral=True)
        return

    # ================= BLACKLIST =================
    if action.value == "Blacklist":
        await interaction.guild.ban(member, reason=reason)

        embed = discord.Embed(
            title="AZDPS Blacklist",
            description=f"{member.mention} has been permanently blacklisted.\nReason: {reason}",
            color=discord.Color.dark_red()
        )

        channel = bot.get_channel(INFRACTION_CHANNEL_ID)
        await channel.send(embed=embed)

        staff_channel = bot.get_channel(STAFF_LOG_CHANNEL_ID)
        await staff_channel.send(
            embed=discord.Embed(
                title="SYSTEM LOG • BLACKLIST",
                description=f"User: {member} ({member.id})\nBy: {interaction.user}\nReason: {reason}",
                timestamp=datetime.utcnow(),
                color=discord.Color.dark_red()
            )
        )
        return

    # ================= NORMAL INFRACTIONS =================

    user_id = str(member.id)
    strike_counts[user_id] = strike_counts.get(user_id, 0)

    if action.value == "Strike":
        strike_counts[user_id] += 1
        if strike_counts[user_id] > 3:
            strike_counts[user_id] = 3
        save_strikes(strike_counts)

    embed = discord.Embed(
        title="AZDPS Infraction",
        description=(
            f"User: {member.mention}\n"
            f"Type: {action.value}\n"
            f"Reason: {reason}\n"
            f"Appealable: {appealable.value}"
        ),
        color=discord.Color.red()
    )

    channel = bot.get_channel(INFRACTION_CHANNEL_ID)
    message = await channel.send(content=member.mention, embed=embed)

    # ================= APPEAL THREAD =================

    if (
        action.value in ["Strike", "Suspend", "Terminate"]
        and appealable.value == "Yes"
    ):
        thread = await message.create_thread(
            name="Appeal",
            auto_archive_duration=1440
        )
        await thread.send(
            "Appeal your infraction here.\nProvide evidence and reasoning."
        )

    # ================= DM USER =================
    try:
        await member.send(embed=embed)
    except:
        pass

    # ================= STAFF LOG =================

    log_embed = discord.Embed(
        title="SYSTEM LOG • INFRACTION",
        color=discord.Color.dark_red(),
        timestamp=datetime.utcnow()
    )
    log_embed.add_field(name="Member", value=f"{member} ({member.id})", inline=False)
    log_embed.add_field(name="Action", value=action.value, inline=False)
    log_embed.add_field(name="Appealable", value=appealable.value, inline=False)
    log_embed.add_field(name="Issued By", value=f"{interaction.user}", inline=False)
    log_embed.add_field(name="Reason", value=reason, inline=False)

    staff_channel = bot.get_channel(STAFF_LOG_CHANNEL_ID)
    await staff_channel.send(embed=log_embed)

# ==============================
# PROMOTION COMMAND (unchanged logic)
# ==============================

@bot.tree.command(name="promotiondps", description="Promote a member")
@app_commands.describe(member="Member", role="New Role", reason="Reason")
async def promotiondps(interaction: discord.Interaction, member: discord.Member, role: discord.Role, reason: str):

    await interaction.response.defer(ephemeral=True)

    if not has_permission(interaction.user):
        await interaction.followup.send("❌ No permission.", ephemeral=True)
        return

    await member.add_roles(role)

    embed = discord.Embed(
        title="AZDPS Promotion",
        description=(
            f"User: {member.mention}\n"
            f"New Rank: {role.mention}\n"
            f"Reason: {reason}"
        ),
        color=discord.Color.green()
    )

    channel = bot.get_channel(PROMOTION_CHANNEL_ID)
    await channel.send(content=member.mention, embed=embed)

    try:
        await member.send(embed=embed)
    except:
        pass

    staff_channel = bot.get_channel(STAFF_LOG_CHANNEL_ID)
    await staff_channel.send(
        embed=discord.Embed(
            title="SYSTEM LOG • PROMOTION",
            description=f"User: {member} ({member.id})\nBy: {interaction.user}\nRole: {role.name}\nReason: {reason}",
            timestamp=datetime.utcnow(),
            color=discord.Color.blue()
        )
    )

# ==============================
# RUN
# ==============================

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)