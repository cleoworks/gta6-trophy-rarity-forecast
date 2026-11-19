"""gta6-trophy-rarity-forecast-01: forecast Exophase GTA VI trophy earn rates.

Model v3 (tweak round 2, 2026-11-19 ~12:45 UTC; v2 = commit da05a33, tag v2):
  v2 plus ONE measured change — a minimax median blend toward persistence:
  after all other median work, each trophy's median (logit) is pulled 35%
  of the way toward the logit of its last observed rate (BLEND_ALPHA = 0.35).
  The 100% trophy is untouched (last rate 100); trophies with no last rate
  keep their fitted median. Rationale, measured on TWO independent synthetic
  generators (harness/gen.py and harness2/gen2.py, the second built with
  Poisson refreshes, daily buyer cohorts + weekend surge, and per-group
  hazards drawn from research-analog ranges — frozen before any experiment
  was measured): v2's extrapolated median systematically OVERSHOOTS in the
  second generator's world (Ch1 median 59.5% vs truth 46.1% in scenario A;
  final 5.0% vs 2.8%), because a log-linear fit extrapolates a fast early
  climb too steeply, and the same overshoot is what makes v2 lose to
  persistence whenever a late dilution shock divides rates by ~3. The blend
  is a hedge between the two plausible worlds: the generators disagree on
  the sign of v2's median error in scenario A, so no single median is right
  in both — the blend wins on the average and on the worst case.
  Measured (practice + 6 synthetic scenarios): practice 0.9721 (v2 0.9708);
  gen1 A 0.3030 / B 0.3823 / C 0.3861 (v2: 0.2367 / 0.5228 / 0.2893);
  gen2 A 0.2109 / B 0.6551 / C 0.2664 (v2: 0.3367 / 1.1470 / 0.3102);
  mean of 6: 0.3673 (v2 0.4738, -0.1065); worst case 1.1470 -> 0.6551.
  The full alpha curve (mean of 6): 0.00 -> 0.4738, 0.15 -> 0.4161,
  0.25 -> 0.3841, 0.35 -> 0.3673, 0.45 -> 0.3711, 0.50 -> 0.3752,
  0.75 -> 0.4211 — the minimum is FLAT across 0.35-0.45; 0.35 is picked by
  the pre-registered rule (best mean among variants passing: mean improves,
  practice regresses <= 0.02, improves in >= 4 of 7 measurement sets).
  HONEST LIMIT: v3 still loses to persistence in scenario B in BOTH
  generators (gen1-B 0.3823 vs 0.3074; gen2-B 0.6551 vs 0.2269) — no alpha
  reaches the explicit minimax target without destroying A/C (alpha 0.75
  beats persistence in gen1-B only, at A/C +0.23/+0.29). Gen1 A/C cost
  +0.066/+0.097. Full experiment tables: results/experiments-tweak2.md.
  Rejected in this round, with reasons in results/experiments-tweak2.md:
  (b) weekend-weighted target time (helps gen1 A/C slightly, hurts gen2
  everywhere: the weekend weight raises medians that already overshoot);
  (c1) story median -0.3 (passes the letter of the rule but gains only
  -0.0089 mean, far below the blend; kept out, tested in combination too);
  (c2) story-only down-spread 1.5 (mean gain -0.0009 = noise, 3/7 sets);
  (a) at other alphas (0.15/0.25 pass but worse mean; 0.45/0.50 fail the
  >=4/7-sets rule; 0.75 fails badly).

  [Rest of the v2 docstring follows unchanged.]

  v1 plus two measured changes, everything else identical:
  (c) per-group spread recalibration from the real refresh event (median
      logit move -1.59) and the launch analogs: story band 0.7-1.2 -> 0.8-1.4
      (fast-rising story is hit hardest by a dilution refresh), grind band
      1.2-1.8 -> 1.0-1.6 (slow trophies' rates move least). Measured on the
      rebuilt synthetic generator: A 0.2392->0.2344, B 0.5209->0.5205,
      C 0.2969->0.2870; practice 0.9692->0.9685. Small, but better in all
      four measurements.
  (d) the 100% trophy's q05 96.93% -> ~80% (INTRO_DOWN 3.5 -> 4.76). Under
      a two-world mixture (quirk survives with prob p, else the rate falls
      to ~1%), the q05 pinball premium is exactly tied at p = 0.95, lower
      wins for every p < 0.95, and costs little above it. The rest of the
      intro row is unchanged (q25+ stay in the survive world for any
      p > 0.75). Cost in the survive world is ~0.002 on practice.
  Rejected in this round, with reasons in results/experiments-tweak.md:
  (a) asymmetric down-spread (all-groups and story-only variants fail their
      written thresholds: B gains < A/C regressions); (b) separate E/N model
      (wins 2/3 scenarios by dust, loses the mean); (e) S-curve basis for
      story (overshoots: B 0.52->0.90); (f) effective horizon (net ~0);
      (g) narrower slow-group spreads (synthetic gain smaller than the
      practice regression it causes, and it bets on generator optimism about
      grind earners that contradicts launch evidence).

  - Rate is earners over tracked players: r = E / N.  Each read's per-trophy
    earner count is reconstructed as round(rate * N / 100) and checked against
    the read's trophies_earned total (a warning on stderr if it ever disagrees;
    the forecast never crashes on it).
  - The page is a step function: most reads repeat the previous page exactly.
    The fit uses only DISTINCT page states (first-seen time of each state),
    so a long frozen stretch cannot outweigh the reads where the page moved.
  - Per trophy, logit(rate) is fitted against x = ln(1 + (t - launch) / tau)
    with tau = 18h, by recency-weighted least squares, over the LAST 24 HOURS
    of distinct page states only.  The early history is a different regime
    (launch-night freeze, then a dilution dip as tracked players flood in):
    a straight line fitted over the whole history averages the dip and the
    recovery and extrapolates almost flat, while the recent window carries
    the current trend.  (Measured: on synthetic long-horizon cases the
    full-history fit lost to the house curve 0.90 vs 0.47; the 24h window
    is the fix.)  The slope is shrunk toward its trophy group's mean slope
    (thin trophies must not run wild), then the intercept is refit through
    the data at the shrunk slope.  For the slowest groups (grind, platinum,
    100%-completion) the slope is floored at 0: their observed logit-decline
    is dilution, and denominator growth is front-loaded and decelerating
    (638 -> 3,868 -> ~10,000 already slowed from 6x to 2.6x), so a constant
    log-linear decline extrapolated 4.5 days forward overshoots the fall;
    these rates bottom out instead.  When fewer than 2 distinct states fall
    in the window, the fit falls back to all distinct states.
  - The median at the target is pulled 25% back toward a per-group prior cap
    when the fit overshoots it (a log-linear fit with no cap overshoots on
    fast-rising story trophies); the fit is trusted over the prior otherwise.
  - Medians are then made monotone along the story chain
    (Ch1 >= Ch2 >= Ch3 >= Ch4 >= final mission) and platinum <= 100%-completion
    <= every other trophy, because the story cohort is nested.
  - Spread per trophy is s = sqrt(fit^2 + refresh^2 + floor^2) on the logit
    scale, floor 0.5, clamped to a per-group band (story 0.8-1.4, activity /
    strand 0.9-1.5, grind 1.0-1.6, platinum / 100% 1.5-2.0).  The one trophy
    sitting at 100% ("Just Like Paradise") keeps median ~99.99 but gets a wide
    downward-only spread: if that 100% is an Exophase quirk that gets fixed,
    its rate can fall a long way, and a q05 pinned near 100 would be punished
    hard (pinball ~3.08/5 on that trophy alone); v2 sets q05 ~80% instead.
  - A trophy with no usable rate in any read falls back to its group prior;
    a trophy that appears only in later reads is fitted from what exists.
    Nothing here reads the network; output is deterministic.

Quantiles use z = (-1.645, -0.674, 0, 0.674, 1.645), clamped to 0.01..99.99,
non-decreasing, rounded to 4 decimals half-up (same rounding as the starter).
"""

