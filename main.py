print("BOT STARTING...")

import os
import discord
from discord import app_commands
from discord.ext import commands

ALLOWED_ROLE_IDS = [
    1458973055924834305,
    1458973048001532136
]

# 🔥 PROMOTION LOG CHANNEL
PROMOTION_LOG_CHANNEL_ID = 1297339994842595398

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

@bot.tree.command(name="promotion_issue", description="Promote a trooper")
@app_commands.describe(
    member="The member you want to promote",
    role="The role you want to give them"
)
async def promotion_issue(interaction: discord.Interaction, member: discord.Member, role: discord.Role):

    # ✅ FIX: Defer interaction to avoid timeout
    await interaction.response.defer()

    if not any(r.id in ALLOWED_ROLE_IDS for r in interaction.user.roles):
        await interaction.followup.send(
            "❌ You do not have permission to use this command.",
            ephemeral=True
        )
        return

    if role >= interaction.guild.me.top_role:
        await interaction.followup.send(
            "❌ That role is higher than my highest role.",
            ephemeral=True
        )
        return

    if member.top_role >= interaction.guild.me.top_role:
        await interaction.followup.send(
            "❌ I cannot modify that member due to role hierarchy.",
            ephemeral=True
        )
        return

    try:
        # ✅ Add role
        await member.add_roles(role)

        # ✅ Command response
        await interaction.followup.send(
            f"✅ {member.mention} has been promoted to {role.mention}."
        )

        # 🔥 EMBED 1 — IMAGE
        embed_image = discord.Embed()
        embed_image.set_image(
            url="https://cdn.discordapp.com/attachments/1463985139431379078/1478563632970207323/Copy_of_Copy_of_Balkwy_Creations.png"
        )

        # 🔥 EMBED 2 — PROMOTION
        embed_main = discord.Embed(
            title="**<:AZDPS:1312784566725120030> | AZDPS Promotion**",
            description=(
                "High Command has deemed you fit for a promotion.\n"
                f"{member.mention} ----------> {role.mention}\n"
                "Please review your new roles, and duties. Congratulations!"
            ),
            color=discord.Color.gold()
        )

        embed_main.set_footer(
            text="Signed,\nAZDPS High Command Team"
        )

        # 🔥 SAFE CHANNEL FETCH
        log_channel = interaction.guild.get_channel(PROMOTION_LOG_CHANNEL_ID)
        if log_channel is None:
            log_channel = await bot.fetch_channel(PROMOTION_LOG_CHANNEL_ID)

        await log_channel.send(embeds=[embed_image, embed_main])

    except discord.Forbidden:
        await interaction.followup.send(
            "❌ I don't have permission to manage roles.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(
            f"⚠️ Error: {str(e)}",
            ephemeral=True
        )

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
