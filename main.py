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

STRIKE_ROLE_1 = 1458973175814557800
STRIKE_ROLE_2 = 1458973176573857982
TERMINATED_ROLE = 1467017398736654521

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

# ==============================
# READY
# ==============================

@bot.event
async def on_ready():
    if not rotate_status.is_running():
        rotate_status.start()
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

# ==============================
# PROMOTION
# ==============================

@bot.tree.command(name="promotiondps", description="Promote a member (DPS System)")
@app_commands.describe(member="Member being promoted", role="New role", reason="Reason")
async def promotiondps(interaction: discord.Interaction, member: discord.Member, role: discord.Role, reason: str):

    await interaction.response.defer(ephemeral=True)

    if not any(r.id in AUTHORIZED_ROLES for r in interaction.user.roles):
        await interaction.followup.send("❌ No permission.", ephemeral=True)
        return

    await member.add_roles(role)

    # Public Embed
    embed = discord.Embed(
        title="**AZDPS Promotion**",
        description=(
            f"User: {member.mention}\n"
            f"New Rank: {role.mention}\n"
            f"Reason: {reason}"
        ),
        color=discord.Color.green()
    )
    embed.set_footer(text="AZDPS High Command")

    promotion_channel = bot.get_channel(PROMOTION_CHANNEL_ID)
    await promotion_channel.send(content=member.mention, embed=embed)

    # DM User
    try:
        await member.send(embed=embed)
    except:
        pass

    # Staff Log (Automated Format)
    log_embed = discord.Embed(
        title="SYSTEM LOG • PROMOTION",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    log_embed.add_field(name="Member", value=f"{member} ({member.id})", inline=False)
    log_embed.add_field(name="Promoted By", value=f"{interaction.user} ({interaction.user.id})", inline=False)
    log_embed.add_field(name="New Role", value=role.name, inline=False)
    log_embed.add_field(name="Reason", value=reason, inline=False)

    staff_channel = bot.get_channel(STAFF_LOG_CHANNEL_ID)
    await staff_channel.send(embed=log_embed)

# ==============================
# INFRACTION
# ==============================

@bot.tree.command(name="infractiondps", description="Issue an infraction")
@app_commands.describe(member="Member", action="Infraction Type", reason="Reason")
@app_commands.choices(action=[
    app_commands.Choice(name="Strike", value="Strike"),
    app_commands.Choice(name="Terminate", value="Terminate"),
    app_commands.Choice(name="Suspend", value="Suspend"),
    app_commands.Choice(name="Warning", value="Warning"),
])
async def infractiondps(interaction: discord.Interaction, member: discord.Member, action: app_commands.Choice[str], reason: str):

    await interaction.response.defer(ephemeral=True)

    if not any(r.id in AUTHORIZED_ROLES for r in interaction.user.roles):
        await interaction.followup.send("❌ No permission.", ephemeral=True)
        return

    user_id = str(member.id)
    strike_counts[user_id] = strike_counts.get(user_id, 0)

    if action.value == "Strike":
        strike_counts[user_id] += 1
        if strike_counts[user_id] > 3:
            strike_counts[user_id] = 3
        save_strikes(strike_counts)

    if action.value == "Terminate":
        strike_counts[user_id] = 3
        save_strikes(strike_counts)

    # Public Embed
    embed = discord.Embed(
        title="**AZDPS Infraction**",
        description=(
            f"User: {member.mention}\n"
            f"Type: {action.value}\n"
            f"Current Infractions: {strike_counts[user_id]} / 3\n"
            f"Reason: {reason}"
        ),
        color=discord.Color.red()
    )
    embed.set_footer(text="AZDPS High Command")

    infraction_channel = bot.get_channel(INFRACTION_CHANNEL_ID)
    await infraction_channel.send(content=member.mention, embed=embed)

    # DM User
    try:
        await member.send(embed=embed)
    except:
        pass

    # Staff Log (Automated Format)
    log_embed = discord.Embed(
        title="SYSTEM LOG • INFRACTION",
        color=discord.Color.dark_red(),
        timestamp=datetime.utcnow()
    )
    log_embed.add_field(name="Member", value=f"{member} ({member.id})", inline=False)
    log_embed.add_field(name="Action", value=action.value, inline=False)
    log_embed.add_field(name="Issued By", value=f"{interaction.user} ({interaction.user.id})", inline=False)
    log_embed.add_field(name="Strike Count", value=f"{strike_counts[user_id]} / 3", inline=False)
    log_embed.add_field(name="Reason", value=reason, inline=False)

    staff_channel = bot.get_channel(STAFF_LOG_CHANNEL_ID)
    await staff_channel.send(embed=log_embed)

# ==============================
# RUN
# ==============================

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)