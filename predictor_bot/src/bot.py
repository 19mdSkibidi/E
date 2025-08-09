import os
import sys
from typing import Optional

from dotenv import load_dotenv

try:
    import discord
    from discord.ext import commands
except Exception as e:  # pragma: no cover - handled at runtime
    print("discord.py is required. Install via `pip install -r requirements.txt`.")
    raise

# Enable importing the local src package when running as a module
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from src.prediction import (
    Vector2,
    Vector3,
    predict_intercept_2d,
    predict_intercept_3d,
)


def format_float(value: float) -> str:
    return f"{value:.6g}"


def format_vec2(v: Vector2) -> str:
    return f"({format_float(v.x)}, {format_float(v.y)})"


def format_vec3(v: Vector3) -> str:
    return f"({format_float(v.x)}, {format_float(v.y)}, {format_float(v.z)})"


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN", "")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=commands.DefaultHelpCommand())


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (id={bot.user.id})")


@bot.command(name="predict2d")
async def predict2d(ctx: commands.Context, *args: str) -> None:
    """
    Usage: !predict2d xs ys xt yt vtx vty speed [vsx vsy]
    """
    try:
        if len(args) not in (7, 9):
            await ctx.reply("Usage: !predict2d xs ys xt yt vtx vty speed [vsx vsy]")
            return
        values = list(map(float, args))
        xs, ys, xt, yt, vtx, vty, speed = values[:7]
        shooter_vel_opt: Optional[Vector2] = None
        if len(values) == 9:
            shooter_vel_opt = Vector2(values[7], values[8])

        res = predict_intercept_2d(
            shooter_position=Vector2(xs, ys),
            target_position=Vector2(xt, yt),
            target_velocity=Vector2(vtx, vty),
            projectile_speed=speed,
            shooter_velocity=shooter_vel_opt,
        )
        if res is None:
            await ctx.reply("No valid intercept (check inputs).")
            return

        t, intercept, aim_unit, distance = res
        reply = (
            "2D Intercept\n"
            f"time: {format_float(t)} s\n"
            f"intercept_point: {format_vec2(intercept)}\n"
            f"aim_unit: {format_vec2(aim_unit)}\n"
            f"distance: {format_float(distance)}"
        )
        await ctx.reply(reply)
    except Exception as e:
        await ctx.reply(f"Error: {e}")


@bot.command(name="predict3d")
async def predict3d(ctx: commands.Context, *args: str) -> None:
    """
    Usage: !predict3d xs ys zs xt yt zt vtx vty vtz speed [vsx vsy vsz]
    """
    try:
        if len(args) not in (10, 13):
            await ctx.reply("Usage: !predict3d xs ys zs xt yt zt vtx vty vtz speed [vsx vsy vsz]")
            return
        values = list(map(float, args))
        xs, ys, zs, xt, yt, zt, vtx, vty, vtz, speed = values[:10]
        shooter_vel_opt: Optional[Vector3] = None
        if len(values) == 13:
            shooter_vel_opt = Vector3(values[10], values[11], values[12])

        res = predict_intercept_3d(
            shooter_position=Vector3(xs, ys, zs),
            target_position=Vector3(xt, yt, zt),
            target_velocity=Vector3(vtx, vty, vtz),
            projectile_speed=speed,
            shooter_velocity=shooter_vel_opt,
        )
        if res is None:
            await ctx.reply("No valid intercept (check inputs).")
            return

        t, intercept, aim_unit, distance = res
        reply = (
            "3D Intercept\n"
            f"time: {format_float(t)} s\n"
            f"intercept_point: {format_vec3(intercept)}\n"
            f"aim_unit: {format_vec3(aim_unit)}\n"
            f"distance: {format_float(distance)}"
        )
        await ctx.reply(reply)
    except Exception as e:
        await ctx.reply(f"Error: {e}")


if __name__ == "__main__":
    if not TOKEN:
        print("Missing DISCORD_TOKEN in environment. Create a .env file or export the variable.")
        sys.exit(1)
    bot.run(TOKEN)