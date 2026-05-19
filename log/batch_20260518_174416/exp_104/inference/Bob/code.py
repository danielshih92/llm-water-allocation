# ============================================================
# Experiment: exp_104
# Agent: Bob
# Source: exp_104
# ============================================================

# ============================================================
# Meta Round 1
# ============================================================

META_ROUND_1_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = day_context['day']

    alive_opps = [o for o in opponents_status.values() if o.get('alive')]

    # Base urgency from our health and no-water streak
    hp = int(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # If we are in danger, bid aggressively; otherwise bid moderately.
    danger = 0
    if hp <= 2:
        danger += 2
    elif hp <= 4:
        danger += 1
    if no_water_days >= 1:
        danger += 1

    # Estimate how many full requirements the supply can cover.
    # Use int indices safely: only for list indexing; here just compute thresholds.
    # Normalize supply to [0,1]
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5

    # If we can afford to be competitive, bid around a fraction of salary.
    # Higher supply -> slightly lower bid; lower supply -> slightly higher bid.
    scarcity_factor = 1.0 + (0.5 - supply_norm) * 0.35

    # No trace exploitation possible: use yesterday bids if present, but keep it robust.
    yesterday_bids = []
    for opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
    else:
        highest_prev_bid = 0.0

    # Target bid logic
    if danger >= 2:
        target = DAILY_SALARY * 0.65 * scarcity_factor
    elif danger == 1:
        target = DAILY_SALARY * 0.55 * scarcity_factor
    else:
        target = DAILY_SALARY * 0.45 * scarcity_factor

    # If opponents previously bid high, slightly outbid to secure water.
    if highest_prev_bid > 0:
        # If they were already near our salary fraction, we need to match/beat.
        if highest_prev_bid >= DAILY_SALARY * 0.70:
            target = max(target, highest_prev_bid + 2.0)
        elif highest_prev_bid >= DAILY_SALARY * 0.45:
            target = max(target, highest_prev_bid + 1.0)

    # Ensure we don't bid more than we can pay.
    bid = min(budget, target)

    # Also ensure bid is not trivially low; minimum to have a chance.
    min_bid = max(DAILY_SALARY * 0.25, WATER_REQ * 1.5)
    bid = max(min_bid, bid)

    # Final clamp
    if bid < 0:
        bid = 0.0
    return float(bid)
"""

# ============================================================
# Meta Round 2
# ============================================================

META_ROUND_2_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = day_context['day']

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opponents = []
    for opp in opponents_status.values():
        if opp.get('alive', False):
            alive_opponents.append(opp)

    # If no opponents alive, bid conservatively.
    if not alive_opponents:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace for immediate reaction.
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict) and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Base aggressiveness: higher when my HP is low or when supply is tight.
    supply_tightness = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_tightness = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_tightness = max(0.0, min(1.0, supply_tightness))

    hp_pressure = 0.0
    if my_hp <= 2:
        hp_pressure = 1.0
    elif my_hp <= 4:
        hp_pressure = 0.7
    elif my_hp <= 6:
        hp_pressure = 0.4
    else:
        hp_pressure = 0.2

    no_water_pressure = 0.0
    if my_no_water_days >= 2:
        no_water_pressure = 1.0
    elif my_no_water_days == 1:
        no_water_pressure = 0.5

    pressure = 0.55 * hp_pressure + 0.35 * no_water_pressure + 0.10 * supply_tightness

    # If someone previously bid extremely high, we must not get undercut.
    extreme_threshold = DAILY_SALARY * 0.85  # 76.5
    if highest_prev_bid >= extreme_threshold:
        target = DAILY_SALARY * (0.65 + 0.25 * pressure)
        # Slightly shadow the leader without matching exactly.
        target = max(target, min(my_budget, highest_prev_bid * 0.92))
    else:
        # Otherwise, bid enough to compete but preserve budget.
        target = DAILY_SALARY * (0.48 + 0.30 * pressure)
        # If my budget is low, cap target.
        target = min(target, DAILY_SALARY * 0.85)

    # Convert target into a safe bid: never exceed budget; keep non-negative.
    bid = max(0.0, min(my_budget, target))

    # If budget is extremely low, still bid a minimum to try to avoid starvation.
    if my_budget < 10.0:
        bid = max(0.0, min(my_budget, 8.0))

    return float(bid)
"""

# ============================================================
# Meta Round 3
# ============================================================

META_ROUND_3_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        # No competition: bid conservatively but ensure some chance to buy water
        return float(min(budget, DAILY_SALARY * 0.4))

    # Read only yesterday previous_trace bids from alive opponents
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Determine pressure from opponents' yesterday bids
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    avg_prev_bid = (sum(prev_bids) / len(prev_bids)) if prev_bids else 0.0

    # Base bid depends on my HP and consecutive no-water days
    # If I'm low HP or have gone multiple days without water, increase bid.
    if hp <= 2.0 or no_water_days >= 2:
        base = DAILY_SALARY * 0.85
    elif hp <= 4.0 or no_water_days == 1:
        base = DAILY_SALARY * 0.65
    else:
        base = DAILY_SALARY * 0.55

    # If opponents were bidding aggressively yesterday, we must match pressure.
    # Cindy's death implies some players may underbid; others bid enough to survive.
    # Use a capped reaction to avoid overspending.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # High pressure: bid near base but slightly above the observed high bid.
        target = max(base, highest_prev_bid * 1.02)
    else:
        # Moderate pressure: stay around avg/median-ish but not too high.
        target = max(base, avg_prev_bid * 0.95)

    # Also scale with supply: when supply is tighter (lower), increase bid.
    # supply in [15,25]
    supply_tightness = (float(MAX_SUPPLY) - supply) / float(MAX_SUPPLY - MIN_SUPPLY)  # 0..1
    target *= (1.0 + 0.20 * supply_tightness)

    # Final cap: never exceed budget; keep within a reasonable daily range
    # to avoid running out before end of episode.
    cap = min(budget, DAILY_SALARY * 1.10)
    bid = float(min(cap, max(1.0, target)))
    return bid
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    # Determine alive opponents and their yesterday bids
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict) and prev.get('bid') is not None:
            yesterday_bids.append(float(prev.get('bid', 0.0)))

    # Estimate scarcity: if supply is near lower bound, competition likely increases
    scarcity = (supply - 15.0) / (25.0 - 15.0) if (25.0 - 15.0) != 0 else 0.5
    is_scarce = scarcity < 0.45

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Baseline bid depends on our risk
    if hp <= 2 or no_water_days >= 2:
        target = DAILY_SALARY * 0.95
    elif hp <= 4 or no_water_days >= 1:
        target = DAILY_SALARY * 0.75
    else:
        target = DAILY_SALARY * (0.55 if not is_scarce else 0.70)

    # React to yesterday: if others paid heavily, we raise bid to avoid losing the water share
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids))

        # If the market cleared around/above our salary, match slightly below the highest to win efficiently
        if highest_prev_bid >= DAILY_SALARY * 0.85:
            if hp > 3:
                target = max(target, DAILY_SALARY * 0.80)
            else:
                target = max(target, DAILY_SALARY * 0.95)
        # If bids were moderate, bid around average if scarce
        elif is_scarce and avg_prev_bid >= DAILY_SALARY * 0.55:
            target = max(target, min(DAILY_SALARY * 0.75, avg_prev_bid + 5.0))

    # Keep within budget and avoid overbidding when budget is tight
    if budget <= 0.0:
        return 0.0

    bid = min(budget, target)

    # Small strategic bump on scarce days to beat same-tier bidders
    if is_scarce and hp > 2:
        bid = min(budget, bid + 5.0)

    # Ensure non-negative
    if bid < 0.0:
        bid = 0.0

    return float(bid)
