# ==========================================================
# AZDPS BOT v1.0.0
# Proprietary System
# Developed by Wrd.Jaxk
# All Rights Reserved
# ==========================================================

import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
import asyncio
import json
import re
import random
from datetime import time
import pytz

# ==========================================================
# ========================== TOKEN ==========================
# ==========================================================

TOKEN = os.getenv("TOKEN")

if TOKEN is None:
    raise ValueError("TOKEN environment variable not set.")

# ==========================================================
# ======================= CHANNEL IDS ======================
# ==========================================================

INFRACTION_CHANNEL_ID = 1454919487903109161
PROMOTION_CHANNEL_ID = 1297339994842595398
BLACKLIST_CHANNEL_ID = 1473501284316352593
STAFF_LOG_CHANNEL_ID = 1478873218688487485
UPDATE_CHANNEL_ID = 1474211686947885187
SUGGESTION_FORUM_ID = 1475601720242475124
QUOTE_CHANNEL_ID = 1478137798065258496

# ==========================================================
# ======================== ROLE IDS ========================
# ==========================================================

ROLE_1 = 1458973048001532136
ROLE_2 = 1458973055924834305

TERMINATED_ROLE_ID = 1467017398736654521

APPROVED_ROLE = 1475602324230770901
PENDING_ROLE = 1475602330148802842
DENIED_ROLE = 1475602332829089842

APPEAL_LINK = "https://docs.google.com/forms/d/e/1FAIpQLSfSo_KOuQ_QxBKW5-5twHeW2pKoIK2RFGbhgZZD4NE1ATpOnQ/viewform?usp=dialog"

# ==========================================================
# ========================= BOT SETUP ======================
# ==========================================================

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ==========================================================
# ====================== STRIKE STORAGE ====================
# ==========================================================

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

# ==========================================================
# ===================== PERMISSION CHECK ===================
# ==========================================================

def has_permission(member):
    return any(role.id in [ROLE_1, ROLE_2] for role in member.roles)

# ==========================================================
# ======================== STAFF LOG =======================
# ==========================================================

async def send_staff_log(embed: discord.Embed):
    channel = bot.get_channel(STAFF_LOG_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)

# ==========================================================
# ====================== STATUS ROTATION ===================
# ==========================================================

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
# ====================== HELPER METHODS ====================
# ==========================================================

def parse_duration(duration: str):
    if not (duration.endswith("d") or duration.endswith("h")):
        return None

    try:
        value = int(duration[:-1])
    except:
        return None

    if duration.endswith("d"):
        return timedelta(days=value)
    else:
        return timedelta(hours=value)

def is_user_id(value: str):
    return value.isdigit()

def extract_invite_code(invite: str):
    match = re.search(r"(?:discord\.gg/|discord\.com/invite/)(\w+)", invite)
    return match.group(1) if match else None
    # ==========================================================
# ===================== INFRACTION SYSTEM ==================
# ==========================================================

@bot.tree.command(name="infractiondps", description="Issue an infraction")
@app_commands.describe(
    member="Member",
    action="Infraction type",
    appealable="Appealable?",
    reason="Reason",
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
async def infractiondps(
    interaction: discord.Interaction,
    member: discord.Member,
    action: app_commands.Choice[str],
    appealable: app_commands.Choice[str],
    reason: str
):

    await interaction.response.defer(ephemeral=True)

    if not has_permission(interaction.user):
        return await interaction.followup.send("No permission.", ephemeral=True)

    delta = parse_duration(duration)
    if not delta:
        return await interaction.followup.send("Duration must end in d or h.", ephemeral=True)

    user_id = str(member.id)
    strike_counts[user_id] = strike_counts.get(user_id, 0)

    if action.value == "Strike":
        strike_counts[user_id] += 1
        save_strikes(strike_counts)

    if action.value == "Terminate":
        terminated_role = interaction.guild.get_role(TERMINATED_ROLE_ID)
        if terminated_role:
            await member.add_roles(terminated_role)

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
    embed.add_field(name="Appealable", value=appealable.value, inline=False)
    embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)

    inf_channel = bot.get_channel(INFRACTION_CHANNEL_ID)
    msg = await inf_channel.send(content=member.mention, embed=embed)

    if appealable.value == "Yes":
        thread = await msg.create_thread(name="Appeal", auto_archive_duration=10080)
        await thread.send(f"Appeal here. Link: {APPEAL_LINK}")

    # DM USER
    try:
        dm_embed = embed.copy()
        if appealable.value == "Yes":
            dm_embed.add_field(name="Appeal Link", value=APPEAL_LINK, inline=False)
        await member.send(embed=dm_embed)
    except:
        pass

    await send_staff_log(embed)

    await interaction.followup.send("Infraction issued.", ephemeral=True)

