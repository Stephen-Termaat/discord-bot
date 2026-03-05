import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
import asyncio
import json

# ================== TOKEN ==================
TOKEN = os.getenv("TOKEN")

if TOKEN is None:
    raise ValueError("TOKEN environment variable not set.")

# ================== CHANNEL IDS ==================
INFRACTION_CHANNEL_ID = 1454919487903109161
BLACKLIST_CHANNEL_ID = 1473501284316352593

# ================== ROLE PERMISSIONS ==================
ROLE_1 = 1458973048001532136
ROLE_2 = 1458973055924834305

APPEAL_LINK = "https://docs.google.com/forms/d/e/1FAIpQLSfSo_KOuQ_QxBKW5-5twHeW2pKoIK2RFGbhgZZD4NE1ATpOnQ/viewform?usp=dialog"

# ================== BOT SETUP ==================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ================== STRIKE STORAGE ==================
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

@tasks.loop(seconds=15)
async def change_status():
    while True:
        for status in statuses:
            await bot.change_presence(activity=discord.Game(name=status))
            await asyncio.sleep(15)

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
    action="Infraction type",
    appealable="Appealable?",
    reason="Reason",
    duration="Duration (7d / 12h)"
)
@app_commands.choices(
    action=[
        app_commands.Choice(name="Strike", value="Strike"),
        app_commands.Choice(name="Suspend", value="Suspend"),
        app_commands.Choice(name="Terminate", value="Terminate"),
        app_commands.Choice(name="Warning", value="Warning"),
    ],
    appealable=[
        app_commands.Choice(name="Yes", value="Yes"),
        app_commands.Choice(name="No", value="No"),
    ]
)
async def infractiondps(interaction: discord.Interaction,
                        member: discord.Member,
                        action: app_commands.Choice[str],
                        appealable: app_commands.Choice[str],
                        reason: str,
                        duration: str):

    await interaction.response.defer(ephemeral=True)

    if not has_permission(interaction.user):
        return await interaction.followup.send("No permission.", ephemeral=True)

    if not (duration.endswith("d") or duration.endswith("h")):
        return await interaction.followup.send("Duration must end in d or h.", ephemeral=True)

    user_id = str(member.id)
    strike_counts[user_id] = strike_counts.get(user_id, 0)

    if action.value == "Strike":
        strike_counts[user_id] += 1
        save_strikes(strike_counts)

    embed = discord.Embed(
        title="AZDPS Infraction",
        color=discord.Color.red(),
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="User", value=member.mention, inline=False)
    embed.add_field(name="Action", value=action.value, inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Duration", value=duration, inline=False)
    embed.add_field(name="Current Strikes", value=str(strike_counts[user_id]), inline=False)
    embed.add_field(name="Appeal", value=appealable.value, inline=False)
    embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)

    message = await bot.get_channel(INFRACTION_CHANNEL_ID).send(content=member.mention, embed=embed)

    if appealable.value == "Yes":
        thread = await message.create_thread(name="Appeal", auto_archive_duration=10080)
        await thread.send("Appeal your infraction here.")

    await interaction.followup.send("Infraction issued.", ephemeral=True)

# ==========================================================
# ===================== PROMOTION ==========================
# ==========================================================