"""

# ============================================================
# Meta Round 5
# ============================================================

META_ROUND_5_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive = []
    for agent_id, st in opponents_status.items():
        if st.get('alive', False):
            alive.append((agent_id, st))

    if not alive:
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Pressure from yesterday: how aggressively someone bid
    yesterday_bids = []
    for _, st in alive:
        prev = st.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    pressure = 0.0
    if yesterday_bids:
        # Use max as a proxy for current competitive intensity
        pressure = max(yesterday_bids)

    # If supply is low, allocate more to avoid missing water (higher chance to lose to Cindy-like bids)
    # If supply is high, we can underbid slightly and still secure water.
    supply_frac = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)  # 0..1-ish
    if supply_frac < 0:
        supply_frac = 0.0
    if supply_frac > 1:
        supply_frac = 1.0

    # Base bid target: mid range
    base = DAILY_SALARY * (0.45 + 0.25 * (1.0 - supply_frac))

    # React to yesterday pressure: if someone was bidding near/above 0.85 salary, raise bid
    if pressure >= DAILY_SALARY * 0.85:
        base *= 1.15
    elif pressure >= DAILY_SALARY * 0.65:
        base *= 1.05

    # Urgency from our HP/no-water days
    # If we're close to danger, bid more aggressively.
    if my_hp <= 2.5 or my_no_water_days >= 2:
        base = max(base, DAILY_SALARY * 0.9)
    elif my_hp <= 4.0 or my_no_water_days == 1:
        base = max(base, DAILY_SALARY * 0.65)

    # Keep bids within budget and avoid extreme overpaying
    # Also cap relative to pressure to avoid matching Cindy's very high bids unnecessarily.
    cap = DAILY_SALARY * 1.05
    if pressure > 0:
        cap = min(cap, pressure * 1.02)

    bid = float(min(my_budget, max(5.0, min(base, cap))))
    return bid
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = day_context['day']

    my_hp = int(my_status['hp'])
    my_budget = float(my_status['budget'])
    my_no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return float(min(my_budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids for immediate reaction
    prev_bids = []
    prev_by_opponent = {}
    for oid, o in opponents_status.items():
        if not o.get('alive', False):
            continue
        prev = o.get('previous_trace', {}) or {}
        bid = prev.get('bid', None)
        if bid is not None:
            try:
                bid_val = float(bid)
            except Exception:
                bid_val = None
            if bid_val is not None:
                prev_bids.append(bid_val)
                prev_by_opponent[oid] = bid_val

    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_highest_prev_bid = 0.0
    if len(prev_bids) >= 2:
        sorted_bids = sorted(prev_bids)
        second_highest_prev_bid = sorted_bids[-2]

    # Identify likely aggressive opponent from yesterday (highest bid)
    # If tie, just use highest_prev_bid.
    aggressive_pressure = 0.0
    if highest_prev_bid > 0:
        aggressive_pressure = min(1.0, highest_prev_bid / (DAILY_SALARY * 2.6))

    # If our hp is low or we've already had no water days, bid more.
    # If our hp is healthy, bid less to conserve budget against Cindy-like budgeted aggression.
    hp_risk = 0.0
    if my_hp <= 2:
        hp_risk = 1.0
    elif my_hp <= 4:
        hp_risk = 0.7
    elif my_hp <= 6:
        hp_risk = 0.4
    else:
        hp_risk = 0.2

    no_water_risk = 0.0
    if my_no_water_days >= 3:
        no_water_risk = 1.0
    elif my_no_water_days == 2:
        no_water_risk = 0.6
    elif my_no_water_days == 1:
        no_water_risk = 0.3
    else:
        no_water_risk = 0.1

    risk = 0.65 * hp_risk + 0.35 * no_water_risk

    # Supply scaling: higher supply reduces need to overbid.
    # Normalize supply within [MIN_SUPPLY, MAX_SUPPLY]
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    else:
        supply_norm = 0.5
    supply_norm = max(0.0, min(1.0, supply_norm))

    # Base target bid: mid-high when risk is high; otherwise moderate.
    # Also slightly discount when aggressive_pressure is high to avoid bidding into Cindy's likely dominance.
    discount = 0.85 if aggressive_pressure >= 0.55 else 1.0

    # Target fraction of daily salary
    # When risk high: ~0.78*salary; when low: ~0.45*salary
    target_frac = (0.45 + 0.33 * risk) * discount

    # If yesterday had extremely high bids, nudge upward but not to chase.
    if highest_prev_bid >= DAILY_SALARY * 2.0:
        target_frac = max(target_frac, 0.62)

    # If our budget is tight, cap by what we can afford.
    raw_bid = DAILY_SALARY * target_frac

    # If supply is low, increase slightly.
    if supply_norm < 0.4:
        raw_bid *= 1.08

    # Ensure positive and within budget
    bid = float(max(0.0, min(my_budget, raw_bid)))

    # If we are extremely low on budget, bid minimal to survive: either 0 or a small fraction.
    if my_budget <= DAILY_SALARY * 0.15:
        bid = float(min(my_budget, DAILY_SALARY * 0.12))

    # Final safety: don't bid more than a reasonable cap tied to supply
    # (prevents overbidding when supply is abundant)
    max_reasonable = DAILY_SALARY * (0.95 if supply_norm < 0.7 else 0.75)
    bid = float(min(bid, max_reasonable, my_budget))

    return bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context.get('supply', 0.0)
    day = day_context.get('day', 0)

    # Safety checks
    my_budget = float(my_status.get('budget', 0.0))
    my_hp = float(my_status.get('hp', 0.0))
    my_no_water_days = int(my_status.get('no_water_days', 0))

    # If we are in immediate danger, bid aggressively but still bounded by budget.
    if my_hp <= 2 or my_no_water_days >= 2:
        return min(my_budget, DAILY_SALARY * 0.95)

    # Analyze yesterday bids from alive opponents to infer aggressiveness.
    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Baseline bid depends on supply: with more supply, we can bid lower yet still win.
    # supply is float, but we only use it for comparisons.
    supply_frac = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_frac = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        if supply_frac < 0:
            supply_frac = 0.0
        if supply_frac > 1:
            supply_frac = 1.0

    # If opponents were aggressive yesterday, slightly increase bid; otherwise stay conservative.
    if yesterday_bids:
        highest_prev_bid = max(yesterday_bids)
        # Cindy-like behavior: very high bids.
        if highest_prev_bid >= DAILY_SALARY * 1.2:
            # Still not matching; aim to secure water without burning budget.
            bid = DAILY_SALARY * (0.45 + 0.15 * supply_frac)
        elif highest_prev_bid >= DAILY_SALARY * 0.7:
            bid = DAILY_SALARY * (0.40 + 0.10 * supply_frac)
        else:
            bid = DAILY_SALARY * (0.35 + 0.08 * supply_frac)
    else:
        bid = DAILY_SALARY * (0.35 + 0.08 * supply_frac)

    # Ensure we don't bid more than budget.
    if my_budget <= 0:
        return 0.0

    # If budget is low, reduce further.
    budget_frac = my_budget / (DAILY_SALARY + 1e-9)
    if budget_frac < 0.4:
        bid = min(bid, my_budget * 0.9)

    # Final clamp.
    return float(min(my_budget, max(0.0, bid)))
"""

