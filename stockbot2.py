import os
import logging
import discord
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType
import yfinance as yf
from dotenv import load_dotenv
import datetime
from keep_alive import keep_alive

# Replit stay awake
keep_alive()

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

# Command: !price <TICKER>
@bot.command(name="price", aliases=["p"])
@cooldown(rate=3, per=10, type=BucketType.user)
async def price(ctx, symbol: str):
    symbol = symbol.upper().strip()
    try:
        ticker = yf.Ticker(symbol)
        price = ticker.fast_info.get("lastPrice")
        if price is None:
            price = (
                ticker.history(period="1d", interval="1m")["Close"]
                .dropna()
                .iloc[-1]
            )
        await ctx.send(f"**{symbol}** → ${price:,.2f}")
    except Exception as e:
        logging.warning(f"[price] Error for {symbol}: {e}")
        await ctx.send(f"⚠️ Couldn’t fetch data for `{symbol}`.")

# Command: !info <TICKER>
@bot.command(name="info", aliases=["i"])
@cooldown(rate=3, per=10, type=BucketType.user)
async def info(ctx, symbol: str):
    symbol = symbol.upper().strip()
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        name = info.get("shortName", "N/A")
        sector = info.get("sector", "N/A")
        market_cap = info.get("marketCap", 0)
        currency = info.get("currency", "USD")

        await ctx.send(
            f"📘 **{name}** ({symbol})\nSector: {sector}\nMarket Cap: ${market_cap:,} {currency}"
        )
    except Exception as e:
        logging.warning(f"[info] Error for {symbol}: {e}")
        await ctx.send(f"⚠️ Couldn’t fetch company info for `{symbol}`.")

# Command: !volume <TICKER>
@bot.command(name="volume", aliases=["v"])
@cooldown(rate=3, per=10, type=BucketType.user)
async def volume(ctx, symbol: str):
    symbol = symbol.upper().strip()
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        vol = info.get("volume", 0)
        avg_vol = info.get("averageVolume", 0)

        await ctx.send(
            f"📊 **{symbol}** Volume: {vol:,} (Avg: {avg_vol:,})"
        )
    except Exception as e:
        logging.warning(f"[volume] Error for {symbol}: {e}")
        await ctx.send(f"⚠️ Couldn’t fetch volume data for `{symbol}`.")

# Command: !chart <TICKER>
@bot.command(name="chart", aliases=["c"])
@cooldown(rate=3, per=10, type=BucketType.user)
async def chart(ctx, symbol: str):
    symbol = symbol.upper().strip()
    url = f"https://finance.yahoo.com/quote/{symbol}"
    await ctx.send(f"📈 Chart for **{symbol}**: {url}")

# Command: !rating <TICKER>
@bot.command(name="rating", aliases=["r"])
@cooldown(rate=3, per=10, type=BucketType.user)
async def rating(ctx, symbol: str):
    symbol = symbol.upper().strip()
    try:
        ticker = yf.Ticker(symbol)

        info = ticker.info
        mean = info.get("recommendationMean")
        key = info.get("recommendationKey")

        recs = ticker.recommendations
        latest = recs.tail(1).iloc[0] if recs is not None and not recs.empty else None

        msg = f"🧠 **{symbol}** Analyst Summary:\n"

        if key:
            msg += f"• Consensus: **{key.title()}**"
            if mean:
                msg += f" (Mean: {mean:.2f})\n"
            else:
                msg += "\n"
        else:
            msg += "• No consensus rating available\n"

        if latest is not None:
            firm = latest.get("Firm", "Unknown")
            to_grade = latest.get("To Grade", "N/A")

            # Fix: avoid crashing if .name is not a datetime
            date_raw = latest.name
            if isinstance(date_raw, (datetime.datetime, datetime.date)):
                date = date_raw.strftime("%Y-%m-%d")
            else:
                date = "Unknown"

            msg += f"• Latest Rating: `{firm}` → **{to_grade}** on {date}"
        else:
            msg += "• No individual analyst actions found."

        await ctx.send(msg)

    except Exception as e:
        logging.warning(f"[rating] Error for {symbol}: {e}")
        await ctx.send(f"⚠️ Couldn’t fetch analyst rating for `{symbol}`.")