@bot.tree.command(name="promotiondps", description="Issue a promotion")
@app_commands.describe(
    member="Member being promoted",
    new_rank="New rank/title",
    reason="Reason for promotion"
)
async def promotiondps(interaction: discord.Interaction,
                       member: discord.Member,
                       new_rank: str,
                       reason: str):

    await interaction.response.defer(ephemeral=True)

    if not has_permission(interaction.user):
        return await interaction.followup.send("No permission.", ephemeral=True)

    embed = discord.Embed(
        title="AZDPS Promotion",
        color=discord.Color.green(),
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="Member", value=member.mention, inline=False)
    embed.add_field(name="New Rank", value=new_rank, inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Approved By", value=interaction.user.mention, inline=False)

    await bot.get_channel(INFRACTION_CHANNEL_ID).send(content=member.mention, embed=embed)

    try:
        await member.send(f"You have been promoted to {new_rank}. Reason: {reason}")
    except:
        pass

    await interaction.followup.send("Promotion logged.", ephemeral=True)

# ==========================================================
# ===================== BLACKLIST ==========================
# ==========================================================

@bot.tree.command(name="blacklist", description="Blacklist a user or server")
@app_commands.describe(
    target="User ID, Server ID, Invite, or Name",
    appealable="Appealable?",
    reason="Reason",
    duration="Duration (7d / 12h)",
    proof="Proof attachment"
)
@app_commands.choices(
    appealable=[
        app_commands.Choice(name="Yes", value="Yes"),
        app_commands.Choice(name="No", value="No"),
    ]
)
async def blacklist(interaction: discord.Interaction,
                    target: str,
                    appealable: app_commands.Choice[str],
                    reason: str,
                    duration: str,
                    proof: discord.Attachment):

    await interaction.response.defer(ephemeral=True)

    if not has_permission(interaction.user):
        return await interaction.followup.send("No permission.", ephemeral=True)

    if not (duration.endswith("d") or duration.endswith("h")):
        return await interaction.followup.send("Duration must end in d or h.", ephemeral=True)

    embed = discord.Embed(
        title="AZDPS Permanent Blacklist",
        color=discord.Color.dark_red(),
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="Target", value=target, inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Duration", value=duration, inline=False)
    embed.add_field(name="Proof", value=proof.url, inline=False)
    embed.add_field(name="Appeal", value=appealable.value, inline=False)
    embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)

    await bot.get_channel(BLACKLIST_CHANNEL_ID).send(embed=embed)

    if target.isdigit():
        try:
            user = await bot.fetch_user(int(target))
            await interaction.guild.ban(user, reason=reason)

            if appealable.value == "Yes":
                await user.send(f"You have been permanently blacklisted. Reason: {reason}\nAppeal: {APPEAL_LINK}")
            else:
                await user.send(f"You have been permanently blacklisted. Reason: {reason}")

        except:
            pass

    await interaction.followup.send("Blacklist issued.", ephemeral=True)

# ==========================================================
# ===================== BAN / UNBAN ========================
# ==========================================================

@bot.tree.command(name="ban", description="Ban a user")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str):
    await interaction.response.defer(ephemeral=True)

    if not has_permission(interaction.user):
        return await interaction.followup.send("No permission.", ephemeral=True)

    try:
        await member.send(f"You were banned. Reason: {reason}\nAppeal: {APPEAL_LINK}")
    except:
        pass

    await interaction.guild.ban(member, reason=reason)
    await interaction.followup.send("User banned.", ephemeral=True)

@bot.tree.command(name="unban", description="Unban user by ID")
async def unban(interaction: discord.Interaction, user_id: str):
    await interaction.response.defer(ephemeral=True)

    if not has_permission(interaction.user):
        return await interaction.followup.send("No permission.", ephemeral=True)

    user = await bot.fetch_user(int(user_id))
    await interaction.guild.unban(user)
    await interaction.followup.send("User unbanned.", ephemeral=True)

# ==========================================================
# ===================== MUTE / UNMUTE ======================
# ==========================================================

@bot.tree.command(name="mute", description="Mute a user")
async def mute(interaction: discord.Interaction, member: discord.Member, duration: str, reason: str):
    await interaction.response.defer(ephemeral=True)

    if not has_permission(interaction.user):
        return await interaction.followup.send("No permission.", ephemeral=True)

    hours = int(duration[:-1]) * (24 if duration.endswith("d") else 1)
    until = datetime.utcnow() + timedelta(hours=hours)

    await member.timeout(until, reason=reason)
    await interaction.followup.send("User muted.", ephemeral=True)