# ============================================================
# Meta Round 8
# ============================================================

META_ROUND_8_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opponents = [o for o in opponents_status.values() if o.get('alive', False)]
    if not alive_opponents:
        return float(min(budget, DAILY_SALARY * 0.4))

    # Extract yesterday bids from previous_trace only
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Pressure estimate from yesterday
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        sorted_b = sorted(yesterday_bids, reverse=True)
        second_prev_bid = float(sorted_b[1])

    # Determine risk: if I'm close to dying, I must bid more.
    # Typical water requirement is 9; if supply is near 15, competition is higher.
    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    # supply_ratio ~0 means scarce (15), ~1 means abundant (25)

    # Base bid: try to be competitive but not reckless.
    # When supply is scarce, raise baseline.
    scarce_factor = 1.0 + (1.0 - supply_ratio) * 0.35  # up to +35%

    # If highest opponent bid yesterday was high, they likely secure water; we should slightly overbid.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        if hp > 3.5 and no_water_days <= 1:
            target = (second_prev_bid if second_prev_bid > 0 else highest_prev_bid) + 2.0
        else:
            target = highest_prev_bid * 1.03
    else:
        # Moderate environment: bid around a fraction of salary scaled by scarcity
        target = DAILY_SALARY * 0.55 * scarce_factor
        if highest_prev_bid > 0:
            target = max(target, min(highest_prev_bid + 1.5, highest_prev_bid * 0.95 + 5.0))

    # Urgency override
    if hp <= 2.5:
        target = max(target, DAILY_SALARY * 0.9)
    elif no_water_days >= 2:
        target = max(target, DAILY_SALARY * 0.7)

    # Budget and day horizon control: later days bid more to convert remaining budget into survival.
    horizon_factor = 0.85 + (float(day) / 10.0) * 0.35  # day is 1..10 typically
    target *= horizon_factor

    # Final cap
    bid = float(min(budget, target))
    if bid < 0.0:
        bid = 0.0

    return bid