import json
import math
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.645, -0.674, 0.0, 0.674, 1.645]

# Launch: the house curve's origin (RULES: ln(1 + hours from 2026-11-19T00:00Z)).
LAUNCH = datetime(2026, 11, 19, 0, 0, 0, tzinfo=timezone.utc)
TAU_HOURS = 18.0

# Shrinkage strength: a trophy's own slope counts as n_points observations,
# its group mean counts as SHRINK_K.
SHRINK_K = 2.0
# Spread pieces (logit units).
SPREAD_FLOOR = 0.5
SPREAD_REFRESH_DEFAULT = 0.3
# The 100% trophy's downward-only spread (see module docstring).
# v2 (d): INTRO_DOWN 3.5 -> 4.76, so the 100% trophy's q05 is ~80%
# instead of 96.93% (mixture premium table in results/experiments-tweak.md:
# exact tie at p(survive)=0.95, wins for every p < 0.95).
# TWEAK2 (a): minimax median blend toward persistence — fraction of the
# extrapolated median (in logit space) pulled back to the last observed
# rate. 0.0 = v2. Set per variant: 0.15 / 0.35.
BLEND_ALPHA = 0.35
INTRO_DOWN = 4.76
INTRO_UP = 0.5

# Named story missions (ids 8-13): descriptions as they appear in the case.
STORY_MISSIONS = {
    "Complete Breakfast Run.",
    "Complete The Cartel Heist.",
    "Complete Child's Play.",
    "Complete Headliners.",
    "Complete VCIA Takedown.",
    "Complete Operation Savage Glory.",
}

