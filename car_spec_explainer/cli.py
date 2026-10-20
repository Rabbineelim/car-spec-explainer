"""Command line interface: python -m car_spec_explainer SPEC.json [OTHER.json]"""

from __future__ import annotations

import argparse
import json

from .explain import CarSpec, compare, explain, load_spec, metrics


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="car-spec-explainer", description="Explain car specs in plain English.")
    parser.add_argument("spec", nargs="?", help="JSON spec file")
    parser.add_argument("other", nargs="?", help="Optional second JSON spec to compare against")
    parser.add_argument("--hp", type=float)
    parser.add_argument("--torque", type=float, help="Torque in lb-ft")
    parser.add_argument("--weight", type=float, help="Curb weight in lb")
    parser.add_argument("--drivetrain", default="fwd", choices=["fwd", "rwd", "awd", "4wd"])
    parser.add_argument("--name", default="Your car")
    parser.add_argument("--json", action="store_true", help="Print derived metrics as JSON")
    args = parser.parse_args(argv)

    if args.spec:
        spec = load_spec(args.spec)
    elif args.hp and args.torque and args.weight:
        spec = CarSpec(args.name, args.hp, args.torque, args.weight, args.drivetrain)
    else:
        parser.error("give a JSON spec file, or --hp, --torque and --weight")

    if args.json:
        print(json.dumps(metrics(spec), indent=2))
    elif args.other:
        print(compare(spec, load_spec(args.other)))
    else:
        print(explain(spec))
    return 0
