import os
import io
import random
import logging
from typing import List, Tuple, Literal

import discord
from discord import app_commands
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# ----- Configuration -----
MAX_PREDICTIONS_PER_REQUEST = 200
DEFAULT_DIGITS = 3

# Prediction table (ping -> 6 prediction methods)
PREDICTIONS: dict[int, Tuple[float, float, float, float, float, float]] = {
    1: (0.038, 0.0261, 0.0212, 0.1004444444, 0.1005006833, 0.101),
    10: (0.047, 0.036, 0.032, 0.1044444444, 0.1050683333, 0.11),
    20: (0.057, 0.047, 0.044, 0.1088888889, 0.1102733333, 0.12),
    30: (0.067, 0.058, 0.056, 0.1133333333, 0.115615, 0.13),
    40: (0.077, 0.069, 0.068, 0.1177777778, 0.1210933333, 0.14),
    50: (0.087, 0.080, 0.085, 0.1222222222, 0.1267083333, 0.15),
    60: (0.097, 0.091, 0.096, 0.1266666667, 0.13246, 0.16),
    70: (0.107, 0.102, 0.107, 0.1311111111, 0.1383483333, 0.17),
    80: (0.117, 0.113, 0.118, 0.1355555556, 0.1443733333, 0.18),
    90: (0.127, 0.124, 0.129, 0.14, 0.150535, 0.19),
    100: (0.137, 0.135, 0.145, 0.1444444444, 0.1568333333, 0.2),
    110: (0.147, 0.146, 0.1555, 0.1488888889, 0.1632683333, 0.21),
    120: (0.157, 0.157, 0.166, 0.1533333333, 0.16984, 0.22),
    130: (0.163, 0.168, 0.1765, 0.1577777778, 0.1765483333, 0.23),
    140: (0.173, 0.179, 0.187, 0.1622222222, 0.1833933333, 0.24),
    150: (0.183, 0.19, 0.1975, 0.1666666667, 0.190375, 0.25),
    160: (0.193, 0.201, 0.208, 0.1711111111, 0.1974933333, 0.26),
    170: (0.203, 0.212, 0.2185, 0.1755555556, 0.2047483333, 0.27),
    180: (0.213, 0.223, 0.229, 0.18, 0.21214, 0.28),
    190: (0.223, 0.234, 0.2395, 0.1844444444, 0.2196683333, 0.29),
    200: (0.233, 0.245, 0.25, 0.1888888889, 0.2273333333, 0.3),
    210: (0.243, 0.256, 0.2605, 0.1933333333, 0.235135, 0.31),
    220: (0.253, 0.267, 0.271, 0.1977777778, 0.2430733333, 0.32),
    230: (0.263, 0.278, 0.2815, 0.2022222222, 0.2511483333, 0.33),
    240: (0.273, 0.289, 0.292, 0.2066666667, 0.25936, 0.34),
    250: (0.283, 0.3, 0.3025, 0.2111111111, 0.2677083333, 0.35),
}

# Close/mid/far multipliers
MULTIPLIERS: dict[str, float] = {
    "close": 0.985,
    "mid": 1.0,
    "far": 1.015,
}

# 2-tap multiplier
TWO_TAP = 1.0025

# Optional fine-tuning by type/mode (kept subtle so original math stays primary)
TYPE_ADJUST: dict[str, float] = {
    "blatant": 1.000,
    "hvh": 0.998,
}

MODE_ADJUST: dict[str, float] = {
    "camlock": 1.000,
    "targetaim": 1.001,
}


def clamp(value: int, min_value: int, max_value: int) -> int:
    return max(min_value, min(value, max_value))


def parse_ping_input(ping_input: str, count: int) -> List[int]:
    """Parse single ping like "100" or range like "50-150" (whitespace tolerated)."""
    text = ping_input.strip()
    if "-" in text:
        try:
            left, right = [int(part.strip()) for part in text.split("-", 1)]
        except ValueError:
            raise ValueError("Ping range must be like 50-150")
        if left < 0 or right < 0:
            raise ValueError("Ping cannot be negative")
        if left > right:
            left, right = right, left
        # Sample with replacement (uniform)
        return [random.randint(left, right) for _ in range(count)]
    else:
        try:
            single = int(text)
        except ValueError:
            raise ValueError("Ping must be an integer or a range like 50-150")
        if single < 0:
            raise ValueError("Ping cannot be negative")
        return [single for _ in range(count)]


def calc_final_prediction(
    ping: int,
    digits: int,
    starterdigit: float,
    distance: Literal["close", "mid", "far"] = "mid",
    pred_type: Literal["blatant", "hvh"] = "blatant",
    mode: Literal["camlock", "targetaim"] = "camlock",
) -> float:
    # Find closest ping in table
    closest_ping = min(PREDICTIONS.keys(), key=lambda k: abs(k - ping))
    regular, linear, stepwise, fraction, complex_p, slope = PREDICTIONS[closest_ping]

    # Combine all prediction methods
    combined = (regular + linear + stepwise + fraction + complex_p + slope) / 6

    # Apply distance multiplier (close/mid/far) & 2-tap and subtle type/mode adjusters
    combined *= MULTIPLIERS[distance]
    combined *= TWO_TAP
    combined *= TYPE_ADJUST.get(pred_type, 1.0)
    combined *= MODE_ADJUST.get(mode, 1.0)

    # Scale from starterdigit
    final_value = starterdigit * (1 + combined)
    return round(final_value, digits)


