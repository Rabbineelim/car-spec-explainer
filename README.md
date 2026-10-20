# car-spec-explainer

Turns a car's headline specs (horsepower, torque, weight, drivetrain) into plain-English explanations: what torque vs horsepower actually means for how the car feels, what the power-to-weight ratio says about speed, and what the drivetrain changes.

Pure Python 3.10+, no dependencies.

## Demo

```console
$ python -m car_spec_explainer examples/hot-hatch.json
Example hot hatch
=================

Power: 241 hp (179.7 kW). Horsepower is how fast the engine can do work; it sets top speed and how hard the car keeps pulling at high speed.
Torque: 273 lb-ft (370.1 Nm). Torque is the engine's twisting force; it is the push you feel in your back when you step on it.
Torque is high compared with horsepower, so it feels strong low in the rev range. Think turbo or diesel: easy shove from a stop without revving hard.

Weight: 3150 lb (1429 kg), which works out to 13.07 lb per hp (153.0 hp per US ton). That is brisk, faster than most everyday cars.
Rough 0-60 mph estimate from power-to-weight alone: about 5.9 s (real numbers depend on gearing, traction and launch).

Front-wheel drive: the engine pulls the car with the front wheels. It is light, cheap and good in rain, but strong launches can make the front tires slip and the steering tug (torque steer).

Peak torque arrives at 1600 rpm out of a 6800 rpm redline, so the strongest pull comes early in each gear.
```

Compare two cars:

```console
$ python -m car_spec_explainer examples/hot-hatch.json examples/roadster.json
Example hot hatch: 13.07 lb/hp, 273 lb-ft, FWD
Example roadster: 12.93 lb/hp, 151 lb-ft, RWD
Example roadster has the better power-to-weight ratio, so it should feel quicker overall. Example hot hatch has more torque, so it should feel stronger at low RPM.
```

Or skip the file and pass numbers directly (add `--json` for raw derived metrics):

```console
$ python -m car_spec_explainer --hp 300 --torque 280 --weight 3300 --drivetrain awd --name "My car"
```

## Spec format

```json
{"name": "Example roadster", "hp": 181, "torque_lbft": 151, "weight_lb": 2340,
 "drivetrain": "rwd", "peak_torque_rpm": 4000, "redline_rpm": 7500}
```

`drivetrain` is one of `fwd`, `rwd`, `awd`, `4wd`. The two rpm fields are optional. The example cars are made-up numbers for illustration, not any real model's specs.

## How it works

- Converts units (hp to kW, lb-ft to Nm, lb to kg).
- Weight per horsepower sets a speed band and a rough 0-60 mph estimate (an empirical fit, `1.2 * (lb/hp)^0.62`, which ignores gearing and traction).
- The torque-to-horsepower ratio tells whether the engine pulls hard low down (turbo/diesel feel) or makes its power by revving.
- Peak-torque rpm relative to redline says where in each gear the strongest pull comes.

## Tests

```console
$ python -m unittest discover -s tests -v
```

## Roadmap

- Gearing and tire size for wheel torque and top speed per gear
- Small web page front end
- Side-by-side tables for more than two cars

## License

MIT
