import os
import json
import discord
from discord.ext import commands
from dotenv import load_dotenv
import yfinance as yf  # for stock info
from discord.ui import Button, View
import random

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True  # Needed to read message content for commands

bot = commands.Bot(command_prefix='!', intents=intents, description="Community & Market Bot")

# ----- NEW MEMBER -----
@bot.command(name='welcome')
async def welcome_committee(ctx):
    if ctx.channel.name != '🆕welcome-committee':
        return  # Only allow this command in the welcome committee channel

    welcome_message = """
    **👋 Welcome to the Welcome Committee!**

    Your role is super important in making new members feel at home. Here’s what you do:
    - Greet newcomers warmly 👋
    - Answer their questions ❓
    - Guide them through server rules and channels 📜
    - Help create a friendly and inclusive atmosphere 💖

    If you have any questions or need support, reach out to the moderators or admins anytime!

    Thank you for being part of our awesome team! 🚀
    """

    await ctx.send(welcome_message)


# ----- COMMUNITY COMMANDS -----
@bot.group(name='community', invoke_without_command=True)
async def community(ctx):
    await ctx.send("Community commands: !community greet, !community rules")

@community.command()
async def greet(ctx):
    await ctx.send(f"Hello {ctx.author.mention}! Welcome to the community!")

@community.command()
async def rules(ctx):
    rules_text = """
    **Community Rules**
    1. Be respectful
    2. No spam
    3. Follow Discord Terms of Service
    """
    await ctx.send(rules_text)

# ----- INFORMATION COMMANDS -----
@bot.command(name='newvideo')
async def announce_new_video(ctx, url: str, *, description: str = None):
    # Only allow in the #new-videos channel
    if ctx.channel.name != '‼️new-videos':
        await ctx.send(f"Please use this command in the #new-videos channel, {ctx.author.mention}.")
        return

    description_text = description if description else "Check out this new video!"

    embed = discord.Embed(
        title="🎬 New Video Alert!",
        description=description_text,
        url=url,
        color=discord.Color.red()
    )
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    embed.add_field(name="Watch here:", value=f"[Click to watch]({url})", inline=False)
    embed.set_footer(text="Support our creators! 🚀")

    await ctx.send(embed=embed)

@bot.group(name='info', invoke_without_command=True)
async def info(ctx):
    await ctx.send("Information commands: !info server, !info user")

@info.command()
async def server(ctx):
    server = ctx.guild
    await ctx.send(f"Server name: {server.name}\nMembers: {server.member_count}")

@info.command()
async def user(ctx, member: discord.Member = None):
    member = member or ctx.author
    await ctx.send(f"User info for {member.name}#{member.discriminator} (ID: {member.id})")

# Define the stockbot channel name
STOCKBOT_CHANNEL = "🤖stockbot"

# ----- STOCKS COMMANDS -----
@bot.group(name='stocks', invoke_without_command=True)
async def stocks(ctx):
    if ctx.channel.name != STOCKBOT_CHANNEL:
        return  # Ignore if not in stockbot channel
    help_msg = (
        "Stocks commands:\n"
        "`!stocks price <ticker>` - Current stock price\n"
        "`!stocks summary <ticker>` - Company summary\n"
        "`!stocks stats <ticker>` - Key statistics\n"
        "`!stocks history <ticker> <days>` - Closing prices for past days\n"
        "`!stocks news <ticker>` - Latest news headlines\n"
    )
    await ctx.send(help_msg)

@stocks.command()
async def price(ctx, ticker: str):
    if ctx.channel.name != STOCKBOT_CHANNEL:
        return
    ticker = ticker.upper()
    try:
        stock = yf.Ticker(ticker)
        price = stock.info.get('regularMarketPrice')
        if price:
            await ctx.send(f"The current price of {ticker} is **${price}**")
        else:
            await ctx.send(f"Price info not available for {ticker}")
    except Exception:
        await ctx.send(f"Could not retrieve price for {ticker}")

@stocks.command()
async def summary(ctx, ticker: str):
    if ctx.channel.name != STOCKBOT_CHANNEL:
        return
    ticker = ticker.upper()
    try:
        stock = yf.Ticker(ticker)
        summary = stock.info.get('longBusinessSummary')
        if summary:
            await ctx.send(f"**{ticker} Summary:**\n{summary[:500]}...")
        else:
            await ctx.send(f"Summary not available for {ticker}")
    except Exception:
        await ctx.send(f"Could not retrieve summary for {ticker}")

