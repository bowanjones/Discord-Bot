from discord.ext.commands import check
import time
import os
import logging
import discord
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType
import yfinance as yf
from dotenv import load_dotenv
import datetime

CHANNELS = {
    "welcome": 1397334679706800168,
    "rules": 1397335801305501838,
    "announcements": 1397335829461860423,
    "stock_bot": 1397336028607545435,
    "trade_bot": 1397336069573312634,
    "test_lab": 1397336095775264799,
    "stock_chat": 1397336144672325745,
    "stock_info": 1397336166113476699,
    "discord_store": 1399515025605001298,  # <- store commands allowed only here
}

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Enable message content intent
intents = discord.Intents.default()
intents.message_content = True

# Create the bot instance
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"✅  Logged in as {bot.user} (id={bot.user.id})")
    
#Welcome
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(CHANNELS["welcome"])
    if channel:
        await channel.send(f"👋 Welcome {member.mention} to the server! Make sure to read the 📏rules.")

#Rules
@bot.command()
async def rules(ctx):
    if ctx.channel.id != CHANNELS["rules"]:
        return
    await ctx.send("📏 **Server Rules**:\n1. Be kind.\n2. No spam.\n3. Stay on topic.\n4. Respect others.")

#Announcements
@bot.command()
async def announce(ctx, *, message):
    if ctx.channel.id != CHANNELS["announcements"]:
        return
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send("❌ Only admins can post announcements.")
    await ctx.send(f"📢 **Announcement:**\n{message}")

#Trade Bot
@bot.command()
async def logtrade(ctx, *, trade_note):
    if ctx.channel.id != CHANNELS["trade_bot"]:
        return
    await ctx.send(f"📒 Trade logged: `{trade_note}`")

#Stock Chat
@bot.event
async def on_message(message):
    await bot.process_commands(message)  # ensure other commands still run

    if message.author.bot:
        return

    if message.channel.id == CHANNELS["stock_chat"]:
        user_id = message.author.id
        user_balances[user_id] = user_balances.get(user_id, 0) + 1  # +1 coin per msg
        print(f"🪙 Gave 1 coin to {message.author.name} for chatting in stock-chat.")

#Stock Info
@bot.command()
async def moreinfo(ctx, symbol: str):
    if ctx.channel.id != CHANNELS["stock_info"]:
        return
    symbol = symbol.upper().strip()
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        description = info.get("longBusinessSummary", "No description.")
        await ctx.send(f"📝 **{symbol} Description**:\n{description[:1000]}")
    except Exception as e:
        await ctx.send("⚠️ Could not fetch extended info.")

#Store
def is_store_channel():
    async def predicate(ctx):
        return ctx.channel.id == CHANNELS["discord_store"]
    return check(predicate)

# In-memory user balance
user_balances = {}

# Track when each user last claimed their daily reward
last_daily_claim = {}

@bot.command()
@is_store_channel()
async def daily(ctx):
    user_id = ctx.author.id
    now = time.time()
    last_claim = last_daily_claim.get(user_id, 0)

    # 86400 seconds = 24 hours
    if now - last_claim < 86400:
        remaining = int(86400 - (now - last_claim))
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        seconds = remaining % 60
        return await ctx.send(
            f"⏳ You already claimed your daily reward. Try again in {hours}h {minutes}m {seconds}s."
        )

    reward_amount = 50  # customize as needed
    user_balances[user_id] = user_balances.get(user_id, 0) + reward_amount
    last_daily_claim[user_id] = now

    await ctx.send(f"🎁 {ctx.author.mention}, you received **{reward_amount} coins** for your daily check-in!")


@bot.command()
async def balance(ctx):
    user = ctx.author.id
    balance = user_balances.get(user, 0)
    await ctx.send(f"{ctx.author.mention}, your balance is {balance} coins.")

@bot.command()
async def give(ctx, member: discord.Member, amount: int):
    if ctx.author.guild_permissions.administrator:
        user_balances[member.id] = user_balances.get(member.id, 0) + amount
        await ctx.send(f"Gave {amount} coins to {member.mention}.")

store_items = {
    "vip": {"price": 100, "role_name": "VIP"},
}

@bot.command()
async def buy(ctx, item_name):
    user = ctx.author.id
    item = store_items.get(item_name)
    if not item:
        return await ctx.send("Item not found.")

    if user_balances.get(user, 0) < item["price"]:
        return await ctx.send("Not enough coins!")

    role = discord.utils.get(ctx.guild.roles, name=item["role_name"])
    if role:
        await ctx.author.add_roles(role)
        user_balances[user] -= item["price"]
        await ctx.send(f"{ctx.author.mention} bought {item_name} and received the {role.name} role!")


#Error Handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        if ctx.channel.id not in CHANNELS.values():
            return
        await ctx.send("⚠️ You can't use this command in this channel. Please use the correct one.")


