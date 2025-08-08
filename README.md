# Prediction Generator Discord Bot

A Python Discord bot that generates high-precision Da Hood/Fake Da Hood prediction values based on ping, mode, and type. It DM's the invoker a `predictions.txt` file.

## Requirements
- Python 3.10+
- A Discord Bot token

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create a `.env` file in the project root with:
   ```ini
   DISCORD_TOKEN=your_bot_token_here
   GUILD_ID=optional_single_guild_id_for_faster_command_sync
   ```

## Run
```bash
python -m bot
```

On first run the slash command is registered. If you set `GUILD_ID`, it registers instantly for that guild; otherwise global registration can take up to an hour.

## Slash Command
```
/generate ping: <number|range like 50-150> \
          type: <blatant|hvh> \
          mode: <camlock|targetaim> \
          digits: <int> \
          starterdigit: <float> \
          count: <int> \
          xy: <true|false>
```

Examples:
- Single axis:
  ```
  /generate 50-150 blatant targetaim 11 0.137 10 false
  ```
- X/Y pair:
  ```
  /generate 50-150 blatant targetaim 11 0.137 10 true
  ```

The bot DM's you `predictions.txt` with content like:
```
Generated 10 predictions
Mode: blatant
---
┌ Predictions:
├ 0.13712345678
├ ...
└ 0.13787654321
```

For `xy: true` it lists X and Y separately.