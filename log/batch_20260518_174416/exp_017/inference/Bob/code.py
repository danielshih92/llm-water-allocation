# ============================================================
# Experiment: exp_017
# Agent: Bob
# Source: exp_017
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
    day = int(day_context['day'])

    alive_opponents = []
    for oid, o in opponents_status.items():
        if o.get('alive'):
            alive_opponents.append((oid, o))

    # If no opponents, take a safe moderate bid
    if not alive_opponents:
        base = DAILY_SALARY * 0.55 if my_status['hp'] > 2 else DAILY_SALARY * 0.9
        return max(0.0, min(float(my_status['budget']), float(base)))

    # Read yesterday bids from previous_trace only
    prev_bids = []
    for oid, o in alive_opponents:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                prev_bids.append(float(prev['bid']))
            except Exception:
                pass

    # Estimate how contested it was yesterday
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else highest_prev_bid

    # Urgency based on hp and no_water_days
    hp = float(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])

    urgency = 0.0
    if hp <= 2.0:
        urgency += 0.35
    elif hp <= 4.0:
        urgency += 0.15
    if no_water_days >= 2:
        urgency += 0.25
    elif no_water_days >= 1:
        urgency += 0.1

    # Supply pressure: higher supply -> bid less; lower supply -> bid more
    # Normalize between MIN_SUPPLY and MAX_SUPPLY
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_factor = 0.5
    else:
        supply_factor = (supply - float(MIN_SUPPLY)) / (float(MAX_SUPPLY) - float(MIN_SUPPLY))
        if supply_factor < 0.0:
            supply_factor = 0.0
        if supply_factor > 1.0:
            supply_factor = 1.0

    # Baseline bid target
    base_low = DAILY_SALARY * 0.45
    base_high = DAILY_SALARY * 0.85
    base = base_high - (base_high - base_low) * supply_factor

    # Counter logic vs opponent aggression
    # If they bid very high yesterday, we slightly undercut to win without overspending.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        target = min(highest_prev_bid - 2.0, DAILY_SALARY * (0.78 + urgency))
        if target < DAILY_SALARY * 0.55:
            target = DAILY_SALARY * (0.62 + urgency)
    else:
        # If they were moderate, hover between their likely range and our baseline.
        # Use second-highest as a proxy for how much we need to outbid.
        proxy = second_prev_bid if second_prev_bid > 0.0 else highest_prev_bid
        target = max(base, proxy + 1.5)
        target = target * (1.0 + 0.4 * urgency)

    # Budget and hp safety caps
    budget = float(my_status['budget'])
    # If hp is very low, spend more
    if hp <= 2.0:
        cap = DAILY_SALARY * 0.95
    elif hp <= 4.0:
        cap = DAILY_SALARY * 0.85
    else:
        cap = DAILY_SALARY * 0.75

    bid = min(budget, min(cap, target))

    # Ensure non-negative
    if bid < 0.0:
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    alive_opponents = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', True):
            alive_opponents.append(opp)

    # If no opponents are alive, conserve.
    if not alive_opponents:
        return min(float(my_status['budget']), DAILY_SALARY * 0.4)

    # Read yesterday bids from immediate trace only.
    yesterday_bids = []
    for opp in alive_opponents:
        prev = opp.get('previous_trace', {})
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                try:
                    yesterday_bids.append(float(b))
                except Exception:
                    pass
        else:
            # If previous_trace is not a dict, ignore.
            pass

    # Determine opponent pressure from yesterday.
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Base bid scales with supply: higher supply => we can bid less to still win.
    # When supply is scarce (near MIN_SUPPLY), we bid more to avoid running out.
    scarcity = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        scarcity = (MAX_SUPPLY - supply) / (MAX_SUPPLY - MIN_SUPPLY)
    scarcity = max(0.0, min(1.0, scarcity))

    # Convert scarcity to a target fraction of salary.
    # Aim around 0.55-0.75 of salary depending on scarcity.
    target_frac = 0.55 + 0.20 * scarcity

    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    # If my hp is critical, escalate.
    if my_hp <= 2 or no_water_days >= 2:
        target_frac = max(target_frac, 0.90)
    elif my_hp <= 4:
        target_frac = max(target_frac, 0.70)

    # Exploit observed behavior: Cindy/Eric bid very high and survived; but Alex/David died.
    # If yesterday pressure was extreme, we avoid matching it; instead bid just above a safe threshold.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        # Match moderately rather than fully.
        target_frac = max(target_frac, 0.65)

    # Compute candidate bid.
    candidate = my_budget if my_budget < DAILY_SALARY else DAILY_SALARY * target_frac

    # Additional adjustment based on water requirement vs supply.
    # If supply is low, we need more water allocation; bid higher.
    # Approximate needed units: supply / WATER_REQ.
    units = 0.0
    if WATER_REQ > 0:
        units = supply / float(WATER_REQ)
    if units < 2.0:
        candidate = max(candidate, DAILY_SALARY * (0.65 + 0.15 * scarcity))

    # Hard cap to avoid bankrupting.
    # Keep some budget buffer for later rounds.
    cap = max(0.0, my_budget * 0.75)
    bid = min(candidate, cap)

    # Ensure bid is non-negative.
    if bid < 0.0:
        bid = 0.0

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

    supply = float(day_context.get('supply', 0.0))
    day = day_context.get('day', 0)

    hp = int(my_status.get('hp', 0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append((oid, o))

    if not alive_opps:
        return max(0.0, min(budget, DAILY_SALARY * 0.4))

    # Read yesterday bids from immediate previous_trace only
    prev_bids = []
    for oid, o in alive_opps:
        prev = o.get('previous_trace', {})
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Estimate aggressiveness: high bids likely indicate they are trying to take most/all water.
    highest_prev_bid = max(prev_bids) if prev_bids else 0.0
    second_prev_bid = sorted(prev_bids)[-2] if len(prev_bids) >= 2 else 0.0

    # Supply pressure: at higher supply, we can bid less and still secure water.
    # At lower supply, bidding too low risks losing to aggressive opponents.
    supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY > MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base target bid: moderate, adjusted by supply and our condition.
    # If we're close to dying (low hp / many no-water days), increase.
    risk_factor = 0.0
    if hp <= 2:
        risk_factor += 0.45
    if no_water_days >= 2:
        risk_factor += 0.25
    if hp <= 4:
        risk_factor += 0.15

    # If someone previously bid extremely high, avoid mirroring; instead, bid enough to beat typical bids.
    # Use highest_prev_bid only as a cap/indicator.
    typical = second_prev_bid if second_prev_bid > 0 else (highest_prev_bid if highest_prev_bid > 0 else DAILY_SALARY * 0.5)

    # Determine a competitive but not reckless bid.
    # When supply is low, we tilt toward typical+small; when supply is high, we stay near typical.
    small_increment = 2.0 + 3.0 * (1.0 - supply_ratio)
    target = typical + small_increment

    # If highest_prev_bid is huge, keep target below it to save budget.
    # Otherwise, allow pushing closer to it.
    if highest_prev_bid >= DAILY_SALARY * 1.1:
        target = min(target, highest_prev_bid * (0.55 + 0.25 * supply_ratio))
    else:
        target = min(target, highest_prev_bid * (0.8 + 0.1 * supply_ratio) if highest_prev_bid > 0 else target)

    # Apply risk adjustment.
    target = target * (1.0 + risk_factor)

    # Convert to feasible bid bounds.
    # Also ensure we don't bid more than we can afford.
    max_affordable = max(0.0, budget)

    # Safety floor: if our risk is high, bid more aggressively.
    if risk_factor >= 0.45:
        target = max(target, DAILY_SALARY * 0.75)
    elif risk_factor >= 0.25:
        target = max(target, DAILY_SALARY * 0.6)
    else:
        target = max(target, DAILY_SALARY * (0.45 + 0.15 * supply_ratio))

    bid = min(max_affordable, target)

    # If budget is tiny, just spend what we can.
    if bid <= 0.0:
        bid = min(max_affordable, DAILY_SALARY * 0.1)

    return float(bid)
"""

# ============================================================
# Meta Round 4
# ============================================================

META_ROUND_4_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MIN_SUPPLY = 15
    MAX_SUPPLY = 25

    supply = float(day_context['supply'])
    day = day_context['day']

    hp = float(my_status['hp'])
    budget = float(my_status['budget'])
    no_water_days = int(my_status['no_water_days'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    # If alone, bid low but nonzero to conserve budget.
    if not alive_opps:
        bid = DAILY_SALARY * 0.35
        if budget < bid:
            bid = budget
        return float(bid)

    # Extract yesterday bids from previous_trace for immediate pressure.
    yesterday_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    pressure = 0.0
    if yesterday_bids:
        pressure = max(yesterday_bids)

    # Supply factor: with 15-25 supply, water per winner is limited.
    # Higher supply allows lower bids; lower supply requires higher bids.
    supply_ratio = (supply - MIN_SUPPLY) / float(MAX_SUPPLY - MIN_SUPPLY) if MAX_SUPPLY != MIN_SUPPLY else 0.5
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # Base bid targeting mid-high competitiveness.
    base = DAILY_SALARY * (0.62 - 0.18 * supply_ratio)  # ~0.62 at low supply, ~0.44 at high

    # React to yesterday max pressure: if others were willing to pay big, we must match more.
    # Eric died after low bids, so ignore low-pressure outliers by only using max.
    if pressure >= DAILY_SALARY * 0.85:
        base *= 1.18
    elif pressure >= DAILY_SALARY * 0.65:
        base *= 1.08

    # Urgency based on our hp and consecutive no-water days.
    urgency = 1.0
    if hp <= 2.0:
        urgency = 1.55
    elif hp <= 4.0:
        urgency = 1.25
    if no_water_days >= 2:
        urgency *= 1.20
    if no_water_days >= 3:
        urgency *= 1.10

    bid = base * urgency

    # Budget safety: if budget is low, cap aggressively.
    # Also avoid bidding more than we can afford.
    if budget <= 0:
        return 0.0

    # Keep some budget for later days; still try to survive.
    # If hp is very low, spend more.
    reserve_fraction = 0.25 if hp <= 3.0 else 0.40
    max_affordable = budget * (1.0 - reserve_fraction)
    bid = min(bid, max_affordable)

    # Ensure non-negative and at most budget.
    if bid < 0:
        bid = 0.0
    if bid > budget:
        bid = budget

    # If we are about to be desperate, ensure a minimum bid floor to compete.
    if hp <= 3.0 and bid < DAILY_SALARY * 0.55:
        bid = min(budget, DAILY_SALARY * 0.85)

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
    day = day_context['day']

    # If very low HP, prioritize survival over budget efficiency.
    my_hp = float(my_status['hp'])
    my_budget = float(my_status['budget'])

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return max(0.0, min(my_budget, DAILY_SALARY * 0.4))

    # Read yesterday bids to infer how aggressively others are competing.
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Baseline: mid bid to beat underbidders but not overpay.
    # Supply is between 15 and 25; higher supply reduces urgency.
    supply_factor = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY + 1e-9)  # 0..1
    urgency = 1.0 - max(0.0, min(1.0, supply_factor))

    # Estimate competitive pressure from yesterday's high bid.
    comp_pressure = 0.0
    if prev_bids:
        comp_pressure = max(prev_bids)

    # If someone previously paid very high, we should raise bid; otherwise hold mid-high.
    # Use DAILY_SALARY as a reference scale.
    high_threshold = DAILY_SALARY * 0.85

    if my_hp <= 2.0:
        target = DAILY_SALARY * (0.9 - 0.2 * urgency)
    elif comp_pressure >= high_threshold:
        # Others were very aggressive; match their intensity but keep some budget.
        target = DAILY_SALARY * (0.7 + 0.2 * urgency)
    else:
        # Mix: slightly above mid to avoid being outbid by aggressive survivors.
        target = DAILY_SALARY * (0.55 + 0.15 * urgency)

    # Clamp by budget.
    bid = min(my_budget, target)

    # Ensure non-negative.
    if bid < 0.0:
        bid = 0.0

    # Small deterministic bump on later days to avoid endgame starvation.
    try:
        if int(day) >= 7:
            bid = min(my_budget, bid + DAILY_SALARY * 0.05)
    except Exception:
        pass

    return float(bid)
"""

# ============================================================
# Meta Round 6
# ============================================================

META_ROUND_6_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90
    MAX_SUPPLY = 25
    MIN_SUPPLY = 15

    supply = float(day_context['supply'])
    day = int(day_context['day'])

    # Alive opponents
    alive_opps = []
    for k, o in opponents_status.items():
        if o.get('alive'):
            alive_opps.append((k, o))

    if not alive_opps:
        return float(min(my_status['budget'], DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace only (immediate reaction)
    yesterday_bids = []
    for _, o in alive_opps:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev['bid']))
            except Exception:
                pass

    max_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Estimate how many "water units" we can buy from supply-based typical conversion.
    # We don't know exact mechanics; use supply to cap aggressiveness.
    # If supply is near MAX, we can bid slightly less and still get enough water.
    # If supply is near MIN, we must bid more to secure allocation.
    supply_norm = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_norm = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    if supply_norm < 0.0:
        supply_norm = 0.0
    if supply_norm > 1.0:
        supply_norm = 1.0

    # Base bid: moderate, scaled by supply availability.
    # Lower supply -> higher base bid.
    base = DAILY_SALARY * (0.62 - 0.18 * supply_norm)

    # If yesterday's max bid was very high, bidding war likely; adjust.
    # Cindy/others showed high bids; we avoid overspending unless we must.
    if max_prev_bid >= DAILY_SALARY * 1.4:
        # War mode but still conservative: bid enough to compete, not to match max.
        base = max(base, DAILY_SALARY * (0.7 - 0.1 * supply_norm))
    elif max_prev_bid >= DAILY_SALARY * 0.85:
        base = max(base, DAILY_SALARY * (0.66 - 0.08 * supply_norm))

    # Survival pressure from my HP and no_water_days
    my_hp = int(my_status['hp'])
    no_water_days = int(my_status['no_water_days'])

    # If I'm close to death, escalate sharply.
    if my_hp <= 2 or no_water_days >= 2:
        base = max(base, DAILY_SALARY * (0.85 - 0.05 * supply_norm))
    elif my_hp <= 4:
        base = max(base, DAILY_SALARY * (0.72 - 0.05 * supply_norm))

    # Budget cap
    budget = float(my_status['budget'])
    bid = float(min(budget, base))

    # If budget is extremely low, bid what we can.
    if bid <= 0.0:
        return 0.0

    # Small anti-overspend nudge: keep under typical war peaks.
    # If we have plenty budget, avoid matching max_prev_bid exactly.
    if budget > DAILY_SALARY * 2.0 and max_prev_bid > 0.0:
        cap = max_prev_bid * 0.85
        bid = float(min(bid, cap))

    # Ensure bid is not negative
    if bid < 0.0:
        bid = 0.0

    return bid
"""

# ============================================================
# Meta Round 7
# ============================================================

META_ROUND_7_CODE = """
def get_bid(day_context, my_status, opponents_status):
    WATER_REQ = 9
    DAILY_SALARY = 90

    supply = day_context['supply']
    day = day_context['day']

    # Alive opponents
    alive = []
    for oid, o in opponents_status.items():
        if o.get('alive', True):
            alive.append((oid, o))

    # If no opponents, conserve budget
    if not alive:
        return max(0.0, min(my_status['budget'], DAILY_SALARY * 0.4))

    # Examine yesterday bids to infer aggression level
    yesterday_bids = []
    for oid, o in alive:
        prev = o.get('previous_trace', {})
        if prev and prev.get('bid') is not None:
            try:
                yesterday_bids.append(float(prev.get('bid')))
            except Exception:
                pass

    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0

    # Pressure estimate: if someone previously bid close to salary, others likely contest today too
    aggressive = highest_prev_bid >= DAILY_SALARY * 0.85

    # Determine how many water units are likely available; use int() for safety
    # supply is float; convert to int index-like quantities
    supply_int = int(supply)
    # Approximate number of
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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    alive_opps = []
    for oid, o in opponents_status.items():
        if o.get('alive', False):
            alive_opps.append(o)

    if not alive_opps:
        return min(float(my_status['budget']), DAILY_SALARY * 0.4)

    # Read yesterday bids from previous_trace for immediate reaction
    prev_bids = []
    for o in alive_opps:
        prev = o.get('previous_trace', None)
        if isinstance(prev, dict):
            b = prev.get('bid', None)
            if b is not None:
                prev_bids.append(float(b))

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Estimate how many
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

    supply = float(day_context.get('supply', 0.0))

    # Alive opponents only
    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    # If no one is alive, spend only enough to meet requirement safely
    if not alive_opps:
        return max(0.0, min(my_status.get('budget', 0.0), DAILY_SALARY * 0.4))

    # Read yesterday bids from previous_trace for immediate reaction
    yesterday_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                yesterday_bids.append(float(b))
            except Exception:
                pass

    # Use yesterday highest bid as pressure signal
    highest_prev_bid = max(yesterday_bids) if yesterday_bids else 0.0
    avg_prev_bid = sum(yesterday_bids) / float(len(yesterday_bids)) if yesterday_bids else 0.0

    my_hp = float(my_status.get('hp', 0.0))
    my_budget = float(my_status.get('budget', 0.0))

    # Supply pressure: higher supply reduces urgency; lower supply increases urgency
    # Map supply in [MIN_SUPPLY, MAX_SUPPLY] to a factor in [1.15, 0.85]
    if MAX_SUPPLY == MIN_SUPPLY:
        supply_factor = 1.0
    else:
        t = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
        supply_factor = 1.15 - 0.30 * t

    # Core target bid band derived from yesterday traces:
    # Alex/Cindy were ~100+, Eric ~73. Use a weighted target.
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        base_target = max(avg_prev_bid, highest_prev_bid * 0.9)
    else:
        base_target = max(avg_prev_bid, DAILY_SALARY * 0.55)

    # If supply is low, push slightly higher; if high, pull back.
    target = base_target * supply_factor

    # HP-based risk control: if low HP, avoid overbidding; if healthy, be more aggressive.
    if my_hp <= 2.0:
        target *= 0.75
    elif my_hp <= 4.0:
        target *= 0.9
    else:
        target *= 1.05

    # Don't exceed budget; also keep within a reasonable fraction of daily salary to avoid depletion.
    # (We still allow higher than salary if budget is large and pressure is high.)
    cap = my_budget
    if highest_prev_bid >= DAILY_SALARY * 0.85:
        cap = min(cap, DAILY_SALARY * 1.35)
    else:
        cap = min(cap, DAILY_SALARY * 1.10)

    bid = max(0.0, min(cap, target))

    # Ensure we always bid at least a small amount if budget allows
    if bid <= 0.0 and my_budget > 0.0:
        bid = min(my_budget, DAILY_SALARY * 0.25)

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

    supply = float(day_context.get('supply', 0.0))
    day = int(day_context.get('day', 0))

    hp = float(my_status.get('hp', 0.0))
    budget = float(my_status.get('budget', 0.0))
    no_water_days = int(my_status.get('no_water_days', 0))

    alive_opps = []
    for opp_id, opp in opponents_status.items():
        if opp.get('alive', False):
            alive_opps.append((opp_id, opp))

    if not alive_opps:
        return min(budget, DAILY_SALARY * 0.4)

    # Read yesterday bids from traces to infer their aggressiveness.
    prev_bids = []
    for _, opp in alive_opps:
        prev = opp.get('previous_trace', {}) or {}
        b = prev.get('bid', None)
        if b is not None:
            try:
                prev_bids.append(float(b))
            except Exception:
                pass

    # Fallback if trace missing
    if not prev_bids:
        base = DAILY_SALARY * (0.75 if hp > 2 else 0.95)
        return min(budget, base)

    # Aggression bands from yesterday
    high_bid = max(prev_bids)
    mid_bid = sorted(prev_bids)[len(prev_bids)//2]

    # Supply factor: higher supply reduces need to overbid.
    # Ensure indices are safe (no lists used for indexing here).
    supply_ratio = 0.0
    if MAX_SUPPLY > MIN_SUPPLY:
        supply_ratio = (supply - MIN_SUPPLY) / (MAX_SUPPLY - MIN_SUPPLY)
    supply_ratio = max(0.0, min(1.0, supply_ratio))

    # If we are in danger (low hp / many no-water days), bid more.
    danger = 0
    if hp <= 2.0:
        danger += 2
    if no_water_days >= 2:
        danger += 1

    # Strategy: undercut the high-bid band slightly; only chase if we're in danger.
    # Empirically, Cindy/Eric averaged ~117-122; target around 108-116 when safe.
    # Use a small epsilon to beat simultaneous ties.
    epsilon = 1.0
    target = None

    if danger >= 2:
        # Must secure water; bid close to the high band.
        target = max(mid_bid, high_bid - (8.0 if supply_ratio < 0.5 else 12.0)) + epsilon
    else:
        # Normal: bid just below the high band to capture water without burning budget.
        undercut = 9.0 if supply_ratio < 0.6 else 12.0
        target = min(high_bid - undercut + epsilon, max(mid_bid * 0.92, DAILY_SALARY * (0.55 + 0.25 * supply_ratio)))

    # Budget and reasonable caps
    # If budget is low, scale down but keep some pressure.
    if budget <= 0.0:
        return 0.0

    # Soft cap: don't exceed a fraction of budget; also avoid extreme bids.
    cap = min(budget, DAILY_SALARY * (1.15 if danger >= 2 else 0.95))
    bid = min(float(target), cap)

    # Ensure non-negative and at least minimal meaningful bid.
    if bid < 0.0:
        bid = 0.0

    # If we can afford, add small pressure when supply is low.
    if supply_ratio < 0.3 and danger == 0:
        bid = min(budget, bid + 6.0)

    return bid
"""
