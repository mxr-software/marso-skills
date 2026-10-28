# Polygon budget

`plan_assets.py --polycount` writes `polygon_count` on each asset routed to `generate`, and `crop_objects.py` copies it into the brief. Without the option no budget is written and the generation step uses its own default.

## Rules

| `--polycount` | `polygon_count` |
| --- | --- |
| a whole number, such as `40000` | that number on every generated asset |
| `by-size` | from the asset's largest dimension `size_m`: under 0.3 m 40000; under 1 m 50000; under 2 m 100000; otherwise 250000 |

An asset with no size reads as 0 m and gets the smallest budget; it is usually flagged `low-size-confidence` already.

## It is a default to review

- The budget is chosen from size alone. A small object with fine relief (a carved ornament) can need more; a large plain one (a bin) can need less. Change `polygon_count` in `asset_plan.json` during review, and record the change in `review`.
- The model decides what is allowed. Before a job is sent, read the selected model's live options and clip the budget to the nearest offered value at or below it, or the smallest offered value when none is below. For example, Tripo `tripo_h3_1` has offered 40k, 50k, 100k, 250k, 500k, 1M and 1.5M; read the live list rather than trusting this one.
- Never send a number the live options do not list. Report every asset whose budget was clipped.
