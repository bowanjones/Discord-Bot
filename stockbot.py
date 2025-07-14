import os
import discord
from discord.ext import commands
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()

# 1️⃣  Discord intents – message content must be enabled to read raw text
intents = discord.Intents.default()
intents.message_content = True

# 2️⃣  Create the bot
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"✅  Logged in as {bot.user} (id={bot.user.id})")

# 3️⃣  Command: !price <TICKER>
@bot.command(name="price", aliases=["p"])
async def price(ctx, symbol: str):
    symbol = symbol.upper().strip()

    try:
        ticker = yf.Ticker(symbol)

        # Prefer fast_info → lastPrice (changes quickly, ~15‑min delay for US stocks)
        price = ticker.fast_info.get("lastPrice")
        if price is None:
            # Fallback: grab the most recent close from the 1‑minute candle
            price = (
                ticker.history(period="1d", interval="1m")["Close"]
                .dropna()
                .iloc[-1]
            )

        await ctx.send(f"**{symbol}** → ${price:,.2f}")
    except Exception as e:
        await ctx.send(f"⚠️  Couldn’t fetch data for `{symbol}`. ({e})")

# 4️⃣  Run the bot (expects DISCORD_TOKEN in env vars)
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("Set DISCORD_TOKEN as an environment variable!")
    bot.run(token)