# ==========================================================
# ======================= CASE SYSTEM ======================
# ==========================================================

CASE_FILE = "case_counter.json"

if os.path.exists(CASE_FILE):
    with open(CASE_FILE, "r") as f:
        case_data = json.load(f)
        case_counter = case_data.get("last_case", 0)
else:
    case_counter = 0


def get_next_case():
    global case_counter
    case_counter += 1

    with open(CASE_FILE, "w") as f:
        json.dump({"last_case": case_counter}, f, indent=4)

    return case_counter
# ==========================================================
# ===================== PROMOTION SYSTEM ===================
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

    # ================= CASE GENERATION =================
    case_number = get_next_case()

    # ================= SAVE TO DATABASE =================
    save_case(
        case_number=case_number,
        case_type="Promotion",
        member_id=member.id,
        moderator_id=interaction.user.id,
        reason=reason
    )
    # ====================================================

    embed = discord.Embed(
        title=f"AZDPS Promotion | Case #{case_number:04d}",
        color=discord.Color.green(),
        timestamp=datetime.utcnow()
    )

    embed.add_field(name="Member", value=member.mention, inline=False)
    embed.add_field(name="New Rank", value=new_rank, inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Approved By", value=interaction.user.mention, inline=False)

    promo_channel = bot.get_channel(PROMOTION_CHANNEL_ID)
    await promo_channel.send(content=member.mention, embed=embed)

    try:
        await member.send(
            f"You have been promoted to {new_rank}.\n"
            f"Reason: {reason}\n"
            f"Case #{case_number:04d}"
        )
    except:
        pass

    await send_staff_log(embed)

    await interaction.followup.send(
        f"Promotion logged under Case #{case_number:04d}.",
        ephemeral=True
    )
# ==========================================================
# ======================== BLACKLIST =======================
# ==========================================================

@bot.tree.command(name="blacklist", description="Blacklist a user or server")
async def blacklist(interaction: discord.Interaction, target_id: str, reason: str):

    await interaction.response.defer(ephemeral=True)

    if not has_permission(interaction.user):
        return await interaction.followup.send("No permission.", ephemeral=True)

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    user = bot.get_user(int(target_id))
    guild = bot.get_guild(int(target_id))

    if user:
        blacklisted_users[target_id] = {
            "date": now,
            "moderator": str(interaction.user.id),
            "reason": reason
        }

        try:
            await user.send(f"You have been blacklisted.\nReason: {reason}")
        except:
            pass

    elif guild:
        blacklisted_servers[target_id] = {
            "date": now,
            "moderator": str(interaction.user.id),
            "reason": reason
        }

        try:
            owner = guild.owner
            await owner.send(f"Your server has been blacklisted.\nReason: {reason}")
        except:
            pass

    else:
        return await interaction.followup.send("Invalid ID.", ephemeral=True)

    with open("blacklist.json", "w") as f:
        json.dump({
            "users": blacklisted_users,
            "servers": blacklisted_servers
        }, f, indent=4)

    await interaction.followup.send("Blacklisted successfully.", ephemeral=True)


# ==========================================================
# ===================== BLACKLIST REMOVE ===================
# ==========================================================

@bot.tree.command(name="blacklistremove", description="Remove from blacklist")
async def blacklistremove(interaction: discord.Interaction, target_id: str):

    if not has_permission(interaction.user):
        return await interaction.response.send_message("No permission.", ephemeral=True)

    removed_data = None

    if target_id in blacklisted_users:
        removed_data = blacklisted_users.pop(target_id)

    elif target_id in blacklisted_servers:
        removed_data = blacklisted_servers.pop(target_id)

    if removed_data:
        with open("blacklist.json", "w") as f:
            json.dump({
                "users": blacklisted_users,
                "servers": blacklisted_servers
            }, f, indent=4)

        await interaction.response.send_message(
            f"Removed from blacklist.\nOriginally added: {removed_data['date']}\nReason: {removed_data['reason']}",
            ephemeral=True
        )
    else:
        await interaction.response.send_message("ID not found.", ephemeral=True)


# ==========================================================
# ====================== BLACKLIST INFO ====================
# ==========================================================

@bot.tree.command(name="blacklistinfo", description="View blacklist details")
async def blacklistinfo(interaction: discord.Interaction, target_id: str):

    if not has_permission(interaction.user):
        return await interaction.response.send_message("No permission.", ephemeral=True)

    data = blacklisted_users.get(target_id) or blacklisted_servers.get(target_id)

    if not data:
        return await interaction.response.send_message("Not blacklisted.", ephemeral=True)

    embed = discord.Embed(
        title="Blacklist Info",
        color=discord.Color.red()
    )

    embed.add_field(name="ID", value=target_id, inline=False)
    embed.add_field(name="Date Added", value=data["date"], inline=False)
    embed.add_field(name="Moderator ID", value=data["moderator"], inline=False)
    embed.add_field(name="Reason", value=data["reason"], inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)

# ==========================================================
# ======================== BAN / UNBAN =====================
# ==========================================================

@bot.tree.command(name="ban", description="Ban a user")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str):

    await interaction.response.defer(ephemeral=True)

    if not has_permission(interaction.user):
        return await interaction.followup.send("No permission.", ephemeral=True)

    try:
        await member.send(f"You were banned.\nReason: {reason}\nAppeal: {APPEAL_LINK}")
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