"""

# ============================================================
# Meta Round 9
# ============================================================

META_ROUND_9_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Determine alive opponents and yesterday bids
    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        # No contest: conserve budget
        return min(my_status['budget'], DAILY_SALARY * 0.45)

    yesterday_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    second_prev_bid = 0.0
    if len(yesterday_bids) >= 2:
        s = sorted(yesterday_bids)
        second_prev_bid = s[-2]

    # Supply-based urgency: with supply in [15,25], 1 unit water likely means 2-3 days.
    # We need WATER_REQ=9; treat supply as total units available to allocate.
    # If supply is low, we must bid more to secure water.
    supply_tier = 0
    if supply <= (MIN_SUPPLY + MAX_SUPPLY) / 2.0:
        supply_tier = 1  # lower supply
    else:
        supply_tier = 2  # higher supply

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # If we're already in danger, bid aggressively but cap to budget.
    danger = (hp <= 2.5) or (no_water_days >= 2)

    # Undercut logic: if someone previously bid extremely high, we try a modest undercut.
    # Use thresholds relative to DAILY_SALARY.
    extreme = highest_prev_bid >= DAILY_SALARY * 1.6

    # Base bid targets
    if danger:
        target = DAILY_SALARY * (0.75 if supply_tier == 2 else 0.95)
    else:
        if extreme:
            # Underbid slightly below the highest previous bid, but not too low.
            # Also ensure we don't exceed what we can afford.
            target = min(highest_prev_bid - 2.0, DAILY_SALARY * (0.65 if supply_tier == 2 else 0.8))
            if target < DAILY_SALARY * 0.35:
                target = DAILY_SALARY * 0.35
        else:
            # If bids were moderate, bid around a low-to-mid tier.
            base = DAILY_SALARY * (0.5 if supply_tier == 2 else 0.65)
            # If second_prev_bid exists, lean slightly above it.
            if second_prev_bid > 0:
                target = max(base, second_prev_bid + 1.5)
            else:
                target = base

    # Budget-aware cap
    if budget <= 0:
        return 0.0

    # Ensure non-negative and not above budget
    bid = max(0.0, min(budget, target))

    # Extra small adjustment to avoid ties when not in danger
    if not danger:
        bid += 0.25

    return float(bid)
"""

