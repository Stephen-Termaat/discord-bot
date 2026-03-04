import os
import discord
from discord import app_commands
from discord.ext import commands

# Allowed role IDs (people who can run the command)
ALLOWED_ROLE_IDS = [
    1458973055924834305,
    1458973048001532136
]

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

    print(f"Logged in as {bot.user}")

@bot.tree.command(name="promotion_issue", description="Promote a trooper@")
@app_commands.describe(
    member="The member you want to promote",
    role="The role you want to give them"
)
async def promotion_issue(interaction: discord.Interaction, member: discord.Member, role: discord.Role):

    # Check if user has one of the allowed roles
    if not any(r.id in ALLOWED_ROLE_IDS for r in interaction.user.roles):
        await interaction.response.send_message(
            "❌ You do not have permission to use this command.",
            ephemeral=True
        )
        return

    # Role hierarchy checks
    if role >= interaction.guild.me.top_role:
        await interaction.response.send_message(
            "❌ That role is higher than my highest role.",
            ephemeral=True
        )
        return

    if member.top_role >= interaction.guild.me.top_role:
        await interaction.response.send_message(
            "❌ I cannot modify that member due to role hierarchy.",
            ephemeral=True
        )
        return

    try:
        await member.add_roles(role)
        await interaction.response.send_message(
            f"✅ {member.mention} has been promoted to {role.mention}."
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I don't have permission to manage roles.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"⚠️ Error: {str(e)}",
            ephemeral=True
        )

# Get token from Railway Variables
TOKEN = os.getenv("DISCORD_TOKEN")

bot.run(TOKEN)