def generate_predictions(
    ping_input: str,
    digits: int,
    starterdigit: float,
    count: int,
    xy: bool,
    distance: Literal["close", "mid", "far"],
    pred_type: Literal["blatant", "hvh"],
    mode: Literal["camlock", "targetaim"],
) -> List[float] | List[Tuple[float, float]]:
    pings = parse_ping_input(ping_input, count)
    results: List[float] | List[Tuple[float, float]] = []

    for p in pings:
        if xy:
            x_pred = calc_final_prediction(p, digits, starterdigit, distance, pred_type, mode)
            y_pred = calc_final_prediction(p, digits, starterdigit * 0.75, distance, pred_type, mode)
            results.append((x_pred, y_pred))
        else:
            pred = calc_final_prediction(p, digits, starterdigit, distance, pred_type, mode)
            results.append(pred)

    return results


class PredictionClient(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        # Global sync; for faster iteration, set a GUILD_ID to sync per-guild instead
        guild_id = os.getenv("GUILD_ID")
        if guild_id and guild_id.isdigit():
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

    async def on_ready(self) -> None:
        logging.info("Logged in as %s (ID: %s)", self.user, getattr(self.user, "id", "?"))


client = PredictionClient()


# Rate-limit to avoid spam: 1 use per 2 seconds per user
@app_commands.checks.cooldown(1, 2.0, key=lambda i: i.user.id)
@client.tree.command(name="generate", description="Generate DaHood/FakeDaHood predictions")
@app_commands.describe(
    ping="Single ping or range (e.g., 50 or 50-150)",
    pred_type="blatant or hvh",
    mode="camlock or targetaim",
    digits="How many digits in final prediction (0-6 typical)",
    starterdigit="Starter digit",
    count="How many predictions to generate (max 200)",
    xy="true for X/Y predictions, false otherwise",
    distance="Distance multiplier to apply",
)
async def generate(
    interaction: discord.Interaction,
    ping: str,
    pred_type: Literal["blatant", "hvh"],
    mode: Literal["camlock", "targetaim"],
    digits: app_commands.Range[int, 0, 10],
    starterdigit: app_commands.Range[float, 0.0, 10_000.0],
    count: app_commands.Range[int, 1, MAX_PREDICTIONS_PER_REQUEST],
    xy: bool,
    distance: Literal["close", "mid", "far"] = "mid",
) -> None:
    # Defer to give us time, keep reply hidden
    await interaction.response.defer(ephemeral=True)

    # Clamp digits just in case
    digits = clamp(digits, 0, 10)

    try:
        preds = generate_predictions(
            ping_input=ping,
            digits=digits,
            starterdigit=starterdigit,
            count=count,
            xy=xy,
            distance=distance,
            pred_type=pred_type,
            mode=mode,
        )
    except ValueError as exc:
        await interaction.followup.send(f"❌ {exc}", ephemeral=True)
        return

    # Build output text
    lines: List[str] = []
    lines.append(f"Generated {count} predictions")
    lines.append(f"Type: {pred_type}")
    lines.append(f"Mode: {mode}")
    lines.append(f"Distance: {distance}")
    lines.append("---")
    if xy:
        lines.append("Predictions (X / Y):")
        for x, y in preds:  # type: ignore[assignment]
            lines.append(f"X: {x}\tY: {y}")
    else:
        lines.append("Predictions:")
        for pred in preds:  # type: ignore[assignment]
            lines.append(str(pred))

    content = "\n".join(lines)
    file = discord.File(io.BytesIO(content.encode("utf-8")), filename="predictions.txt")

    # Try DM first; fall back to ephemeral file if DM blocked
    try:
        await interaction.user.send(content=interaction.user.mention, file=file)
        await interaction.followup.send("✅ Predictions generated and sent to your DMs", ephemeral=True)
    except discord.Forbidden:
        # Rebuild file object, as File/BytesIO may be consumed by the prior attempt
        file2 = discord.File(io.BytesIO(content.encode("utf-8")), filename="predictions.txt")
        await interaction.followup.send(
            content=(
                "⚠️ I couldn't DM you (DMs disabled). "
                "Here's your file instead."
            ),
            file=file2,
            ephemeral=True,
        )


@generate.error
async def on_generate_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"⏳ Slow down. Try again in {error.retry_after:.1f}s.", ephemeral=True
        )
    else:
        logging.exception("Unhandled error in /generate: %s", error)
        try:
            await interaction.response.send_message("❌ An unexpected error occurred.", ephemeral=True)
        except discord.InteractionResponded:
            await interaction.followup.send("❌ An unexpected error occurred.", ephemeral=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise SystemExit(
            "Missing DISCORD_TOKEN environment variable. "
            "Create a bot at https://discord.com/developers, then set DISCORD_TOKEN, "
            "or create a .env file with DISCORD_TOKEN=your_token_here."
        )
    client.run(token)