@stocks.command()
async def stats(ctx, ticker: str):
    if ctx.channel.name != STOCKBOT_CHANNEL:
        return
    ticker = ticker.upper()
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        stats_msg = (
            f"**{ticker} Key Stats:**\n"
            f"Market Cap: {info.get('marketCap', 'N/A')}\n"
            f"PE Ratio (TTM): {info.get('trailingPE', 'N/A')}\n"
            f"Dividend Yield: {info.get('dividendYield', 'N/A')}\n"
            f"52 Week High: {info.get('fiftyTwoWeekHigh', 'N/A')}\n"
            f"52 Week Low: {info.get('fiftyTwoWeekLow', 'N/A')}\n"
            f"Volume: {info.get('volume', 'N/A')}\n"
        )
        await ctx.send(stats_msg)
    except Exception:
        await ctx.send(f"Could not retrieve stats for {ticker}")

@stocks.command()
async def history(ctx, ticker: str, days: int = 5):
    if ctx.channel.name != STOCKBOT_CHANNEL:
        return
    ticker = ticker.upper()
    try:
        end = datetime.now()
        start = end - timedelta(days=days*2)
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start, end=end)
        if hist.empty:
            await ctx.send(f"No historical data found for {ticker}")
            return
        
        msg = f"**{ticker} Closing Prices (last {days} trading days):**\n"
        count = 0
        for date, row in hist[::-1].iterrows():
            if count >= days:
                break
            date_str = date.strftime('%Y-%m-%d')
            close = row['Close']
            msg += f"{date_str}: ${close:.2f}\n"
            count += 1
        await ctx.send(msg)
    except Exception:
        await ctx.send(f"Could not retrieve historical data for {ticker}")

@stocks.command()
async def news(ctx, ticker: str):
    if ctx.channel.name != STOCKBOT_CHANNEL:
        return
    ticker = ticker.upper()
    try:
        stock = yf.Ticker(ticker)
        news_items = stock.news
        if not news_items:
            await ctx.send(f"No recent news found for {ticker}")
            return
        
        msg = f"**Latest News for {ticker}:**\n"
        for item in news_items[:3]:
            title = item.get('title')
            link = item.get('link')
            if title and link:
                msg += f"- [{title}]({link})\n"
        await ctx.send(msg)
    except Exception:
        await ctx.send(f"Could not retrieve news for {ticker}")

MEMES_FILE = "memes.json"

# Default memes (preset)
default_memes = [
    "https://i.imgur.com/W3b7QZQ.jpg",
]

# Load user memes from file
def load_memes():
    if os.path.exists(MEMES_FILE):
        with open(MEMES_FILE, "r") as f:
            return json.load(f)
    else:
        return []

# Save user memes to file
def save_memes(memes_list):
    with open(MEMES_FILE, "w") as f:
        json.dump(memes_list, f)

user_memes = load_memes()

@bot.command(name="resetmemes")
@commands.has_permissions(administrator=True)  # Only admins can reset
async def reset_memes(ctx):
    global user_memes
    user_memes = []
    save_memes(user_memes)
    await ctx.send("✅ Memes have been reset to default!")


@bot.command(name="submitmeme")
async def submit_meme(ctx, *, meme: str):
    if ctx.channel.name != "🤣memes":
        return  # Only allow submissions in memes channel

    # Add to user memes and save
    user_memes.append(meme)
    save_memes(user_memes)
    await ctx.send(f"Thanks for submitting your meme, {ctx.author.mention}! 🎉")

@bot.command(name="again")
async def again(ctx):
    if ctx.channel.name != "🤣memes":
        return  # Only respond in memes channel

    all_memes = default_memes + user_memes
    if not all_memes:
        await ctx.send("No memes available yet! Submit some with `!submitmeme <url or text>`.")
        return

    meme = random.choice(all_memes)
    await ctx.send(meme)


CROWNS_FILE = "crowns.json"

def save_crowns():
    with open(CROWNS_FILE, "w") as f:
        json.dump(user_crowns, f)

def load_crowns():
    global user_crowns
    if os.path.exists(CROWNS_FILE):
        with open(CROWNS_FILE, "r") as f:
            user_crowns = json.load(f)
            # keys in JSON are strings, convert to int keys
            user_crowns = {int(k): v for k, v in user_crowns.items()}
            save_crowns()
    else:
        user_crowns = {}

