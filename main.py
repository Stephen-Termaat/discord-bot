import os
import json
import discord
from discord import app_commands
from discord.ext import commands

# ==============================
# CONFIG
# ==============================

STRIKE_ROLE_1 = 1458973175814557800
STRIKE_ROLE_2 = 1458973176573857982
TERMINATED_ROLE = 1467017398736654521

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
# READY EVENT
# ==============================

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

    print(f"Logged in as {bot.user}")

# ==============================
# PROMOTION COMMAND
# ==============================

@bot.tree.command(name="promotiondps", description="Promote a member (DPS System)")
@app_commands.describe(member="Member being promoted", role="New role being given")
async def promotiondps(interaction: discord.Interaction, member: discord.Member, role: discord.Role):

    await interaction.response.defer()

    if member.top_role >= interaction.guild.me.top_role:
        await interaction.followup.send("❌ My role must be above this user's top role.", ephemeral=True)
        return

    try:
        await member.add_roles(role)

        embed = discord.Embed(
            title="**<:AZDPS:1312784566725120030> | AZDPS Promotion**",
            description=(
                f"High Command has deemed you fit for a promotion.\n"
                f"{member.mention} ----------> {role.mention}\n"
                f"Please review your new roles, and duties. Congratulations!"
            )
        )
        embed.set_image(url="https://cdn.discordapp.com/attachments/1463985139431379078/1478563632970207323/Copy_of_Copy_of_Balkwy_Creations.png")
        embed.set_footer(text="Signed,\nAZDPS High Command Team")

        await interaction.followup.send(embed=embed)

    except discord.Forbidden:
        await interaction.followup.send("❌ I lack permissions.", ephemeral=True)

# ==============================
# INFRACTION COMMAND
# ==============================

@bot.tree.command(name="infractiondps", description="Issue an infraction (DPS System)")
@app_commands.describe(member="Member receiving infraction", action="Type", reason="Reason")
@app_commands.choices(action=[
    app_commands.Choice(name="Strike", value="Strike"),
    app_commands.Choice(name="Terminate", value="Terminate"),
    app_commands.Choice(name="Suspend", value="Suspend"),
    app_commands.Choice(name="Warning", value="Warning"),
])
async def infractiondps(interaction: discord.Interaction, member: discord.Member, action: app_commands.Choice[str], reason: str = "No reason provided."):

    await interaction.response.defer()

    if member.top_role >= interaction.guild.me.top_role:
        await interaction.followup.send("❌ My role must be above this user's top role.", ephemeral=True)
        return

    try:
        user_id = str(member.id)
        strike_counts[user_id] = strike_counts.get(user_id, 0)

        role1 = interaction.guild.get_role(STRIKE_ROLE_1)
        role2 = interaction.guild.get_role(STRIKE_ROLE_2)
        terminated_role = interaction.guild.get_role(TERMINATED_ROLE)

        if action.value == "Strike":
            strike_counts[user_id] += 1
            if strike_counts[user_id] > 3:
                strike_counts[user_id] = 3
            save_strikes(strike_counts)

            if strike_counts[user_id] == 1 and role1:
                await member.add_roles(role1)

            elif strike_counts[user_id] == 2:
                if role1: await member.add_roles(role1)
                if role2: await member.add_roles(role2)

            elif strike_counts[user_id] == 3:
                if role1 and role1 in member.roles:
                    await member.remove_roles(role1)
                if role2 and role2 in member.roles:
                    await member.remove_roles(role2)
                if terminated_role:
                    await member.add_roles(terminated_role)

        elif action.value == "Terminate":
            strike_counts[user_id] = 3
            save_strikes(strike_counts)

            if role1 and role1 in member.roles:
                await member.remove_roles(role1)
            if role2 and role2 in member.roles:
                await member.remove_roles(role2)
            if terminated_role:
                await member.add_roles(terminated_role)

        embed = discord.Embed(
            title="**<:AZDPS:1312784566725120030> | AZDPS Infraction**",
            description=(
                f"Unfortunately, High Command has decided to infract you.\n\n"
                f"User: {member.mention}\n"
                f"Infraction Type: {action.value}\n"
                f"Current Infractions: {strike_counts[user_id]} / 3\n"
                f"Reason: {reason}"
            )
        )
        embed.set_image(url="https://cdn.discordapp.com/attachments/1463985139431379078/1478849460795740413/Copy_of_Copy_of_Balkwy_Creations.png")
        embed.set_footer(text="Signed,\nAZDPS High Command Team")

        await interaction.followup.send(embed=embed)

    except discord.Forbidden:
        await interaction.followup.send("❌ I lack permissions.", ephemeral=True)

# ==============================
# RUN BOT
# ==============================

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)