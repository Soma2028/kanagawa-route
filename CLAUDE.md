# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Streamlit web app that proposes an optimal sightseeing route around Kamakura given a time
budget and area preferences. This is an **orienteering problem** (maximize collected score
within a time limit), not a TSP — the solver chooses both which spots to visit and in what
order, and it's expected/desired that low-value spots get dropped.

## Commands

```bash
uv sync                        # install dependencies (Python >=3.14, managed via uv)
uv run streamlit run app.py    # run the main app
uv run python optimize.py      # run the solver standalone, prints one sample route to stdout
uv run python compare_runs.py  # check solution variance across search_sec settings (5/15/30s, 10 trials each)
uv run python compare_matrix.py  # validate straight-line-distance approximation against ORS ground truth
```

There is no test suite, linter, or CI config in this repo — verification is done via the
`check_*.py` / `compare_*.py` scripts and by eyeballing solver output.

`ORS_API_KEY` (OpenRouteService) must be set in `.env` to re-run `fetch_walk_matrix.py`.
**Never commit `.env`** — it holds the ORS API key (already gitignored; don't change that).

## Data pipeline (run in order, mostly one-off / already executed)

The repo ships with the CSVs these scripts produce already checked in, so day-to-day work on
`app.py` or `optimize.py` does not require re-running the pipeline. Re-run a step only when
changing spot selection, scoring, or travel-time methodology.

1. `fetch_spots.py` → `spots_kamakura.csv` — raw Overpass API pull (found to be noisy/incomplete,
   see README "OSM だけでは足りなかった"; kept for reference, not used downstream anymore)
2. `filter_spots.py` → `candidates.csv` — mechanical filtering of the Overpass dump
3. `fetch_coords.py` → `spots_master.csv` — the actual source of truth: a **hand-curated list of
   34 spots** (`SPOTS` in the file) geocoded via Nominatim, with `stay_min`/`open_hour`/
   `close_hour`/`fee`/`score` filled in by hand afterward
4. `check_coords.py` / `check_spots.py` — sanity checks on the above
5. `fetch_walk_matrix.py` → `walk_matrix_ors.csv` — real walking-time matrix from OpenRouteService
   (`spots_master.csv` row order must match this matrix's index/columns exactly)
6. `travel_time.py` (`build_matrix`) → `travel_matrix.csv` — combines the ORS walk matrix with a
   rail-or-walk decision per spot pair (see below), run via `travel_time.py`'s `__main__`
7. `fetch_photos.py` → `photo_candidates.csv` — searches Wikimedia Commons per spot, keeps only
   commercially-reusable licenses (CC BY / CC BY-SA / CC0 / public domain)
8. `select_photos.py` — a separate small Streamlit app for manually picking one photo per spot
   from the candidates → `photos_selected.csv` (consumed by `app.py` for spot cards)

`compare_matrix.py` and `compare_runs.py` are one-off analysis scripts (not part of the pipeline)
used to validate the travel-time approximation and solver stability; their output is summarized
in the README.

## Architecture

**`spots_master.csv`** is the single hand-maintained master table (34 spots + attributes:
area, lat/lon, stay_min, open_hour/close_hour, fee, score 1–10, description). Everything else
derives from it. `score` is **manually set, 1–10**, based on the spot's fame (知名度) and the
quality of the experience (体験の質) — it is not derived from any OSM tag or external rating, so
don't assume it can be recomputed or validated automatically.

**Travel time / mode selection** (`travel_time.py`): for every spot pair, the shorter of (a) the
ORS real walking-time measurement and (b) walk-to-nearest-station + wait (`WAIT_MIN`) + Enoden/
rail ride time (`rail_min`, via `RAIL_FROM_KAMAKURA`) + walk-from-station is chosen, and the
chosen mode is recorded in a parallel `modes` matrix. This two-mode model exists because
pure straight-line-distance walking estimates were badly wrong for stations far from Kamakura
Station (e.g. Kamakurakoukou-mae) — see README for the specific before/after numbers.

**Solver** (`optimize.py`, OR-Tools Routing, `load_data()` + `solve()`):
- `load_data()` reloads `spots_master.csv` + `travel_matrix.csv`, prepends a synthetic "起点"
  (start = Kamakura Station) node at index 0, and recomputes start↔spot travel times/modes the
  same walk-vs-rail way as `travel_time.py` (this duplication is intentional — the precomputed
  matrix only covers spot-to-spot pairs, not the start node).
- Single vehicle, single route (`RoutingIndexManager(n, 1, 0)`).
- Arc cost = travel time + stay time at the *origin* node of the arc.
- One `Time` dimension enforces the overall time budget; each spot's opening hours become a
  `CumulVar` range on that dimension. `max_wait` (slack) controls how long the route may wait
  for a spot to open — this was previously hardcoded to 0 (no waiting allowed), which
  over-constrained the search space and produced a worse solution even though it looked like a
  parameter-tuning problem: penalty scale sweeps (100/300/1000) all returned the *identical*
  route, and only allowing up to 60 min of wait fixed it — total score went from **54 (9 spots,
  0-min wait) to 67 (8 spots, 60-min wait)** (see README "パラメータではなく制約構造が原因だっ
  た"). Keep this in mind if solver results look suspiciously insensitive to other parameters —
  check dimension/slack setup before tuning penalties or search time.
- Every non-start spot is wrapped in `AddDisjunction([...], penalty)` with
  `penalty = score * penalty_scale`, i.e. spots can be skipped, and skipping a high-score spot
  costs more. The objective is **sum of scores of visited spots**, not visit count or distance —
  an earlier version optimized visit count and produced routes that skipped all the famous
  (long-stay) spots in favor of packing in short, close-together ones.
- `GUIDED_LOCAL_SEARCH` + `PATH_CHEAPEST_ARC` first solution, time-limited by `search_sec`.
- An earlier CP-SAT formulation (`optimize_cpsat.py`, kept for comparison) used BIG-M time
  constraints and did not converge at 34 spots; the Routing-based formulation replaced it.

**App** (`app.py`): loads data via `optimize.load_data()`, lets the user set start time, time
budget, preferred areas (unpicked areas get their scores clamped to 1, i.e. deprioritized but
not excluded), search seconds, and max wait, then calls `solve()`. Renders a left-column
itinerary timeline (with per-spot photo/credit from `photos_selected.csv`, area color/icon from
`AREA_COLORS`/`AREA_ICONS`, star rating from `stars()`) and a right-column folium map (solid
line = walk, orange dashed = rail; markers offset when spots are close together to avoid
overlap).

`src/kanagawa_route/__init__.py` is an unused packaging stub (`project.scripts` entry point);
all real logic lives in the top-level scripts, not under `src/`.
