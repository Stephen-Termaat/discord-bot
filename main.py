import os
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

@bot.tree.command(name="test")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message("Bot is working.")

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
