# Predictor Bot (Generic Target-Leading Math)

This is a generic, non-game-specific Discord bot that computes target-leading predictions for moving targets with constant velocity. It is intended for educational and training purposes in custom, non-competitive projects.

- Supports 2D and 3D calculations without gravity
- Computes time-to-intercept, predicted intercept point, aim unit vector, and lead displacement
- Does not integrate with or target any live game

## Quick start

1. Create a virtual environment (optional but recommended):

```
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```
pip install -r requirements.txt
```

3. Configure environment:

- Copy `.env.example` to `.env`
- Put your Discord bot token into `DISCORD_TOKEN`

4. Run the bot:

```
python -m src.bot
```

## Commands

- `!predict2d xs ys xt yt vtx vty speed [vsx vsy]`
  - `xs, ys`: shooter position
  - `xt, yt`: target position
  - `vtx, vty`: target velocity
  - `speed`: projectile speed (positive)
  - `vsx, vsy` (optional): shooter velocity (for relative motion correction)

- `!predict3d xs ys zs xt yt zt vtx vty vtz speed [vsx vsy vsz]`
  - Same semantics in 3D

Units are arbitrary but must be consistent (e.g., meters and meters/second).

## Notes

- Gravity is not modeled in these commands. For ballistic arcs, you need additional physics and constraints.
- If there is no valid positive intercept time based on the inputs, the bot will report that no solution exists.
- This bot is for learning and custom projects. Do not use it to violate terms of service of any platform.