DAILY_REWARD_CHANNEL = "🥇daily-reward"
user_crowns = {}  # Simple in-memory dict: user_id -> crowns
user_first_try_done = set()  # Track users who have already had their guaranteed win

@bot.group(name='games', invoke_without_command=True)
async def games(ctx):
    if ctx.channel.name != DAILY_REWARD_CHANNEL:
        return  # Only respond in daily-reward channel
    await ctx.send("Games commands: !games guess")

@games.command()
async def guess(ctx, guess: int = None):
    if ctx.channel.name != DAILY_REWARD_CHANNEL:
        return

    user_id = ctx.author.id

    # Check if user already played (first_try_done means played)
    if user_id not in user_first_try_done:
        # First time playing, give 100 crowns just for playing
        user_crowns[user_id] = user_crowns.get(user_id, 0) + 100
        save_crowns()
        await ctx.send(f"{ctx.author.mention}, you earned **100 crowns** just for playing! Your total crowns: **{user_crowns[user_id]}**")
    else:
        # Already played, no playing bonus
        await ctx.send(f"{ctx.author.mention}, you have already played today! No bonus crowns.")

    if guess is None:
        await ctx.send("Please provide your guess like this: `!games guess <number>`")
        return

    number = 7  # fixed number for demo

    # First guess is always correct and gives 1000 crowns
    if user_id not in user_first_try_done and guess == number:
        user_first_try_done.add(user_id)
        user_crowns[user_id] += 1000
        save_crowns()
        await ctx.send(f"🎉 Correct! You guessed it on your first try! You earned **1000 crowns**! Your total crowns: **{user_crowns[user_id]}**")
        return

    # If user has already played before, just check guess normally
    if guess == number:
        user_crowns[user_id] += 1000
        save_crowns()
        await ctx.send(f"🎉 Correct! You earned **1000 crowns**! Your total crowns: **{user_crowns[user_id]}**")
    else:
        await ctx.send(f"❌ Nope, the number was {number}. Try again later!")


###----Market Commands---###

# Assuming you have this from your previous code
user_crowns = {}  # user_id -> crowns dictionary

# Store items example
store_items = {
    "Peasant's Hat": 300,
    "Royal Crown": 1500,
    "Knight's Shield": 1000,
    "Wizard's Wand": 2000,
    "Emperor's Sword": 5000,    
    "Queen's Chair": 25000,  
}

class StoreView(View):
    def __init__(self, user_id):
        super().__init__(timeout=60)  # buttons active for 60 seconds
        self.user_id = user_id

        # Create a button for each store item
        for item_name, price in store_items.items():
            self.add_item(StoreButton(label=item_name, price=price))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Only allow the original user to click buttons
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This store session is not for you!", ephemeral=True)
            return False
        return True

class StoreButton(Button):
    def __init__(self, label, price):
        super().__init__(label=f"{label} - {price} crowns", style=discord.ButtonStyle.primary)
        self.price = price
        self.item_name = label

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        balance = user_crowns.get(user_id, 0)

        if balance >= self.price:
            user_crowns[user_id] = balance - self.price
            await interaction.response.send_message(
                f"🎉 You bought **{self.item_name}** for {self.price} crowns! "
                f"Remaining balance: {user_crowns[user_id]} crowns.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"❌ You don't have enough crowns to buy **{self.item_name}**. "
                f"Your balance: {balance} crowns.",
                ephemeral=True
            )

@bot.command(name="store")
async def store(ctx):
    user_id = ctx.author.id
    balance = user_crowns.get(user_id, 0)
    description = "\n".join([f"**{item}** — {price} crowns" for item, price in store_items.items()])

    embed = discord.Embed(
        title="👑 King Store",
        description=description + f"\n\nYour balance: **{balance} crowns**",
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed, view=StoreView(user_id))

@bot.command(name="balance")
async def balance(ctx):
    user_id = ctx.author.id
    balance = user_crowns.get(user_id, 0)
    await ctx.send(f"{ctx.author.mention}, you have **{balance} crowns**.")


# ----- EVENT: Welcome new members -----
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name='announcements')
    if channel:
        await channel.send(f"Welcome {member.mention} to the server! 🎉")

#
load_crowns()

# Run the bot
bot.run(TOKEN)