GRIND_WORDS = (
    "250 Stunts",
    "Collectible Card sets",
    "WAiNK It at 100 locations",
    "50 Challenges",
    "100 vehicles",
    "Bank Vaults",
    "Explore all of Leonida",
    "laundering Marked Bills",
    "Spend $100,000",
    "garage properties",
    "Scooter Bros",
    "Shooting Range",
    "gold medal",
)


def clamp_pct(x: float) -> float:
    return min(99.99, max(0.01, x))


def logit(pct: float) -> float:
    p = clamp_pct(pct)
    return math.log(p / (100.0 - p))


def sigmoid(lg: float) -> float:
    if lg >= 0:
        return 1.0 / (1.0 + math.exp(-lg))
    e = math.exp(lg)
    return e / (1.0 + e)


def round4(x: float):
    """Round to 4 decimals, half up, like the starter (JS Math.round)."""
    scaled = x * 10000.0
    whole = math.floor(scaled)
    if scaled - whole >= 0.5:
        whole += 1
    value = whole / 10000.0
    return int(value) if value == int(value) else value


def parse_time(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def classify(trophy: dict):
    """Return (group, cap_pct, spread_min, spread_max) for one trophy.

    Groups are keyed off the trophy's own description/tier, never its id, so
    a trophy added after launch still lands in a sensible group.
    """
    desc = trophy.get("description", "") or ""
    tier = trophy.get("tier", "") or ""
    if tier == "platinum":
        return ("plat", 0.5, 1.5, 2.0)
    if desc == "Complete Gone Fishing.":
        return ("intro", 100.0, 0.0, 0.0)
    if "Complete Chapter 1." in desc:
        return ("story", 70.0, 0.8, 1.4)
    if "Complete Chapter 2." in desc:
        return ("story", 55.0, 0.8, 1.4)
    if "Complete Chapter 3." in desc:
        return ("story", 40.0, 0.8, 1.4)
    if "Complete Chapter 4." in desc:
        return ("story", 25.0, 0.8, 1.4)
    if desc == "Complete the final mission.":
        return ("story", 10.0, 0.8, 1.4)
    if desc in STORY_MISSIONS:
        return ("story", 25.0, 0.8, 1.4)
    if "Attain 100% Completion." in desc:
        return ("completion", 0.5, 1.5, 2.0)
    if "final mission for" in desc or "mission strands" in desc:
        return ("strand", 15.0, 0.9, 1.5)
    if any(w in desc for w in GRIND_WORDS):
        return ("grind", 8.0, 1.0, 1.6)
    return ("activity", 30.0, 0.9, 1.5)


def x_of(t: datetime) -> float:
    """Log-time coordinate: ln(1 + (t - launch) / tau)."""
    dt_h = (t - LAUNCH).total_seconds() / 3600.0
    # Reads just before launch give a small negative dt; keep 1 + dt/tau > 0.
    dt_h = max(dt_h, -0.9 * TAU_HOURS)
    return math.log1p(dt_h / TAU_HOURS)


def distinct_reads(history):
    """Collapse the history to distinct page states, first-seen time each.

    Returns a list of (time, players_tracked, rates_tuple) in time order.
    """
    seen = {}
    order = []
    for read in history:
        rates = tuple(read["rates"])
        key = (read["players_tracked"], rates)
        if key not in seen:
            seen[key] = (parse_time(read["at"]), read["players_tracked"], rates)
            order.append(key)
    return [seen[k] for k in order]


def wls(points):
    """Weighted least squares of y on x. points = [(x, y, w), ...].

    Returns (slope, intercept, resid_sd) or (None, None, 0.0) when the fit is
    degenerate (fewer than 2 distinct x values or no y variance).
    """
    if len(points) < 2:
        return None, None, 0.0
    sw = sum(w for _, _, w in points)
    mx = sum(w * x for x, _, w in points) / sw
    my = sum(w * y for _, y, w in points) / sw
    sxx = sum(w * (x - mx) ** 2 for x, _, w in points)
    if sxx <= 1e-12:
        return None, None, 0.0
    sxy = sum(w * (x - mx) * (y - my) for x, y, w in points)
    slope = sxy / sxx
    intercept = my - slope * mx
    resid = math.sqrt(
        sum(w * (y - (intercept + slope * x)) ** 2 for x, y, w in points) / sw
    )
    return slope, intercept, resid


def forecast_case(case: dict, name: str) -> dict:
    trophies = case["trophies"]
    history = case.get("history") or []
    horizon_days = case["horizon_minutes"] / 1440.0
    target = parse_time(case["target"])
    x_target = x_of(target)

    states = distinct_reads(history)

    # Fit window: only the last 24h of distinct states (see module docstring).
    # Fall back to all states when the window holds fewer than 2.
    if len(states) >= 2:
        window_start = states[-1][0] - timedelta(hours=24)
        fit_states = [s for s in states if s[0] >= window_start]
        if len(fit_states) < 2:
            fit_states = states
    else:
        fit_states = states
    # Earner-count validation on the raw history (reconstruction must add up).
    for read in history:
        n = read["players_tracked"]
        total = sum(
            round(r * n / 100.0) for r in read["rates"] if r is not None
        )
        if total != read["trophies_earned"]:
            print(
                f"warning: {name} read {read['at']}: reconstructed earners "
                f"{total} != trophies_earned {read['trophies_earned']}",
                file=sys.stderr,
            )
            break

    # Time span of the fit window, for scaling the fit residual to horizon.
    if len(fit_states) >= 2:
        span_days = max(
            (fit_states[-1][0] - fit_states[0][0]).total_seconds() / 86400.0,
            0.25,
        )
    else:
        span_days = 0.25

    # Refresh cadence from gaps between distinct states (hours, median gap).
    if len(states) >= 3:
        gaps = sorted(
            (states[i + 1][0] - states[i][0]).total_seconds() / 3600.0
            for i in range(len(states) - 1)
        )
        med_gap = gaps[len(gaps) // 2]
        s_refresh = 0.2 + 0.1 * min(2.0, med_gap / 12.0)
    else:
        s_refresh = SPREAD_REFRESH_DEFAULT

    groups = [classify(t) for t in trophies]
    n_tr = len(trophies)

    # Per-trophy series over the fit window's distinct states:
    # (x, logit(rate), weight).
    series = []
    for i in range(n_tr):
        pts = []
        for j, (t, n, rates) in enumerate(fit_states):
            r = rates[i]
            if r is None:
                continue
            pts.append((x_of(t), logit(r), 1.0 + j))
        series.append(pts)

    # Per-trophy WLS slopes, then group-mean slopes for shrinkage.
    own_slope = [None] * n_tr
    own_resid = [0.0] * n_tr
    for i in range(n_tr):
        s, _, resid = wls(series[i])
        own_slope[i] = s
        own_resid[i] = resid
    group_slope = {}
    for g in {g[0] for g in groups}:
        num = 0.0
        den = 0.0
        for i in range(n_tr):
            if groups[i][0] == g and own_slope[i] is not None:
                w = len(series[i])
                num += w * own_slope[i]
                den += w
        group_slope[g] = (num / den) if den > 0 else 0.0

    med_logit = [0.0] * n_tr
    spread = [0.0] * n_tr
    for i in range(n_tr):
        group, cap, s_min, s_max = groups[i]
        pts = series[i]
        g_slope = group_slope[group]
        if pts:
            if own_slope[i] is not None:
                b = (
                    len(pts) * own_slope[i] + SHRINK_K * g_slope
                ) / (len(pts) + SHRINK_K)
            else:
                b = g_slope
            # Slowest groups never extrapolate a decline: dilution flattens.
            if group in ("grind", "plat", "completion"):
                b = max(b, 0.0)
            # Refit the intercept at the shrunk slope (line through the data).
            sw = sum(w for _, _, w in pts)
            a = sum(w * (y - b * x) for x, y, w in pts) / sw
            med = a + b * x_target
            # Soft cap: 25% of any overshoot past the group cap survives.
            cap_lg = logit(cap)
            if med > cap_lg:
                med = cap_lg + 0.25 * (med - cap_lg)
            med = max(med, logit(0.01))
            s_fit = own_resid[i] * math.sqrt(1.0 + horizon_days / span_days)
            s = math.sqrt(s_fit ** 2 + s_refresh ** 2 + SPREAD_FLOOR ** 2)
            s = min(max(s, s_min), s_max)
        else:
            # Never observed: group prior, middling spread.
            med = logit(cap * 0.5) if group != "intro" else logit(99.99)
            s = (s_min + s_max) / 2.0 if s_max > 0 else 1.0
        med_logit[i] = med
        spread[i] = s

    # The 100% trophy is data-driven too: any trophy at 100% in the last
    # read is the intro anomaly, whatever its description says.
    if states:
        last_rates = states[-1][2]
        for i in range(n_tr):
            if last_rates[i] is not None and last_rates[i] >= 99.99:
                med_logit[i] = logit(99.99)

    # Monotonicity on medians: story chain, then platinum/completion.
    chain = []
    for i, t in enumerate(trophies):
        desc = t.get("description", "") or ""
        if "Complete Chapter 1." in desc:
            chain.append((1, i))
        elif "Complete Chapter 2." in desc:
            chain.append((2, i))
        elif "Complete Chapter 3." in desc:
            chain.append((3, i))
        elif "Complete Chapter 4." in desc:
            chain.append((4, i))
        elif desc == "Complete the final mission.":
            chain.append((5, i))
    chain.sort()
    idxs = [i for _, i in chain]
    # Enforce Ch1 >= Ch2 >= Ch3 >= Ch4 >= final: cap each later chapter at
    # the one before it (a later chapter must never forecast above an
    # earlier one; the earlier values are left untouched).
    for k in range(len(idxs) - 1):
        if med_logit[idxs[k + 1]] > med_logit[idxs[k]]:
            med_logit[idxs[k + 1]] = med_logit[idxs[k]]
    plat_i = next(
        (i for i, t in enumerate(trophies) if t.get("tier") == "platinum"), None
    )
    comp_i = next(
        (
            i
            for i, t in enumerate(trophies)
            if "Attain 100% Completion." in (t.get("description", "") or "")
        ),
        None,
    )
    intro_idx = {
        i
        for i in range(n_tr)
        if states and states[-1][2][i] is not None and states[-1][2][i] >= 99.99
    }
    if comp_i is not None:
        others = [
            med_logit[i]
            for i in range(n_tr)
            if i != comp_i and i != plat_i and i not in intro_idx
        ]
        if others:
            med_logit[comp_i] = min(med_logit[comp_i], min(others))
    if plat_i is not None and comp_i is not None:
        med_logit[plat_i] = min(med_logit[plat_i], med_logit[comp_i])

    # TWEAK2 (a): minimax blend — pull the extrapolated median toward the
    # last observed rate (persistence), the B-world median proxy. The 100%
    # trophy is untouched (last rate 100); trophies with no last rate keep
    # their fitted median.
    if states and BLEND_ALPHA > 0.0:
        last_rates = states[-1][2]
        for i in range(n_tr):
            r = last_rates[i]
            if r is None or r >= 99.99:
                continue
            med_logit[i] = (1.0 - BLEND_ALPHA) * med_logit[i] + BLEND_ALPHA * logit(r)

    rows = []
    for i, trophy in enumerate(trophies):
        group = groups[i][0]
        med = med_logit[i]
        s = spread[i]
        qs = []
        for z in Z:
            if group == "intro" or i in intro_idx:
                s_use = INTRO_DOWN if z < 0 else (INTRO_UP if z > 0 else 0.0)
                lg = med + z * s_use if z != 0 else med
            else:
                lg = med + z * s
            qs.append(round4(clamp_pct(100.0 * sigmoid(lg))))
        # Enforce non-decreasing after rounding (rounding can tie, never fall).
        for k in range(1, 5):
            if qs[k] < qs[k - 1]:
                qs[k] = qs[k - 1]
        rows.append({"id": trophy["id"], "q": qs})
    return {"trophies": rows}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(INPUT_DIR.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        forecast = forecast_case(case, path.name)
        (OUTPUT_DIR / f"{path.stem}.out").write_text(
            json.dumps(forecast, separators=(",", ":")) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
