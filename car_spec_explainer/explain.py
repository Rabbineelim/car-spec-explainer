"""Core logic: parse a spec, derive metrics, and explain them in plain English."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

HP_TO_KW = 0.7457
LBFT_TO_NM = 1.35582
LB_TO_KG = 0.453592

DRIVETRAINS = {
    "fwd": "Front-wheel drive: the engine pulls the car with the front wheels. "
    "It is light, cheap and good in rain, but strong launches can make the front tires slip "
    "and the steering tug (torque steer).",
    "rwd": "Rear-wheel drive: the rear wheels push the car while the front wheels only steer. "
    "That gives balanced handling and clean launches in the dry, but less grip on snow.",
    "awd": "All-wheel drive: power goes to all four wheels, so it puts power down well "
    "off the line and in bad weather, at the cost of extra weight and some efficiency.",
    "4wd": "Four-wheel drive: a rugged system meant for off-road traction, usually with "
    "low-range gearing. It is heavier and less efficient on normal roads.",
}


@dataclass
class CarSpec:
    """A car's headline specs. Power in hp, torque in lb-ft, weight in lb."""

    name: str
    hp: float
    torque_lbft: float
    weight_lb: float
    drivetrain: str = "fwd"
    redline_rpm: float | None = None
    peak_torque_rpm: float | None = None
    extras: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        for label, value in (("hp", self.hp), ("torque_lbft", self.torque_lbft), ("weight_lb", self.weight_lb)):
            if value is None or value <= 0:
                raise ValueError(f"{label} must be a positive number, got {value!r}")
        self.drivetrain = self.drivetrain.lower()
        if self.drivetrain not in DRIVETRAINS:
            raise ValueError(f"drivetrain must be one of {sorted(DRIVETRAINS)}, got {self.drivetrain!r}")

    @classmethod
    def from_dict(cls, data: dict) -> "CarSpec":
        known = {"name", "hp", "torque_lbft", "weight_lb", "drivetrain", "redline_rpm", "peak_torque_rpm"}
        extras = {k: v for k, v in data.items() if k not in known}
        return cls(
            name=data.get("name", "Unnamed car"),
            hp=float(data["hp"]),
            torque_lbft=float(data["torque_lbft"]),
            weight_lb=float(data["weight_lb"]),
            drivetrain=data.get("drivetrain", "fwd"),
            redline_rpm=data.get("redline_rpm"),
            peak_torque_rpm=data.get("peak_torque_rpm"),
            extras=extras,
        )


def load_spec(path: str | Path) -> CarSpec:
    with open(path, encoding="utf-8") as fh:
        return CarSpec.from_dict(json.load(fh))


def metrics(spec: CarSpec) -> dict:
    """Derived numbers used by the explanations."""
    lb_per_hp = spec.weight_lb / spec.hp
    hp_per_ton = spec.hp / (spec.weight_lb / 2000)
    # Rough empirical fit for 0-60 mph in seconds from weight-to-power alone.
    zero_to_sixty = round(1.2 * lb_per_hp ** 0.62, 1)
    return {
        "kw": round(spec.hp * HP_TO_KW, 1),
        "torque_nm": round(spec.torque_lbft * LBFT_TO_NM, 1),
        "weight_kg": round(spec.weight_lb * LB_TO_KG),
        "lb_per_hp": round(lb_per_hp, 2),
        "hp_per_ton": round(hp_per_ton, 1),
        "torque_to_hp": round(spec.torque_lbft / spec.hp, 2),
        "est_0_60_s": zero_to_sixty,
    }


def _weight_band(lb_per_hp: float) -> str:
    if lb_per_hp < 6:
        return "supercar territory: every horsepower carries very little weight"
    if lb_per_hp < 10:
        return "properly quick, like a modern sports car or hot hatch"
    if lb_per_hp < 15:
        return "brisk, faster than most everyday cars"
    if lb_per_hp < 20:
        return "average for a daily driver"
    return "relaxed: fine for commuting, but merging and passing take planning"


def _torque_character(ratio: float) -> str:
    if ratio >= 1.1:
        return ("Torque is high compared with horsepower, so it feels strong low in the rev range. "
                "Think turbo or diesel: easy shove from a stop without revving hard.")
    if ratio <= 0.8:
        return ("Horsepower is high compared with torque, so the engine makes its power by revving. "
                "It rewards keeping the RPM up, like a high-revving sports engine.")
    return "Torque and horsepower are balanced, so pull is fairly even across the rev range."


def explain(spec: CarSpec) -> str:
    """Return a plain-English explanation of a car's specs."""
    m = metrics(spec)
    lines = [
        f"{spec.name}",
        "=" * len(spec.name),
        "",
        f"Power: {spec.hp:g} hp ({m['kw']} kW). Horsepower is how fast the engine can do work; "
        "it sets top speed and how hard the car keeps pulling at high speed.",
        f"Torque: {spec.torque_lbft:g} lb-ft ({m['torque_nm']} Nm). Torque is the engine's twisting force; "
        "it is the push you feel in your back when you step on it.",
        _torque_character(m["torque_to_hp"]),
        "",
        f"Weight: {spec.weight_lb:g} lb ({m['weight_kg']} kg), which works out to {m['lb_per_hp']} lb per hp "
        f"({m['hp_per_ton']} hp per US ton). That is {_weight_band(m['lb_per_hp'])}.",
        f"Rough 0-60 mph estimate from power-to-weight alone: about {m['est_0_60_s']} s "
        "(real numbers depend on gearing, traction and launch).",
        "",
        DRIVETRAINS[spec.drivetrain],
    ]
    if spec.peak_torque_rpm and spec.redline_rpm:
        share = spec.peak_torque_rpm / spec.redline_rpm
        where = "early" if share < 0.4 else "in the middle" if share < 0.7 else "late"
        lines += ["", f"Peak torque arrives at {spec.peak_torque_rpm:g} rpm out of a {spec.redline_rpm:g} rpm "
                      f"redline, so the strongest pull comes {where} in each gear."]
    return "\n".join(lines)


def compare(a: CarSpec, b: CarSpec) -> str:
    """Short side-by-side comparison of two cars."""
    ma, mb = metrics(a), metrics(b)
    quicker = a if ma["lb_per_hp"] < mb["lb_per_hp"] else b
    torquier = a if a.torque_lbft > b.torque_lbft else b
    return (
        f"{a.name}: {ma['lb_per_hp']} lb/hp, {a.torque_lbft:g} lb-ft, {a.drivetrain.upper()}\n"
        f"{b.name}: {mb['lb_per_hp']} lb/hp, {b.torque_lbft:g} lb-ft, {b.drivetrain.upper()}\n"
        f"{quicker.name} has the better power-to-weight ratio, so it should feel quicker overall. "
        f"{torquier.name} has more torque, so it should feel stronger at low RPM."
    )
