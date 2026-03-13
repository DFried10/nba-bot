import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
 
load_dotenv()
 
intents = discord.Intents.default()
intents.message_content = True
 
bot = commands.Bot(command_prefix="!", intents=intents)
 
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")
 
async def setup():
    await bot.load_extension("commands.player")
    await bot.load_extension("commands.team")
 
async def main():
    async with bot:
        await setup()
        await bot.start(os.getenv("DISCORD_TOKEN"))
 
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())