@bot.tree.command(name="kick", description="Kick a user")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str):

    await interaction.response.defer(ephemeral=True)

    if not has_permission(interaction.user):
        return await interaction.followup.send("No permission.", ephemeral=True)

    try:
        await member.send(f"You were kicked.\nReason: {reason}")
    except:
        pass

    await interaction.guild.kick(member, reason=reason)

    await interaction.followup.send("User kicked.", ephemeral=True)


# ==========================================================
# ====================== ROLE MANAGEMENT ===================
# ==========================================================

@bot.tree.command(name="add-role", description="Add a role to a user")
async def add_role(interaction: discord.Interaction, member: discord.Member, role: discord.Role):

    await interaction.response.defer(ephemeral=True)

    if not has_permission(interaction.user):
        return await interaction.followup.send("No permission.", ephemeral=True)

    await member.add_roles(role)

    await interaction.followup.send(f"Role {role.name} added to {member.mention}.", ephemeral=True)


@bot.tree.command(name="remove-role", description="Remove a role from a user")
async def remove_role(interaction: discord.Interaction, member: discord.Member, role: discord.Role):

    await interaction.response.defer(ephemeral=True)

    if not has_permission(interaction.user):
        return await interaction.followup.send("No permission.", ephemeral=True)

    await member.remove_roles(role)

    await interaction.followup.send(f"Role {role.name} removed from {member.mention}.", ephemeral=True)
    # ==========================================================
# =========================== MUTE =========================
# ==========================================================

@bot.tree.command(name="mute", description="Mute a user")
async def mute(interaction: discord.Interaction, member: discord.Member, duration: str, reason: str):

    await interaction.response.defer(ephemeral=True)

    if not has_permission(interaction.user):
        return await interaction.followup.send("No permission.", ephemeral=True)

    delta = parse_duration(duration)
    if not delta:
        return await interaction.followup.send("Duration must end in d or h.", ephemeral=True)

    until = discord.utils.utcnow() + delta
    await member.timeout(until, reason=reason)

    try:
        await member.send(f"You have been muted.\nDuration: {duration}\nReason: {reason}")
    except:
        pass

    await interaction.followup.send("User muted.", ephemeral=True)