# Command: !rsi <TICKER>
@bot.command(name="rsi")
@cooldown(rate=3, per=10, type=BucketType.user)
async def rsi(ctx, symbol: str):
    symbol = symbol.upper().strip()
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1mo", interval="1d")

        if data.empty or "Close" not in data:
            await ctx.send(f"⚠️ Not enough data to calculate RSI for `{symbol}`.")
            return

        close = data["Close"]

        # RSI calculation (14-day)
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        latest_rsi = rsi.dropna().iloc[-1]

        emoji = "🟢" if latest_rsi < 30 else "🔴" if latest_rsi > 70 else "🟡"
        await ctx.send(f"{emoji} **{symbol} RSI (14-day)**: {latest_rsi:.2f}")
    except Exception as e:
        logging.warning(f"[rsi] Error for {symbol}: {e}")
        await ctx.send(f"⚠️ Couldn’t calculate RSI for `{symbol}`.")

# Command: !summary <TICKER>
@bot.command(name="summary", aliases=["s"])
@cooldown(rate=3, per=10, type=BucketType.user)
async def summary(ctx, symbol: str):
    symbol = symbol.upper().strip()
    try:
        ticker = yf.Ticker(symbol)
        price = ticker.fast_info.get("lastPrice")
        info = ticker.info
        key = info.get("recommendationKey", "N/A").title()
        rsi_data = ticker.history(period="1mo", interval="1d")["Close"]
        rsi_val = None

        if not rsi_data.empty:
            delta = rsi_data.diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            rsi_val = 100 - (100 / (1 + rs)).dropna().iloc[-1]

        msg = f"📊 **{symbol}** Summary:\n"
        if price: msg += f"• Price: ${price:,.2f}\n"
        msg += f"• Rating: {key}\n"
        if rsi_val: msg += f"• RSI (14): {rsi_val:.2f}"

        await ctx.send(msg)
    except Exception as e:
        logging.warning(f"[summary] Error for {symbol}: {e}")
        await ctx.send(f"⚠️ Couldn't fetch summary for `{symbol}`.")

# Command: !movingavg <TICKER>
@bot.command(name="movingavg", aliases=["ma"])
@cooldown(rate=3, per=10, type=BucketType.user)
async def movingavg(ctx, symbol: str):
    symbol = symbol.upper().strip()
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1y", interval="1d")

        if data.empty or "Close" not in data:
            await ctx.send(f"⚠️ Not enough data to calculate moving averages for `{symbol}`.")
            return

        close = data["Close"]

        ma_50 = close.rolling(window=50).mean().dropna().iloc[-1]
        ma_200 = close.rolling(window=200).mean().dropna().iloc[-1]

        trend = "📈 Uptrend" if ma_50 > ma_200 else "📉 Downtrend"

        await ctx.send(
            f"🧮 **{symbol} Moving Averages**\n"
            f"• 50-Day: ${ma_50:,.2f}\n"
            f"• 200-Day: ${ma_200:,.2f}\n"
            f"{trend} (50 vs. 200)"
        )
    except Exception as e:
        logging.warning(f"[movingavg] Error for {symbol}: {e}")
        await ctx.send(f"⚠️ Couldn’t calculate moving averages for `{symbol}`.")

# Command: !news <TICKER>
@bot.command(name="news", aliases=["n"])
@cooldown(rate=3, per=10, type=BucketType.user)
async def news(ctx, symbol: str):
    symbol = symbol.upper().strip()
    try:
        ticker = yf.Ticker(symbol)
        news_items = ticker.news[:3]  # top 3 items
        if not news_items:
            await ctx.send(f"📰 No news found for `{symbol}`.")
            return

        msg = f"🗞️ **{symbol} Latest News**\n"
        for item in news_items:
            msg += f"• [{item['title']}]({item['link']})\n"
        await ctx.send(msg)
    except Exception as e:
        logging.warning(f"[news] Error for {symbol}: {e}")
        await ctx.send(f"⚠️ Couldn't fetch news for `{symbol}`.")

