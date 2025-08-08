from __future__ import annotations

import io
import os
import random
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from bot.predictions import (
    generate_single_prediction,
    generate_xy_prediction,
    parse_ping,
    format_file_content,
)


INTENTS = discord.Intents.none()
INTENTS.messages = True
INTENTS.dm_messages = True
INTENTS.guilds = True


def _get_tree_sync_guild() -> Optional[discord.Object]:
    guild_id = os.getenv("GUILD_ID")
    if guild_id:
        try:
            return discord.Object(id=int(guild_id))
        except ValueError:
            return None
    return None


class PredictionClient(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix=commands.when_mentioned_or("!"), intents=INTENTS)
        self.synced = False

    async def setup_hook(self) -> None:
        guild_obj = _get_tree_sync_guild()
        if guild_obj:
            self.tree.copy_global_to(guild=guild_obj)
            await self.tree.sync(guild=guild_obj)
        else:
            # Fallback: register globally (may take a while)
            await self.tree.sync()


bot = PredictionClient()


PING_DESC = "Single ping like 50 or range like 50-150"
TYPE_DESC = "Type of playstyle: blatant or hvh"
MODE_DESC = "Mode: camlock or targetaim"
DIGITS_DESC = "Number of digits after decimal for output"
STARTER_DESC = "Starter digits (decimal prefix), e.g. 0.137"
COUNT_DESC = "How many predictions to generate"
XY_DESC = "Generate X and Y predictions (true/false)"


@bot.tree.command(name="generate", description="Generate Da Hood predictions and DM as a text file")
@app_commands.describe(
    ping=PING_DESC,
    type=TYPE_DESC,
    mode=MODE_DESC,
    digits=DIGITS_DESC,
    starterdigit=STARTER_DESC,
    count=COUNT_DESC,
    xy=XY_DESC,
)
@app_commands.choices(
    type=[
        app_commands.Choice(name="blatant", value="blatant"),
        app_commands.Choice(name="hvh", value="hvh"),
    ],
    mode=[
        app_commands.Choice(name="camlock", value="camlock"),
        app_commands.Choice(name="targetaim", value="targetaim"),
    ],
    xy=[
        app_commands.Choice(name="false", value="false"),
        app_commands.Choice(name="true", value="true"),
    ],
)
async def generate(
    interaction: discord.Interaction,
    ping: str,
    type: app_commands.Choice[str],
    mode: app_commands.Choice[str],
    digits: int,
    starterdigit: float,
    count: int,
    xy: app_commands.Choice[str],
):
    await interaction.response.defer(ephemeral=True)

    # Validate
    digits = max(0, min(16, digits))
    count = max(1, min(500, count))
    type_val = type.value
    mode_val = mode.value
    xy_flag = (xy.value == "true")

    # Seed RNG per request for reproducibility across a DM send
    seed = random.randrange(1 << 30)
    rng = random.Random(seed)

    avg_ping, lo_ping, hi_ping, is_range = parse_ping(ping, rng)

    predictions = []
    if not xy_flag:
        for _ in range(count):
            current_ping = random.uniform(lo_ping, hi_ping) if is_range else avg_ping
            val = generate_single_prediction(
                ping_ms=current_ping,
                type_=type_val,
                mode=mode_val,
                digits=digits,
                starterdigit=starterdigit,
                rng=rng,
            )
            predictions.append(val)
    else:
        for _ in range(count):
            current_ping = random.uniform(lo_ping, hi_ping) if is_range else avg_ping
            x, y = generate_xy_prediction(
                ping_ms=current_ping,
                type_=type_val,
                mode=mode_val,
                digits=digits,
                starterdigit=starterdigit,
                rng=rng,
            )
            predictions.append((x, y))

    file_text = format_file_content(count, type_val, xy_flag, predictions)

    # Create file in memory
    file_bytes = io.BytesIO(file_text.encode("utf-8"))
    discord_file = discord.File(fp=file_bytes, filename="predictions.txt")

    # DM the invoker and ping them in DM content
    try:
        user = interaction.user
        dm = await user.create_dm()
        mention = user.mention
        header = f"{mention}"
        await dm.send(content=header, file=discord_file)
    except Exception as e:
        await interaction.followup.send(
            f"Couldn't DM you (check privacy settings). Error: {e}", ephemeral=True
        )
        return

    await interaction.followup.send("DM sent with predictions.txt", ephemeral=True)


@bot.tree.command(name="deploy", description="Force-sync slash commands")
async def deploy(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild_obj = _get_tree_sync_guild()
    if guild_obj:
        bot.tree.copy_global_to(guild=guild_obj)
        await bot.tree.sync(guild=guild_obj)
        await interaction.followup.send("Commands synced to guild.", ephemeral=True)
    else:
        await bot.tree.sync()
        await interaction.followup.send("Commands synced globally (may take time).", ephemeral=True)


def run_bot() -> None:
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN missing from environment or .env")
    bot.run(token)