# Discord Prediction Bot

Improved, safer Discord bot that generates DaHood/FakeDaHood predictions via a slash command.

## Setup
1. Python 3.10+
2. Install dependencies:
   
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment:
   - Copy `.env.example` to `.env`, then set `DISCORD_TOKEN`.
   - Optional: set `GUILD_ID` to your development server ID for faster slash command sync.

## Run
```bash
python /workspace/bot.py
```

## Slash Command
- `/generate`
  - `ping`: "100" or range like "50-150"
  - `pred_type`: `blatant` or `hvh`
  - `mode`: `camlock` or `targetaim`
  - `digits`: 0-10
  - `starterdigit`: base value
  - `count`: up to 200
  - `xy`: whether to return X/Y pairs (Y uses 0.75x starterdigit)
  - `distance`: `close`, `mid`, or `far`

The bot DMs you a `predictions.txt`. If your DMs are closed, it returns the file ephemerally.

## Security
Never hardcode bot tokens. If your token was posted anywhere, reset it in the Discord Developer Portal and update `DISCORD_TOKEN`.