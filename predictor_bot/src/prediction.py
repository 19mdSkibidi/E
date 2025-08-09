from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Optional, Tuple


@dataclass(frozen=True)
class Vector2:
    x: float
    y: float

    def add(self, other: "Vector2") -> "Vector2":
        return Vector2(self.x + other.x, self.y + other.y)

    def sub(self, other: "Vector2") -> "Vector2":
        return Vector2(self.x - other.x, self.y - other.y)

    def mul(self, scalar: float) -> "Vector2":
        return Vector2(self.x * scalar, self.y * scalar)

    def dot(self, other: "Vector2") -> float:
        return self.x * other.x + self.y * other.y

    def norm(self) -> float:
        return sqrt(self.dot(self))

    def unit(self) -> "Vector2":
        n = self.norm()
        if n == 0:
            return Vector2(0.0, 0.0)
        return self.mul(1.0 / n)


@dataclass(frozen=True)
class Vector3:
    x: float
    y: float
    z: float

    def add(self, other: "Vector3") -> "Vector3":
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def sub(self, other: "Vector3") -> "Vector3":
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def mul(self, scalar: float) -> "Vector3":
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    def dot(self, other: "Vector3") -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def norm(self) -> float:
        return sqrt(self.dot(self))

    def unit(self) -> "Vector3":
        n = self.norm()
        if n == 0:
            return Vector3(0.0, 0.0, 0.0)
        return self.mul(1.0 / n)


def _solve_intercept_time(relative_position_sq: float, relative_position_dot_velocity: float, relative_velocity_sq: float, projectile_speed: float) -> Optional[float]:
    """
    Solve for lowest positive t satisfying |r + v t| = s t where r is relative position and v is relative velocity.

    This expands to (v·v - s^2) t^2 + 2 (r·v) t + (r·r) = 0.
    """
    a = relative_velocity_sq - projectile_speed * projectile_speed
    b = 2.0 * relative_position_dot_velocity
    c = relative_position_sq

    if abs(a) < 1e-12:
        # Degenerate to linear: b t + c = 0 => t = -c / b
        if abs(b) < 1e-12:
            return None
        t = -c / b
        return t if t > 0 else None

    discriminant = b * b - 4.0 * a * c
    if discriminant < 0:
        return None

    sqrt_disc = sqrt(discriminant)
    t1 = (-b - sqrt_disc) / (2.0 * a)
    t2 = (-b + sqrt_disc) / (2.0 * a)

    # Choose the smallest positive time
    candidates = [t for t in (t1, t2) if t > 0]
    if not candidates:
        return None
    return min(candidates)


def predict_intercept_2d(
    shooter_position: Vector2,
    target_position: Vector2,
    target_velocity: Vector2,
    projectile_speed: float,
    shooter_velocity: Optional[Vector2] = None,
) -> Optional[Tuple[float, Vector2, Vector2, float]]:
    """
    Returns (time_to_intercept, intercept_point, aim_unit_vector, distance_to_intercept) or None if no solution.
    """
    if projectile_speed <= 0:
        return None

    relative_position = target_position.sub(shooter_position)
    relative_velocity = target_velocity.sub(shooter_velocity) if shooter_velocity else target_velocity

    r_dot_r = relative_position.dot(relative_position)
    r_dot_v = relative_position.dot(relative_velocity)
    v_dot_v = relative_velocity.dot(relative_velocity)

    t = _solve_intercept_time(r_dot_r, r_dot_v, v_dot_v, projectile_speed)
    if t is None:
        return None

    intercept_point = target_position.add(relative_velocity.mul(t))
    aim_vector = intercept_point.sub(shooter_position)
    distance = aim_vector.norm()
    aim_unit = aim_vector.unit()

    return t, intercept_point, aim_unit, distance


def predict_intercept_3d(
    shooter_position: Vector3,
    target_position: Vector3,
    target_velocity: Vector3,
    projectile_speed: float,
    shooter_velocity: Optional[Vector3] = None,
) -> Optional[Tuple[float, Vector3, Vector3, float]]:
    """
    Returns (time_to_intercept, intercept_point, aim_unit_vector, distance_to_intercept) or None if no solution.
    """
    if projectile_speed <= 0:
        return None

    relative_position = target_position.sub(shooter_position)
    relative_velocity = target_velocity.sub(shooter_velocity) if shooter_velocity else target_velocity

    r_dot_r = relative_position.dot(relative_position)
    r_dot_v = relative_position.dot(relative_velocity)
    v_dot_v = relative_velocity.dot(relative_velocity)

    t = _solve_intercept_time(r_dot_r, r_dot_v, v_dot_v, projectile_speed)
    if t is None:
        return None

    intercept_point = target_position.add(relative_velocity.mul(t))
    aim_vector = intercept_point.sub(shooter_position)
    distance = aim_vector.norm()
    aim_unit = aim_vector.unit()

    return t, intercept_point, aim_unit, distance