# ============================================================
# Meta Round 10
# ============================================================

META_ROUND_10_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents
    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opponents.append((opp_id, opp))

    if not alive_opponents:
        # Conservative: if no one else alive, secure enough to avoid no-water death.
        target_bid = DAILY_SALARY * 0.35
        return min(my_status['budget'], target_bid)

    # Read yesterday bids from immediate previous_trace only
    yesterday_bids = []
    for _, opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    # Determine competitive pressure
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = (sum(yesterday_bids) / len(yesterday_bids)) if yesterday_bids else 0.0

    # If someone was extremely aggressive yesterday, we must respond.
    # Cindy died quickly (low bids), so we don't assume others will be that passive.
    aggressive_threshold = DAILY_SALARY * 0.85

    # Budget and HP safety
    my_hp = float(my_status.get('hp', 0))
    my_budget = float(my_status.get('budget', 0))
    no_water_days = int(my_status.get('no_water_days', 0))

    # Estimate how many days of water we can cover if we win minimal water each day.
    # Water allocation per winning bid is not given; we use supply to infer feasibility.
    # Strategy: bid to secure at least one unit of WATER_REQ worth.
    # Convert supply to an expected number of WATER_REQ blocks.
    blocks = int(supply / float(WATER_REQ))
    if blocks < 1:
        blocks = 1

    # Base bid: aim around mid of yesterday survivor bids
    # Use avg_prev_bid as anchor; if highest is high, push closer to highest.
    if highest_prev_bid >= aggressive_threshold:
        # Must compete; but keep some budget for later.
        if my_hp > 3:
            target = max(avg_prev_bid, highest_prev_bid * 0.7) + 1.0
        else:
            target = max(avg_prev_bid, highest_prev_bid * 0.85) + 2.0
    else:
        # Not extreme pressure: bid slightly above average to win often.
        target = max(avg_prev_bid, DAILY_SALARY * 0.5) + 1.5

    # If we're in danger (low HP or already many no-water days), increase bid.
    if my_hp <= 2.5 or no_water_days >= 2:
        target *= 1.15

    # If budget is low, cap spending.
    # We want to stretch across remaining days; approximate remaining days as episode_days - day.
    remaining_days = 10 - int(day)
    if remaining_days < 1:
        remaining_days = 1

    # Spend budget fraction depending on danger.
    danger_factor = 1.0
    if my_hp <= 2.5:
        danger_factor = 1.25
    elif my_hp <= 4.0:
        danger_factor = 1.10

    max_affordable = (my_budget / float(remaining_days)) * danger_factor

    # Also ensure bid isn't absurdly high relative to supply range.
    # Use a soft cap tied to DAILY_SALARY.
    soft_cap = DAILY_SALARY * 0.95

    bid = min(target, max_affordable, soft_cap, my_budget)

    # Ensure bid is at least a minimal positive amount when budget allows.
    if bid <= 0.0:
        bid = min(my_budget, DAILY_SALARY * 0.2)

    return float(bid)
"""
