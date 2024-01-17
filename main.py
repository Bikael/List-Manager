import asyncio
import os 
import discord
import certifi
from dotenv import load_dotenv
from discord.ext import commands

os.environ['SSL_CERT_FILE'] = certifi.where()
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

intents = discord.Intents.all()
intents.members = True

bot = commands.Bot(command_prefix='.', intents=intents, help_command= None)

async def load():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

async def main():
    await load()
    await bot.start(BOT_TOKEN)

asyncio.run(main())
