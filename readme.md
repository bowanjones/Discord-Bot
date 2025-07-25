# 🤖 Discord Bot Setup Guide

## Step 1: Create a Discord Application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click **"New Application"**.
3. Give your application a name.
4. In the left sidebar, navigate to **"Bot"**.
5. Click **"Reset Token"** and copy the token.  
   > ⚠️ Keep this token safe! Do not share it publicly.
6. Set bot permissions:
   - ✅ Send Messages  
   - ✅ Read Message History  
   - ✅ View Channels  
   - (Add more based on your bot's functionality)

---

## Step 2: Invite the Bot to Your Server

1. In the left sidebar, go to **OAuth2 > URL Generator**.
2. Under **Scopes**, select:
   - `bot`
3. Under **Bot Permissions**, select the same permissions as above.
4. Copy the **generated URL** and open it in your browser.
5. Choose your server and click **Authorize**.

---

## Step 3: Set Up the Project

### Install Required Packages

```bash
pip install discord.py==2.3.2 yfinance python-dotenv watchdog
```

### Create a .env File
```bash
DISCORD_BOT_TOKEN=your_token_here
```

### Run the Project
```bash
python bot.py
```

### If Running Doesn't Work
1. Install a virtual environment
python -m venv venv
2. Activate the environment
.\venv\Scripts\Activate.ps1

### Additional Resources
1. Context commands for discord:
https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.Context