@bot.tree.command(name="unmute", description="Unmute a user")
async def unmute(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer(ephemeral=True)

    if not has_permission(interaction.user):
        return await interaction.followup.send("No permission.", ephemeral=True)

    await member.timeout(None)
    await interaction.followup.send("User unmuted.", ephemeral=True)

# ==========================================================
# ===================== FETCH USER FROM ID =========================
# ==========================================================

@bot.tree.command(name="fetchuserfromid", description="Convert a Discord ID to a username")
@app_commands.describe(user_id="The Discord user ID")
async def fetchuserfromid(interaction: discord.Interaction, user_id: str):

    await interaction.response.defer(ephemeral=True)

    if not has_permission(interaction.user):
        return await interaction.followup.send("No permission.", ephemeral=True)

    if not user_id.isdigit():
        return await interaction.followup.send("Invalid ID format.", ephemeral=True)

    try:
        user = await bot.fetch_user(int(user_id))

        embed = discord.Embed(
            title="ID Lookup Result",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )

        embed.add_field(name="Username", value=user.name, inline=False)
        embed.add_field(name="User ID", value=user.id, inline=False)
        embed.add_field(name="Account Created", value=user.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)

        await interaction.followup.send(embed=embed, ephemeral=True)

    except:
        await interaction.followup.send("User not found.", ephemeral=True)
        
# ==========================================================
# ===================== CHAIN OF COMMAND (PUBLIC) =========================
# ==========================================================
@bot.tree.command(name="chainofcommand", description="View the AZDPS chain of command")
async def chainofcommand(interaction: discord.Interaction):

    await interaction.response.defer(ephemeral=True)

    # 🔴 High Command
    high_command = (
        "**Commissioner**\n"
        "**Acting Commissioner**\n"
        "**Deputy Commissioner**\n"
        "**Assistant Commissioner**\n"
        "**Superintendent**\n"
        "**Colonel**"
    )

    # 🟡 Supervisors
    supervisors = (
        "**Lieutenant Colonel**\n"
        "**Major**\n"
        "**Captain**\n"
        "**Lieutenant**"
    )

    # 🟢 Field Supervisors
    field_supervisors = (
        "**Sergeant First Class**\n"
        "**Staff Sergeant**\n"
        "**Sergeant**\n"
        "**Trial Sergeant**"
    )

    # 🔵 Field Patrol
    field_patrol = (
        "**Master Trooper**\n"
        "**Senior Trooper**\n"
        "**Corporal**\n"
        "**Lance Corporal**\n"
        "**Trooper 1st Class**\n"
        "**Trooper 2nd Class**\n"
        "**Trooper 3rd Class**"
    )

    # 🟣 FTO Program
    fto_program = (
        "**Probationary Trooper**"
    )

    embed = discord.Embed(
        title="Arizona Department of Public Safety",
        description="Official Chain of Command",
        color=discord.Color.red()
    )

    embed.add_field(name="🔴 High Command", value=high_command, inline=False)
    embed.add_field(name="🟡 Supervisors", value=supervisors, inline=False)
    embed.add_field(name="🟢 Field Supervisors", value=field_supervisors, inline=False)
    embed.add_field(name="🔵 Field Patrol", value=field_patrol, inline=False)
    embed.add_field(name="🟣 FTO Program", value=fto_program, inline=False)

    embed.set_footer(text="AZDPS Official Structure")

    await interaction.followup.send(embed=embed, ephemeral=True)
# =================================================================
# ====================== DEPARTMENT UPDATE ========================
# =================================================================

UPDATE_CHANNEL_ID = 1474211686947885187

@bot.tree.command(name="update", description="Post a formatted department update")
@app_commands.describe(
    number="Update number (example: 011)",
    update="Type out the department update"
)
async def update(interaction: discord.Interaction, number: str, update: str):

    allowed_roles = [1458973048001532136, 1458973055924834305]

    if not any(role.id in allowed_roles for role in interaction.user.roles):
        await interaction.response.send_message(
            "You do not have permission to use this command.",
            ephemeral=True
        )
        return

    channel = bot.get_channel(UPDATE_CHANNEL_ID)

    if not channel:
        await interaction.response.send_message(
            "Update channel not found.",
            ephemeral=True
        )
        return

    try:
        number = f"{int(number):03}"
    except ValueError:
        pass

    formatted_message = (
        f"<:AZDPS:1312784566725120030> Department Update #{number} <:AZDPS:1312784566725120030>\n\n"
        f"> {update}"
    )

    await channel.send(formatted_message)

    await interaction.response.send_message(
        f"Department Update #{number} successfully posted.",
        ephemeral=True
    )
    # =================================================================
# ============================ SAY ================================
# =================================================================

@bot.tree.command(name="say", description="Make the bot say something")
@app_commands.describe(
    message="The message you want the bot to send",
    channel="Optional: Select a channel to send the message to",
    type="Optional: Send as normal message or embed"
)
@app_commands.choices(type=[
    app_commands.Choice(name="Message", value="message"),
    app_commands.Choice(name="Embed", value="embed")
])
async def say(
    interaction: discord.Interaction,
    message: str,
    channel: discord.TextChannel | None = None,
    type: app_commands.Choice[str] | None = None
):

    allowed_roles = [1458973048001532136, 1458973055924834305]

    if not any(role.id in allowed_roles for role in interaction.user.roles):
        await interaction.response.send_message(
            "You do not have permission to use this command.",
            ephemeral=True
        )
        return

    target_channel = channel if channel else interaction.channel
    message_type = type.value if type else "message"

    try:
        if message_type == "embed":
            embed = discord.Embed(
                description=message,
                color=discord.Color.blue()
            )
            await target_channel.send(embed=embed)
        else:
            await target_channel.send(message)

    except discord.Forbidden:
        await interaction.response.send_message(
            "I do not have permission to send messages in that channel.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"Message sent in {target_channel.mention} as {message_type}.",
        ephemeral=True
    )
    # =================================================================
# ========================== SERVER INFO ==========================
# =================================================================

@bot.tree.command(name="serverinfo", description="View information about this server")
async def serverinfo(interaction: discord.Interaction):

    guild = interaction.guild

    embed = discord.Embed(
        title=guild.name,
        color=discord.Color.blue()
    )

    embed.add_field(name="Server ID", value=guild.id, inline=False)
    embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=False)
    embed.add_field(name="Created On", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
    embed.add_field(name="Member Count", value=guild.member_count, inline=False)
    embed.add_field(name="Boost Level", value=guild.premium_tier, inline=False)
    embed.add_field(name="Boosts", value=guild.premium_subscription_count, inline=False)

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    await interaction.response.send_message(embed=embed, ephemeral=True)


# =================================================================
# =========================== ACCOUNT ==============================
# =================================================================

@bot.tree.command(name="account", description="View information about a user account")
@app_commands.describe(member="Optional: Select a member")
async def account(interaction: discord.Interaction, member: discord.Member | None = None):

    member = member or interaction.user

    embed = discord.Embed(
        title=f"{member.name}",
        color=discord.Color.blue()
    )

    embed.add_field(name="Username", value=member.name, inline=False)
    embed.add_field(name="User ID", value=member.id, inline=False)
    embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
    embed.add_field(
        name="Joined Server",
        value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S UTC") if member.joined_at else "Unknown",
        inline=False
    )

    roles = [role.mention for role in member.roles if role.name != "@everyone"]
    embed.add_field(
        name="Roles",
        value=", ".join(roles) if roles else "None",
        inline=False
    )

    embed.set_thumbnail(url=member.display_avatar.url)

    await interaction.response.send_message(embed=embed, ephemeral=True)
# ==========================================================
bot.run(TOKEN)