@bot.command(name="action", aliases=["a"])
@cooldown(rate=3, per=10, type=BucketType.user)
async def should_i_buy(ctx, symbol: str):
    symbol = symbol.upper().strip()
    try:
        ticker = yf.Ticker(symbol)

        # Use 1 year of daily data for all calculations
        hist = ticker.history(period="1y", interval="1d")
        if hist.empty or "Close" not in hist:
            await ctx.send(f"⚠️ Not enough data to analyze `{symbol}`.")
            return

        close = hist["Close"]

        # Current price
        current_price = close.iloc[-1]

        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        latest_rsi = rsi.dropna()
        if latest_rsi.empty:
            await ctx.send(f"⚠️ Not enough RSI data for `{symbol}`.")
            return
        latest_rsi = latest_rsi.iloc[-1]

        # Moving Averages
        ma_50_series = close.rolling(window=50).mean().dropna()
        ma_200_series = close.rolling(window=200).mean().dropna()
        if ma_50_series.empty or ma_200_series.empty:
            await ctx.send(f"⚠️ Not enough data for moving averages on `{symbol}`.")
            return
        ma_50 = ma_50_series.iloc[-1]
        ma_200 = ma_200_series.iloc[-1]

        # Analyst Recommendation
        try:
            info = ticker.info
            recommendation = info.get("recommendationKey", "N/A").lower()
        except Exception as info_error:
            logging.warning(f"[info error] {symbol}: {info_error}")
            recommendation = "N/A"

        # Score
        score = 0
        reasons = []

        # Price confirms trend
        if current_price > ma_50 and ma_50 > ma_200:
            score += 1
            reasons.append("🟢 Price > 50-day > 200-day → Confirmed uptrend")
        elif current_price < ma_50 and ma_50 < ma_200:
            score -= 1
            reasons.append("🔴 Price < 50-day < 200-day → Confirmed downtrend")
        else:
            reasons.append("🔁 Price and MAs not aligned (neutral trend)")

        # RSI
        if latest_rsi < 30:
            score += 1
            reasons.append(f"📉 RSI {latest_rsi:.2f} < 30 → Oversold")
        elif latest_rsi > 70:
            score -= 1
            reasons.append(f"📈 RSI {latest_rsi:.2f} > 70 → Overbought")
        else:
            reasons.append(f"🔁 RSI {latest_rsi:.2f} → Neutral")

        # Analyst recommendation
        if recommendation in ["buy", "strong buy"]:
            score += 1
            reasons.append(f"✅ Analyst rating: {recommendation.title()}")
        elif recommendation in ["sell", "strong sell"]:
            score -= 1
            reasons.append(f"⚠️ Analyst rating: {recommendation.title()}")
        else:
            reasons.append(f"❔ Analyst rating: {recommendation.title()}")

        # Final verdict based on score
        if score >= 3:
            verdict = "🟢 Recommendation: **BUY**"
        elif score == 2:
            verdict = "🔵 Recommendation: **WATCH TO BUY**"
        elif score == -1:
            verdict = "🟠 Recommendation: **WATCH TO SELL**"
        elif score <= -2:
            verdict = "🔴 Recommendation: **SELL**"
        else:
            verdict = "🟡 Recommendation: **HOLD / WAIT**"

        # Output
        msg = (
            f"🤔 **Should You Buy `{symbol}`?**\n"
            f"💲 Current Price: `${current_price:,.2f}`\n\n"
            + "\n".join(reasons)
            + f"\n\n{verdict}"
            + f"\n⚠️ This is not financial advice. Use your own judgment or consult a professional."
        )

        await ctx.send(msg)

    except Exception as e:
        logging.warning(f"[action] Error for {symbol}: {e}")
        await ctx.send(f"⚠️ Couldn’t analyze `{symbol}`.")


# Comand: !whoami 
@bot.command(name="whoami", aliases=["w"])
async def ping(ctx):
    author = ctx.author.nick
    guild = ctx.guild
    channel = ctx.channel.name
    channel_id = ctx.channel.id
    await ctx.send(f"{author} has made a change in {channel} in {guild}. channel_id:{channel_id}")


# Command: !help or !commands
@bot.command(name="help", aliases=["commands", "h"])
async def help_command(ctx):
    help_text = """
📌 **Available Commands**
`!price <TICKER>` (p) — Get the latest stock price  
`!info <TICKER>` (i) — Company overview  
`!volume <TICKER>` (v) — Current & average volume  
`!chart <TICKER>` (c) — Link to Yahoo Finance chart  
`!rating <TICKER>` (r) — Latest analyst rating
`!rsi <TICKER>` (rsi lol) — Show the latest RSI 
`!summary <TICKER>` (s) — Price + Rating + RSI
`!movingavg <TICKER>` (ma) — Returns Moving Average 50 and 200 day
`!news <TICKER>` (n) — Returns top 3 news articles
`!action <TICKER>` (a) — Responds with what to do
`!whoami <TICKER>` (w) — Responds with where I am
`!help` (h) — Show this command list
"""
    await ctx.send(help_text)


# Run the bot
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("Set DISCORD_TOKEN as an environment variable!")
    bot.run(token)
