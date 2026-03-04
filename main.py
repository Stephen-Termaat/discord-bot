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
# STRIKE STORAGE (PERMANENT)
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

@bot.tree.command(name="promotion", description="Promote a member")
@app_commands.describe(
    member="Member being promoted",
    role="New role being given"
)
async def promotion(interaction: discord.Interaction, member: discord.Member, role: discord.Role):

    await interaction.response.defer()

    try:
        if member.top_role >= interaction.guild.me.top_role:
            await interaction.followup.send(
                "❌ My role must be above this user's top role to promote them.",
                ephemeral=True
            )
            return

        await member.add_roles(role)

        embed1 = discord.Embed()
        embed1.set_image(
            url="https://cdn.discordapp.com/attachments/1463985139431379078/1478563632970207323/Copy_of_Copy_of_Balkwy_Creations.png"
        )

        embed2 = discord.Embed(
            title="**<:AZDPS:1312784566725120030> | AZDPS Promotion**",
            description=(
                f"High Command has deemed you fit for a promotion.\n"
                f"{member.mention} ----------> {role.mention}\n"
                f"Please review your new roles, and duties. Congratulations!"
            )
        )
        embed2.set_footer(text="Signed,\nAZDPS High Command Team")

        await interaction.followup.send(embeds=[embed1, embed2])

    except discord.Forbidden:
        await interaction.followup.send(
            "❌ I do not have permission to modify this user's roles.",
            ephemeral=True
        )

    except Exception as e:
        await interaction.followup.send(
            f"⚠️ Unexpected error: {str(e)}",
            ephemeral=True
        )

# ==============================
# INFRACTION COMMAND
# ==============================

@bot.tree.command(name="infraction", description="Issue an infraction to a member")
@app_commands.describe(
    member="The member receiving the infraction",
    action="Type of infraction",
    reason="Reason for the infraction"
)
@app_commands.choices(action=[
    app_commands.Choice(name="Strike", value="Strike"),
    app_commands.Choice(name="Terminate", value="Terminate"),
    app_commands.Choice(name="Suspend", value="Suspend"),
    app_commands.Choice(name="Warning", value="Warning"),
])
async def infraction(
    interaction: discord.Interaction,
    member: discord.Member,
    action: app_commands.Choice[str],
    reason: str = "No reason provided."
):

    await interaction.response.defer()

    # Role hierarchy protection
    if member.top_role >= interaction.guild.me.top_role:
        await interaction.followup.send(
            "❌ My role must be above this user's top role to infract them.",
            ephemeral=True
        )
        return

    try:
        user_id = str(member.id)
        strike_counts[user_id] = strike_counts.get(user_id, 0)

        role1 = interaction.guild.get_role(STRIKE_ROLE_1)
        role2 = interaction.guild.get_role(STRIKE_ROLE_2)
        terminated_role = interaction.guild.get_role(TERMINATED_ROLE)

        # ==========================
        # STRIKE LOGIC
        # ==========================

        if action.value == "Strike":

            strike_counts[user_id] += 1
            strike_number = strike_counts[user_id]

            # Cap at 3
            if strike_number > 3:
                strike_counts[user_id] = 3

            save_strikes(strike_counts)

            if strike_counts[user_id] == 1:
                if role1 and role1 not in member.roles:
                    await member.add_roles(role1)

            elif strike_counts[user_id] == 2:
                if role1 and role1 not in member.roles:
                    await member.add_roles(role1)

                if role2 and role2 not in member.roles:
                    await member.add_roles(role2)

            elif strike_counts[user_id] == 3:
                if role1 and role1 in member.roles:
                    await member.remove_roles(role1)

                if role2 and role2 in member.roles:
                    await member.remove_roles(role2)

                if terminated_role and terminated_role not in member.roles:
                    await member.add_roles(terminated_role)

        elif action.value == "Terminate":

            strike_counts[user_id] = 3
            save_strikes(strike_counts)

            if role1 and role1 in member.roles:
                await member.remove_roles(role1)

            if role2 and role2 in member.roles:
                await member.remove_roles(role2)

            if terminated_role and terminated_role not in member.roles:
                await member.add_roles(terminated_role)

        # Warning and Suspend do not change strikes
        current_infraction_display = f"{strike_counts[user_id]} / 3"

        # ==========================
        # EMBEDS
        # ==========================

        embed1 = discord.Embed()
        embed1.set_image(
            url="https://cdn.discordapp.com/attachments/1463985139431379078/1478849460795740413/Copy_of_Copy_of_Balkwy_Creations.png"
        )

        embed2 = discord.Embed(
            title="**<:AZDPS:1312784566725120030> | AZDPS Infraction**",
            description=(
                f"Unfortunately, High Command has decided to infract you.\n"
                f"Please review the rules to avoid being infracted again.\n\n"
                f"User: {member.mention}\n"
                f"Infraction Type: {action.value}\n"
                f"Current Infractions: {current_infraction_display}\n"
                f"Reason: {reason}"
            )
        )
        embed2.set_footer(text="Signed,\nAZDPS High Command Team")

        await interaction.followup.send(embeds=[embed1, embed2])

    except discord.Forbidden:
        await interaction.followup.send(
            "❌ I do not have permission to modify this user's roles.",
            ephemeral=True
        )

    except Exception as e:
        await interaction.followup.send(
            f"⚠️ Unexpected error: {str(e)}",
            ephemeral=True
        )

# ==============================
# RUN BOT
# ==============================

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)