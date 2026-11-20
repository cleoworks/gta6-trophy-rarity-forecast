"""gta6-trophy-rarity-forecast-01: forecast Exophase GTA VI trophy earn rates.

Model v7 (tweak round 13, frozen-mode alignment, sealed 2026-11-20):
the v6 engine (described below) with its frozen-regime mode aligned
to the measured launch->S1 transition statistics at full precision
(results/experiments-tweak13.md): (i) frozen spreads are the measured
per-group residual dispersions with no floor (ch1 0.0051, chain
0.0043, fishing 0.0024, platgrind 0.2188, other 0.2022), (ii) the
100% trophy is flat at its median in frozen mode (its measured
transition dispersion is exactly zero), and (iii) frozen component
medians apply the measured group-median rate ratios (FROZEN_F) as
rate ratios -- logit(rate x f) -- instead of logit-space shifts,
with the story chain sharing one base median. Outside frozen mode
the output is byte-identical to v6. Measured: practice 0.0839 ->
0.0739, coverage 0.945, real1/real2/mean6 unchanged.

Model v6 (tweak round 12, frozen-regime mode, sealed 2026-11-20): the
v5 engine (described below) plus ONE change -- a frozen-regime mode
for cases whose history never refreshed. Implemented from the written
design in results/experiments-tweak12.md on top of the v5 code. The
v5 layer is the round-11 design "s3": the v4 engine (t9_mix) plus an
upward-jump (surge) component in the scenario mixture, implemented
fresh from results/experiments-tweak11.md on top of the v4 code, whose
design is results/experiments-tweak9.md (+ experiments-tweak7.md §
Desain t7, experiments-tweak6.md § Desain t6, research-exophase.md §3).

Base engine (t7_both control):
  - Rate is earners over tracked players: r = E / N. Distinct page states
    only (first-seen time each); E_i(t) = round(rate * N / 100).
  - Tracked players N: log-time fit ln N vs x = ln(1 + (t - launch)/18h),
    recency weights 1+j, DAMPED extrapolation (L = 1.0):
    ln N_tgt = ln N_last + slope * L * (1 - exp(-(x_tgt - x_last)/L)),
    slope floored at 0, N_tgt >= N_last. s_N = fit residual scaled by
    sqrt(1 + horizon_days / span_days).
  - Earners E per trophy: log-time fit of ln E over the last 24h of
    distinct states (fallback: all states), E <= 0 points skipped, slope
    shrunk toward the group mean (SHRINK_K = 2), slope floored at 0,
    intercept refit, E_tgt >= E_last, E_tgt capped at group cap x N_tgt.
    Fewer than 2 usable E points: E_tgt = E_last, s_E = 0. A trophy never
    observed falls back to its group prior (median cap/2, mid-band spread).
  - Median m0 = logit(100 * E_tgt / N_tgt); spread
    s = sqrt(s_E^2 + s_N^2 + 0.5^2) clamped to the per-group band, then
    s x 0.7 symmetric (combo1). Story q05/q25 are widened x1.5 in logit
    around q50 after the mixture bisection (down15-story).
  - Blend alpha = 0.35: m0 (logit) pulled 35% toward logit(last rate)
    BEFORE the mixture; the 100% trophy is untouched.
  - Monotonicity (story chain Ch1 >= Ch2 >= Ch3 >= Ch4 >= final;
    platinum <= 100%-completion <= every other trophy) is enforced on m0
    and on every mixture component median.
  - The intro trophy ("Complete Gone Fishing.") and any trophy at 100% in
    the last read keep the v3 treatment: median ~99.99, downward-only
    spread INTRO_DOWN = 4.76 (q05 ~80%), no mixture.

Transition factors (per transition group: ch1 / chain / fishing /
platgrind / other; intro excluded, factor 1.0):
  - A jump event is a pair of consecutive distinct states with
    N ratio >= 2.0 AND median rate ratio <= 0.75. f_g = median rate ratio
    over the group's trophies at the LAST event (floored at 0.01);
    J_N = that event's N ratio.
  - No event, frozen history (1 distinct state): the launch->S1 priors
    (Ch1 0.39, chain 0.21, fishing 0.57, plat/grind/completion 0.16,
    strand/activity 0.19), J_N = 6.06.
  - No event, smooth growth: uniform f = 1/3, J_N = 3.0.

Scenario mixture (the round-9 change): components k = 0..5 jumps in the
horizon (tail > 5 folded into k = 5), component median
m_k = m0 - shift_k, shift_k = max(0, c_k * (-ln f_g) - g),
g = ln(N_tgt / N_last) (the K2 correction: only the part of a transition
the trend has not already assumed can shift the median).
  - Damping: c_k = rho^n_past * (1 - rho^k) / (1 - rho), c_0 = 0, where
    n_past = jumps already in the history and rho = median over groups of
    ln(f_last)/ln(f_prev) when the history holds >= 2 jumps, else
    RHO_PRIOR = 0.689.
  - Weights (hurdle): w_0 = 1 - P1; w_k = P1 * Poisson(mu_eff; k) /
    (1 - Poisson(mu_eff; 0)) for k >= 1, with mu = horizon_hours / 7.0
    and mu_eff = mu * exp(-horizon_hours / 48).
  - P1 is the t7 event engine: p_raw = 1 - exp(-dt/7), dt = target minus
    last history read (hours); if the interval contains a 04:00 UTC
    instant, p_raw = max(p_raw, 0.8), else p_raw *= 0.03 (the measured
    gate; the written t5/t6 design said 0.08, the measured implementation
    behaves as 0.03); P1 = p_raw * exp(-horizon_hours / 48).
  - Mixture quantiles by CDF bisection, 60 iterations, logit bracket
    [-12, 12]; per-component spread = control spread.

Surge components (the round-11 change): a transition group whose last
jump factor f_g > 1 is an UP group; its components k >= 1 are
m_k = m0 + k * min(ln f_g, ln 2) instead of crash components -- UNDAMPED
(no c_k, no rho: the rho calibrated on downward jumps proved too strong
for upward jumps) and with NO g subtraction (the K2 overlap for upward
jumps is the E-trend slope, which under-extrapolates steps; subtracting
g would zero the surge, exactly the round-7 K2 pattern). The ln 2 cap
keeps one more jump from more than doubling a group's rate; it binds
only in the final case (the observed up-factors 5.6x/10.9x are one-time
public-wave onboarding, not a repeating pattern). Direction is decided
per group from the case's own last jump (in-case factor, frozen prior,
or smooth 1/3), never from any target. DOWN groups, the intro treatment,
spread, blend and hurdle weights are exactly v4.

Frozen-regime mode (the round-12 change): when the case history holds
<= 1 distinct page state AND the interval (last read, target] contains
a 04:00 UTC instant, the page demonstrably did not refresh during the
observation window and the daily refresh falls inside the horizon. In
that regime (i) the no-jump mixture component is dropped (weights
renormalized over k >= 1), (ii) every jump component collapses to the
prior point forecast m0 + ln f_g (the launch->S1 per-group factor
already used for frozen histories; the multi-jump damping ladder
models >= 2 refreshes inside the horizon, which the observed >= 4.5 h
refresh cadence makes negligible at 90 minutes), (iii) the spread is
the measured launch->S1 residual dispersion per transition group
(FROZEN_SIGMA, same public-snapshot provenance as PRIOR_F; the 0.05
floor is the 2-dp rate-quantization scale) and the story down15
widening is off, and (iv) the persistence blend is skipped. Outside
this regime the output is byte-identical to v5 (verified on all
measurement sets: the detector cannot fire on a history containing a
jump, so the final case -- whose history holds several refreshes --
is unaffected). Measured (results/experiments-tweak12.md): practice
0.2530 -> 0.0839, real1/real2/mean6 unchanged.

Measured for the v5 design (results/experiments-tweak11.md, 13 sets):
practice 0.2530, real1 0.2357, real2 0.5139, gen1 0.1841/0.6368/0.2391,
gen2 0.1749/0.6629/0.2509, mean6 0.3581, worst13 0.7949,
PRAK 0.2861/0.4687/0.1434/0.7949, coverage 0.982. Byte-identical to v4
on 12/13 sets (the surge cannot fire where every f_g <= 1); on real2 it
moves only the two UP-group trophies (Chapter 1, fishing). Sealed as v5
under the user's re-evaluated acceptance frame (headline + mean6,
decision 2026-11-20 16:43 WIB), under which it weakly dominates v4 on
every aggregate (practice/real1/mean6 identical, real2 0.5139 vs
0.5427).

Round 14 (v8) leaves the non-frozen machinery untouched and fixes the
one regime the frozen mode mishandled: a frozen history with a LONG
horizon. v7's frozen point assumed exactly one more dilution whatever
the horizon, so on a 30.8 h frozen backtest (launch reads -> S3) 53 of
55 truths fell outside the band and the loss was 1.99. v8 compounds
the measured factor by the hurdle's own expected jump count EK_f and
widens the frozen band by the jump-count level uncertainty
|ln F| * sd_K, both gated to frozen horizons over 24 h: that backtest
drops to 0.68 while practice and every other measured set stay
byte-identical to v7 (results/experiments-tweak14.md).

Round 15 (v9) adds one gated change at the quantile stage: when the
case's own last transition contains NO up group (every transition
factor f_g <= 1), the upper mixture quantiles are tightened toward
q50 (logit deviations of q75/q95 x 0.80). The observed transition
process is asymmetric -- downward dilution is the violent,
fat-tailed direction, while upward moves are either trend-following
(already in the median via the earner fit) or concentrated surges
that the surge components already price when a case shows an up
group. Where no up group is on record, the symmetric upper tail
double-counts generic upside risk; the lower half of the band,
which carries all the dilution insurance, is untouched. Measured
(results/experiments-tweak15.md): gen1 A 0.1841 -> 0.1713, gen2 A
0.1749 -> 0.1642, mean6 0.3581 -> 0.3498, the B worlds improve too;
realL1 pays +0.0147 (inside the pre-registered +0.02 tolerance);
practice, real2 and realL2 are byte-identical to v8 (frozen mode /
surge gate). The final case's last observed transition contains up
groups (Chapter 1, fishing), so its forecast is unchanged from v8.

Round 16 (v10) adds one information-gated term at the median
stage, in non-frozen mode only: a story-chain progression flow.
When the case history is sparse (<= 5 distinct states) and holds
at least one detected jump, each story trophy after the first in
id order receives half (kappa = 0.50, ramped in over the first
8.5 h of horizon) of its predecessor's projected earner surplus
over its own projection, computed from base projections with no
cascade. The observed transitions put the whole chapter
increment on the single position behind the large reservoir
(S1->S2 frontier conversion 0.50; zero-gap positions did not
move; the frontier advanced one chapter per transition), while
in rich histories the per-trophy trends already identify the
chain (measured story medians calibrated), so the term stays
off there. Measured (results/experiments-tweak16.md): realL1
0.8479 -> 0.8333, real2 0.5139 -> 0.4994, real1 0.2356 ->
0.2311, entirely through Chapter 2, the frontier trophy;
practice, realL2, both gen batteries and PRAK are byte-identical
to v9. Scope honesty: the final case's history is sparse with
jumps, so this term DOES fire there -- it is the first change
since v5 whose final-case forecast differs from its predecessor,
in the direction the two observed transitions support.

Nothing here reads the network; output is deterministic.
Quantiles are clamped to 0.01..99.99, non-decreasing, rounded to 4
decimals half-up (same rounding as the starter).
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

# Launch: the house curve's origin (RULES: ln(1 + hours from 2026-11-19T00:00Z)).
LAUNCH = datetime(2026, 11, 19, 0, 0, 0, tzinfo=timezone.utc)
TAU_HOURS = 18.0

SHRINK_K = 2.0
SPREAD_FLOOR = 0.5
BLEND_ALPHA = 0.35
INTRO_DOWN = 4.76
INTRO_UP = 0.5

# N-model damping length (in x units) and mixture machinery constants.
N_DAMP_L = 1.0
SPREAD_SYM = 0.7
DOWN15 = 1.5
EVENT_N_RATIO = 2.0
EVENT_RATE_RATIO = 0.75
HAZARD_HOURS = 7.0
DECAY_HOURS = 48.0
WINDOW_BOOST = 0.8
GATE_MULT = 0.03
RHO_PRIOR = 0.689
SURGE_CAP_LN = math.log(2.0)  # v5: per-component cap on the surge ln-factor
FROZEN_SIGMA = {  # round 13: launch->S1 residual dispersion (logit)
    # per transition group at full measured precision (diag_r13.py; the
    # round-12 table floored the three exact groups at 0.05). RMS is
    # measured around the prior point forecasts (the diag R-d residuals)
    # and kept for every frozen variant: re-measuring around the
    # median-ratio points gives 0.0000 for the exact groups -- an
    # artifact of fitting center and width to the same single
    # transition, and a coverage trap (see experiments-tweak13.md (f)).
    "ch1": 0.0051,
    "chain": 0.0043,
    "fishing": 0.0024,
    "platgrind": 0.2188,
    "other": 0.2022,
    "intro": 0.0,
}
FROZEN_F = {  # round 13: measured group-median launch->S1 rate ratios
    # (diag_r13.py, same public snapshot pair as PRIOR_F -- the priors
    # are these ratios rounded to 2 decimals). Used only by the g3
    # frozen point construction, applied as rate ratios.
    "ch1": 0.392,
    "chain": 0.209091,
    "fishing": 0.568627,
    "platgrind": 0.162698,
    "other": 0.180851,
    "intro": 1.0,
}
J_N_PRIOR = 6.06
J_N_SMOOTH = 3.0
F_SMOOTH = 1.0 / 3.0
F_FLOOR = 0.01

# Launch->S1 transition priors per transition group (research-exophase §3).
PRIOR_F = {
    "ch1": 0.39,
    "chain": 0.21,
    "fishing": 0.57,
    "platgrind": 0.16,
    "other": 0.19,
    "intro": 1.00,
}

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


def phi(z: float) -> float:
    """Standard normal CDF."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def median(vals):
    s = sorted(vals)
    n = len(s)
    if n == 0:
        return None
    if n % 2 == 1:
        return s[n // 2]
    return 0.5 * (s[n // 2 - 1] + s[n // 2])


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


def transition_group(trophy: dict, group: str) -> str:
    """Coarser grouping used ONLY for transition factors (round-7 design):
    ch1 / chain / fishing / platgrind / other; intro stands apart."""
    desc = trophy.get("description", "") or ""
    if group == "intro":
        return "intro"
    if "Complete Chapter 1." in desc:
        return "ch1"
    if group == "story":
        return "chain"
    if "fishing" in desc.lower():
        return "fishing"
    if group in ("plat", "completion", "grind"):
        return "platgrind"
    return "other"


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


def enforce_monotone(med, trophies, intro_idx):
    """Story chain non-increasing; platinum <= completion <= all others.

    Operates on a copy of a median vector (used for m0 and for every
    mixture component median)."""
    med = list(med)
    n_tr = len(med)
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
    for k in range(len(idxs) - 1):
        if med[idxs[k + 1]] > med[idxs[k]]:
            med[idxs[k + 1]] = med[idxs[k]]
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
    if comp_i is not None:
        others = [
            med[i]
            for i in range(n_tr)
            if i != comp_i and i != plat_i and i not in intro_idx
        ]
        if others:
            med[comp_i] = min(med[comp_i], min(others))
    if plat_i is not None and comp_i is not None:
        med[plat_i] = min(med[plat_i], med[comp_i])
    return med


def contains_0400(start: datetime, end: datetime) -> bool:
    """True when some date's 04:00 UTC instant lies in (start, end]."""
    day = start.date()
    last_day = end.date()
    while day <= last_day:
        instant = datetime(day.year, day.month, day.day, 4, 0, 0,
                           tzinfo=timezone.utc)
        if start < instant <= end:
            return True
        day += timedelta(days=1)
    return False


def forecast_case(case: dict, name: str) -> dict:
    trophies = case["trophies"]
    history = case.get("history") or []
    horizon_hours = case["horizon_minutes"] / 60.0
    horizon_days = case["horizon_minutes"] / 1440.0
    target = parse_time(case["target"])
    x_target = x_of(target)
    n_tr = len(trophies)

    groups = [classify(t) for t in trophies]
    tgroups = [transition_group(t, groups[i][0]) for i, t in enumerate(trophies)]

    states = distinct_reads(history)

    # ---- Frozen-regime detection (round 12) ----
    # Frozen history (<= 1 distinct state) whose horizon contains the
    # daily 04:00 UTC refresh instant: the refresh is the expected
    # event, not a 22.5%-weighted tail branch.
    if history:
        last_read_t0 = parse_time(history[-1]["at"])
    else:
        last_read_t0 = target - timedelta(hours=horizon_hours)
    frozen_mode = len(states) <= 1 and contains_0400(last_read_t0, target)
    # Round 14 (h1f): frozen jump-count statistics (expected count and
    # its sd under the hurdle weights, frozen renormalization applied),
    # for the long-horizon frozen edits. Zero when not frozen.
    ek_f = 0.0
    sd_k = 0.0
    if frozen_mode:
        _dt = (target - last_read_t0).total_seconds() / 3600.0
        _pr = 1.0 - math.exp(-_dt / HAZARD_HOURS) if _dt > 0 else 0.0
        if contains_0400(last_read_t0, target):
            _pr = max(_pr, WINDOW_BOOST)
        else:
            _pr *= GATE_MULT
        _p1f = min(max(_pr * math.exp(-horizon_hours / DECAY_HOURS), 0.0), 1.0)
        _mu = (horizon_hours / HAZARD_HOURS) * math.exp(
            -horizon_hours / DECAY_HOURS)

        def _pois2(k, m):
            return math.exp(-m) * (m ** k) / math.factorial(k)

        _den = 1.0 - _pois2(0, _mu)
        if _den > 1e-12:
            _ws = [1.0 - _p1f] + [
                _p1f * _pois2(k, _mu) / _den for k in range(1, 5)
            ] + [_p1f * (1.0 - sum(_pois2(k, _mu) for k in range(0, 5))) / _den]
        else:
            _ws = [1.0] + [0.0] * 5
        _rest = sum(_ws[1:])
        if _rest > 1e-12:
            _ws = [0.0] + [w / _rest for w in _ws[1:]]
        else:
            _ws = [0.0, 1.0, 0.0, 0.0, 0.0, 0.0]
        ek_f = sum(k * w for k, w in enumerate(_ws))
        sd_k = math.sqrt(max(
            sum((k ** 2) * w for k, w in enumerate(_ws)) - ek_f ** 2, 0.0))
    frozen_pow = ek_f if (frozen_mode and horizon_hours > 24.0) else 1.0

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

    # ---- Model N: damped log-time fit over distinct states ----
    if states:
        n_last = states[-1][1]
        x_last_state = x_of(states[-1][0])
    else:
        n_last = 0
        x_last_state = x_target
    n_pts = [
        (x_of(t), math.log(n), 1.0 + j)
        for j, (t, n, _) in enumerate(states)
        if n and n > 0
    ]
    slope_n, _, resid_n = wls(n_pts)
    if slope_n is None:
        slope_n = 0.0
        resid_n = 0.0
    slope_n = max(slope_n, 0.0)
    if n_last and n_last > 0:
        dx = x_target - x_last_state
        ln_n_tgt = math.log(n_last) + slope_n * N_DAMP_L * (
            1.0 - math.exp(-dx / N_DAMP_L)
        )
        n_tgt = max(math.exp(ln_n_tgt), float(n_last))
    else:
        n_tgt = 0.0
    if len(states) >= 2:
        span_n_days = max(
            (states[-1][0] - states[0][0]).total_seconds() / 86400.0, 0.25
        )
    else:
        span_n_days = 0.25
    s_n = resid_n * math.sqrt(1.0 + horizon_days / span_n_days)
    g_trend = math.log(n_tgt / n_last) if (n_last and n_tgt) else 0.0

    # ---- E fit window: last 24h of distinct states ----
    if len(states) >= 2:
        window_start = states[-1][0] - timedelta(hours=24)
        fit_states = [s for s in states if s[0] >= window_start]
        if len(fit_states) < 2:
            fit_states = states
    else:
        fit_states = states
    if len(fit_states) >= 2:
        span_e_days = max(
            (fit_states[-1][0] - fit_states[0][0]).total_seconds() / 86400.0,
            0.25,
        )
    else:
        span_e_days = 0.25

    # Per-trophy earner series over the fit window + last observed earners.
    e_points = []
    e_last = [None] * n_tr
    observed = [False] * n_tr
    for i in range(n_tr):
        pts = []
        for j, (t, n, rates) in enumerate(fit_states):
            r = rates[i]
            if r is None or not n:
                continue
            e = round(r * n / 100.0)
            if e >= 1:
                pts.append((x_of(t), math.log(e), 1.0 + j))
        e_points.append(pts)
        for (t, n, rates) in reversed(states):
            r = rates[i]
            if r is not None:
                observed[i] = True
                e_last[i] = round(r * n / 100.0) if n else 0
                break

    own_slope = [None] * n_tr
    own_resid = [0.0] * n_tr
    for i in range(n_tr):
        s, _, resid = wls(e_points[i])
        own_slope[i] = s
        own_resid[i] = resid
    group_slope = {}
    for gname in {g[0] for g in groups}:
        num = 0.0
        den = 0.0
        for i in range(n_tr):
            if groups[i][0] == gname and own_slope[i] is not None:
                w = len(e_points[i])
                num += w * own_slope[i]
                den += w
        group_slope[gname] = (num / den) if den > 0 else 0.0

    # ---- Base medians m0 (pre-blend) and control spreads ----
    med0 = [0.0] * n_tr
    spread = [0.0] * n_tr
    for i in range(n_tr):
        group, cap, s_min, s_max = groups[i]
        pts = e_points[i]
        if not observed[i] or not n_tgt:
            # Never observed: group prior, middling spread.
            med = logit(cap * 0.5) if group != "intro" else logit(99.99)
            s = (s_min + s_max) / 2.0 if s_max > 0 else 1.0
        elif len(pts) < 2:
            # Too few usable earner points: persist last earners.
            e_tgt = float(e_last[i] or 0)
            med = logit(100.0 * e_tgt / n_tgt)
            s = math.sqrt(s_n ** 2 + SPREAD_FLOOR ** 2)
            s = min(max(s, s_min), s_max) if s_max > 0 else s
        else:
            if own_slope[i] is not None:
                b = (
                    len(pts) * own_slope[i] + SHRINK_K * group_slope[group]
                ) / (len(pts) + SHRINK_K)
            else:
                b = group_slope[group]
            b = max(b, 0.0)
            sw = sum(w for _, _, w in pts)
            a = sum(w * (y - b * x) for x, y, w in pts) / sw
            e_tgt = math.exp(a + b * x_target)
            e_tgt = max(e_tgt, float(e_last[i] or 0))
            e_tgt = min(e_tgt, cap / 100.0 * n_tgt)
            med = logit(100.0 * e_tgt / n_tgt)
            s_e = own_resid[i] * math.sqrt(1.0 + horizon_days / span_e_days)
            s = math.sqrt(s_e ** 2 + s_n ** 2 + SPREAD_FLOOR ** 2)
            s = min(max(s, s_min), s_max) if s_max > 0 else s
        med0[i] = med
        spread[i] = s * SPREAD_SYM

    # The 100% trophy is data-driven: any trophy at >=99.99% in the last
    # distinct state is the intro anomaly, whatever its description says.
    intro_idx = set()
    if states:
        last_rates = states[-1][2]
        for i in range(n_tr):
            if last_rates[i] is not None and last_rates[i] >= 99.99:
                intro_idx.add(i)
                med0[i] = logit(99.99)

    # ---- Blend alpha 0.35 toward persistence (on m0, before mixture) ----
    if states and BLEND_ALPHA > 0.0 and not frozen_mode:
        last_rates = states[-1][2]
        for i in range(n_tr):
            r = last_rates[i]
            if r is None or r >= 99.99:
                continue
            med0[i] = (1.0 - BLEND_ALPHA) * med0[i] + BLEND_ALPHA * logit(r)

    # ---- Monotonicity on m0 ----
    med0 = enforce_monotone(med0, trophies, intro_idx)
    if frozen_mode:
        for i in range(n_tr):
            if horizon_hours > 24.0:
                # Round 14 (h1f): at long horizons the number of
                # compounding dilutions is itself uncertain; the
                # band must carry that level uncertainty.
                spread[i] = math.sqrt(
                    FROZEN_SIGMA[tgroups[i]] ** 2
                    + (abs(math.log(FROZEN_F[tgroups[i]])) * sd_k) ** 2
                )
            else:
                spread[i] = FROZEN_SIGMA[tgroups[i]]

    # ---- Transition events, factors, damping ----
    events = []  # (J_N, {tgroup: f_g}, overall median ratio)
    for k in range(len(states) - 1):
        _, n0, r0 = states[k]
        _, n1, r1 = states[k + 1]
        if not n0 or n1 / n0 < EVENT_N_RATIO:
            continue
        ratios_all = []
        per_group = {}
        for i in range(n_tr):
            if tgroups[i] == "intro":
                continue
            a, b = r0[i], r1[i]
            if a is None or b is None or a <= 0:
                continue
            ratio = b / a
            ratios_all.append(ratio)
            per_group.setdefault(tgroups[i], []).append(ratio)
        if not ratios_all:
            continue
        overall = median(ratios_all)
        if overall is not None and overall <= EVENT_RATE_RATIO:
            fmap = {}
            for gname, vals in per_group.items():
                fmap[gname] = max(median(vals), F_FLOOR)
            events.append((n1 / n0, fmap, max(overall, F_FLOOR)))

    n_past = len(events)
    if events:
        j_n = events[-1][0]
        fmap_last = events[-1][1]
        overall_last = events[-1][2]
        f_per = [
            1.0 if tgroups[i] == "intro"
            else fmap_last.get(tgroups[i], overall_last)
            for i in range(n_tr)
        ]
    elif len(states) <= 1:
        j_n = J_N_PRIOR
        f_per = [PRIOR_F[tgroups[i]] for i in range(n_tr)]
    else:
        j_n = J_N_SMOOTH
        f_per = [F_SMOOTH] * n_tr
    _ = j_n  # J_N is part of the design record; the mixture uses f and g.

    if len(events) >= 2:
        f_last = events[-1][1]
        f_prev = events[-2][1]
        rho_vals = []
        for gname, fv in f_last.items():
            pv = f_prev.get(gname)
            if pv is not None and 0.0 < pv < 1.0 and 0.0 < fv < 1.0:
                rho_vals.append(math.log(fv) / math.log(pv))
        rho = median(rho_vals) if rho_vals else RHO_PRIOR
    else:
        rho = RHO_PRIOR

    def c_of(k: int) -> float:
        if k == 0:
            return 0.0
        base = rho ** n_past
        if abs(1.0 - rho) < 1e-12:
            return base * k
        return base * (1.0 - rho ** k) / (1.0 - rho)

    # ---- Event engine P1 (t7) ----
    if history:
        last_read_t = parse_time(history[-1]["at"])
    else:
        last_read_t = target - timedelta(hours=horizon_hours)
    dt_hours = (target - last_read_t).total_seconds() / 3600.0
    p_raw = 1.0 - math.exp(-dt_hours / HAZARD_HOURS) if dt_hours > 0 else 0.0
    if contains_0400(last_read_t, target):
        p_raw = max(p_raw, WINDOW_BOOST)
    else:
        p_raw *= GATE_MULT
    p1 = min(max(p_raw * math.exp(-horizon_hours / DECAY_HOURS), 0.0), 1.0)

    # ---- Hurdle weights over jump counts k = 0..5 (tail folded) ----
    mu = horizon_hours / HAZARD_HOURS
    mu_eff = mu * math.exp(-horizon_hours / DECAY_HOURS)

    def pois(k: int, m: float) -> float:
        return math.exp(-m) * (m ** k) / math.factorial(k)

    denom = 1.0 - pois(0, mu_eff)
    weights = [1.0 - p1]
    if denom > 1e-12:
        for k in range(1, 5):
            weights.append(p1 * pois(k, mu_eff) / denom)
        tail = 1.0 - sum(pois(k, mu_eff) for k in range(0, 5))
        weights.append(p1 * tail / denom)
    else:
        weights += [0.0] * 5
    if frozen_mode:
        rest = sum(weights[1:])
        if rest > 1e-12:
            weights = [0.0] + [w / rest for w in weights[1:]]
        else:
            weights = [0.0, 1.0, 0.0, 0.0, 0.0, 0.0]

    # ---- Round 16 (m1): story-chain progression flow, gated ----
    # Design: results/experiments-tweak16.md. In sparse post-jump
    # histories the frontier chapter's near-term earners are
    # predicted better by its predecessor's projected stock (the
    # reservoir) than by its own floor-bound trend: on the observed
    # transitions the whole chapter increment landed on the single
    # position behind the large reservoir (S1->S2 frontier
    # conversion 0.50 at 8.5 h; zero-gap positions did not move),
    # and the frontier moved one chapter per transition -- hence
    # base projections only, no cascade. Rich histories (>= 6
    # distinct states) identify the per-trophy trends directly
    # (measured story medians there are already calibrated), so
    # the term stays off there; frozen mode is untouched.
    if not frozen_mode and n_past >= 1 and len(states) <= 5 and n_tgt:
        seq = [i for i in range(n_tr) if groups[i][0] == "story"]
        seq.sort(key=lambda i: trophies[i]["id"])
        base_e = {i: sigmoid(med0[i]) * n_tgt for i in seq}
        kappa = 0.5 * min(1.0, horizon_hours / 8.5)
        for pos in range(1, len(seq)):
            j = seq[pos]
            gap = base_e[seq[pos - 1]] - base_e[j]
            if gap > 0.0:
                e_new = base_e[j] + kappa * gap
                med0[j] = logit(100.0 * e_new / n_tgt)

    # ---- Component medians per trophy, monotonicity per component ----
    # v5 change (round-11 design "s3"): a group whose last jump factor
    # f_g > 1 is an UP group and gets surge components
    # m_k = m0 + k * min(ln f_g, ln 2) for k >= 1 -- UNDAMPED (no c_k, no
    # rho) and with NO g subtraction: the K2 overlap for upward jumps is
    # the E-trend slope, which under-extrapolates steps rather than
    # already assuming them (subtracting g would make the surge a no-op,
    # exactly the round-7 K2 pattern). DOWN groups keep the v4 crash
    # components exactly; k = 0 is m0 for every group.
    # Round 13 (g2+): story-cohort exactness in frozen mode. The chain
    # trophies share one earner count at both observed states of the
    # launch->S1 transition, so in frozen mode they share one base
    # median: the cohort's median last-earner count, reconstructed.
    frozen_chain_med0 = None
    if frozen_mode:
        _ch_e = [e_last[i] for i in range(n_tr)
                 if tgroups[i] == "chain" and e_last[i] is not None]
        if _ch_e and n_tgt:
            frozen_chain_med0 = logit(100.0 * median(_ch_e) / n_tgt)

    comp_meds = []  # comp_meds[k][i]
    raw_components = []
    for k in range(6):
        ck = c_of(k)
        vec = []
        for i in range(n_tr):
            f_i = min(max(f_per[i], F_FLOOR), 1e9)
            if k == 0:
                vec.append(med0[i])
            elif frozen_mode:
                _base = med0[i]
                if (frozen_chain_med0 is not None
                        and tgroups[i] == "chain"
                        and e_last[i] is not None):
                    _base = frozen_chain_med0
                # Round 13 (g3): the measured factors are RATE ratios;
                # apply them as rate ratios (logit of the product), not
                # as logit-space shifts (the add construction carries a
                # measured +0.009..+0.013 bias on the exact groups).
                vec.append(logit(clamp_pct(
                    100.0 * sigmoid(_base)
                    * FROZEN_F[tgroups[i]] ** frozen_pow)))
            elif f_i > 1.0:
                vec.append(med0[i] + k * min(math.log(f_i), SURGE_CAP_LN))
            else:
                shift = max(0.0, ck * (-math.log(f_i)) - g_trend)
                vec.append(med0[i] - shift)
        raw_components.append(vec)
    for k in range(6):
        comp_meds.append(enforce_monotone(raw_components[k], trophies, intro_idx))

    # ---- Quantiles ----
    rows = []
    for i, trophy in enumerate(trophies):
        group = groups[i][0]
        med = med0[i]
        s = spread[i]
        if group == "intro" or i in intro_idx:
            qs = []
            if frozen_mode:
                # Round 13: the measured launch->S1 dispersion of the
                # 100% trophy is exactly zero (100.00 -> 100.00, its
                # earners scaled with N exactly). FROZEN_SIGMA["intro"]
                # = 0.0, applied here: flat at the median in frozen
                # mode. Outside frozen mode the v3 treatment stands.
                qs = [round4(clamp_pct(100.0 * sigmoid(med)))] * 5
            else:
                for lev, z in zip(LEVELS, (-1.645, -0.674, 0.0, 0.674, 1.645)):
                    if z < 0:
                        lg = med + z * INTRO_DOWN
                    elif z > 0:
                        lg = med + z * INTRO_UP
                    else:
                        lg = med
                    qs.append(round4(clamp_pct(100.0 * sigmoid(lg))))
        else:
            meds_i = [comp_meds[k][i] for k in range(6)]

            def mix_cdf(x, meds=meds_i, ss=s):
                return sum(
                    w * phi((x - m) / ss) for w, m in zip(weights, meds)
                )

            qlog = []
            for tau in LEVELS:
                lo, hi = -12.0, 12.0
                for _ in range(60):
                    mid = 0.5 * (lo + hi)
                    if mix_cdf(mid) < tau:
                        lo = mid
                    else:
                        hi = mid
                qlog.append(0.5 * (lo + hi))
            if group == "story" and not frozen_mode:
                # down15-story: widen q05/q25 x1.5 in logit, anchored at q50.
                qlog[0] = qlog[2] - DOWN15 * (qlog[2] - qlog[0])
                qlog[1] = qlog[2] - DOWN15 * (qlog[2] - qlog[1])
            if not frozen_mode and not any(f > 1.0 for f in f_per):
                # Round 15 (k1): upper-tail tightening x0.80 around q50,
                # gated on no up-group in the case's own last transition
                # (design: results/experiments-tweak15.md).
                qlog[3] = qlog[2] + 0.8 * (qlog[3] - qlog[2])
                qlog[4] = qlog[2] + 0.8 * (qlog[4] - qlog[2])
            qs = [round4(clamp_pct(100.0 * sigmoid(v))) for v in qlog]
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