@bot.tree.command(name="unmute", description="Unmute a user")
async def unmute(interaction: discord.Interaction, member: discord.Member):

    await interaction.response.defer(ephemeral=True)

    if not has_permission(interaction.user):
        return await interaction.followup.send("No permission.", ephemeral=True)

    await member.timeout(None)

    await interaction.followup.send("User unmuted.", ephemeral=True)


# ==========================================================
# ======================== FETCH USER ======================
# ==========================================================

@bot.tree.command(name="fetchuser", description="Fetch info about a user")
async def fetchuser(interaction: discord.Interaction, member: discord.Member):

    embed = discord.Embed(
        title="User Info",
        color=discord.Color.blue()
    )

    embed.add_field(name="Username", value=str(member), inline=False)
    embed.add_field(name="ID", value=member.id, inline=False)
    embed.add_field(name="Joined", value=member.joined_at, inline=False)
    embed.add_field(name="Created", value=member.created_at, inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


# # ==========================================================
# ========================== UPDATE =========================
# ==========================================================

UPDATE_CHANNEL_ID = 1474211686947885187


@app_commands.default_permissions(administrator=True)
@bot.tree.command(name="update", description="Send a department update")
@app_commands.describe(
    number="Update number (example: 010)",
    update="The update message"
)
async def update(interaction: discord.Interaction, number: str, update: str):

    if not has_permission(interaction.user):
        return await interaction.response.send_message("No permission.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)

    update_channel = bot.get_channel(UPDATE_CHANNEL_ID)

    if update_channel is None:
        return await interaction.followup.send("Update channel not found.", ephemeral=True)

    formatted_message = (
        f"<:AZDPS:1312784566725120030> "
        f"Department Update #{number} "
        f"<:AZDPS:1312784566725120030>\n\n"
        f"> {update}"
    )

    await update_channel.send(formatted_message)

    await interaction.followup.send("Department update sent successfully.", ephemeral=True)
# ==========================================================
# =========================== SAY ==========================
# ==========================================================

@bot.tree.command(name="say", description="Make the bot say something")
async def say(interaction: discord.Interaction, message: str):

    if not has_permission(interaction.user):
        return await interaction.response.send_message("No permission.", ephemeral=True)

    await interaction.channel.send(message)
    await interaction.response.send_message("Sent.", ephemeral=True)


# ==========================================================
# ======================= SERVER INFO ======================
# ==========================================================

@bot.tree.command(name="serverinfo", description="Get server info")
async def serverinfo(interaction: discord.Interaction):

    guild = interaction.guild

    embed = discord.Embed(
        title=guild.name,
        color=discord.Color.blurple()
    )

    embed.add_field(name="Members", value=guild.member_count)
    embed.add_field(name="Owner", value=guild.owner)
    embed.add_field(name="Created", value=guild.created_at)

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ==========================================================
# ========================== ACCOUNT =======================
# ==========================================================

@bot.tree.command(name="account", description="Get your account info")
async def account(interaction: discord.Interaction):

    member = interaction.user

    embed = discord.Embed(
        title="Account Info",
        color=discord.Color.green()
    )

    embed.add_field(name="Username", value=str(member))
    embed.add_field(name="ID", value=member.id)
    embed.add_field(name="Created", value=member.created_at)

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ==========================================================
# ====================== SUGGESTION SYSTEM =================
# ==========================================================

@bot.tree.command(name="suggest", description="Create a suggestion")
async def suggest(interaction: discord.Interaction, title: str, suggestion: str):

    await interaction.response.defer(ephemeral=True)

    forum = bot.get_channel(SUGGESTION_FORUM_ID)

    embed = discord.Embed(
        title=title,
        description=suggestion,
        color=discord.Color.orange(),
        timestamp=datetime.utcnow()
    )

    embed.add_field(name="Status", value="<@&1475602330148802842>", inline=False)
    embed.set_footer(text=f"Suggested by {interaction.user}")

    thread = await forum.create_thread(
        name=title,
        content="<@&1475602330148802842>",
        embed=embed
    )

    await interaction.followup.send("Suggestion posted.", ephemeral=True)


@bot.tree.command(name="suggestapprove", description="Approve a suggestion")
async def suggestapprove(interaction: discord.Interaction):

    if not has_permission(interaction.user):
        return await interaction.response.send_message("No permission.", ephemeral=True)

    embed = interaction.channel.last_message.embeds[0]
    embed.color = discord.Color.green()
    embed.set_field_at(0, name="Status", value="<@&1475602324230770901>", inline=False)

    await interaction.channel.send("<@&1475602324230770901>")
    await interaction.channel.last_message.edit(embed=embed)

    await interaction.response.send_message("Suggestion approved.", ephemeral=True)


@bot.tree.command(name="suggestdeny", description="Deny a suggestion")
async def suggestdeny(interaction: discord.Interaction):

    if not has_permission(interaction.user):
        return await interaction.response.send_message("No permission.", ephemeral=True)

    embed = interaction.channel.last_message.embeds[0]
    embed.color = discord.Color.red()
    embed.set_field_at(0, name="Status", value="<@&1475602332829089842>", inline=False)

    await interaction.channel.send("<@&1475602332829089842>")
    await interaction.channel.last_message.edit(embed=embed)

    await interaction.response.send_message("Suggestion denied.", ephemeral=True)


@bot.tree.command(name="suggestpending", description="Mark suggestion as pending")
async def suggestpending(interaction: discord.Interaction):

    if not has_permission(interaction.user):
        return await interaction.response.send_message("No permission.", ephemeral=True)

    embed = interaction.channel.last_message.embeds[0]
    embed.color = discord.Color.orange()
    embed.set_field_at(0, name="Status", value="<@&1475602330148802842>", inline=False)

    await interaction.channel.send("<@&1475602330148802842>")
    await interaction.channel.last_message.edit(embed=embed)

    await interaction.response.send_message("Suggestion pending.", ephemeral=True)
# ==========================================================
# =========================== LOCK =========================
# ==========================================================

@bot.tree.command(name="lock", description="Lock a channel")
async def lock(interaction: discord.Interaction, channel: discord.TextChannel = None):

    if not has_permission(interaction.user):
        return await interaction.response.send_message("No permission.", ephemeral=True)

    channel = channel or interaction.channel

    await channel.set_permissions(interaction.guild.default_role, send_messages=False)

    await interaction.response.send_message(f"{channel.mention} has been locked.")


# ==========================================================
# ========================== UNLOCK ========================
# ==========================================================

@bot.tree.command(name="unlock", description="Unlock a channel")
async def unlock(interaction: discord.Interaction, channel: discord.TextChannel = None):

    if not has_permission(interaction.user):
        return await interaction.response.send_message("No permission.", ephemeral=True)

    channel = channel or interaction.channel

    await channel.set_permissions(interaction.guild.default_role, send_messages=True)

    await interaction.response.send_message(f"{channel.mention} has been unlocked.")


# ==========================================================
# ========================= SLOWMODE =======================
# ==========================================================

@bot.tree.command(name="slowmode", description="Set slowmode in a channel")
async def slowmode(interaction: discord.Interaction, seconds: int, channel: discord.TextChannel = None):

    if not has_permission(interaction.user):
        return await interaction.response.send_message("No permission.", ephemeral=True)

    channel = channel or interaction.channel

    await channel.edit(slowmode_delay=seconds)

    await interaction.response.send_message(
        f"Slowmode set to {seconds} seconds in {channel.mention}."
    )


# ==========================================================
# ============================ WARN ========================
# ==========================================================

warnings = {}

@bot.tree.command(name="warn", description="Warn a user")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):

    if not has_permission(interaction.user):
        return await interaction.response.send_message("No permission.", ephemeral=True)

    if member.id not in warnings:
        warnings[member.id] = []

    warnings[member.id].append({
        "moderator": interaction.user.id,
        "reason": reason
    })

    try:
        await member.send(f"You were warned.\nReason: {reason}")
    except:
        pass

    await interaction.response.send_message(
        f"{member.mention} has been warned."
    )


# ==========================================================
# ========================== STRIKES =======================
# ==========================================================

@bot.tree.command(name="strikes", description="View a user's warnings")
async def strikes(interaction: discord.Interaction, member: discord.Member):

    if not has_permission(interaction.user):
        return await interaction.response.send_message("No permission.", ephemeral=True)

    user_warnings = warnings.get(member.id)

    if not user_warnings:
        return await interaction.response.send_message(
            "No strikes found.", ephemeral=True
        )

    description = ""
    for i, warn_data in enumerate(user_warnings, start=1):
        description += f"Strike {i}: {warn_data['reason']}\n"

    embed = discord.Embed(
        title=f"{member.name}'s Strikes",
        description=description,
        color=discord.Color.orange()
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ==========================================================
# ======================== STRIKE RESET ====================
# ==========================================================

@bot.tree.command(name="strikereset", description="Reset a user's strikes")
async def strikereset(interaction: discord.Interaction, member: discord.Member):

    if not has_permission(interaction.user):
        return await interaction.response.send_message("No permission.", ephemeral=True)

    if member.id in warnings:
        warnings.pop(member.id)

    await interaction.response.send_message(
        f"{member.mention}'s strikes have been reset."
    )


# ==========================================================
# ============================ AUDIT =======================
# ==========================================================

@bot.tree.command(name="audit", description="View recent audit logs")
async def audit(interaction: discord.Interaction):

    if not has_permission(interaction.user):
        return await interaction.response.send_message("No permission.", ephemeral=True)

    logs = []
    async for entry in interaction.guild.audit_logs(limit=5):
        logs.append(f"{entry.user} did {entry.action}")

    embed = discord.Embed(
        title="Recent Audit Logs",
        description="\n".join(logs) if logs else "No logs found.",
        color=discord.Color.blurple()
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ==========================================================
# ===================== FORCE APPEAL CLOSE =================
# ==========================================================

@bot.tree.command(name="forceappealclose", description="Force close an appeal thread")
async def forceappealclose(interaction: discord.Interaction):

    if not has_permission(interaction.user):
        return await interaction.response.send_message("No permission.", ephemeral=True)

    if isinstance(interaction.channel, discord.Thread):
        await interaction.channel.edit(archived=True, locked=True)
        await interaction.response.send_message("Appeal thread closed.")
    else:
        await interaction.response.send_message(
            "This command must be used inside an appeal thread.",
            ephemeral=True
        )
# ==========================================================
# ======================= CASE DATABASE ====================
# ==========================================================

CASE_DB_FILE = "cases.json"

if os.path.exists(CASE_DB_FILE):
    with open(CASE_DB_FILE, "r") as f:
        case_database = json.load(f)
else:
    case_database = {}


def save_case(case_number, case_type, member_id, moderator_id, reason):
    case_database[str(case_number)] = {
        "type": case_type,
        "member": str(member_id),
        "moderator": str(moderator_id),
        "reason": reason,
        "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(CASE_DB_FILE, "w") as f:
        json.dump(case_database, f, indent=4)
        # ==========================================================
# ========================== CASE LOOKUP ===================
# ==========================================================

@bot.tree.command(name="case", description="Lookup a case by number")
@app_commands.describe(case_number="Case number (example: 23)")
async def case_lookup(interaction: discord.Interaction, case_number: int):

    if not has_permission(interaction.user):
        return await interaction.response.send_message("No permission.", ephemeral=True)

    case_data = case_database.get(str(case_number))

    if not case_data:
        return await interaction.response.send_message("Case not found.", ephemeral=True)

    member = interaction.guild.get_member(int(case_data["member"]))
    moderator = interaction.guild.get_member(int(case_data["moderator"]))

    embed = discord.Embed(
        title=f"Case #{case_number:04d}",
        color=discord.Color.blurple()
    )

    embed.add_field(name="Type", value=case_data["type"], inline=False)
    embed.add_field(name="Member", value=member.mention if member else case_data["member"], inline=False)
    embed.add_field(name="Moderator", value=moderator.mention if moderator else case_data["moderator"], inline=False)
    embed.add_field(name="Reason", value=case_data["reason"], inline=False)
    embed.add_field(name="Date", value=case_data["date"], inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)
    # ==========================================================
# ======================= USER CASES =======================
# ==========================================================

@bot.tree.command(name="cases", description="View all cases for a member")
@app_commands.describe(member="Member to lookup")
async def cases(interaction: discord.Interaction, member: discord.Member):

    if not has_permission(interaction.user):
        return await interaction.response.send_message("No permission.", ephemeral=True)

    user_cases = []

    for case_number, data in case_database.items():
        if data["member"] == str(member.id):
            user_cases.append((int(case_number), data))

    if not user_cases:
        return await interaction.response.send_message(
            "No cases found for this member.",
            ephemeral=True
        )

    user_cases.sort(key=lambda x: x[0])

    description = ""
    for case_number, data in user_cases:
        description += (
            f"Case #{int(case_number):04d} | "
            f"{data['type']} | "
            f"{data['date']}\n"
        )

    embed = discord.Embed(
        title=f"Cases for {member}",
        description=description,
        color=discord.Color.blurple()
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ==========================================================
# ======================= CASE COUNT =======================
# ==========================================================

@bot.tree.command(name="casecount", description="View total case count")
async def casecount(interaction: discord.Interaction):

    if not has_permission(interaction.user):
        return await interaction.response.send_message("No permission.", ephemeral=True)

    total_cases = len(case_database)

    embed = discord.Embed(
        title="Total Cases Issued",
        description=f"{total_cases} total cases in database.",
        color=discord.Color.green()
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)
    
# ==========================================================
# ======================= CHAIN OF COMMAND =======================
# ==========================================================
@bot.tree.command(name="chainofcommand", description="View the Arizona Department of Public Safety Chain of Command")
async def chainofcommand(interaction: discord.Interaction):

    embed = discord.Embed(
        title="Arizona Department of Public Safety - Chain of Command",
        color=discord.Color.red()
    )

    # High Command
    embed.add_field(
        name="High Command",
        value=(
            "Commissioner\n"
            "Acting Commissioner (If Applicable)\n"
            "Deputy Commissioner\n"
            "Assistant Commissioner\n"
            "Superintendent\n"
            "Colonel"
        ),
        inline=False
    )

    # Supervisors
    embed.add_field(
        name="Supervisors",
        value=(
            "Lieutenant Colonel\n"
            "Major\n"
            "Captain\n"
            "Lieutenant"
        ),
        inline=False
    )

    # Field Supervisors
    embed.add_field(
        name="Field Supervisors",
        value=(
            "Sergeant First Class\n"
            "Staff Sergeant\n"
            "Sergeant\n"
            "Trial Sergeant"
        ),
        inline=False
    )

    # Field Patrol
    embed.add_field(
        name="Field Patrol",
        value=(
            "Corporal\n"
            "Lance Corporal\n"
            "Master Trooper\n"
            "Senior Trooper\n"
            "Trooper First Class\n"
            "Trooper Second Class\n"
            "Trooper Third Class"
        ),
        inline=False
    )

    # FTO Program
    embed.add_field(
        name="Field Training Officer Program",
        value="Probationary Trooper",
        inline=False
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)
# ==========================================================
# =========================== PING ==========================
# ==========================================================

import time

@bot.tree.command(name="ping", description="View bot latency and response time")
async def ping(interaction: discord.Interaction):

    start_time = time.perf_counter()

    await interaction.response.defer(ephemeral=True)

    end_time = time.perf_counter()
    api_latency = round((end_time - start_time) * 1000)
    websocket_latency = round(bot.latency * 1000)

    embed = discord.Embed(
        title="Pong!",
        color=discord.Color.green()
    )

    embed.add_field(
        name="WebSocket Latency",
        value=f"{websocket_latency} ms",
        inline=False
    )

    embed.add_field(
        name="API Response Time",
        value=f"{api_latency} ms",
        inline=False
    )

    embed.set_footer(text="Wrd.Jaxk")

    await interaction.followup.send(embed=embed, ephemeral=True)
    
# ==========================================================
# ========================== RUN BOT =======================
# ==========================================================

bot.run(TOKEN)